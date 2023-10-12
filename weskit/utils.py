# SPDX-FileCopyrightText: 2023 The WESkit Contributors
#
# SPDX-License-Identifier: MIT

import asyncio
import logging
import os
import traceback
from asyncio import AbstractEventLoop
from datetime import datetime
from importlib.abc import Traversable
from importlib.resources import files
from typing import Dict, Union, List, TypeVar, Optional, Callable, Any, Mapping
from urllib.parse import urlparse

import boto3
from cerberus import Validator

logger = logging.getLogger(__name__)


def get_event_loop() -> AbstractEventLoop:
    try:
        return asyncio.get_event_loop()
    except RuntimeError as ex:
        # Compare StackOverflow: https://tinyurl.com/yckkwbew
        if str(ex).startswith('There is no current event loop in thread'):
            logger.warning("Using a fresh asyncio event-loop")
            event_loop = asyncio.new_event_loop()
            asyncio.set_event_loop(event_loop)
            return event_loop
        else:
            raise ex


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


def now() -> datetime:
    """
    MongoDB stores datetime as int64 in microseconds. This means that through storage of datetimes
    the nanoseconds of the original datetime are truncated. We do the truncation directly here,
    to ensure the original timestamp has microseconds precision and therefore input and output
    timestamps of the DB are identical.

    See https://jira.mongodb.org/browse/PYTHON-1173
    """
    return datetime.fromtimestamp(int(datetime.utcnow().timestamp() * 1000) / 1000.0)


def format_timestamp(time: datetime) -> str:
    return time.isoformat()


def from_formatted_timestamp(stamp: str) -> datetime:
    return datetime.fromisoformat(stamp)


def get_current_timestamp() -> str:
    return format_timestamp(now())


def all_subclasses(cls):
    """Stolen from https://stackoverflow.com/a/3862957/8784544"""
    return set(cls.__subclasses__()).union(
        [s for c in cls.__subclasses__() for s in all_subclasses(c)])


def get_traceback(e: Exception) -> str:
    return ''.join(traceback.format_exception(None, e, e.__traceback__))


def create_validator(schema):
    """Return a validator function that can be provided a data structure to
    be validated. The validator is returned as second argument."""
    def _validate(target) -> Union[Dict[str, dict], List[str]]:
        validator = Validator()
        validation_success = validator.validate(target, schema)
        if validation_success:
            return validator.normalized(target, schema)
        else:
            return [validator.errors]
    return _validate


def safe_getenv(key: str) -> str:
    value = os.environ[key]
    if value is None or len(value) == 0:
        raise ValueError("Environment variable '%s' is set to invalid value '%s'" % (key, value))
    return value


def return_pre_signed_url(workdir, outfile):
    """Returns a presigned url for an output in a workdir file."""
    s3client = boto3.client("s3",
                            endpoint_url=safe_getenv("WESKIT_S3_ENDPOINT"),
                            aws_access_key_id=safe_getenv("WESKIT_S3_ID"),
                            aws_secret_access_key=safe_getenv("WESKIT_S3_SECRET"),
                            region_name=safe_getenv("WESKIT_S3_REGION"))
    url = s3client.generate_presigned_url(
        ClientMethod="get_object",
        Params={
            "Bucket": workdir.split("/")[0],
            "Key": "{}/{}".format(workdir.split("/")[1], outfile)
        }
    )
    return url


T = TypeVar("T")

R = TypeVar("R")


def mop(value: Optional[T], fun: Callable[[T], R]) -> Optional[R]:
    """
    Map a function over an optional value.
    """
    if value is not None:
        return fun(value)
    else:
        return None


def identity(value: T) -> T:
    """
    Just an identity function. There is none in the standard library.
    """
    return value


def updated(d: Mapping[str, Any], **kwargs) -> Mapping[str, Any]:
    """
    This is to avoid duplicate signature key errors when doing

        function(**some_dict, override_key=override_value)

    and its alternative with "**" madness.

    Note: This does not do a deep copy. Just replace values.
    """
    dc = {**d}
    for k, v in kwargs.items():
        dc[k] = v
    return dc


def resource_path(module: str, name: str) -> Traversable:
    return files(module).joinpath(name)


def read_resource(module: str, name: str) -> str:
    return resource_path(module, name).read_text(encoding="utf-8")
