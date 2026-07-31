import os

import pytest

from gltest import get_contract_factory
from gltest.assertions import tx_execution_succeeded


pytestmark = pytest.mark.slow


def receipt_status(receipt):
    if isinstance(receipt, dict):
        return receipt.get("status")
    return getattr(receipt, "status", None)


def test_real_network_receipts_finalize_before_reads():
    buyer_address = os.getenv("TRUST_AFRICA_INTEGRATION_BUYER_ADDRESS")
    seller_address = os.getenv("TRUST_AFRICA_INTEGRATION_SELLER_ADDRESS")
    if not buyer_address or not seller_address:
        pytest.skip("Set integration buyer and seller addresses to run against GenLayer")

    factory = get_contract_factory("TrustAfricaIntelligentCommerce")
    contract = factory.deploy(args=[])
    trade_id = "INTEGRATION-FINALITY-1"

    create_receipt = contract.create_trade(
        args=[
            trade_id,
            "Integration Buyer",
            "Integration Seller",
            buyer_address,
            seller_address,
            "Verified sample goods",
            100,
            "Integration evidence",
        ]
    ).transact()
    assert tx_execution_succeeded(create_receipt)
    assert receipt_status(create_receipt) == "FINALIZED"

    validate_receipt = contract.validate_trade(
        args=[trade_id, "Integration evidence with delivery proof"]
    ).transact()
    assert tx_execution_succeeded(validate_receipt)
    assert receipt_status(validate_receipt) == "FINALIZED"

    trade = contract.get_trade(args=[trade_id]).call()
    report = contract.get_full_trust_report(args=[trade_id]).call()
    assert trade["validation_completed"] is True
    assert report["state_machine"]["validation_completed"] is True
