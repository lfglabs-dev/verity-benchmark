# Benchmark report

This report is generated from the benchmark manifests.

## Summary

- Families: 6
- Implementations: 6
- Active cases: 4
- Buildable active cases: 4
- Active tasks: 18
- Backlog cases: 2

## Buildable active cases

### `ethereum/deposit_contract_minimal`
- Family / implementation: `ethereum` / `deposit_contract`
- Stage: `build_green`
- Status dimensions: translation=`translated`, spec=`frozen`, proof=`partial`
- Lean target: `Benchmark.Cases.Ethereum.DepositContractMinimal.Compile`
- Source ref: `https://github.com/ethereum/deposit_contract@691feb18330d3d102b5a4b3d4434fac7571f51b8:deposit_contract/contracts/validator_registration.v.py`
- Selected functions: `deposit`
- Source artifact: `deposit_contract/contracts/validator_registration.v.py`
- Notes: Counter-oriented slice of the deposit path. Merkle tree, SSZ hashing, and log emission are omitted so the benchmark can focus on threshold-driven state updates.

### `kleros/sortition_trees`
- Family / implementation: `kleros` / `kleros_v2`
- Stage: `build_green`
- Status dimensions: translation=`translated`, spec=`frozen`, proof=`partial`
- Lean target: `Benchmark.Cases.Kleros.SortitionTrees.Compile`
- Source ref: `https://github.com/kleros/kleros-v2@75125dfa54eee723cac239f20e5746d15786196b:contracts/src/libraries/SortitionTrees.sol`
- Selected functions: `set`, `updateParents`, `draw`
- Source artifact: `contracts/src/libraries/SortitionTrees.sol`
- Notes: Sortition-tree slice focused on additive parent invariants, root conservation, interval-based draws, and ID/index correspondence.

### `nexus_mutual/ramm_price_band`
- Family / implementation: `nexus_mutual` / `smart_contracts`
- Stage: `build_green`
- Status dimensions: translation=`translated`, spec=`frozen`, proof=`partial`
- Lean target: `Benchmark.Cases.NexusMutual.RammPriceBand.Compile`
- Source ref: `https://github.com/NexusMutual/smart-contracts@ad212043a78953a2cd98cd02b06c8e3e354c6023:contracts/modules/capital/Ramm.sol`
- Selected functions: `calculateNxm`, `_getReserves`, `getSpotPrices`, `getBookValue`
- Source artifact: `contracts/modules/capital/Ramm.sol`
- Notes: Price-band slice of Nexus Mutual RAMM. The Verity model keeps the buffered book-value computation behind buy and sell spot prices and omits unrelated state evolution machinery.

### `paladin_votes/stream_recovery_claim_usdc`
- Family / implementation: `paladin_votes` / `stream_recovery_claim`
- Stage: `build_green`
- Status dimensions: translation=`translated`, spec=`frozen`, proof=`partial`
- Lean target: `Benchmark.Cases.PaladinVotes.StreamRecoveryClaimUsdc.Compile`
- Source ref: `https://github.com/Figu3/sonic-earn-recovery-system@699cbbc79def374cab9739e451acbbf866293d12:src/StreamRecoveryClaim.sol`
- Selected functions: `claimUsdc`, `_claimUsdc`
- Source artifact: `src/StreamRecoveryClaim.sol`
- Notes: Single-round accounting slice of the USDC claim path. Merkle verification is abstracted as a boolean witness and token transfer side effects are omitted.

## Non-buildable active cases

- None

## Active tasks

### `ethereum/deposit_contract_minimal/chain_start_threshold`
- Track / property class / proof family: `proof-only` / `threshold_activation` / `protocol_transition_correctness`
- Readiness: prompt_context=`ready`, editable_proof=`ready`, reference_solution=`ready`
- Theorem target: `Benchmark.Cases.Ethereum.DepositContractMinimal.full_deposit_starts_chain_at_threshold`
- Evaluation: engine=`lean_proof_generation`, target_kind=`proof_generation`
- Implementation files: `cases/ethereum/deposit_contract_minimal/verity/Contract.lean`, `Benchmark/Cases/Ethereum/DepositContractMinimal/Contract.lean`
- Specification files: `cases/ethereum/deposit_contract_minimal/verity/Specs.lean`, `Benchmark/Cases/Ethereum/DepositContractMinimal/Specs.lean`
- Editable proof file: `Benchmark/Generated/Ethereum/DepositContractMinimal/Tasks/ChainStartThreshold.lean`
- Hidden reference solution: `Benchmark.Cases.Ethereum.DepositContractMinimal.Proofs`

