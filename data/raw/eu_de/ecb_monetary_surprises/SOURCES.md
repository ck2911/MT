# ECB Monetary Surprise Sources

This directory stores raw ECB high-frequency monetary-policy surprise sources for the EU/DE thesis.
Raw files are kept unchanged once downloaded.

## Sources

- ECB EA-MPD workbook: https://www.ecb.europa.eu/pub/pdf/annex/Dataset_EA-MPD.xlsx
- ABGMR factor page: https://gragusa.org/factors/
- Current press-release factor CSV: https://gragusa.org/factors/data/press_release_factors_2025-10-30.csv
- Current press-conference factor CSV: https://gragusa.org/factors/data/press_conference_factors_2025-10-30.csv
- ABGMR all-vintages ZIP: https://gragusa.org/factors/factors.zip

## Working Vintage

- Press release factors: `press_release_factors_2025-10-30.csv`
- Press conference factors: `press_conference_factors_2025-10-30.csv`
- EA-MPD workbook: `Dataset_EA-MPD_2026-05-15.xlsx`

## Source Notes

- The ABGMR factor files split the policy-decision and communication windows: `target` is in the press-release file; `timing`, `fg`, and `qe` are in the press-conference file.
- The ECB EA-MPD workbook is used for event validation and lightweight Jarocinski-Karadi-style sign screening through `OIS_6M` and `STOXX50` in the monetary-event window.
- The thesis shock is the monthly sum of the target factor, sign-flipped so that positive values are easing surprises (`target_factor_monthly_easing`). The other factors and aggregation rules are robustness checks.
