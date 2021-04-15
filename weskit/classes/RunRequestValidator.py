import os
from typing import List, Optional
from urllib.parse import urlparse

from weskit.utils import all_subclasses
from weskit.classes.WorkflowEngine import WorkflowEngine


class RunRequestValidator(object):
    known_engine_ids = [engine.name()
                        for engine in all_subclasses(WorkflowEngine)]

    def __init__(self, syntax_validator):
        """The syntax validator is a function that returns a string with
         an error message, if there is an error, or None otherwise."""
        self.syntax_validator = syntax_validator

    def validate(self,
                 data: dict,
                 require_workdir_tag: bool) -> Optional[List[str]]:
        """Validate the overall structure, types and values of the run request
        fields. workflow_params and workflow_engine_parameters are not tested
        semantically but their structure is validated (see schema)."""
        def applyIfNotNone(value, func):
            if value is not None:
                return func(value)
            else:
                return None

        stx_error = self._validate_syntax(data)
        wev_error = applyIfNotNone(data.get("workflow_type", None),
                                   self._validate_workflow_type)
        wtv_error = applyIfNotNone(data.get("workflow_type_version", None),
                                   self._validate_workflow_type_version)
        url_error = applyIfNotNone(data.get("workflow_url", None),
                                   self._validate_workflow_url)
        workdir_tag_error = self._validate_workdir_tag(
            data.get("tags", None), require_workdir_tag)

        return list(filter(lambda v: v is not None,
                           [stx_error, wev_error, wtv_error,
                            url_error, workdir_tag_error]))

    def _validate_syntax(self, data: dict) -> Optional[str]:
        return self.syntax_validator(data)

    def _validate_workflow_type(self, type_version: str) \
            -> Optional[str]:
        if type_version not in RunRequestValidator.known_engine_ids:
            return "Unknown workflow_type '%s'. Know %s" % \
                   (type_version,
                    ", ".join(RunRequestValidator.known_engine_ids))
        else:
            return None

    def _validate_workflow_type_version(self, value: str) \
            -> Optional[str]:
        # TODO The value needs to be an allowed version for the workflow_type
        return None

    def _validate_workflow_url(self, url: str) \
            -> Optional[str]:
        """Only allow https:// or relative file: URIs. HTTPS is used because
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
            elif parsed_url.scheme == "file":
                if os.path.isabs(parsed_url.path):
                    return "Not a relative path: '%s'" % url
                else:
                    # TODO Check that relative paths never go up with ../ beyond the path-root  # noqa
                    return None
            else:
                return "Only 'https://' and 'file:' (relative) URIs" + \
                       " are allowed: '%s'" % url
        except Exception:
            return "Could not parse URI '%s'" % url

    def _validate_workdir_tag(self, tags, require_workdir_tag):
        if require_workdir_tag:
            if tags is None:
                return "'run_dir' tag is required and tags field is missing"
            elif "run_dir" not in tags.keys():
                return "'run_dir' tag is required and missing"
        return None
