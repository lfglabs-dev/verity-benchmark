# Upstream metadata

- Repository: https://github.com/reserve-protocol/reserve-index-dtf
- Contract path: `contracts/utils/FolioLib.sol`
- Functions of interest: `computeMintFees`
- Source language: Solidity 0.8.28

Reason for selection:
- real production fee-split arithmetic with DAO floor enforcement and self-fee burn
- interesting ceiling-division rounding interactions across multiple max() operations
- clear conservation invariant testable without transcendental math dependencies
