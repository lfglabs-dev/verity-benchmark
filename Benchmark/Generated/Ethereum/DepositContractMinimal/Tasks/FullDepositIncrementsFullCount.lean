import Benchmark.Cases.Ethereum.DepositContractMinimal.Specs

namespace Benchmark.Cases.Ethereum.DepositContractMinimal

open Verity
open Verity.EVM.Uint256

/--
Executing `deposit` at or above the full threshold increments
`fullDepositCount` by one.
-/
theorem full_deposit_increments_full_count
    (depositAmount : Uint256) (s : ContractState)
    (hCount : s.storage 0 < 4294967295)
    (hMin : depositAmount >= 1000000000)
    (hFull : depositAmount >= 32000000000) :
    let s' := ((DepositContractMinimal.deposit depositAmount).run s).snd
    deposit_increments_full_count_for_full_deposit_spec depositAmount s s' := by
  -- Replace this placeholder with a complete Lean proof.
  exact ?_

end Benchmark.Cases.Ethereum.DepositContractMinimal
