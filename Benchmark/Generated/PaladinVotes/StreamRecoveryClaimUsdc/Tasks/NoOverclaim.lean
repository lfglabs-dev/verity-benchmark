import Benchmark.Cases.PaladinVotes.StreamRecoveryClaimUsdc.Specs

namespace Benchmark.Cases.PaladinVotes.StreamRecoveryClaimUsdc

open Verity
open Verity.EVM.Uint256

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
  -- Replace this placeholder with a complete Lean proof.
  exact ?_

end Benchmark.Cases.PaladinVotes.StreamRecoveryClaimUsdc
