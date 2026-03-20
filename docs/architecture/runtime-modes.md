# Runtime Modes

All modes use the same task contract and evaluator.

`strict`
- no agent-visible tools
- agent returns one final proof file

`interactive`
- same contract
- adds `read_public_file`, `write_editable_proof`, `run_lean_check`, `inspect_lean_goals`, and `search_public_defs`

`custom`
- calls an external command adapter
- still uses the same file allowlist and final evaluation
