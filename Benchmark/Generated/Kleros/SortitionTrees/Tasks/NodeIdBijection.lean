import Benchmark.Cases.Kleros.SortitionTrees.Specs

namespace Benchmark.Cases.Kleros.SortitionTrees

open Verity
open Verity.EVM.Uint256

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
  -- Replace this placeholder with a complete Lean proof.
  exact ?_

end Benchmark.Cases.Kleros.SortitionTrees
