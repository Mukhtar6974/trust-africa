"""
Trust Africa API Prototype

This is not a real web server yet.
It simulates backend API actions.
"""

from contracts.protected_trade import ProtectedTrade
from ai_engine.decision_engine import evaluate_trade


def create_agreement():
    return ProtectedTrade(
        buyer="Amina",
        seller="Kwame",
        product="500 textile materials",
        amount="2000 USDC",
        delivery_date="10 days"
    )


def submit_evidence(trade):
    trade.add_evidence("Shipping receipt")
    trade.add_evidence("Tracking number")
    trade.add_evidence("Product photos")
    return trade


def review_trade(trade):
    trade.ai_review()
    decision = evaluate_trade(len(trade.evidence))
    return decision


trade = create_agreement()
submit_evidence(trade)
decision = review_trade(trade)

print("========== TRUST AFRICA API ==========")
print()
trade.show_status()
print()
print("Decision:")
print(decision)