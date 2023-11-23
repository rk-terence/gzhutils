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
import logging
import platform
import typing as t
from pathlib import Path
from contextlib import contextmanager, redirect_stdout

from .miscellaneous import InfiniteTimer, get_all_stdout_redirector


type LoggerLike = logging.Logger | str
type LevelLike = int | str
type Formatter = str | logging.Formatter
type Handler = logging.Handler


DEFAULT_FORMATTER_STRING: t.Final[str] = \
    "%(asctime)s - %(name)s - %(levelname)s - %(message)s"


LEVEL_MAP: t.Final[t.Mapping[str, int]] = {
    "NOTSET": logging.NOTSET,
    "DEBUG": logging.DEBUG,
    "INFO": logging.INFO,
    "WARNING": logging.WARNING,
    "ERROR": logging.ERROR,
    "CRITICAL": logging.CRITICAL
}


def _normalize_level(level: LevelLike) -> int:
    if isinstance(level, str):
        level = level.upper()
        return LEVEL_MAP[level]
    else:
        return level

def _normalize_logger(logger: LoggerLike) -> logging.Logger:
    if isinstance(logger, str):
        return logging.getLogger(logger)
    else:
        return logger


class LoggerOptions(t.TypedDict, total=False):
    level: LevelLike
    propagate: bool
    handlers: t.Sequence[Handler]
    fmts: t.Sequence[Formatter]


def _configure_logger(
        logger_like: LoggerLike, 
        **options: t.Unpack[LoggerOptions]
) -> None:
    logger = _normalize_logger(logger_like)
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
        logger_like: LoggerLike,
        level: LevelLike = logging.WARNING,
        propagate: bool = False,
        handlers: t.Sequence[Handler] = (logging.StreamHandler(sys.stderr),),
        fmts: t.Sequence[Formatter] = (DEFAULT_FORMATTER_STRING,)
) -> logging.Logger:
    """
    Utility function mainly used to configure the root logger of a package.
    (distinguished by package name)
    """
    _configure_logger(
        logger_like, 
        level=level, propagate=propagate, handlers=handlers, fmts=fmts
    )

    logging.getLogger(__name__).log(
        logging.WARNING if _PACKAGE_NAME != logger_like 
            else logging.INFO,
        f"Configured logger {logger_like} with options set to "
        f"{level=}, {propagate=}, {handlers=}, {fmts=}"
    )

    return _normalize_logger(logger_like)


@contextmanager
def logger_options(logger_like: LoggerLike, **options: t.Unpack[LoggerOptions]):
    logger = _normalize_logger(logger_like)

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


def get_log_functions(logger_like: LoggerLike):
    logger = _normalize_logger(logger_like)
    return logger.debug, logger.info, logger.warning, logger.error


class VerboseLogger:
    """
    Context manager to temporarily change one or several loggers' level.
    """
    def __init__(
            self: t.Self, 
            *package_names: str, 
            level: LevelLike = logging.DEBUG
    ) -> None:
        self.level = _normalize_level(level)
        self.loggers: list[logging.Logger] = []
        self.level_baks: list[int] = []
        for package_name in package_names:
            logger = logging.getLogger(package_name)
            self.loggers.append(logger)
            self.level_baks.append(logger.level)
    
    def __enter__(self: t.Self):
        for logger in self.loggers:
            logger.setLevel(self.level)
    
    def __exit__(self: t.Self, *args: t.Any):
        for logger, level in zip(self.loggers, self.level_baks):
            logger.setLevel(level)


@contextmanager
def add_file_handler_to_loggers(
        filepath: Path, 
        *loggers: LoggerLike,
        fmt: str = DEFAULT_FORMATTER_STRING
) -> t.Generator[None, None, None]:
    # None, None, None
    # yield, send, return
    handler = logging.FileHandler(filepath)
    handler.setFormatter(logging.Formatter(fmt))
            
    for logger in (_normalize_logger(logger) for logger in loggers):
        logger.addHandler(handler)
    try:
        yield
    finally:
        for logger in loggers:
            _normalize_logger(logger).removeHandler(handler)
        handler.close()


@contextmanager
def redirect_all_stdout(
        logger_or_file: LoggerLike | io.TextIOBase,
        level: LevelLike = logging.INFO
):
    sys_name = platform.system()
    SUPPORTED_SYS_NAME = ("Windows", "Linux", "Darwin")
    if sys_name not in SUPPORTED_SYS_NAME:
        raise RuntimeError("OS not supported.")
    
    stdout_redirector = get_all_stdout_redirector(sys_name)

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


class _LoggerFile(t.TextIO):
    def __init__(
            self: t.Self, 
            logger_like: logging.Logger, 
            level: LevelLike,
            write_to_stdout: bool = False
    ) -> None:
        self.logger = _normalize_logger(logger_like)
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
        logger_like: LoggerLike, 
        level: LevelLike,
        keep_stdout: bool = False
):
    with redirect_stdout(_LoggerFile(_normalize_logger(logger_like), 
                                     level, 
                                     write_to_stdout=keep_stdout)):
        yield


@contextmanager
def log_msg_each_interval(
        logger_like: LoggerLike, 
        interval: float = 60,
        level: LevelLike = logging.INFO,
        msg: str = "I am alive"
):
    def callback(logger: logging.Logger, level: LevelLike, msg: str) -> None:
        logger.log(_normalize_level(level), msg)
    
    inf_timer = InfiniteTimer(
        interval=interval,
        callback=callback,
    ).setargs(_normalize_logger(logger_like), level, msg)
    inf_timer.start()

    try:
        yield inf_timer
    finally:
        inf_timer.stop()
        inf_timer.join()



# configure the logger for this package.
_PACKAGE_NAME = '.'.join(__name__.split('.')[:-1])
configure_logger(_PACKAGE_NAME, level=logging.WARNING)
