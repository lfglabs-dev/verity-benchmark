## Status

This case remains a backlog candidate.

On 2026-03-22, the four reference theorems for
`Benchmark.Cases.UniswapV2.PairFeeAdjustedSwap` were proved and validated
locally in an untracked `Benchmark/Cases/UniswapV2/PairFeeAdjustedSwap/Proofs.lean`
file, but that proof source is intentionally not committed.

Validation run locally:

```bash
python3 scripts/validate_manifests.py
timeout 600s lake build Benchmark.Cases.UniswapV2.PairFeeAdjustedSwap.Proofs
```

Because the proof module is not committed, the generated task stubs in
`Benchmark/Generated/UniswapV2/PairFeeAdjustedSwap/Tasks/` still contain
`exact ?_` holes and this case is not promoted into the active suite.
