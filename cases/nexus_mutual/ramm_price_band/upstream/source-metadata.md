# Upstream metadata

- Repository: https://github.com/NexusMutual/smart-contracts
- Commit: `ad212043a78953a2cd98cd02b06c8e3e354c6023`
- Contract path: `contracts/modules/capital/Ramm.sol`
- Functions of interest: `calculateNxm`, `_getReserves`, `getSpotPrices`, `getBookValue`
- Source language: Solidity

Reason for selection:
- real production pricing logic with explicit buffered relation to book value
- clean arithmetic invariants that can seed proof tasks over a live protocol artifact
