import Benchmark.Cases.Reserve.FolioMintFees.Specs

namespace Benchmark.Cases.Reserve.FolioMintFees

open Verity
open Verity.EVM.Uint256

/--
Conservation when folioFeeForSelf is zero: sharesOut + daoFeeShares +
feeRecipientFeeShares = shares. No value is burned, so the split is exact.
-/
theorem conservation_no_self_fee
    (shares mintFee daoFeeNumerator daoFeeDenominator daoFeeFloor : Uint256)
    (s : ContractState)
    (hDen : daoFeeDenominator != 0)
    (hNoOverflow1 : shares.val * mintFee.val + 999999999999999999 < modulus)
    (hNoOverflow2 : shares.val * (Nat.max daoFeeFloor.val 300000000000000) + 999999999999999999 < modulus)
    (hFeeLeShares : div (add (mul shares mintFee) 999999999999999999) 1000000000000000000 ≤ shares)
    (hFloorLeShares : div (add (mul shares (if daoFeeFloor > 300000000000000 then daoFeeFloor else 300000000000000)) 999999999999999999) 1000000000000000000 ≤ shares) :
    let s' := ((FolioMintFees.computeMintFees shares mintFee 0 daoFeeNumerator daoFeeDenominator daoFeeFloor).run s).snd
    conservation_no_self_fee_spec shares s s' := by
  -- Replace this placeholder with a complete Lean proof.
  exact ?_

end Benchmark.Cases.Reserve.FolioMintFees
