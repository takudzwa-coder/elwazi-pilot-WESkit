import json

def test_get_service_info(client):
    """Test information about the transcriber library on the backend is provided"""
    print("test service-info")
    response = client.get("/ga4gh/wes/v1/service-info")
    print(response)
    assert response.status_code == 200

#def test_post_run(client):
#    """Test information about the transcriber library on the backend is provided"""
#    workflow_params = json.dumps({"text":"blablablubb"})
#    parts =  [("workflow_params", workflow_params),
#        ("workflow_type", "Snakemake"),
#        ("workflow_type_version", "5.8.2"),
#        ("workflow_url", "/home/twardzso/workspace/wesnake/test/wf1/Snakefile")]
#    response = client.post("/ga4gh/wes/v1/runs", data=parts)
#    print(response)
#    assert response.status_code == 200