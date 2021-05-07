#  Copyright (c) 2021. Berlin Institute of Health (BIH) and Deutsches Krebsforschungszentrum (DKFZ).
#
#  Distributed under the MIT License. Full text at
#
#      https://gitlab.com/one-touch-pipeline/weskit/api/-/blob/master/LICENSE
#
#  Authors: The WESkit Team

import os
import traceback
from urllib.parse import urlparse
from datetime import datetime


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


def get_current_timestamp() -> str:
    return datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ")


def all_subclasses(cls):
    """Stolen from https://stackoverflow.com/a/3862957/8784544"""
    return set(cls.__subclasses__()).union(
        [s for c in cls.__subclasses__() for s in all_subclasses(c)])


def get_traceback(e: Exception) -> str:
    return ''.join(traceback.format_exception(None, e, e.__traceback__))
