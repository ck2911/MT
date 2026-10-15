# First-Stage Screen

This screen asks whether ECB policy-news shocks are strong enough to instrument monthly bridge variables. It is a relevance check, not a response result.

## Decision

No bridge passes the full stability screen. The least weak fragile candidate is `d_dfr_eop` with `target_factor_monthly_easing` (F=17.07).

ECB asset stocks remain useful liquidity responses. They are not selected as the main treatment just because the older quarterly design used them.

## Available Candidate Winners

| target | target_family | instrument | observations | first_stage_f_stat | partial_r_squared | rolling_sign_stability | jackknife_f_ratio | final_screen |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| d_dfr_eop | policy-rate bridge | target_factor_monthly_easing | 246 | 17.072 | 0.066 | 1.000 | 0.313 | fragile_candidate |
| d_ln_ecb_assets_ea_mavg | liquidity stock | timing_factor_monthly_easing | 244 | 10.991 | 0.044 | 0.454 | 0.826 | fragile_candidate |
| d_dfr_mavg | policy-rate bridge | fg_factor_monthly_easing | 244 | 9.427 | 0.038 | 0.989 | 0.139 | fragile_candidate |
| d_ln_ecb_assets_ea_stock | liquidity stock | timing_factor_monthly_easing | 244 | 7.049 | 0.029 | 0.730 | 0.923 | fragile_candidate |
| d_ln_hh_loans_ea_stock | credit response | target_factor_monthly_easing | 246 | 3.018 | 0.012 | 0.968 | 1.051 | reject_weak_relevance |
| d_ln_nfc_loans_ea_stock | credit response | qe_factor_monthly_easing | 142 | 2.499 | 0.018 | 1.000 | 0.462 | reject_weak_relevance |
| d_ln_retail_de_chained_index | purchasing-power proxy | qe_factor_monthly_easing | 142 | 1.315 | 0.010 | 1.000 | 1.277 | reject_weak_relevance |
| d_ln_dax_real_de | macro-financial response | weighted_composite_monthly_easing | 246 | 0.711 | 0.003 | 0.369 | 0.002 | reject_weak_relevance |
| d_wx_shadow_rate | policy-rate bridge | weighted_composite_monthly_easing | 208 | 0.456 | 0.002 | 0.940 | 1.309 | reject_weak_relevance |

## Requested Candidates Not Locally Available

| requested_candidate | status | note |
| --- | --- | --- |
| 2Y Bund yield | not present in raw or processed local data | do not proxy mechanically with DFR |
| ESTR / EONIA | not present in raw or processed local data | DFR is only an administered-rate proxy |
| term spread | not present in raw or processed local data | requires yield-curve source before inclusion |
| sovereign spread | not present in raw or processed local data | requires sovereign-yield source before inclusion |
| excess liquidity | not present as official series | ECB assets are retained only as a liquidity-stock proxy |
| liquidity spreads | not present in raw or processed local data | requires money-market spread source before inclusion |

## Policy-Rate Bridge Leaders

| target | instrument | observations | first_stage_f_stat | partial_r_squared | coefficient | sign | rolling_sign_stability | final_screen |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| d_dfr_eop | target_factor_monthly_easing | 246 | 17.072 | 0.066 | -0.014 | negative | 1.000 | fragile_candidate |
| d_dfr_mavg | fg_factor_monthly_easing | 244 | 9.427 | 0.038 | 0.004 | positive | 0.989 | fragile_candidate |
| d_dfr_eop | qe_factor_monthly_easing | 142 | 5.733 | 0.040 | 0.010 | positive | 1.000 | fragile_candidate |
| d_dfr_mavg | target_factor_monthly_easing | 246 | 2.458 | 0.010 | -0.003 | negative | 0.561 | reject_weak_relevance |
| d_dfr_eop | timing_factor_monthly_easing | 244 | 1.382 | 0.006 | 0.005 | positive | 0.408 | reject_weak_relevance |
| d_dfr_mavg | weighted_composite_monthly_easing | 246 | 0.586 | 0.002 | 0.007 | positive | 0.743 | reject_weak_relevance |
| d_dfr_mavg | qe_factor_monthly_easing | 142 | 0.525 | 0.004 | 0.002 | positive | 0.988 | reject_weak_relevance |
| d_wx_shadow_rate | weighted_composite_monthly_easing | 208 | 0.456 | 0.002 | -0.030 | negative | 0.940 | reject_weak_relevance |
| d_wx_shadow_rate | qe_factor_monthly_easing | 104 | 0.329 | 0.003 | -0.009 | negative | 0.911 | reject_weak_relevance |
| d_wx_shadow_rate | fg_factor_monthly_easing | 206 | 0.297 | 0.001 | -0.004 | negative | 0.735 | reject_weak_relevance |

