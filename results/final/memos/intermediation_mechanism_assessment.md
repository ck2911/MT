# Banking And Lending Timing

This layer adds banking and lending evidence to the monthly response estimates. It is timing evidence for financial propagation, not a bank-channel treatment effect.

## Banking Timing Matrix

| response_label | channel | frequency_integrity | earliest_p10_horizon | peak_abs_horizon | cumulative_response | direction | status |
| --- | --- | --- | --- | --- | --- | --- | --- |
| mortgage lending spread | banking_lending_conditions | monthly_observed | 1.0000 | 12.0000 | 0.1401 | positive | estimated |
| NFC lending spread | banking_lending_conditions | monthly_observed | 1.0000 | 12.0000 | 0.0707 | positive | estimated |
| mortgage lending rate | banking_lending_conditions | monthly_observed |  | 24.0000 | 0.0600 | positive | estimated |
| NFC lending rate | banking_lending_conditions | monthly_observed |  | 24.0000 | 0.0128 | positive | estimated |
| household credit | financial_credit | monthly_observed |  | 24.0000 | -0.0011 | negative | estimated |
| NFC credit | financial_credit | monthly_observed |  | 24.0000 | -0.0019 | negative | estimated |
| house-purchase lending growth | housing_finance | monthly_observed | 0.0000 | 6.0000 | 0.3570 | positive | estimated |
| pure new house-purchase loans | housing_finance | monthly_observed |  | 24.0000 | -0.0055 | negative | estimated |
| real wage tracker excl. one-offs | compensation_proxy | monthly_observed | 0.0000 | 24.0000 | -0.0414 | negative | estimated |
| employment expectations | labor_tightness | monthly_observed | 24.0000 | 1.0000 | 1.9621 | positive | estimated |
| BLS mortgage credit standards | bank_lending_survey | quarter_end_observed_only_no_interpolation |  |  |  | negative | estimated_quarter_end_only |
| BLS enterprise credit standards | bank_lending_survey | quarter_end_observed_only_no_interpolation |  |  |  | negative | estimated_quarter_end_only |
| BLS consumer-credit standards | bank_lending_survey | quarter_end_observed_only_no_interpolation |  |  |  | negative | estimated_quarter_end_only |
| BLS mortgage loan demand | bank_lending_survey | quarter_end_observed_only_no_interpolation |  |  |  | positive | estimated_quarter_end_only |
| BLS enterprise loan demand | bank_lending_survey | quarter_end_observed_only_no_interpolation |  |  |  | positive | estimated_quarter_end_only |
| BLS consumer-credit demand | bank_lending_survey | quarter_end_observed_only_no_interpolation |  |  |  | positive | estimated_quarter_end_only |

## Credit Supply Response Table

| response_label | channel | frequency_integrity | peak_response | coefficient_1sd | p_value | timing_note |
| --- | --- | --- | --- | --- | --- | --- |
| mortgage lending spread | banking_lending_conditions | monthly_observed | 0.0500 |  |  |  |
| NFC lending spread | banking_lending_conditions | monthly_observed | 0.0252 |  |  |  |
| mortgage lending rate | banking_lending_conditions | monthly_observed | 0.0338 |  |  |  |
| NFC lending rate | banking_lending_conditions | monthly_observed | 0.0375 |  |  |  |
| household credit | financial_credit | monthly_observed | -0.0014 |  |  |  |
| NFC credit | financial_credit | monthly_observed | -0.0009 |  |  |  |
| house-purchase lending growth | housing_finance | monthly_observed | 0.1487 |  |  |  |
| pure new house-purchase loans | housing_finance | monthly_observed | -0.0308 |  |  |  |
| BLS mortgage credit standards | bank_lending_survey | quarter_end_observed_only_no_interpolation |  | -0.1241 | 0.8905 | BLS is quarterly and appears only on quarter-end months; no monthly filling is used. |
| BLS enterprise credit standards | bank_lending_survey | quarter_end_observed_only_no_interpolation |  | -1.4785 | 0.0087 | BLS is quarterly and appears only on quarter-end months; no monthly filling is used. |
| BLS consumer-credit standards | bank_lending_survey | quarter_end_observed_only_no_interpolation |  | -0.7696 | 0.2457 | BLS is quarterly and appears only on quarter-end months; no monthly filling is used. |
| BLS mortgage loan demand | bank_lending_survey | quarter_end_observed_only_no_interpolation |  | 3.6077 | 0.0301 | BLS is quarterly and appears only on quarter-end months; no monthly filling is used. |
| BLS enterprise loan demand | bank_lending_survey | quarter_end_observed_only_no_interpolation |  | 3.0995 | 0.0000 | BLS is quarterly and appears only on quarter-end months; no monthly filling is used. |
| BLS consumer-credit demand | bank_lending_survey | quarter_end_observed_only_no_interpolation |  | 2.7758 | 0.0025 | BLS is quarterly and appears only on quarter-end months; no monthly filling is used. |

