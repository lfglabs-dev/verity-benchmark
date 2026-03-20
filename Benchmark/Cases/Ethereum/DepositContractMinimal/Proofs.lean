import Benchmark.Cases.Ethereum.DepositContractMinimal.Specs
import Verity.Proofs.Stdlib.Automation

namespace Benchmark.Cases.Ethereum.DepositContractMinimal

open Verity
open Verity.EVM.Uint256

private theorem deposit_small_slot_writes
    (depositAmount : Uint256) (s : ContractState)
    (hCount : s.storage 0 < 4294967295)
    (hMin : depositAmount >= 1000000000)
    (hSmall : depositAmount < 32000000000) :
    let s' := ((DepositContractMinimal.deposit depositAmount).run s).snd
    s'.storage 0 = add (s.storage 0) 1 ∧
    s'.storage 1 = s.storage 1 := by
  have hNotFull : ¬ 32000000000 ≤ depositAmount := by
    exact Nat.not_le_of_lt hSmall
  constructor
  · simp [DepositContractMinimal.deposit, hCount, hMin, hNotFull,
      DepositContractMinimal.depositCount, getStorage, setStorage, Verity.require, Verity.bind,
      Bind.bind, Verity.pure, Pure.pure, Contract.run, ContractResult.snd]
  · simp [DepositContractMinimal.deposit, hCount, hMin, hNotFull,
      DepositContractMinimal.depositCount, DepositContractMinimal.fullDepositCount, getStorage,
      setStorage, Verity.require, Verity.bind, Bind.bind, Verity.pure, Pure.pure, Contract.run,
      ContractResult.snd]

private theorem deposit_full_slot_writes
    (depositAmount : Uint256) (s : ContractState)
    (hCount : s.storage 0 < 4294967295)
    (hMin : depositAmount >= 1000000000)
    (hFull : depositAmount >= 32000000000) :
    let s' := ((DepositContractMinimal.deposit depositAmount).run s).snd
    s'.storage 0 = add (s.storage 0) 1 ∧
    s'.storage 1 = add (s.storage 1) 1 := by
  by_cases hThreshold : add (s.storage 1) 1 = 65536
  · constructor
    · simp [DepositContractMinimal.deposit, hCount, hMin, hFull, hThreshold,
        DepositContractMinimal.depositCount, DepositContractMinimal.fullDepositCount,
        DepositContractMinimal.chainStarted, getStorage, setStorage, Verity.require, Verity.bind,
        Bind.bind, Verity.pure, Pure.pure, Contract.run, ContractResult.snd]
    · simp [DepositContractMinimal.deposit, hCount, hMin, hFull, hThreshold,
        DepositContractMinimal.depositCount, DepositContractMinimal.fullDepositCount,
        DepositContractMinimal.chainStarted, getStorage, setStorage, Verity.require, Verity.bind,
        Bind.bind, Verity.pure, Pure.pure, Contract.run, ContractResult.snd]
  · constructor
    · simp [DepositContractMinimal.deposit, hCount, hMin, hFull, hThreshold,
        DepositContractMinimal.depositCount, DepositContractMinimal.fullDepositCount,
        DepositContractMinimal.chainStarted, getStorage, setStorage, Verity.require, Verity.bind,
        Bind.bind, Verity.pure, Pure.pure, Contract.run, ContractResult.snd]
    · simp [DepositContractMinimal.deposit, hCount, hMin, hFull, hThreshold,
        DepositContractMinimal.depositCount, DepositContractMinimal.fullDepositCount,
        DepositContractMinimal.chainStarted, getStorage, setStorage, Verity.require, Verity.bind,
        Bind.bind, Verity.pure, Pure.pure, Contract.run, ContractResult.snd]

private theorem deposit_full_sets_chain_started
    (depositAmount : Uint256) (s : ContractState)
    (hCount : s.storage 0 < 4294967295)
    (hMin : depositAmount >= 1000000000)
    (hFull : depositAmount >= 32000000000)
    (hThreshold : add (s.storage 1) 1 = 65536) :
    let s' := ((DepositContractMinimal.deposit depositAmount).run s).snd
    s'.storage 2 = 1 := by
  simp [DepositContractMinimal.deposit, hCount, hMin, hFull, hThreshold,
    DepositContractMinimal.depositCount, DepositContractMinimal.fullDepositCount,
    DepositContractMinimal.chainStarted, getStorage, setStorage, Verity.require, Verity.bind,
    Bind.bind, Contract.run, ContractResult.snd]

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
  unfold deposit_increments_deposit_count_spec
  by_cases hFull : depositAmount >= 32000000000
  · exact (deposit_full_slot_writes depositAmount s hCount hMin hFull).1
  · have hSmall : depositAmount < 32000000000 := Nat.lt_of_not_ge hFull
    exact (deposit_small_slot_writes depositAmount s hCount hMin hSmall).1

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
  unfold deposit_preserves_full_count_for_small_deposit_spec
  dsimp
  intro _hSmall
  simpa using (deposit_small_slot_writes depositAmount s hCount hMin hSmall).2

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
  unfold deposit_increments_full_count_for_full_deposit_spec
  dsimp
  intro _hFull
  simpa using (deposit_full_slot_writes depositAmount s hCount hMin hFull).2

/--
Executing a threshold-crossing full deposit sets `chainStarted`.
-/
theorem full_deposit_starts_chain_at_threshold
    (depositAmount : Uint256) (s : ContractState)
    (hCount : s.storage 0 < 4294967295)
    (hMin : depositAmount >= 1000000000)
    (hFull : depositAmount >= 32000000000)
    (hThreshold : add (s.storage 1) 1 = 65536) :
    let s' := ((DepositContractMinimal.deposit depositAmount).run s).snd
    deposit_starts_chain_at_threshold_spec depositAmount s s' := by
  unfold deposit_starts_chain_at_threshold_spec
  dsimp
  intro _hFull _hThreshold
  simpa using deposit_full_sets_chain_started depositAmount s hCount hMin hFull hThreshold

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
  dsimp
  rcases deposit_full_slot_writes depositAmount s hCount hMin hFull with ⟨hDeposits, hFullDeposits⟩
  rw [hDeposits, hFullDeposits]
  apply Verity.Core.Uint256.add_right_cancel
  calc
    ((s.storage 0 + 1) - (s.storage 1 + 1)) + (s.storage 1 + 1)
        = s.storage 0 + 1 := by
            exact Verity.Core.Uint256.sub_add_cancel_left (s.storage 0 + 1) (s.storage 1 + 1)
    _ = (s.storage 0 - s.storage 1) + (s.storage 1 + 1) := by
          rw [← Verity.Core.Uint256.add_assoc]
          rw [Verity.Core.Uint256.sub_add_cancel_left (s.storage 0) (s.storage 1)]

end Benchmark.Cases.Ethereum.DepositContractMinimal
