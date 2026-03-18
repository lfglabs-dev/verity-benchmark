import Benchmark.Cases.Kleros.SortitionTrees.Specs

namespace Benchmark.Cases.Kleros.SortitionTrees

open Verity
open Verity.EVM.Uint256

/--
If the tree's parent sums are consistent and the root equals the sum of all
leaves, then removing the left subtree weight from the root leaves exactly the
right subtree weight.
-/
theorem root_minus_left_equals_right_subtree
    (s' : ContractState) :
    parent_equals_sum_of_children_spec s' ->
    root_equals_sum_of_leaves_spec s' ->
    s'.storage 0 - s'.storage 1 = s'.storage 2 := by
  intro hParent hRoot
  unfold parent_equals_sum_of_children_spec at hParent
  rcases hParent with ⟨hLeft, hRight⟩
  unfold root_equals_sum_of_leaves_spec at hRoot
  unfold leaf_sum at hRoot
  rw [hRoot, hLeft, hRight]
  rw [Verity.Core.Uint256.add_comm (add (s'.storage 3) (s'.storage 4)) (add (s'.storage 5) (s'.storage 6))]
  exact Verity.Core.Uint256.sub_add_cancel (add (s'.storage 5) (s'.storage 6)) (add (s'.storage 3) (s'.storage 4))

end Benchmark.Cases.Kleros.SortitionTrees
