# Spec review

Plain-English mapping:
- `deposit_sets_pool_balance_spec`: depositing increases tracked pool ETH by exactly the deposited amount.
- `deposit_sets_sender_credit_spec`: depositing mints matching withdrawable credit for the caller.
- `flashLoanViaDeposit_preserves_pool_balance_spec`: the flash-loan-plus-deposit exploit path leaves pool ETH unchanged.
- `exploit_trace_drains_pool_spec`: if the attacker starts with zero credit, then borrowing and repaying through deposit followed by withdraw reduces pool ETH by exactly the borrowed amount.

Why this matches the intended property:
- The real challenge bug comes from using the same accounting path for ordinary deposits and flash-loan repayment.
- The benchmark keeps only the storage needed to expose that mismatch: assets stay flat during the flash-loan step while liabilities rise and can later be withdrawn.

Known uncertainties:
- The benchmark summarizes the callback as one atomic step rather than modeling nested external calls.
- It omits per-user ETH balances and any liveness assumptions beyond successful execution.
