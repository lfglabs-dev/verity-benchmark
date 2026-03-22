import Benchmark.Cases.DamnVulnerableDeFi.SideEntrance.Specs

namespace Benchmark.Cases.DamnVulnerableDeFi.SideEntrance

open Verity
open Verity.EVM.Uint256

/--
Executing `deposit` stores `oldPoolBalance + amount` in `poolBalance`.
-/
theorem deposit_sets_pool_balance
    (amount : Uint256) (s : ContractState) :
    let s' := ((SideEntrance.deposit amount).run s).snd
    deposit_sets_pool_balance_spec amount s s' := by
  sorry

end Benchmark.Cases.DamnVulnerableDeFi.SideEntrance
