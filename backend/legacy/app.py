"""
Trust Africa Backend
"""

from contracts.protected_trade import ProtectedTrade
from ai_engine.decision_engine import evaluate_trade


trade = ProtectedTrade(
    buyer="Amina",
    seller="Kwame",
    product="500 textile materials",
    amount="2000 USDC",
    delivery_date="10 days"
)

trade.add_evidence("Shipping receipt")
trade.add_evidence("Tracking number")
trade.add_evidence("Product photos")

result = evaluate_trade(
    len(trade.evidence)
)
trade.ai_review()

print("==========")
print("TRUST AFRICA")
print("==========")
print()

trade.show_status()

print()
print("AI Decision")
print(result)