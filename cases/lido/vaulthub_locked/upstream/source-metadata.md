# Upstream metadata

- Repository: https://github.com/lidofinance/core
- Branch: `feat/vaults`
- Commit: `5e51ea044b09e1e2606074e1fe4ff6b6a4eff172`
- Contract path: `contracts/0.8.25/vaults/VaultHub.sol`
- Functions of interest: `_locked`, `getPooledEthBySharesRoundUp`
- Source language: Solidity 0.8.25

Reason for selection:
- Certora formal verification report (December 2025) identified F-01 as a finding
  that could not be proven: the locked funds solvency inequality
- The property is self-contained arithmetic requiring ~5 axioms and ~10 lines of
  algebra with one case split
- Supporting invariants P-VH-03 and P-VH-04 were proven by Certora and serve as
  axioms/supporting lemmas for the main proof
