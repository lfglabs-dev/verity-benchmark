import Verity.Specs.Common
import Benchmark.Cases.Ethereum.DepositContractMinimal.Contract

namespace Benchmark.Cases.Ethereum.DepositContractMinimal

open Verity
open Verity.EVM.Uint256

def deposit_increments_deposit_count_spec (s s' : ContractState) : Prop :=
  s'.storage 0 = add (s.storage 0) 1

def deposit_preserves_full_count_for_small_deposit_spec (depositAmount : Uint256) (s s' : ContractState) : Prop :=
  depositAmount < 32000000000 -> s'.storage 1 = s.storage 1

def deposit_increments_full_count_for_full_deposit_spec (depositAmount : Uint256) (s s' : ContractState) : Prop :=
  depositAmount >= 32000000000 -> s'.storage 1 = add (s.storage 1) 1

def deposit_starts_chain_at_threshold_spec (depositAmount : Uint256) (s s' : ContractState) : Prop :=
  depositAmount >= 32000000000 ->
  add (s.storage 1) 1 = 65536 ->
  s'.storage 2 = 1

end Benchmark.Cases.Ethereum.DepositContractMinimal
