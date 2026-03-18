# Benchmark report

This report is generated from the benchmark manifests.

## Summary

- Families: 6
- Implementations: 6
- Active cases: 4
- Buildable active cases: 4
- Active tasks: 14
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
- Status dimensions: translation=`translated`, spec=`frozen`, proof=`not_started`
- Lean target: `Benchmark.Cases.NexusMutual.RammPriceBand.Compile`
- Source ref: `https://github.com/NexusMutual/smart-contracts@ad212043a78953a2cd98cd02b06c8e3e354c6023:contracts/modules/capital/Ramm.sol`
- Selected functions: `calculateNxm`, `_getReserves`, `getSpotPrices`, `getBookValue`
- Source artifact: `contracts/modules/capital/Ramm.sol`
- Notes: Price-band slice of Nexus Mutual RAMM. The Verity model keeps the buffered book-value computation behind buy and sell spot prices and omits unrelated state evolution machinery.

### `paladin_votes/stream_recovery_claim_usdc`
- Family / implementation: `paladin_votes` / `stream_recovery_claim`
- Stage: `build_green`
- Status dimensions: translation=`translated`, spec=`frozen`, proof=`not_started`
- Lean target: `Benchmark.Cases.PaladinVotes.StreamRecoveryClaimUsdc.Compile`
- Source ref: `https://github.com/Figu3/sonic-earn-recovery-system@699cbbc79def374cab9739e451acbbf866293d12:src/StreamRecoveryClaim.sol`
- Selected functions: `claimUsdc`, `_claimUsdc`
- Source artifact: `src/StreamRecoveryClaim.sol`
- Notes: Single-round accounting slice of the USDC claim path. Merkle verification is abstracted as a boolean witness and token transfer side effects are omitted.

## Non-buildable active cases

- None

## Active tasks

### `ethereum/deposit_contract_minimal/chain_start_threshold`
- Track / property class: `proof-only` / `threshold_activation`
- Readiness: translation=`ready`, spec=`ready`, proof=`planned`, evaluation=`ready`
- Statement id: `deposit_starts_chain_at_threshold_spec`
- Evaluation: engine=`lean_build`, target_kind=`spec`, target=`Benchmark.Cases.Ethereum.DepositContractMinimal.Specs`, declaration=`deposit_starts_chain_at_threshold_spec`
- Spec target: `Benchmark.Cases.Ethereum.DepositContractMinimal.Specs`

### `ethereum/deposit_contract_minimal/deposit_count`
- Track / property class: `proof-only` / `monotonic_counter`
- Readiness: translation=`ready`, spec=`ready`, proof=`planned`, evaluation=`ready`
- Statement id: `deposit_increments_deposit_count_spec`
- Evaluation: engine=`lean_build`, target_kind=`spec`, target=`Benchmark.Cases.Ethereum.DepositContractMinimal.Specs`, declaration=`deposit_increments_deposit_count_spec`
- Spec target: `Benchmark.Cases.Ethereum.DepositContractMinimal.Specs`

### `ethereum/deposit_contract_minimal/full_deposit_preserves_partial_gap`
- Track / property class: `proof-only` / `accounting_conservation`
- Readiness: translation=`ready`, spec=`ready`, proof=`ready`, evaluation=`ready`
- Statement id: `full_deposit_preserves_partial_gap`
- Evaluation: engine=`lean_build`, target_kind=`proof`, target=`Benchmark.Cases.Ethereum.DepositContractMinimal.Proofs`, declaration=`full_deposit_preserves_partial_gap`
- Spec target: `Benchmark.Cases.Ethereum.DepositContractMinimal.Specs`
- Proof target: `Benchmark.Cases.Ethereum.DepositContractMinimal.Proofs`

### `kleros/sortition_trees/draw_interval_matches_weights`
- Track / property class: `proof-only` / `weighted_selection`
- Readiness: translation=`ready`, spec=`ready`, proof=`planned`, evaluation=`ready`
- Statement id: `draw_interval_matches_weights_spec`
- Evaluation: engine=`lean_build`, target_kind=`spec`, target=`Benchmark.Cases.Kleros.SortitionTrees.Specs`, declaration=`draw_interval_matches_weights_spec`
- Spec target: `Benchmark.Cases.Kleros.SortitionTrees.Specs`

### `kleros/sortition_trees/node_id_bijection`
- Track / property class: `proof-only` / `mapping_consistency`
- Readiness: translation=`ready`, spec=`ready`, proof=`planned`, evaluation=`ready`
- Statement id: `node_id_bijection_spec`
- Evaluation: engine=`lean_build`, target_kind=`spec`, target=`Benchmark.Cases.Kleros.SortitionTrees.Specs`, declaration=`node_id_bijection_spec`
- Spec target: `Benchmark.Cases.Kleros.SortitionTrees.Specs`

### `kleros/sortition_trees/parent_equals_sum_of_children`
- Track / property class: `proof-only` / `tree_conservation`
- Readiness: translation=`ready`, spec=`ready`, proof=`planned`, evaluation=`ready`
- Statement id: `parent_equals_sum_of_children_spec`
- Evaluation: engine=`lean_build`, target_kind=`spec`, target=`Benchmark.Cases.Kleros.SortitionTrees.Specs`, declaration=`parent_equals_sum_of_children_spec`
- Spec target: `Benchmark.Cases.Kleros.SortitionTrees.Specs`