## Liquidity-Stock Leaders

| target | instrument | observations | first_stage_f_stat | partial_r_squared | coefficient | sign | rolling_sign_stability | final_screen |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| d_ln_ecb_assets_ea_mavg | timing_factor_monthly_easing | 244 | 10.991 | 0.044 | 0.003 | positive | 0.454 | fragile_candidate |
| d_ln_ecb_assets_ea_stock | timing_factor_monthly_easing | 244 | 7.049 | 0.029 | 0.003 | positive | 0.730 | fragile_candidate |
| d_ln_ecb_assets_ea_mavg | target_factor_monthly_easing | 246 | 4.424 | 0.018 | -0.002 | negative | 1.000 | reject_weak_relevance |
| d_ln_ecb_assets_ea_stock | qe_factor_monthly_easing | 142 | 2.063 | 0.015 | -0.001 | negative | 0.916 | reject_weak_relevance |
| d_ln_ecb_assets_ea_stock | target_factor_monthly_easing | 246 | 1.176 | 0.005 | -0.001 | negative | 0.802 | reject_weak_relevance |
| d_ln_ecb_assets_ea_mavg | weighted_composite_monthly_easing | 246 | 0.909 | 0.004 | 0.003 | positive | 0.503 | reject_weak_relevance |
| d_ln_ecb_assets_ea_mavg | qe_factor_monthly_easing | 142 | 0.789 | 0.006 | 0.001 | positive | 0.892 | reject_weak_relevance |
| d_ln_ecb_assets_ea_stock | weighted_composite_monthly_easing | 246 | 0.250 | 0.001 | 0.002 | positive | 0.401 | reject_weak_relevance |
| d_ln_ecb_assets_ea_stock | fg_factor_monthly_easing | 244 | 0.047 | 0.000 | -0.000 | negative | 0.465 | reject_weak_relevance |
| d_ln_ecb_assets_ea_mavg | fg_factor_monthly_easing | 244 | 0.005 | 0.000 | 0.000 | positive | 0.514 | reject_weak_relevance |

## Transmission-Response Leaders

| target | target_family | instrument | observations | first_stage_f_stat | partial_r_squared | coefficient | sign | rolling_sign_stability | final_screen |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| d_ln_hh_loans_ea_stock | credit response | target_factor_monthly_easing | 246 | 3.018 | 0.012 | 0.000 | positive | 0.968 | reject_weak_relevance |
| d_ln_nfc_loans_ea_stock | credit response | qe_factor_monthly_easing | 142 | 2.499 | 0.018 | 0.000 | positive | 1.000 | reject_weak_relevance |
| d_ln_hh_loans_ea_stock | credit response | fg_factor_monthly_easing | 244 | 2.382 | 0.010 | -0.000 | negative | 0.751 | reject_weak_relevance |
| d_ln_retail_de_chained_index | purchasing-power proxy | qe_factor_monthly_easing | 142 | 1.315 | 0.010 | -0.001 | negative | 1.000 | reject_weak_relevance |
| d_ln_hh_loans_ea_stock | credit response | qe_factor_monthly_easing | 142 | 0.990 | 0.007 | -0.000 | negative | 0.843 | reject_weak_relevance |
| d_ln_nfc_loans_ea_stock | credit response | weighted_composite_monthly_easing | 246 | 0.950 | 0.004 | 0.001 | positive | 0.727 | reject_weak_relevance |
| d_ln_dax_real_de | macro-financial response | weighted_composite_monthly_easing | 246 | 0.711 | 0.003 | -0.005 | negative | 0.369 | reject_weak_relevance |
| d_ln_dax_real_de | macro-financial response | timing_factor_monthly_easing | 244 | 0.657 | 0.003 | -0.001 | negative | 0.692 | reject_weak_relevance |
| d_ln_dax_real_de | macro-financial response | qe_factor_monthly_easing | 142 | 0.462 | 0.003 | 0.001 | positive | 0.217 | reject_weak_relevance |
| d_ln_nfc_loans_ea_stock | credit response | fg_factor_monthly_easing | 244 | 0.339 | 0.001 | 0.000 | positive | 0.627 | reject_weak_relevance |

## Reading Rules

- `candidate`: F >= 10 and no stability screen failure.
- `fragile_candidate`: F >= 5 but below the main relevance gate or stability is thin.
- `reject_weak_relevance`: F < 5.
- Rolling relevance uses 60-month windows.
- Event sensitivity drops the five largest absolute instrument months and recomputes the first stage.

## Interpretation

If no bridge variable remains strong after stability and event-sensitivity checks, the thesis should use monthly reduced-form local projections and treat the high-frequency surprises as policy-news shocks rather than forcing a structural IV claim.
