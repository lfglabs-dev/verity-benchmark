import Benchmark.Cases.Reserve.FolioMintFees.Specs

namespace Benchmark.Cases.Reserve.FolioMintFees

open Verity
open Verity.EVM.Uint256

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
  -- Replace this placeholder with a complete Lean proof.
  exact ?_

end Benchmark.Cases.Reserve.FolioMintFees
