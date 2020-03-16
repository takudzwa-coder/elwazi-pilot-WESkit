import logging
from logging.config import dictConfig


def log_info(log_config, msg):
    dictConfig(log_config)
    logger = logging.getLogger()
    logger.info(msg)


def log_error(log_config, msg):
    dictConfig(log_config)
    logger = logging.getLogger()
    logger.error(msg)
