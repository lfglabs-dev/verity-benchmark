import Contracts.Common

namespace Benchmark.Cases.PaladinVotes.StreamRecoveryClaimUsdc

open Verity hiding pure bind
open Verity.EVM.Uint256
open Verity.Stdlib.Math

/-
  Minimal Verity slice of StreamRecoveryClaim._claimUsdc specialized to a single active
  round. Merkle verification is abstracted as a boolean input and token transfer side
  effects are omitted; the benchmark focuses on the accounting path that enforces
  "cannot claim more than allocated".
-/
verity_contract StreamRecoveryClaimUsdc where
  storage
    roundUsdcTotal : Uint256 := slot 0
    roundUsdcClaimed : Uint256 := slot 1
    totalUsdcAllocated : Uint256 := slot 2
    roundActive : Uint256 := slot 3
    hasSignedWaiver : Address → Uint256 := slot 4
    hasClaimedUsdc : Address → Uint256 := slot 5

  function claimUsdc (shareWad : Uint256, proofAccepted : Bool) : Uint256 := do
    let sender ← msgSender
    let waiverSigned ← getMapping hasSignedWaiver sender
    let active ← getStorage roundActive
    let alreadyClaimed ← getMapping hasClaimedUsdc sender
    let roundTotal ← getStorage roundUsdcTotal
    let roundClaimed ← getStorage roundUsdcClaimed
    let totalAllocated ← getStorage totalUsdcAllocated

    require (waiverSigned != 0) "WaiverNotSigned"
    require (active != 0) "RoundNotActive"
    require (alreadyClaimed == 0) "AlreadyClaimed"
    require proofAccepted "InvalidProof"

    let amount := div (mul shareWad roundTotal) 1000000000000000000
    require (add roundClaimed amount <= roundTotal) "ClaimExceedsTotal"

    setMapping hasClaimedUsdc sender 1
    setStorage roundUsdcClaimed (add roundClaimed amount)
    setStorage totalUsdcAllocated (sub totalAllocated amount)
    return amount

  function claimableUsdc (shareWad : Uint256) : Uint256 := do
    let roundTotal ← getStorage roundUsdcTotal
    return (div (mul shareWad roundTotal) 1000000000000000000)

end Benchmark.Cases.PaladinVotes.StreamRecoveryClaimUsdc
