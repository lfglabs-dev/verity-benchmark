import Benchmark.Cases.Lido.VaulthubLocked.Specs

namespace Benchmark.Cases.Lido.VaulthubLocked

open Verity.EVM.Uint256

/--
Certora F-01: Locked funds solvency.
The locked amount multiplied by the reserve ratio complement is at least
the liability multiplied by total basis points:

  locked(maxLS, minRes, RR) * (BP - RR) >= getPooledEthBySharesRoundUp(LS) * BP

The proof requires a case split on whether the computed reserve or the minimal
reserve dominates, then algebraic manipulation using the ceilDiv sandwich bound
and share conversion monotonicity.
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
    -- No overflow: the add inside locked (liability + effectiveReserve) fits in Uint256
    (hNoOverflow3 : let liab := getPooledEthBySharesRoundUp maxLiabilityShares totalPooledEther totalShares
                    let reserve := ceilDiv (mul liab reserveRatioBP) (sub TOTAL_BASIS_POINTS reserveRatioBP)
                    let eff := if reserve ≥ minimalReserve then reserve else minimalReserve
                    liab.val + eff.val < modulus)
    -- No overflow: locked * (BP - RR) fits in Uint256
    (hNoOverflow4 : (locked maxLiabilityShares minimalReserve reserveRatioBP totalPooledEther totalShares).val
                    * (sub TOTAL_BASIS_POINTS reserveRatioBP).val < modulus)
    -- No overflow: liability * BP fits in Uint256
    (hNoOverflow5 : (getPooledEthBySharesRoundUp liabilityShares totalPooledEther totalShares).val
                    * TOTAL_BASIS_POINTS.val < modulus) :
    locked_funds_solvency_spec maxLiabilityShares liabilityShares minimalReserve reserveRatioBP
      totalPooledEther totalShares := by
  -- Replace this placeholder with a complete Lean proof.
  exact ?_

end Benchmark.Cases.Lido.VaulthubLocked
