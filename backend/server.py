from flask import Flask, jsonify, request
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

amina_score = 65
kwame_score = 85

@app.route("/")
def home():
    return """
    <h1>Trust Africa Platform</h1>
    <p>Status: ACTIVE</p>
    """

@app.route("/marketplace")
def marketplace():
    return jsonify({
        "seller": "Kwame",
        "product": "500 textile materials",
        "price": 2000
    })

@app.route("/trade")
def trade():
    return jsonify({
        "buyer": "Amina",
        "seller": "Kwame",
        "amount": 2000,
        "status": "RELEASE_FUNDS"
    })

@app.route("/reputation")
def reputation():
    return jsonify({
        "amina_score": amina_score,
        "kwame_score": kwame_score
    })

@app.route("/dispute")
def dispute():
    return jsonify({
        "decision": "Seller fulfilled obligations",
        "action": "Funds released to seller",
        "confidence": "96%"
    })

@app.route("/resolve-dispute", methods=["POST"])
def resolve_dispute():
    payload = request.get_json(silent=True) or {}
    buyer_claim = str(payload.get("buyer_claim", "")).lower()
    seller_response = str(payload.get("seller_response", "")).lower()
    seller_has_evidence = any(
        keyword in seller_response for keyword in ("proof", "receipt", "delivered")
    )

    if "not delivered" in buyer_claim and not seller_has_evidence:
        result = {
            "decision": "REFUND_BUYER",
            "risk_level": "HIGH",
            "confidence": "94%",
            "reason": "Seller did not provide valid delivery proof"
        }
    elif seller_has_evidence:
        result = {
            "decision": "RELEASE_FUNDS",
            "risk_level": "LOW",
            "confidence": "96%",
            "reason": "Seller provided valid delivery proof"
        }
    else:
        result = {
            "decision": "MANUAL_REVIEW",
            "risk_level": "MEDIUM",
            "confidence": "70%",
            "reason": "Available claims and evidence are inconclusive"
        }

    return jsonify(result)

@app.route("/contract-trust")
def contract_trust():
    return jsonify({
        "source": "GenLayer Intelligent Contract",
        "trade_validation": "APPROVED",
        "trust_score": 92,
        "risk_level": "LOW",
        "certificate_status": "VERIFIED",
        "decision": "Escrow can release funds after trade confirmation"
    })

@app.route("/trust-analysis")
def trust_analysis():
    return jsonify({
        "score": 92,
        "risk": "LOW",
        "recommendation": "SAFE TO TRADE"
    })

@app.route("/fraud-check")
def fraud_check():
    return jsonify({
        "risk_level": "LOW",
        "fraud_score": 8,
        "recommendation": "Trader appears legitimate"
    })

@app.route("/risk-dashboard")
def risk_dashboard():
    return jsonify({
        "active_trades": 3,
        "safe_trades": 2,
        "disputed_trades": 1,
        "fraud_alerts": 0,
        "system_status": "HEALTHY"
    })

@app.route("/trade/create")
def create_trade():
    global amina_score, kwame_score

    amina_score += 1
    kwame_score += 1

    return jsonify({
        "trade_id": "TRADE003",
        "buyer": "New Buyer",
        "seller": "New Seller",
        "amount": 5000,
        "status": "OPEN"
    })

@app.route("/trust-certificate")
def trust_certificate():
    return jsonify({
        "certificate_id": "TA-2026-001",
        "status": "VERIFIED",
        "trust_score": 92,
        "issuer": "Trust Africa AI"
    })

@app.route("/escrow-status")
def escrow_status():
    return jsonify({
        "escrow_status": "LOCKED",
        "buyer": "New Buyer",
        "seller": "New Seller",
        "amount": 5000,
        "condition": "Funds locked until seller provides valid proof",
        "ai_decision": "WAITING_FOR_EVIDENCE"
    })

@app.route("/validate-evidence", methods=["POST"])
def validate_evidence():
    payload = request.get_json(silent=True) or {}
    evidence = str(payload.get("evidence", "")).lower()

    if any(keyword in evidence for keyword in ("scam", "fake", "fraud")):
        result = {
            "decision": "REJECTED",
            "risk_level": "HIGH",
            "trust_score": 20,
            "certificate_status": "REJECTED",
            "reason": "Evidence contains high-risk fraud indicators"
        }
    elif any(keyword in evidence for keyword in ("receipt", "delivered", "confirmed", "proof")):
        result = {
            "decision": "APPROVED",
            "risk_level": "LOW",
            "trust_score": 92,
            "certificate_status": "VERIFIED",
            "reason": "Evidence appears valid"
        }
    else:
        result = {
            "decision": "PENDING",
            "risk_level": "MEDIUM",
            "trust_score": 60,
            "certificate_status": "PENDING",
            "reason": "More evidence is required for validation"
        }

    return jsonify(result)

if __name__ == "__main__":
    app.run(debug=True)
