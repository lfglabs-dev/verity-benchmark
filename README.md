# verity-benchmark

Reproducible benchmark scaffold for evaluating Verity-based specification and proof workflows on real protocol slices.

This repository pins:
- Lean toolchain: `leanprover/lean4:v4.22.0`
- Verity dependency: `Th0rgal/verity@34a6b2b2e91713f870572fef1e1c4b5131812dfb`

Current status:
- `ready`: 2 cases with compileable Verity translations and frozen simple specs
- `blocked` or `pending`: 6 cases kept visible with explicit manifests and rationale

Repository layout:
- `Benchmark/`: canonical Lean modules that must compile under `lake build`
- `cases/`: benchmark-facing case directories with metadata, review notes, and thin Lean wrappers
- `benchmark-inventory.json`: machine-readable case inventory
- `REPORT.md`: short status report
- `scripts/check.sh`: top-level build/check entrypoint

Design choices:
- One folder per benchmark case
- One selected contract per project unless scope is private or still ambiguous
- Simple frozen specs only
- `ready` means the Verity slice typechecks today; it does not mean the case is fully proved
- Abstractions are documented case-by-case, especially where external crypto, Merkle proofs, encrypted types, or protocol-wide state are reduced to a benchmarkable slice

Check all ready cases with:

```bash
./scripts/check.sh
```
