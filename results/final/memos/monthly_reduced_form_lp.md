# Monthly Reduced-Form Local Projections

This step estimates monthly responses to high-frequency ECB policy surprises. Coefficients are reported for a one-standard-deviation ECB surprise; unscaled coefficients are also kept for reference.

## Primary Target-Shock IRFs

| response_label | channel | horizon_months | coefficient | std_error_hac | ci_90_low | ci_90_high | bootstrap_ci_90_low | bootstrap_ci_90_high | p_value | nobs |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| mortgage lending rate | banking_lending_conditions | 0 | -0.0026 | 0.0027 | -0.0070 | 0.0018 | -0.0081 | 0.0031 | 0.3318 | 246 |
| mortgage lending rate | banking_lending_conditions | 1 | 0.0002 | 0.0052 | -0.0084 | 0.0088 | -0.0089 | 0.0087 | 0.9682 | 245 |
| mortgage lending rate | banking_lending_conditions | 3 | -0.0004 | 0.0106 | -0.0179 | 0.0171 | -0.0165 | 0.0151 | 0.9689 | 243 |
| mortgage lending rate | banking_lending_conditions | 6 | 0.0023 | 0.0167 | -0.0253 | 0.0298 | -0.0250 | 0.0332 | 0.8927 | 240 |
| mortgage lending rate | banking_lending_conditions | 12 | 0.0268 | 0.0260 | -0.0161 | 0.0696 | -0.0298 | 0.0773 | 0.3040 | 234 |
| mortgage lending rate | banking_lending_conditions | 24 | 0.0338 | 0.0441 | -0.0388 | 0.1063 | -0.0375 | 0.1100 | 0.4442 | 222 |
| mortgage lending spread | banking_lending_conditions | 0 | 0.0061 | 0.0065 | -0.0047 | 0.0168 | -0.0027 | 0.0136 | 0.3521 | 246 |
| mortgage lending spread | banking_lending_conditions | 1 | 0.0207 | 0.0085 | 0.0067 | 0.0346 | 0.0085 | 0.0323 | 0.0149 | 245 |
| mortgage lending spread | banking_lending_conditions | 3 | 0.0146 | 0.0156 | -0.0111 | 0.0402 | -0.0081 | 0.0347 | 0.3500 | 243 |
| mortgage lending spread | banking_lending_conditions | 6 | 0.0269 | 0.0205 | -0.0068 | 0.0605 | -0.0037 | 0.0547 | 0.1890 | 240 |
| mortgage lending spread | banking_lending_conditions | 12 | 0.0500 | 0.0260 | 0.0073 | 0.0927 | 0.0064 | 0.0973 | 0.0543 | 234 |
| mortgage lending spread | banking_lending_conditions | 24 | 0.0219 | 0.0233 | -0.0164 | 0.0603 | -0.0207 | 0.0658 | 0.3471 | 222 |
| NFC lending rate | banking_lending_conditions | 0 | -0.0088 | 0.0059 | -0.0185 | 0.0008 | -0.0186 | -0.0003 | 0.1316 | 246 |
| NFC lending rate | banking_lending_conditions | 1 | -0.0048 | 0.0114 | -0.0235 | 0.0139 | -0.0185 | 0.0106 | 0.6732 | 245 |
| NFC lending rate | banking_lending_conditions | 3 | -0.0123 | 0.0199 | -0.0450 | 0.0205 | -0.0399 | 0.0112 | 0.5377 | 243 |
| NFC lending rate | banking_lending_conditions | 6 | -0.0081 | 0.0288 | -0.0554 | 0.0392 | -0.0489 | 0.0319 | 0.7785 | 240 |
| NFC lending rate | banking_lending_conditions | 12 | 0.0093 | 0.0473 | -0.0684 | 0.0871 | -0.0775 | 0.0914 | 0.8434 | 234 |
| NFC lending rate | banking_lending_conditions | 24 | 0.0375 | 0.0630 | -0.0662 | 0.1411 | -0.0609 | 0.1370 | 0.5521 | 222 |
| NFC lending spread | banking_lending_conditions | 0 | 0.0004 | 0.0067 | -0.0106 | 0.0114 | -0.0095 | 0.0097 | 0.9538 | 246 |
| NFC lending spread | banking_lending_conditions | 1 | 0.0166 | 0.0092 | 0.0014 | 0.0318 | 0.0051 | 0.0280 | 0.0726 | 245 |
| NFC lending spread | banking_lending_conditions | 3 | 0.0030 | 0.0088 | -0.0114 | 0.0174 | -0.0100 | 0.0157 | 0.7330 | 243 |
| NFC lending spread | banking_lending_conditions | 6 | 0.0152 | 0.0105 | -0.0021 | 0.0325 | 0.0005 | 0.0314 | 0.1494 | 240 |
| NFC lending spread | banking_lending_conditions | 12 | 0.0252 | 0.0119 | 0.0056 | 0.0447 | 0.0030 | 0.0487 | 0.0342 | 234 |
| NFC lending spread | banking_lending_conditions | 24 | 0.0104 | 0.0105 | -0.0069 | 0.0277 | -0.0144 | 0.0363 | 0.3218 | 222 |
| real wage tracker excl. one-offs | compensation_proxy | 0 | -0.0690 | 0.0369 | -0.1297 | -0.0084 | -0.1206 | -0.0057 | 0.0611 | 152 |
| real wage tracker excl. one-offs | compensation_proxy | 1 | -0.0202 | 0.0416 | -0.0886 | 0.0483 | -0.0944 | 0.0590 | 0.6276 | 151 |
| real wage tracker excl. one-offs | compensation_proxy | 3 | -0.0814 | 0.0405 | -0.1480 | -0.0147 | -0.1720 | 0.0276 | 0.0446 | 149 |
| real wage tracker excl. one-offs | compensation_proxy | 6 | -0.0895 | 0.0619 | -0.1912 | 0.0123 | -0.2021 | 0.0410 | 0.1482 | 146 |
| real wage tracker excl. one-offs | compensation_proxy | 12 | -0.0418 | 0.0607 | -0.1417 | 0.0581 | -0.1835 | 0.1739 | 0.4913 | 140 |
| real wage tracker excl. one-offs | compensation_proxy | 24 | 0.2605 | 0.2183 | -0.0987 | 0.6196 | 0.0690 | 0.5112 | 0.2329 | 128 |
| real wage tracker excl. one-offs, 3m avg | compensation_proxy | 0 | -0.0036 | 0.0162 | -0.0303 | 0.0230 | -0.0256 | 0.0172 | 0.8220 | 152 |
| real wage tracker excl. one-offs, 3m avg | compensation_proxy | 1 | 0.0022 | 0.0311 | -0.0490 | 0.0533 | -0.0423 | 0.0555 | 0.9448 | 151 |
| real wage tracker excl. one-offs, 3m avg | compensation_proxy | 3 | -0.0243 | 0.0529 | -0.1113 | 0.0627 | -0.1060 | 0.0611 | 0.6458 | 149 |
| real wage tracker excl. one-offs, 3m avg | compensation_proxy | 6 | -0.0092 | 0.0676 | -0.1204 | 0.1021 | -0.1117 | 0.0928 | 0.8922 | 146 |
| real wage tracker excl. one-offs, 3m avg | compensation_proxy | 12 | 0.0310 | 0.0491 | -0.0498 | 0.1119 | -0.1309 | 0.2287 | 0.5278 | 140 |
| real wage tracker excl. one-offs, 3m avg | compensation_proxy | 24 | 0.2318 | 0.1704 | -0.0485 | 0.5121 | 0.0145 | 0.4812 | 0.1738 | 128 |

