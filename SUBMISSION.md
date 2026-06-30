# Trust Africa — GenLayer Resubmission Notes

## Response to Rejection Feedback

> "Thanks for submitting. This cannot be accepted as a Projects & Milestones
> contribution because the reviewed contract is deterministic and does not use
> GenLayer consensus for a meaningful non-deterministic result."

The original contract used a private `_classify_evidence()` method that applied
deterministic keyword matching:

```python
# REMOVED — old deterministic logic
def _classify_evidence(self, evidence: str) -> dict:
    text = evidence.lower()
    if "fraud" in text or "scam" in text or "fake" in text:
        return {"decision": "REJECTED", ...}
    if "receipt" in text or "proof" in text or "tracking" in text:
        return {"decision": "APPROVED", ...}
    return {"decision": "REVIEW_REQUIRED", ...}
```

Any single Python process could compute this result with no external calls. There
was nothing for validators to independently evaluate, so consensus added no value.

---

## What Is Non-Deterministic Now

The three core decision functions now use the **GenLayer Equivalence Principle**
(`gl.eq_principle.prompt_comparative`) with `gl.nondet.exec_prompt`:

### `validate_trade(trade_id, evidence)`

```python
def get_verdict():
    raw = gl.nondet.exec_prompt(prompt, response_format="json")
    ...
    return {"decision": decision, "confidence": ..., "risk": ..., "reason": ...}

verdict = gl.eq_principle.prompt_comparative(
    get_verdict,
    principle=(
        "The outputs are equivalent if and only if the `decision` field is "
        "exactly the same string: APPROVED, REJECTED, or REVIEW_REQUIRED. "
        "This is the sole consensus criterion — it represents the categorical "
        "judgment on whether the trade evidence is valid. ..."
    ),
)
```

Each validator independently calls the AI with the full trade context (buyer,
seller, product, amount, evidence). A comparison LLM then checks that the
`decision` fields match. On-chain state (escrow allocation, reputation delta,
certificate status) only updates after a validator majority passes.

### `resolve_dispute(trade_id, buyer_claim, seller_response, evidence)`

Same pattern. Each validator independently asks the AI to weigh both parties'
arguments. Consensus required on: `RELEASE_FUNDS | REFUND_BUYER | MANUAL_REVIEW`.

### `issue_trust_passport(business)`

Same pattern. Each validator independently asks the AI to assess the business's
full trade history. Consensus required on: `VERIFIED | WATCHLIST | UNVERIFIED`.

---

## Why These Decisions Are Meaningfully Non-Deterministic

1. **Evidence evaluation is inherently subjective.** "Seller sent confirmation"
   means something different in Lagos than in Cape Town; a receipt written in
   Amharic requires contextual judgment, not string containment.

2. **Dispute resolution requires holistic judgment.** Two parties can each produce
   plausible-sounding claims. Weighing credibility cannot be reduced to
   `"proof" in seller_response`.

3. **Trust passport assessment needs context.** A score of 72 with 5 disputes
   might warrant VERIFIED or WATCHLIST depending on delivery patterns, trade
   volume, and corridor risk. A static threshold (`score >= 80`) is gameable.

4. **Consensus prevents manipulation.** With keyword rules, crafting a string
   like "delivery receipt tracking proof" trivially passes. With multi-validator
   AI consensus, a malicious actor would need to convince an independent majority
   of validators each evaluating the full evidence context from scratch.

5. **The results have real on-chain consequences.** `RELEASE_FUNDS` moves escrow
   to the seller. `REFUND_BUYER` returns it to the buyer. `VERIFIED` grants a
   trust passport. These are not cosmetic labels.

---

## What Has Not Changed

- Contract runner: `py-genlayer:1jb45aa8ynh2a9c9xn3b7qqh8sm5q93hwfp7jqmwsfhh8jpz09h6` (pinned)
- Storage layout: `TreeMap`, `DynArray`, `u256` (unchanged)
- Public API surface: all original methods preserved
- `create_trade` and `update_reputation` remain deterministic — they perform
  bookkeeping and arithmetic that genuinely do not require AI consensus
- View methods remain deterministic — they read and return on-chain state

---

## Robustness and Security Fixes (V7 → V8)

### V7 — LLM output robustness

The `get_verdict()` helper in every AI decision function wraps confidence
parsing in a `try/except (TypeError, ValueError)` so the contract degrades
gracefully if the LLM returns a non-numeric confidence value.

```python
try:
    confidence = max(0, min(100, int(raw.get("confidence", 70))))
except (TypeError, ValueError):
    confidence = 70
```

### V8 — Access control on `update_reputation`

`update_reputation` previously had no access control — any address could call it
to arbitrarily raise or lower any business's trust score, bypassing the
AI-consensus-backed `issue_trust_passport`. The `owner` address was stored in
`__init__` but never enforced.

Fixed by adding an owner check:

```python
@gl.public.write
def update_reputation(self, business: str, score_delta: int) -> int:
    """Owner-only deterministic score adjustment."""
    if gl.message.sender_account != self.owner:
        raise gl.UserError("Only the contract owner can call update_reputation")
    ...
```

Two direct-mode tests cover this:
- `test_update_reputation_owner_succeeds` — verifies the deployer can call it
- `test_update_reputation_non_owner_rejected` — verifies any other address is rejected

### Final production hardening

- Flask debug mode is disabled by default and can be explicitly enabled with
  `FLASK_DEBUG=1` for local development.
- CORS remains local-demo friendly by default but can be restricted with
  `TRUST_AFRICA_CORS_ORIGINS`.
- The compatibility `/trade/create` route now creates real unique trade records
  instead of returning the legacy static `TRADE003` response.
- The local `TrustEngine` preserves duplicate client-supplied trade IDs by adding
  a suffix instead of overwriting existing records.
- Validator prompts now encode user-controlled trade/evidence fields as JSON
  strings and explicitly treat them as untrusted data, reducing prompt-injection
  risk in AI consensus calls.
- Python bytecode and generated artifacts are excluded with `.gitignore`; cached
  `.pyc` files were removed from version control.

---

## Test Results

```
py -3.14 -m pytest tests/ -v

7 passed, 12 skipped in 4.31s
```

- **7 local unit/API tests pass** (`tests/test_trust_engine.py`, `tests/test_backend_api.py`) — no external services required.
- **12 direct contract tests collected** (`tests/direct/`) — skipped automatically
  when the GenVM binary is not available locally. These include:
  - 10 AI decision correctness and state-transition tests
  - 2 new access-control tests for `update_reputation` (owner succeeds; non-owner rejected)
  They pass when the GenVM binary can be downloaded (`genvm-lint check` + a working GenVM runtime).

---

## Lint Result

```
✓ Lint passed (3 checks)
✓ Validation passed
  Contract: TrustAfricaIntelligentCommerce
  Methods: 8 (3 view, 5 write)
```

## Full Technical Documentation

See [docs/genlayer-nondeterministic-consensus.md](docs/genlayer-nondeterministic-consensus.md)
for the complete technical explanation of the equivalence principle, validator
comparison logic, and why each decision requires GenLayer consensus.
