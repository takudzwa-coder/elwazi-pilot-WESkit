def test_get_list_runs(test_app):
    response = test_app.get("/ga4gh/wes/v1/runs")
    print(response)
    assert response.status_code == 200
