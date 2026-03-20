import Benchmark.Cases.Ethereum.DepositContractMinimal.Specs

namespace Benchmark.Cases.Ethereum.DepositContractMinimal

open Verity
open Verity.EVM.Uint256

/--
Executing a full deposit increments both counters in lockstep, so the gap
between all deposits and full deposits is preserved.
-/
theorem full_deposit_preserves_partial_gap
    (depositAmount : Uint256) (s : ContractState)
    (hCount : s.storage 0 < 4294967295)
    (hMin : depositAmount >= 1000000000)
    (hFull : depositAmount >= 32000000000) :
    let s' := ((DepositContractMinimal.deposit depositAmount).run s).snd
    s'.storage 0 - s'.storage 1 = s.storage 0 - s.storage 1 := by
  -- Replace this placeholder with a complete Lean proof.
  exact ?_

end Benchmark.Cases.Ethereum.DepositContractMinimal
