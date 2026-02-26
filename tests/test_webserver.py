import json

import pytest

import webserver


@pytest.fixture
def client(tmp_path, monkeypatch):
    config_file = tmp_path / "config.json"
    auth_file = tmp_path / "auth.json"

    monkeypatch.setattr(webserver, "CONFIG_FILE", str(config_file))
    monkeypatch.setattr(webserver, "AUTH_FILE", str(auth_file))

    webserver.app.config["TESTING"] = True
    with webserver.app.test_client() as test_client:
        yield test_client


def test_allowed_file_accepts_known_image_extensions():
    assert webserver.allowed_file("photo.png") is True
    assert webserver.allowed_file("photo.JPG") is True
    assert webserver.allowed_file("notes.txt") is False
    assert webserver.allowed_file("no_extension") is False


def test_protected_route_requires_authentication(client):
    response = client.get("/api/config")

    assert response.status_code == 401
    payload = response.get_json()
    assert payload["success"] is False


def test_auth_login_and_fetch_config(client):
    login_response = client.post(
        "/api/auth/login",
        json={"username": webserver.DEFAULT_USERNAME, "password": webserver.DEFAULT_PASSWORD},
    )
    assert login_response.status_code == 200
    assert login_response.get_json()["success"] is True

    config_response = client.get("/api/config")
    assert config_response.status_code == 200
    assert config_response.get_json()["background"] == "bg.png"


def test_update_config_persists_to_file(client):
    login_response = client.post(
        "/api/auth/login",
        json={"username": webserver.DEFAULT_USERNAME, "password": webserver.DEFAULT_PASSWORD},
    )
    assert login_response.status_code == 200

    updated_config = {
        "background": "uploads/new-bg.png",
        "buttons": [{"id": 1, "action_type": "media", "action_value": "PLAY"}],
    }

    update_response = client.post("/api/config", json=updated_config)
    assert update_response.status_code == 200
    assert update_response.get_json()["success"] is True

    with open(webserver.CONFIG_FILE, "r") as saved_config:
        assert json.load(saved_config) == updated_config
