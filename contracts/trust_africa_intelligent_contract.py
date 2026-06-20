# { "Depends": "py-genlayer:1jb45aa8ynh2a9c9xn3b7qqh8sm5q93hwfp7jqmwsfhh8jpz09h6" }

import json

from genlayer import *


class TrustAfricaIntelligentCommerce(gl.Contract):
    """Consensus-owned trust, reputation, dispute, and escrow state."""

    owner: Address
    trades: TreeMap[str, str]
    trade_order: DynArray[str]
    passports: TreeMap[str, str]
    events: DynArray[str]
    trade_count: u256
    funds_released: u256
    funds_refunded: u256
    funds_held: u256

    def __init__(self):
        self.owner = gl.message.sender_account
        self.trade_count = u256(0)
        self.funds_released = u256(0)
        self.funds_refunded = u256(0)
        self.funds_held = u256(0)
        self.passports["Lagos Textile Export Ltd"] = self._passport_json(
            "Lagos Textile Export Ltd", 91, 145, 139, 4, 1, "VERIFIED"
        )
        self.passports["Accra Retail Partners"] = self._passport_json(
            "Accra Retail Partners", 88, 122, 118, 3, 2, "VERIFIED"
        )

    def _passport_json(
        self,
        business: str,
        trust_score: int,
        completed_trades: int,
        successful_deliveries: int,
        disputes_won: int,
        disputes_lost: int,
        verification_status: str,
    ) -> str:
        return json.dumps(
            {
                "business": business,
                "trust_score": trust_score,
                "completed_trades": completed_trades,
                "successful_deliveries": successful_deliveries,
                "disputes_won": disputes_won,
                "disputes_lost": disputes_lost,
                "verification_status": verification_status,
            },
            sort_keys=True,
        )

    def _ensure_passport(self, business: str) -> None:
        if business not in self.passports:
            self.passports[business] = self._passport_json(
                business, 70, 0, 0, 0, 0, "PENDING"
            )

    def _adjust_passport(
        self,
        business: str,
        score_delta: int,
        completed_delta: int,
        delivery_delta: int,
        won_delta: int,
        lost_delta: int,
    ) -> None:
        self._ensure_passport(business)
        passport = json.loads(self.passports[business])
        score = int(passport["trust_score"]) + score_delta
        passport["trust_score"] = max(0, min(100, score))
        passport["completed_trades"] = int(passport["completed_trades"]) + completed_delta
        passport["successful_deliveries"] = int(passport["successful_deliveries"]) + delivery_delta
        passport["disputes_won"] = int(passport["disputes_won"]) + won_delta
        passport["disputes_lost"] = int(passport["disputes_lost"]) + lost_delta
        passport["verification_status"] = (
            "VERIFIED" if int(passport["trust_score"]) >= 80 else "PENDING"
        )
        self.passports[business] = json.dumps(passport, sort_keys=True)

    def _classify_evidence(self, evidence: str) -> dict:
        text = evidence.lower()
        if "fraud" in text or "scam" in text or "fake" in text:
            return {
                "decision": "REJECTED",
                "confidence": 98,
                "risk": "HIGH",
                "reason": "Evidence contains fraud indicators",
                "certificate_status": "REJECTED",
                "escrow_decision": "REFUND_BUYER",
            }
        if (
            "receipt" in text
            or "proof" in text
            or "tracking" in text
            or "invoice" in text
            or "delivered" in text
        ):
            return {
                "decision": "APPROVED",
                "confidence": 94,
                "risk": "LOW",
                "reason": "Evidence contains verifiable delivery proof",
                "certificate_status": "VERIFIED",
                "escrow_decision": "RELEASE_FUNDS",
            }
        return {
            "decision": "REVIEW_REQUIRED",
            "confidence": 70,
            "risk": "MEDIUM",
            "reason": "Evidence requires validator review",
            "certificate_status": "PENDING",
            "escrow_decision": "HOLD_ESCROW",
        }

    @gl.public.write
    def create_trade(
        self,
        trade_id: str,
        buyer: str,
        seller: str,
        product: str,
        amount: u256,
        evidence: str,
    ) -> str:
        if not trade_id or trade_id in self.trades:
            raise gl.UserError("Trade ID must be unique")
        if not buyer or not seller or not product or int(amount) <= 0:
            raise gl.UserError("Trade fields and amount are required")
        self._ensure_passport(buyer)
        self._ensure_passport(seller)
        trade = {
            "trade_id": trade_id,
            "buyer": buyer,
            "seller": seller,
            "product": product,
            "amount": str(amount),
            "evidence": evidence,
            "decision": "REVIEW_REQUIRED",
            "confidence": 0,
            "risk": "MEDIUM",
            "reason": "Awaiting GenLayer validation",
            "certificate_status": "PENDING",
            "escrow_decision": "HOLD_ESCROW",
        }
        self.trades[trade_id] = json.dumps(trade, sort_keys=True)
        self.trade_order.append(trade_id)
        self.trade_count += u256(1)
        self.events.append(f"TRADE_CREATED:{trade_id}")
        return trade_id

    @gl.public.write
    def validate_trade(self, trade_id: str, evidence: str) -> str:
        if trade_id not in self.trades:
            raise gl.UserError("Unknown trade")
        trade = json.loads(self.trades[trade_id])
        verdict = self._classify_evidence(evidence)
        trade["evidence"] = evidence
        trade.update(verdict)
        amount = u256(int(trade["amount"]))
        if verdict["decision"] == "APPROVED":
            self.funds_released += amount
            self._adjust_passport(trade["buyer"], 2, 1, 0, 0, 0)
            self._adjust_passport(trade["seller"], 5, 1, 1, 0, 0)
        elif verdict["decision"] == "REJECTED":
            self.funds_refunded += amount
            self._adjust_passport(trade["seller"], -15, 0, 0, 0, 0)
        else:
            self.funds_held += amount
        self.trades[trade_id] = json.dumps(trade, sort_keys=True)
        self.events.append(f"TRADE_VALIDATED:{trade_id}:{verdict['decision']}")
        return verdict["decision"]

    @gl.public.write
    def resolve_dispute(
        self,
        trade_id: str,
        buyer_claim: str,
        seller_response: str,
        evidence: str,
    ) -> str:
        if trade_id not in self.trades:
            raise gl.UserError("Unknown trade")
        trade = json.loads(self.trades[trade_id])
        claim = buyer_claim.lower()
        proof = (seller_response + " " + evidence).lower()
        has_proof = (
            "proof" in proof
            or "receipt" in proof
            or "tracking" in proof
            or "delivered" in proof
        )
        amount = u256(int(trade["amount"]))
        if "not delivered" in claim and not has_proof:
            decision = "REFUND_BUYER"
            self.funds_refunded += amount
            self._adjust_passport(trade["buyer"], 2, 0, 0, 1, 0)
            self._adjust_passport(trade["seller"], 0, 0, 0, 0, 1)
        elif has_proof:
            decision = "RELEASE_FUNDS"
            self.funds_released += amount
            self._adjust_passport(trade["seller"], 2, 0, 0, 1, 0)
            self._adjust_passport(trade["buyer"], 0, 0, 0, 0, 1)
        else:
            decision = "MANUAL_REVIEW"
            self.funds_held += amount
        trade["dispute_decision"] = decision
        self.trades[trade_id] = json.dumps(trade, sort_keys=True)
        self.events.append(f"DISPUTE_RESOLVED:{trade_id}:{decision}")
        return decision

    @gl.public.write
    def issue_trust_passport(self, business: str) -> str:
        self._ensure_passport(business)
        passport = json.loads(self.passports[business])
        passport["verification_status"] = (
            "VERIFIED" if int(passport["trust_score"]) >= 80 else "PENDING"
        )
        self.passports[business] = json.dumps(passport, sort_keys=True)
        self.events.append(f"PASSPORT_ISSUED:{business}")
        return passport["verification_status"]

    @gl.public.write
    def update_reputation(self, business: str, score_delta: int) -> int:
        self._adjust_passport(business, score_delta, 0, 0, 0, 0)
        passport = json.loads(self.passports[business])
        self.events.append(f"REPUTATION_UPDATED:{business}:{score_delta}")
        return int(passport["trust_score"])

    @gl.public.view
    def get_trade(self, trade_id: str) -> dict:
        if trade_id not in self.trades:
            raise gl.UserError("Unknown trade")
        return json.loads(self.trades[trade_id])

    @gl.public.view
    def get_trust_passport(self, business: str) -> dict:
        if business not in self.passports:
            raise gl.UserError("Unknown business")
        return json.loads(self.passports[business])

    @gl.public.view
    def get_full_trust_report(self, trade_id: str) -> dict:
        if trade_id not in self.trades:
            raise gl.UserError("Unknown trade")
        trade = json.loads(self.trades[trade_id])
        return {
            "trade": trade,
            "buyer_passport": json.loads(self.passports[trade["buyer"]]),
            "seller_passport": json.loads(self.passports[trade["seller"]]),
            "escrow": {
                "funds_released": str(self.funds_released),
                "funds_refunded": str(self.funds_refunded),
                "funds_held": str(self.funds_held),
            },
        }
