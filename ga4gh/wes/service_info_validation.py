from cerberus import Validator


def validate_service_info(static_service_info, service_info_validation):
    validator = Validator()
    return validator.validate(static_service_info, service_info_validation)
