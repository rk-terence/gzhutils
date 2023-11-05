"""
Initializes the logging of this module
"""
import io
import sys
import os
import logging
import ctypes
import tempfile
import platform
from typing import Self, Any, Mapping, Literal
from contextlib import contextmanager


DEFAULT_FORMATTER_STRING = \
    "%(asctime)s - %(name)s - %(levelname)s - %(message)s"


LEVEL_MAP: Mapping[str, int] = {
    "NOTSET": logging.NOTSET,
    "DEBUG": logging.DEBUG,
    "INFO": logging.INFO,
    "WARNING": logging.WARNING,
    "ERROR": logging.ERROR,
    "CRITICAL": logging.CRITICAL
}


def _normalize_level(level: int | str) -> int:
    if isinstance(level, str):
        level = level.upper()
        return LEVEL_MAP[level]
    else:
        return level


def configure_logger(
        logger: logging.Logger,
        level: int | str = logging.WARNING,
        propagate: bool = False,
        handler: logging.Handler = logging.StreamHandler(sys.stderr),
        fmt: str = DEFAULT_FORMATTER_STRING
) -> logging.Logger:
    """
    Utility function mainly used to configure the root logger of a package.
    (distinguished by package name)
    """
    logger.setLevel(_normalize_level(level))
    # disable message propagation.
    logger.propagate = propagate

    handler.setFormatter(logging.Formatter(fmt))
    logger.addHandler(handler)

    logging.getLogger(__name__).info(
        f"Configured logger {logger} with options set to "
        f"{level=}, {propagate=}, {handler=}, {fmt=}"
    )

    return logger


def get_log_functions(logger: logging.Logger):
    return logger.debug, logger.info, logger.warning, logger.error


class VerboseLogger:
    """
    Context manager to temporarily change one or several loggers' level.
    """
    def __init__(
            self: Self, 
            *package_names: str, 
            level: int | str = logging.DEBUG
    ) -> None:
        self.level = _normalize_level(level)
        self.loggers: list[logging.Logger] = []
        self.level_baks: list[int] = []
        for package_name in package_names:
            logger = logging.getLogger(package_name)
            self.loggers.append(logger)
            self.level_baks.append(logger.level)
    
    def __enter__(self: Self):
        for logger in self.loggers:
            logger.setLevel(self.level)
    
    def __exit__(self: Self, *args: Any):
        for logger, level in zip(self.loggers, self.level_baks):
            logger.setLevel(level)


def _get_all_stdout_redirector(
        sys_name: Literal["Linux", "Windows", "Darwin"]
):
    """ 
    Copied and modified from 
    https://gist.github.com/natedileas/8eb31dc03b76183c0211cdde57791005

    Capture and redirect stdout which arises from c extension or shared library.

    KNOWN LIMITATIONS: If code block to be executed inside this context manager 
    keeps a reference to the `sys.stdout` and tries to write to it
    (for example, a logger whose handlers already include one sys.stdout
    StreamHandler trying to log message in it), an OSError of invalid handle
    will occur.
    
    More references:
    1. wurlitzer: https://github.com/minrk/wurlitzer
    2. https://eli.thegreenplace.net/2015/redirecting-all-kinds-of-stdout-in-python/
    3. https://stackoverflow.com/questions/17942874/stdout-redirection-with-ctypes
    """ 
    if sys_name == "Windows":
        if hasattr(sys, 'gettotalrefcount'): # debug build
            libc = ctypes.CDLL('ucrtbased')
        else:
            libc = ctypes.CDLL('api-ms-win-crt-stdio-l1-1-0')
        # c_stdout = ctypes.c_void_p.in_dll(libc, 'stdout')
        kernel32 = ctypes.WinDLL('kernel32')
        STD_OUTPUT_HANDLE = -11
        c_stdout = kernel32.GetStdHandle(STD_OUTPUT_HANDLE)
    elif sys_name == "Linux":
        libc = ctypes.CDLL(None)  # "libc.so.6"
        c_stdout = ctypes.c_void_p.in_dll(libc, 'stdout')
    elif sys_name == "Darwin":
        libc = ctypes.CDLL(None)
        c_stdout = ctypes.c_void_p.in_dll(libc, '__stdoutp')

            
    ##############################################################

    @contextmanager
    def all_stdout_redirector(stream: io.BytesIO):
        # use sys.__stdout__ because sys.stdout might be modified by ipython
        # or jupyter, while C prints to the sys.__stdout__.
        c_stdout_fd = sys.__stdout__.fileno()
        stdout_bak = sys.stdout

        def redirect_all_stdout(to_fd: int):
            """Redirect stdout to the given file descriptor."""
            # Flush the C-level buffer stdout
            if sys_name == "Windows":
                libc.fflush(None)   #### CHANGED THIS ARG TO NONE #############
            else:
                libc.fflush(c_stdout)

            # Make c_stdout_fd point to to_fd
            os.dup2(to_fd, c_stdout_fd)

        # Save a copy of the original c_stdout_fd
        saved_c_stdout_fd = os.dup(c_stdout_fd)
        try:
            # Create a temporary file and redirect c extension's stdout to it
            tfile = tempfile.TemporaryFile(mode='w+b')
            sys.stdout = (sio := io.StringIO())
            redirect_all_stdout(tfile.fileno())
            try:
                yield
            finally:
                redirect_all_stdout(saved_c_stdout_fd)
                sys.stdout = stdout_bak
            tfile.flush()
            tfile.seek(0, io.SEEK_SET)
            stream.write(b"C lib stdout:\n" + tfile.read())
            stream.write(b"Python stdout:\n" + 
                         bytes(sio.getvalue(), encoding='utf-8'))
        finally:
            tfile.close()
            os.close(saved_c_stdout_fd)
    
    return all_stdout_redirector


@contextmanager
def redirect_all_stdout(
        logger_or_file: logging.Logger | io.TextIOBase,
        level: int | str = logging.INFO
):
    sys_name = platform.system()
    SUPPORTED_SYS_NAME = ("Windows", "Linux", "Darwin")
    if sys_name not in SUPPORTED_SYS_NAME:
        raise RuntimeError("OS not supported.")
    
    stdout_redirector = _get_all_stdout_redirector(sys_name)

    f = io.BytesIO()
    with stdout_redirector(f):
        yield
    captured_stdout = f.getvalue().decode("utf-8")
    
    if isinstance(logger_or_file, logging.Logger):
        logger_or_file.log(_normalize_level(level), captured_stdout)
    elif isinstance(logger_or_file, io.TextIOBase):
        print(captured_stdout, end='', file=logger_or_file)
    else:
        raise TypeError(
            "Invalid target type. "
            "Expected io.TextIOBase or logging.Logger, "
            f"got {logger_or_file.__class__.__name__} instead."
        )


# configure the logger for this package.
PACKAGE_NAME = '.'.join(__name__.split('.')[:-1])
configure_logger(logging.getLogger(PACKAGE_NAME), level=logging.INFO)
