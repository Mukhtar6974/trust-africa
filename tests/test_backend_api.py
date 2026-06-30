from backend.server import app


def test_trade_create_get_returns_unique_real_trade_records():
    client = app.test_client()

    first = client.get("/trade/create").get_json()
    second = client.get("/trade/create").get_json()

    assert first["trade_id"] != "TRADE003"
    assert second["trade_id"] != "TRADE003"
    assert first["trade_id"] != second["trade_id"]
    assert first["decision"] in {"APPROVED", "REJECTED", "REVIEW_REQUIRED"}
    assert "escrow" in first


def test_escrow_status_route_matches_frontend_contract():
    client = app.test_client()
    data = client.get("/escrow-status").get_json()

    assert data["escrow_status"] in {"RELEASED", "REFUNDED", "HELD"}
    assert data["ai_decision"] in {"RELEASE_FUNDS", "REFUND_BUYER", "HOLD_ESCROW"}
    assert "condition" in data
    assert "funds_released" in data
