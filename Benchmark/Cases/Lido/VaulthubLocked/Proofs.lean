import Benchmark.Cases.Lido.VaulthubLocked.Specs

namespace Benchmark.Cases.Lido.VaulthubLocked

open Verity.EVM.Uint256

/-
  Reference proofs for the Lido VaultHub _locked() solvency properties.

  The F-01 proof proceeds by case split on whether the reserve-ratio-based
  reserve dominates the minimal reserve:

  Case 1 (reserve >= minimalReserve):
    locked = liability_max + ceil(liability_max * RR / (BP - RR))
    locked * (BP-RR) = liability_max*(BP-RR) + ceil(liability_max*RR/(BP-RR))*(BP-RR)
                     >= liability_max*(BP-RR) + liability_max*RR   [ceilDiv sandwich]
                     = liability_max * BP
                     >= liability * BP                              [monotonicity, maxLS >= LS]

  Case 2 (minimalReserve > reserve):
    locked = liability_max + minimalReserve
    Need: (liability_max + minReserve) * (BP-RR) >= liability * BP
    Since minReserve > ceil(liability_max * RR / (BP-RR)) >= liability_max * RR / (BP-RR):
      minReserve * (BP-RR) > liability_max * RR
    So: locked * (BP-RR) = liability_max*(BP-RR) + minReserve*(BP-RR)
                         > liability_max*(BP-RR) + liability_max*RR
                         = liability_max * BP >= liability * BP
-/

/--
  Supporting lemma: ceilDiv sandwich bound.
-/
theorem ceildiv_sandwich
    (x d : Uint256)
    (hd : d > 0) :
    ceildiv_sandwich_spec x d := by
  unfold ceildiv_sandwich_spec
  intro _
  sorry

/--
  Supporting lemma: share conversion monotonicity.
-/
theorem shares_conversion_monotone
    (a b : Uint256)
    (totalPooledEther totalShares : Uint256)
    (hTS : totalShares > 0) :
    shares_conversion_monotone_spec a b totalPooledEther totalShares := by
  unfold shares_conversion_monotone_spec
  intro _
  sorry

/--
  P-VH-04: maxLiabilityShares >= liabilityShares.
  In the real contract this is maintained by the minting and reporting logic.
  Here we state it as a theorem to be proven from the contract invariants.
-/
theorem max_liability_shares_bound
    (maxLiabilityShares liabilityShares : Uint256)
    (hBound : maxLiabilityShares ≥ liabilityShares) :
    max_liability_shares_bound_spec maxLiabilityShares liabilityShares := by
  unfold max_liability_shares_bound_spec
  exact hBound

/--
  P-VH-03: Reserve ratio is within valid bounds.
-/
theorem reserve_ratio_bounds
    (reserveRatioBP : Uint256)
    (hPos : reserveRatioBP > 0)
    (hLt : reserveRatioBP < TOTAL_BASIS_POINTS) :
    reserve_ratio_bounds_spec reserveRatioBP := by
  unfold reserve_ratio_bounds_spec
  exact ⟨hPos, hLt⟩

/--
  F-01: Locked funds solvency.
  The locked amount multiplied by the reserve ratio complement is at least
  the liability multiplied by total basis points.
-/
theorem locked_funds_solvency
    (maxLiabilityShares liabilityShares : Uint256)
    (minimalReserve reserveRatioBP : Uint256)
    (totalPooledEther totalShares : Uint256)
    -- Axioms
    (hMaxLS : maxLiabilityShares ≥ liabilityShares)
    (hRR_pos : reserveRatioBP > 0)
    (hRR_lt : reserveRatioBP < TOTAL_BASIS_POINTS)
    (hTS : totalShares > 0)
    (hTPE : totalPooledEther > 0)
    -- No overflow: maxLiabilityShares * totalPooledEther fits in Uint256
    (hNoOverflow1 : maxLiabilityShares.val * totalPooledEther.val < modulus)
    -- No overflow: liability * reserveRatioBP fits in Uint256
    (hNoOverflow2 : (getPooledEthBySharesRoundUp maxLiabilityShares totalPooledEther totalShares).val
                    * reserveRatioBP.val < modulus)
    -- No overflow: locked * (BP - RR) fits in Uint256
    (hNoOverflow3 : (locked maxLiabilityShares minimalReserve reserveRatioBP totalPooledEther totalShares).val
                    * (sub TOTAL_BASIS_POINTS reserveRatioBP).val < modulus)
    -- No overflow: liability * BP fits in Uint256
    (hNoOverflow4 : (getPooledEthBySharesRoundUp liabilityShares totalPooledEther totalShares).val
                    * TOTAL_BASIS_POINTS.val < modulus) :
    locked_funds_solvency_spec maxLiabilityShares liabilityShares minimalReserve reserveRatioBP
      totalPooledEther totalShares := by
  unfold locked_funds_solvency_spec locked getPooledEthBySharesRoundUp
  sorry

end Benchmark.Cases.Lido.VaulthubLocked
