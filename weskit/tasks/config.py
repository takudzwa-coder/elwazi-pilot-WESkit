#  Copyright (c) 2022. Berlin Institute of Health (BIH) and Deutsches Krebsforschungszentrum (DKFZ).
#
#  Distributed under the MIT License. Full text at
#
#      https://gitlab.com/one-touch-pipeline/weskit/api/-/blob/master/LICENSE
#
#  Authors: The WESkit Team
import logging
import os

import yaml

logger = logging.getLogger(__name__)


def read_config():
    if os.getenv("WESKIT_CONFIG") is not None:
        config_file = os.getenv("WESKIT_CONFIG", "")
    else:
        raise ValueError("Cannot start WESkit: Environment variable WESKIT_CONFIG is undefined")

    with open(config_file, "r") as yaml_file:
        config = yaml.safe_load(yaml_file)
        logger.info("Read config from " + config_file)
    return config
