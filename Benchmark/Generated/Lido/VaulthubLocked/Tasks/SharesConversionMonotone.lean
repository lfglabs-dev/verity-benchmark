import Benchmark.Cases.Lido.VaulthubLocked.Specs

namespace Benchmark.Cases.Lido.VaulthubLocked

open Verity
open Verity.EVM.Uint256

/--
Supporting arithmetic lemma: getPooledEthBySharesRoundUp is monotone in shares.
If a >= b then getPooledEthBySharesRoundUp(a) >= getPooledEthBySharesRoundUp(b).
Needed to lift the F-01 solvency bound from maxLiabilityShares to liabilityShares.
-/
theorem shares_conversion_monotone
    (a b : Uint256)
    (totalPooledEther totalShares : Uint256)
    (hTS : totalShares > 0)
    (hNoOverflow : a.val * totalPooledEther.val < modulus) :
    shares_conversion_monotone_spec a b totalPooledEther totalShares := by
  -- Replace this placeholder with a complete Lean proof.
  exact ?_

end Benchmark.Cases.Lido.VaulthubLocked
