# folio_mint_fees

Source:
- `reserve-protocol/reserve-index-dtf`
- file `contracts/utils/FolioLib.sol`

Focus:
- `computeMintFees`
- Fee split: receiver shares, DAO shares, fee recipient shares
- DAO fee floor enforcement (min 0.03%)
- Self-fee burn (folioFeeForSelf)

Out of scope:
- TVL fee computation (requires transcendental math)
- Auction/rebalancing logic
- ERC20 token transfers
- DAO fee registry implementation
