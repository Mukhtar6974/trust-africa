"""In-memory V6 trust engine used by the Flask prototype.

The engine mirrors the state transitions implemented by the GenLayer
intelligent contract while keeping the local demo fast and dependency-free.
"""

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from threading import RLock


APPROVAL_TERMS = ("receipt", "proof", "tracking", "invoice", "delivered")
REJECTION_TERMS = ("fraud", "scam", "fake")


@dataclass
class TrustPassport:
    business: str
    trust_score: int
    completed_trades: int
    successful_deliveries: int
    disputes_won: int
    disputes_lost: int
    verification_status: str = "VERIFIED"

    def adjust_score(self, points: int) -> None:
        self.trust_score = max(0, min(100, self.trust_score + points))

    def to_dict(self) -> dict:
        return asdict(self)


class TrustEngine:
    def __init__(self) -> None:
        self._lock = RLock()
        self.passports = {
            "Lagos Textile Export Ltd": TrustPassport(
                "Lagos Textile Export Ltd", 91, 145, 139, 4, 1
            ),
            "Accra Retail Partners": TrustPassport(
                "Accra Retail Partners", 88, 122, 118, 3, 2
            ),
            "Nairobi Agro Supply": TrustPassport(
                "Nairobi Agro Supply", 86, 87, 83, 2, 1
            ),
            "Kigali Logistics Hub": TrustPassport(
                "Kigali Logistics Hub", 89, 103, 99, 3, 1
            ),
        }
        self.trades: dict[str, dict] = {}
        self.events: list[dict] = []
        self.escrow = {"released": 5500.0, "refunded": 0.0, "held": 0.0}
        self.latest_trade_id = "TRADE-DEMO-001"
        self.latest_decision = {
            "decision": "APPROVED",
            "confidence": 94,
            "risk": "LOW",
            "reason": "Evidence contains delivery confirmation",
            "certificate_status": "VERIFIED",
            "escrow_decision": "RELEASE_FUNDS",
            "escrow_status": "RELEASED",
        }
        self.trades[self.latest_trade_id] = {
            "trade_id": self.latest_trade_id,
            "buyer": "Accra Retail Partners",
            "seller": "Lagos Textile Export Ltd",
            "product": "Premium textile consignment",
            "amount": 2000.0,
            "evidence": "Delivery receipt confirmed",
            **self.latest_decision,
        }
        self._record_event("Trade Approved", self.latest_trade_id, "APPROVED")
        self._record_event("Trust Passport Issued", "Lagos Textile Export Ltd", "VERIFIED")

    @staticmethod
    def _now() -> str:
        return datetime.now(timezone.utc).isoformat()

    @staticmethod
    def _amount(value) -> float:
        try:
            return max(0.0, float(value))
        except (TypeError, ValueError):
            return 0.0

    def _passport(self, business: str) -> TrustPassport:
        name = business.strip() or "Unverified Business"
        if name not in self.passports:
            self.passports[name] = TrustPassport(name, 70, 0, 0, 0, 0, "PENDING")
        return self.passports[name]

    def _record_event(self, title: str, subject: str, status: str) -> None:
        self.events.insert(
            0,
            {"title": title, "subject": subject, "status": status, "timestamp": self._now()},
        )
        del self.events[20:]

    @staticmethod
    def judge(evidence: str) -> dict:
        text = evidence.lower()
        if any(term in text for term in REJECTION_TERMS):
            return {
                "decision": "REJECTED",
                "confidence": 98,
                "risk": "HIGH",
                "reason": "Evidence contains fraud indicators",
                "certificate_status": "REJECTED",
                "escrow_decision": "REFUND_BUYER",
                "escrow_status": "REFUNDED",
            }
        if any(term in text for term in APPROVAL_TERMS):
            return {
                "decision": "APPROVED",
                "confidence": 94,
                "risk": "LOW",
                "reason": "Evidence contains verifiable delivery proof",
                "certificate_status": "VERIFIED",
                "escrow_decision": "RELEASE_FUNDS",
                "escrow_status": "RELEASED",
            }
        return {
            "decision": "REVIEW_REQUIRED",
            "confidence": 70,
            "risk": "MEDIUM",
            "reason": "Evidence requires validator review",
            "certificate_status": "PENDING",
            "escrow_decision": "HOLD_ESCROW",
            "escrow_status": "HELD",
        }

    def adjudicate_trade(self, payload: dict) -> dict:
        with self._lock:
            trade_id = str(payload.get("trade_id") or f"TRADE-{int(datetime.now().timestamp() * 1000)}")
            buyer = str(payload.get("buyer", "")).strip() or "Accra Retail Partners"
            seller = str(payload.get("seller", "")).strip() or "Lagos Textile Export Ltd"
            product = str(payload.get("product", "")).strip() or "Commercial goods"
            evidence = str(payload.get("evidence", "")).strip()
            amount = self._amount(payload.get("amount"))
            result = self.judge(evidence)

            buyer_passport = self._passport(buyer)
            seller_passport = self._passport(seller)
            if result["decision"] == "APPROVED":
                buyer_passport.adjust_score(2)  # successful trade
                seller_passport.adjust_score(3)  # approved evidence
                seller_passport.adjust_score(2)  # successful delivery
                buyer_passport.completed_trades += 1
                seller_passport.completed_trades += 1
                seller_passport.successful_deliveries += 1
                self.escrow["released"] += amount
            elif result["decision"] == "REJECTED":
                seller_passport.adjust_score(-10)  # fraud detected
                seller_passport.adjust_score(-5)  # rejected evidence
                self.escrow["refunded"] += amount
            else:
                self.escrow["held"] += amount

            trade = {
                "trade_id": trade_id,
                "buyer": buyer,
                "seller": seller,
                "product": product,
                "amount": amount,
                "evidence": evidence,
                **result,
                "buyer_passport": buyer_passport.to_dict(),
                "seller_passport": seller_passport.to_dict(),
                "timestamp": self._now(),
            }
            self.trades[trade_id] = trade
            self.latest_trade_id = trade_id
            self.latest_decision = result.copy()
            self._record_event("AI Trade Decision", trade_id, result["decision"])
            self._record_event("Escrow Decision", trade_id, result["escrow_decision"])
            return {**trade, "escrow": self.escrow_status()}

    def resolve_dispute(self, payload: dict) -> dict:
        with self._lock:
            trade = self.trades.get(str(payload.get("trade_id") or self.latest_trade_id), {})
            buyer = str(payload.get("buyer") or trade.get("buyer") or "Accra Retail Partners")
            seller = str(payload.get("seller") or trade.get("seller") or "Lagos Textile Export Ltd")
            buyer_claim = str(payload.get("buyer_claim", "")).lower()
            seller_response = str(payload.get("seller_response", "")).lower()
            evidence = str(payload.get("evidence", "")).lower()
            proof_text = f"{seller_response} {evidence}"
            has_proof = any(term in proof_text for term in ("proof", "receipt", "tracking", "delivered"))
            amount = self._amount(payload.get("amount") or trade.get("amount"))

            if "not delivered" in buyer_claim and not has_proof:
                result = {"decision": "REFUND_BUYER", "confidence": 94, "risk_level": "HIGH", "reason": "No delivery proof was provided"}
                winner, loser = buyer, seller
                self.escrow["refunded"] += amount
            elif has_proof:
                result = {"decision": "RELEASE_FUNDS", "confidence": 96, "risk_level": "LOW", "reason": "Seller supplied valid delivery proof"}
                winner, loser = seller, buyer
                self.escrow["released"] += amount
            else:
                result = {"decision": "MANUAL_REVIEW", "confidence": 70, "risk_level": "MEDIUM", "reason": "Evidence is inconclusive"}
                winner = loser = ""
                self.escrow["held"] += amount

            if winner:
                winner_passport = self._passport(winner)
                loser_passport = self._passport(loser)
                winner_passport.adjust_score(2)
                winner_passport.disputes_won += 1
                loser_passport.disputes_lost += 1

            self._record_event("Dispute Resolved", trade.get("trade_id", self.latest_trade_id), result["decision"])
            return {**result, "escrow": self.escrow_status(), "buyer_passport": self._passport(buyer).to_dict(), "seller_passport": self._passport(seller).to_dict()}

    def escrow_status(self) -> dict:
        return {
            "escrow_status": self.latest_decision["escrow_status"],
            "ai_decision": self.latest_decision["escrow_decision"],
            "condition": "GenLayer trust decision must reach consensus",
            "funds_released": round(self.escrow["released"], 2),
            "funds_refunded": round(self.escrow["refunded"], 2),
            "funds_held": round(self.escrow["held"], 2),
        }

    def passport(self, business: str) -> dict:
        with self._lock:
            return self._passport(business).to_dict()

    def passport_list(self) -> list[dict]:
        with self._lock:
            return [passport.to_dict() for passport in self.passports.values()]

    def report(self) -> dict:
        with self._lock:
            latest = self.trades[self.latest_trade_id]
            return {
                "trade": latest,
                "escrow": self.escrow_status(),
                "passports": self.passport_list(),
                "events": self.events[:10],
            }


engine = TrustEngine()
