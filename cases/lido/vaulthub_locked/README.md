# vaulthub_locked

Source:
- `lidofinance/core` (feat/vaults branch)
- commit `5e51ea044b09e1e2606074e1fe4ff6b6a4eff172`
- file `contracts/0.8.25/vaults/VaultHub.sol`

Focus:
- `_locked` (collateral lock computation)
- `getPooledEthBySharesRoundUp` (axiomatised share-to-ether conversion)
- Certora F-01: locked funds solvency inequality
- Certora P-VH-03: reserve ratio bounds
- Certora P-VH-04: maxLiabilityShares bound

Out of scope:
- Oracle, LazyOracle, OperatorGrid
- mintShares, burnShares, rebalance state transitions
- Vault connection lifecycle
- Redemptions and force-exit logic
