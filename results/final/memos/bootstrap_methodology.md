# Bootstrap Methodology

The response tables keep HAC/Newey-West intervals and add dependence-aware bootstrap checks. The bootstrap changes uncertainty assessment, not the estimand.

## Methods

- Moving-block bootstrap: residual vectors are resampled in adjacent time blocks using a common draw across horizons for each response.
- Wild bootstrap: residual vectors are multiplied by common Rademacher shocks across horizons, preserving heteroskedasticity-sensitive cross-horizon comovement.
- Automatic block length: `max(6, round(n^(1/3)), min(12, max_horizon / 2))`; sensitivity checks report block lengths 4, 6, 9, 12, and automatic.
- Cumulative intervals: cumulative draws sum bootstrapped horizon coefficients from the same resample path, so horizon dependence is carried into the percentile envelope.

## Horizon Dependence Diagnostics

| response_label | channel | nobs_common_horizon_sample | mean_adjacent_horizon_residual_corr | max_abs_horizon_residual_corr |
| --- | --- | --- | --- | --- |
| ECB assets | financial_liquidity | 222 | 0.7745 | 0.8172 |
| real DAX | financial_market | 222 | 0.6472 | 0.7196 |
| mortgage lending spread | banking_lending_conditions | 222 | 0.7265 | 0.8149 |
| NFC lending spread | banking_lending_conditions | 222 | 0.6534 | 0.6979 |
| NFC credit | financial_credit | 222 | 0.8222 | 0.8668 |
| house-purchase lending growth | housing_finance | 222 | 0.7614 | 0.8621 |
| pure new house-purchase loans | housing_finance | 73 | 0.4310 | 0.5629 |
| real wage tracker excl. one-offs | compensation_proxy | 128 | 0.6856 | 0.8228 |
| German industry real wage bill growth | compensation_proxy | 211 | 0.4069 | 0.5212 |
| employment expectations | labor_tightness | 222 | 0.5448 | 0.7504 |

## Block-Length Sensitivity Preview

| response_label | horizon_months | block_length_setting | interval_width_90 | bootstrap_replications |
| --- | --- | --- | --- | --- |
| ECB assets | 6 | 4 | 0.0207 | 199 |
| ECB assets | 12 | 4 | 0.0306 | 199 |
| ECB assets | 24 | 4 | 0.0402 | 199 |
| ECB assets | 6 | 6 | 0.0219 | 199 |
| ECB assets | 12 | 6 | 0.0345 | 199 |
| ECB assets | 24 | 6 | 0.0451 | 199 |
| ECB assets | 6 | 9 | 0.0219 | 199 |
| ECB assets | 12 | 9 | 0.0326 | 199 |
| ECB assets | 24 | 9 | 0.0461 | 199 |
| ECB assets | 6 | 12 | 0.0223 | 199 |
| ECB assets | 12 | 12 | 0.0349 | 199 |
| ECB assets | 24 | 12 | 0.0460 | 199 |
| ECB assets | 6 | auto | 0.0223 | 199 |
| ECB assets | 12 | auto | 0.0349 | 199 |
| ECB assets | 24 | auto | 0.0460 | 199 |
| real DAX | 6 | 4 | 0.0231 | 199 |
| real DAX | 12 | 4 | 0.0315 | 199 |
| real DAX | 24 | 4 | 0.0363 | 199 |
| real DAX | 6 | 6 | 0.0233 | 199 |
| real DAX | 12 | 6 | 0.0318 | 199 |
| real DAX | 24 | 6 | 0.0360 | 199 |
| real DAX | 6 | 9 | 0.0232 | 199 |
| real DAX | 12 | 9 | 0.0310 | 199 |
| real DAX | 24 | 9 | 0.0343 | 199 |
| real DAX | 6 | 12 | 0.0211 | 199 |
| real DAX | 12 | 12 | 0.0269 | 199 |
| real DAX | 24 | 12 | 0.0363 | 199 |
| real DAX | 6 | auto | 0.0211 | 199 |
| real DAX | 12 | auto | 0.0269 | 199 |
| real DAX | 24 | auto | 0.0363 | 199 |

## Interpretation

Bootstrap ribbons and fan charts show sampling uncertainty under serial dependence, overlapping horizons, and small monthly samples. They support the persistence comparison but do not create new structural estimates.
