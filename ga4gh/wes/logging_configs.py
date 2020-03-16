import logging as logging
from logging import config


def log_info(log_config, msg):
    logging.config.dictConfig(log_config)
    logger = logging.getLogger()
    logger.info(msg)


def log_error(log_config, msg):
    logging.config.dictConfig(log_config)
    logger = logging.getLogger()
    logger.error(msg)
