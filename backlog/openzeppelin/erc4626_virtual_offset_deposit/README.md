## Status

This case is a backlog candidate for ERC-4626 rounding and inflation-attack
reasoning.

It models the OpenZeppelin virtual-offset defense with a minimal state:
`totalAssets`, `totalShares`, `virtualAssets = 1`, and `virtualShares = 1000`.
The slice keeps the `previewDeposit` floor-division behavior and the
state-changing `deposit` update while omitting token transfers, withdrawals,
fees, and hooks.

Upstream references:

- OpenZeppelin ERC-4626 implementation:
  <https://github.com/OpenZeppelin/openzeppelin-contracts/blob/45f032d1bcf1a88b7bc90154d7eef76c87bf9d45/contracts/token/ERC20/extensions/ERC4626.sol>
- OpenZeppelin inflation-attack analysis:
  <https://blog.openzeppelin.com/a-novel-defense-against-erc4626-inflation-attacks>

The intended theorem tasks are:

1. `deposit_sets_totalAssets`
2. `deposit_sets_totalShares`
3. `previewDeposit_rounds_down`
4. `positive_deposit_mints_positive_shares_under_rate_bound`

The reference proof module is committed at
`Benchmark/Cases/OpenZeppelin/ERC4626VirtualOffsetDeposit/Proofs.lean`, so this
backlog case is runnable in the reference benchmark path.
