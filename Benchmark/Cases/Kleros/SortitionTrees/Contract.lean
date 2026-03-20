import Contracts.Common

namespace Benchmark.Cases.Kleros.SortitionTrees

open Verity hiding pure bind
open Verity.EVM.Uint256
open Verity.Stdlib.Math

/-
  Fixed-arity slice of Kleros SortitionTrees.
  The upstream library is dynamic over K and unbounded node arrays; this benchmark
  specializes it to a balanced binary tree with four leaves so the benchmark can
  focus on parent sums, root sums, draw intervals, and index/ID correspondence.
-/
verity_contract SortitionTrees where
  storage
    rootSum : Uint256 := slot 0
    leftSum : Uint256 := slot 1
    rightSum : Uint256 := slot 2
    leaf0 : Uint256 := slot 3
    leaf1 : Uint256 := slot 4
    leaf2 : Uint256 := slot 5
    leaf3 : Uint256 := slot 6
    nodeIndexesToIDs : Uint256 → Uint256 := slot 7
    IDsToNodeIndexes : Uint256 → Uint256 := slot 8
    selectedNode : Uint256 := slot 9

  function setLeaf (nodeIndex : Uint256, stakePathID : Uint256, weight : Uint256) : Unit := do
    require (nodeIndex >= 3) "LeafIndexTooSmall"
    require (nodeIndex <= 6) "LeafIndexTooLarge"

    let leaf0Value ← getStorage leaf0
    let leaf1Value ← getStorage leaf1
    let leaf2Value ← getStorage leaf2
    let leaf3Value ← getStorage leaf3

    let nextLeaf0 := ite (nodeIndex == 3) weight leaf0Value
    let nextLeaf1 := ite (nodeIndex == 4) weight leaf1Value
    let nextLeaf2 := ite (nodeIndex == 5) weight leaf2Value
    let nextLeaf3 := ite (nodeIndex == 6) weight leaf3Value

    setStorage leaf0 nextLeaf0
    setStorage leaf1 nextLeaf1
    setStorage leaf2 nextLeaf2
    setStorage leaf3 nextLeaf3

    setMappingUint nodeIndexesToIDs nodeIndex stakePathID
    setMappingUint IDsToNodeIndexes stakePathID nodeIndex

    let nextLeft := add nextLeaf0 nextLeaf1
    let nextRight := add nextLeaf2 nextLeaf3

    setStorage leftSum nextLeft
    setStorage rightSum nextRight
    setStorage rootSum (add nextLeft nextRight)

  function draw (ticket : Uint256) : Uint256 := do
    let root ← getStorage rootSum
    let left ← getStorage leftSum
    let leaf0Value ← getStorage leaf0
    let leaf2Value ← getStorage leaf2

    require (root != 0) "TreeEmpty"
    require (ticket < root) "TicketOutOfRange"

    let rightTicket := sub ticket left
    let selected :=
      ite (ticket < left)
        (ite (ticket < leaf0Value) 3 4)
        (ite (rightTicket < leaf2Value) 5 6)

    setStorage selectedNode selected
    return selected

end Benchmark.Cases.Kleros.SortitionTrees
