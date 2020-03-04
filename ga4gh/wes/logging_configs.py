import logging, yaml
from logging.config import dictConfig


def log_config():
    with open("log_config.yaml") as f:
        log_cfg = yaml.load(f, Loader=yaml.FullLoader)
    dictConfig(log_cfg)


def log_info(msg):
    log_config()
    logger = logging.getLogger()
    logger.info(msg)


def log_error(msg):
    log_config()
    logger = logging.getLogger()
    logger.error(msg)
