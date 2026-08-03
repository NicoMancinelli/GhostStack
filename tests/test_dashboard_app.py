import os

os.environ["GHOSTSTACK_DASHBOARD_AUTH"] = "false"

from dashboard.app import app, _init_socketio


def test_index_loads():
    _init_socketio()
    client = app.test_client()
    response = client.get("/")
    assert response.status_code == 200
    assert b"GHOSTSTACK" in response.data


def test_api_health():
    _init_socketio()
    client = app.test_client()
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.is_json
