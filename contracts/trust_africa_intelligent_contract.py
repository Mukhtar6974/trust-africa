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
    buyer_claim: str
    seller_response: str
    evidence: str
    confidence: int

    def __init__(self):
        self.buyer = "Amina"
        self.seller = "Kwame"
        self.product = "500 textile materials"
        self.amount = 2000

        self.buyer_score = 67
        self.seller_score = 87
        self.trust_score = 70
        self.risk_level = "MEDIUM"
        self.certificate_status = "PENDING"
        self.dispute_decision = "No decision yet"

        self.buyer_claim = ""
        self.seller_response = ""
        self.evidence = ""
        self.confidence = 0

   @gl.public.write
    def create_trade(
        self,
        buyer: str,
        seller: str,
        product: str,
        amount: int
   ) -> None:

        self.buyer = buyer
        self.seller = seller
        self.product = product
        self.amount = amount

        self.certificate_status = "PENDING"
        self.risk_level = "MEDIUM"
        self.trust_score = 70
        self.dispute_decision = "Awaiting validation"

    @gl.public.view
    def get_trade(self) -> str:
        return f"{self.buyer} buying {self.product} from {self.seller} for {self.amount}"

    @gl.public.view
    def get_reputation(self) -> str:
        return f"Buyer Score: {self.buyer_score} | Seller Score: {self.seller_score}"

    @gl.public.view
    def get_trust_certificate(self) -> str:
        return f"Certificate Status: {self.certificate_status} | Trust Score: {self.trust_score}"

    @gl.public.view
    def get_risk_status(self) -> str:
        return f"Risk Level: {self.risk_level} | Confidence: {self.confidence}%"

    @gl.public.write
    def validate_trade(self, buyer_evidence: str, seller_evidence: str) -> None:
        self.evidence = buyer_evidence + " " + seller_evidence
        evidence_text = self.evidence.lower()

        if "scam" in evidence_text or "fake" in evidence_text or "fraud" in evidence_text:
            self.risk_level = "HIGH"
            self.trust_score = 35
            self.confidence = 90
            self.certificate_status = "REJECTED"
            self.dispute_decision = "Block trade and flag for review"

        elif "receipt" in evidence_text or "delivered" in evidence_text or "confirmed" in evidence_text:
            self.risk_level = "LOW"
            self.trust_score = 92
            self.confidence = 96
            self.certificate_status = "VERIFIED"
            self.dispute_decision = "Approve trade and allow escrow release"
            self.buyer_score += 1
            self.seller_score += 1

        else:
            self.risk_level = "MEDIUM"
            self.trust_score = 70
            self.confidence = 65
            self.certificate_status = "PENDING"
            self.dispute_decision = "Request more evidence"

    @gl.public.write
    def resolve_dispute(self, buyer_claim: str, seller_response: str) -> None:
        self.buyer_claim = buyer_claim
        self.seller_response = seller_response

        buyer_text = buyer_claim.lower()
        seller_text = seller_response.lower()

        if "not delivered" in buyer_text and "proof" not in seller_text:
            self.dispute_decision = "Refund buyer"
            self.risk_level = "HIGH"
            self.trust_score = 40
            self.confidence = 88
            self.certificate_status = "REJECTED"
            self.seller_score -= 5

        elif "proof" in seller_text or "receipt" in seller_text or "delivered" in seller_text:
            self.dispute_decision = "Release funds to seller"
            self.risk_level = "LOW"
            self.trust_score = 92
            self.confidence = 96
            self.certificate_status = "VERIFIED"
            self.seller_score += 2

        else:
            self.dispute_decision = "Manual review required"
            self.risk_level = "MEDIUM"
            self.trust_score = 70
            self.confidence = 60
            self.certificate_status = "PENDING"

    @gl.public.view
    def get_dispute_decision(self) -> str:
        return self.dispute_decision

    @gl.public.view
    def get_full_trust_report(self) -> str:
        return (
            f"Trade: {self.buyer} -> {self.seller} | "
            f"Score: {self.trust_score} | "
            f"Risk: {self.risk_level} | "
            f"Certificate: {self.certificate_status} | "
            f"Decision: {self.dispute_decision} | "
            f"Confidence: {self.confidence}%"
        )