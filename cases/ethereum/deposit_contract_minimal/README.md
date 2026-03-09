# deposit_contract_minimal

Selected from `ethereum/deposit_contract` at `691feb18330d3d102b5a4b3d4434fac7571f51b8`.

What is selected:
- Contract: `deposit_contract/contracts/validator_registration.v.py`
- Function: `deposit`
- Benchmark focus: deposit counters and chain-start threshold logic

Frozen specs:
- `depositCount` increments by one
- small deposits preserve `fullDepositCount`
- full deposits increment `fullDepositCount`
- reaching the full-deposit threshold sets `chainStarted`

Intentionally left out:
- SSZ and SHA-256 tree computation
- event logs
- byte-length checks on pubkey, credentials, and signature
