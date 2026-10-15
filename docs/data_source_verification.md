# Data Source Verification (2026-09-27)

Every raw series used by the thesis was traced to its origin and re-downloaded from the live source on
27 September 2026, then compared value by value (or by SHA-256 for whole files) with the file in `data/raw/eu_de/`.
The provenance of the manually downloaded files comes from their own metadata headers (recorded in a
file-structure inventory from the data-construction phase), the original FRED downloads, and the Codex session
logs of 15 May 2026, which show the raw extracts being written from those originals. The inventory and the FRED
originals are not part of this repository. They are kept in the author's backup archive
`THESIS_Model_archive_backup_20261011.zip` (folders `eu_de_forensic_phase/` and `source_raw_downloads/`) and are
available on request.

Thesis table: `LATEX/tables/static_data_sources.tex` (Table A.2).

| Raw file | Origin | Series / code | Accessed | Live check 2026-09-27 |
|---|---|---|---|---|
| `ecb_deposit_facility_rate_daily.csv` | FRED `ECBDFR` (source ECB) | ECB `FM.D.U2.EUR.4F.KR.DFR.LEV` | 2026-05-15 | identical, 7,670 / 7,670 days |
| `ecb_central_bank_assets_weekly.csv` | FRED `ECBASSETSW` (source ECB) | ECB `ILM.W.U2.C.T000000.Z5.Z01` | 2026-05-15 | identical, 1,095 / 1,095 weeks |
| `germany_residential_prices_quarterly.csv` | FRED `QDEN628BIS` (source BIS), data updated 2026-04-30 | BIS `WS_SPP Q.DE.N.628` | 2026-05-15 | same series, revised by BIS (FRED update 2026-07-31); differences up to 0.4 %. No ECB series matches (ECB RESR indices differ in method and base). |
| `hicp_selected_cp00_de_ea20_ea.tsv` | Eurostat `prc_hicp_midx` bulk TSV | `M.I05.CP00.{DE,EA20,EA}` (index 2005=100) | 2026-05-15 | identical, 1,033 / 1,033 |
| `1. Wu-Xia Euro Area Shadow Rate.xls` | sites.google.com/view/jingcynthiawu/shadow-rates, "Excel file" | euro area shadow rate 2004-09 to 2022-08 | 2026-05-15 | byte-identical (SHA-256) |
| `8. DAX 40.csv` | Yahoo Finance `^GDAXI`, monthly | DAX index | 2026-05-15 | open/high/low/close identical to the cent (float rounding only); volume column differs and is unused |
| `4. loans to euro area households ....xlsx` | ECB Data Portal, downloaded 2026-05-15 14:47:34 | `BSI.M.U2.N.A.A20T.A.1.U2.2250.Z01.E` | 2026-05-15 | identical through 2024-11 (2-dp rounding), later months revised by the ECB |
| `5. Adjusted loans to euro area NFCs ....xlsx` | ECB Data Portal, downloaded 2026-05-15 14:53:21 | `BSI.M.U2.N.A.A20T.A.1.U2.2240.Z01.E` | 2026-05-15 | identical through 2024-11, later months revised |
| `9. Compensation per employee.xlsx` | ECB Data Portal, downloaded 2026-05-15 15:53:07 | `MNA.Q.Y.I9.W2.S1.S1._Z.COM_PS._Z._T._Z.IX.V.N` | 2026-05-15 | same series, national-accounts revision (max 0.28 index points, 2025Q4) |
| `Dataset_EA-MPD_2026-05-15.xlsx` | ECB | EA-MPD workbook | 2026-05-15 | byte-identical |
| `press_{release,conference}_factors_2025-10-30.csv` | gragusa.org/factors | ABGMR factors, vintage 2025-10-30 | 2026-05-15 | byte-identical |
| BLS (6), MIR (3), CES (2) CSVs | ECB Data Portal API | keys in the source manifests | 2026-05-16 | identical (MIR NFC rate: 2026-02/03 revised) |
| `ecb_bsi_house_purchase_annual_growth.csv` | ECB Data Portal API | `BSI.M.U2.Y.U.A22.A.I.U2.2250.Z01.A` | 2026-05-16 | identical (float noise < 1e-9 only) |
| ECB wage tracker (3) + coverage | ECB Data Portal API | `EWT.M.U2.N.WT.{INWX,INWS,INWR}._T.4F0.GY` | 2026-05-16 | same series, full-history revision by the ECB (max 0.24 pp ex one-offs, corr 0.998) |
| Eurostat ECFIN (2), STS wage bill | Eurostat API | manifests | 2026-05-16 | identical |
| Eurostat unemployment | Eurostat API | `une_rt_m` EA21 SA | 2026-05-16 | same series, small revisions |

Consequence: the estimates use the 15-16 May 2026 vintages. Re-downloading today would change the wage-tracker,
compensation, loan-stock, unemployment and house-price inputs slightly. Keep the raw files unchanged.

Used as a robustness diagnostic (German retail volume, Ch. 4 and 6): `10 volume of sales ... .xlsx`
(Eurostat `sts_trtu_m`, extracted 2026-05-15 15:55:48).

Not used in the thesis, so not cited: `6./6.1 Credit standards ... .xlsx` (superseded by the BLS API pulls),
the annual Eurosystem balance sheet.
