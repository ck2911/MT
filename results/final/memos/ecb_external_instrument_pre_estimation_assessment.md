# ECB External-Instrument Pre-Estimation Note

This note closes the external-instrument preparation stage. It does not estimate response paths or write thesis conclusions.

## Source and Coverage

- Working factor vintage: ABGMR `2025-10-30`.
- Event coverage after cleaning: 244 event rows from 2002-01-03 to 2025-10-30.
- Quarterly export coverage: 96 quarters, with 0 no-event quarters.
- ECB EA-MPD coverage gap: `2008-10-08,2008-11-06`.
- Post-2014 QE factor coverage: 100.0%.
- PEPP emergency 2020-03-18 in source event list: `review`. This is flagged because EA-MPD/ABGMR factors do not necessarily include every unscheduled emergency announcement.

## 1. Is the instrument strong enough?

Source check for the timing-factor first stage, using `timing_factor_quarterly_sum`:

- Wu-Xia shadow-rate change: F=0.02, partial R2=0.000, coef=0.0029, p=0.894, weak_instrument_warning_below_rule_of_thumb_10
- ECB asset log growth: F=1.26, partial R2=0.015, coef=-0.0027, p=0.265, weak_instrument_warning_below_rule_of_thumb_10
- DFR change: F=0.08, partial R2=0.001, coef=0.0034, p=0.784, weak_instrument_warning_below_rule_of_thumb_10

Current LP-IV instrument: `target_factor_market_magnitude_weighted_quarterly_sum` against `d_ecb_assets_ea_qavg`. The timing-factor rows above are source checks only.

## 2. Is quarterly aggregation defensible?

Yes, the `quarterly_sum` rule is defensible for the thesis design. ECB surprises are high-frequency news-flow shocks. Multiple meetings in a quarter represent cumulative policy-information arrivals, so summing is the most natural quarterly mapping. The code also exports `quarterly_mean`, `absolute_sum`, and `signed_cumulative` variants to test whether conclusions depend on meeting density, sign, or cumulative-news treatment.

## 3. Does identification depend excessively on crisis periods?

For the timing factor, crisis regimes account for 49.5% of total absolute quarterly surprise mass. The top decile of absolute timing surprises accounts for 42.1% of total absolute mass. Outlier quarters with |z| >= 3: `2006Q2,2008Q2,2009Q3,2011Q3`.

This means crisis leverage must be reported explicitly. Regime concentration, rolling variance, and quarter-density checks are reviewed before estimation.

## 4. Is the main instrument stable across QE, COVID, and tightening?

The source covers the QE era, COVID period, and 2022 tightening transition. QE factors are populated after 2014, and the 2022H2 tightening events are present. The COVID emergency-announcement check is cautious because the PEPP emergency date is not present in the ABGMR factor event list.

The lightweight JK-style sign screen is preserved as an interpretation layer. It flags potential central-bank information events from rate/equity comovement but is not used as the main identification source.

## 5. Final pre-estimation recommendation

- LP-IV instrument: `target_factor_market_magnitude_weighted_quarterly_sum`.
- Checks: weighted shocks, signed cumulative variants, quarterly means, and monthly bridge variants.
- Excluded from the main design: simultaneous multi-factor instruments, full Jarocinski-Karadi replication, and DAX as a main response.

Next step: response estimation with first-stage, rolling, regime, horizon, and weak-IV checks.
