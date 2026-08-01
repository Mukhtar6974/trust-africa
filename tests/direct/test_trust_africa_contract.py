import pytest


CONTRACT_PATH = "contracts/trust_africa_intelligent_contract.py"


def create_trade(contract, buyer_address, seller_address, trade_id="T-1", amount=1000):
    return contract.create_trade(
        trade_id,
        "Accra Retail Partners",
        "Lagos Textile Export Ltd",
        buyer_address,
        seller_address,
        "Premium textiles",
        amount,
        "Initial trade evidence",
    )


def configure_review_flow(direct_vm, dispute_decision="RELEASE_FUNDS"):
    direct_vm.clear_mocks()
    direct_vm.mock_llm(
        "trade verification expert",
        '{"decision":"REVIEW_REQUIRED","confidence":70,"risk":"MEDIUM","reason":"Needs more evidence"}',
    )
    direct_vm.mock_llm(
        "dispute resolution expert",
        '{"decision":"%s","reason":"Dispute evidence was reviewed"}' % dispute_decision,
    )


def test_create_trade_stores_addresses_and_initial_state(
    direct_vm, direct_deploy, direct_alice, direct_bob
):
    contract = direct_deploy(CONTRACT_PATH)
    direct_vm.sender = direct_alice

    create_trade(contract, direct_alice, direct_bob)

    trade = contract.get_trade("T-1")
    report = contract.get_full_trust_report("T-1")
    assert trade["buyer_address"].lower() == ("0x" + bytes(direct_alice).hex()).lower()
    assert trade["seller_address"].lower() == ("0x" + bytes(direct_bob).hex()).lower()
    assert trade["status"] == "CREATED"
    assert trade["validation_completed"] is False
    assert trade["dispute_resolved"] is False
    assert trade["settled"] is False
    assert trade["settlement_accounted"] is False
    assert report["escrow"]["funds_held"] == "1000"


def test_only_buyer_can_create_trade(direct_vm, direct_deploy, direct_alice, direct_bob):
    contract = direct_deploy(CONTRACT_PATH)
    direct_vm.sender = direct_bob

    with pytest.raises(Exception, match="Only the buyer"):
        create_trade(contract, direct_alice, direct_bob)


def test_validate_trade_rejects_unauthorized_caller(
    direct_vm, direct_deploy, direct_alice, direct_bob, direct_charlie
):
    contract = direct_deploy(CONTRACT_PATH)
    direct_vm.sender = direct_alice
    create_trade(contract, direct_alice, direct_bob)
    direct_vm.sender = direct_charlie

    with pytest.raises(Exception, match="Only the buyer or seller"):
        contract.validate_trade("T-1", "Evidence from an unauthorized caller")


def test_approved_validation_settles_once_and_updates_reputation(
    direct_vm, direct_deploy, direct_alice, direct_bob
):
    contract = direct_deploy(CONTRACT_PATH)
    direct_vm.sender = direct_alice
    create_trade(contract, direct_alice, direct_bob, amount=1250)
    buyer_before = contract.get_trust_passport("Accra Retail Partners")
    seller_before = contract.get_trust_passport("Lagos Textile Export Ltd")

    decision = contract.validate_trade("T-1", "Signed receipt and courier tracking")

    assert decision == "APPROVED"
    trade = contract.get_trade("T-1")
    report = contract.get_full_trust_report("T-1")
    buyer_after = contract.get_trust_passport("Accra Retail Partners")
    seller_after = contract.get_trust_passport("Lagos Textile Export Ltd")
    assert trade["validation_completed"] is True
    assert trade["settled"] is True
    assert trade["status"] == "SETTLED"
    assert trade["settlement_accounted"] is True
    assert report["escrow"] == {"funds_released": "1250", "funds_refunded": "0", "funds_held": "0"}
    assert buyer_after["completed_trades"] == buyer_before["completed_trades"] + 1
    assert seller_after["successful_deliveries"] == seller_before["successful_deliveries"] + 1

    with pytest.raises(Exception, match="already settled|already completed"):
        contract.validate_trade("T-1", "Replay evidence")

    replay_report = contract.get_full_trust_report("T-1")
    assert replay_report["escrow"] == report["escrow"]
    assert contract.get_trust_passport("Lagos Textile Export Ltd")["successful_deliveries"] == seller_after[
        "successful_deliveries"
    ]


def test_dispute_requires_review_required_trade(
    direct_vm, direct_deploy, direct_alice, direct_bob
):
    contract = direct_deploy(CONTRACT_PATH)
    direct_vm.sender = direct_alice
    create_trade(contract, direct_alice, direct_bob)
    contract.validate_trade("T-1", "Signed delivery evidence")

    with pytest.raises(Exception, match="already settled|only permitted"):
        contract.resolve_dispute("T-1", "Claim", "Response", "Evidence")


