"""
Trust Africa: Protected Trade Contract

Trust Beyond Borders

No honest person should ever have to choose
between opportunity and safety.
"""


class ProtectedTrade:
    def __init__(self, buyer, seller, product, amount, delivery_date):
        self.buyer = buyer
        self.seller = seller
        self.product = product
        self.amount = amount
        self.delivery_date = delivery_date
        self.evidence = []
        self.status = "AGREEMENT_CREATED"
        self.ai_confidence = 0
        self.ai_reasoning = ""

    def add_evidence(self, evidence_item):
        self.evidence.append(evidence_item)
        self.status = "EVIDENCE_SUBMITTED"

    def ai_review(self):
        evidence_count = len(self.evidence)

        if evidence_count >= 3:
            self.ai_confidence = 90
            self.ai_reasoning = "Enough evidence was submitted for a high-confidence decision."
            self.status = "READY_TO_RELEASE"
        elif evidence_count >= 1:
            self.ai_confidence = 60
            self.ai_reasoning = "Some evidence was submitted, but more evidence is needed."
            self.status = "MORE_EVIDENCE_REQUIRED"
        else:
            self.ai_confidence = 30
            self.ai_reasoning = "No evidence was submitted. Human review is required."
            self.status = "HUMAN_REVIEW_REQUIRED"

    def show_status(self):
        print("Buyer:", self.buyer)
        print("Seller:", self.seller)
        print("Product:", self.product)
        print("Amount:", self.amount)
        print("Delivery Date:", self.delivery_date)
        print("Status:", self.status)
        print("AI Confidence:", self.ai_confidence)
        print("AI Reasoning:", self.ai_reasoning)