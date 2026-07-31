# GenLayer integration architecture

Trust Africa treats the deployed intelligent contract as the source of truth. Flask serves the frontend and deployment metadata; it does not adjudicate, settle, cache authoritative trades, or expose an alternative write API.

## Clients

The browser creates two `genlayer-js` clients:

- `readClient`: configured with the selected GenLayer chain and used for `get_trade`, `get_trust_passport`, `get_full_trust_report`, and receipt polling.
- `writeClient`: configured with the connected wallet account and `window.ethereum`; used for `create_trade`, `validate_trade`, and `resolve_dispute`.

The network and deployed address are injected with `VITE_GENLAYER_NETWORK` and `VITE_GENLAYER_CONTRACT_ADDRESS`.

## Finality rule

Every write returns a transaction hash. The browser waits for `TransactionStatus.FINALIZED`, checks `txExecutionResultName`, and only then reads or renders contract state. A finalized transaction with a failed execution result is surfaced as an error and cannot advance the UI workflow.

## Contract boundary

The contract owns:

- participant addresses and trade state;
- consensus-backed validation and dispute decisions;
- escrow held, released, and refunded counters;
- one-time settlement and reputation accounting;
- owner-only reputation/passport administration.

The frontend owns presentation and wallet interaction. Flask owns only file delivery, `/health`, and read-only `/config` metadata.

## State transitions

```text
CREATED → SETTLED
CREATED → REVIEW_REQUIRED → SETTLED
CREATED → REVIEW_REQUIRED → MANUAL_REVIEW
SETTLED → no further processing
```

The state payload includes `validation_completed`, `dispute_resolved`, `settled`, `settlement_accounted`, and `status`. Funds are placed in the held counter once at creation and removed once by the guarded settlement helper.
