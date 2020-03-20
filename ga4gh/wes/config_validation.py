from cerberus import Validator


def validate_config(config, config_validation):
    validator = Validator()
    return validator.validate(config, config_validation)
