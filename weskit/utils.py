#  Copyright (c) 2021. Berlin Institute of Health (BIH) and Deutsches Krebsforschungszentrum (DKFZ).
#
#  Distributed under the MIT License. Full text at
#
#      https://gitlab.com/one-touch-pipeline/weskit/api/-/blob/master/LICENSE
#
#  Authors: The WESkit Team

import os
import traceback
from typing import Optional
from urllib.parse import urlparse
from datetime import datetime

from cerberus import Validator


def collect_relative_paths_from(directory):
    files = []
    for dir_path, _, filenames in os.walk(directory):
        for f in filenames:
            files.append(os.path.relpath(os.path.join(dir_path, f), directory))
    return files


def to_filename(uris):
    filenames = []
    for uri in uris:
        filenames.append(os.path.basename(urlparse(uri).path))
    return filenames


def format_timestamp(time) -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ")


def get_current_timestamp() -> str:
    return format_timestamp(datetime.now())


def all_subclasses(cls):
    """Stolen from https://stackoverflow.com/a/3862957/8784544"""
    return set(cls.__subclasses__()).union(
        [s for c in cls.__subclasses__() for s in all_subclasses(c)])


def get_traceback(e: Exception) -> str:
    return ''.join(traceback.format_exception(None, e, e.__traceback__))


def create_validator(schema):
    """Return a validator function that can be provided a data structure to
    be validated. The validator is returned as second argument."""
    def _validate(target) -> Optional[str]:
        validator = Validator()
        result = validator.validate(target, schema)
        if result:
            return None
        else:
            return validator.errors
    return _validate
