import requests

def test_types(client):
    path = '/api/v1/types/'
    resp = client.get(path)
    assert resp.status_code == 200
