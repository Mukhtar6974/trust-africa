from backend.server import app, gateway


def test_backend_reads_trade_from_genlayer_gateway(monkeypatch):
    calls = []

    def fake_read(method, *args):
        calls.append((method, args))
        return {"trade_id": args[0], "source": "contract"}

    monkeypatch.setattr(gateway, "read", fake_read)
    response = app.test_client().get("/trade/T-100")

    assert response.status_code == 200
    assert response.get_json() == {"trade_id": "T-100", "source": "contract"}
    assert calls == [("get_trade", ("T-100",))]


def test_backend_reads_full_report_from_contract(monkeypatch):
    monkeypatch.setattr(
        gateway,
        "read",
        lambda method, trade_id: {"method": method, "trade": {"trade_id": trade_id}},
    )
    data = app.test_client().get("/full-trust-report/T-200").get_json()
    assert data["method"] == "get_full_trust_report"
    assert data["trade"]["trade_id"] == "T-200"


def test_backend_rejects_unsigned_state_changes():
    response = app.test_client().post("/ai-judge", json={"trade_id": "T-1"})
    assert response.status_code == 409
    assert "wallet-signed" in response.get_json()["error"]
