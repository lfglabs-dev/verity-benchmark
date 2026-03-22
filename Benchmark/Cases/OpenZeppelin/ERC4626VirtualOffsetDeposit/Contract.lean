import Contracts.Common
import Verity.Stdlib.Math

namespace Benchmark.Cases.OpenZeppelin.ERC4626VirtualOffsetDeposit

open Verity hiding pure bind
open Verity.EVM.Uint256
open Verity.Stdlib.Math

/-
  Minimal Verity slice of OpenZeppelin ERC-4626 deposit math.
  The benchmark keeps only total-assets / total-shares storage, fixed virtual
  offsets, the `previewDeposit` floor-division rule, and the final `deposit`
  state update. Token transfers and all other vault behavior are elided.
-/

def virtualAssets : Uint256 := 1

def virtualShares : Uint256 := 1000

def previewDepositAmount (assets totalAssets totalShares : Uint256) : Uint256 :=
  div (mul assets (add totalShares virtualShares)) (add totalAssets virtualAssets)

verity_contract ERC4626VirtualOffsetDeposit where
  storage
    totalAssets : Uint256 := slot 0
    totalShares : Uint256 := slot 1

  function deposit (assets : Uint256) : Uint256 := do
    let oldTotalAssets ← getStorage totalAssets
    let oldTotalShares ← getStorage totalShares
    let mintedShares := div
      (mul assets (add oldTotalShares 1000))
      (add oldTotalAssets 1)

    setStorage totalAssets (add oldTotalAssets assets)
    setStorage totalShares (add oldTotalShares mintedShares)

    return mintedShares

end Benchmark.Cases.OpenZeppelin.ERC4626VirtualOffsetDeposit
