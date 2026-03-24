import Verity.Specs.Common
import Benchmark.Cases.OpenZeppelin.ERC4626VirtualOffsetDeposit.Contract

namespace Benchmark.Cases.OpenZeppelin.ERC4626VirtualOffsetDeposit

open Verity
open Verity.EVM.Uint256

def previewDeposit (assets : Uint256) (s : ContractState) : Uint256 :=
  previewDepositAmount assets (s.storage 0) (s.storage 1)

def deposit_sets_totalAssets_spec
    (assets : Uint256) (s s' : ContractState) : Prop :=
  s'.storage 0 = add (s.storage 0) assets

def deposit_sets_totalShares_spec
    (assets : Uint256) (s s' : ContractState) : Prop :=
  s'.storage 1 = add (s.storage 1) (previewDeposit assets s)

def previewDeposit_rounds_down_spec
    (assets : Uint256) (s : ContractState) : Prop :=
  (previewDeposit assets s : Nat) * ((add (s.storage 0) virtualAssets : Uint256) : Nat)
    <= (assets : Nat) * ((add (s.storage 1) virtualShares : Uint256) : Nat)

def positive_deposit_mints_positive_shares_under_rate_bound_spec
    (assets : Uint256) (s : ContractState) : Prop :=
  0 < (previewDeposit assets s : Nat)

end Benchmark.Cases.OpenZeppelin.ERC4626VirtualOffsetDeposit
