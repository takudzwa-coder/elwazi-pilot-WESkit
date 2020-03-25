from bson.son import SON


class ServiceInfo:
    def __init__(self, static_service_info, swagger, database):
        self._static_service_info = static_service_info
        self._db = database
        self._swagger = swagger

    def get_workflow_type_versions(self):
        static_workflow_type_versions = self._static_service_info["workflow_type_versions"]
        return static_workflow_type_versions

    def get_supported_wes_versions(self):
        static_supported_wes_versions = [self._swagger["info"]["version"]]
        return static_supported_wes_versions
    
    def get_supported_filesystem_protocols(self):
        static_supported_filesystem_protocols = self._static_service_info["supported_filesystem_protocols"]
        return static_supported_filesystem_protocols
    
    def get_workflow_engine_versions(self):
        static_workflow_engine_versions = self._static_service_info["workflow_engine_versions"]
        return static_workflow_engine_versions
    
    def get_default_workflow_engine_parameters(self):
        static_default_workflow_engine_parameters = self._static_service_info["default_workflow_engine_parameters"]
        return static_default_workflow_engine_parameters
    
    def get_system_state_counts(self):
        aggregate = [
            {"$unwind": "$run_status"},
            {"$group": {"_id": "$run_status", "num_states": {"$sum": 1}}},
            {"$sort": SON([("_id", 1), ("num_states", -1)])}
            ]
        system_state_counts = self._db.aggregate_states(aggregate)
        return system_state_counts
    
    def get_auth_instructions_url(self):
        static_auth_instructions_url = self._static_service_info["auth_instructions_url"]
        return static_auth_instructions_url
    
    def get_contact_info_url(self):
        static_contact_info = self._static_service_info["contact_info_url"]
        return static_contact_info
    
    def get_tags(self):
        static_tags = self._static_service_info["tags"]
        return static_tags
