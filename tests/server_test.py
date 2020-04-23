
def test_get_list_runs(test_app):
    response = test_app.get("/ga4gh/wes/v1/runs")
    assert response.status_code == 200


def test_get_service_info(test_app):
    response = test_app.get("/ga4gh/wes/v1/service-info")
    assert response.status_code == 200
    assert response.json == {
        'auth_instructions_url': 'https://somewhere.org',
        'contact_info_url': 'your@email.de',
        'default_workflow_engine_parameters': [{
            'default_value': 'defaultValue1',
            'name': 'parameterName1',
            'parameter_type': 'parameterType1'
        }, {
            'default_value': 'defaultValue2',
            'name': 'parameterName2',
            'parameter_type': 'parameterType2'
        }],
        'supported_filesystem_protocols': ['s3', 'posix'],
        'supported_wes_versions': ['1.0.0'],
        'system_state_counts': {
            'CANCELED': 0,
            'CANCELING': 0,
            'COMPLETE': 0,
            'EXECUTOR_ERROR': 0,
            'INITIALIZING': 0,
            'PAUSED': 0,
            'QUEUED': 0,
            'RUNNING': 0,
            'SYSTEM_ERROR': 0,
            'UNKNOWN': 0
        },
        'tags': {'tag1': 'value1', 'tag2': 'value2'},
        'workflow_engine_versions': {'Snakemake': ['5.8.2']},
        'workflow_type_versions': {'Snakemake': {"workflow_type_version": ['5']}}
    }
#
# {
#     "workflow_type_versions": {
#         "additionalProp1": {
#             "workflow_type_version": [
#                 "string"
#             ]
#         },
#         "additionalProp2": {
#             "workflow_type_version": [
#                 "string"
#             ]
#         },
#         "additionalProp3": {
#             "workflow_type_version": [
#                 "string"
#             ]
#         }
#     },
#     "supported_wes_versions": [
#         "string"
#     ],
#     "supported_filesystem_protocols": [
#         "string"
#     ],
#     "workflow_engine_versions": {
#         "additionalProp1": "string",
#         "additionalProp2": "string",
#         "additionalProp3": "string"
#     },
#     "default_workflow_engine_parameters": [
#         {
#             "name": "string",
#             "type": "string",
#             "default_value": "string"
#         }
#     ],
#     "system_state_counts": {
#         "additionalProp1": 0,
#         "additionalProp2": 0,
#         "additionalProp3": 0
#     },
#     "auth_instructions_url": "string",
#     "contact_info_url": "string",
#     "tags": {
#         "additionalProp1": "string",
#         "additionalProp2": "string",
#         "additionalProp3": "string"
#     }
# }