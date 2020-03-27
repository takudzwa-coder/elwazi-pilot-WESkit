from ga4gh.wes.server import GetServiceInfo


def test_get_list_runs(test_app):
    response = test_app.get("/ga4gh/wes/v1/runs")
    print(response)
    assert response.status_code == 200


def test_get_service_info(static_service_info, service_info_validation):
    GetServiceInfo(static_service_info, service_info_validation)
