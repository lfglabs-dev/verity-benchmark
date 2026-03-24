import Benchmark.Cases.NexusMutual.RammPriceBand.Specs
import Verity.Proofs.Stdlib.Automation

namespace Benchmark.Cases.NexusMutual.RammPriceBand

open Verity
open Verity.EVM.Uint256

private theorem syncPriceBand_slot_write
    (capital_ supply_ : Uint256) (s : ContractState)
    (hSupply : supply_ != 0) :
    let s' := ((RammPriceBand.syncPriceBand capital_ supply_).run s).snd
    s'.storage 0 = capital_ ∧
    s'.storage 2 = div (mul 1000000000000000000 capital_) supply_ ∧
    s'.storage 3 = div (mul (div (mul 1000000000000000000 capital_) supply_) 10100) 10000 ∧
    s'.storage 4 = div (mul (div (mul 1000000000000000000 capital_) supply_) 9900) 10000 := by
  repeat' constructor
  all_goals
    simp [RammPriceBand.syncPriceBand, hSupply, RammPriceBand.capital, RammPriceBand.supply,
      RammPriceBand.bookValue, RammPriceBand.buySpotPrice, RammPriceBand.sellSpotPrice,
      Verity.require, Verity.bind, Bind.bind, Contract.run, ContractResult.snd, setStorage]

/--
Executing `syncPriceBand` stores the provided capital value.
-/
theorem syncPriceBand_sets_capital
    (capital_ supply_ : Uint256) (s : ContractState)
    (hSupply : supply_ != 0) :
    let s' := ((RammPriceBand.syncPriceBand capital_ supply_).run s).snd
    syncPriceBand_sets_capital_spec capital_ s s' := by
  simpa [syncPriceBand_sets_capital_spec] using (syncPriceBand_slot_write capital_ supply_ s hSupply).1

/--
Executing `syncPriceBand` stores the synchronized book value.
-/
theorem syncPriceBand_sets_book_value
    (capital_ supply_ : Uint256) (s : ContractState)
    (hSupply : supply_ != 0) :
    let s' := ((RammPriceBand.syncPriceBand capital_ supply_).run s).snd
    syncPriceBand_sets_book_value_spec capital_ supply_ s s' := by
  simpa [syncPriceBand_sets_book_value_spec] using (syncPriceBand_slot_write capital_ supply_ s hSupply).2.1

/--
Executing `syncPriceBand` stores the synchronized buy quote.
-/
theorem syncPriceBand_sets_buy_price
    (capital_ supply_ : Uint256) (s : ContractState)
    (hSupply : supply_ != 0) :
    let s' := ((RammPriceBand.syncPriceBand capital_ supply_).run s).snd
    syncPriceBand_sets_buy_price_spec capital_ supply_ s s' := by
  simpa [syncPriceBand_sets_buy_price_spec] using (syncPriceBand_slot_write capital_ supply_ s hSupply).2.2.1

/--
Executing `syncPriceBand` stores the synchronized sell quote.
-/
theorem syncPriceBand_sets_sell_price
    (capital_ supply_ : Uint256) (s : ContractState)
    (hSupply : supply_ != 0) :
    let s' := ((RammPriceBand.syncPriceBand capital_ supply_).run s).snd
    syncPriceBand_sets_sell_price_spec capital_ supply_ s s' := by
  simpa [syncPriceBand_sets_sell_price_spec] using (syncPriceBand_slot_write capital_ supply_ s hSupply).2.2.2

/--
The sell spot price never exceeds the buy spot price,
provided the book-value multiplication does not overflow.
-/
theorem syncPriceBand_sell_le_buy
    (capital_ supply_ : Uint256) (s : ContractState)
    (hSupply : supply_ != 0)
    (hNoOverflow : (div (mul 1000000000000000000 capital_) supply_).val * 10100 < modulus) :
    let s' := ((RammPriceBand.syncPriceBand capital_ supply_).run s).snd
    syncPriceBand_sell_le_buy_spec s s' := by
  sorry

end Benchmark.Cases.NexusMutual.RammPriceBand
