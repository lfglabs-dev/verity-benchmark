# ramm_price_band

Selected from `NexusMutual/smart-contracts` at `ad212043a78953a2cd98cd02b06c8e3e354c6023`.

What is selected:
- Contract: `contracts/modules/capital/Ramm.sol`
- Functions: `calculateNxm`, `_getReserves`, `getSpotPrices`, `getBookValue`
- Benchmark focus: the enforced 1 percent price band around book value

Frozen specs:
- buy price is at least book value plus 1 percent
- sell price is at most book value minus 1 percent
- sell price is no greater than buy price

Intentionally left out:
- reserve injection and extraction dynamics
- time-based ratchets
- TWAP observations
- actual swap execution and circuit breakers
