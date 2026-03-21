import Verity.Specs.Common
import Benchmark.Cases.Reserve.FolioMintFees.Contract

namespace Benchmark.Cases.Reserve.FolioMintFees

open Verity
open Verity.EVM.Uint256

/-
  D18 = 1e18, used for fixed-point arithmetic throughout.
  MIN_MINT_FEE = 300000000000000 (0.03%)
-/

/--
  No value creation: the sum of receiver shares, DAO shares, and fee recipient
  shares never exceeds the original share amount. The difference is the
  folioSelfShares that are burned (not minted to anyone).
-/
def no_value_creation_spec
    (shares : Uint256) (_s s' : ContractState) : Prop :=
  s'.storage 0 + s'.storage 1 + s'.storage 2 ≤ shares

/--
  DAO floor enforced: the DAO always receives at least
  ceilDiv(shares * max(daoFeeFloor, MIN_MINT_FEE), 1e18) shares.
-/
def dao_floor_enforced_spec
    (shares daoFeeFloor : Uint256) (_s s' : ContractState) : Prop :=
  let effectiveFloor := if daoFeeFloor > 300000000000000
    then daoFeeFloor
    else 300000000000000
  s'.storage 1 ≥ div (add (mul shares effectiveFloor) 999999999999999999) 1000000000000000000

/--
  Minter always pays: the total fee deducted from the minter
  (shares - sharesOut) is at least the DAO's portion.
-/
def minter_pays_at_least_dao_spec
    (shares : Uint256) (_s s' : ContractState) : Prop :=
  sub shares (s'.storage 0) ≥ s'.storage 1

/--
  Conservation when no self-fee: when folioFeeForSelf is zero, the shares
  split exactly (no burned portion), so sharesOut + daoFeeShares +
  feeRecipientFeeShares = shares.
-/
def conservation_no_self_fee_spec
    (shares : Uint256) (_s s' : ContractState) : Prop :=
  add (add (s'.storage 0) (s'.storage 1)) (s'.storage 2) = shares

end Benchmark.Cases.Reserve.FolioMintFees
