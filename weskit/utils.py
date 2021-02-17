import os
import pathlib
from urllib.parse import urlparse
from datetime import datetime


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
