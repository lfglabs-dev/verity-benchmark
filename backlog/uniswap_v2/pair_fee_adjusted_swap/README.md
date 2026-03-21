# Uniswap V2 Pair Fee-Adjusted Swap

This candidate benchmark slice comes from the guarded reserve update in
`UniswapV2Pair.swap`, where Uniswap V2 enforces its fee-adjusted constant-product
condition before storing the new reserves.

Why this belongs in the benchmark:

- It adds AMM invariant reasoning, which is not covered by the current active suite.
- It stays close to economically meaningful production logic from a canonical protocol.
- The slice is compact enough for Lean/Verity while still requiring nontrivial guarded
  arithmetic reasoning over pre-state and post-state values.

Abstraction choices:

- Token transfers, callbacks, and routing are omitted.
- The benchmark takes post-transfer balances and inferred input amounts as direct inputs.
- The slice preserves the 0.3% fee-adjusted product guard and the final reserve writes.
