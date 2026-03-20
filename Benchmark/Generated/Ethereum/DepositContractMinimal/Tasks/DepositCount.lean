import Benchmark.Cases.Ethereum.DepositContractMinimal.Specs

namespace Benchmark.Cases.Ethereum.DepositContractMinimal

open Verity
open Verity.EVM.Uint256

/--
Executing `deposit` on the successful path increments the total deposit counter
by exactly one.
-/
theorem deposit_increments_deposit_count
    (depositAmount : Uint256) (s : ContractState)
    (hCount : s.storage 0 < 4294967295)
    (hMin : depositAmount >= 1000000000) :
    let s' := ((DepositContractMinimal.deposit depositAmount).run s).snd
    deposit_increments_deposit_count_spec s s' := by
  -- Replace this placeholder with a complete Lean proof.
  exact ?_

end Benchmark.Cases.Ethereum.DepositContractMinimal
