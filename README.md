# Trust Africa V6

**GenLayer-native intelligent trust infrastructure for African commerce.**

Trust Africa helps businesses protect cross-border transactions with intelligent evidence validation, autonomous escrow decisions, business trust passports, dynamic reputation, and AI-assisted dispute resolution.

## Product Experience

The responsive SaaS frontend includes:

- A protected trade form and explainable AI decision card
- Live certificate and escrow outcomes
- Business Trust Passports with dynamic scores
- Recent trust events
- AI dispute resolution with evidence
- Five realistic African trade corridors and active values

## Architecture

```text
Browser (HTML/CSS/JavaScript)
        ↓
Flask API + local TrustEngine preview
        ↓
GenLayer Intelligent Contract
        ↓
Consensus verdict + escrow transition + passport update
```

- **Frontend:** product UI, form validation, result rendering, and API consumption.
- **Flask backend:** local preview engine, indexed views, route activity, and event feeds.
- **GenLayer contract:** authoritative trade, evidence, reputation, passport, dispute, and escrow state transitions.

See [GenLayer integration architecture](docs/genlayer-integration.md) for the consensus boundary and deployment path.

## Trust Passport

Every business passport tracks:

- Trust Score
- Completed Trades
- Successful Deliveries
- Disputes Won
- Disputes Lost
- Verification Status

Example seeded passports:

| Business | Trust Score | Completed Trades | Certificate |
|---|---:|---:|---|
| Lagos Textile Export Ltd | 91 | 145 | VERIFIED |
| Accra Retail Partners | 88 | 122 | VERIFIED |

### Dynamic Reputation Rules

| Event | Score change |
|---|---:|
| Successful trade | +2 |
| Approved evidence | +3 |
| Dispute won | +2 |
| Fraud detected | -10 |
| Rejected evidence | -5 |

Scores are bounded from 0 to 100 and update automatically after trade and dispute outcomes.

## AI Trade Judge

Inputs: buyer, seller, product, amount, and evidence.

| Evidence | Decision | Risk |
|---|---|---|
| receipt, proof, tracking, invoice, delivered | APPROVED | LOW |
| fraud, scam, fake | REJECTED | HIGH |
| anything else | REVIEW_REQUIRED | MEDIUM |

Every response includes a numeric confidence score and human-readable reason.

## Autonomous Escrow Engine

| Trust decision | Escrow action |
|---|---|
| APPROVED | RELEASE_FUNDS |
| REJECTED | REFUND_BUYER |
| REVIEW_REQUIRED | HOLD_ESCROW |

The API exposes current status plus total released, refunded, and held value.

## AI Dispute Resolution

Disputes accept a buyer claim, seller response, and evidence:

- Non-delivery without proof → `REFUND_BUYER`
- Proof, receipt, tracking, or delivered evidence → `RELEASE_FUNDS`
- Inconclusive evidence → `MANUAL_REVIEW`

Winning and losing passport records update in the same workflow.

## Cross-Border Commerce

The demo includes live sample values for:

- Nigeria → Ghana
- Kenya → Uganda
- Rwanda → Tanzania
- South Africa → Botswana
- Egypt → Morocco

## GenLayer Intelligent Contract

The production-pinned contract is at `contracts/trust_africa_intelligent_contract.py` and exposes:

- `create_trade()`
- `validate_trade()`
- `resolve_dispute()`
- `issue_trust_passport()`
- `update_reputation()`
- `get_full_trust_report()`

The contract pins `py-genlayer:1jb45aa8ynh2a9c9xn3b7qqh8sm5q93hwfp7jqmwsfhh8jpz09h6` and contains no local-only runner aliases.

## API

| Endpoint | Purpose |
|---|---|
| `POST /ai-judge` | Create and adjudicate a trade |
| `POST /validate-evidence` | Preview evidence classification |
| `POST /resolve-dispute` | Resolve a claim with evidence |
| `GET /escrow-status` | Escrow status and totals |
| `GET /trust-passports` | List business passports |
| `GET /trust-passport/<business>` | Read one passport |
| `GET /trust-events` | Recent platform events |
| `GET /cross-border-activity` | Trade corridors and active values |
| `GET /full-trust-report` | Latest trade, passports, escrow, and events |

All previous MVP routes remain available for compatibility.

## Run Locally

```bash
pip install flask flask-cors pytest
python backend/server.py
```

Open `frontend/index.html` in a browser. The API runs at `http://127.0.0.1:5000`.

## Validation

```bash
python -m pytest tests/test_trust_engine.py -v
genvm-lint lint contracts/trust_africa_intelligent_contract.py --json
python -m pytest tests/direct/test_trust_africa_contract.py -v
```

Direct tests require the GenVM artifact matching the pinned runner.

## Screenshots

The repository includes an earlier dashboard screenshot at [Screenshot 2026-06-19 183231.png](Screenshot%202026-06-19%20183231.png). Replace it with a V6 product screenshot after deployment.

## Future Roadmap

- Comparative GenLayer validator for subjective document interpretation
- On-chain passport discovery and portable business identity
- Appeals and multi-round commercial arbitration
- Stablecoin escrow settlement
- Regional compliance and logistics-oracle integrations
- Production indexer for accepted/finalized GenLayer events

## License

MIT
