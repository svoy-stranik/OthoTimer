import sys
import threading
from logging import getLogger
from logging.config import dictConfig


logging_config = {
    "version": 1,
    "disable_existing_loggers": True,
    "formatters": {
        "default": {
            "format": "[%(asctime)s] <%(levelname)s> %(funcName)s: %(message)s",
            "datefmt": "%Y-%m-%d %H:%M:%S",
        }
    },
    "handlers": {
        "console": {
            "formatter": "default",
            "class": "logging.StreamHandler",
            "stream": "ext://sys.stdout",
        },
        "file": {
            "formatter": "default",
            "class": "logging.FileHandler",
            "filename": "timer.log",
        },
    },
    "root": {
        "level": "INFO",
        "handlers": ["console", "file"],
    },
}


dictConfig(logging_config)
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
