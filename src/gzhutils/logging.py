"""
Initializes the logging of this module
"""
import logging


DEFAULT_FORMATTER_STRING = \
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s'


def configure_logger(
        logger: logging.Logger,
        level: int = logging.INFO,
        handler: logging.Handler = logging.StreamHandler(),
        fmt: str = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
) -> logging.Logger:
    logger.setLevel(level)

    handler.setFormatter(logging.Formatter(fmt))
    logger.addHandler(handler)

    return logger


# configure the logger for this package.
module_name = '.'.join(__name__.split('.')[:-1])
configure_logger(logging.getLogger(module_name))
