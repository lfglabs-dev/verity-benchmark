import Benchmark.Cases.Kleros.SortitionTrees.Specs

namespace Benchmark.Cases.Kleros.SortitionTrees

open Verity
open Verity.EVM.Uint256

/--
Executing `setLeaf` recomputes the root as the sum of the four leaf weights.
-/
theorem root_equals_sum_of_leaves
    (nodeIndex stakePathID weight : Uint256) (s : ContractState)
    (hLow : nodeIndex >= 3)
    (hHigh : nodeIndex <= 6) :
    let s' := ((SortitionTrees.setLeaf nodeIndex stakePathID weight).run s).snd
    root_equals_sum_of_leaves_spec s' := by
  -- Replace this placeholder with a complete Lean proof.
  exact ?_

end Benchmark.Cases.Kleros.SortitionTrees
