# Regime Identification Stability

Regime-specific checks split the sample into pre-QE, QE, COVID, and tightening windows. Small-regime first stages are screening evidence, not structural estimates.

## Regime First-Stage Leaders

| instrument | factor | aggregation | target_equation | regime | F_stat | partial_R2 | observations | sign_stability |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| target_factor_quarterly_abs_sum | target | quarterly_abs_sum | d_dfr_eop | qe_era | 45.796 | 0.686 | 23 | unstable_or_unavailable |
| target_factor_monthly_abs_sum | target | monthly_abs_sum | d_dfr_eop | qe_era | 45.796 | 0.686 | 23 | unstable_or_unavailable |
| qe_factor_monthly_abs_sum | qe | monthly_abs_sum | d_ln_hh_loans_ea_stock | tightening | 23.345 | 0.642 | 15 | stable |
| qe_factor_monthly_mean | qe | monthly_mean | d_dfr_eop | tightening | 22.816 | 0.637 | 15 | stable |
| qe_factor_monthly_sum | qe | monthly_sum | d_dfr_eop | tightening | 22.816 | 0.637 | 15 | stable |
| qe_factor_quarterly_sum | qe | quarterly_sum | d_dfr_eop | tightening | 22.304 | 0.614 | 16 | stable |
| qe_factor_quarterly_signed_cumulative | qe | quarterly_signed_cumulative | d_dfr_eop | tightening | 22.304 | 0.614 | 16 | stable |
| qe_factor_crisis_weighted_quarterly_sum | qe | crisis_weighted | d_dfr_eop | tightening | 22.304 | 0.614 | 16 | stable |
| qe_factor_quarterly_mean | qe | quarterly_mean | d_dfr_eop | tightening | 19.429 | 0.581 | 16 | stable |
| qe_factor_qe_event_weighted_quarterly_sum | qe | qe_event_weighted | d_dfr_eop | tightening | 17.238 | 0.552 | 16 | stable |
| target_factor_quarterly_abs_sum | target | quarterly_abs_sum | d_dfr_eop | tightening | 17.150 | 0.551 | 16 | stable |
| target_factor_monthly_abs_sum | target | monthly_abs_sum | d_dfr_eop | tightening | 16.040 | 0.552 | 15 | stable |

## Stability Summary

| instrument | factor | architecture | max_regime_F | median_regime_F | stable_sign_share | strong_regime_count |
| --- | --- | --- | --- | --- | --- | --- |
| target_factor_quarterly_abs_sum | target | direct_quarterly | 45.795970026009755 | 2.326579796503029 | 0.5 | 5 |
| target_factor_monthly_abs_sum | target | monthly_bridge_quarterly | 45.795970026009755 | 2.326579796503029 | 0.4642857142857143 | 4 |
| qe_factor_monthly_abs_sum | qe | monthly_bridge_quarterly | 23.344990078736163 | 0.23128365693573766 | 0.2857142857142857 | 1 |
| qe_factor_monthly_sum | qe | monthly_bridge_quarterly | 22.81641610051038 | 0.8502306182594933 | 0.39285714285714285 | 1 |
| qe_factor_monthly_mean | qe | monthly_bridge_quarterly | 22.81641610051038 | 0.9943793343261959 | 0.35714285714285715 | 1 |
| qe_factor_quarterly_signed_cumulative | qe | direct_quarterly | 22.303543500699735 | 0.9295647417220152 | 0.39285714285714285 | 1 |
| qe_factor_quarterly_sum | qe | direct_quarterly | 22.303543500699735 | 0.9295647417220152 | 0.39285714285714285 | 1 |
| qe_factor_crisis_weighted_quarterly_sum | qe | weighted_event_quarterly | 22.30354350069973 | 0.9295647417220152 | 0.39285714285714285 | 1 |
| qe_factor_quarterly_mean | qe | direct_quarterly | 19.42866110426934 | 1.0421524762468388 | 0.32142857142857145 | 1 |
| qe_factor_qe_event_weighted_quarterly_sum | qe | weighted_event_quarterly | 17.238001632768825 | 1.1265675937807884 | 0.39285714285714285 | 1 |
| qe_factor_quarterly_abs_sum | qe | direct_quarterly | 15.246009745888431 | 0.23128365693573766 | 0.2857142857142857 | 1 |
| qe_factor_market_magnitude_weighted_quarterly_sum | qe | weighted_event_quarterly | 14.048761111220484 | 1.159538917349792 | 0.39285714285714285 | 1 |

## Reading Rule

An instrument that is strong only in one short regime is not automatically a main instrument. It is a candidate for regime-restricted checks.