### `ethereum/deposit_contract_minimal/deposit_count`
- Track / property class / proof family: `proof-only` / `monotonic_counter` / `state_preservation_local_effects`
- Readiness: prompt_context=`ready`, editable_proof=`ready`, reference_solution=`ready`
- Theorem target: `Benchmark.Cases.Ethereum.DepositContractMinimal.deposit_increments_deposit_count`
- Evaluation: engine=`lean_proof_generation`, target_kind=`proof_generation`
- Implementation files: `cases/ethereum/deposit_contract_minimal/verity/Contract.lean`, `Benchmark/Cases/Ethereum/DepositContractMinimal/Contract.lean`
- Specification files: `cases/ethereum/deposit_contract_minimal/verity/Specs.lean`, `Benchmark/Cases/Ethereum/DepositContractMinimal/Specs.lean`
- Editable proof file: `Benchmark/Generated/Ethereum/DepositContractMinimal/Tasks/DepositCount.lean`
- Hidden reference solution: `Benchmark.Cases.Ethereum.DepositContractMinimal.Proofs`

### `ethereum/deposit_contract_minimal/full_deposit_increments_full_count`
- Track / property class / proof family: `proof-only` / `monotonic_counter` / `protocol_transition_correctness`
- Readiness: prompt_context=`ready`, editable_proof=`ready`, reference_solution=`ready`
- Theorem target: `Benchmark.Cases.Ethereum.DepositContractMinimal.full_deposit_increments_full_count`
- Evaluation: engine=`lean_proof_generation`, target_kind=`proof_generation`
- Implementation files: `cases/ethereum/deposit_contract_minimal/verity/Contract.lean`, `Benchmark/Cases/Ethereum/DepositContractMinimal/Contract.lean`
- Specification files: `cases/ethereum/deposit_contract_minimal/verity/Specs.lean`, `Benchmark/Cases/Ethereum/DepositContractMinimal/Specs.lean`
- Editable proof file: `Benchmark/Generated/Ethereum/DepositContractMinimal/Tasks/FullDepositIncrementsFullCount.lean`
- Hidden reference solution: `Benchmark.Cases.Ethereum.DepositContractMinimal.Proofs`

### `ethereum/deposit_contract_minimal/full_deposit_preserves_partial_gap`
- Track / property class / proof family: `proof-only` / `accounting_conservation` / `refinement_equivalence`
- Readiness: prompt_context=`ready`, editable_proof=`ready`, reference_solution=`ready`
- Theorem target: `Benchmark.Cases.Ethereum.DepositContractMinimal.full_deposit_preserves_partial_gap`
- Evaluation: engine=`lean_proof_generation`, target_kind=`proof_generation`
- Implementation files: `cases/ethereum/deposit_contract_minimal/verity/Contract.lean`, `Benchmark/Cases/Ethereum/DepositContractMinimal/Contract.lean`
- Specification files: `cases/ethereum/deposit_contract_minimal/verity/Specs.lean`, `Benchmark/Cases/Ethereum/DepositContractMinimal/Specs.lean`
- Editable proof file: `Benchmark/Generated/Ethereum/DepositContractMinimal/Tasks/FullDepositPreservesPartialGap.lean`
- Hidden reference solution: `Benchmark.Cases.Ethereum.DepositContractMinimal.Proofs`