def test_rejected_validation_refunds_once_and_debits_seller_reputation(
    direct_vm, direct_deploy, direct_alice, direct_bob
):
    direct_vm.clear_mocks()
    direct_vm.mock_llm(
        "trade verification expert",
        '{"decision":"REJECTED","confidence":96,"risk":"HIGH","reason":"Fraud evidence"}',
    )
    contract = direct_deploy(CONTRACT_PATH)
    direct_vm.sender = direct_alice
    create_trade(contract, direct_alice, direct_bob, amount=400)
    seller_before = contract.get_trust_passport("Lagos Textile Export Ltd")["trust_score"]

    assert contract.validate_trade("T-1", "Fabricated delivery evidence") == "REJECTED"
    trade = contract.get_trade("T-1")
    report = contract.get_full_trust_report("T-1")
    assert trade["settled"] is True
    assert trade["escrow_decision"] == "REFUND_BUYER"
    assert report["escrow"] == {"funds_released": "0", "funds_refunded": "400", "funds_held": "0"}
    assert contract.get_trust_passport("Lagos Textile Export Ltd")["trust_score"] == seller_before - 15

    with pytest.raises(Exception, match="already settled|already completed"):
        contract.validate_trade("T-1", "Replay evidence")
    assert contract.get_full_trust_report("T-1")["escrow"] == report["escrow"]


def test_review_dispute_authorization_replay_and_exact_once_settlement(
    direct_vm, direct_deploy, direct_alice, direct_bob, direct_charlie
):
    configure_review_flow(direct_vm)
    contract = direct_deploy(CONTRACT_PATH)
    direct_vm.sender = direct_alice
    create_trade(contract, direct_alice, direct_bob, amount=900)
    assert contract.validate_trade("T-1", "Ambiguous evidence") == "REVIEW_REQUIRED"

    review = contract.get_trade("T-1")
    assert review["status"] == "REVIEW_REQUIRED"
    assert review["settled"] is False
    assert contract.get_full_trust_report("T-1")["escrow"]["funds_held"] == "900"

    direct_vm.sender = direct_charlie
    with pytest.raises(Exception, match="Only the buyer or seller"):
        contract.resolve_dispute("T-1", "Claim", "Response", "Evidence")

    direct_vm.sender = direct_alice
    assert contract.resolve_dispute("T-1", "Claim", "Response", "Evidence") == "RELEASE_FUNDS"
    settled = contract.get_trade("T-1")
    report = contract.get_full_trust_report("T-1")
    assert settled["dispute_resolved"] is True
    assert settled["settled"] is True
    assert settled["status"] == "SETTLED"
    assert report["escrow"] == {"funds_released": "900", "funds_refunded": "0", "funds_held": "0"}

    with pytest.raises(Exception, match="already settled|already resolved"):
        contract.resolve_dispute("T-1", "Replay claim", "Replay response", "Replay evidence")
    assert contract.get_full_trust_report("T-1")["escrow"] == report["escrow"]


def test_manual_review_is_terminal_for_dispute_processing(
    direct_vm, direct_deploy, direct_alice, direct_bob
):
    configure_review_flow(direct_vm, dispute_decision="MANUAL_REVIEW")
    contract = direct_deploy(CONTRACT_PATH)
    direct_vm.sender = direct_alice
    create_trade(contract, direct_alice, direct_bob, amount=600)
    contract.validate_trade("T-1", "Ambiguous evidence")

    assert contract.resolve_dispute("T-1", "Claim", "Response", "Evidence") == "MANUAL_REVIEW"
    trade = contract.get_trade("T-1")
    report = contract.get_full_trust_report("T-1")
    assert trade["status"] == "MANUAL_REVIEW"
    assert trade["dispute_resolved"] is True
    assert trade["settled"] is False
    assert report["escrow"] == {"funds_released": "0", "funds_refunded": "0", "funds_held": "600"}

    with pytest.raises(Exception, match="already resolved|not permitted"):
        contract.resolve_dispute("T-1", "Replay claim", "Replay response", "Replay evidence")


def test_owner_only_reputation_and_passport_writes(
    direct_vm, direct_deploy, direct_owner, direct_alice
):
    contract = direct_deploy(CONTRACT_PATH)
    direct_vm.sender = direct_owner
    before = contract.get_trust_passport("Lagos Textile Export Ltd")["trust_score"]
    assert contract.update_reputation("Lagos Textile Export Ltd", 5) == before + 5
    assert contract.issue_trust_passport("Lagos Textile Export Ltd") == "VERIFIED"

    direct_vm.sender = direct_alice
    with pytest.raises(Exception, match="Only the contract owner"):
        contract.update_reputation("Lagos Textile Export Ltd", 50)
    with pytest.raises(Exception, match="Only the contract owner"):
        contract.issue_trust_passport("Lagos Textile Export Ltd")


def test_full_report_exposes_state_machine_and_consensus_contract(
    direct_vm, direct_deploy, direct_alice, direct_bob
):
    contract = direct_deploy(CONTRACT_PATH)
    direct_vm.sender = direct_alice
    create_trade(contract, direct_alice, direct_bob)

    report = contract.get_full_trust_report("T-1")

    assert report["state_machine"] == {
        "status": "CREATED",
        "validation_completed": False,
        "dispute_resolved": False,
        "settled": False,
        "settlement_accounted": False,
    }
    assert "REVIEW_REQUIRED" in report["consensus_info"]["allowed_decisions"]["validate_trade"]
    assert "MANUAL_REVIEW" in report["consensus_info"]["allowed_decisions"]["resolve_dispute"]
