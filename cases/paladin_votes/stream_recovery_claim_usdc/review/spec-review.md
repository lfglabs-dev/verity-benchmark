# Spec review

Plain-English mapping:
- `claimUsdc_marks_claimed_spec`: after a successful claim, the sender is marked as claimed.
- `claimUsdc_updates_round_claimed_spec`: the round's claimed amount increases by exactly the computed payout.
- `claimUsdc_updates_total_allocated_spec`: remaining global allocated USDC decreases by that payout.
- `claimUsdc_preserves_round_bound_spec`: the post-state never exceeds the round total.

Why this matches the intended property:
- The protocol goal in scope is "cannot claim more than entitlement".
- This slice captures the local accounting guard `round.usdcClaimed + amount <= round.usdcTotal`.

Known uncertainties:
- Merkle correctness is not modeled here.
- This is a single-round specialization, not the whole contract.
- "Entitlement" is interpreted as the computed payout under an accepted proof witness.
