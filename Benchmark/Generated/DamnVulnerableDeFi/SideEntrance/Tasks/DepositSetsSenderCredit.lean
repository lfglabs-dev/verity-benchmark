import Benchmark.Cases.DamnVulnerableDeFi.SideEntrance.Specs

namespace Benchmark.Cases.DamnVulnerableDeFi.SideEntrance

open Verity
open Verity.EVM.Uint256

/--
Executing `deposit` increases the caller's credited balance by `amount`.
-/
theorem deposit_sets_sender_credit
    (amount : Uint256) (s : ContractState) :
    let s' := ((SideEntrance.deposit amount).run s).snd
    deposit_sets_sender_credit_spec amount s s' := by
  sorry

end Benchmark.Cases.DamnVulnerableDeFi.SideEntrance
