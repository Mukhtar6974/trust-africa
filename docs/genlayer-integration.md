# GenLayer-Native Architecture

## Consensus Boundary

Trust Africa separates product convenience from authoritative settlement.

- **Frontend and Flask own:** user experience, API previews, route indexing, cached analytics, and local demo state.
- **GenLayer owns:** trade creation, evidence verdicts, trust-passport state, reputation deltas, dispute outcomes, and escrow release/refund/hold transitions.
- **Businesses and logistics providers own:** invoices, receipts, tracking records, delivery proof, and claim evidence submitted for evaluation.

The Flask `TrustEngine` mirrors contract transitions for a fast local demo. It is not the final source of truth. In a deployed system, accepted GenLayer state is indexed back into the API and UI.

## Intelligent Decision Flow

```text
Business creates trade
        ↓
Evidence submitted to Trust Africa
        ↓
GenLayer validators evaluate the evidence rule
        ↓
APPROVED / REJECTED / REVIEW_REQUIRED
        ↓
RELEASE_FUNDS / REFUND_BUYER / HOLD_ESCROW
        ↓
Trust passports and reputation are updated
```

The V6 contract pins the production GenVM runner:

```text
py-genlayer:1jb45aa8ynh2a9c9xn3b7qqh8sm5q93hwfp7jqmwsfhh8jpz09h6
```

No `test`, `latest`, or unversioned runner alias is used.

## Intelligent Contract Interface

`contracts/trust_africa_intelligent_contract.py` exposes:

- `create_trade()` — records counterparties, value, product, and initial evidence.
- `validate_trade()` — produces the final trade verdict and escrow action.
- `resolve_dispute()` — compares buyer claims with seller response and evidence.
- `issue_trust_passport()` — issues or refreshes a business verification status.
- `update_reputation()` — applies bounded reputation changes.
- `get_full_trust_report()` — returns trade, passport, and escrow state together.

## Trust Passport State

Each passport stores:

- Trust score (bounded from 0 to 100)
- Completed trades
- Successful deliveries
- Disputes won
- Disputes lost
- Verification status

Reputation changes are applied automatically:

| Event | Score change |
|---|---:|
| Successful trade | +2 |
| Approved evidence | +3 |
| Dispute won | +2 |
| Fraud detected | -10 |
| Rejected evidence | -5 |

## AI Judge and Escrow Engine

The current V6 classifier provides a deterministic baseline suitable for direct testing:

- `receipt`, `proof`, `tracking`, `invoice`, or `delivered` → `APPROVED`
- `fraud`, `scam`, or `fake` → `REJECTED`
- anything else → `REVIEW_REQUIRED`

The verdict drives escrow without a separate operator:

- `APPROVED` → `RELEASE_FUNDS`
- `REJECTED` → `REFUND_BUYER`
- `REVIEW_REQUIRED` → `HOLD_ESCROW`

For production evidence that requires subjective document interpretation, this classifier is the normalization layer around a GenLayer comparative validator. Validators should independently analyze the same evidence and agree on the stable decision fields rather than trusting one leader's prose.

## Dispute Resolution

Disputes accept a buyer claim, seller response, and additional evidence:

- Non-delivery without proof → `REFUND_BUYER`
- Proof, receipt, tracking, or delivered evidence → `RELEASE_FUNDS`
- Inconclusive evidence → `MANUAL_REVIEW`

The winner receives a reputation increase, passport dispute counters change, and escrow state is updated in the same transition.

## Deployment Path

1. Lint with `genvm-lint check contracts/trust_africa_intelligent_contract.py`.
2. Run direct state-transition tests.
3. Run full integration tests against a GenLayer environment to verify validator agreement.
4. Deploy the contract with the pinned runner.
5. Configure the backend indexer with the deployed address.
6. Treat accepted/finalized contract events as the authoritative API state.
