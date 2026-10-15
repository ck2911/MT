# QE vs Timing Identification

This note compares QE-centered ECB surprise measures with conventional timing surprises. It does not estimate response paths.

## Answer

QE provides materially stronger identification than timing for this thesis design.

Best QE first-stage F-stat across ECB asset, loan, and housing targets: `5.597`.

Best timing first-stage F-stat across the same target family: `3.144`.

## QE Candidate Leaders

| instrument | target_equation | sample | F_stat | partial_R2 | coef | p_value |
| --- | --- | --- | --- | --- | --- | --- |
| qe_factor_crisis_weighted_quarterly_sum | d_ln_nfc_loans_ea_stock | robustness_2005q1_2025q4 | 5.597 | 0.108 | -0.001 | 0.022 |
| qe_factor_quarterly_sum | d_ln_nfc_loans_ea_stock | robustness_2005q1_2025q4 | 4.250 | 0.085 | -0.001 | 0.045 |
| qe_factor_quarterly_signed_cumulative | d_ln_nfc_loans_ea_stock | robustness_2005q1_2025q4 | 4.250 | 0.085 | -0.001 | 0.045 |
| qe_factor_quarterly_mean | d_ln_nfc_loans_ea_stock | robustness_2005q1_2025q4 | 3.823 | 0.077 | -0.001 | 0.057 |
| qe_factor_monthly_mean | d_ln_nfc_loans_ea_stock | robustness_2005q1_2025q4 | 3.526 | 0.073 | -0.001 | 0.067 |
| qe_factor_qe_event_weighted_quarterly_sum | d_ln_nfc_loans_ea_stock | robustness_2005q1_2025q4 | 2.844 | 0.058 | -0.000 | 0.098 |
| qe_factor_monthly_abs_sum | d_ln_nfc_loans_ea_stock | robustness_2005q1_2025q4 | 2.491 | 0.052 | 0.001 | 0.122 |
| qe_factor_market_magnitude_weighted_quarterly_sum | d_ln_nfc_loans_ea_stock | robustness_2005q1_2025q4 | 2.313 | 0.048 | -0.000 | 0.135 |

## Timing Candidate Leaders

| instrument | target_equation | sample | F_stat | partial_R2 | coef | p_value |
| --- | --- | --- | --- | --- | --- | --- |
| timing_factor_market_magnitude_weighted_quarterly_sum | d_ln_ecb_assets_ea_stock | robustness_2005q1_2025q4 | 3.144 | 0.037 | -0.001 | 0.080 |
| timing_factor_quarterly_mean | d_ln_ecb_assets_ea_stock | robustness_2005q1_2025q4 | 1.815 | 0.022 | -0.009 | 0.182 |
| timing_factor_monthly_mean | d_ln_ecb_assets_ea_stock | robustness_2005q1_2025q4 | 1.792 | 0.022 | -0.009 | 0.184 |
| timing_factor_crisis_weighted_quarterly_sum | d_ln_ecb_assets_ea_stock | robustness_2005q1_2025q4 | 1.562 | 0.019 | -0.002 | 0.215 |
| timing_factor_quarterly_sum | d_ln_ecb_assets_ea_stock | robustness_2005q1_2025q4 | 1.260 | 0.015 | -0.003 | 0.265 |
| timing_factor_quarterly_signed_cumulative | d_ln_ecb_assets_ea_stock | robustness_2005q1_2025q4 | 1.260 | 0.015 | -0.003 | 0.265 |
| timing_factor_monthly_sum | d_ln_ecb_assets_ea_stock | robustness_2005q1_2025q4 | 1.239 | 0.015 | -0.003 | 0.269 |
| timing_factor_quarterly_sum | d_ln_hh_loans_ea_stock | robustness_2005q1_2025q4 | 1.174 | 0.014 | -0.000 | 0.282 |

## Interpretation

QE is economically natural for a balance-sheet transmission thesis, but it still has to show relevance. If QE strength appears mainly against DFR and not against ECB assets, household loans, NFC loans, or housing, it is not enough to carry the design by itself.
