from cerberus import Validator


def validate_service_info(service_info, service_info_validation):
    validator = Validator()
    return validator.validate(service_info, service_info_validation)
