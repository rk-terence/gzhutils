"""
Initializes the logging of this module

Assumed and suggested usage case:
Each logger has name the same as the module's runtime value of `__name__`.
For each top-level package, only the logger with name the same as 
the package name are configured with a handler, and the root logger 
of a package should not propagate further root logger.
"""
import io
import sys
import os
import logging
import ctypes
import tempfile
import platform
from typing import (
    Self, Any, Mapping, Literal, TextIO, TypedDict, Unpack, Sequence, Final,
    Callable
)
from contextlib import contextmanager, redirect_stdout

from .miscellaneous import InfiniteTimer


type Logger = logging.Logger
type Level = int | str
type Formatter = str | logging.Formatter
type Handler = logging.Handler


DEFAULT_FORMATTER_STRING: Final[str] = \
    "%(asctime)s - %(name)s - %(levelname)s - %(message)s"


LEVEL_MAP: Final[Mapping[str, int]] = {
    "NOTSET": logging.NOTSET,
    "DEBUG": logging.DEBUG,
    "INFO": logging.INFO,
    "WARNING": logging.WARNING,
    "ERROR": logging.ERROR,
    "CRITICAL": logging.CRITICAL
}


def _normalize_level(level: Level) -> int:
    if isinstance(level, str):
        level = level.upper()
        return LEVEL_MAP[level]
    else:
        return level


class LoggerOptions(TypedDict, total=False):
    level: Level
    propagate: bool
    handlers: Sequence[Handler]
    fmts: Sequence[Formatter]


def _configure_logger(
        logger: Logger, 
        **options: Unpack[LoggerOptions]
) -> None:
    if (level := options.get("level")) is not None:
        logger.setLevel(_normalize_level(level))

    logger.propagate = options.get("propagate") or logger.propagate
    
    if (handlers := options.get("handlers")) is not None:
        if len(old_handlers := logger.handlers.copy()):
            for handler in old_handlers:
                logger.removeHandler(handler)
        
        if (fmts := options.get("fmts")) is not None:
            assert len(fmts) == len(handlers)
        else:
            fmts = (None for _ in handlers)

        for handler, fmt in zip(handlers, fmts):
            if isinstance(fmt, logging.Formatter):
                handler.setFormatter(fmt)
            else:
                handler.setFormatter(logging.Formatter(fmt))
            logger.addHandler(handler)


def configure_logger(
        logger: Logger,
        level: Level = logging.WARNING,
        propagate: bool = False,
        handlers: Sequence[Handler] = (logging.StreamHandler(sys.stderr),),
        fmts: Sequence[Formatter] = (DEFAULT_FORMATTER_STRING,)
) -> Logger:
    """
    Utility function mainly used to configure the root logger of a package.
    (distinguished by package name)
    """
    _configure_logger(
        logger, 
        level=level, propagate=propagate, handlers=handlers, fmts=fmts
    )

    logging.getLogger(__name__).info(
        f"Configured logger {logger} with options set to "
        f"{level=}, {propagate=}, {handlers=}, {fmts=}"
    )

    return logger


@contextmanager
def logger_options(logger: Logger, **options: Unpack[LoggerOptions]):
    backup: LoggerOptions = {}
    for potential_key in LoggerOptions.__optional_keys__:
        if potential_key in options:
            match potential_key:
                case "level" | "propagate":
                    backup[potential_key] = getattr(logger, potential_key)
                case "handler":
                    backup["handlers"] = logger.handlers
                case "fmt":
                    backup["fmts"] = [
                        handler.formatter or logging.Formatter()
                        for handler in logger.handlers
                    ]
    
    _configure_logger(logger, **options)
    try: yield
    finally: _configure_logger(logger, **backup)


def get_log_functions(logger: Logger):
    return logger.debug, logger.info, logger.warning, logger.error


class VerboseLogger:
    """
    Context manager to temporarily change one or several loggers' level.
    """
    def __init__(
            self: Self, 
            *package_names: str, 
            level: Level = logging.DEBUG
    ) -> None:
        self.level = _normalize_level(level)
        self.loggers: list[Logger] = []
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
            stream.write(tfile.read())
            stream.write(bytes(sio.getvalue(), encoding='utf-8'))
        finally:
            tfile.close()
            os.close(saved_c_stdout_fd)
    
    return all_stdout_redirector


@contextmanager
def redirect_all_stdout(
        logger_or_file: Logger | io.TextIOBase,
        level: Level = logging.INFO
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
            "Expected io.TextIOBase or Logger, "
            f"got {logger_or_file.__class__.__name__} instead."
        )


class _LoggerFile(TextIO):
    def __init__(
            self: Self, 
            logger: Logger, 
            level: Level,
            write_to_stdout: bool = False
    ) -> None:
        self.logger = logger
        self.level = level
        self.write_to_stdout = write_to_stdout

        self.stdout = sys.stdout
    
    def write(self, msg: str):
        self.logger.log(_normalize_level(self.level), msg)
        if self.write_to_stdout:
            self.stdout.write(msg)
    
    def flush(self):
        if self.write_to_stdout:
            self.stdout.flush()


@contextmanager
def redirect_stdout_to_logger(
        logger: Logger, 
        level: Level,
        keep_stdout: bool = False
):
    with redirect_stdout(
            _LoggerFile(logger, level, write_to_stdout=keep_stdout)
    ):
        yield


def log_msg_each_interval(
        logger: Logger, 
        interval: float = 60,
        level: Level = logging.INFO,
        msg: str = "I am alive"
):
    def callback(logger: Logger, level: Level, msg: str) -> None:
        logger.log(_normalize_level(level), msg)
    
    return InfiniteTimer(
        interval=interval,
        callback=callback,
    ).run(logger, level, msg)


# configure the logger for this package.
PACKAGE_NAME = '.'.join(__name__.split('.')[:-1])
configure_logger(logging.getLogger(PACKAGE_NAME), level=logging.INFO)
