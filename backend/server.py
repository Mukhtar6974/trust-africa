import os
from pathlib import Path

from flask import Flask, jsonify, send_from_directory
from flask_cors import CORS


PROJECT_ROOT = Path(__file__).resolve().parents[1]
BUILT_FRONTEND_ROOT = PROJECT_ROOT / "dist" / "frontend"
FRONTEND_ROOT = BUILT_FRONTEND_ROOT if BUILT_FRONTEND_ROOT.exists() else PROJECT_ROOT / "frontend"

app = Flask(__name__, static_folder=str(FRONTEND_ROOT), static_url_path="")

cors_origins = os.getenv("TRUST_AFRICA_CORS_ORIGINS", "*")
CORS(
    app,
    resources={
        r"/*": {
            "origins": "*"
            if cors_origins == "*"
            else [origin.strip() for origin in cors_origins.split(",") if origin.strip()]
        }
    },
)


@app.get("/")
def home():
    return send_from_directory(FRONTEND_ROOT, "index.html")


@app.get("/health")
def health():
    return jsonify({"status": "ok", "source": "static frontend + GenLayer contract"})


@app.get("/config")
def config():
    return jsonify(
        {
            "network": os.getenv("VITE_GENLAYER_NETWORK", "testnetBradbury"),
            "contract_address": os.getenv("VITE_GENLAYER_CONTRACT_ADDRESS", ""),
        }
    )


@app.post("/ai-judge")
@app.post("/trade/create")
@app.post("/resolve-dispute")
def removed_state_changing_route():
    return jsonify({"error": "State-changing API routes were removed; use the GenLayer contract."}), 404


@app.get("/<path:filename>")
def frontend_file(filename: str):
    return send_from_directory(FRONTEND_ROOT, filename)


if __name__ == "__main__":
    app.run(debug=os.getenv("FLASK_DEBUG", "0") == "1")
