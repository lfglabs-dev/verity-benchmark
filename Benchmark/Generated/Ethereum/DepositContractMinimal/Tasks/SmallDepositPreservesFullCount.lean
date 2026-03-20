import Benchmark.Cases.Ethereum.DepositContractMinimal.Specs

namespace Benchmark.Cases.Ethereum.DepositContractMinimal

open Verity
open Verity.EVM.Uint256

/--
Executing `deposit` below the full threshold leaves `fullDepositCount`
unchanged.
-/
theorem small_deposit_preserves_full_count
    (depositAmount : Uint256) (s : ContractState)
    (hCount : s.storage 0 < 4294967295)
    (hMin : depositAmount >= 1000000000)
    (hSmall : depositAmount < 32000000000) :
    let s' := ((DepositContractMinimal.deposit depositAmount).run s).snd
    deposit_preserves_full_count_for_small_deposit_spec depositAmount s s' := by
  -- Replace this placeholder with a complete Lean proof.
  exact ?_

end Benchmark.Cases.Ethereum.DepositContractMinimal
