from bson.son import SON
from ga4gh.wes.RunStatus import RunStatus


class ServiceInfo:
    '''Note that the static_service_info is not validated in here. External
    validaton is required. ServiceInfo returns whatever it gets as static
    service info.'''
    def __init__(self, static_service_info, swagger, database):
        self._static_service_info = static_service_info
        self._db = database
        self._swagger = swagger

    def get_workflow_type_versions(self):
        return self._static_service_info["workflow_type_versions"]

    def get_supported_wes_versions(self):
        return [self._swagger["info"]["version"]]

    def get_supported_filesystem_protocols(self):
        return self._static_service_info["supported_filesystem_protocols"]

    def get_workflow_engine_versions(self):
        return self._static_service_info["workflow_engine_versions"]

    def get_default_workflow_engine_parameters(self):
        return self._static_service_info["default_workflow_engine_parameters"]

    def get_system_state_counts(self):
        aggregate = [
            {"$unwind": "$run_status"},
            {"$group": {"_id": "$run_status", "status_count": {"$sum": 1}}},
            {"$sort": SON([("_id", 1), ("status_count", -1)])}
            ]
        counts = self._db.aggregate_states(aggregate)
        for status in RunStatus:
            if status.name not in counts:
                counts[status.name] = 0
        return counts

    def get_auth_instructions_url(self):
        return self._static_service_info["auth_instructions_url"]

    def get_contact_info_url(self):
        return self._static_service_info["contact_info_url"]

    def get_tags(self):
        return self._static_service_info["tags"]