## Transmission Ranking

| response_label | channel | intermediation_timing_score | early_timing_score | persistence_rank | direction | frequency_integrity |
| --- | --- | --- | --- | --- | --- | --- |
| house-purchase lending growth | housing_finance | 3.0000 | 1.0000 | 2.0000 | positive | monthly_observed |
| employment expectations | labor_tightness | 4.0000 | 3.0000 | 1.0000 | positive | monthly_observed |
| mortgage lending spread | banking_lending_conditions | 5.0000 | 2.0000 | 3.0000 | positive | monthly_observed |
| NFC lending spread | banking_lending_conditions | 6.0000 | 2.0000 | 4.0000 | positive | monthly_observed |
| real wage tracker excl. one-offs | compensation_proxy | 7.0000 | 1.0000 | 6.0000 | negative | monthly_observed |
| mortgage lending rate | banking_lending_conditions | 8.0000 | 3.0000 | 5.0000 | positive | monthly_observed |
| NFC lending rate | banking_lending_conditions | 10.0000 | 3.0000 | 7.0000 | positive | monthly_observed |
| pure new house-purchase loans | housing_finance | 11.0000 | 3.0000 | 8.0000 | negative | monthly_observed |
| NFC credit | financial_credit | 12.0000 | 3.0000 | 9.0000 | negative | monthly_observed |
| household credit | financial_credit | 13.0000 | 3.0000 | 10.0000 | negative | monthly_observed |
| BLS consumer-credit standards | bank_lending_survey | 15.0000 | 4.0000 | 11.0000 | negative | quarter_end_observed_only_no_interpolation |
| BLS mortgage credit standards | bank_lending_survey | 15.0000 | 4.0000 | 11.0000 | negative | quarter_end_observed_only_no_interpolation |
| BLS enterprise credit standards | bank_lending_survey | 15.0000 | 4.0000 | 11.0000 | negative | quarter_end_observed_only_no_interpolation |
| BLS consumer-credit demand | bank_lending_survey | 15.0000 | 4.0000 | 11.0000 | positive | quarter_end_observed_only_no_interpolation |
| BLS mortgage loan demand | bank_lending_survey | 15.0000 | 4.0000 | 11.0000 | positive | quarter_end_observed_only_no_interpolation |
| BLS enterprise loan demand | bank_lending_survey | 15.0000 | 4.0000 | 11.0000 | positive | quarter_end_observed_only_no_interpolation |

## Sequential Timing Summary

| pathway | upstream_label | downstream_label | shock_to_upstream_coef | shock_to_downstream_coef | timing_classification | sequence_class | language_guardrail |
| --- | --- | --- | --- | --- | --- | --- | --- |
| mortgage_spread_to_house_purchase_growth | mortgage lending spread | house-purchase lending growth | 0.0207 | 0.1487 | ordered_dynamic_transmission | timing_consistent_financial_propagation | ordered timing evidence only |
| nfc_lending_spread_to_nfc_credit | NFC lending spread | NFC credit | 0.0166 | 0.0002 | ordered_dynamic_transmission | timing_consistent_financial_propagation | ordered timing evidence only |
| liquidity_to_nfc_credit | ECB assets | NFC credit | -0.0019 | -0.0005 | ordered_dynamic_transmission | timing_consistent_financial_propagation | ordered timing evidence only |
| household_credit_to_house_purchase_growth | household credit | house-purchase lending growth | 0.0001 | 0.1340 | ordered_dynamic_transmission | timing_consistent_financial_propagation | ordered timing evidence only |
| house_purchase_growth_to_new_mortgage_flow | house-purchase lending growth | pure new house-purchase loans | 0.0536 | 0.0014 | ordered_dynamic_transmission | timing_consistent_financial_propagation | ordered timing evidence only |
| nfc_credit_to_wage_pressure | NFC credit | real wage tracker excl. one-offs | -0.0006 | -0.0895 | ordered_dynamic_transmission | timing_consistent_financial_propagation | ordered timing evidence only |
| employment_expectations_to_wage_pressure | employment expectations | real wage tracker excl. one-offs | 1.1731 | -0.0895 | ordered_dynamic_transmission | timing_consistent_financial_propagation | ordered timing evidence only |
| market_conditions_to_wage_pressure | real DAX | real wage tracker excl. one-offs | -0.0021 | -0.0895 | ordered_dynamic_transmission | timing_consistent_financial_propagation | ordered timing evidence only |

## Interpretation Boundary

Banking and lending variables are evaluated for whether they respond earlier or more persistently than housing-finance and wage-pressure proxies. That supports an intermediation reading, but not bank-to-distribution treatment-effect claims, exact structural magnitudes, or welfare interpretation.
