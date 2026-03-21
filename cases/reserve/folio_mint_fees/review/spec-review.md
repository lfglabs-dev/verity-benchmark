# Spec review

Plain-English mapping:
- `no_value_creation_spec`: the sum of all distributed shares (receiver + DAO + fee recipients) never exceeds the original mint amount. The gap is folioSelfShares burned.
- `dao_floor_enforced_spec`: the DAO always receives at least ceil(shares * max(daoFeeFloor, 0.03%) / 1e18), regardless of the configured mintFee.
- `minter_pays_at_least_dao_spec`: the total fee deducted from the minter is at least the DAO's portion (totalFeeShares >= daoFeeShares).
- `conservation_no_self_fee_spec`: when folioFeeForSelf is zero, the three-way split is exact with no burned remainder.

Why this matches the intended property:
- The Solidity code enforces a DAO fee floor via max(daoFeeFloor, MIN_MINT_FEE) and then bumps totalFeeShares upward if necessary.
- These specs isolate the arithmetic invariants of the fee split without modeling the DAO registry or ERC20 transfers.

Known uncertainties:
- The benchmark slice abstracts the DAO fee registry as direct parameters.
- It does not model the subsequent share minting or token transfer steps.
- The folioSelfShares burn is implicit (difference between shares and the three outputs).
