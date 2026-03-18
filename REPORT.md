# Benchmark report

This report is generated from the per-case `case.yaml` manifests.

## Summary

- Active cases: 4
- Buildable active cases: 2
- Backlog entries: 4

## Buildable active cases

### `ethereum/deposit_contract_minimal`
- Stage: `build_green`
- Lean target: `Benchmark.Cases.Ethereum.DepositContractMinimal.Compile`
- Selected functions: `deposit`
- Source artifact: `deposit_contract/contracts/validator_registration.v.py`
- Notes: Counter-oriented slice of the deposit path. Merkle tree, SSZ hashing, and log emission are omitted so the benchmark can focus on threshold-driven state updates.

### `paladin_votes/stream_recovery_claim_usdc`
- Stage: `build_green`
- Lean target: `Benchmark.Cases.PaladinVotes.StreamRecoveryClaimUsdc.Compile`
- Selected functions: `claimUsdc`, `_claimUsdc`
- Source artifact: `src/StreamRecoveryClaim.sol`
- Notes: Single-round accounting slice of the USDC claim path. Merkle verification is abstracted as a boolean witness and token transfer side effects are omitted.

## Non-buildable active cases

### `ethereum/beacon_roots_predeploy`
- Stage: `scoped`
- Failure reason: `missing_implementation_artifact`
- Selected functions: `get`, `set`
- Source artifact: `EIPS/eip-4788.md`
- Notes: Candidate selected, but the benchmark currently lacks a pinned implementation artifact beyond the EIP text.

### `zama/erc7984`
- Stage: `scoped`
- Failure reason: `missing_verity_feature`
- Selected functions: `confidentialTransfer`, `confidentialTransferFrom`
- Source artifact: `contracts/token/ERC7984/ERC7984.sol`
- Notes: Selected as requested, but blocked because the contract depends on encrypted euint64 values and FHE-specific runtime semantics that are not benchmarked in this v1 scaffold.

## Backlog

### `kleros/placeholder`
- Stage: `candidate`
- Failure reason: `selection_pending`
- Source artifact: `TBD`
- Notes: Waiting for protocol-side contract/function selection.

### `nexus_mutual/placeholder`
- Stage: `candidate`
- Failure reason: `selection_pending`
- Source artifact: `TBD`
- Notes: Waiting for protocol-side invariant and target contract selection.

### `unlink_xyz/placeholder`
- Stage: `candidate`
- Failure reason: `upstream_unavailable`
- Source artifact: `TBD`
- Notes: Referenced repository was not resolvable during setup, so no candidate contract was pinned.

### `usual/placeholder`
- Stage: `candidate`
- Failure reason: `private_access`
- Source artifact: `TBD`
- Notes: Pending private repository access and target selection.

## Commands

- Regenerate metadata: `python3 scripts/generate_metadata.py`
- Run one case: `./scripts/run_case.sh <project/case_id>`
- Run active suite: `./scripts/run_all.sh`
- Run repo check: `./scripts/check.sh`
