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
private theorem div_mul_le_div_mul (bv : Uint256)
    (hNoOverflow : bv.val * 10100 < modulus) :
    div (mul bv 9900) 10000 ≤ div (mul bv 10100) 10000 := by
  -- Work at Nat level
  show (div (mul bv 9900) 10000).val ≤ (div (mul bv 10100) 10000).val
  -- mul doesn't overflow
  have hMul9900Lt : bv.val * 9900 < modulus :=
    Nat.lt_of_le_of_lt (Nat.mul_le_mul_left bv.val (by omega : (9900 : Nat) ≤ 10100)) hNoOverflow
  have hMul9900 : (mul bv (9900 : Uint256)).val = bv.val * 9900 := by
    simp [HMul.hMul, Verity.Core.Uint256.mul, Verity.Core.Uint256.ofNat]
    exact Nat.mod_eq_of_lt hMul9900Lt
  have hMul10100 : (mul bv (10100 : Uint256)).val = bv.val * 10100 := by
    simp [HMul.hMul, Verity.Core.Uint256.mul, Verity.Core.Uint256.ofNat]
    exact Nat.mod_eq_of_lt hNoOverflow
  -- Expand div at Uint256 level
  simp only [HDiv.hDiv, Verity.Core.Uint256.div, hMul9900, hMul10100,
    show (10000 : Uint256).val ≠ 0 from by decide, ↓reduceIte,
    Verity.Core.Uint256.val_ofNat, Verity.Core.Uint256.modulus]
  -- Goal: Div.div (a) 10k % 2^256 ≤ Div.div (b) 10k % 2^256
  have h10kval : Verity.Core.Uint256.val (10000 : Uint256) = 10000 := by decide
  simp only [h10kval, Verity.Core.UINT256_MODULUS]
  -- Both quotients are < 2^256, so % is identity
  have h9900Lt : bv.val * 9900 / 10000 < 2 ^ 256 := by
    have : bv.val * 9900 / 10000 ≤ bv.val * 9900 := Nat.div_le_self _ _
    simp [modulus, Verity.Core.Uint256.modulus, Verity.Core.UINT256_MODULUS] at hMul9900Lt
    omega
  have h10100Lt : bv.val * 10100 / 10000 < 2 ^ 256 := by
    have : bv.val * 10100 / 10000 ≤ bv.val * 10100 := Nat.div_le_self _ _
    simp [modulus, Verity.Core.Uint256.modulus, Verity.Core.UINT256_MODULUS] at hNoOverflow
    omega
  -- Use show to normalize Div.div to / notation for rw to work
  show bv.val * 9900 / 10000 % 2 ^ 256 ≤ bv.val * 10100 / 10000 % 2 ^ 256
  rw [Nat.mod_eq_of_lt h9900Lt, Nat.mod_eq_of_lt h10100Lt]
  exact Nat.div_le_div_right (by omega : bv.val * 9900 ≤ bv.val * 10100)

theorem syncPriceBand_sell_le_buy
    (capital_ supply_ : Uint256) (s : ContractState)
    (hSupply : supply_ != 0)
    (hNoOverflow : (div (mul 1000000000000000000 capital_) supply_).val * 10100 < modulus) :
    let s' := ((RammPriceBand.syncPriceBand capital_ supply_).run s).snd
    syncPriceBand_sell_le_buy_spec s s' := by
  have hw := syncPriceBand_slot_write capital_ supply_ s hSupply
  simp only [syncPriceBand_sell_le_buy_spec, hw.2.2.2, hw.2.2.1]
  exact div_mul_le_div_mul _ hNoOverflow

end Benchmark.Cases.NexusMutual.RammPriceBand
