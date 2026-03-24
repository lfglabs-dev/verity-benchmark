import Verity.Specs.Common
import Benchmark.Cases.NexusMutual.RammPriceBand.Contract

namespace Benchmark.Cases.NexusMutual.RammPriceBand

open Verity
open Verity.EVM.Uint256

def syncPriceBand_sets_capital_spec
    (capital_ : Uint256) (_s s' : ContractState) : Prop :=
  s'.storage 0 = capital_

def syncPriceBand_sets_book_value_spec
    (capital_ supply_ : Uint256) (_s s' : ContractState) : Prop :=
  s'.storage 2 = div (mul 1000000000000000000 capital_) supply_

def syncPriceBand_sets_buy_price_spec
    (capital_ supply_ : Uint256) (_s s' : ContractState) : Prop :=
  let bv := div (mul 1000000000000000000 capital_) supply_
  s'.storage 3 = div (mul bv 10100) 10000

def syncPriceBand_sets_sell_price_spec
    (capital_ supply_ : Uint256) (_s s' : ContractState) : Prop :=
  let bv := div (mul 1000000000000000000 capital_) supply_
  s'.storage 4 = div (mul bv 9900) 10000

def syncPriceBand_sell_le_buy_spec
    (_s s' : ContractState) : Prop :=
  s'.storage 4 ≤ s'.storage 3

end Benchmark.Cases.NexusMutual.RammPriceBand
