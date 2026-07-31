from pathlib import Path


FRONTEND = Path(__file__).parents[1] / "frontend" / "app.js"


def test_frontend_uses_genlayer_clients_and_no_backend_decision_engine():
    source = FRONTEND.read_text(encoding="utf-8")

    assert "createClient" in source
    assert "readClient" in source
    assert "writeClient" in source
    assert "writeContract" in source
    assert '"create_trade"' in source
    assert '"validate_trade"' in source
    assert '"resolve_dispute"' in source
    assert '"get_trade"' in source
    assert '"get_trust_passport"' in source
    assert '"get_full_trust_report"' in source
    assert "TransactionStatus.FINALIZED" in source
    assert "txExecutionResultName" in source
    assert "VITE_GENLAYER_NETWORK" in source
    assert "VITE_GENLAYER_CONTRACT_ADDRESS" in source
    assert "fetch(" not in source
