# Shock Weighting

The weighting layer tests whether equal event weighting weakens relevance.

## Schemes

- Market-magnitude weighting: each event shock is multiplied by its absolute surprise size relative to the factor's mean absolute event surprise.
- Crisis weighting: GFC, sovereign-crisis, COVID, and tightening-regime events receive a 1.5 multiplier.
- QE-event weighting: events with larger QE surprises receive larger weights, applied across factor families to test balance-sheet-signal concentration.

## First-Stage Leaders

| instrument | target_equation | sample | F_stat | partial_R2 | coef | p_value |
| --- | --- | --- | --- | --- | --- | --- |
| qe_factor_crisis_weighted_quarterly_sum | d_dfr_eop | robustness_2005q1_2025q4 | 13.776 | 0.230 | -0.033 | 0.001 |
| target_factor_market_magnitude_weighted_quarterly_sum | d_dfr_eop | robustness_2005q1_2025q4 | 13.197 | 0.140 | 0.003 | 0.000 |
| target_factor_market_magnitude_weighted_quarterly_sum | d_ecb_assets_ea_qavg | robustness_2005q1_2025q4 | 11.075 | 0.120 | -1797.286 | 0.001 |
| target_factor_crisis_weighted_quarterly_sum | d_dfr_eop | robustness_2005q1_2025q4 | 8.025 | 0.090 | 0.020 | 0.006 |
| target_factor_qe_event_weighted_quarterly_sum | d_dfr_eop | robustness_2005q1_2025q4 | 8.024 | 0.090 | 0.013 | 0.006 |
| qe_factor_qe_event_weighted_quarterly_sum | d_dfr_eop | robustness_2005q1_2025q4 | 6.259 | 0.120 | -0.008 | 0.016 |
| qe_factor_crisis_weighted_quarterly_sum | d_ln_nfc_loans_ea_stock | robustness_2005q1_2025q4 | 5.597 | 0.108 | -0.001 | 0.022 |
| qe_factor_market_magnitude_weighted_quarterly_sum | d_dfr_eop | robustness_2005q1_2025q4 | 5.212 | 0.102 | -0.009 | 0.027 |
| target_factor_market_magnitude_weighted_quarterly_sum | d_ln_house_price_de_real | robustness_2005q1_2025q4 | 4.232 | 0.050 | -0.000 | 0.043 |
| timing_factor_market_magnitude_weighted_quarterly_sum | d_ln_ecb_assets_ea_stock | robustness_2005q1_2025q4 | 3.144 | 0.037 | -0.001 | 0.080 |
| target_factor_crisis_weighted_quarterly_sum | d_ecb_assets_ea_qavg | robustness_2005q1_2025q4 | 2.998 | 0.036 | -8034.309 | 0.087 |
| qe_factor_qe_event_weighted_quarterly_sum | d_ln_nfc_loans_ea_stock | robustness_2005q1_2025q4 | 2.844 | 0.058 | -0.000 | 0.098 |

## Interpretation

Weighted variants are not automatically preferred. They must improve relevance without making identification depend mechanically on crisis leverage or QE-only events.
