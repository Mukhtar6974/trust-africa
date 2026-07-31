from backend.server import app


def test_flask_serves_the_frontend_without_trade_state():
    client = app.test_client()

    response = client.get("/")

    assert response.status_code == 200
    assert b"GenLayer" in response.data


def test_config_exposes_deployment_settings_only():
    client = app.test_client()

    response = client.get("/config")
    data = response.get_json()

    assert response.status_code == 200
    assert data["network"]
    assert "contract_address" in data


def test_health_identifies_on_chain_source():
    client = app.test_client()

    data = client.get("/health").get_json()

    assert data == {"status": "ok", "source": "static frontend + GenLayer contract"}


def test_state_changing_legacy_routes_are_not_available():
    client = app.test_client()

    assert client.post("/ai-judge", json={}).status_code == 404
    assert client.post("/trade/create", json={}).status_code == 404
    assert client.post("/resolve-dispute", json={}).status_code == 404
