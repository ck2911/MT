# Information-Effect Screen

This screen compares three event-level signs:

- rate-factor sign: `target_factor` when available, otherwise `timing_factor`;
- yield-window sign: `OIS_6M` from the EA-MPD monetary-event window when available;
- equity-window sign: `STOXX50` from the same event window.

Same-sign yield and equity moves are flagged as possible central-bank information shocks. Opposite-sign yield and equity moves are treated as possible pure monetary shocks. Factor-yield sign conflicts and missing/zero market windows are contamination flags, not exclusions by themselves.

## Full Event Screen

| information_effect_screen | event_count | share |
| --- | --- | --- |
| possible_pure_monetary_shock | 86 | 0.352 |
| mixed_sign_factor_yield_conflict | 81 | 0.332 |
| possible_information_shock | 68 | 0.279 |
| ambiguous_zero_response | 9 | 0.037 |

## Monthly Identification Window

| information_effect_screen | event_count | share |
| --- | --- | --- |
| possible_pure_monetary_shock | 76 | 0.365 |
| mixed_sign_factor_yield_conflict | 69 | 0.332 |
| possible_information_shock | 54 | 0.260 |
| ambiguous_zero_response | 9 | 0.043 |

## Regime Summary

| regime | information_effect_screen | event_count | share_within_regime |
| --- | --- | --- | --- |
| covid | mixed_sign_factor_yield_conflict | 6 | 0.300 |
| covid | possible_information_shock | 6 | 0.300 |
| covid | possible_pure_monetary_shock | 8 | 0.400 |
| euro_crisis | ambiguous_zero_response | 1 | 0.017 |
| euro_crisis | mixed_sign_factor_yield_conflict | 20 | 0.333 |
| euro_crisis | possible_information_shock | 17 | 0.283 |
| euro_crisis | possible_pure_monetary_shock | 22 | 0.367 |
| gfc | mixed_sign_factor_yield_conflict | 2 | 0.105 |
| gfc | possible_information_shock | 9 | 0.474 |
| gfc | possible_pure_monetary_shock | 8 | 0.421 |
| pre_gfc | mixed_sign_factor_yield_conflict | 29 | 0.372 |
| pre_gfc | possible_information_shock | 24 | 0.308 |
| pre_gfc | possible_pure_monetary_shock | 25 | 0.321 |
| qe_era | ambiguous_zero_response | 7 | 0.175 |
| qe_era | mixed_sign_factor_yield_conflict | 13 | 0.325 |
| qe_era | possible_information_shock | 8 | 0.200 |
| qe_era | possible_pure_monetary_shock | 12 | 0.300 |
| tightening_regime | ambiguous_zero_response | 1 | 0.037 |
| tightening_regime | mixed_sign_factor_yield_conflict | 11 | 0.407 |
| tightening_regime | possible_information_shock | 4 | 0.148 |
| tightening_regime | possible_pure_monetary_shock | 11 | 0.407 |

## Recent Flagged Events

| event_date | event_quarter | regime | rate_factor_sign | yield_response_sign | equity_response_sign | information_effect_screen |
| --- | --- | --- | --- | --- | --- | --- |
| 2023-03-16 | 2023Q1 | tightening_regime | positive | positive | positive | possible_information_shock |
| 2023-06-15 | 2023Q2 | tightening_regime | negative | positive | positive | mixed_sign_factor_yield_conflict |
| 2023-09-14 | 2023Q3 | tightening_regime | positive | positive | positive | possible_information_shock |
| 2023-12-14 | 2023Q4 | tightening_regime | negative | positive | negative | mixed_sign_factor_yield_conflict |
| 2024-03-07 | 2024Q1 | tightening_regime | positive | negative | positive | mixed_sign_factor_yield_conflict |
| 2024-04-11 | 2024Q2 | tightening_regime | negative | zero | positive | ambiguous_zero_response |
| 2024-06-06 | 2024Q2 | tightening_regime | negative | positive | negative | mixed_sign_factor_yield_conflict |
| 2024-09-12 | 2024Q3 | tightening_regime | negative | positive | negative | mixed_sign_factor_yield_conflict |
| 2024-12-12 | 2024Q4 | tightening_regime | positive | positive | positive | possible_information_shock |
| 2025-03-06 | 2025Q1 | tightening_regime | negative | positive | positive | mixed_sign_factor_yield_conflict |
| 2025-06-05 | 2025Q2 | tightening_regime | negative | positive | negative | mixed_sign_factor_yield_conflict |
| 2025-07-24 | 2025Q3 | tightening_regime | negative | positive | negative | mixed_sign_factor_yield_conflict |

## Use In The Thesis

These flags identify events whose market reaction may contain central-bank information or sign conflicts. They do not prove exogeneity. They are used to check whether the main housing-versus-compensation result survives cleaner event samples.
