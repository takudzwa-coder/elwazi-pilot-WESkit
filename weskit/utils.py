import os
import pathlib
import traceback
from urllib.parse import urlparse
from datetime import datetime
from flask import current_app


def get_absolute_file_paths(directory):
    files = []
    for dir_path, _, filenames in os.walk(directory):
        for f in filenames:
            files.append(os.path.abspath(os.path.join(dir_path, f)))
    return files


def to_uri(paths):
    uri_paths = []
    for path in paths:
        uri_paths.append(pathlib.Path(path).as_uri())
    return uri_paths


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


def check_conditions(run_id, user_id, run=None):

    if run is None:
        current_app.error_logger.error("Could not find %s" % run_id)
        return {"msg": "Could not find %s" % run_id,
                "status_code": 0
                }, 404

    if user_id != run.user_id:
        current_app.error_logger.error("User not allowed to perform this action on %s" % run_id)
        return {"msg": "User not allowed to perform this action on %s" % run_id,
                       "status_code": 0}, 403

    return None
