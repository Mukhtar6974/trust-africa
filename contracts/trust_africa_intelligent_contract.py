# { "Depends": "py-genlayer:1jb45aa8ynh2a9c9xn3b7qqh8sm5q93hwfp7jqmwsfhh8jpz09h6" }

# Trust Africa Intelligent Contract
#
# Core trust decisions (validate_trade, resolve_dispute, issue_trust_passport) are
# NON-DETERMINISTIC: multiple GenLayer validators independently ask an AI to evaluate
# the same evidence and must agree on the decision category before any state is updated.
#
# Why GenLayer is required:
#   Evidence evaluation is inherently subjective. Two receipts can look legitimate yet
#   differ in phrasing. Fraud signals can be implicit. A single node cannot be trusted
#   to make these calls — consensus across independent validators prevents manipulation.
#
# What validators agree on:
#   The decision CATEGORY — APPROVED, REJECTED, REVIEW_REQUIRED (trade validation);
#   RELEASE_FUNDS, REFUND_BUYER, MANUAL_REVIEW (dispute resolution);
#   VERIFIED, WATCHLIST, UNVERIFIED (trust passport).
#   Validators may produce different explanations and confidence values — only the
#   category must match for consensus to pass.

import json
import re

from genlayer import *

ERROR_EXPECTED  = "[EXPECTED]"
ERROR_LLM       = "[LLM_ERROR]"
ERROR_TRANSIENT = "[TRANSIENT]"


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

    # -------------------------------------------------------------------------
    # Storage helpers (deterministic — no consensus needed)
    # -------------------------------------------------------------------------

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
        passport["successful_deliveries"] = (
            int(passport["successful_deliveries"]) + delivery_delta
        )
        passport["disputes_won"] = int(passport["disputes_won"]) + won_delta
        passport["disputes_lost"] = int(passport["disputes_lost"]) + lost_delta
        self.passports[business] = json.dumps(passport, sort_keys=True)

    # -------------------------------------------------------------------------
    # LLM response helpers
    # -------------------------------------------------------------------------

    def _clean_json(self, text) -> dict:
        if isinstance(text, dict):
            return text
        first = text.find("{")
        last = text.rfind("}")
        if first == -1 or last == -1:
            raise gl.vm.UserError(f"{ERROR_LLM} No JSON object in LLM response")
        text = text[first : last + 1]
        text = re.sub(r",(?!\s*?[\{\[\"\'\w])", "", text)
        return json.loads(text)

    def _parse_trade_verdict(self, raw) -> dict:
        data = self._clean_json(raw) if not isinstance(raw, dict) else raw
        if not isinstance(data, dict):
            raise gl.vm.UserError(f"{ERROR_LLM} Non-dict LLM response: {type(data)}")
        decision = str(data.get("decision", "")).upper().strip()
        if decision not in {"APPROVED", "REJECTED", "REVIEW_REQUIRED"}:
            raise gl.vm.UserError(
                f"{ERROR_LLM} Invalid trade decision '{decision}'"
            )
        return {
            "decision": decision,
            "confidence": max(0, min(100, int(data.get("confidence", 70)))),
            "risk": str(data.get("risk", "MEDIUM")).upper(),
            "reason": str(data.get("reason", "")),
        }

    def _parse_dispute_verdict(self, raw) -> dict:
        data = self._clean_json(raw) if not isinstance(raw, dict) else raw
        if not isinstance(data, dict):
            raise gl.vm.UserError(f"{ERROR_LLM} Non-dict LLM response: {type(data)}")
        decision = str(data.get("decision", "")).upper().strip()
        if decision not in {"RELEASE_FUNDS", "REFUND_BUYER", "MANUAL_REVIEW"}:
            raise gl.vm.UserError(
                f"{ERROR_LLM} Invalid dispute decision '{decision}'"
            )
        return {"decision": decision, "reason": str(data.get("reason", ""))}

    def _parse_passport_verdict(self, raw) -> dict:
        data = self._clean_json(raw) if not isinstance(raw, dict) else raw
        if not isinstance(data, dict):
            raise gl.vm.UserError(f"{ERROR_LLM} Non-dict LLM response: {type(data)}")
        status = str(data.get("status", "")).upper().strip()
        if status not in {"VERIFIED", "WATCHLIST", "UNVERIFIED"}:
            raise gl.vm.UserError(
                f"{ERROR_LLM} Invalid passport status '{status}'"
            )
        return {"status": status, "reason": str(data.get("reason", ""))}

    # -------------------------------------------------------------------------
    # Canonical error handler for validator functions
    # -------------------------------------------------------------------------

    def _handle_leader_error(self, leaders_res, leader_fn) -> bool:
        leader_msg = getattr(leaders_res, "message", "")
        try:
            leader_fn()
            return False  # leader errored but validator succeeded — disagree
        except gl.vm.UserError as exc:
            validator_msg = getattr(exc, "message", str(exc))
            # Deterministic errors (business logic, LLM format) must match exactly
            if validator_msg.startswith(ERROR_EXPECTED) or validator_msg.startswith(ERROR_LLM):
                return validator_msg == leader_msg
            # LLM failures: force rotation so a different validator can succeed
            return False
        except Exception:
            return False

    # =========================================================================
    # NON-DETERMINISTIC CONSENSUS CALLS
    # Each function below is the heart of why Trust Africa requires GenLayer.
    # =========================================================================

    def _ai_evaluate_trade(
        self, buyer: str, seller: str, product: str, amount: str, evidence: str
    ) -> dict:
        """
        NON-DETERMINISTIC — GenLayer validator consensus required.

        Multiple independent validators each call an AI with the same trade details.
        The contract accepts the result only when a validator majority agrees on the
        decision CATEGORY. Validators may produce different explanations or confidence
        values — only APPROVED / REJECTED / REVIEW_REQUIRED must match.

        Allowed equivalent outputs:
          - APPROVED   + any explanation  == APPROVED   (consensus passes)
          - REJECTED   + any explanation  == REJECTED   (consensus passes)
          - APPROVED   vs REJECTED        → not equivalent (consensus fails, retry)
        """
        prompt = f"""You are a trade verification expert for African cross-border commerce.

Evaluate whether the evidence provided is sufficient to approve this trade.

Trade details:
  Buyer: {buyer}
  Seller: {seller}
  Product: {product}
  Amount: {amount}
  Evidence: {evidence}

Choose exactly ONE decision:
  APPROVED        — evidence clearly demonstrates a legitimate, completed trade
  REJECTED        — evidence shows fraud, deception, or a clear policy violation
  REVIEW_REQUIRED — evidence is ambiguous, incomplete, or requires further verification

Consider:
  1. Is the evidence credible and independently verifiable?
  2. Are there fraud or misrepresentation indicators?
  3. Does the evidence match the stated transaction details?
  4. Is the amount reasonable for the described product and corridor?

Respond with JSON only:
{{
  "decision": "APPROVED" | "REJECTED" | "REVIEW_REQUIRED",
  "confidence": <integer 0-100>,
  "risk": "LOW" | "MEDIUM" | "HIGH",
  "reason": "<one-sentence explanation>"
}}"""

        def leader_fn():
            raw = gl.nondet.exec_prompt(prompt, response_format="json")
            return self._parse_trade_verdict(raw)

        def validator_fn(leaders_res: gl.vm.Result) -> bool:
            # Validator re-runs the same AI task independently, then compares
            # only the decision category — not the explanation or confidence.
            if not isinstance(leaders_res, gl.vm.Return):
                return self._handle_leader_error(leaders_res, leader_fn)
            validator_result = leader_fn()
            return leaders_res.calldata["decision"] == validator_result["decision"]

        return gl.vm.run_nondet_unsafe(leader_fn, validator_fn)

    def _ai_resolve_dispute(
        self,
        buyer_claim: str,
        seller_response: str,
        evidence: str,
        product: str,
        amount: str,
    ) -> dict:
        """
        NON-DETERMINISTIC — GenLayer validator consensus required.

        Multiple independent validators each call an AI with the full dispute record.
        The contract accepts the result only when validators agree on the escrow
        disposition CATEGORY. Explanations may differ; the category must match.

        Allowed equivalent outputs:
          - RELEASE_FUNDS + any explanation == RELEASE_FUNDS (consensus passes)
          - REFUND_BUYER  + any explanation == REFUND_BUYER  (consensus passes)
          - RELEASE_FUNDS vs REFUND_BUYER   → not equivalent (consensus fails, retry)
        """
        prompt = f"""You are a dispute resolution expert for African cross-border commerce.

A trade dispute has been filed. Evaluate both parties and decide the correct escrow outcome.

Transaction:
  Product: {product}
  Amount: {amount}

Buyer's claim:
  {buyer_claim}

Seller's response:
  {seller_response}

Additional evidence:
  {evidence}

Choose exactly ONE decision:
  RELEASE_FUNDS — evidence supports the seller; release escrow to seller
  REFUND_BUYER  — evidence supports the buyer; refund escrow to buyer
  MANUAL_REVIEW — evidence is conflicting or insufficient; requires human arbitration

Consider:
  1. Which party presents more credible and specific evidence?
  2. Are there signs of fraud or deception on either side?
  3. Is the seller's proof of delivery independently verifiable?
  4. Is the buyer's complaint substantiated with specific details?

Respond with JSON only:
{{
  "decision": "RELEASE_FUNDS" | "REFUND_BUYER" | "MANUAL_REVIEW",
  "reason": "<one-sentence explanation>"
}}"""

        def leader_fn():
            raw = gl.nondet.exec_prompt(prompt, response_format="json")
            return self._parse_dispute_verdict(raw)

        def validator_fn(leaders_res: gl.vm.Result) -> bool:
            if not isinstance(leaders_res, gl.vm.Return):
                return self._handle_leader_error(leaders_res, leader_fn)
            validator_result = leader_fn()
            return leaders_res.calldata["decision"] == validator_result["decision"]

        return gl.vm.run_nondet_unsafe(leader_fn, validator_fn)

    def _ai_issue_passport(self, business: str, passport_data: dict) -> dict:
        """
        NON-DETERMINISTIC — GenLayer validator consensus required.

        Multiple independent validators each call an AI with the business's trade
        history. The contract accepts the result only when validators agree on the
        verification STATUS. Explanations may differ; the status must match.

        Allowed equivalent outputs:
          - VERIFIED   + any explanation == VERIFIED   (consensus passes)
          - WATCHLIST  + any explanation == WATCHLIST  (consensus passes)
          - VERIFIED   vs WATCHLIST      → not equivalent (consensus fails, retry)
        """
        prompt = f"""You are a business trust verification expert for African cross-border commerce.

Assess this business's trading record and assign the correct trust passport status.

Business: {business}

Trading history:
  Trust Score:           {passport_data.get('trust_score', 0)} / 100
  Completed Trades:      {passport_data.get('completed_trades', 0)}
  Successful Deliveries: {passport_data.get('successful_deliveries', 0)}
  Disputes Won:          {passport_data.get('disputes_won', 0)}
  Disputes Lost:         {passport_data.get('disputes_lost', 0)}

Choose exactly ONE status:
  VERIFIED   — strong history, high trust score (≥75), low dispute rate; trusted partner
  WATCHLIST  — mixed history, moderate score (50–74), or elevated dispute rate; monitor closely
  UNVERIFIED — poor history, low score (<50), high dispute rate, or insufficient trading history

Consider:
  1. Overall trust score and trend
  2. Dispute win / loss ratio
  3. Delivery success rate relative to completed trades
  4. Total trading experience and volume

Respond with JSON only:
{{
  "status": "VERIFIED" | "WATCHLIST" | "UNVERIFIED",
  "reason": "<one-sentence explanation>"
}}"""

        def leader_fn():
            raw = gl.nondet.exec_prompt(prompt, response_format="json")
            return self._parse_passport_verdict(raw)

        def validator_fn(leaders_res: gl.vm.Result) -> bool:
            if not isinstance(leaders_res, gl.vm.Return):
                return self._handle_leader_error(leaders_res, leader_fn)
            validator_result = leader_fn()
            return leaders_res.calldata["status"] == validator_result["status"]

        return gl.vm.run_nondet_unsafe(leader_fn, validator_fn)

    # =========================================================================
    # Public write methods
    # =========================================================================

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
            "reason": "Awaiting GenLayer consensus validation",
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
        """
        GenLayer consensus call — NON-DETERMINISTIC.

        Submits evidence to AI validators for independent evaluation. Each validator
        runs the same LLM prompt and the result is accepted only when a majority
        agrees on the decision category: APPROVED, REJECTED, or REVIEW_REQUIRED.

        This function cannot be replaced with deterministic keyword rules because:
          - Evidence phrasing varies across languages and cultures
          - Fraud signals can be subtle and contextual
          - A single node's keyword check is trivially gameable
        """
        if trade_id not in self.trades:
            raise gl.UserError("Unknown trade")
        trade = json.loads(self.trades[trade_id])

        # NON-DETERMINISTIC: AI validator consensus determines the decision
        verdict = self._ai_evaluate_trade(
            trade["buyer"],
            trade["seller"],
            trade["product"],
            trade["amount"],
            evidence,
        )

        trade["evidence"] = evidence
        trade["decision"] = verdict["decision"]
        trade["confidence"] = verdict["confidence"]
        trade["risk"] = verdict["risk"]
        trade["reason"] = verdict["reason"]
        trade["certificate_status"] = (
            "VERIFIED"
            if verdict["decision"] == "APPROVED"
            else ("REJECTED" if verdict["decision"] == "REJECTED" else "PENDING")
        )
        trade["escrow_decision"] = (
            "RELEASE_FUNDS"
            if verdict["decision"] == "APPROVED"
            else ("REFUND_BUYER" if verdict["decision"] == "REJECTED" else "HOLD_ESCROW")
        )

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
        """
        GenLayer consensus call — NON-DETERMINISTIC.

        Submits the full dispute record (both parties' statements plus evidence) to
        AI validators. Each validator independently evaluates the dispute and the
        result is accepted only when a majority agrees on the escrow disposition:
        RELEASE_FUNDS, REFUND_BUYER, or MANUAL_REVIEW.

        This cannot be deterministic because:
          - "proof" can be fabricated; context determines credibility
          - Buyer and seller claims require holistic judgment, not keyword scanning
          - Stake amounts and corridor context affect the appropriate threshold
        """
        if trade_id not in self.trades:
            raise gl.UserError("Unknown trade")
        trade = json.loads(self.trades[trade_id])

        # NON-DETERMINISTIC: AI validator consensus determines the escrow outcome
        result = self._ai_resolve_dispute(
            buyer_claim,
            seller_response,
            evidence,
            trade["product"],
            trade["amount"],
        )

        decision = result["decision"]
        amount = u256(int(trade["amount"]))

        if decision == "REFUND_BUYER":
            self.funds_refunded += amount
            self._adjust_passport(trade["buyer"], 2, 0, 0, 1, 0)
            self._adjust_passport(trade["seller"], 0, 0, 0, 0, 1)
        elif decision == "RELEASE_FUNDS":
            self.funds_released += amount
            self._adjust_passport(trade["seller"], 2, 0, 0, 1, 0)
            self._adjust_passport(trade["buyer"], 0, 0, 0, 0, 1)
        else:
            self.funds_held += amount

        trade["dispute_decision"] = decision
        trade["dispute_reason"] = result["reason"]
        self.trades[trade_id] = json.dumps(trade, sort_keys=True)
        self.events.append(f"DISPUTE_RESOLVED:{trade_id}:{decision}")
        return decision

    @gl.public.write
    def issue_trust_passport(self, business: str) -> str:
        """
        GenLayer consensus call — NON-DETERMINISTIC.

        Submits a business's full trade history to AI validators. Each validator
        independently evaluates the record and the result is accepted only when a
        majority agrees on the verification status: VERIFIED, WATCHLIST, or UNVERIFIED.

        This cannot be deterministic because:
          - Trust thresholds require contextual judgment about corridor norms
          - A business with a moderate score may warrant VERIFIED or WATCHLIST
            depending on dispute context, trade volume, and delivery patterns
          - Static score thresholds are gameable; AI holistic assessment is not
        """
        self._ensure_passport(business)
        passport = json.loads(self.passports[business])

        # NON-DETERMINISTIC: AI validator consensus determines passport status
        result = self._ai_issue_passport(business, passport)

        passport["verification_status"] = result["status"]
        passport["passport_reason"] = result["reason"]
        self.passports[business] = json.dumps(passport, sort_keys=True)
        self.events.append(f"PASSPORT_ISSUED:{business}:{result['status']}")
        return result["status"]

    @gl.public.write
    def update_reputation(self, business: str, score_delta: int) -> int:
        """Deterministic score adjustment — no consensus needed for arithmetic."""
        self._adjust_passport(business, score_delta, 0, 0, 0, 0)
        passport = json.loads(self.passports[business])
        self.events.append(f"REPUTATION_UPDATED:{business}:{score_delta}")
        return int(passport["trust_score"])

    # =========================================================================
    # Public view methods (deterministic reads — no consensus needed)
    # =========================================================================

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
        """
        Returns the complete trust record for a trade including both passports,
        escrow totals, and metadata about how consensus was reached.
        """
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
            "consensus_info": {
                "method": "GenLayer AI validator consensus (run_nondet_unsafe)",
                "equivalence_principle": (
                    "Decision category must match across validators; "
                    "explanations and confidence values may differ"
                ),
                "allowed_decisions": {
                    "validate_trade": ["APPROVED", "REJECTED", "REVIEW_REQUIRED"],
                    "resolve_dispute": ["RELEASE_FUNDS", "REFUND_BUYER", "MANUAL_REVIEW"],
                    "issue_trust_passport": ["VERIFIED", "WATCHLIST", "UNVERIFIED"],
                },
            },
        }
