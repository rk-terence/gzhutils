"""
Initializes the logging of this module
"""
import logging


module_name = '.'.join(__name__.split('.')[:-1])
logger = logging.getLogger(module_name)
# The default level is `logging.WARNING`
logger.setLevel(logging.INFO)
# By default there is no handler
sh = logging.StreamHandler()
sh.setFormatter(logging.Formatter(
    '%(name)s - %(levelname)s - %(message)s'
))
logger.addHandler(sh)
