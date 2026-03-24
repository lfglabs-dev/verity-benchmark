# Spec review

Plain-English mapping:
- `locked_funds_solvency_spec` (F-01): the locked collateral multiplied by the reserve ratio
  complement is at least the liability multiplied by total basis points. This ensures the vault
  always locks enough to cover its stETH obligations with the required reserve buffer.
- `max_liability_shares_bound_spec` (P-VH-04): maxLiabilityShares is always >= liabilityShares.
  Maintained by minting and reporting logic.
- `reserve_ratio_bounds_spec` (P-VH-03): reserveRatioBP is strictly between 0 and 10000.
  Enforced by vault connection validation.
- `ceildiv_sandwich_spec`: ceil(x/d) * d >= x. Key arithmetic lemma for the F-01 proof.
- `shares_conversion_monotone_spec`: getPooledEthBySharesRoundUp is monotone in shares.
  Needed to lift the inequality from maxLiabilityShares down to liabilityShares.

Why this matches the intended property:
- The F-01 inequality directly captures the solvency condition that Certora could not prove.
- The proof structure requires a case split on whether the reserve-ratio-based reserve or
  the minimal reserve dominates, followed by algebraic manipulation using the ceilDiv
  sandwich bound and share conversion monotonicity.

Known uncertainties:
- The benchmark models getPooledEthBySharesRoundUp as an axiomatised function rather than
  inlining the Lido share rate computation.
- No-overflow hypotheses are required as explicit preconditions since we operate in Uint256.
- The P-VH-04 invariant (maxLiabilityShares bound) is stated as a precondition rather than
  proven from the full state machine, matching its role as an axiom for F-01.
