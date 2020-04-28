def test_get_list_runs(test_app, database_connection):
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
            'type': 'parameterType1'
        }, {
            'default_value': 'defaultValue2',
            'name': 'parameterName2',
            'type': 'parameterType2'
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
        'workflow_engine_versions': {'Snakemake': '5.8.2'},
        'workflow_type_versions': {'Snakemake': {"workflow_type_version": ['5']}}
    }