### `ethereum/deposit_contract_minimal/small_deposit_preserves_full_count`
- Track / property class / proof family: `proof-only` / `threshold_partition` / `state_preservation_local_effects`
- Readiness: prompt_context=`ready`, editable_proof=`ready`, reference_solution=`ready`
- Theorem target: `Benchmark.Cases.Ethereum.DepositContractMinimal.small_deposit_preserves_full_count`
- Evaluation: engine=`lean_proof_generation`, target_kind=`proof_generation`
- Implementation files: `cases/ethereum/deposit_contract_minimal/verity/Contract.lean`, `Benchmark/Cases/Ethereum/DepositContractMinimal/Contract.lean`
- Specification files: `cases/ethereum/deposit_contract_minimal/verity/Specs.lean`, `Benchmark/Cases/Ethereum/DepositContractMinimal/Specs.lean`
- Editable proof file: `Benchmark/Generated/Ethereum/DepositContractMinimal/Tasks/SmallDepositPreservesFullCount.lean`
- Hidden reference solution: `Benchmark.Cases.Ethereum.DepositContractMinimal.Proofs`

### `kleros/sortition_trees/draw_interval_matches_weights`
- Track / property class / proof family: `proof-only` / `weighted_selection` / `functional_correctness`
- Readiness: prompt_context=`ready`, editable_proof=`ready`, reference_solution=`ready`
- Theorem target: `Benchmark.Cases.Kleros.SortitionTrees.draw_interval_matches_weights`
- Evaluation: engine=`lean_proof_generation`, target_kind=`proof_generation`
- Implementation files: `cases/kleros/sortition_trees/verity/Contract.lean`, `Benchmark/Cases/Kleros/SortitionTrees/Contract.lean`
- Specification files: `cases/kleros/sortition_trees/verity/Specs.lean`, `Benchmark/Cases/Kleros/SortitionTrees/Specs.lean`
- Editable proof file: `Benchmark/Generated/Kleros/SortitionTrees/Tasks/DrawIntervalMatchesWeights.lean`
- Hidden reference solution: `Benchmark.Cases.Kleros.SortitionTrees.Proofs`

### `kleros/sortition_trees/draw_selects_valid_leaf`
- Track / property class / proof family: `proof-only` / `output_range` / `functional_correctness`
- Readiness: prompt_context=`ready`, editable_proof=`ready`, reference_solution=`ready`
- Theorem target: `Benchmark.Cases.Kleros.SortitionTrees.draw_selects_valid_leaf`
- Evaluation: engine=`lean_proof_generation`, target_kind=`proof_generation`
- Implementation files: `cases/kleros/sortition_trees/verity/Contract.lean`, `Benchmark/Cases/Kleros/SortitionTrees/Contract.lean`
- Specification files: `cases/kleros/sortition_trees/verity/Specs.lean`, `Benchmark/Cases/Kleros/SortitionTrees/Specs.lean`
- Editable proof file: `Benchmark/Generated/Kleros/SortitionTrees/Tasks/DrawSelectsValidLeaf.lean`
- Hidden reference solution: `Benchmark.Cases.Kleros.SortitionTrees.Proofs`

### `kleros/sortition_trees/node_id_bijection`
- Track / property class / proof family: `proof-only` / `mapping_consistency` / `state_preservation_local_effects`
- Readiness: prompt_context=`ready`, editable_proof=`ready`, reference_solution=`ready`
- Theorem target: `Benchmark.Cases.Kleros.SortitionTrees.node_id_bijection`
- Evaluation: engine=`lean_proof_generation`, target_kind=`proof_generation`
- Implementation files: `cases/kleros/sortition_trees/verity/Contract.lean`, `Benchmark/Cases/Kleros/SortitionTrees/Contract.lean`
- Specification files: `cases/kleros/sortition_trees/verity/Specs.lean`, `Benchmark/Cases/Kleros/SortitionTrees/Specs.lean`
- Editable proof file: `Benchmark/Generated/Kleros/SortitionTrees/Tasks/NodeIdBijection.lean`
- Hidden reference solution: `Benchmark.Cases.Kleros.SortitionTrees.Proofs`

