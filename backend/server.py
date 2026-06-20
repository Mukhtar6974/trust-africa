from flask import Flask, jsonify, request
from flask_cors import CORS

try:
    from backend.trust_engine import engine
except ModuleNotFoundError:  # Supports `python backend/server.py`.
    from trust_engine import engine

app = Flask(__name__)
CORS(app)

@app.route("/")
def home():
    return """
    <h1>Trust Africa</h1>
    <p>AI-powered trust infrastructure for African commerce</p>
    <p>Status: ACTIVE</p>
    """

@app.route("/marketplace")
def marketplace():
    return jsonify({
        "seller": "Lagos Textile Export Ltd",
        "product": "500 premium textile units",
        "price": 2000,
        "active_routes": 5
    })

@app.route("/trade")
def trade():
    return jsonify(engine.trades[engine.latest_trade_id])

@app.route("/reputation")
def reputation():
    buyer = engine.passport("Accra Retail Partners")
    seller = engine.passport("Lagos Textile Export Ltd")
    return jsonify({"amina_score": buyer["trust_score"], "kwame_score": seller["trust_score"], "buyer": buyer, "seller": seller})

@app.route("/dispute")
def dispute():
    return jsonify({
        "decision": "RELEASE_FUNDS",
        "action": "Escrow released after delivery proof",
        "confidence": 96
    })

@app.route("/resolve-dispute", methods=["POST"])
def resolve_dispute():
    return jsonify(engine.resolve_dispute(request.get_json(silent=True) or {}))

@app.route("/contract-trust")
def contract_trust():
    latest = engine.latest_decision
    return jsonify({
        "source": "GenLayer Intelligent Contract",
        "trade_validation": latest["decision"],
        "trust_score": engine.passport(engine.trades[engine.latest_trade_id]["seller"])["trust_score"],
        "risk_level": latest["risk"],
        "certificate_status": latest["certificate_status"],
        "decision": latest["escrow_decision"]
    })

@app.route("/trust-analysis")
def trust_analysis():
    latest = engine.latest_decision
    return jsonify({
        "score": engine.passport(engine.trades[engine.latest_trade_id]["seller"])["trust_score"],
        "risk": latest["risk"],
        "recommendation": latest["decision"]
    })

@app.route("/fraud-check")
def fraud_check():
    latest = engine.latest_decision
    return jsonify({
        "risk_level": latest["risk"],
        "fraud_score": 8 if latest["risk"] == "LOW" else 90 if latest["risk"] == "HIGH" else 45,
        "recommendation": latest["reason"]
    })

@app.route("/risk-dashboard")
def risk_dashboard():
    decisions = [trade["decision"] for trade in engine.trades.values()]
    return jsonify({
        "active_trades": len(decisions),
        "safe_trades": decisions.count("APPROVED"),
        "disputed_trades": decisions.count("REJECTED"),
        "fraud_alerts": decisions.count("REJECTED"),
        "system_status": "HEALTHY" if "REJECTED" not in decisions[-1:] else "ALERT"
    })

@app.route("/trade/create", methods=["GET", "POST"])
def create_trade():
    if request.method == "POST":
        return jsonify(engine.adjudicate_trade(request.get_json(silent=True) or {}))
    return jsonify({"trade_id": "TRADE003", "buyer": "Nairobi Agro Supply", "seller": "Kigali Logistics Hub", "amount": 5000, "status": "OPEN"})

@app.route("/trust-certificate")
def trust_certificate():
    latest_trade = engine.trades[engine.latest_trade_id]
    passport = engine.passport(latest_trade["seller"])
    return jsonify({
        "certificate_id": f"TA-{latest_trade['trade_id']}",
        "status": passport["verification_status"],
        "trust_score": passport["trust_score"],
        "issuer": "Trust Africa GenLayer Network"
    })

@app.route("/escrow-status")
def escrow_status():
    return jsonify(engine.escrow_status())

@app.route("/validate-evidence", methods=["POST"])
def validate_evidence():
    payload = request.get_json(silent=True) or {}
    result = engine.judge(str(payload.get("evidence", "")))
    score = 92 if result["decision"] == "APPROVED" else 20 if result["decision"] == "REJECTED" else 60
    return jsonify({**result, "risk_level": result["risk"], "trust_score": score})

@app.route("/ai-judge", methods=["POST"])
def ai_judge():
    return jsonify(engine.adjudicate_trade(request.get_json(silent=True) or {}))

@app.route("/trust-passports")
def trust_passports():
    return jsonify({"passports": engine.passport_list()})

@app.route("/trust-passport/<path:business>")
def trust_passport(business):
    return jsonify(engine.passport(business))

@app.route("/trust-events")
def trust_events():
    return jsonify({"events": engine.events[:10]})

@app.route("/cross-border-activity")
def cross_border_activity():
    return jsonify({"routes": [
        {"route": "Nigeria → Ghana", "active_trade_value": 185000},
        {"route": "Kenya → Uganda", "active_trade_value": 132500},
        {"route": "Rwanda → Tanzania", "active_trade_value": 98000},
        {"route": "South Africa → Botswana", "active_trade_value": 245000},
        {"route": "Egypt → Morocco", "active_trade_value": 176000},
    ]})

@app.route("/full-trust-report")
def full_trust_report():
    return jsonify(engine.report())

if __name__ == "__main__":
    app.run(debug=True)
