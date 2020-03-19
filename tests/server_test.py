from ga4gh.wes.server import GetServiceInfo


def test_get_list_runs(test_app):
    response = test_app.get("/ga4gh/wes/v1/runs")
    print(response)
    assert response.status_code == 200


# This is for testing the validation
def test_get_service_info(service_info, service_info_validation):
    GetServiceInfo(service_info, service_info_validation)