### `kleros/sortition_trees/root_equals_sum_of_leaves`
- Track / property class: `proof-only` / `total_conservation`
- Readiness: translation=`ready`, spec=`ready`, proof=`planned`, evaluation=`ready`
- Statement id: `root_equals_sum_of_leaves_spec`
- Evaluation: engine=`lean_build`, target_kind=`spec`, target=`Benchmark.Cases.Kleros.SortitionTrees.Specs`, declaration=`root_equals_sum_of_leaves_spec`
- Spec target: `Benchmark.Cases.Kleros.SortitionTrees.Specs`

### `kleros/sortition_trees/root_minus_left_equals_right_subtree`
- Track / property class: `proof-only` / `subtree_partition`
- Readiness: translation=`ready`, spec=`ready`, proof=`ready`, evaluation=`ready`
- Statement id: `root_minus_left_equals_right_subtree`
- Evaluation: engine=`lean_build`, target_kind=`proof`, target=`Benchmark.Cases.Kleros.SortitionTrees.Proofs`, declaration=`root_minus_left_equals_right_subtree`
- Spec target: `Benchmark.Cases.Kleros.SortitionTrees.Specs`
- Proof target: `Benchmark.Cases.Kleros.SortitionTrees.Proofs`

### `nexus_mutual/ramm_price_band/buy_price_ge_bv_plus_1pct`
- Track / property class: `proof-only` / `price_lower_bound`
- Readiness: translation=`ready`, spec=`ready`, proof=`planned`, evaluation=`ready`
- Statement id: `buy_price_above_book_value_buffer_spec`
- Evaluation: engine=`lean_build`, target_kind=`spec`, target=`Benchmark.Cases.NexusMutual.RammPriceBand.Specs`, declaration=`buy_price_above_book_value_buffer_spec`
- Spec target: `Benchmark.Cases.NexusMutual.RammPriceBand.Specs`

### `nexus_mutual/ramm_price_band/sell_price_le_buy_price`
- Track / property class: `proof-only` / `price_ordering`
- Readiness: translation=`ready`, spec=`ready`, proof=`planned`, evaluation=`ready`
- Statement id: `sell_price_below_buy_price_spec`
- Evaluation: engine=`lean_build`, target_kind=`spec`, target=`Benchmark.Cases.NexusMutual.RammPriceBand.Specs`, declaration=`sell_price_below_buy_price_spec`
- Spec target: `Benchmark.Cases.NexusMutual.RammPriceBand.Specs`

### `nexus_mutual/ramm_price_band/sell_price_le_bv_minus_1pct`
- Track / property class: `proof-only` / `price_upper_bound`
- Readiness: translation=`ready`, spec=`ready`, proof=`planned`, evaluation=`ready`
- Statement id: `sell_price_below_book_value_buffer_spec`
- Evaluation: engine=`lean_build`, target_kind=`spec`, target=`Benchmark.Cases.NexusMutual.RammPriceBand.Specs`, declaration=`sell_price_below_book_value_buffer_spec`
- Spec target: `Benchmark.Cases.NexusMutual.RammPriceBand.Specs`

### `paladin_votes/stream_recovery_claim_usdc/claim_marks_user`
- Track / property class: `proof-only` / `authorization_state`
- Readiness: translation=`ready`, spec=`ready`, proof=`planned`, evaluation=`ready`
- Statement id: `claimUsdc_marks_claimed_spec`
- Evaluation: engine=`lean_build`, target_kind=`spec`, target=`Benchmark.Cases.PaladinVotes.StreamRecoveryClaimUsdc.Specs`, declaration=`claimUsdc_marks_claimed_spec`
- Spec target: `Benchmark.Cases.PaladinVotes.StreamRecoveryClaimUsdc.Specs`

### `paladin_votes/stream_recovery_claim_usdc/claimed_plus_allocated_conserved`
- Track / property class: `proof-only` / `accounting_conservation`
- Readiness: translation=`ready`, spec=`ready`, proof=`ready`, evaluation=`ready`
- Statement id: `claimUsdc_claimed_plus_allocated_conserved`
- Evaluation: engine=`lean_build`, target_kind=`proof`, target=`Benchmark.Cases.PaladinVotes.StreamRecoveryClaimUsdc.Proofs`, declaration=`claimUsdc_claimed_plus_allocated_conserved`
- Spec target: `Benchmark.Cases.PaladinVotes.StreamRecoveryClaimUsdc.Specs`
- Proof target: `Benchmark.Cases.PaladinVotes.StreamRecoveryClaimUsdc.Proofs`

### `paladin_votes/stream_recovery_claim_usdc/no_overclaim`
- Track / property class: `proof-only` / `accounting_bound`
- Readiness: translation=`ready`, spec=`ready`, proof=`planned`, evaluation=`ready`
- Statement id: `claimUsdc_preserves_round_bound_spec`
- Evaluation: engine=`lean_build`, target_kind=`spec`, target=`Benchmark.Cases.PaladinVotes.StreamRecoveryClaimUsdc.Specs`, declaration=`claimUsdc_preserves_round_bound_spec`
- Spec target: `Benchmark.Cases.PaladinVotes.StreamRecoveryClaimUsdc.Specs`

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
