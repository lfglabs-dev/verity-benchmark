import Benchmark.Cases.PaladinVotes.StreamRecoveryClaimUsdc.Specs
import Verity.Proofs.Stdlib.Automation

namespace Benchmark.Cases.PaladinVotes.StreamRecoveryClaimUsdc

open Verity
open Verity.EVM.Uint256

private theorem add_sub_assoc (a b c : Uint256) : a + (b - c) = (a + b) - c := by
  have lhs_eq : (a + (b - c)) + c = a + b := by
    have hCancel := Verity.Core.Uint256.sub_add_cancel_left b c
    calc
      (a + (b - c)) + c = a + ((b - c) + c) := by rw [Verity.Core.Uint256.add_assoc]
      _ = a + b := by rw [hCancel]
  have rhs_eq : ((a + b) - c) + c = a + b :=
    Verity.Core.Uint256.sub_add_cancel_left (a + b) c
  exact Verity.Core.Uint256.add_right_cancel (by rw [lhs_eq, rhs_eq])

private theorem claimUsdc_slot_writes
    (shareWad : Uint256) (s : ContractState)
    (hWaiver : s.storageMap 4 s.sender != 0)
    (hActive : s.storage 3 != 0)
    (hFresh : s.storageMap 5 s.sender = 0)
    (hBound : add (s.storage 1) (computedClaimAmount shareWad s) <= s.storage 0) :
    let s' := ((StreamRecoveryClaimUsdc.claimUsdc shareWad true).run s).snd
    s'.storage 0 = s.storage 0 ∧
    s'.storageMap 5 s.sender = 1 ∧
    s'.storage 1 = add (s.storage 1) (computedClaimAmount shareWad s) ∧
    s'.storage 2 = sub (s.storage 2) (computedClaimAmount shareWad s) := by
  let amount := computedClaimAmount shareWad s
  have hFresh' : (s.storageMap 5 s.sender == 0) = true := by
    simp [hFresh]
  have hBound' :
      add (s.storage 1) (div (mul shareWad (s.storage 0)) 1000000000000000000) <= s.storage 0 := by
    simpa [computedClaimAmount] using hBound
  constructor
  · simp [amount, StreamRecoveryClaimUsdc.claimUsdc, computedClaimAmount, hWaiver, hActive, hFresh',
      hBound', StreamRecoveryClaimUsdc.roundUsdcTotal, StreamRecoveryClaimUsdc.roundUsdcClaimed,
      StreamRecoveryClaimUsdc.totalUsdcAllocated, StreamRecoveryClaimUsdc.roundActive,
      StreamRecoveryClaimUsdc.hasSignedWaiver, StreamRecoveryClaimUsdc.hasClaimedUsdc, getMapping,
      getStorage, setMapping, setStorage, msgSender, Verity.require, Verity.bind, Bind.bind,
      Verity.pure, Pure.pure, Contract.run, ContractResult.snd]
  constructor
  · simp [amount, StreamRecoveryClaimUsdc.claimUsdc, computedClaimAmount, hWaiver, hActive, hFresh',
      hBound', StreamRecoveryClaimUsdc.roundUsdcTotal, StreamRecoveryClaimUsdc.roundUsdcClaimed,
      StreamRecoveryClaimUsdc.totalUsdcAllocated, StreamRecoveryClaimUsdc.roundActive,
      StreamRecoveryClaimUsdc.hasSignedWaiver, StreamRecoveryClaimUsdc.hasClaimedUsdc, getMapping,
      getStorage, setMapping, setStorage, msgSender, Verity.require, Verity.bind, Bind.bind,
      Verity.pure, Pure.pure, Contract.run, ContractResult.snd]
  constructor
  · simp [amount, StreamRecoveryClaimUsdc.claimUsdc, computedClaimAmount, hWaiver, hActive, hFresh',
      hBound', StreamRecoveryClaimUsdc.roundUsdcTotal, StreamRecoveryClaimUsdc.roundUsdcClaimed,
      StreamRecoveryClaimUsdc.totalUsdcAllocated, StreamRecoveryClaimUsdc.roundActive,
      StreamRecoveryClaimUsdc.hasSignedWaiver, StreamRecoveryClaimUsdc.hasClaimedUsdc, getMapping,
      getStorage, setMapping, setStorage, msgSender, Verity.require, Verity.bind, Bind.bind,
      Verity.pure, Pure.pure, Contract.run, ContractResult.snd]
  · simp [amount, StreamRecoveryClaimUsdc.claimUsdc, computedClaimAmount, hWaiver, hActive, hFresh',
      hBound', StreamRecoveryClaimUsdc.roundUsdcTotal, StreamRecoveryClaimUsdc.roundUsdcClaimed,
      StreamRecoveryClaimUsdc.totalUsdcAllocated, StreamRecoveryClaimUsdc.roundActive,
      StreamRecoveryClaimUsdc.hasSignedWaiver, StreamRecoveryClaimUsdc.hasClaimedUsdc, getMapping,
      getStorage, setMapping, setStorage, msgSender, Verity.require, Verity.bind, Bind.bind,
      Verity.pure, Pure.pure, Contract.run, ContractResult.snd]

