def test_create_validate_and_report(direct_vm, direct_deploy, direct_alice):
    contract = direct_deploy("contracts/trust_africa_intelligent_contract.py")
    direct_vm.sender = direct_alice

    trade_id = contract.create_trade(
        "TRADE-DIRECT-1",
        "Accra Retail Partners",
        "Lagos Textile Export Ltd",
        "Textiles",
        1000,
        "Invoice and tracking receipt",
    )
    assert trade_id == "TRADE-DIRECT-1"
    assert contract.validate_trade(trade_id, "Invoice and tracking receipt") == "APPROVED"

    report = contract.get_full_trust_report(trade_id)
    assert report["trade"]["escrow_decision"] == "RELEASE_FUNDS"
    assert report["seller_passport"]["trust_score"] == 96


def test_rejected_evidence_refunds_buyer(direct_vm, direct_deploy, direct_alice):
    contract = direct_deploy("contracts/trust_africa_intelligent_contract.py")
    direct_vm.sender = direct_alice
    contract.create_trade(
        "TRADE-DIRECT-2", "Accra Retail Partners", "Lagos Textile Export Ltd",
        "Textiles", 500, "fake invoice"
    )

    assert contract.validate_trade("TRADE-DIRECT-2", "fake invoice scam") == "REJECTED"
    report = contract.get_full_trust_report("TRADE-DIRECT-2")
    assert report["escrow"]["funds_refunded"] == "500"


def test_dispute_resolution_updates_reputation(direct_vm, direct_deploy, direct_alice):
    contract = direct_deploy("contracts/trust_africa_intelligent_contract.py")
    direct_vm.sender = direct_alice
    contract.create_trade(
        "TRADE-DIRECT-3", "Accra Retail Partners", "Lagos Textile Export Ltd",
        "Textiles", 800, "pending"
    )

    decision = contract.resolve_dispute(
        "TRADE-DIRECT-3", "Goods not delivered", "Seller response", "tracking proof"
    )
    assert decision == "RELEASE_FUNDS"
    assert contract.get_trust_passport("Lagos Textile Export Ltd")["disputes_won"] == 5
