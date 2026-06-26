# Direct-mode contract tests for Trust Africa.
#
# These tests exercise the GenLayer intelligent contract logic in direct
# (single-node, no-consensus) mode. The core decision functions —
# validate_trade, resolve_dispute, issue_trust_passport — use
# gl.eq_principle.prompt_comparative internally, so exact output values vary.
#
# Assertions check that:
#   1. Return values are within the documented allowed set
#   2. On-chain state transitions are consistent with whatever decision the AI made
#   3. Passport score deltas match the expected adjustment rules
#
# To exercise real multi-validator consensus, use integration tests.

VALID_TRADE_DECISIONS    = {"APPROVED", "REJECTED", "REVIEW_REQUIRED"}
VALID_DISPUTE_DECISIONS  = {"RELEASE_FUNDS", "REFUND_BUYER", "MANUAL_REVIEW"}
VALID_PASSPORT_STATUSES  = {"VERIFIED", "WATCHLIST", "UNVERIFIED"}


# ---------------------------------------------------------------------------
# validate_trade — evidence scenarios
# ---------------------------------------------------------------------------

def test_valid_evidence_returns_allowed_decision(direct_vm, direct_deploy, direct_alice):
    """Clear delivery evidence: AI should decide within the allowed set."""
    contract = direct_deploy("contracts/trust_africa_intelligent_contract.py")
    direct_vm.sender = direct_alice

    contract.create_trade(
        "T-VALID-1",
        "Accra Retail Partners",
        "Lagos Textile Export Ltd",
        "Premium textiles",
        1000,
        "Delivery confirmed with official invoice and courier tracking number KE-4821",
    )
    decision = contract.validate_trade(
        "T-VALID-1",
        "Delivery confirmed with official invoice and courier tracking number KE-4821",
    )
    assert decision in VALID_TRADE_DECISIONS, f"Unexpected decision: {decision}"

    trade = contract.get_trade("T-VALID-1")
    assert trade["decision"] == decision
    assert trade["certificate_status"] in {"VERIFIED", "REJECTED", "PENDING"}
    assert trade["escrow_decision"] in {"RELEASE_FUNDS", "REFUND_BUYER", "HOLD_ESCROW"}


def test_suspicious_evidence_returns_allowed_decision(direct_vm, direct_deploy, direct_alice):
    """Suspicious evidence with fraud signals: AI should decide within the allowed set."""
    contract = direct_deploy("contracts/trust_africa_intelligent_contract.py")
    direct_vm.sender = direct_alice

    contract.create_trade(
        "T-FRAUD-1",
        "Accra Retail Partners",
        "Lagos Textile Export Ltd",
        "Electronic goods",
        500,
        "This is a completely fabricated transaction; seller admitted to running a scam",
    )
    decision = contract.validate_trade(
        "T-FRAUD-1",
        "This is a completely fabricated transaction; seller admitted to running a scam",
    )
    assert decision in VALID_TRADE_DECISIONS, f"Unexpected decision: {decision}"


def test_ambiguous_evidence_returns_allowed_decision(direct_vm, direct_deploy, direct_alice):
    """Ambiguous evidence with no clear indicators: AI should decide within the allowed set."""
    contract = direct_deploy("contracts/trust_africa_intelligent_contract.py")
    direct_vm.sender = direct_alice

    contract.create_trade(
        "T-AMBIG-1",
        "Nairobi Agro Supply",
        "Kigali Logistics Hub",
        "Agricultural produce",
        750,
        "Seller says goods were sent last week",
    )
    decision = contract.validate_trade(
        "T-AMBIG-1",
        "Seller says goods were sent last week",
    )
    assert decision in VALID_TRADE_DECISIONS, f"Unexpected decision: {decision}"


def test_validate_trade_state_consistent_with_decision(direct_vm, direct_deploy, direct_alice):
    """Escrow and certificate state must be consistent with the decision returned."""
    contract = direct_deploy("contracts/trust_africa_intelligent_contract.py")
    direct_vm.sender = direct_alice

    contract.create_trade(
        "T-STATE-1",
        "Accra Retail Partners",
        "Lagos Textile Export Ltd",
        "Textiles",
        800,
        "Signed delivery receipt from licensed courier, invoice ref ACC-2024-019",
    )
    decision = contract.validate_trade(
        "T-STATE-1",
        "Signed delivery receipt from licensed courier, invoice ref ACC-2024-019",
    )
    trade = contract.get_trade("T-STATE-1")

    if decision == "APPROVED":
        assert trade["escrow_decision"] == "RELEASE_FUNDS"
        assert trade["certificate_status"] == "VERIFIED"
    elif decision == "REJECTED":
        assert trade["escrow_decision"] == "REFUND_BUYER"
        assert trade["certificate_status"] == "REJECTED"
    else:
        assert trade["escrow_decision"] == "HOLD_ESCROW"
        assert trade["certificate_status"] == "PENDING"


# ---------------------------------------------------------------------------
# resolve_dispute — dispute scenarios
# ---------------------------------------------------------------------------

