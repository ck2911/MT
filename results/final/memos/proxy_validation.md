# Proxy Selection

This note records the monthly proxy choices. No quarterly housing or compensation series is turned into artificial monthly data. A proxy is used only when it is observed monthly or transparently constructed from monthly data.

## Main Selections

| side | variable | label | conceptual_object | source | sample_start | sample_end | monthly_continuity | quarterly_target_correlation | horizon_sign_stability | information_effect_flag | validation_score |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| compensation | ecb_wage_tracker_ex_oneoffs_real_yoy | ECB Wage Tracker excluding one-off payments, real | Monthly real negotiated wage pressure excluding one-off payments. | ECB EWT | 2013-01-31 | 2025-10-31 | 1.000 | 0.729 | 1.000 | stable_to_info_screen | 120 |
| housing | ecb_house_purchase_growth_yoy | ECB lending for house purchase, annual growth | Monthly growth in MFI loans for house purchase; housing-finance transmission. | ECB BSI | 2005-01-31 | 2025-10-31 | 1.000 | 0.018 | 1.000 | stable_to_info_screen | 119 |

## Accepted Proxies

| side | role | variable | label | conceptual_object | source | observations | monthly_continuity | quarterly_target_correlation | decision_reason |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| compensation | canonical | ecb_wage_tracker_ex_oneoffs_real_yoy | ECB Wage Tracker excluding one-off payments, real | Monthly real negotiated wage pressure excluding one-off payments. | ECB EWT | 154 | 1.000 | 0.729 | Best monthly compensation-side proxy for persistent real negotiated wage pressure; not actual compensation per employee. |
| compensation | diagnostic | ecb_wage_tracker_ex_oneoffs_real_yoy_momentum_3m | ECB Wage Tracker excluding one-offs, real 3-month momentum | Three-month change in real negotiated wage pressure excluding one-off payments. | ECB EWT + EA HICP | 151 | 1.000 | 0.153 | Momentum captures acceleration in real negotiated wage pressure and is useful for signal-timing checks. |
| compensation | diagnostic_short_sample | ecb_ces_real_income_expectations_12m_median | ECB CES real household income expectations | Weighted median expected household income growth over the next 12 months minus HICP inflation. | ECB CES | 43 | 1.000 | 0.952 | Monthly household income-pressure expectations are observable, but the public aggregate sample starts late. |
| compensation | diagnostic_short_sample | ecb_ces_unemployment_expectations_12m_median | ECB CES expected unemployment rate | Weighted median expected unemployment rate over the next 12 months. | ECB CES | 43 | 1.000 | -0.960 | Monthly household labor-market expectations are useful as a short-window expectation diagnostic. |
| compensation | indirect | eurostat_ecfin_eei_ea20 | European Commission employment expectations indicator | Monthly euro-area employment expectations indicator over the next three months. | Eurostat/DG ECFIN BCS | 250 | 1.000 | -0.053 | Timely monthly expected-employment pressure proxy from harmonised business surveys. |
| compensation | indirect | eurostat_ecfin_services_employment_expectations_ea20 | European Commission services employment expectations | Monthly euro-area services employment expectations balance. | Eurostat/DG ECFIN BCS | 250 | 1.000 | -0.048 | Monthly services-sector employment expectations add a services wage-pressure timing proxy. |
| compensation | indirect | eurostat_labor_tightness_unemployment_inv | Eurostat unemployment inverse labor-tightness proxy | Negative of the monthly seasonally adjusted euro-area unemployment rate. | Eurostat LFS | 250 | 1.000 | -0.057 | True monthly labor-tightness proxy; higher transformed value means lower unemployment and tighter labor markets. |
| compensation | robustness | eurostat_sts_industry_wage_bill_de_real_yoy | Eurostat German industry wage bill, real annual growth | Monthly gross wages and salaries index for German industry, deflated by German HICP annual inflation. | Eurostat STS | 238 | 1.000 | 0.313 | True monthly wage-bill series; adds a hard observed payroll-cost proxy, but only for German industry. |
| compensation | robustness | ecb_wage_tracker_headline_real_yoy | ECB Wage Tracker headline, real | Monthly real negotiated wage pressure including smoothed one-off payments. | ECB EWT | 154 | 1.000 | 0.731 | Monthly negotiated wage signal including smoothed one-off payments; useful check around the main wage tracker. |
| compensation | robustness | ecb_wage_tracker_ex_oneoffs_real_yoy_ma3 | ECB Wage Tracker excluding one-offs, real 3-month average | Three-month average of monthly real negotiated wage pressure excluding one-off payments. | ECB EWT + EA HICP | 154 | 1.000 | 0.719 | Rolling real wage-pressure proxy smooths month-specific noise without fabricating observations. |
| compensation | robustness | ecb_wage_tracker_unsmoothed_oneoffs_real_yoy | ECB Wage Tracker with unsmoothed one-off payments, real | Monthly real negotiated wage pressure including unsmoothed one-off payments. | ECB EWT | 154 | 1.000 | 0.730 | Real monthly wage tracker, but one-off payments make it a noisier compensation proxy. |
| housing | canonical | ecb_house_purchase_growth_yoy | ECB lending for house purchase, annual growth | Monthly growth in MFI loans for house purchase; housing-finance transmission. | ECB BSI | 250 | 1.000 | 0.018 | Direct monthly housing-finance series with full sample coverage; it proxies mortgage-credit transmission, not house prices themselves. |
| housing | robustness | ln_ecb_house_purchase_pure_new_loans | ECB pure new loans for house purchase | Monthly flow of pure new house-purchase loans; mortgage-origination transmission. | ECB MIR | 99 | 1.000 | 0.763 | Direct housing-finance flow, but available only from 2017-08 in the pulled ECB vintage. |

