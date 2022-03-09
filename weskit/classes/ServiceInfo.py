#  Copyright (c) 2021. Berlin Institute of Health (BIH) and Deutsches Krebsforschungszentrum (DKFZ).
#
#  Distributed under the MIT License. Full text at
#
#      https://gitlab.com/one-touch-pipeline/weskit/api/-/blob/master/LICENSE
#
#  Authors: The WESkit Team
import datetime
from typing import Dict, List

from weskit.classes.WorflowEngineFactory import ConfParameters
from weskit.classes.Database import Database


class ServiceInfo:
    """Note that the static_service_info is not validated in here. External
    validation is required. ServiceInfo returns whatever it gets as static
    service info."""
    def __init__(self, static_service_info, swagger, database: Database):
        self._static_service_info = static_service_info
        self._db = database
        self._swagger = swagger

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
        return self._static_service_info["workflow_type_versions"]

    def supported_wes_versions(self) -> List[str]:
        return [self._swagger["info"]["version"]]

    def supported_filesystem_protocols(self) -> List[str]:
        return self._static_service_info["supported_filesystem_protocols"]

    def workflow_engine_versions(self) -> Dict[str, List[str]]:
        return dict(map(lambda k: (k, list(self.default_workflow_engine_parameters()[k].keys())),
                        self.default_workflow_engine_parameters().keys()))

    def default_workflow_engine_parameters(self) \
            -> Dict[str, Dict[str, ConfParameters]]:
        """
        We use the "api" field internally, to configure in the server which parameters are allowed
        to be set via the REST API. Forbidden parameters are not reported via the ServiceInfo
        """
        return {engine: {version: [{"name": parameter["name"], "value": parameter["value"]}
                                   for parameter in parameters
                                   if parameter["api"]]
                         for version, parameters in by_version.items()}
                for engine, by_version
                in self._static_service_info["default_workflow_engine_parameters"].items()}

    def system_state_counts(self) -> Dict[str, int]:
        return self._db.count_states()

    def auth_instructions_url(self) -> str:
        return self._static_service_info["auth_instructions_url"]

    def tags(self) -> Dict[str, str]:
        return self._static_service_info["tags"]
