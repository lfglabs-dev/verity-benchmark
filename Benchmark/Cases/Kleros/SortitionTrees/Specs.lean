import Verity.Specs.Common
import Benchmark.Cases.Kleros.SortitionTrees.Contract

namespace Benchmark.Cases.Kleros.SortitionTrees

open Verity
open Verity.EVM.Uint256

def leaf_sum (s : ContractState) : Uint256 :=
  add (add (s.storage 3) (s.storage 4)) (add (s.storage 5) (s.storage 6))

def parent_equals_sum_of_children_spec (s' : ContractState) : Prop :=
  s'.storage 1 = add (s'.storage 3) (s'.storage 4) /\
  s'.storage 2 = add (s'.storage 5) (s'.storage 6)

def root_equals_sum_of_leaves_spec (s' : ContractState) : Prop :=
  s'.storage 0 = leaf_sum s'

def draw_interval_matches_weights_spec (ticket : Uint256) (s s' : ContractState) : Prop :=
  ticket < s.storage 0 ->
  (
    (ticket < s.storage 1 /\ ticket < s.storage 3 -> s'.storage 9 = 3) /\
    (ticket < s.storage 1 /\ s.storage 3 <= ticket -> s'.storage 9 = 4) /\
    (s.storage 1 <= ticket /\ sub ticket (s.storage 1) < s.storage 5 -> s'.storage 9 = 5) /\
    (s.storage 1 <= ticket /\ s.storage 5 <= sub ticket (s.storage 1) -> s'.storage 9 = 6)
  )

def draw_selects_valid_leaf_spec (s' : ContractState) : Prop :=
  3 <= s'.storage 9 /\ s'.storage 9 <= 6

def node_id_bijection_spec (nodeIndex stakePathID : Uint256) (s' : ContractState) : Prop :=
  s'.storageMapUint 7 nodeIndex = stakePathID /\
  s'.storageMapUint 8 stakePathID = nodeIndex

def root_minus_left_equals_right_subtree_spec (s' : ContractState) : Prop :=
  s'.storage 0 - s'.storage 1 = s'.storage 2

end Benchmark.Cases.Kleros.SortitionTrees