## Retained Limitations

| variable | retained_limitations |
| --- | --- |
| ecb_wage_tracker_ex_oneoffs_real_yoy | It is negotiated wage pressure, not observed total compensation per employee, payroll income, welfare, or redistribution. |
| ecb_wage_tracker_ex_oneoffs_real_yoy_momentum_3m | Momentum is mechanically noisier than the level and is not used as the primary compensation proxy. |
| ecb_ces_real_income_expectations_12m_median | Short public CES sample makes it unsuitable as the main long-window compensation proxy. |
| ecb_ces_unemployment_expectations_12m_median | Short sample and expectation construct prevent main compensation use. |
| eurostat_ecfin_eei_ea20 | Survey expectations are indirect wage-pressure evidence and can revise with seasonal adjustment. |
| eurostat_ecfin_services_employment_expectations_ea20 | It captures expected services employment, not observed services wages. |
| eurostat_labor_tightness_unemployment_inv | Labor tightness is an indirect wage-pressure proxy, not compensation or wage growth. |
| eurostat_sts_industry_wage_bill_de_real_yoy | Sector/geography are narrow; the series measures wage bill, not compensation per employee. |
| ecb_wage_tracker_headline_real_yoy | One-off treatment can mechanically change short-horizon wage dynamics. |
| ecb_wage_tracker_ex_oneoffs_real_yoy_ma3 | Smoothing is transparent and only uses observed current/past monthly data; it is not a distinct source series. |
| ecb_wage_tracker_unsmoothed_oneoffs_real_yoy | Noisier one-off payments reduce persistence interpretability. |
| ecb_house_purchase_growth_yoy | It is a credit-growth proxy, not a direct affordability, price, rent, or welfare measure. |
| ln_ecb_house_purchase_pure_new_loans | Short sample beginning in 2017 limits regime and pre-QE comparisons. |

## Rejected Or Unavailable Proxies

