import logging, yaml, os
from logging.config import dictConfig


def log_config():
    path = os.path.abspath(os.path.join("log_config.yaml"))
    with open(path) as f:
        log_cfg = yaml.load(f, Loader=yaml.FullLoader)
    dictConfig(log_cfg["logging"])


def log_info(msg):
    log_config()
    logger = logging.getLogger()
    logger.info(msg)


def log_error(msg):
    log_config()
    logger = logging.getLogger()
    logger.error(msg)
