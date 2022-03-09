#  Copyright (c) 2021. Berlin Institute of Health (BIH) and Deutsches Krebsforschungszentrum (DKFZ).
#
#  Distributed under the MIT License. Full text at
#
#      https://gitlab.com/one-touch-pipeline/weskit/api/-/blob/master/LICENSE
#
#  Authors: The WESkit Team
from __future__ import annotations

import logging
import os
import re
from typing import List, Optional, Dict, Callable, TypeVar, Union
from urllib.parse import urlparse

logger = logging.Logger(__file__)


class RunRequestValidator(object):

    def __init__(self,
                 syntax_validator: Callable[[Dict[str, dict]], Union[Dict[str, dict], List[str]]],
                 workflow_types_and_versions: Dict[str, List[str]],
                 data_dir: str,
                 require_workdir_tag: bool):
        """The syntax validator is a function that returns a string with
         an error message, if there is an error, or None otherwise."""
        self.syntax_validator = syntax_validator
        self.workflow_types_and_versions = workflow_types_and_versions
        self.data_dir = data_dir
        self.require_rundir_tag = require_workdir_tag

    def validate(self,
                 data: dict) \
            -> Union[dict, List[str]]:
        """Validate the overall structure, types and values of the run request
        fields. workflow_params and workflow_engine_parameters are not tested
        semantically but their structure is validated (see schema).
        Either return the normalized data or a list of error messages."""

        T = TypeVar('T')

        def apply_if_not_none(value: Optional[T], func: Callable[[T], List[str]]) -> List[str]:
            if value is not None:
                return func(value)
            else:
                return []

        stx_errors: List[str] = []
        syntax_validation_result = self._validate_and_normalize_syntax(data)
        if isinstance(syntax_validation_result, list):
            stx_errors += syntax_validation_result
            normalized_data = data
        else:
            normalized_data = syntax_validation_result

        wtnv_errors = self._validate_workflow_type_and_version(
            normalized_data.get("workflow_type", None),           # not optional by standard
            normalized_data.get("workflow_type_version", None))   # not optional by standard
        url_errors = apply_if_not_none(normalized_data.get("workflow_url", None),
                                       self._validate_workflow_url)
        workdir_tag_errors = self._validate_rundir_tag(
            normalized_data.get("tags", None))

        all_errors = stx_errors + wtnv_errors + url_errors + workdir_tag_errors
        if len(all_errors) > 0:
            return list(filter(lambda v: v != [] and v is not None, all_errors))
        else:
            return normalized_data

    def _validate_and_normalize_syntax(self, data: dict) \
            -> Union[dict, List[str]]:
        return self.syntax_validator(data)

    def _validate_workflow_type_and_version(self, wf_type: str, version: str) \
            -> List[str]:
        if wf_type is not None:
            if wf_type not in self.workflow_types_and_versions.keys():
                return ["Unknown workflow_type '%s'. Know %s" %
                        (wf_type, ", ".join(self.workflow_types_and_versions.keys()))]
            elif version is not None and version not in self.workflow_types_and_versions[wf_type]:
                return ["Unknown workflow_type_version '%s'. Know %s" %
                        (version, ", ".join(self.workflow_types_and_versions[wf_type]))]
        return []

    def _path_is_outside_data_dir(self, path) -> bool:
        """
        Return whether the `path`, which may include multiple '..', points to a directory that
        is still in or below data_dir.
        """
        from os.path import join, normpath, commonprefix
        expected_path = normpath(join(self.data_dir, path))
        return commonprefix([self.data_dir, expected_path]) != self.data_dir

    def _validate_file_url_path(self, url: str) -> List[str]:
        result = []
        try:
            parsed_url = urlparse(url)
            result += self.forbidden_characters(parsed_url.path)
            if os.path.isabs(parsed_url.path):
                result += ["Not a relative path: '%s'" % url]
            elif self._path_is_outside_data_dir(parsed_url.path):
                result += ["Normalized path points outside allowed root: '%s'" %
                           parsed_url.path]

        except Exception:
            result += ["Could not parse URI '%s'" % url]

        return result

    def _validate_url(self, url: str) -> List[str]:
        """
        Only allow https:// or relative file: URIs. HTTPS is used because
        it is encrypted and temper-proof (in contrast to 'git://' URLs. file:
        is needed for locally installed workflows and workflows extracted from
        submitted attachments.

        For relative paths use

            file:path/to/file   or    path/to/file

        Local paths must not contain forbidden characters (to avoid MongoDB or shell injection
        attacks.
        """
        result = []
        try:
            parsed_url = urlparse(url)
            if parsed_url.scheme == "https":
                # A URI may still try to access a third-party external server with a malicious URL.
                # I don't see any general way to decode the query and recognize such attacks.
                pass
            elif parsed_url.scheme == "" or parsed_url.scheme == "file":
                result += self._validate_file_url_path(url)
            else:
                result += ["Only 'https://' and 'file:' (relative) URIs are allowed: '%s'" % url]

        except Exception as ex:
            logger.warning(f"Exception during file URL validation: {ex}")
            result += ["Could not parse URI '%s'" % url]

        return result

    def _validate_workflow_url(self, url: str) -> List[str]:
        result = []
        try:
            parsed_url = urlparse(url)
            if parsed_url.scheme == "trs":
                # No further validation of the TRS URI yet.
                pass
            elif parsed_url.scheme == "" or parsed_url.scheme == "file":
                result += self._validate_file_url_path(url)
            else:
                result += ["Only 'file:' (relative) and 'trs:' are allowed in workflow URIs: '%s'"
                           % url]

        except Exception as ex:
            logger.warning(f"Exception during workflow URI validation: {ex}")
            result += [f"Could not parse URI '{url}'"]

        return result

    def _validate_rundir_tag(self, tags) -> List[str]:
        try:
            if self.require_rundir_tag:
                if tags is None:
                    return ["'run_dir' tag is required but tags field is missing"]
                elif "run_dir" not in tags.keys():
                    return ["'run_dir' tag is required and missing"]

                parsed_url = urlparse(tags["run_dir"])
                if parsed_url.scheme != "" and parsed_url.scheme != "file":
                    return ["'run_dir' tag must be relative file path"]

                return self._validate_url(tags["run_dir"])
            return []
        except Exception:
            return ["Could not parse 'run_dir' tag"]

    _uuid_pattern = re. \
        compile(r'^[0-9a-zA-Z]{8}-[0-9a-zA-Z]{4}-[0-9a-zA-Z]{4}-[0-9a-zA-Z]{4}-[0-9a-zA-Z]{12}$')

    @staticmethod
    def invalid_run_id(run_id: str) -> Optional[str]:
        """
        Run-IDs are UUIDs. So ensure run_id has the right pattern
        """
        if not RunRequestValidator._uuid_pattern.search(run_id):
            return "UUID expected. Got: '%s'" % run_id
        return None

    _user_pattern = re. \
        compile(r'^(\d|\w|-){,1000}$')

    @staticmethod
    def invalid_user_id(user_id: str) -> Optional[str]:
        """
        User-IDs must consist of alphanumerical values, '_', '-' (and limited to 1000 symbols
        (which is hilariously high for a user-name).
        """
        if not RunRequestValidator._user_pattern.search(user_id):
            return "Invalid user ID: Got: '%s'" % user_id
        return None

    _uri_query_forbidden_pattern = re. \
        compile(r'[;\'"\[\]{}()$]')

    @staticmethod
    def forbidden_characters(value: str) -> List[str]:
        """
        Ensure a string does not contain any malicious code, without being too restrictive. Still,
        e.g. it should be possible to use the string to actually do a query to a remote server to
        retrieve a resource. This is probably just a minimal check.
        """
        if RunRequestValidator._uri_query_forbidden_pattern.search(value):
            return ["Forbidden characters: '%s'" % value]
        return []
