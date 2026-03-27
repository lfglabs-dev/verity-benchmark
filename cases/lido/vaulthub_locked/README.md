# vaulthub_locked

Source:
- `lidofinance/core` (feat/vaults branch)
- commit `96738395ca3bffd6513700a45d4c9389662c5835`
- file `contracts/0.8.25/vaults/VaultHub.sol`

Focus:
- `_locked` (collateral lock computation)
- `getPooledEthBySharesRoundUp` (axiomatised share-to-ether conversion)
- Certora F-01: locked funds solvency inequality
- Certora P-VH-03: reserve ratio bounds
- Certora P-VH-04: maxLiabilityShares bound

Model:
- `Benchmark.Cases.Lido.VaulthubLocked.Contract` defines pure arithmetic helpers
  (`ceilDiv`, `getPooledEthBySharesRoundUp`, `locked`) plus an executable Verity
  contract entrypoint `syncLocked`.
- `syncLocked` reads the benchmark inputs from storage slots `0..5`, computes the
  locked amount, stores it in slot `6`, and returns it.
- `Benchmark.Cases.Lido.VaulthubLocked.Specs` states F-01 over the post-state of
  that contract execution, while `Proofs.lean` bridges the executable contract
  back to the pure arithmetic model.

Verification:
- `lake build Benchmark.Cases.Lido.VaulthubLocked.Compile` checks the reference
  implementation and proofs for the case.
- `./scripts/run_case.sh lido/vaulthub_locked` runs the case's declared
  `lean_target` and records the result under `results/`.
- Files under `Benchmark/Generated/Lido/VaulthubLocked/Tasks/` are public,
  editable proof templates. They are expected to contain holes until a benchmark
  agent or user fills them in, so they are not part of the green reference build.

Out of scope:
- Oracle, LazyOracle, OperatorGrid
- mintShares, burnShares, rebalance state transitions
- Vault connection lifecycle
- Redemptions and force-exit logic
