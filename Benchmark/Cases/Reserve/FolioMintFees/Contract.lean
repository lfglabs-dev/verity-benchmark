import Contracts.Common

namespace Benchmark.Cases.Reserve.FolioMintFees

open Verity hiding pure bind
open Verity.EVM.Uint256
open Verity.Stdlib.Math

/-
  Focused Verity slice of Reserve Protocol's Folio mint fee computation.
  The benchmark isolates the fee-split arithmetic from `FolioLib.computeMintFees`,
  which distributes minted shares among the receiver, the DAO, and fee recipients,
  enforcing a DAO fee floor and an optional self-fee burn.
  External dependencies (the DAO fee registry) are abstracted as function parameters.

  The verity_contract macro requires `if` at the monadic statement level, so the
  three max() operations from the Solidity source are expressed as explicit branches.
-/
verity_contract FolioMintFees where
  storage
    sharesOut : Uint256 := slot 0
    daoFeeShares : Uint256 := slot 1
    feeRecipientFeeShares : Uint256 := slot 2

  function computeMintFees (
    shares : Uint256,
    mintFee : Uint256,
    folioFeeForSelf : Uint256,
    daoFeeNumerator : Uint256,
    daoFeeDenominator : Uint256,
    daoFeeFloor : Uint256
  ) : Unit := do
    require (daoFeeDenominator != 0) "ZeroDenominator"

    -- totalFeeShares = ceilDiv(shares * mintFee, 1e18)
    let totalFeeShares := div (add (mul shares mintFee) 999999999999999999) 1000000000000000000

    -- daoShares = ceilDiv(totalFeeShares * daoFeeNumerator, daoFeeDenominator)
    let daoShares := div (add (mul totalFeeShares daoFeeNumerator) (sub daoFeeDenominator 1)) daoFeeDenominator

    -- Branch on effectiveFloor = max(daoFeeFloor, MIN_MINT_FEE)
    if daoFeeFloor > 300000000000000 then
      -- effectiveFloor = daoFeeFloor
      let minDaoShares := div (add (mul shares daoFeeFloor) 999999999999999999) 1000000000000000000
      -- finalDaoShares = max(daoShares, minDaoShares)
      if daoShares < minDaoShares then
        -- finalTotalFees = max(totalFeeShares, minDaoShares)
        if totalFeeShares < minDaoShares then
          setStorage sharesOut (sub shares minDaoShares)
          setStorage daoFeeShares minDaoShares
          setStorage feeRecipientFeeShares 0
        else
          let recipientPortion := sub totalFeeShares minDaoShares
          let folioSelfShares := div (mul recipientPortion folioFeeForSelf) 1000000000000000000
          setStorage sharesOut (sub shares totalFeeShares)
          setStorage daoFeeShares minDaoShares
          setStorage feeRecipientFeeShares (sub recipientPortion folioSelfShares)
      else
        if totalFeeShares < daoShares then
          setStorage sharesOut (sub shares daoShares)
          setStorage daoFeeShares daoShares
          setStorage feeRecipientFeeShares 0
        else
          let recipientPortion := sub totalFeeShares daoShares
          let folioSelfShares := div (mul recipientPortion folioFeeForSelf) 1000000000000000000
          setStorage sharesOut (sub shares totalFeeShares)
          setStorage daoFeeShares daoShares
          setStorage feeRecipientFeeShares (sub recipientPortion folioSelfShares)
    else
      -- effectiveFloor = MIN_MINT_FEE = 300000000000000
      let minDaoShares := div (add (mul shares 300000000000000) 999999999999999999) 1000000000000000000
      if daoShares < minDaoShares then
        if totalFeeShares < minDaoShares then
          setStorage sharesOut (sub shares minDaoShares)
          setStorage daoFeeShares minDaoShares
          setStorage feeRecipientFeeShares 0
        else
          let recipientPortion := sub totalFeeShares minDaoShares
          let folioSelfShares := div (mul recipientPortion folioFeeForSelf) 1000000000000000000
          setStorage sharesOut (sub shares totalFeeShares)
          setStorage daoFeeShares minDaoShares
          setStorage feeRecipientFeeShares (sub recipientPortion folioSelfShares)
      else
        if totalFeeShares < daoShares then
          setStorage sharesOut (sub shares daoShares)
          setStorage daoFeeShares daoShares
          setStorage feeRecipientFeeShares 0
        else
          let recipientPortion := sub totalFeeShares daoShares
          let folioSelfShares := div (mul recipientPortion folioFeeForSelf) 1000000000000000000
          setStorage sharesOut (sub shares totalFeeShares)
          setStorage daoFeeShares daoShares
          setStorage feeRecipientFeeShares (sub recipientPortion folioSelfShares)

end Benchmark.Cases.Reserve.FolioMintFees