| side | label | variable | decision | decision_reason |
| --- | --- | --- | --- | --- |
| compensation | German retail volume | ln_retail_de_chained_index | rejected | Monthly real-activity/purchasing-power proxy, not a compensation or wage construct. |
| compensation | Euro area real compensation per employee, quarter-end observed | ln_compensation_ea20_real_q_observed | rejected_nonmonthly | Conceptually direct, but observed only at quarter-end; the monthly thesis layer does not interpolate it. |
| compensation | ECB Wage Tracker coverage | ecb_wage_tracker_coverage_pct | rejected_not_compensation | Coverage is a source-quality diagnostic, not a wage-pressure response variable. |
| housing | ECB adjusted loans to households | ln_hh_loans_ea_stock | rejected_for_canonical | Monthly and continuous, but it covers all household loans rather than house-purchase credit specifically. |
| housing | German real house-price index, quarter-end observed | ln_house_price_de_real_q_observed | rejected_nonmonthly | Conceptually direct, but observed only at quarter-end; the monthly thesis layer does not interpolate it. |
| housing | residential REIT index |  | rejected_unavailable_or_nonmonthly | not in local official raw set; broad equity alternatives would weaken housing-specific interpretation |
| housing | property-company equity index |  | rejected_unavailable_or_nonmonthly | not in local official raw set; DAX is too broad to stand in for property companies |
| housing | Eurostat house-price expectations |  | rejected_unavailable_or_nonmonthly | not in local raw set as a monthly official series |
| housing | mortgage approval volumes |  | rejected_unavailable_or_nonmonthly | not in local raw set; ECB portal contains related MIR/BSI house-purchase lending volumes instead |
| housing | housing sentiment indicators |  | rejected_unavailable_or_nonmonthly | not in local raw set as a reproducible monthly official series |
| housing | construction-sector equity index |  | rejected_unavailable_or_nonmonthly | not in local official raw set |
| housing | housing-finance conditions |  | rejected_unavailable_or_nonmonthly | not in local raw set beyond house-purchase lending volumes |
| housing | mortgage spreads |  | rejected_unavailable_or_nonmonthly | not in local raw set as a reproducible monthly official spread series |
| housing | new mortgage issuance |  | rejected_unavailable_or_nonmonthly | proxied by ECB MIR pure new loans for house purchase where available |
| housing | residential lending standards |  | rejected_unavailable_or_nonmonthly | ECB Bank Lending Survey is quarterly and therefore not accepted as a monthly LP response |
| compensation | Eurostat labour-cost index |  | rejected_unavailable_or_nonmonthly | quarterly, not a monthly compensation proxy |
| compensation | Eurostat compensation per employee |  | rejected_unavailable_or_nonmonthly | national-accounts compensation per employee is quarterly, not monthly |
| compensation | Eurostat job vacancy rate |  | rejected_unavailable_or_nonmonthly | job vacancy statistics are quarterly, so they are rejected for monthly LP responses |
| compensation | sector-specific ECB negotiated wages |  | rejected_unavailable_or_nonmonthly | ECB EWT API exposes only total-economy monthly wage-tracker series in this vintage |
| compensation | services ECB negotiated wage pressure |  | rejected_unavailable_or_nonmonthly | no separate monthly services EWT wage series is exposed; services employment expectations are retained only as an indirect proxy |
| compensation | core negotiated wage pressure outside ex-one-offs |  | rejected_unavailable_or_nonmonthly | the available monthly core-like EWT measure is the excluding-one-offs series; no additional official core EWT series is exposed |
| compensation | Eurostat services wage bill |  | rejected_unavailable_or_nonmonthly | searched STS services wage-bill dimensions do not return usable euro-area/German monthly observations in the official API query |
| compensation | Eurostat retail wage bill |  | rejected_unavailable_or_nonmonthly | searched STS trade wage-bill dimensions do not return usable euro-area/German monthly observations in the official API query |
| compensation | payroll/employment-income micro proxy |  | rejected_unavailable_or_nonmonthly | no reproducible public monthly official euro-area payroll micro proxy was found |
| compensation | Indeed wage tracker |  | rejected_unavailable_or_nonmonthly | not retained because the public official-source reproducibility standard is not met |
| compensation | PMI employment subindices |  | rejected_unavailable_or_nonmonthly | not retained because the series are proprietary and not reproducible from official public sources |
| compensation | negotiated pay settlements outside ECB Wage Tracker |  | rejected_unavailable_or_nonmonthly | not in local raw set |
| compensation | monthly compensation per employee |  | rejected_unavailable_or_nonmonthly | not available as a real monthly series in local or pulled official sources |

## Selection Criteria

Each candidate is scored on economic relevance, monthly continuity, interpretability, response stability, correlation with the lower-frequency target, subperiod stability, and sensitivity to information-effect events. The score helps document measurement choices; it is not a mechanical claim filter.

## Interpretation Boundary

Accepted housing proxies measure housing finance, not residential prices. Accepted compensation proxies measure negotiated wage pressure, not compensation per employee or welfare. The final empirical claim may compare persistence in housing-finance and wage-pressure responses to ECB surprises, but exact housing-price, compensation, welfare, or redistribution magnitudes remain outside clean identification scope.

## Source Notes

- ECB house-purchase lending growth: `BSI.M.U2.Y.U.A22.A.I.U2.2250.Z01.A`.
- ECB pure new loans for house purchase: `MIR.M.U2.B.A2C.A.B.A.2250.EUR.P`.
- ECB Wage Tracker monthly series: headline `EWT.M.U2.N.WT.INWS._T.4F0.GY`; excluding one-offs `EWT.M.U2.N.WT.INWX._T.4F0.GY`; unsmoothed one-offs `EWT.M.U2.N.WT.INWR._T.4F0.GY`.
- Eurostat labour-cost indicators are quarterly and therefore rejected for the monthly comparison layer.
