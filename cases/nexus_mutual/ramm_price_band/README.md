# ramm_price_band

Source:
- `NexusMutual/smart-contracts`
- commit `ad212043a78953a2cd98cd02b06c8e3e354c6023`
- file `contracts/modules/capital/Ramm.sol`

Focus:
- `calculateNxm`
- `_getReserves`
- `getSpotPrices`
- `getBookValue`
- 1% price band around book value

Out of scope:
- reserve flow dynamics
- time ratchets
- TWAP
- swaps and circuit breakers
