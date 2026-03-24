import Benchmark.Cases.OpenZeppelin.ERC4626VirtualOffsetDeposit.Specs
import Verity.Proofs.Stdlib.Math

namespace Benchmark.Cases.OpenZeppelin.ERC4626VirtualOffsetDeposit

open Verity
open Verity.EVM.Uint256
open Verity.Stdlib.Math
open Verity.Proofs.Stdlib.Math

private theorem deposit_slot_writes
    (assets : Uint256) (s : ContractState) :
    let s' := ((ERC4626VirtualOffsetDeposit.deposit assets).run s).snd
    s'.storage 0 = add (s.storage 0) assets ∧
    s'.storage 1 = add (s.storage 1) (previewDeposit assets s) := by
  constructor
  · simp [ERC4626VirtualOffsetDeposit.deposit,
      ERC4626VirtualOffsetDeposit.totalAssets, ERC4626VirtualOffsetDeposit.totalShares,
      getStorage, setStorage, Verity.bind, Bind.bind, Verity.pure, Pure.pure, Contract.run,
      ContractResult.snd]
  · simp [ERC4626VirtualOffsetDeposit.deposit, previewDeposit, previewDepositAmount,
      virtualAssets, virtualShares, ERC4626VirtualOffsetDeposit.totalAssets,
      ERC4626VirtualOffsetDeposit.totalShares, getStorage, setStorage, Verity.bind, Bind.bind,
      Verity.pure, Pure.pure, Contract.run, ContractResult.snd]

theorem deposit_sets_totalAssets
    (assets : Uint256) (s : ContractState) :
    let s' := ((ERC4626VirtualOffsetDeposit.deposit assets).run s).snd
    deposit_sets_totalAssets_spec assets s s' := by
  unfold deposit_sets_totalAssets_spec
  exact (deposit_slot_writes assets s).1

theorem deposit_sets_totalShares
    (assets : Uint256) (s : ContractState) :
    let s' := ((ERC4626VirtualOffsetDeposit.deposit assets).run s).snd
    deposit_sets_totalShares_spec assets s s' := by
  unfold deposit_sets_totalShares_spec
  exact (deposit_slot_writes assets s).2

theorem previewDeposit_rounds_down
    (assets : Uint256) (s : ContractState)
    (hMul : (assets : Nat) * ((add (s.storage 1) virtualShares : Uint256) : Nat) <= MAX_UINT256) :
    previewDeposit_rounds_down_spec assets s := by
  unfold previewDeposit_rounds_down_spec previewDeposit previewDepositAmount
  simpa [mulDivDown] using mulDivDown_mul_le assets (add (s.storage 1) virtualShares)
    (add (s.storage 0) virtualAssets) hMul

theorem positive_deposit_mints_positive_shares_under_rate_bound
    (assets : Uint256) (s : ContractState)
    (_hAssets : assets ≠ 0)
    (hDenom : add (s.storage 0) virtualAssets ≠ 0)
    (hRate : ((add (s.storage 0) virtualAssets : Uint256) : Nat)
      <= (assets : Nat) * ((add (s.storage 1) virtualShares : Uint256) : Nat))
    (hMul : (assets : Nat) * ((add (s.storage 1) virtualShares : Uint256) : Nat) <= MAX_UINT256) :
    positive_deposit_mints_positive_shares_under_rate_bound_spec assets s := by
  unfold positive_deposit_mints_positive_shares_under_rate_bound_spec previewDeposit previewDepositAmount
  simpa [mulDivDown] using mulDivDown_pos assets (add (s.storage 1) virtualShares)
    (add (s.storage 0) virtualAssets) hDenom hRate hMul

end Benchmark.Cases.OpenZeppelin.ERC4626VirtualOffsetDeposit
