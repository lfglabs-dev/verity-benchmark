import Verity.Specs.Common
import Benchmark.Cases.PaladinVotes.StreamRecoveryClaimUsdc.Contract

namespace Benchmark.Cases.PaladinVotes.StreamRecoveryClaimUsdc

open Verity
open Verity.EVM.Uint256

def computedClaimAmount (shareWad : Uint256) (s : ContractState) : Uint256 :=
  div (mul shareWad (s.storage 0)) 1000000000000000000

def claimUsdc_marks_claimed_spec (s s' : ContractState) : Prop :=
  s'.storageMap 5 s.sender = 1

def claimUsdc_updates_round_claimed_spec (shareWad : Uint256) (s s' : ContractState) : Prop :=
  s'.storage 1 = add (s.storage 1) (computedClaimAmount shareWad s)

def claimUsdc_updates_total_allocated_spec (shareWad : Uint256) (s s' : ContractState) : Prop :=
  s'.storage 2 = sub (s.storage 2) (computedClaimAmount shareWad s)

def claimUsdc_claimed_plus_allocated_conserved_spec (_shareWad : Uint256) (s s' : ContractState) : Prop :=
  add (s'.storage 1) (s'.storage 2) = add (s.storage 1) (s.storage 2)

def claimUsdc_preserves_round_bound_spec (s' : ContractState) : Prop :=
  s'.storage 1 <= s'.storage 0

end Benchmark.Cases.PaladinVotes.StreamRecoveryClaimUsdc