### `kleros/sortition_trees/parent_equals_sum_of_children`
- Track / property class / proof family: `proof-only` / `tree_conservation` / `state_preservation_local_effects`
- Readiness: prompt_context=`ready`, editable_proof=`ready`, reference_solution=`ready`
- Theorem target: `Benchmark.Cases.Kleros.SortitionTrees.parent_equals_sum_of_children`
- Evaluation: engine=`lean_proof_generation`, target_kind=`proof_generation`
- Implementation files: `cases/kleros/sortition_trees/verity/Contract.lean`, `Benchmark/Cases/Kleros/SortitionTrees/Contract.lean`
- Specification files: `cases/kleros/sortition_trees/verity/Specs.lean`, `Benchmark/Cases/Kleros/SortitionTrees/Specs.lean`
- Editable proof file: `Benchmark/Generated/Kleros/SortitionTrees/Tasks/ParentEqualsSumOfChildren.lean`
- Hidden reference solution: `Benchmark.Cases.Kleros.SortitionTrees.Proofs`

### `kleros/sortition_trees/root_equals_sum_of_leaves`
- Track / property class / proof family: `proof-only` / `total_conservation` / `refinement_equivalence`
- Readiness: prompt_context=`ready`, editable_proof=`ready`, reference_solution=`ready`
- Theorem target: `Benchmark.Cases.Kleros.SortitionTrees.root_equals_sum_of_leaves`
- Evaluation: engine=`lean_proof_generation`, target_kind=`proof_generation`
- Implementation files: `cases/kleros/sortition_trees/verity/Contract.lean`, `Benchmark/Cases/Kleros/SortitionTrees/Contract.lean`
- Specification files: `cases/kleros/sortition_trees/verity/Specs.lean`, `Benchmark/Cases/Kleros/SortitionTrees/Specs.lean`
- Editable proof file: `Benchmark/Generated/Kleros/SortitionTrees/Tasks/RootEqualsSumOfLeaves.lean`
- Hidden reference solution: `Benchmark.Cases.Kleros.SortitionTrees.Proofs`

### `kleros/sortition_trees/root_minus_left_equals_right_subtree`
- Track / property class / proof family: `proof-only` / `subtree_partition` / `refinement_equivalence`
- Readiness: prompt_context=`ready`, editable_proof=`ready`, reference_solution=`ready`
- Theorem target: `Benchmark.Cases.Kleros.SortitionTrees.root_minus_left_equals_right_subtree`
- Evaluation: engine=`lean_proof_generation`, target_kind=`proof_generation`
- Implementation files: `cases/kleros/sortition_trees/verity/Contract.lean`, `Benchmark/Cases/Kleros/SortitionTrees/Contract.lean`
- Specification files: `cases/kleros/sortition_trees/verity/Specs.lean`, `Benchmark/Cases/Kleros/SortitionTrees/Specs.lean`
- Editable proof file: `Benchmark/Generated/Kleros/SortitionTrees/Tasks/RootMinusLeftEqualsRightSubtree.lean`
- Hidden reference solution: `Benchmark.Cases.Kleros.SortitionTrees.Proofs`

### `nexus_mutual/ramm_price_band/sync_sets_book_value`
- Track / property class / proof family: `proof-only` / `price_computation` / `functional_correctness`
- Readiness: prompt_context=`ready`, editable_proof=`ready`, reference_solution=`ready`
- Theorem target: `Benchmark.Cases.NexusMutual.RammPriceBand.syncPriceBand_sets_book_value`
- Evaluation: engine=`lean_proof_generation`, target_kind=`proof_generation`
- Implementation files: `cases/nexus_mutual/ramm_price_band/verity/Contract.lean`, `Benchmark/Cases/NexusMutual/RammPriceBand/Contract.lean`
- Specification files: `cases/nexus_mutual/ramm_price_band/verity/Specs.lean`, `Benchmark/Cases/NexusMutual/RammPriceBand/Specs.lean`
- Editable proof file: `Benchmark/Generated/NexusMutual/RammPriceBand/Tasks/SyncSetsBookValue.lean`
- Hidden reference solution: `Benchmark.Cases.NexusMutual.RammPriceBand.Proofs`

