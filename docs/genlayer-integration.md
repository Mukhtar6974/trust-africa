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

## AI Judge and Escrow Engine — GenLayer Equivalence Principle

`validate_trade()` uses `gl.eq_principle.prompt_comparative`. Each validator
independently calls the AI with the full trade context (buyer, seller, product,
amount, evidence). A comparison LLM then checks that the `decision` fields match.
No keyword rules are used.

| AI consensus verdict | Escrow action |
|---|---|
| `APPROVED` | `RELEASE_FUNDS` |
| `REJECTED` | `REFUND_BUYER` |
| `REVIEW_REQUIRED` | `HOLD_ESCROW` |

The equivalence principle: `decision` must be exactly the same across validators.
`confidence`, `risk`, and `reason` may differ and are not compared.

## Dispute Resolution — GenLayer Equivalence Principle

`resolve_dispute()` uses `gl.eq_principle.prompt_comparative`. Each validator
independently asks the AI to weigh the buyer's claim, seller's response, and
supporting evidence. A comparison LLM checks that the `decision` fields match.
No keyword rules are used.

| AI consensus verdict | Action |
|---|---|
| `RELEASE_FUNDS` | Escrow released to seller; seller gains dispute win |
| `REFUND_BUYER` | Escrow refunded to buyer; buyer gains dispute win |
| `MANUAL_REVIEW` | Escrow held; no reputation change |

The equivalence principle: `decision` must be exactly the same across validators.
`reason` may differ and is not compared.

## Deployment Path

1. Lint with `genvm-lint check contracts/trust_africa_intelligent_contract.py`.
2. Run direct state-transition tests.
3. Run full integration tests against a GenLayer environment to verify validator agreement.
4. Deploy the contract with the pinned runner.
5. Configure the backend indexer with the deployed address.
6. Treat accepted/finalized contract events as the authoritative API state.
