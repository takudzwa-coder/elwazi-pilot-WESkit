#  Copyright (c) 2021. Berlin Institute of Health (BIH) and Deutsches Krebsforschungszentrum (DKFZ).
#
#  Distributed under the MIT License. Full text at
#
#      https://gitlab.com/one-touch-pipeline/weskit/api/-/blob/master/LICENSE
#
#  Authors: The WESkit Team

import os
from typing import List, Optional, Dict
from urllib.parse import urlparse


class RunRequestValidator(object):

    def __init__(self,
                 syntax_validator,
                 workflow_types_and_versions: Dict[str, List[str]]):
        """The syntax validator is a function that returns a string with
         an error message, if there is an error, or None otherwise."""
        self.syntax_validator = syntax_validator
        self.workflow_types_and_versions = workflow_types_and_versions

    def validate(self,
                 data: dict,
                 require_workdir_tag: bool) -> Optional[List[str]]:
        """Validate the overall structure, types and values of the run request
        fields. workflow_params and workflow_engine_parameters are not tested
        semantically but their structure is validated (see schema)."""
        def apply_if_not_none(value, func) -> Optional[str]:
            if value is not None:
                return func(value)
            else:
                return None

        stx_error = self._validate_syntax(data)
        wtnv_error = self._validate_workflow_type_and_version(
            data.get("workflow_type", None),
            data.get("workflow_type_version", None))
        url_error = apply_if_not_none(data.get("workflow_url", None),
                                      self._validate_workflow_url)
        workdir_tag_error = self._validate_workdir_tag(
            data.get("tags", None), require_workdir_tag)

        return list(filter(lambda v: v is not None,
                           [stx_error, wtnv_error,
                            url_error, workdir_tag_error]))

    def _validate_syntax(self, data: dict) -> Optional[str]:
        return self.syntax_validator(data)

    def _validate_workflow_type_and_version(self, type: str, version: str) \
            -> Optional[str]:
        if type is not None:
            if type not in self.workflow_types_and_versions.keys():
                return "Unknown workflow_type '%s'. Know %s" % \
                       (type, ", ".join(self.workflow_types_and_versions.keys()))
            elif version is not None and version not in self.workflow_types_and_versions[type]:
                return "Unknown workflow_type_version '%s'. Know %s" % \
                       (version, ", ".join(self.workflow_types_and_versions[type]))
        else:
            return None

    def _validate_workflow_type_version(self, workflow_type: str) \
            -> Optional[str]:
        # TODO The value needs to be an allowed version for the workflow_type
        return None

    def _validate_url(self, url: str) -> Optional[str]:
        """
        Only allow https:// or relative file: URIs. HTTPS is used because
        it is encrypted and temper-proof (in contrast to 'git://' URLs. file:
        is needed for locally installed workflows and workflows extracted from
        submitted attachments.

        For relative paths use

        file:path/to/file
        """
        try:
            parsed_url = urlparse(url)
            if parsed_url.scheme == "https":
                return None
            elif parsed_url.scheme == "" or parsed_url.scheme == "file":
                if os.path.isabs(parsed_url.path):
                    return "Not a relative path: '%s'" % url
                else:
                    # TODO Check that relative paths never go up with ../ beyond the path-root  # noqa
                    return None
            else:
                return "Only 'https://' and 'file:' (relative) URIs are allowed: '%s'" % url
        except Exception:
            return "Could not parse URI '%s'" % url

    def _validate_workflow_url(self, url: str) \
            -> Optional[str]:
        return self._validate_url(url)

    def _validate_workdir_tag(self, tags, require_workdir_tag):
        try:
            if require_workdir_tag:
                if tags is None:
                    return "'run_dir' tag is required and tags field is missing"
                elif "run_dir" not in tags.keys():
                    return "'run_dir' tag is required and missing"
                return self._validate_url(tags["run_dir"])
            return None
        except Exception:
            return "Could not parse 'run_dir' tag"
