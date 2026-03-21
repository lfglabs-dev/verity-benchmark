import Benchmark.Cases.Reserve.FolioMintFees.Specs

namespace Benchmark.Cases.Reserve.FolioMintFees

open Verity
open Verity.EVM.Uint256

/--
Minter always pays at least the DAO share: shares - sharesOut >= daoFeeShares.
-/
theorem minter_pays_at_least_dao
    (shares mintFee folioFeeForSelf daoFeeNumerator daoFeeDenominator daoFeeFloor : Uint256)
    (s : ContractState)
    (hDen : daoFeeDenominator != 0)
    (hNoOverflow1 : shares.val * mintFee.val + 999999999999999999 < modulus)
    (hNoOverflow2 : shares.val * (Nat.max daoFeeFloor.val 300000000000000) + 999999999999999999 < modulus) :
    let s' := ((FolioMintFees.computeMintFees shares mintFee folioFeeForSelf daoFeeNumerator daoFeeDenominator daoFeeFloor).run s).snd
    minter_pays_at_least_dao_spec shares s s' := by
  -- Replace this placeholder with a complete Lean proof.
  exact ?_

end Benchmark.Cases.Reserve.FolioMintFees
