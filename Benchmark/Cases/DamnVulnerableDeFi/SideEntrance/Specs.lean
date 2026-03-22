import Verity.Specs.Common
import Benchmark.Cases.DamnVulnerableDeFi.SideEntrance.Contract

namespace Benchmark.Cases.DamnVulnerableDeFi.SideEntrance

open Verity
open Verity.EVM.Uint256

def deposit_sets_pool_balance_spec
    (amount : Uint256) (s s' : ContractState) : Prop :=
  s'.storage 0 = add (s.storage 0) amount

def deposit_sets_sender_credit_spec
    (amount : Uint256) (s s' : ContractState) : Prop :=
  s'.storageMap 2 s.sender = add (s.storageMap 2 s.sender) amount

def flashLoanViaDeposit_preserves_pool_balance_spec
    (_amount : Uint256) (s s' : ContractState) : Prop :=
  s'.storage 0 = s.storage 0

def flashLoanViaDeposit_sets_sender_credit_spec
    (amount : Uint256) (s s' : ContractState) : Prop :=
  s'.storageMap 2 s.sender = add (s.storageMap 2 s.sender) amount

def exploit_trace_drains_pool_spec
    (amount : Uint256) (s s'' : ContractState) : Prop :=
  s''.storage 0 = sub (s.storage 0) amount

end Benchmark.Cases.DamnVulnerableDeFi.SideEntrance
