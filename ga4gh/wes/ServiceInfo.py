from bson.son import SON


class ServiceInfo:
    def __init__(self, service_info,  swagger, database):
        self._static_service_info = service_info
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
            {"$group": {"_id": "$run_status", "num_states": {"$sum": 1}}},
            {"$sort": SON([("_id", 1), ("num_states", -1)])}
            ]
        return self._db.aggregate_states(aggregate)

    def get_auth_instructions_url(self):
        return self._static_service_info["auth_instructions_url"]
    
    def get_contact_info_url(self):
        return self._static_service_info["contact_info_url"]
    
    def get_tags(self):
        return self._static_service_info["tags"]
