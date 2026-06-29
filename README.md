# Trust Africa

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

The AI Trade Judge is a **non-deterministic GenLayer consensus call**. It does not use
keyword matching. Multiple validators independently ask an AI to evaluate the full trade
context and the result is accepted on-chain only when a majority agree on the decision.

| Decision | Meaning |
|---|---|
| `APPROVED` | AI consensus: evidence demonstrates a legitimate, completed trade |
| `REJECTED` | AI consensus: evidence shows fraud, deception, or policy violation |
| `REVIEW_REQUIRED` | AI consensus: evidence is ambiguous or incomplete |

Every response includes a numeric confidence score and human-readable reason from the
consensus round.

## Autonomous Escrow Engine

| Trust decision | Escrow action |
|---|---|
| APPROVED | RELEASE_FUNDS |
| REJECTED | REFUND_BUYER |
| REVIEW_REQUIRED | HOLD_ESCROW |

The API exposes current status plus total released, refunded, and held value.

## AI Dispute Resolution

Disputes accept a buyer claim, seller response, and evidence.

Resolution is a **non-deterministic GenLayer consensus call**: multiple validators
independently ask an AI to weigh both parties' arguments and the result is accepted
only when a majority agree on the escrow outcome.

| Decision | Meaning |
|---|---|
| `RELEASE_FUNDS` | AI consensus: seller's position is credible; release escrow |
| `REFUND_BUYER` | AI consensus: buyer's position is credible; refund escrow |
| `MANUAL_REVIEW` | AI consensus: evidence is conflicting; human arbitration needed |

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

## Non-Deterministic GenLayer Consensus

Trust Africa's three core trust decisions are made through **AI validator consensus**, not fixed keyword rules. Each decision function submits the full context to an AI and requires independent validator agreement before any on-chain state changes.

| Function | Decision options | Why AI consensus? |
|---|---|---|
| `validate_trade()` | `APPROVED` / `REJECTED` / `REVIEW_REQUIRED` | Evidence credibility is contextual and subjective |
| `resolve_dispute()` | `RELEASE_FUNDS` / `REFUND_BUYER` / `MANUAL_REVIEW` | Dispute claims require holistic judgment across both parties |
| `issue_trust_passport()` | `VERIFIED` / `WATCHLIST` / `UNVERIFIED` | Trade history requires AI holistic assessment, not a score threshold |

### How consensus works — GenLayer Equivalence Principle

Each decision function uses `gl.eq_principle.prompt_comparative`:

1. A **leader** validator runs `get_verdict()` and produces a structured result.
2. Each subsequent **validator** independently reruns `get_verdict()`.
3. A **comparison LLM** receives both outputs and checks them against the principle string.
4. The on-chain result is accepted only when a **majority of validators pass the comparison**.
5. Validators may produce different explanations — only the decision/status field must match.

```python
verdict = gl.eq_principle.prompt_comparative(
    get_verdict,
    principle="The `decision` field must be exactly the same. reason may differ.",
)
```

```
APPROVED  +  "receipt confirmed"   ==  APPROVED  +  "invoice verified"  → consensus passes
APPROVED  vs  REJECTED                                                   → consensus fails, rotate validator
```

This means keyword-crafted evidence cannot manipulate the outcome: a malicious actor would need to convince an independent majority of AI validators, each re-evaluating the evidence from scratch.

### Why not keyword rules?

The original implementation used `if "receipt" in evidence` and `if "fraud" in evidence` — deterministic keyword matching. This was rejected by the GenLayer team because:

- It does not use consensus for anything meaningful; any single node produces the same output
- It is trivially gameable by including or excluding specific words
- It does not reflect the subjective, contextual judgment that real trade evidence requires

See [docs/genlayer-nondeterministic-consensus.md](docs/genlayer-nondeterministic-consensus.md) for the full technical explanation.

## Why GenLayer

Trust Africa uses GenLayer intelligent contracts because trade evidence evaluation, dispute resolution, and business trust assessment are **inherently subjective** tasks. They require the kind of contextual judgment that:

- Cannot be reduced to deterministic rules without being gameable
- Needs multi-party independent verification to be trustworthy
- Has real financial consequences (escrow release, refund, or hold)
- Must be auditable and on-chain for dispute appeals

Escrow can autonomously release funds, refund the buyer, or hold settlement for review — but only after independent AI validators agree. Business Trust Passports update over time as verified trades, successful deliveries, disputes, and fraud signals build a portable reputation history.

## Demo Workflow

```text
Create Protected Trade
        → Submit Evidence
        → AI Trade Judge
        → Trust Certificate
        → Escrow Release / Refund / Hold
        → Trust Passport Update
```

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
# Unit tests — no external dependencies, run immediately
py -3.14 -m pytest tests/test_trust_engine.py -v

# Lint the intelligent contract
genvm-lint check contracts/trust_africa_intelligent_contract.py

# Direct contract tests — require GenVM binary (downloaded automatically on first run)
py -3.14 -m pytest tests/direct/ -v
```

Unit tests: **4 passed**. Direct tests skip automatically when the GenVM binary
cannot be downloaded (no failure noise). They validate AI decision correctness and
state-transition consistency once the GenVM runtime is available.

## Screenshots

The repository includes an earlier dashboard screenshot at [Screenshot 2026-06-19 183231.png](Screenshot%202026-06-19%20183231.png). Replace it with a V6 product screenshot after deployment.

## Future Roadmap

- Real GenLayer deployment
- Wallet connection
- USDC escrow
- Business verification
- Document upload
- Courier and tracking API verification
- Multi-agent AI dispute council

## Submission Highlights

- GenLayer Intelligent Contract
- AI Trade Judge
- Autonomous Escrow
- Evidence-Based Dispute Resolution
- Dynamic Trust Passports
- Cross-Border Trade Intelligence
- Professional SaaS Frontend

## License

MIT