/--
Executing `claimUsdc` on the successful path marks the caller as claimed.
-/
theorem claimUsdc_marks_user_claimed
    (shareWad : Uint256) (s : ContractState)
    (hWaiver : s.storageMap 4 s.sender != 0)
    (hActive : s.storage 3 != 0)
    (hFresh : s.storageMap 5 s.sender = 0)
    (hBound : add (s.storage 1) (computedClaimAmount shareWad s) <= s.storage 0) :
    let s' := ((StreamRecoveryClaimUsdc.claimUsdc shareWad true).run s).snd
    claimUsdc_marks_claimed_spec s s' := by
  unfold claimUsdc_marks_claimed_spec
  exact (claimUsdc_slot_writes shareWad s hWaiver hActive hFresh hBound).2.1

/--
Executing `claimUsdc` on the successful path preserves the round bound.
-/
theorem claimUsdc_preserves_round_bound
    (shareWad : Uint256) (s : ContractState)
    (hWaiver : s.storageMap 4 s.sender != 0)
    (hActive : s.storage 3 != 0)
    (hFresh : s.storageMap 5 s.sender = 0)
    (hBound : add (s.storage 1) (computedClaimAmount shareWad s) <= s.storage 0) :
    let s' := ((StreamRecoveryClaimUsdc.claimUsdc shareWad true).run s).snd
    claimUsdc_preserves_round_bound_spec s' := by
  rcases claimUsdc_slot_writes shareWad s hWaiver hActive hFresh hBound with
    ⟨hTotal, _, hClaimed, _⟩
  unfold claimUsdc_preserves_round_bound_spec
  simpa [hTotal, hClaimed] using hBound

/--
Executing `claimUsdc` moves the computed amount from `totalUsdcAllocated`
into `roundUsdcClaimed`, preserving the combined accounting mass.
-/
theorem claimUsdc_claimed_plus_allocated_conserved
    (shareWad : Uint256) (s : ContractState)
    (hWaiver : s.storageMap 4 s.sender != 0)
    (hActive : s.storage 3 != 0)
    (hFresh : s.storageMap 5 s.sender = 0)
    (hBound : add (s.storage 1) (computedClaimAmount shareWad s) <= s.storage 0) :
    let s' := ((StreamRecoveryClaimUsdc.claimUsdc shareWad true).run s).snd
    claimUsdc_claimed_plus_allocated_conserved_spec shareWad s s' := by
  rcases claimUsdc_slot_writes shareWad s hWaiver hActive hFresh hBound with
    ⟨_, _, hClaimed, hAllocated⟩
  unfold claimUsdc_claimed_plus_allocated_conserved_spec
  dsimp
  rw [hClaimed, hAllocated]
  calc
    add (add (s.storage 1) (computedClaimAmount shareWad s)) (sub (s.storage 2) (computedClaimAmount shareWad s))
        = add (computedClaimAmount shareWad s) (add (s.storage 1) (sub (s.storage 2) (computedClaimAmount shareWad s))) := by
            calc
              add (add (s.storage 1) (computedClaimAmount shareWad s))
                  (sub (s.storage 2) (computedClaimAmount shareWad s))
                  =
                  add (add (computedClaimAmount shareWad s) (s.storage 1))
                    (sub (s.storage 2) (computedClaimAmount shareWad s)) := by
                      exact Verity.Core.Uint256.add_left_comm (s.storage 1)
                        (computedClaimAmount shareWad s)
                        (sub (s.storage 2) (computedClaimAmount shareWad s))
              _ = add (computedClaimAmount shareWad s)
                    (add (s.storage 1) (sub (s.storage 2) (computedClaimAmount shareWad s))) := by
                      exact Verity.Core.Uint256.add_assoc (computedClaimAmount shareWad s)
                        (s.storage 1)
                        (sub (s.storage 2) (computedClaimAmount shareWad s))
    _ = add (computedClaimAmount shareWad s) ((add (s.storage 1) (s.storage 2)) - computedClaimAmount shareWad s) := by
          simpa using congrArg (fun t => add (computedClaimAmount shareWad s) t)
            (add_sub_assoc (s.storage 1) (s.storage 2) (computedClaimAmount shareWad s))
    _ = add ((add (s.storage 1) (s.storage 2)) - computedClaimAmount shareWad s) (computedClaimAmount shareWad s) := by
          exact Verity.Core.Uint256.add_comm _ _
    _ = add (s.storage 1) (s.storage 2) := by
          exact Verity.Core.Uint256.sub_add_cancel_left (add (s.storage 1) (s.storage 2))
            (computedClaimAmount shareWad s)

end Benchmark.Cases.PaladinVotes.StreamRecoveryClaimUsdc
