import Benchmark.Cases.Ethereum.DepositContractMinimal.Specs

namespace Benchmark.Cases.Ethereum.DepositContractMinimal

open Verity
open Verity.EVM.Uint256

/--
A full deposit increments both `depositCount` and `fullDepositCount`, so the
gap between all deposits and full deposits is preserved.
-/
theorem full_deposit_preserves_partial_gap
    (depositAmount : Uint256) (s s' : ContractState) :
    deposit_increments_deposit_count_spec s s' ->
    deposit_increments_full_count_for_full_deposit_spec depositAmount s s' ->
    s'.storage 0 - s'.storage 1 = s.storage 0 - s.storage 1 := by
  intro hDeposit hFull
  unfold deposit_increments_deposit_count_spec at hDeposit
  unfold deposit_increments_full_count_for_full_deposit_spec at hFull
  rw [hDeposit, hFull]
  apply Verity.Core.Uint256.add_right_cancel
  calc
    ((s.storage 0 + 1) - (s.storage 1 + 1)) + (s.storage 1 + 1)
        = s.storage 0 + 1 := by
            exact Verity.Core.Uint256.sub_add_cancel_left (s.storage 0 + 1) (s.storage 1 + 1)
    _ = (s.storage 0 - s.storage 1) + (s.storage 1 + 1) := by
          rw [Verity.Core.Uint256.add_assoc]
          rw [Verity.Core.Uint256.sub_add_cancel_left (s.storage 0) (s.storage 1)]

end Benchmark.Cases.Ethereum.DepositContractMinimal
