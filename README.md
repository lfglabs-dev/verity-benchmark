# verity-benchmark

Reproducible benchmark scaffold for evaluating Verity-based specification and proof workflows on real protocol slices. The repository is structured for agent use: one canonical manifest per case, one generator for derived metadata, and one runner contract for per-case or suite-wide execution.

This repository pins:
- Lean toolchain: `leanprover/lean4:v4.22.0`
- Verity dependency: `Th0rgal/verity@34a6b2b2e91713f870572fef1e1c4b5131812dfb`

Current status:
- Active `cases/`: 4 concrete benchmark cases
- Buildable `build_green`: 2 cases with compileable Verity translations and frozen simple specs
- Active `scoped`: 2 concrete targets that are pinned but not yet runnable
- `backlog/`: 4 placeholders kept visible without polluting the active suite

Repository layout:
- `Benchmark/`: canonical Lean modules that must compile under `lake build`
- `cases/`: active benchmark cases with canonical `case.yaml` manifests
- `backlog/`: non-runnable placeholders and intake candidates
- `benchmark-inventory.json`: generated machine-readable inventory
- `REPORT.md`: generated status report
- `results/`: JSON outputs emitted by the runner scripts
- `scripts/generate_metadata.py`: regenerates the inventory and report from manifests
- `scripts/run_case.sh`: agent entrypoint for one case
- `scripts/run_all.sh`: agent entrypoint for all active cases
- `scripts/check.sh`: repo-level metadata and benchmark check

Design choices:
- One folder per benchmark case
- One selected contract per project unless scope is still ambiguous
- Simple frozen specs only
- `case.yaml` is the only source of truth for benchmark state
- Stages are intentionally small: `candidate`, `scoped`, `build_green`, `proof_partial`, `proof_complete`
- `build_green` means the Verity slice typechecks today; it does not mean the case is fully proved
- Abstractions are documented case-by-case, especially where external crypto, Merkle proofs, encrypted types, or protocol-wide state are reduced to a benchmarkable slice

Regenerate metadata:

```bash
python3 scripts/generate_metadata.py
```

Run one case:

```bash
./scripts/run_case.sh ethereum/deposit_contract_minimal
```

Run all active cases:

```bash
./scripts/run_all.sh
```

Check metadata and all runnable cases:

```bash
./scripts/check.sh
```
