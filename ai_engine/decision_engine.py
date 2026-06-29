"""
LEGACY PROTOTYPE — NOT USED BY THE PRODUCTION CONTRACT.

This file is a very early-stage sketch from before the GenLayer integration.
The evidence-count logic below is the original deterministic approach that was
replaced. It has no connection to the deployed intelligent contract.

The production decision logic lives in:
    contracts/trust_africa_intelligent_contract.py

The three production decision functions (validate_trade, resolve_dispute,
issue_trust_passport) all use gl.eq_principle.prompt_comparative with
gl.nondet.exec_prompt. None of them use evidence counts or keyword rules.
"""

# --------------------------------------------------------------------------
# Original sketch kept for project history only — never call this.
# --------------------------------------------------------------------------

def _legacy_evaluate_trade(evidence_count):  # noqa: dead code
    if evidence_count >= 3:
        return {"decision": "RELEASE_FUNDS", "confidence": 90, "reason": "High confidence."}
    elif evidence_count >= 1:
        return {"decision": "REQUEST_MORE_EVIDENCE", "confidence": 60, "reason": "Additional evidence required."}
    else:
        return {"decision": "HUMAN_VALIDATORS", "confidence": 30, "reason": "AI uncertainty is too high."}
