import os

from ghoststack.auth import check_http_auth, check_socket_auth, credentials_valid


def test_credentials_with_env(monkeypatch):
    monkeypatch.setenv("GHOSTSTACK_DASHBOARD_USER", "lab")
    monkeypatch.setenv("GHOSTSTACK_DASHBOARD_PASSWORD", "secret")
    monkeypatch.setenv("GHOSTSTACK_DASHBOARD_AUTH", "true")
    assert credentials_valid("lab", "secret")
    assert not credentials_valid("lab", "wrong")


def test_socket_token_auth(monkeypatch):
    monkeypatch.setenv("GHOSTSTACK_DASHBOARD_USER", "lab")
    monkeypatch.setenv("GHOSTSTACK_DASHBOARD_PASSWORD", "secret")
    monkeypatch.setenv("GHOSTSTACK_DASHBOARD_TOKEN", "tok123")
    monkeypatch.setenv("GHOSTSTACK_DASHBOARD_AUTH", "true")
    assert check_socket_auth({"token": "tok123"})
    assert not check_socket_auth({"token": "bad"})
