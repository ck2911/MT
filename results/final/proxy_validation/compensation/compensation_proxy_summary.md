# Compensation Proxy Selection

This note explains the monthly compensation-side measures. Every retained proxy is observed monthly or is a transparent transformation of monthly data.

## Main Compensation Selection

| rank | canonical_status | variable | label | role | source | compensation_proxy_score | residual_limitation |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | secondary_robustness_compensation_proxy | eurostat_sts_industry_wage_bill_de_real_yoy | Eurostat German industry wage bill, real annual growth | robustness | Eurostat STS | 157 | Sector/geography are narrow; the series measures wage bill, not compensation per employee. |
| 3 | primary_canonical_compensation_proxy | ecb_wage_tracker_ex_oneoffs_real_yoy | ECB Wage Tracker excluding one-off payments, real | canonical | ECB EWT | 141 | It is negotiated wage pressure, not observed total compensation per employee, payroll income, welfare, or redistribution. |
| 8 | noise_control_robustness_proxy | ecb_wage_tracker_ex_oneoffs_real_yoy_ma3 | ECB Wage Tracker excluding one-offs, real 3-month average | robustness | ECB EWT + EA HICP | 114 | Smoothing is transparent and only uses observed current/past monthly data; it is not a distinct source series. |

The main compensation proxy is `ecb_wage_tracker_ex_oneoffs_real_yoy`: nominal ECB negotiated wage pressure excluding one-off payments minus HICP inflation. It is selected because it is the most interpretable monthly wage-pressure measure for persistent compensation dynamics, even when the mechanical scorecard ranks the narrower German industry wage-bill proxy higher on shock sensitivity.

The secondary check is `eurostat_sts_industry_wage_bill_de_real_yoy`. It is a hard observed monthly wage-bill indicator and therefore valuable as a payroll-cost check, but it is not the main proxy because its German industry scope is narrower than the euro-area negotiated-wage concept.

No composite index is selected. The available candidates measure different constructs, and combining negotiated wages, sector wage bills, labor-market tightness, and expectations would obscure the measurement boundary more than it would strengthen it. The 3-month wage-tracker average remains a transparent noise-control check, not a new source series.

## Full Ranking

| rank | variable | label | role | source | canonical_status | compensation_proxy_score | directional_consistency | cumulative_persistence | hac_p10_horizon_share | bootstrap_sign_stability_h6 | contamination_flag | frequency_integrity |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | eurostat_sts_industry_wage_bill_de_real_yoy | Eurostat German industry wage bill, real annual growth | robustness | Eurostat STS | secondary_robustness_compensation_proxy | 157 | 1.000 | 1.539 | 0.600 | 1.000 | stable_to_info_screen | true_monthly_observed_or_transformed_from_true_monthly |
| 2 | eurostat_ecfin_eei_ea20 | European Commission employment expectations indicator | indirect | Eurostat/DG ECFIN BCS | not_selected | 145 | 1.000 | 2.732 | 0.000 | 0.824 | stable_to_info_screen | true_monthly_observed_or_transformed_from_true_monthly |
| 3 | ecb_wage_tracker_ex_oneoffs_real_yoy | ECB Wage Tracker excluding one-off payments, real | canonical | ECB EWT | primary_canonical_compensation_proxy | 141 | 1.000 | -0.304 | 0.400 | 0.910 | stable_to_info_screen | true_monthly_observed_or_transformed_from_true_monthly |
| 4 | eurostat_ecfin_services_employment_expectations_ea20 | European Commission services employment expectations | indirect | Eurostat/DG ECFIN BCS | not_selected | 140 | 1.000 | 2.146 | 0.000 | 0.829 | stable_to_info_screen | true_monthly_observed_or_transformed_from_true_monthly |
| 5 | ecb_wage_tracker_headline_real_yoy | ECB Wage Tracker headline, real | robustness | ECB EWT | not_selected | 138 | 0.800 | -0.233 | 0.200 | 0.829 | stable_to_info_screen | true_monthly_observed_or_transformed_from_true_monthly |
| 6 | ecb_wage_tracker_unsmoothed_oneoffs_real_yoy | ECB Wage Tracker with unsmoothed one-off payments, real | robustness | ECB EWT | not_selected | 120 | 0.600 | -0.092 | 0.000 | 0.553 | sensitive_to_info_screen | true_monthly_observed_or_transformed_from_true_monthly |
| 7 | eurostat_labor_tightness_unemployment_inv | Eurostat unemployment inverse labor-tightness proxy | indirect | Eurostat LFS | not_selected | 118 | 0.800 | 0.141 | 0.000 | 0.899 | sensitive_to_info_screen | true_monthly_observed_or_transformed_from_true_monthly |
| 8 | ecb_wage_tracker_ex_oneoffs_real_yoy_ma3 | ECB Wage Tracker excluding one-offs, real 3-month average | robustness | ECB EWT + EA HICP | noise_control_robustness_proxy | 114 | 0.600 | -0.005 | 0.000 | 0.553 | sensitive_to_info_screen | true_monthly_observed_or_transformed_from_true_monthly |
| 8 | ecb_wage_tracker_ex_oneoffs_real_yoy_momentum_3m | ECB Wage Tracker excluding one-offs, real 3-month momentum | diagnostic | ECB EWT + EA HICP | not_selected | 114 | 0.600 | 0.014 | 0.000 | 0.613 | sensitive_to_info_screen | true_monthly_observed_or_transformed_from_true_monthly |
| 10 | ecb_ces_real_income_expectations_12m_median | ECB CES real household income expectations | diagnostic_short_sample | ECB CES | not_selected | 66 |  |  |  |  | not_enough_clean_event_variation | true_monthly_observed_or_transformed_from_true_monthly |
| 11 | ecb_ces_unemployment_expectations_12m_median | ECB CES expected unemployment rate | diagnostic_short_sample | ECB CES | not_selected | 64 |  |  |  |  | not_enough_clean_event_variation | true_monthly_observed_or_transformed_from_true_monthly |

