# Legacy / Prototype Backend Scripts

These files are early-stage Python prototypes from the initial project design phase.
They are **not part of the production backend** and are not imported by `backend/server.py`.

The production backend is:

```
backend/server.py        — read-only GenLayer contract API facade
backend/genlayer_gateway.py — real deployed-contract reads via GenLayer CLI
```

`backend/trust_engine.py` is historical deterministic demo/test code only.

These files are kept for project history only.
