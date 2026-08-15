# Trust Africa

Trust Africa is a GenLayer-native trade trust application. Its intelligent
contract is the only authoritative source for trades, AI validation, disputes,
trust passports, trust reports, and settlement accounting.

## Architecture

- `contracts/trust_africa_intelligent_contract.py` owns all authoritative state.
- `frontend/index.html` uses `genlayer-js` directly. Reads call contract view
  methods; writes are signed by the connected browser wallet and finalized
  before the UI reads the resulting state.
- `backend/server.py` is an optional read-only HTTP facade. It calls the deployed
  contract through the GenLayer CLI and rejects every state-changing request.
- `backend/trust_engine.py` is retained only as a deterministic historical demo
  used by demo tests. It is not imported by the production server or browser.

The contract uses `gl.nondet.exec_prompt` inside
`gl.eq_principle.prompt_comparative` for `validate_trade`, `resolve_dispute`, and
`issue_trust_passport`. No deterministic keyword logic replaces consensus.

## Contract methods used by the application

Wallet-signed writes:

- `create_trade(trade_id, buyer, buyer_address, seller, seller_address, product, amount, evidence)`
- `validate_trade(trade_id, evidence)`
- `resolve_dispute(trade_id, buyer_claim, seller_response, evidence)`
- `issue_trust_passport(business)`

Finalized reads:

- `get_trade(trade_id)`
- `get_trust_passport(business)`
- `get_full_trust_report(trade_id)`

The caller must be the stored buyer or seller to create, validate, or resolve a
trade. Terminal outcomes (`APPROVED`, `REJECTED`, `RELEASE_FUNDS`, and
`REFUND_BUYER`) set `finalized` and cannot be processed again. Manual review
keeps a trade open and accounts its held amount once, even across repeated
reviews.

Settlement fields are accounting records only. This repository does **not**
transfer USDC or another token.

## Configuration

After deploying the contract, set these two meta tags in `frontend/index.html`:

```html
<meta name="genlayer-contract-address" content="0xYOUR_DEPLOYED_ADDRESS">
<meta name="genlayer-network" content="studionet">
```

Supported frontend network names are `localnet`, `studionet`,
`testnetAsimov`, and `testnetBradbury`.

For the optional read-only Flask facade, set:

```text
TRUST_AFRICA_CONTRACT_ADDRESS=0xYOUR_DEPLOYED_ADDRESS
TRUST_AFRICA_RPC_URL=https://YOUR_GENLAYER_RPC
TRUST_AFRICA_NETWORK=studionet
TRUST_AFRICA_CORS_ORIGINS=https://your-frontend.example
```

The backend requires the `genlayer` CLI on `PATH`. Start it with:

```bash
python backend/server.py
```

Serve the frontend over HTTP rather than opening it as a `file://` URL.

## Quality checks

```bash
genvm-lint check contracts/trust_africa_intelligent_contract.py
pytest tests -v
```

Direct tests include regressions for duplicate validation, repeated manual
review, unauthorized settlement, and processing attempts after final settlement.
Run full consensus integration tests against a configured GenLayer environment
before deployment.

## Deployment

```bash
genlayer deploy --contract contracts/trust_africa_intelligent_contract.py
genlayer schema 0xYOUR_DEPLOYED_ADDRESS
```

Then configure the frontend and optional backend with the returned address and
the same network/RPC. A prior deployment must be replaced because the contract
method signature and stored trade schema now include participant addresses and
explicit finalization.
