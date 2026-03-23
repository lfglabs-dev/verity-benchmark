## Status

This case remains a backlog candidate.

On 2026-03-22, the four reference theorems for
`Benchmark.Cases.UniswapV2.PairFeeAdjustedSwap` were proved and committed in
`Benchmark/Cases/UniswapV2/PairFeeAdjustedSwap/Proofs.lean`.

Validation run locally:

```bash
python3 scripts/validate_manifests.py
timeout 600s lake build Benchmark.Cases.UniswapV2.PairFeeAdjustedSwap.Proofs
```

The proof module now makes the backlog case runnable in the reference benchmark
path, while the generated task stubs in
`Benchmark/Generated/UniswapV2/PairFeeAdjustedSwap/Tasks/` still contain
`exact ?_` holes and the case remains backlog-scoped rather than promoted into
the active suite.
