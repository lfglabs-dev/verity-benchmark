import Benchmark.Cases.OpenZeppelin.ERC4626VirtualOffsetDeposit.Specs
import Verity.Stdlib.Math

namespace Benchmark.Cases.OpenZeppelin.ERC4626VirtualOffsetDeposit

open Verity
open Verity.EVM.Uint256
open Verity.Stdlib.Math

/--
Under the rate-bound assumption that the exact numerator already reaches one full
denominator-width, a positive deposit mints a positive number of shares.
-/
theorem positive_deposit_mints_positive_shares_under_rate_bound
    (assets : Uint256) (s : ContractState)
    (hAssets : assets ≠ 0)
    (hDenom : add (s.storage 0) virtualAssets ≠ 0)
    (hRate : ((add (s.storage 0) virtualAssets : Uint256) : Nat)
      <= (assets : Nat) * ((add (s.storage 1) virtualShares : Uint256) : Nat))
    (hMul : (assets : Nat) * ((add (s.storage 1) virtualShares : Uint256) : Nat) <= MAX_UINT256) :
    positive_deposit_mints_positive_shares_under_rate_bound_spec assets s := by
  exact ?_

end Benchmark.Cases.OpenZeppelin.ERC4626VirtualOffsetDeposit