### `nexus_mutual/ramm_price_band/sync_sets_buy_price`
- Track / property class / proof family: `proof-only` / `price_computation` / `functional_correctness`
- Readiness: prompt_context=`ready`, editable_proof=`ready`, reference_solution=`ready`
- Theorem target: `Benchmark.Cases.NexusMutual.RammPriceBand.syncPriceBand_sets_buy_price`
- Evaluation: engine=`lean_proof_generation`, target_kind=`proof_generation`
- Implementation files: `cases/nexus_mutual/ramm_price_band/verity/Contract.lean`, `Benchmark/Cases/NexusMutual/RammPriceBand/Contract.lean`
- Specification files: `cases/nexus_mutual/ramm_price_band/verity/Specs.lean`, `Benchmark/Cases/NexusMutual/RammPriceBand/Specs.lean`
- Editable proof file: `Benchmark/Generated/NexusMutual/RammPriceBand/Tasks/SyncSetsBuyPrice.lean`
- Hidden reference solution: `Benchmark.Cases.NexusMutual.RammPriceBand.Proofs`

### `nexus_mutual/ramm_price_band/sync_sets_capital`
- Track / property class / proof family: `proof-only` / `storage_write` / `state_preservation_local_effects`
- Readiness: prompt_context=`ready`, editable_proof=`ready`, reference_solution=`ready`
- Theorem target: `Benchmark.Cases.NexusMutual.RammPriceBand.syncPriceBand_sets_capital`
- Evaluation: engine=`lean_proof_generation`, target_kind=`proof_generation`
- Implementation files: `cases/nexus_mutual/ramm_price_band/verity/Contract.lean`, `Benchmark/Cases/NexusMutual/RammPriceBand/Contract.lean`
- Specification files: `cases/nexus_mutual/ramm_price_band/verity/Specs.lean`, `Benchmark/Cases/NexusMutual/RammPriceBand/Specs.lean`
- Editable proof file: `Benchmark/Generated/NexusMutual/RammPriceBand/Tasks/SyncSetsCapital.lean`
- Hidden reference solution: `Benchmark.Cases.NexusMutual.RammPriceBand.Proofs`

### `nexus_mutual/ramm_price_band/sync_sets_sell_price`
- Track / property class / proof family: `proof-only` / `price_computation` / `functional_correctness`
- Readiness: prompt_context=`ready`, editable_proof=`ready`, reference_solution=`ready`
- Theorem target: `Benchmark.Cases.NexusMutual.RammPriceBand.syncPriceBand_sets_sell_price`
- Evaluation: engine=`lean_proof_generation`, target_kind=`proof_generation`
- Implementation files: `cases/nexus_mutual/ramm_price_band/verity/Contract.lean`, `Benchmark/Cases/NexusMutual/RammPriceBand/Contract.lean`
- Specification files: `cases/nexus_mutual/ramm_price_band/verity/Specs.lean`, `Benchmark/Cases/NexusMutual/RammPriceBand/Specs.lean`
- Editable proof file: `Benchmark/Generated/NexusMutual/RammPriceBand/Tasks/SyncSetsSellPrice.lean`
- Hidden reference solution: `Benchmark.Cases.NexusMutual.RammPriceBand.Proofs`

### `paladin_votes/stream_recovery_claim_usdc/claim_marks_user`
- Track / property class / proof family: `proof-only` / `authorization_state` / `authorization_enablement`
- Readiness: prompt_context=`ready`, editable_proof=`ready`, reference_solution=`ready`
- Theorem target: `Benchmark.Cases.PaladinVotes.StreamRecoveryClaimUsdc.claimUsdc_marks_user_claimed`
- Evaluation: engine=`lean_proof_generation`, target_kind=`proof_generation`
- Implementation files: `cases/paladin_votes/stream_recovery_claim_usdc/verity/Contract.lean`, `Benchmark/Cases/PaladinVotes/StreamRecoveryClaimUsdc/Contract.lean`
- Specification files: `cases/paladin_votes/stream_recovery_claim_usdc/verity/Specs.lean`, `Benchmark/Cases/PaladinVotes/StreamRecoveryClaimUsdc/Specs.lean`
- Editable proof file: `Benchmark/Generated/PaladinVotes/StreamRecoveryClaimUsdc/Tasks/ClaimMarksUser.lean`
- Hidden reference solution: `Benchmark.Cases.PaladinVotes.StreamRecoveryClaimUsdc.Proofs`

