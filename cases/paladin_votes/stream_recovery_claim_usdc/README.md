# stream_recovery_claim_usdc

Selected from `Figu3/sonic-earn-recovery-system` at `699cbbc79def374cab9739e451acbbf866293d12`.

What is selected:
- Contract: `src/StreamRecoveryClaim.sol`
- Functions: `claimUsdc`, `_claimUsdc`
- Benchmark focus: the accounting path that prevents a user claim from pushing `usdcClaimed` above `usdcTotal`

Frozen specs:
- claimant is marked claimed
- `roundUsdcClaimed` increases by the computed payout
- `totalUsdcAllocated` decreases by the computed payout
- post-state satisfies `roundUsdcClaimed <= roundUsdcTotal`

Intentionally left out:
- multi-round batching
- WETH flow
- actual Merkle verification and proof structure
- ERC20 transfer semantics
