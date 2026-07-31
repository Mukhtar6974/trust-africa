# Trust Africa — GenLayer reviewer follow-up

## Deployment

- Network: `testnetBradbury` by default; override with `VITE_GENLAYER_NETWORK`.
- Contract address: not available in this checkout; supply the deployed address through `VITE_GENLAYER_CONTRACT_ADDRESS`.
- No address, transaction hash, finalized state, replay failure, or unauthorized-account result is claimed because no live deployment credentials were available.

## Reviewer feedback addressed

> The browser and API currently use the local in-memory keyword engine rather than the GenLayer contract. Connect the application to the submitted contract's real read and write methods, then add authorization and finalization so settled trades cannot be processed repeatedly.

The browser no longer calls Flask for decisions or state changes. It uses `genlayer-js` with separate read and wallet-signed write clients. Flask serves files and deployment metadata only. The removed `backend/trust_engine.py` is not an application dependency.

## On-chain flow

```text
Connect wallet
  → create_trade (write client)
  → wait FINALIZED + require FINISHED_WITH_RETURN
  → validate_trade (write client)
  → wait FINALIZED + require FINISHED_WITH_RETURN
  → get_trade / get_trust_passport / get_full_trust_report (read client)
  → if REVIEW_REQUIRED: resolve_dispute (write client)
  → wait FINALIZED + require FINISHED_WITH_RETURN
  → read the finalized report
```

The UI shows the wallet address, contract address, transaction hash, execution result, and finality status. State is never displayed from a write receipt unless `txExecutionResultName` is successful.

## State machine and authorization

```text
CREATED
 ├─ validate_trade(APPROVED) ───────────────→ SETTLED / RELEASE_FUNDS
 ├─ validate_trade(REJECTED) ───────────────→ SETTLED / REFUND_BUYER
 └─ validate_trade(REVIEW_REQUIRED) ────────→ REVIEW_REQUIRED
       ├─ resolve_dispute(RELEASE_FUNDS) ───→ SETTLED
       ├─ resolve_dispute(REFUND_BUYER) ─────→ SETTLED
       └─ resolve_dispute(MANUAL_REVIEW) ────→ MANUAL_REVIEW
```

The contract stores `buyer_address` and `seller_address`. Creation is buyer-only; validation and disputes are buyer-or-seller-only. Validation and dispute writes each have one-time flags. Disputes are accepted only from `REVIEW_REQUIRED` or `DISPUTE_PENDING`. A settled trade rejects every later settlement attempt. Escrow and reputation counters are changed in one guarded settlement helper, exactly once.

## Contract methods

- Writes: `create_trade`, `validate_trade`, `resolve_dispute`.
- Owner-only writes: `update_reputation`, `issue_trust_passport`.
- Reads: `get_trade`, `get_trust_passport`, `get_full_trust_report`.

The contract uses the pinned GenVM runner from its first-line `Depends` declaration and uses comparative GenLayer consensus for the validation, dispute, and passport decisions.

## Files changed

- `contracts/trust_africa_intelligent_contract.py`: secure state machine, participant checks, replay guards, and exact-once accounting.
- `frontend/index.html` and `frontend/app.js`: wallet connection, separate GenLayer clients, finalized receipt handling, direct reads/writes, and transaction observability.
- `backend/server.py`: static/config-only Flask boundary.
- `tests/direct/test_trust_africa_contract.py`: direct GenVM authorization, dispute, replay, and accounting tests.
- `tests/integration/test_trust_africa_flow.py`: finalized receipt/read integration coverage.
- `tests/test_frontend_onchain_flow.py`: frontend contract-flow guardrails.

## Commands and results

```powershell
genvm-lint check contracts/trust_africa_intelligent_contract.py
python -m pytest tests -v
gltest tests/integration/ -v -s --network testnet_bradbury
npm run check:frontend
npm run build
```

The fast GenVM linter passed 3 checks. The full linter validation and all direct GenVM tests were blocked while the sandbox denied downloading the pinned GenVM artifact (`WinError 10013`). The combined pytest result was 5 passed, 1 skipped, and 10 direct tests failed before contract execution. `npm run check:frontend` passed and `npm run build` passed with Vite 8.1.5. No live transaction was performed because the checkout has no deployed address, wallet approval, funded account, or GenLayer CLI.
