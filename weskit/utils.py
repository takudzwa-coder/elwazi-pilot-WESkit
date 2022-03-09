#  Copyright (c) 2021. Berlin Institute of Health (BIH) and Deutsches Krebsforschungszentrum (DKFZ).
#
#  Distributed under the MIT License. Full text at
#
#      https://gitlab.com/one-touch-pipeline/weskit/api/-/blob/master/LICENSE
#
#  Authors: The WESkit Team

import boto3
import os
import traceback
from datetime import datetime
from typing import Dict, Union, List
from urllib.parse import urlparse

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
    return(url)
