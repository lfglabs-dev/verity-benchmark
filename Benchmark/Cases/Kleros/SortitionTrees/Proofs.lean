import Benchmark.Cases.Kleros.SortitionTrees.Specs
import Verity.Proofs.Stdlib.Automation

namespace Benchmark.Cases.Kleros.SortitionTrees

open Verity
open Verity.EVM.Uint256

private theorem draw_selected_node
    (ticket : Uint256) (s : ContractState)
    (hRoot : s.storage 0 != 0)
    (hInRange : ticket < s.storage 0) :
    let s' := ((SortitionTrees.draw ticket).run s).snd
    s'.storage 9 =
      ite (ticket < s.storage 1)
        (ite (ticket < s.storage 3) 3 4)
        (ite (sub ticket (s.storage 1) < s.storage 5) 5 6) := by
  have hRoot' : ¬ s.storage 0 = 0 := by
    intro hEq
    simp [hEq] at hRoot
  simp [SortitionTrees.draw, SortitionTrees.rootSum, SortitionTrees.leftSum, SortitionTrees.leaf0,
    SortitionTrees.leaf2, SortitionTrees.selectedNode, hRoot', hInRange, getStorage, setStorage,
    Verity.require, Verity.bind, Bind.bind, Verity.pure, Pure.pure, Contract.run, ContractResult.snd]

/--
Executing `setLeaf` recomputes each parent node from its direct children.
-/
theorem parent_equals_sum_of_children
    (nodeIndex stakePathID weight : Uint256) (s : ContractState)
    (hLow : nodeIndex >= 3)
    (hHigh : nodeIndex <= 6) :
    let s' := ((SortitionTrees.setLeaf nodeIndex stakePathID weight).run s).snd
    parent_equals_sum_of_children_spec s' := by
  by_cases h3 : nodeIndex == 3
  · simp [SortitionTrees.setLeaf, hLow, hHigh, h3, parent_equals_sum_of_children_spec,
      SortitionTrees.rootSum, SortitionTrees.leftSum, SortitionTrees.rightSum, SortitionTrees.leaf0,
      SortitionTrees.leaf1, SortitionTrees.leaf2, SortitionTrees.leaf3, SortitionTrees.nodeIndexesToIDs,
      SortitionTrees.IDsToNodeIndexes, getStorage, setStorage, setMappingUint, Verity.require,
      Verity.bind, Bind.bind, Contract.run, ContractResult.snd]
  · by_cases h4 : nodeIndex == 4
    · simp [SortitionTrees.setLeaf, hLow, hHigh, h3, h4, parent_equals_sum_of_children_spec,
        SortitionTrees.rootSum, SortitionTrees.leftSum, SortitionTrees.rightSum, SortitionTrees.leaf0,
        SortitionTrees.leaf1, SortitionTrees.leaf2, SortitionTrees.leaf3, SortitionTrees.nodeIndexesToIDs,
        SortitionTrees.IDsToNodeIndexes, getStorage, setStorage, setMappingUint, Verity.require,
        Verity.bind, Bind.bind, Contract.run, ContractResult.snd]
    · by_cases h5 : nodeIndex == 5
      · simp [SortitionTrees.setLeaf, hLow, hHigh, h3, h4, h5, parent_equals_sum_of_children_spec,
          SortitionTrees.rootSum, SortitionTrees.leftSum, SortitionTrees.rightSum, SortitionTrees.leaf0,
          SortitionTrees.leaf1, SortitionTrees.leaf2, SortitionTrees.leaf3, SortitionTrees.nodeIndexesToIDs,
          SortitionTrees.IDsToNodeIndexes, getStorage, setStorage, setMappingUint, Verity.require,
          Verity.bind, Bind.bind, Contract.run, ContractResult.snd]
      · by_cases h6 : nodeIndex == 6
        · simp [SortitionTrees.setLeaf, hLow, hHigh, h3, h4, h5, h6, parent_equals_sum_of_children_spec,
            SortitionTrees.rootSum, SortitionTrees.leftSum, SortitionTrees.rightSum, SortitionTrees.leaf0,
            SortitionTrees.leaf1, SortitionTrees.leaf2, SortitionTrees.leaf3, SortitionTrees.nodeIndexesToIDs,
            SortitionTrees.IDsToNodeIndexes, getStorage, setStorage, setMappingUint, Verity.require,
            Verity.bind, Bind.bind, Contract.run, ContractResult.snd]
        · exfalso
          have hLow' : (3 : Nat) ≤ nodeIndex.val := by simpa using hLow
          have hHigh' : nodeIndex.val ≤ 6 := by simpa using hHigh
          have h3ne : nodeIndex ≠ 3 := by simpa using h3
          have h4ne : nodeIndex ≠ 4 := by simpa using h4
          have h5ne : nodeIndex ≠ 5 := by simpa using h5
          have h6ne : nodeIndex ≠ 6 := by simpa using h6
          have h3' : nodeIndex.val ≠ 3 := by intro hv; apply h3ne; exact Verity.Core.Uint256.ext hv
          have h4' : nodeIndex.val ≠ 4 := by intro hv; apply h4ne; exact Verity.Core.Uint256.ext hv
          have h5' : nodeIndex.val ≠ 5 := by intro hv; apply h5ne; exact Verity.Core.Uint256.ext hv
          have h6' : nodeIndex.val ≠ 6 := by intro hv; apply h6ne; exact Verity.Core.Uint256.ext hv
          omega

