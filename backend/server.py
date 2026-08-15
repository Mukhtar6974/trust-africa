"""Read-only HTTP facade for finalized Trust Africa contract state.

All writes are deliberately rejected by this service. They must be signed by a
participant wallet in the browser and sent directly to GenLayer.
"""

import os

from flask import Flask, jsonify, request
from flask_cors import CORS

try:
    from backend.genlayer_gateway import (
        GenLayerConfigurationError,
        GenLayerReadError,
        gateway,
    )
except ModuleNotFoundError:  # Supports `python backend/server.py`.
    from genlayer_gateway import GenLayerConfigurationError, GenLayerReadError, gateway

app = Flask(__name__)
CORS(app, origins=os.getenv("TRUST_AFRICA_CORS_ORIGINS", "*").split(","))


@app.errorhandler(GenLayerConfigurationError)
def configuration_error(error):
    return jsonify({"error": str(error), "source": "genlayer"}), 503


@app.errorhandler(GenLayerReadError)
def contract_read_error(error):
    return jsonify({"error": str(error), "source": "genlayer"}), 502


@app.get("/")
def home():
    return jsonify({
        "application": "Trust Africa",
        "source_of_truth": "GenLayer intelligent contract",
        "writes": "browser wallet required",
    })


@app.get("/trade/<trade_id>")
def trade(trade_id):
    return jsonify(gateway.read("get_trade", trade_id))


@app.get("/trust-passport/<path:business>")
def trust_passport(business):
    return jsonify(gateway.read("get_trust_passport", business))


@app.get("/full-trust-report/<trade_id>")
def full_trust_report(trade_id):
    return jsonify(gateway.read("get_full_trust_report", trade_id))


@app.route("/trade/create", methods=["POST"])
@app.route("/validate-evidence", methods=["POST"])
@app.route("/ai-judge", methods=["POST"])
@app.route("/resolve-dispute", methods=["POST"])
@app.route("/trust-passport/issue", methods=["POST"])
def wallet_write_required():
    return jsonify({
        "error": "State changes must be wallet-signed and submitted directly to GenLayer",
        "contract_address": gateway.contract_address or None,
    }), 409


@app.get("/contract-config")
def contract_config():
    return jsonify({
        "contract_address": gateway.contract_address or None,
        "network": os.getenv("TRUST_AFRICA_NETWORK", "studionet"),
        "rpc_url": gateway.rpc_url or None,
    })


if __name__ == "__main__":
    app.run(debug=os.getenv("FLASK_DEBUG", "0") == "1")
