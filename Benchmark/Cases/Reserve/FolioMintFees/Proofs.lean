import Benchmark.Cases.Reserve.FolioMintFees.Specs
import Verity.Proofs.Stdlib.Automation

namespace Benchmark.Cases.Reserve.FolioMintFees

open Verity
open Verity.EVM.Uint256

/--
No value creation: sharesOut + daoFeeShares + feeRecipientFeeShares ≤ shares.
The gap is the folioSelfShares that are burned.
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
  sorry

/--
DAO floor enforced: the DAO receives at least ceilDiv(shares * effectiveFloor, 1e18).
-/
theorem dao_floor_enforced
    (shares mintFee folioFeeForSelf daoFeeNumerator daoFeeDenominator daoFeeFloor : Uint256)
    (s : ContractState)
    (hDen : daoFeeDenominator != 0)
    (hNoOverflow1 : shares.val * mintFee.val + 999999999999999999 < modulus)
    (hNoOverflow2 : shares.val * (Nat.max daoFeeFloor.val 300000000000000) + 999999999999999999 < modulus) :
    let s' := ((FolioMintFees.computeMintFees shares mintFee folioFeeForSelf daoFeeNumerator daoFeeDenominator daoFeeFloor).run s).snd
    dao_floor_enforced_spec shares daoFeeFloor s s' := by
  sorry

/--
Minter always pays at least the DAO share.
-/
theorem minter_pays_at_least_dao
    (shares mintFee folioFeeForSelf daoFeeNumerator daoFeeDenominator daoFeeFloor : Uint256)
    (s : ContractState)
    (hDen : daoFeeDenominator != 0)
    (hNoOverflow1 : shares.val * mintFee.val + 999999999999999999 < modulus)
    (hNoOverflow2 : shares.val * (Nat.max daoFeeFloor.val 300000000000000) + 999999999999999999 < modulus) :
    let s' := ((FolioMintFees.computeMintFees shares mintFee folioFeeForSelf daoFeeNumerator daoFeeDenominator daoFeeFloor).run s).snd
    minter_pays_at_least_dao_spec shares s s' := by
  sorry

/--
Conservation when folioFeeForSelf is zero: sharesOut + daoFeeShares +
feeRecipientFeeShares = shares.
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
  sorry

end Benchmark.Cases.Reserve.FolioMintFees
