from flask import Flask, jsonify
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

if __name__ == "__main__":
    app.run(debug=True)