### `paladin_votes/stream_recovery_claim_usdc/claimed_plus_allocated_conserved`
- Track / property class / proof family: `proof-only` / `accounting_conservation` / `refinement_equivalence`
- Readiness: prompt_context=`ready`, editable_proof=`ready`, reference_solution=`ready`
- Theorem target: `Benchmark.Cases.PaladinVotes.StreamRecoveryClaimUsdc.claimUsdc_claimed_plus_allocated_conserved`
- Evaluation: engine=`lean_proof_generation`, target_kind=`proof_generation`
- Implementation files: `cases/paladin_votes/stream_recovery_claim_usdc/verity/Contract.lean`, `Benchmark/Cases/PaladinVotes/StreamRecoveryClaimUsdc/Contract.lean`
- Specification files: `cases/paladin_votes/stream_recovery_claim_usdc/verity/Specs.lean`, `Benchmark/Cases/PaladinVotes/StreamRecoveryClaimUsdc/Specs.lean`
- Editable proof file: `Benchmark/Generated/PaladinVotes/StreamRecoveryClaimUsdc/Tasks/ClaimedPlusAllocatedConserved.lean`
- Hidden reference solution: `Benchmark.Cases.PaladinVotes.StreamRecoveryClaimUsdc.Proofs`

### `paladin_votes/stream_recovery_claim_usdc/no_overclaim`
- Track / property class / proof family: `proof-only` / `accounting_bound` / `authorization_enablement`
- Readiness: prompt_context=`ready`, editable_proof=`ready`, reference_solution=`ready`
- Theorem target: `Benchmark.Cases.PaladinVotes.StreamRecoveryClaimUsdc.claimUsdc_preserves_round_bound`
- Evaluation: engine=`lean_proof_generation`, target_kind=`proof_generation`
- Implementation files: `cases/paladin_votes/stream_recovery_claim_usdc/verity/Contract.lean`, `Benchmark/Cases/PaladinVotes/StreamRecoveryClaimUsdc/Contract.lean`
- Specification files: `cases/paladin_votes/stream_recovery_claim_usdc/verity/Specs.lean`, `Benchmark/Cases/PaladinVotes/StreamRecoveryClaimUsdc/Specs.lean`
- Editable proof file: `Benchmark/Generated/PaladinVotes/StreamRecoveryClaimUsdc/Tasks/NoOverclaim.lean`
- Hidden reference solution: `Benchmark.Cases.PaladinVotes.StreamRecoveryClaimUsdc.Proofs`

## Backlog

### `unlink_xyz/placeholder`
- Family / implementation: `unlink_xyz` / `monorepo`
- Stage: `candidate`
- Status dimensions: translation=`blocked`, spec=`not_started`, proof=`blocked`
- Failure reason: `upstream_unavailable`
- Source ref: `unresolved:https://github.com/unlink-xyz/monorepo@unknown:TBD`
- Source artifact: `TBD`
- Notes: Referenced repository was not resolvable during setup, so no candidate contract was pinned.

### `usual/placeholder`
- Family / implementation: `usual` / `private_repo`
- Stage: `candidate`
- Status dimensions: translation=`blocked`, spec=`not_started`, proof=`blocked`
- Failure reason: `private_access`
- Source ref: `unresolved:usual/private_repo@unknown:TBD`
- Source artifact: `TBD`
- Notes: Pending private repository access and target selection.

## Commands

- Validate manifests: `python3 scripts/validate_manifests.py`
- Regenerate metadata: `python3 scripts/generate_metadata.py`
- Run one task: `./scripts/run_task.sh <project/case_id/task_id>`
- Run one case: `./scripts/run_case.sh <project/case_id>`
- Run active suite: `./scripts/run_all.sh`
- Run repo check: `./scripts/check.sh`
