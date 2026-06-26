class ProtectedTradeAgreement:
    def __init__(self, buyer, seller, product, amount, delivery_date):
        self.buyer = buyer
        self.seller = seller
        self.product = product
        self.amount = amount
        self.delivery_date = delivery_date
        self.evidence = []
        self.status = "CREATED"
        self.decision = None
        self.confidence = 0

    def submit_evidence(self, item):
        self.evidence.append(item)
        self.status = "EVIDENCE_SUBMITTED"

    def ai_review(self):
        evidence_count = len(self.evidence)

        if evidence_count >= 3:
            self.status = "READY_FOR_VALIDATORS"
            self.decision = "RELEASE_FUNDS"
            self.confidence = 90
        elif evidence_count >= 1:
            self.status = "MORE_EVIDENCE_REQUIRED"
            self.decision = "WAIT"
            self.confidence = 60
        else:
            self.status = "HUMAN_REVIEW_REQUIRED"
            self.decision = "HUMAN_REVIEW"
            self.confidence = 30

    def show(self):
        print("Buyer:", self.buyer)
        print("Seller:", self.seller)
        print("Product:", self.product)
        print("Amount:", self.amount)
        print("Status:", self.status)
        print("Decision:", self.decision)
        print("AI Confidence:", self.confidence)


trade = ProtectedTradeAgreement(
    "Amina",
    "Kwame",
    "500 textile materials",
    "2000",
    "10 days"
)



trade.ai_review()
trade.show()