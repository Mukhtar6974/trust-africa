from escrow import Escrow

class Dispute:
    def __init__(self, trade_id, reason):
        self.trade_id = trade_id
        self.reason = reason
        self.status = "OPEN"

    def escalate(self):
        self.status = "UNDER_REVIEW"

    def resolve(self):
        self.status = "RESOLVED"

    def show(self):
        print("Trade ID:", self.trade_id)
        print("Reason:", self.reason)
        print("Status:", self.status)


escrow = Escrow(2000)

dispute = Dispute(
    "TRADE001",
    "Buyer claims goods not delivered"
)

dispute.show()

print()

dispute.escalate()
dispute.show()

print("Escrow Locked:", escrow.locked)

print()

dispute.resolve()
escrow.refund()

dispute.show()