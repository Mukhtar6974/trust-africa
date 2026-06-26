from protected_trade_genlayer import ProtectedTradeAgreement
from escrow import Escrow


class Validator:
    def __init__(self, name):
        self.name = name

    def vote(self, decision):
        vote = decision
        print(self.name, "voted:", vote)
        return vote


validators = [
    Validator("Validator Alpha"),
    Validator("Validator Beta"),
    Validator("Validator Gamma")
]

trade = ProtectedTradeAgreement(
    "Amina",
    "Kwame",
    "500 textile materials",
    2000,
    "10 days"
)

trade.submit_evidence("Shipping receipt")
trade.submit_evidence("Tracking number")
trade.submit_evidence("Product photos")

trade.ai_review()
trade.show()

escrow = Escrow(trade.amount)

decision = trade.decision

votes = []

for validator in validators:
    vote = validator.vote(decision)
    votes.append(vote)

release_votes = votes.count("RELEASE_FUNDS")

print()
print("Total Release Votes:", release_votes)

if release_votes >= 2:
    print("Final Validator Decision: RELEASE_FUNDS")
    escrow.release_funds()
else:
    print("Final Validator Decision: HUMAN_REVIEW_REQUIRED")
    escrow.refund()