def test_dispute_with_seller_proof_returns_allowed_decision(direct_vm, direct_deploy, direct_alice):
    """Seller has specific delivery proof: AI should decide within the allowed set."""
    contract = direct_deploy("contracts/trust_africa_intelligent_contract.py")
    direct_vm.sender = direct_alice

    contract.create_trade(
        "T-DISP-PROOF",
        "Accra Retail Partners",
        "Lagos Textile Export Ltd",
        "Textiles",
        900,
        "Pending",
    )
    decision = contract.resolve_dispute(
        "T-DISP-PROOF",
        "I never received the goods; no delivery was made to my warehouse",
        "Goods were delivered on March 15. Attached: signed delivery note ref DLV-9823 "
        "and courier tracking showing completion at 14:32 GMT",
        "Photo of signed delivery note and GPS timestamp from courier system",
    )
    assert decision in VALID_DISPUTE_DECISIONS, f"Unexpected decision: {decision}"


def test_dispute_without_seller_proof_returns_allowed_decision(direct_vm, direct_deploy, direct_alice):
    """Seller provides no proof: AI should decide within the allowed set."""
    contract = direct_deploy("contracts/trust_africa_intelligent_contract.py")
    direct_vm.sender = direct_alice

    contract.create_trade(
        "T-DISP-NOPROOF",
        "Accra Retail Partners",
        "Lagos Textile Export Ltd",
        "Textiles",
        600,
        "Pending",
    )
    decision = contract.resolve_dispute(
        "T-DISP-NOPROOF",
        "Goods were never delivered. It has been 30 days with no update.",
        "We sent it",
        "No additional evidence",
    )
    assert decision in VALID_DISPUTE_DECISIONS, f"Unexpected decision: {decision}"


def test_dispute_updates_passport_consistently(direct_vm, direct_deploy, direct_alice):
    """Whichever party wins the dispute, their passport's disputes_won must increment."""
    contract = direct_deploy("contracts/trust_africa_intelligent_contract.py")
    direct_vm.sender = direct_alice

    contract.create_trade(
        "T-DISP-PASS",
        "Accra Retail Partners",
        "Lagos Textile Export Ltd",
        "Electronics",
        1200,
        "Pending",
    )

    buyer_before = contract.get_trust_passport("Accra Retail Partners")["disputes_won"]
    seller_before = contract.get_trust_passport("Lagos Textile Export Ltd")["disputes_won"]

    decision = contract.resolve_dispute(
        "T-DISP-PASS",
        "Product was defective and not as described in the trade agreement",
        "Product met all specifications; we have a quality certificate",
        "Independent lab report showing product conforms to spec",
    )
    assert decision in VALID_DISPUTE_DECISIONS

    buyer_after  = contract.get_trust_passport("Accra Retail Partners")["disputes_won"]
    seller_after = contract.get_trust_passport("Lagos Textile Export Ltd")["disputes_won"]

    if decision == "RELEASE_FUNDS":
        assert seller_after == seller_before + 1
    elif decision == "REFUND_BUYER":
        assert buyer_after == buyer_before + 1
    # MANUAL_REVIEW: no passport update expected


# ---------------------------------------------------------------------------
# issue_trust_passport
# ---------------------------------------------------------------------------

def test_issue_passport_returns_allowed_status(direct_vm, direct_deploy, direct_alice):
    """Passport issuance for a seeded business must return a valid status."""
    contract = direct_deploy("contracts/trust_africa_intelligent_contract.py")
    direct_vm.sender = direct_alice

    status = contract.issue_trust_passport("Lagos Textile Export Ltd")
    assert status in VALID_PASSPORT_STATUSES, f"Unexpected status: {status}"

    passport = contract.get_trust_passport("Lagos Textile Export Ltd")
    assert passport["verification_status"] == status


def test_issue_passport_for_new_business(direct_vm, direct_deploy, direct_alice):
    """Passport issuance for a brand-new business must return a valid status."""
    contract = direct_deploy("contracts/trust_africa_intelligent_contract.py")
    direct_vm.sender = direct_alice

    status = contract.issue_trust_passport("Dar es Salaam Export House")
    assert status in VALID_PASSPORT_STATUSES


# ---------------------------------------------------------------------------
# get_full_trust_report — consensus_info present
# ---------------------------------------------------------------------------

def test_full_trust_report_includes_consensus_info(direct_vm, direct_deploy, direct_alice):
    """Full trust report must include consensus metadata after a validation."""
    contract = direct_deploy("contracts/trust_africa_intelligent_contract.py")
    direct_vm.sender = direct_alice

    contract.create_trade(
        "T-REPORT-1",
        "Accra Retail Partners",
        "Lagos Textile Export Ltd",
        "Textiles",
        500,
        "Awaiting confirmation",
    )
    contract.validate_trade(
        "T-REPORT-1",
        "Signed receipt and tracked delivery, invoice ref LOS-20240312",
    )
    report = contract.get_full_trust_report("T-REPORT-1")

    assert "trade" in report
    assert "buyer_passport" in report
    assert "seller_passport" in report
    assert "escrow" in report
    assert "consensus_info" in report

    ci = report["consensus_info"]
    assert "APPROVED" in ci["allowed_decisions"]["validate_trade"]
    assert "RELEASE_FUNDS" in ci["allowed_decisions"]["resolve_dispute"]
    assert "VERIFIED" in ci["allowed_decisions"]["issue_trust_passport"]
