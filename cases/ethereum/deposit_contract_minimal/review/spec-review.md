# Spec review

Plain-English mapping:
- `deposit_increments_deposit_count_spec`: every accepted deposit consumes one fresh index.
- `deposit_preserves_full_count_for_small_deposit_spec`: non-full deposits do not affect the full-deposit counter.
- `deposit_increments_full_count_for_full_deposit_spec`: full deposits increment that counter.
- `deposit_starts_chain_at_threshold_spec`: crossing the threshold flips the chain-start flag.

Why this matches the intended property:
- The real contract's most benchmarkable local behavior is counter maintenance plus threshold activation.
- These specs stay narrow and avoid pretending the benchmark currently models the full Merkle tree.

Known uncertainties:
- The source contract is Vyper, not Solidity.
- The tree and hash semantics are intentionally abstracted away in this first benchmark version.
