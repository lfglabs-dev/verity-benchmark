import Benchmark.Cases.OpenZeppelin.ERC4626VirtualOffsetDeposit.Specs
import Verity.Stdlib.Math

namespace Benchmark.Cases.OpenZeppelin.ERC4626VirtualOffsetDeposit

open Verity
open Verity.EVM.Uint256
open Verity.Stdlib.Math

/--
`previewDeposit` rounds down, so the minted share estimate times the denominator
never exceeds the exact numerator product when the multiplication is exact.
-/
theorem previewDeposit_rounds_down
    (assets : Uint256) (s : ContractState)
    (hMul : (assets : Nat) * ((add (s.storage 1) virtualShares : Uint256) : Nat) <= MAX_UINT256) :
    previewDeposit_rounds_down_spec assets s := by
  exact ?_

end Benchmark.Cases.OpenZeppelin.ERC4626VirtualOffsetDeposit
