# Benchmark report

## Ready cases

### `paladin_votes/stream_recovery_claim_usdc`
- Selected contract: `StreamRecoveryClaim`
- Selected function slice: `claimUsdc` / `_claimUsdc`
- Frozen specs:
  - claimant is marked claimed
  - `roundUsdcClaimed` increases by the computed payout
  - `totalUsdcAllocated` decreases by the computed payout
  - post-state keeps `roundUsdcClaimed <= roundUsdcTotal`
- Simplifications:
  - specialized to a single active round
  - Merkle verification becomes a boolean parameter
  - ERC20 transfer side effects are omitted

### `ethereum/deposit_contract_minimal`
- Selected contract: `validator_registration.v.py`
- Selected function slice: `deposit`
- Frozen specs:
  - `depositCount` increments by one
  - small deposits do not change `fullDepositCount`
  - full deposits increment `fullDepositCount`
  - hitting the threshold sets `chainStarted`
- Simplifications:
  - source is Vyper rather than Solidity
  - SSZ hashing, Merkle tree updates, and logs are omitted

## Blocked or pending cases

- `ethereum/beacon_roots_predeploy`: EIP text is known, but this repo does not yet pin a concrete implementation artifact in the benchmark.
- `zama/erc7984`: selected, but current Verity benchmark slice is blocked on encrypted `euint64` and FHE-specific semantics.
- `nexus_mutual/placeholder`: blocked until a concrete contract/function target is agreed.
- `kleros/placeholder`: blocked until a concrete contract/function target is agreed.
- `unlink_xyz/placeholder`: blocked because the referenced GitHub repository was not resolvable during benchmark setup.
- `usual/placeholder`: pending private access.

## Compile status

- `lake build`: required for all `ready` cases
- `./scripts/check.sh`: repository-level check command
