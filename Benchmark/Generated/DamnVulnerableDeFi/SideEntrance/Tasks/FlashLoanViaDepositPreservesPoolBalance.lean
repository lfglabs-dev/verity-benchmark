import Benchmark.Cases.DamnVulnerableDeFi.SideEntrance.Specs

namespace Benchmark.Cases.DamnVulnerableDeFi.SideEntrance

open Verity
open Verity.EVM.Uint256

/--
Executing the summarized flash-loan-plus-deposit path leaves tracked pool ETH
unchanged.
-/
theorem flashLoanViaDeposit_preserves_pool_balance
    (amount : Uint256) (s : ContractState)
    (hBorrow : amount <= s.storage 0) :
    let s' := ((SideEntrance.flashLoanViaDeposit amount).run s).snd
    flashLoanViaDeposit_preserves_pool_balance_spec amount s s' := by
  sorry

end Benchmark.Cases.DamnVulnerableDeFi.SideEntrance
