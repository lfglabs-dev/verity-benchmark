import Benchmark.Cases.OpenZeppelin.ERC4626VirtualOffsetDeposit.Specs

namespace Benchmark.Cases.OpenZeppelin.ERC4626VirtualOffsetDeposit

open Verity
open Verity.EVM.Uint256

/--
Executing `deposit` stores `oldTotalShares + previewDeposit(assets)` in `totalShares`.
-/
theorem deposit_sets_totalShares
    (assets : Uint256) (s : ContractState) :
    let s' := ((ERC4626VirtualOffsetDeposit.deposit assets).run s).snd
    deposit_sets_totalShares_spec assets s s' := by
  exact ?_

end Benchmark.Cases.OpenZeppelin.ERC4626VirtualOffsetDeposit
