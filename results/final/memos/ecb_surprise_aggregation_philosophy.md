# ECB Surprise Aggregation

This note explains how event surprises are aggregated before response estimation.

## Main Rule

The main aggregation is the market-magnitude weighted quarterly sum of the ABGMR `target` factor:

`target_factor_market_magnitude_weighted_quarterly_sum`.

The reason is theoretical: high-frequency ECB surprises are flow/news shocks. If more than one Governing Council event occurs in a quarter, the quarterly economy receives multiple pieces of monetary-policy information. Summing preserves that cumulative information arrival, while averaging would shrink quarters with several events merely because the ECB met more often.

## Check Exports

The code also exports check transformations for every factor:

- `quarterly_mean`: scale robustness that checks whether results depend on meeting-count intensity.
- `absolute_sum`: intensity-only robustness that ignores the easing/tightening sign and measures shock magnitude.
- `signed_cumulative`: final within-quarter cumulative signed surprise after sorting events by date. At a quarterly endpoint this equals the signed quarterly sum, but it is exported separately to make the cumulative-news interpretation clear.

## Main And Check Roles

The main external instrument is:

```text
target_factor_market_magnitude_weighted_quarterly_sum
```

The `timing_factor`, `fg_factor`, and `qe_factor` series are kept for decomposition and transmission checks. They are not intended to enter the main LP-IV simultaneously.

The lightweight Jarocinski-Karadi-style screen uses signs of `OIS_6M` and `STOXX50` from the EA-MPD monetary-event window. It informs interpretation but does not replace the main instrument.
