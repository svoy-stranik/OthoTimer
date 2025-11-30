import sys
import threading
from logging import getLogger
from logging.config import dictConfig

from constants import LOGGER_CONFIG


dictConfig(LOGGER_CONFIG)
logger = getLogger("Otho Timer")


def _exception_hook(*args):
    if len(args) == 3:
        exc_type, exc_value, exc_traceback = args
    else:
        except_hook_args = args[0]
        exc_type = except_hook_args.exc_type
        exc_value = except_hook_args.exc_value
        exc_traceback = except_hook_args.exc_traceback

    logger.critical("Uncaught exception", exc_info=(exc_type, exc_value, exc_traceback))


def set_exception_hooks():
    sys.excepthook = _exception_hook
    threading.excepthook = _exception_hook
