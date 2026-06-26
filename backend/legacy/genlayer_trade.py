from contracts.protected_trade_genlayer import ProtectedTradeAgreement
from contracts.validators import Validator


trade = ProtectedTradeAgreement(
    "Amina",
    "Kwame",
    "500 textile materials",
    "2000",
    "10 days"
)

trade.submit_evidence("Shipping receipt")
trade.submit_evidence("Tracking number")
trade.submit_evidence("Product photos")

trade.ai_review()

validators = [
    Validator("Validator Alpha"),
    Validator("Validator Beta"),
    Validator("Validator Gamma")
]

votes = []

for validator in validators:
    vote = validator.vote(trade.decision)
    votes.append(vote)

release_votes = votes.count("RELEASE_FUNDS")

print()
print("===== TRUST AFRICA GENLAYER =====")
print()

trade.show()
print()

print("Total Release Votes:", release_votes)

if release_votes >= 2:
    print("Final Decision: RELEASE_FUNDS")
else:
    print("Final Decision: HUMAN_REVIEW_REQUIRED")