# { "Depends": "py-genlayer:1jb45aa8ynh2a9c9xn3b7qqh8sm5q93hwfp7jqmwsfhh8jpz09h6" }

from genlayer import *


class TrustAfrica(gl.Contract):
    buyer: str
    seller: str
    product: str
    amount: int
    buyer_score: int
    seller_score: int
    trust_score: int
    risk_level: str
    certificate_status: str
    dispute_decision: str

    def __init__(self):
        self.buyer = "Amina"
        self.seller = "Kwame"
        self.product = "500 textile materials"
        self.amount = 2000
        self.buyer_score = 67
        self.seller_score = 87
        self.trust_score = 92
        self.risk_level = "LOW"
        self.certificate_status = "VERIFIED"
        self.dispute_decision = "No active dispute"

    @gl.public.view
    def get_trade(self) -> str:
        return f"{self.buyer} buying {self.product} from {self.seller} for {self.amount}"

    @gl.public.view
    def get_reputation(self) -> str:
        return f"Buyer Score: {self.buyer_score} | Seller Score: {self.seller_score}"

    @gl.public.view
    def get_trust_certificate(self) -> str:
        return f"Trust Certificate: {self.certificate_status} | Trust Score: {self.trust_score}"

    @gl.public.view
    def get_risk_status(self) -> str:
        return f"Risk Level: {self.risk_level}"

    @gl.public.write
    def validate_trade(self, buyer_evidence: str, seller_evidence: str) -> None:
        combined_evidence = buyer_evidence.lower() + " " + seller_evidence.lower()

        if "fraud" in combined_evidence or "fake" in combined_evidence or "scam" in combined_evidence:
            self.risk_level = "HIGH"
            self.trust_score = 40
            self.certificate_status = "REJECTED"
        elif "delivered" in combined_evidence or "confirmed" in combined_evidence or "receipt" in combined_evidence:
            self.risk_level = "LOW"
            self.trust_score = 92
            self.certificate_status = "VERIFIED"
            self.buyer_score += 1
            self.seller_score += 1
        else:
            self.risk_level = "MEDIUM"
            self.trust_score = 70
            self.certificate_status = "PENDING"

    @gl.public.write
    def resolve_dispute(self, buyer_claim: str, seller_response: str) -> None:
        buyer_text = buyer_claim.lower()
        seller_text = seller_response.lower()

        if "not delivered" in buyer_text and "proof" not in seller_text:
            self.dispute_decision = "Refund buyer"
            self.risk_level = "HIGH"
            self.seller_score -= 5
        elif "delivered" in seller_text or "receipt" in seller_text or "proof" in seller_text:
            self.dispute_decision = "Release funds to seller"
            self.risk_level = "LOW"
            self.seller_score += 2
        else:
            self.dispute_decision = "Manual review required"
            self.risk_level = "MEDIUM"

    @gl.public.view
    def get_dispute_decision(self) -> str:
        return self.dispute_decision