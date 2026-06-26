# Tests for the local Flask preview TrustEngine (backend/trust_engine.py).
#
# The TrustEngine is a deterministic in-memory simulation used to keep the
# demo fast and dependency-free. It mirrors state transitions but does NOT
# use GenLayer consensus or LLM calls.
#
# The authoritative on-chain logic lives in:
#   contracts/trust_africa_intelligent_contract.py
#
# That contract uses gl.vm.run_nondet_unsafe for non-deterministic AI
# validator consensus. See tests/direct/ for contract-level tests.

from backend.trust_engine import TrustEngine


def test_approved_trade_updates_passports_and_releases_escrow():
    engine = TrustEngine()
    seller_before = engine.passport("Lagos Textile Export Ltd")["trust_score"]
    buyer_before = engine.passport("Accra Retail Partners")["trust_score"]

    result = engine.adjudicate_trade({
        "trade_id": "TRADE-APPROVED",
        "buyer": "Accra Retail Partners",
        "seller": "Lagos Textile Export Ltd",
        "product": "Textiles",
        "amount": 1000,
        "evidence": "Invoice and delivery tracking receipt",
    })

    assert result["decision"] == "APPROVED"
    assert result["escrow_decision"] == "RELEASE_FUNDS"
    assert result["seller_passport"]["trust_score"] == min(100, seller_before + 5)
    assert result["buyer_passport"]["trust_score"] == min(100, buyer_before + 2)
    assert result["escrow"]["funds_released"] == 6500


def test_fraud_rejects_trade_and_penalizes_seller():
    engine = TrustEngine()
    seller_before = engine.passport("Lagos Textile Export Ltd")["trust_score"]
    result = engine.adjudicate_trade({
        "trade_id": "TRADE-REJECTED",
        "buyer": "Accra Retail Partners",
        "seller": "Lagos Textile Export Ltd",
        "product": "Textiles",
        "amount": 500,
        "evidence": "Fake invoice linked to a scam",
    })

    assert result["decision"] == "REJECTED"
    assert result["escrow_decision"] == "REFUND_BUYER"
    assert result["seller_passport"]["trust_score"] == seller_before - 15
    assert result["escrow"]["funds_refunded"] == 500


def test_inconclusive_trade_holds_escrow():
    engine = TrustEngine()
    result = engine.adjudicate_trade({
        "trade_id": "TRADE-REVIEW",
        "buyer": "Nairobi Agro Supply",
        "seller": "Kigali Logistics Hub",
        "product": "Logistics",
        "amount": 750,
        "evidence": "Seller sent a message",
    })

    assert result["decision"] == "REVIEW_REQUIRED"
    assert result["escrow_decision"] == "HOLD_ESCROW"
    assert result["escrow"]["funds_held"] == 750


def test_dispute_uses_claim_response_and_evidence():
    engine = TrustEngine()
    engine.adjudicate_trade({
        "trade_id": "TRADE-DISPUTE",
        "buyer": "Accra Retail Partners",
        "seller": "Lagos Textile Export Ltd",
        "product": "Textiles",
        "amount": 900,
        "evidence": "Awaiting confirmation",
    })
    result = engine.resolve_dispute({
        "trade_id": "TRADE-DISPUTE",
        "buyer_claim": "Goods not delivered",
        "seller_response": "Delivery completed",
        "evidence": "Tracking proof attached",
    })

    assert result["decision"] == "RELEASE_FUNDS"
    assert result["seller_passport"]["disputes_won"] == 5

