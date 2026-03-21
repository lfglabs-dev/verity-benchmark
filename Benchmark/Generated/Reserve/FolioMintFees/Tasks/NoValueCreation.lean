import Benchmark.Cases.Reserve.FolioMintFees.Specs

namespace Benchmark.Cases.Reserve.FolioMintFees

open Verity
open Verity.EVM.Uint256

/--
No value creation: sharesOut + daoFeeShares + feeRecipientFeeShares ≤ shares.
The gap is the folioSelfShares that are burned (not minted to anyone).
-/
theorem no_value_creation
    (shares mintFee folioFeeForSelf daoFeeNumerator daoFeeDenominator daoFeeFloor : Uint256)
    (s : ContractState)
    (hDen : daoFeeDenominator != 0)
    (hNoOverflow1 : shares.val * mintFee.val + 999999999999999999 < modulus)
    (hNoOverflow2 : shares.val * (Nat.max daoFeeFloor.val 300000000000000) + 999999999999999999 < modulus)
    (hFeeLeShares : div (add (mul shares mintFee) 999999999999999999) 1000000000000000000 ≤ shares)
    (hFloorLeShares : div (add (mul shares (if daoFeeFloor > 300000000000000 then daoFeeFloor else 300000000000000)) 999999999999999999) 1000000000000000000 ≤ shares) :
    let s' := ((FolioMintFees.computeMintFees shares mintFee folioFeeForSelf daoFeeNumerator daoFeeDenominator daoFeeFloor).run s).snd
    no_value_creation_spec shares s s' := by
  -- Replace this placeholder with a complete Lean proof.
  exact ?_

end Benchmark.Cases.Reserve.FolioMintFees
