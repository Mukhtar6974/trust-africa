"""
Trust Africa AI Decision Engine
"""


def evaluate_trade(evidence_count):

    if evidence_count >= 3:
        return {
            "decision": "RELEASE_FUNDS",
            "confidence": 90,
            "reason": "High confidence."
        }

    elif evidence_count >= 1:
        return {
            "decision": "REQUEST_MORE_EVIDENCE",
            "confidence": 60,
            "reason": "Additional evidence required."
        }

    else:
        return {
            "decision": "HUMAN_VALIDATORS",
            "confidence": 30,
            "reason": "AI uncertainty is too high."
        }


result = evaluate_trade(3)

print(result)