## Cumulative Responses

| response_label | channel | horizon_months | cumulative_response | ci_90_low | ci_90_high |
| --- | --- | --- | --- | --- | --- |
| mortgage lending rate | banking_lending_conditions | 12 | 0.0262 | -0.0285 | 0.0809 |
| mortgage lending spread | banking_lending_conditions | 12 | 0.1181 | 0.0555 | 0.1808 |
| NFC lending rate | banking_lending_conditions | 12 | -0.0246 | -0.1236 | 0.0743 |
| NFC lending spread | banking_lending_conditions | 12 | 0.0603 | 0.0251 | 0.0955 |
| real wage tracker excl. one-offs | compensation_proxy | 12 | -0.3019 | -0.4839 | -0.1198 |
| real wage tracker excl. one-offs, 3m avg | compensation_proxy | 12 | -0.0039 | -0.1765 | 0.1687 |
| real wage tracker excl. one-offs, 3m momentum | compensation_proxy | 12 | 0.0144 | -0.2135 | 0.2424 |
| real wage tracker headline | compensation_proxy | 12 | -0.2320 | -0.4224 | -0.0417 |
| real wage tracker unsmoothed one-offs | compensation_proxy | 12 | -0.0963 | -0.4314 | 0.2388 |
| German industry real wage bill growth | compensation_proxy | 12 | 1.5929 | 0.9281 | 2.2576 |
| household credit | financial_credit | 12 | 0.0003 | -0.0012 | 0.0018 |
| NFC credit | financial_credit | 12 | -0.0009 | -0.0053 | 0.0035 |
| ECB assets | financial_liquidity | 12 | -0.0217 | -0.0479 | 0.0046 |
| real DAX | financial_market | 12 | -0.0396 | -0.0654 | -0.0137 |
| house-purchase lending growth | housing_finance | 12 | 0.4832 | 0.3266 | 0.6397 |
| pure new house-purchase loans | housing_finance | 12 | 0.0253 | -0.0209 | 0.0715 |
| employment expectations | labor_tightness | 12 | 2.7618 | 0.6534 | 4.8701 |
| services employment expectations | labor_tightness | 12 | 2.1709 | 0.4397 | 3.9020 |
| inverse unemployment labor tightness | labor_tightness | 12 | 0.1437 | 0.0334 | 0.2539 |
| retail volume | real_activity | 12 | -0.0005 | -0.0052 | 0.0043 |
| mortgage lending rate | banking_lending_conditions | 24 | 0.0600 | -0.0309 | 0.1509 |
| mortgage lending spread | banking_lending_conditions | 24 | 0.1401 | 0.0666 | 0.2135 |
| NFC lending rate | banking_lending_conditions | 24 | 0.0128 | -0.1305 | 0.1561 |
| NFC lending spread | banking_lending_conditions | 24 | 0.0707 | 0.0315 | 0.1100 |

## Uncertainty

IRF tables include HAC/Newey-West confidence bands with horizon-specific bandwidth `h + 1`. Target-shock IRFs also include feasible circular-block residual percentile bootstrap intervals. Moving-block and wild bootstrap checks are used for cumulative bands. Cumulative responses support persistence language, not exact structural multipliers.

## Excluded Quarterly-Only Responses

| response | reason |
| --- | --- |
| ln_house_price_de_real_q_observed | Quarterly housing series is sparse at quarter-end only; not interpolated. |
| ln_compensation_ea20_real_q_observed | Quarterly compensation series is sparse at quarter-end only; not interpolated. |

## Interpretation

Use this language: ECB monetary-policy surprises generate dynamic response patterns in monthly financial, housing-finance, real-activity, and negotiated-wage-pressure variables.

Avoid this language: these LPs identify structural QE treatment effects, exact housing-price effects, compensation-per-employee treatment effects, welfare effects, or redistribution magnitudes.