## Rejected Or Diagnostic-Only Candidates

| label | variable | decision | decision_reason |
| --- | --- | --- | --- |
| German retail volume | ln_retail_de_chained_index | rejected | Monthly real-activity/purchasing-power proxy, not a compensation or wage construct. |
| ECB Wage Tracker coverage | ecb_wage_tracker_coverage_pct | rejected_not_compensation | Coverage is a source-quality diagnostic, not a wage-pressure response variable. |
| Euro area real compensation per employee, quarter-end observed | ln_compensation_ea20_real_q_observed | rejected_nonmonthly | Conceptually direct, but observed only at quarter-end; the monthly thesis layer does not interpolate it. |
| Eurostat labour-cost index |  | rejected_unavailable_or_nonmonthly | quarterly, not a monthly compensation proxy |
| Eurostat compensation per employee |  | rejected_unavailable_or_nonmonthly | national-accounts compensation per employee is quarterly, not monthly |
| Eurostat job vacancy rate |  | rejected_unavailable_or_nonmonthly | job vacancy statistics are quarterly, so they are rejected for monthly LP responses |
| sector-specific ECB negotiated wages |  | rejected_unavailable_or_nonmonthly | ECB EWT API exposes only total-economy monthly wage-tracker series in this vintage |
| services ECB negotiated wage pressure |  | rejected_unavailable_or_nonmonthly | no separate monthly services EWT wage series is exposed; services employment expectations are retained only as an indirect proxy |
| core negotiated wage pressure outside ex-one-offs |  | rejected_unavailable_or_nonmonthly | the available monthly core-like EWT measure is the excluding-one-offs series; no additional official core EWT series is exposed |
| Eurostat services wage bill |  | rejected_unavailable_or_nonmonthly | searched STS services wage-bill dimensions do not return usable euro-area/German monthly observations in the official API query |
| Eurostat retail wage bill |  | rejected_unavailable_or_nonmonthly | searched STS trade wage-bill dimensions do not return usable euro-area/German monthly observations in the official API query |
| payroll/employment-income micro proxy |  | rejected_unavailable_or_nonmonthly | no reproducible public monthly official euro-area payroll micro proxy was found |
| Indeed wage tracker |  | rejected_unavailable_or_nonmonthly | not retained because the public official-source reproducibility standard is not met |
| PMI employment subindices |  | rejected_unavailable_or_nonmonthly | not retained because the series are proprietary and not reproducible from official public sources |
| negotiated pay settlements outside ECB Wage Tracker |  | rejected_unavailable_or_nonmonthly | not in local raw set |
| monthly compensation per employee |  | rejected_unavailable_or_nonmonthly | not available as a real monthly series in local or pulled official sources |

## Selection Logic

The scorecard evaluates frequency, coverage, stationarity, persistence, sign consistency, regime stability, bootstrap checks, economic interpretation, clean-event sensitivity, and noise. The ranking documents measurement quality rather than searching for significance.

## Residual Limitations

Even the best monthly compensation proxies are not observed monthly compensation per employee. ECB wage trackers measure negotiated wage pressure, STS wage-bill data are sector/geography narrower, and CES income expectations have a short public sample. The thesis can compare financial-transmission persistence with wage-pressure persistence, but it cannot claim exact compensation, welfare, or redistribution magnitudes.
