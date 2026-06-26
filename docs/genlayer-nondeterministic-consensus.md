# GenLayer Non-Deterministic Consensus in Trust Africa

## Why the First Submission Was Rejected

The original contract was rejected because its core decision logic was **deterministic**:

```python
# Old code — purely deterministic keyword matching
def _classify_evidence(self, evidence: str) -> dict:
    text = evidence.lower()
    if "fraud" in text or "scam" in text or "fake" in text:
        return {"decision": "REJECTED", ...}
    if "receipt" in text or "proof" in text or "tracking" in text:
        return {"decision": "APPROVED", ...}
    return {"decision": "REVIEW_REQUIRED", ...}
```

This approach does not use GenLayer consensus for anything meaningful. Any single
Python process — or a simple SQL query — could produce the same result. There is no
reason for multiple validators to agree because there is nothing for them to independently
evaluate; the output is always determined by string containment checks.

GenLayer's value is **consensus over non-deterministic judgment calls** — specifically,
decisions that require subjective evaluation, contextual reasoning, or access to
information that changes between calls. Keyword matching has none of these properties.

## What Deterministic Logic Means

A function is **deterministic** if running it twice with the same inputs always produces
the same output, and that output can be computed by any single node with no external
calls. Examples:

- `if "fraud" in evidence.lower()` → deterministic
- `score >= 80` → deterministic
- A lookup table for known invoice keywords → deterministic

Deterministic logic does not benefit from validator consensus. One node can compute it
correctly; agreeing on it is trivially guaranteed and adds no trust value.

## What Changed

The refactored contract removes all keyword-based classification and replaces it with
**three non-deterministic AI consensus calls** using `gl.vm.run_nondet_unsafe`:

| Function | Old (deterministic) | New (non-deterministic) |
|---|---|---|
| `validate_trade()` | Keyword scan on evidence string | AI evaluates full trade context |
| `resolve_dispute()` | `"proof" in seller_response` check | AI weighs both parties' claims |
| `issue_trust_passport()` | `trust_score >= 80` threshold | AI holistically assesses trade history |

Each call follows the GenLayer consensus pattern:
1. A **leader** validator calls the AI and produces a structured result.
2. Each subsequent **validator** independently re-runs the same AI prompt.
3. The result is accepted on-chain only if a validator majority agrees on the
   **decision category** (not exact wording).

## Where Non-Deterministic Consensus Is Used

### `validate_trade()` → `_ai_evaluate_trade()`

The AI receives the full trade context — buyer, seller, product, amount, and evidence —
and returns one of: `APPROVED`, `REJECTED`, `REVIEW_REQUIRED`.

This is non-deterministic because:
- The AI may phrase its reasoning differently on each run
- Confidence scores vary by framing and model temperature
- Contextual cues (amount vs. product type, corridor risk) affect the assessment
- Evidence credibility is subjective and varies between evaluators

### `resolve_dispute()` → `_ai_resolve_dispute()`

The AI receives both the buyer's claim and the seller's response, plus supporting
evidence, and returns one of: `RELEASE_FUNDS`, `REFUND_BUYER`, `MANUAL_REVIEW`.

This is non-deterministic because:
- Credibility judgment depends on reading both parties holistically
- The same "proof of delivery" may be convincing or suspicious depending on context
- Fraud signals in claims are implicit, not keyword-searchable
- Human-like reasoning over conflicting accounts cannot be reduced to if/else

### `issue_trust_passport()` → `_ai_issue_passport()`

The AI receives the business's complete trading record and returns one of:
`VERIFIED`, `WATCHLIST`, `UNVERIFIED`.

This is non-deterministic because:
- A trust score of 72 with 3 disputes won may warrant VERIFIED or WATCHLIST
  depending on delivery patterns and trade volume
- Context about corridor norms and industry risk matters
- Static thresholds are gameable; holistic AI assessment is not

## How Validators Compare Outputs

Validators use the **equivalence principle**: two results are considered equivalent if
they share the same **decision category**, regardless of the explanation, confidence
value, or phrasing.

| Leader output | Validator output | Equivalent? |
|---|---|---|
| `APPROVED` with "receipt confirmed" | `APPROVED` with "invoice verified" | Yes |
| `REJECTED` with confidence 95 | `REJECTED` with confidence 88 | Yes |
| `APPROVED` | `REJECTED` | **No** — consensus fails, retry |
| `RELEASE_FUNDS` | `RELEASE_FUNDS` | Yes |
| `RELEASE_FUNDS` | `REFUND_BUYER` | **No** — consensus fails, retry |
| `VERIFIED` | `VERIFIED` | Yes |
| `VERIFIED` | `WATCHLIST` | **No** — consensus fails, retry |

The validator function for each call:

```python
def validator_fn(leaders_res: gl.vm.Result) -> bool:
    if not isinstance(leaders_res, gl.vm.Return):
        return self._handle_leader_error(leaders_res, leader_fn)
    validator_result = leader_fn()
    # Only the category is compared — not explanation, confidence, or risk level
    return leaders_res.calldata["decision"] == validator_result["decision"]
```

## Why Trust Africa Now Requires GenLayer

1. **Evidence is subjective.** A receipt in Swahili, an invoice from a Lagos market,
   and a WhatsApp screenshot from a Nairobi trader are all "evidence" — but they require
   contextual judgment, not keyword scanning.

2. **Consensus prevents manipulation.** If a single node classified evidence, an attacker
   could craft evidence strings that pass keyword checks without genuine legitimacy.
   Multi-validator AI consensus requires independent agreement, which is much harder to
   game.

3. **Escrow decisions have real financial stakes.** `RELEASE_FUNDS` vs `REFUND_BUYER`
   moves actual value. Deterministic keyword rules are not a defensible basis for
   financial settlement. AI consensus with validator agreement provides a transparent,
   auditable, and harder-to-manipulate basis.

4. **Trust passports affect business reputation.** Issuing a `VERIFIED` passport based
   solely on `trust_score >= 80` ignores the full picture. AI holistic assessment
   catches patterns that thresholds miss.

5. **The result is auditable.** Every consensus decision is recorded on-chain with its
   inputs. Any party can verify that the AI was given accurate inputs and that a
   validator majority agreed on the outcome.