/--
Executing `setLeaf` recomputes the root as the sum of the four leaf weights.
-/
theorem root_equals_sum_of_leaves
    (nodeIndex stakePathID weight : Uint256) (s : ContractState)
    (hLow : nodeIndex >= 3)
    (hHigh : nodeIndex <= 6) :
    let s' := ((SortitionTrees.setLeaf nodeIndex stakePathID weight).run s).snd
    root_equals_sum_of_leaves_spec s' := by
  let s' := ((SortitionTrees.setLeaf nodeIndex stakePathID weight).run s).snd
  have hParents : parent_equals_sum_of_children_spec s' := by
    simpa [s'] using parent_equals_sum_of_children nodeIndex stakePathID weight s hLow hHigh
  have hRootParents : s'.storage 0 = add (s'.storage 1) (s'.storage 2) := by
    by_cases h3 : nodeIndex == 3
    · simp [s', SortitionTrees.setLeaf, SortitionTrees.rootSum, SortitionTrees.leftSum,
        SortitionTrees.rightSum, hLow, hHigh, h3, getStorage, setStorage, setMappingUint,
        Verity.require, Verity.bind, Bind.bind, Contract.run, ContractResult.snd]
    · by_cases h4 : nodeIndex == 4
      · simp [s', SortitionTrees.setLeaf, SortitionTrees.rootSum, SortitionTrees.leftSum,
          SortitionTrees.rightSum, hLow, hHigh, h3, h4, getStorage, setStorage, setMappingUint,
          Verity.require, Verity.bind, Bind.bind, Contract.run, ContractResult.snd]
      · by_cases h5 : nodeIndex == 5
        · simp [s', SortitionTrees.setLeaf, SortitionTrees.rootSum, SortitionTrees.leftSum,
            SortitionTrees.rightSum, hLow, hHigh, h3, h4, h5, getStorage, setStorage, setMappingUint,
            Verity.require, Verity.bind, Bind.bind, Contract.run, ContractResult.snd]
        · by_cases h6 : nodeIndex == 6
          · simp [s', SortitionTrees.setLeaf, SortitionTrees.rootSum, SortitionTrees.leftSum,
              SortitionTrees.rightSum, hLow, hHigh, h3, h4, h5, h6, getStorage, setStorage,
              setMappingUint, Verity.require, Verity.bind, Bind.bind, Contract.run, ContractResult.snd]
          · exfalso
            have hLow' : (3 : Nat) ≤ nodeIndex.val := by simpa using hLow
            have hHigh' : nodeIndex.val ≤ 6 := by simpa using hHigh
            have h3ne : nodeIndex ≠ 3 := by simpa using h3
            have h4ne : nodeIndex ≠ 4 := by simpa using h4
            have h5ne : nodeIndex ≠ 5 := by simpa using h5
            have h6ne : nodeIndex ≠ 6 := by simpa using h6
            have h3' : nodeIndex.val ≠ 3 := by intro hv; apply h3ne; exact Verity.Core.Uint256.ext hv
            have h4' : nodeIndex.val ≠ 4 := by intro hv; apply h4ne; exact Verity.Core.Uint256.ext hv
            have h5' : nodeIndex.val ≠ 5 := by intro hv; apply h5ne; exact Verity.Core.Uint256.ext hv
            have h6' : nodeIndex.val ≠ 6 := by intro hv; apply h6ne; exact Verity.Core.Uint256.ext hv
            omega
  rcases hParents with ⟨hLeft, hRight⟩
  unfold root_equals_sum_of_leaves_spec leaf_sum
  calc
    s'.storage 0 = add (s'.storage 1) (s'.storage 2) := hRootParents
    _ = add (add (s'.storage 3) (s'.storage 4)) (add (s'.storage 5) (s'.storage 6)) := by
          rw [hLeft, hRight]

/--
Executing `draw` follows the encoded ticket intervals used by the
implementation.
-/
theorem draw_interval_matches_weights
    (ticket : Uint256) (s : ContractState)
    (hRoot : s.storage 0 != 0)
    (hInRange : ticket < s.storage 0) :
    let s' := ((SortitionTrees.draw ticket).run s).snd
    draw_interval_matches_weights_spec ticket s s' := by
  unfold draw_interval_matches_weights_spec
  dsimp
  intro _
  refine ⟨?_, ?_⟩
  · intro hLeaf0
    rw [draw_selected_node ticket s hRoot hInRange]
    simp [hLeaf0]
  refine ⟨?_, ?_⟩
  · intro hLeft
    rw [draw_selected_node ticket s hRoot hInRange]
    have hNotLeaf0 : ¬ ticket < s.storage 3 := Nat.not_lt_of_ge hLeft.2
    simp [hLeft.1, hNotLeaf0]
  refine ⟨?_, ?_⟩
  · intro hRight
    rw [draw_selected_node ticket s hRoot hInRange]
    have hNotLeft : ¬ ticket < s.storage 1 := Nat.not_lt_of_ge hRight.1
    simp [hNotLeft, hRight.2]
  · intro hLast
    rw [draw_selected_node ticket s hRoot hInRange]
    have hRight : s.storage 1 ≤ ticket := hLast.1
    have hNotLeft : ¬ ticket < s.storage 1 := Nat.not_lt_of_ge hRight
    have hNotLeaf2 : ¬ sub ticket (s.storage 1) < s.storage 5 := Nat.not_lt_of_ge hLast.2
    simp [hNotLeft, hNotLeaf2]

/--
Any successful `draw` resolves to one of the four leaf node indices.
-/
theorem draw_selects_valid_leaf
    (ticket : Uint256) (s : ContractState)
    (hRoot : s.storage 0 != 0)
    (hInRange : ticket < s.storage 0) :
    let s' := ((SortitionTrees.draw ticket).run s).snd
    draw_selects_valid_leaf_spec s' := by
  unfold draw_selects_valid_leaf_spec
  dsimp
  rw [draw_selected_node ticket s hRoot hInRange]
  by_cases hLeft : ticket < s.storage 1
  · by_cases hLeaf0 : ticket < s.storage 3
    · simp [hLeft, hLeaf0]
      decide
    · simp [hLeft, hLeaf0]
      decide
  · by_cases hLeaf2 : sub ticket (s.storage 1) < s.storage 5
    · simp [hLeft, hLeaf2]
      decide
    · simp [hLeft, hLeaf2]
      decide

/--
Executing `setLeaf` writes matching forward and reverse mapping entries for the
updated node and stake-path id.
-/
theorem node_id_bijection
    (nodeIndex stakePathID weight : Uint256) (s : ContractState)
    (hLow : nodeIndex >= 3)
    (hHigh : nodeIndex <= 6) :
    let s' := ((SortitionTrees.setLeaf nodeIndex stakePathID weight).run s).snd
    node_id_bijection_spec nodeIndex stakePathID s' := by
  have h7eq : 7 = SortitionTrees.nodeIndexesToIDs.slot := by decide
  have h8eq : 8 = SortitionTrees.IDsToNodeIndexes.slot := by decide
  by_cases h3 : nodeIndex == 3
  · simp [SortitionTrees.setLeaf, hLow, hHigh, h3, h7eq, h8eq, node_id_bijection_spec, getStorage,
      setStorage, setMappingUint, Verity.require, Verity.bind, Bind.bind, Contract.run, ContractResult.snd]
  · by_cases h4 : nodeIndex == 4
    · simp [SortitionTrees.setLeaf, hLow, hHigh, h3, h4, h7eq, h8eq, node_id_bijection_spec,
        getStorage, setStorage, setMappingUint, Verity.require, Verity.bind, Bind.bind, Contract.run,
        ContractResult.snd]
    · by_cases h5 : nodeIndex == 5
      · simp [SortitionTrees.setLeaf, hLow, hHigh, h3, h4, h5, h7eq, h8eq, node_id_bijection_spec,
          getStorage, setStorage, setMappingUint, Verity.require, Verity.bind, Bind.bind, Contract.run,
          ContractResult.snd]
      · by_cases h6 : nodeIndex == 6
        · simp [SortitionTrees.setLeaf, hLow, hHigh, h3, h4, h5, h6, h7eq, h8eq, node_id_bijection_spec,
            getStorage, setStorage, setMappingUint, Verity.require, Verity.bind, Bind.bind, Contract.run,
            ContractResult.snd]
        · exfalso
          have hLow' : (3 : Nat) ≤ nodeIndex.val := by simpa using hLow
          have hHigh' : nodeIndex.val ≤ 6 := by simpa using hHigh
          have h3ne : nodeIndex ≠ 3 := by simpa using h3
          have h4ne : nodeIndex ≠ 4 := by simpa using h4
          have h5ne : nodeIndex ≠ 5 := by simpa using h5
          have h6ne : nodeIndex ≠ 6 := by simpa using h6
          have h3' : nodeIndex.val ≠ 3 := by intro hv; apply h3ne; exact Verity.Core.Uint256.ext hv
          have h4' : nodeIndex.val ≠ 4 := by intro hv; apply h4ne; exact Verity.Core.Uint256.ext hv
          have h5' : nodeIndex.val ≠ 5 := by intro hv; apply h5ne; exact Verity.Core.Uint256.ext hv
          have h6' : nodeIndex.val ≠ 6 := by intro hv; apply h6ne; exact Verity.Core.Uint256.ext hv
          omega

/--
Executing `setLeaf` keeps the root partitioned into left and right subtree
weights.
-/
theorem root_minus_left_equals_right_subtree
    (nodeIndex stakePathID weight : Uint256) (s : ContractState)
    (hLow : nodeIndex >= 3)
    (hHigh : nodeIndex <= 6) :
    let s' := ((SortitionTrees.setLeaf nodeIndex stakePathID weight).run s).snd
    root_minus_left_equals_right_subtree_spec s' := by
  let s' := ((SortitionTrees.setLeaf nodeIndex stakePathID weight).run s).snd
  have hParents : parent_equals_sum_of_children_spec s' := by
    simpa [s'] using parent_equals_sum_of_children nodeIndex stakePathID weight s hLow hHigh
  have hRoot : root_equals_sum_of_leaves_spec s' := by
    simpa [s'] using root_equals_sum_of_leaves nodeIndex stakePathID weight s hLow hHigh
  have hRootLR : s'.storage 0 = add (s'.storage 1) (s'.storage 2) := by
    rcases hParents with ⟨hLeft, hRight⟩
    unfold root_equals_sum_of_leaves_spec at hRoot
    unfold leaf_sum at hRoot
    calc
      s'.storage 0 = add (add (s'.storage 3) (s'.storage 4)) (add (s'.storage 5) (s'.storage 6)) := hRoot
      _ = add (s'.storage 1) (s'.storage 2) := by rw [← hLeft, ← hRight]
  unfold root_minus_left_equals_right_subtree_spec
  dsimp
  apply Verity.Core.Uint256.add_right_cancel
  calc
    ((s'.storage 0 - s'.storage 1) + s'.storage 1) = s'.storage 0 := by
      exact Verity.Core.Uint256.sub_add_cancel_left (s'.storage 0) (s'.storage 1)
    _ = add (s'.storage 1) (s'.storage 2) := hRootLR
    _ = (s'.storage 2) + (s'.storage 1) := by
          exact Verity.Core.Uint256.add_comm (s'.storage 1) (s'.storage 2)

end Benchmark.Cases.Kleros.SortitionTrees
