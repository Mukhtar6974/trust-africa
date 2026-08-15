from pathlib import Path


FRONTEND = (Path(__file__).parents[1] / "frontend" / "index.html").read_text(encoding="utf-8")


def test_browser_uses_wallet_signed_genlayer_writes_and_real_reads():
    assert 'client.writeContract({' in FRONTEND
    assert 'client.readContract({' in FRONTEND
    assert 'writeAndFinalize("create_trade"' in FRONTEND
    assert 'writeAndFinalize("validate_trade"' in FRONTEND
    assert 'writeAndFinalize("resolve_dispute"' in FRONTEND
    assert 'writeAndFinalize("issue_trust_passport"' in FRONTEND
    assert 'readContract("get_full_trust_report"' in FRONTEND


def test_browser_does_not_send_authoritative_writes_to_flask():
    assert 'fetch("http://127.0.0.1:5000/ai-judge"' not in FRONTEND
    assert 'fetch("http://127.0.0.1:5000/resolve-dispute"' not in FRONTEND
