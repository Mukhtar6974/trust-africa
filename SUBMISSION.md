# Trust Africa — Submission Notes

## Reviewer rejection addressed

The browser no longer sends trade decisions to the local keyword engine. It uses
`genlayer-js` to submit wallet-signed `create_trade`, `validate_trade`,
`resolve_dispute`, and `issue_trust_passport` transactions, waits for GenLayer
finalization, and renders `get_full_trust_report` contract state. The Flask API
is read-only and proxies real contract views; unsigned write endpoints return
HTTP 409.

`backend/trust_engine.py` remains solely as labeled historical demo/test code.
It is not an authoritative production path.

## Consensus implementation

The existing non-deterministic implementation is preserved. Trade validation,
dispute resolution, and passport issuance each call `gl.nondet.exec_prompt`
within `gl.eq_principle.prompt_comparative`. Validators compare the material
decision/status field. No keyword classifier is used on-chain.

The contract pins:

```text
py-genlayer:1jb45aa8ynh2a9c9xn3b7qqh8sm5q93hwfp7jqmwsfhh8jpz09h6
```

Business-rule failures continue to raise `gl.vm.UserError`.

## Authorization and idempotency

Each trade stores buyer and seller GenLayer addresses. Creation requires the
sender to be one of those addresses, and validation/dispute settlement is
limited to those same participants.

`finalized` is set for `APPROVED`, `REJECTED`, `RELEASE_FUNDS`, and
`REFUND_BUYER`. All later validation or settlement attempts revert. A
`REVIEW_REQUIRED` or `MANUAL_REVIEW` outcome remains non-final and uses
`funds_accounted` plus `HOLD_ESCROW` to ensure the amount enters `funds_held`
only once.

The settlement totals are contract accounting values. No direct USDC/token
transfer is implemented or claimed.

## Required deployment configuration

A new deployment is required because the trade schema and `create_trade`
signature changed. After deployment provide:

- contract address;
- network (`localnet`, `studionet`, `testnetAsimov`, or `testnetBradbury`);
- RPC URL for the optional Flask read facade;
- allowed production CORS origin(s).

Put the address/network in the frontend meta tags and export
`TRUST_AFRICA_CONTRACT_ADDRESS`, `TRUST_AFRICA_RPC_URL`, and
`TRUST_AFRICA_NETWORK` for Flask.

## Verification

Run:

```bash
genvm-lint check contracts/trust_africa_intelligent_contract.py
pytest tests -v
```

The direct suite contains dedicated regressions for duplicate validation,
repeated manual review, unauthorized settlement, and any processing after final
settlement. Full multi-validator consensus and browser-wallet smoke testing must
be run against the chosen deployed GenLayer network.
