# Spec review

Plain-English mapping:
- `buy_price_not_below_book_value_spec`: the buy-side quote never drops below book value after integer truncation.
- `sell_price_below_book_value_buffer_spec`: the sell-side quote stays at or below BV - 1%.
- `sell_price_below_buy_price_spec`: the quoted sell price does not cross above the quoted buy price.

Why this matches the intended property:
- The upstream RAMM code hard-codes a 1 percent buffer around book value through `PRICE_BUFFER`, but the buy side is floored by integer division.
- These specs isolate the benchmarkable arithmetic relation without pretending to model all reserve dynamics.

Known uncertainties:
- The benchmark slice abstracts reserve evolution to a synchronized price-band update.
- It does not yet model the ratchet branch conditions or TWAP oracle state.
