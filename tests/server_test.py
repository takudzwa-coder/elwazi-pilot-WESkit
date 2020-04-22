
def test_get_list_runs(test_app):
    response = test_app.get("/ga4gh/wes/v1/runs")
    assert response.status_code == 200


def test_get_service_info(test_app):
    response = test_app.get("/ga4ga/wes/v1/service_info")
    print(response)
