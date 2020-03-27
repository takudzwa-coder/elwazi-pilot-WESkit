from cerberus import Validator
from flask import current_app


def validate_config(config, config_validation):
    validators = Validator(config_validation)
    validators.validate(document={"config_validation": config})
    if validators.errors:
        return validators.errors
    else:
        return True


def validate_service_info(static_service_info, service_info_validation):
    validators = Validator(service_info_validation)
    return validators.validate(document={"service_info_validation": static_service_info})
