import logging
from datetime import datetime

logging.basicConfig(filename="app.log", format="%(asctime)s\t%(levelname)s\t%(message)s",
                    datefmt=datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ"), level=logging.INFO)


def log_info(msg):
    logging.info(msg)


def log_error(msg):
    logging.error(msg)


