import logging
from datetime import datetime
from logging.config import dictConfig

logging.basicConfig(filename="app.log", format="%(asctime)s\t%(levelname)s\t%(message)s",
                    datefmt=datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ"), level=logging.INFO)


def log_info(msg):
    logging.info(msg)


def log_error(msg):
    logging.error(msg)


def dict_config():
    logging_config = {
            "version": 1,
            "formatters": {
                "standard": {
                    "format": "%(asctime)s\t%(levelname)s\t%(message)s",
                    "format_time": datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ")
                }
            },
            "handlers": {
                "console": {
                    "class": logging.StreamHandler,
                    "level": "INFO",
                    "formatter": "standard"
                },
                "file_handler": {
                    "class": logging.FileHandler,
                    "level": "INFO",
                    "formatter": "standard",
                    "filename": "app.log"
                }
            },
            "loggers": {
                "level": "INFO",
                "handlers": ["file_handler"],
                "propagate": True
            }
        }
    return dictConfig(logging_config)
