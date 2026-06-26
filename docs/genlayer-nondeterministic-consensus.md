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
**three non-deterministic AI consensus calls** using `gl.eq_principle.prompt_comparative`:

| Function | Old (deterministic) | New (non-deterministic) |
|---|---|---|
| `validate_trade()` | Keyword scan on evidence string | AI evaluates full trade context via `prompt_comparative` |
| `resolve_dispute()` | `"proof" in seller_response` check | AI weighs both parties' claims via `prompt_comparative` |
| `issue_trust_passport()` | `trust_score >= 80` threshold | AI holistically assesses trade history via `prompt_comparative` |

Each call follows the GenLayer Equivalence Principle pattern:
1. A **leader** validator runs `get_verdict()`, which calls `gl.nondet.exec_prompt`.
2. Each subsequent **validator** independently reruns `get_verdict()`.
3. A **comparison LLM** receives both outputs and checks them against the principle string.
4. The result is accepted on-chain only if a validator majority passes the comparison.

## How the Equivalence Principle Is Applied

All three decision functions now use `gl.eq_principle.prompt_comparative`, the official
GenLayer Equivalence Principle convenience wrapper for comparative consensus.

### Pattern used in each function

```python
def get_verdict():
    # _parse_llm_json handles both dict (already parsed) and string (needs parsing)
    raw = self._parse_llm_json(
        gl.nondet.exec_prompt(prompt, response_format="json")
    )
    decision = str(raw.get("decision", "REVIEW_REQUIRED")).upper().strip()
    if decision not in {"APPROVED", "REJECTED", "REVIEW_REQUIRED"}:
        decision = "REVIEW_REQUIRED"
    return {
        "decision": decision,
        "confidence": max(0, min(100, int(raw.get("confidence", 70)))),
        "risk": str(raw.get("risk", "MEDIUM")).upper(),
        "reason": str(raw.get("reason", "")),
    }

verdict = gl.eq_principle.prompt_comparative(
    get_verdict,
    principle=(
        "The outputs are equivalent if and only if the `decision` field is "
        "exactly the same string: APPROVED, REJECTED, or REVIEW_REQUIRED. "
        "confidence, risk, and reason are metadata and may differ freely."
    ),
)
```

### `validate_trade()`

`get_verdict()` receives the full trade context (buyer, seller, product, amount,
evidence) and asks the AI to return `APPROVED`, `REJECTED`, or `REVIEW_REQUIRED`.

The principle: **`decision` must be exactly the same.** Confidence, risk, and reason
may differ across validators.

### `resolve_dispute()`

`get_verdict()` receives the buyer's claim, seller's response, and evidence, and asks
the AI to return `RELEASE_FUNDS`, `REFUND_BUYER`, or `MANUAL_REVIEW`.

The principle: **`decision` must be exactly the same.** Reason may differ.

### `issue_trust_passport()`

`get_verdict()` receives the business's full trading record and asks the AI to return
`VERIFIED`, `WATCHLIST`, or `UNVERIFIED`.

The principle: **`status` must be exactly the same.** Reason may differ.

## How Validators Compare Outputs

`prompt_comparative` runs `get_verdict()` independently on each validator, then sends
both outputs to a comparison LLM with the principle string. The comparison LLM decides
if they agree.

| Leader output | Validator output | Equivalent? |
|---|---|---|
| `APPROVED` with "receipt confirmed" | `APPROVED` with "invoice verified" | Yes |
| `REJECTED` with confidence 95 | `REJECTED` with confidence 88 | Yes |
| `APPROVED` | `REJECTED` | **No** — consensus fails, retry |
| `RELEASE_FUNDS` | `RELEASE_FUNDS` | Yes |
| `RELEASE_FUNDS` | `REFUND_BUYER` | **No** — consensus fails, retry |
| `VERIFIED` | `VERIFIED` | Yes |
| `VERIFIED` | `WATCHLIST` | **No** — consensus fails, retry |

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
