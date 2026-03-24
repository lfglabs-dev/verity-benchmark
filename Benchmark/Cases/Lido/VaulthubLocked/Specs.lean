import Benchmark.Cases.Lido.VaulthubLocked.Contract

namespace Benchmark.Cases.Lido.VaulthubLocked

open Verity.EVM.Uint256

/-
  Specifications for the Lido VaultHub _locked() solvency properties.
  These correspond to findings and proven properties from the Certora
  formal verification report (December 2025).

  F-01 (Certora finding): The locked amount is sufficient to cover the vault's
  liability at the protocol level, i.e.:
    locked(maxLS, minRes, RR) * (BP - RR) >= getPooledEthBySharesRoundUp(LS) * BP

  P-VH-04 (Certora proven): maxLiabilityShares >= liabilityShares
  P-VH-03 (Certora proven): 0 < reserveRatioBP < TOTAL_BASIS_POINTS
-/

/--
  F-01: Locked funds solvency.
  The amount locked on a vault, multiplied by the complement of the reserve ratio,
  is at least as large as the liability (for the current liability shares) multiplied
  by the full basis points.

  This ensures that the vault always locks enough collateral to cover its
  stETH obligations with the required reserve buffer.

  In symbols (all in Uint256 arithmetic):
    locked(maxLS, minRes, RR, TPE, TS) * (BP - RR)
      >= getPooledEthBySharesRoundUp(LS, TPE, TS) * BP

  where maxLS >= LS (P-VH-04) and 0 < RR < BP (P-VH-03).
-/
def locked_funds_solvency_spec
    (maxLiabilityShares liabilityShares : Uint256)
    (minimalReserve reserveRatioBP : Uint256)
    (totalPooledEther totalShares : Uint256) : Prop :=
  let lockedAmount := locked maxLiabilityShares minimalReserve reserveRatioBP totalPooledEther totalShares
  let liability := getPooledEthBySharesRoundUp liabilityShares totalPooledEther totalShares
  let complement := sub TOTAL_BASIS_POINTS reserveRatioBP
  mul lockedAmount complement ≥ mul liability TOTAL_BASIS_POINTS

/--
  P-VH-04 (Certora proven): maxLiabilityShares is an upper bound on liabilityShares.
  This invariant is maintained by the VaultHub's minting and reporting logic.
  In the benchmark we prove it as a standalone lemma to confirm the Certora result.
-/
def max_liability_shares_bound_spec
    (maxLiabilityShares liabilityShares : Uint256) : Prop :=
  maxLiabilityShares ≥ liabilityShares

/--
  P-VH-03 (Certora proven): Reserve ratio is strictly between 0 and TOTAL_BASIS_POINTS.
  This is enforced by the vault connection validation logic.
-/
def reserve_ratio_bounds_spec
    (reserveRatioBP : Uint256) : Prop :=
  reserveRatioBP > 0 ∧ reserveRatioBP < TOTAL_BASIS_POINTS

/--
  Supporting lemma: ceilDiv sandwich bound.
  For any x and d > 0: ceilDiv(x, d) * d >= x.
  This is a key arithmetic fact used in the F-01 proof.
-/
def ceildiv_sandwich_spec
    (x d : Uint256) : Prop :=
  d > 0 → mul (ceilDiv x d) d ≥ x

/--
  Supporting lemma: getPooledEthBySharesRoundUp is monotone in shares.
  If a >= b then getPooledEthBySharesRoundUp(a) >= getPooledEthBySharesRoundUp(b).
  This relies on ceilDiv monotonicity.
-/
def shares_conversion_monotone_spec
    (a b : Uint256)
    (totalPooledEther totalShares : Uint256) : Prop :=
  a ≥ b →
  getPooledEthBySharesRoundUp a totalPooledEther totalShares ≥
  getPooledEthBySharesRoundUp b totalPooledEther totalShares

end Benchmark.Cases.Lido.VaulthubLocked
