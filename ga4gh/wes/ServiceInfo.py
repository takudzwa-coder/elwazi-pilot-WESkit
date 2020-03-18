from bson.son import SON


class ServiceInfo:
    def __init__(self, service_info,  swagger, database):
        self._service_info = service_info
        self._db = database
        self._swagger = swagger

    def get_workflow_type_versions(self):
        workflow_type_versions = self._service_info["workflow_type_versions"]
        return workflow_type_versions

    def get_supported_wes_versions(self):
        supported_wes_versions = [self._swagger["info"]["version"]]
        return supported_wes_versions
    
    def get_supported_filesystem_protocols(self):
        supported_filesystem_protocols = self._service_info["supported_filesystem_protocols"]
        return supported_filesystem_protocols
    
    def get_workflow_engine_versions(self):
        workflow_engine_versions = self._service_info["workflow_engine_versions"]
        return workflow_engine_versions
    
    def get_default_workflow_engine_parameters(self):
        default_workflow_engine_parameters = self._service_info["default_workflow_engine_parameters"]
        return default_workflow_engine_parameters
    
    def get_system_state_counts(self):
        aggregate = [
            {"$unwind": "$run_status"},
            {"$group": {"_id": "$run_status", "num_states": {"$sum": 1}}},
            {"$sort": SON([("_id", 1), ("num_states", -1)])}
            ]
        system_state_counts = self._db.aggregate_states(aggregate)
        return system_state_counts
    
    def get_auth_instructions_url(self):
        auth_instruction_url = self._service_info["auth_instruction_url"]
        return auth_instruction_url
    
    def get_contact_info_url(self):
        contact_info = self._service_info["contact_info_url"]
        return contact_info
    
    def get_tags(self):
        tags = self._service_info["tags"]
        return tags
