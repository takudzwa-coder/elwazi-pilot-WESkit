# SPDX-FileCopyrightText: 2023 The WESkit Team
#
# SPDX-License-Identifier: MIT

import datetime
from typing import Dict, List, Any

from weskit.classes.Database import Database
from weskit.classes.WorkflowEngineFactory import ConfParameters
from weskit.classes.ProcessingStage import ProcessingStage
from weskit.api.RunStatus import RunStatus


class ServiceInfo:
    """Note that the static_service_info is not validated in here. External
    validation is required. ServiceInfo returns whatever it gets as static
    service info."""
    def __init__(self,
                 static_service_info: dict,
                 engines_config: dict,
                 swagger,
                 database: Database):
        self._static_service_info = static_service_info
        self._engine_configuration = engines_config
        self._db = database
        self._swagger = swagger
        self._metadata_separator = "|"

    def id(self) -> str:
        return self._static_service_info["id"]

    def name(self) -> str:
        return self._static_service_info["name"]

    def type(self) -> Dict[str, str]:
        return self._static_service_info["type"]

    def description(self) -> str:
        return self._static_service_info["description"]

    def organization(self) -> Dict[str, str]:
        return self._static_service_info["organization"]

    def contact_url(self) -> str:
        return self._static_service_info["contact_url"]

    def documentation_url(self) -> str:
        return self._static_service_info["documentation_url"]

    def created_at(self) -> datetime.datetime:
        return self._static_service_info["created_at"]

    def updated_at(self) -> datetime.datetime:
        return self._static_service_info["updated_at"]

    def environment(self) -> str:
        return self._static_service_info["environment"]

    def version(self) -> str:
        return self._static_service_info["version"]

    def workflow_type_versions(self) -> Dict[str, Dict[str, List[str]]]:
        """
        Currently, the workflow_type_versions are just the workflow_engine_versions.
        TODO: Compare https://gitlab.com/one-touch-pipeline/weskit/-/issues/91
        """
        return {engine: {"workflow_type_version": list(by_version.keys())}
                for engine, by_version
                in self._engine_configuration.items()}

    def supported_wes_versions(self) -> List[str]:
        return [self._swagger["info"]["version"]]

    def supported_filesystem_protocols(self) -> List[str]:
        return self._static_service_info["supported_filesystem_protocols"]

    def workflow_engine_versions_dict(self) -> Dict[str, List[str]]:
        return {engine: list(versions.keys())
                for engine, versions in self._raw_api_default_workflow_engine_parameters().items()}

    def workflow_engine_versions(self) -> Dict[str, str]:
        """
        Specs says this should be Dict[str, str], but it should better be
        Dict[str, List[str]]. Let's return the multiple versions as string, but as
        a comma-separated list. For some time we anyway will only have a single version
        of each workflow engine.
        """
        return dict(map(lambda kv: (kv[0], ",".join(kv[1])),
                        self.workflow_engine_versions_dict().items()))

    def _raw_api_default_workflow_engine_parameters(self) \
            -> Dict[str, Dict[str, ConfParameters]]:
        """
        We use the "api" field internally, to configure in the server which parameters are allowed
        to be set via the REST API. Forbidden parameters are not reported via the ServiceInfo.
        """
        return {engine: {version: [{"name": parameter["name"],
                                    "default_value": parameter.get("value"),
                                    "type": parameter["type"]}
                                   for parameter in engine_options["default_parameters"]
                                   if parameter["api"]]
                         for version, engine_options in by_version.items()}
                for engine, by_version
                in self._engine_configuration.items()}

    def default_workflow_engine_parameters(self) \
            -> ConfParameters:
        """
        The default workflow engine parameters as reported by the service info endpoint.

        Note that the 1.0.0 version of the API does not support structurally encoding parameters
        per workflow engine and engine version. Therefore, here we encode this information as
        obligatory fields in the parameter names, like "engine|version|parameter".
        The fields are separated by pipes `|`.
        """
        raw_params = self._raw_api_default_workflow_engine_parameters()
        result: ConfParameters = []
        for engine, versions in raw_params.items():
            for version, parameters in versions.items():
                for parameter in parameters:
                    result.append({
                        "name": self._metadata_separator.join([engine,
                                                               version,
                                                               str(parameter["name"])]),
                        "default_value": parameter["default_value"],
                        "type": parameter["type"]
                    })
        return result

    def system_state_counts(self) -> Dict[str, int]:

        counts_data: List[Any] = self._db.count_states()
        counts: Dict = {status.name: 0 for status in RunStatus}
        for counts_datum in counts_data:
            status = RunStatus.from_stage(
                stage=ProcessingStage.from_string(counts_datum["_id"]["processing_stage"]))
            counts[status.name] += counts_datum["count"]
        return counts

    def auth_instructions_url(self) -> str:
        return self._static_service_info["auth_instructions_url"]

    def tags(self) -> Dict[str, str]:
        return self._static_service_info["tags"]
