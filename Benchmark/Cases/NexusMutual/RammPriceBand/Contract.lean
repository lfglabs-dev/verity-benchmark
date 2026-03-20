import Contracts.Common

namespace Benchmark.Cases.NexusMutual.RammPriceBand

open Verity hiding pure bind
open Verity.EVM.Uint256
open Verity.Stdlib.Math

/-
  Focused Verity slice of Nexus Mutual's RAMM pricing surface.
  The real contract derives buy and sell prices from reserves, ratchets, and a
  1% buffer around book value. This benchmark freezes that invariant-relevant
  boundary computation and omits reserve adjustment, TWAP, and swap execution.
-/
verity_contract RammPriceBand where
  storage
    capital : Uint256 := slot 0
    supply : Uint256 := slot 1
    bookValue : Uint256 := slot 2
    buySpotPrice : Uint256 := slot 3
    sellSpotPrice : Uint256 := slot 4

  function syncPriceBand (capital_ : Uint256, supply_ : Uint256) : Unit := do
    require (supply_ != 0) "SupplyMustBePositive"

    let bv := div (mul 1000000000000000000 capital_) supply_
    let buy := div (mul bv 10100) 10000
    let sell := div (mul bv 9900) 10000

    setStorage capital capital_
    setStorage supply supply_
    setStorage bookValue bv
    setStorage buySpotPrice buy
    setStorage sellSpotPrice sell

end Benchmark.Cases.NexusMutual.RammPriceBand
