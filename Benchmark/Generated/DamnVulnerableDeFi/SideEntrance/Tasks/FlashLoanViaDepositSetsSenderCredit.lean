import Benchmark.Cases.DamnVulnerableDeFi.SideEntrance.Specs

namespace Benchmark.Cases.DamnVulnerableDeFi.SideEntrance

open Verity
open Verity.EVM.Uint256

/--
Executing the summarized flash-loan-plus-deposit path mints caller credit
equal to the borrowed amount.
-/
theorem flashLoanViaDeposit_sets_sender_credit
    (amount : Uint256) (s : ContractState)
    (hBorrow : amount <= s.storage 0) :
    let s' := ((SideEntrance.flashLoanViaDeposit amount).run s).snd
    flashLoanViaDeposit_sets_sender_credit_spec amount s s' := by
  sorry

end Benchmark.Cases.DamnVulnerableDeFi.SideEntrance
