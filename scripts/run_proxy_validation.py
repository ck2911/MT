#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import math
import os
import tempfile
import sys
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
os.environ.setdefault("MPLCONFIGDIR", str(Path(tempfile.gettempdir()) / "thesis_model_mpl_cache"))

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

from src.lpiv.ols_hac import add_constant, fit_ols_hac


MONTHLY_DATASET = ROOT / "data" / "processed" / "eu_de" / "final_monthly_model_dataset.csv"
QUARTERLY_DATASET = ROOT / "data" / "processed" / "eu_de" / "final_quarterly_model_dataset.csv"
EVENT_SCREEN = ROOT / "results" / "final" / "diagnostics" / "information_effect_event_screen.csv"
PROXY_RAW_DIR = ROOT / "data" / "raw" / "eu_de" / "monthly_proxy_candidates"
OUTPUT_DIR = ROOT / "results" / "identification_rebuild"
FINAL_DIAGNOSTICS = ROOT / "results" / "final" / "diagnostics"
FINAL_PROXY_VALIDATION = ROOT / "results" / "final" / "proxy_validation"
FINAL_COMPENSATION = FINAL_PROXY_VALIDATION / "compensation"
FINAL_FIGURES = ROOT / "results" / "final" / "figures"
FINAL_COMPENSATION_FIGURES = FINAL_FIGURES / "compensation"
DOCS_DIR = ROOT / "results" / "final" / "memos"  # working notes; docs/ holds only the curated notes

HORIZONS = (0, 1, 3, 6, 12)
PRIMARY_SHOCK = "target_factor_monthly_easing"
Z90 = 1.6448536269514722

SOURCE_URLS = {
    "ecb_bsi_house_purchase_annual_growth.csv": "https://data.ecb.europa.eu/data/datasets/BSI/BSI.M.U2.Y.U.A22.A.I.U2.2250.Z01.A",
    "ecb_mir_house_purchase_pure_new_loans.csv": "https://data.ecb.europa.eu/data/datasets/MIR/MIR.M.U2.B.A2C.A.B.A.2250.EUR.P",
    "ecb_wage_tracker_headline.csv": "https://data.ecb.europa.eu/data/datasets/EWT/EWT.M.U2.N.WT.INWS._T.4F0.GY",
    "ecb_wage_tracker_ex_oneoffs.csv": "https://data.ecb.europa.eu/data/datasets/EWT/EWT.M.U2.N.WT.INWX._T.4F0.GY",
    "ecb_wage_tracker_unsmoothed_oneoffs.csv": "https://data.ecb.europa.eu/data/datasets/EWT/EWT.M.U2.N.WT.INWR._T.4F0.GY",
    "ecb_wage_tracker_coverage.csv": "https://data-api.ecb.europa.eu/service/data/EWT/M.U2.N.WT.COVR._T.4F0._Z?format=csvdata",
    "eurostat_unemployment_ea21_sa.csv": "https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data/une_rt_m?geo=EA21&sex=T&age=TOTAL&s_adj=SA&unit=PC_ACT",
    "eurostat_ecfin_employment_expectations_ea20.csv": "https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data/ei_bsee_m_r2?geo=EA20&indic=BS-EEI-I&s_adj=SA&unit=INX",
    "eurostat_ecfin_services_employment_expectations_ea20.csv": "https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data/ei_bsee_m_r2?geo=EA20&indic=BS-SEEM-BAL&s_adj=SA&unit=BAL",
    "ecb_ces_income_expectations_12m_median.csv": "https://data-api.ecb.europa.eu/service/data/CES/M.Z18.ALL.T.C3220.NUM_VAR.WM?format=csvdata",
    "ecb_ces_unemployment_expectations_12m_median.csv": "https://data-api.ecb.europa.eu/service/data/CES/M.Z18.ALL.T.C4031.NUM_VAR.WM?format=csvdata",
    "eurostat_sts_industry_wage_bill_de.csv": "https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data/sts_inlb_m?geo=DE&indic_bt=WAGE&nace_r2=B-E36&s_adj=NSA&unit=I21",
}


@dataclass(frozen=True)
class Candidate:
    candidate_id: str
    variable: str
    label: str
    side: str
    role: str
    target_variable: str
    target_transform: str
    economic_relevance: int
    interpretability: int
    source: str
    source_file: str
    source_url: str
    decision: str
    decision_reason: str
    conceptual_object: str
    retained_limitations: str


CANDIDATES = (
    Candidate(
        "housing_house_purchase_growth",
        "ecb_house_purchase_growth_yoy",
        "ECB lending for house purchase, annual growth",
        "housing",
        "canonical",
        "ln_house_price_de_real_q_observed",
        "quarterly_yoy_growth",
        5,
        5,
        "ECB BSI",
        "ecb_bsi_house_purchase_annual_growth.csv",
        SOURCE_URLS["ecb_bsi_house_purchase_annual_growth.csv"],
        "accepted_canonical",
        "Direct monthly housing-finance series with full sample coverage; it proxies mortgage-credit transmission, not house prices themselves.",
        "Monthly growth in MFI loans for house purchase; housing-finance transmission.",
        "It is a credit-growth proxy, not a direct affordability, price, rent, or welfare measure.",
    ),
    Candidate(
        "housing_house_purchase_new_loans",
        "ln_ecb_house_purchase_pure_new_loans",
        "ECB pure new loans for house purchase",
        "housing",
        "robustness",
        "ln_house_price_de_real_q_observed",
        "quarterly_level",
        5,
        4,
        "ECB MIR",
        "ecb_mir_house_purchase_pure_new_loans.csv",
        SOURCE_URLS["ecb_mir_house_purchase_pure_new_loans.csv"],
        "accepted_robustness",
        "Direct housing-finance flow, but available only from 2017-08 in the pulled ECB vintage.",
        "Monthly flow of pure new house-purchase loans; mortgage-origination transmission.",
        "Short sample beginning in 2017 limits regime and pre-QE comparisons.",
    ),
    Candidate(
        "housing_household_loans_stock",
        "ln_hh_loans_ea_stock",
        "ECB adjusted loans to households",
        "housing",
        "fallback",
        "ln_house_price_de_real_q_observed",
        "quarterly_level",
        3,
        3,
        "ECB BSI local workbook",
        "4. loans to euro area households granted by MFIs .xlsx",
        "https://data.ecb.europa.eu/data/datasets/BSI/BSI.M.U2.N.A.A20T.A.1.U2.2250.Z01.E",
        "rejected_for_canonical",
        "Monthly and continuous, but it covers all household loans rather than house-purchase credit specifically.",
        "Broad household credit stock.",
        "Too broad for the housing-finance comparison; retained only as a background credit variable in LP outputs.",
    ),
    Candidate(
        "comp_wage_tracker_ex_oneoffs",
        "ecb_wage_tracker_ex_oneoffs_real_yoy",
        "ECB Wage Tracker excluding one-off payments, real",
        "compensation",
        "canonical",
        "ln_compensation_ea20_real_q_observed",
        "quarterly_yoy_growth",
        5,
        5,
        "ECB EWT",
        "ecb_wage_tracker_ex_oneoffs.csv",
        SOURCE_URLS["ecb_wage_tracker_ex_oneoffs.csv"],
        "accepted_canonical",
        "Best monthly compensation-side proxy for persistent real negotiated wage pressure; not actual compensation per employee.",
        "Monthly real negotiated wage pressure excluding one-off payments.",
        "It is negotiated wage pressure, not observed total compensation per employee, payroll income, welfare, or redistribution.",
    ),
    Candidate(
        "comp_wage_tracker_headline",
        "ecb_wage_tracker_headline_real_yoy",
        "ECB Wage Tracker headline, real",
        "compensation",
        "robustness",
        "ln_compensation_ea20_real_q_observed",
        "quarterly_yoy_growth",
        5,
        4,
        "ECB EWT",
        "ecb_wage_tracker_headline.csv",
        SOURCE_URLS["ecb_wage_tracker_headline.csv"],
        "accepted_robustness",
        "Monthly negotiated wage signal including smoothed one-off payments; useful check around the main wage tracker.",
        "Monthly real negotiated wage pressure including smoothed one-off payments.",
        "One-off treatment can mechanically change short-horizon wage dynamics.",
    ),
    Candidate(
        "comp_wage_tracker_unsmoothed",
        "ecb_wage_tracker_unsmoothed_oneoffs_real_yoy",
        "ECB Wage Tracker with unsmoothed one-off payments, real",
        "compensation",
        "robustness",
        "ln_compensation_ea20_real_q_observed",
        "quarterly_yoy_growth",
        4,
        3,
        "ECB EWT",
        "ecb_wage_tracker_unsmoothed_oneoffs.csv",
        SOURCE_URLS["ecb_wage_tracker_unsmoothed_oneoffs.csv"],
        "accepted_robustness",
        "Real monthly wage tracker, but one-off payments make it a noisier compensation proxy.",
        "Monthly real negotiated wage pressure including unsmoothed one-off payments.",
        "Noisier one-off payments reduce persistence interpretability.",
    ),
    Candidate(
        "comp_wage_tracker_ex_oneoffs_ma3",
        "ecb_wage_tracker_ex_oneoffs_real_yoy_ma3",
        "ECB Wage Tracker excluding one-offs, real 3-month average",
        "compensation",
        "robustness",
        "ln_compensation_ea20_real_q_observed",
        "quarterly_yoy_growth",
        5,
        5,
        "ECB EWT + EA HICP",
        "ecb_wage_tracker_ex_oneoffs.csv",
        SOURCE_URLS["ecb_wage_tracker_ex_oneoffs.csv"],
        "accepted_robustness",
        "Rolling real wage-pressure proxy smooths month-specific noise without fabricating observations.",
        "Three-month average of monthly real negotiated wage pressure excluding one-off payments.",
        "Smoothing is transparent and only uses observed current/past monthly data; it is not a distinct source series.",
    ),
    Candidate(
        "comp_wage_tracker_ex_oneoffs_momentum",
        "ecb_wage_tracker_ex_oneoffs_real_yoy_momentum_3m",
        "ECB Wage Tracker excluding one-offs, real 3-month momentum",
        "compensation",
        "diagnostic",
        "ln_compensation_ea20_real_q_observed",
        "quarterly_yoy_growth",
        4,
        4,
        "ECB EWT + EA HICP",
        "ecb_wage_tracker_ex_oneoffs.csv",
        SOURCE_URLS["ecb_wage_tracker_ex_oneoffs.csv"],
        "accepted_diagnostic",
        "Momentum captures acceleration in real negotiated wage pressure and is useful for signal-timing checks.",
        "Three-month change in real negotiated wage pressure excluding one-off payments.",
        "Momentum is mechanically noisier than the level and is not used as the primary compensation proxy.",
    ),
    Candidate(
        "comp_sts_industry_wage_bill_de_real",
        "eurostat_sts_industry_wage_bill_de_real_yoy",
        "Eurostat German industry wage bill, real annual growth",
        "compensation",
        "robustness",
        "ln_compensation_ea20_real_q_observed",
        "quarterly_yoy_growth",
        4,
        3,
        "Eurostat STS",
        "eurostat_sts_industry_wage_bill_de.csv",
        SOURCE_URLS["eurostat_sts_industry_wage_bill_de.csv"],
        "accepted_robustness",
        "True monthly wage-bill series; adds a hard observed payroll-cost proxy, but only for German industry.",
        "Monthly gross wages and salaries index for German industry, deflated by German HICP annual inflation.",
        "Sector/geography are narrow; the series measures wage bill, not compensation per employee.",
    ),
    Candidate(
        "comp_unemployment_tightness",
        "eurostat_labor_tightness_unemployment_inv",
        "Eurostat unemployment inverse labor-tightness proxy",
        "compensation",
        "indirect",
        "ln_compensation_ea20_real_q_observed",
        "quarterly_yoy_growth",
        3,
        4,
        "Eurostat LFS",
        "eurostat_unemployment_ea21_sa.csv",
        SOURCE_URLS["eurostat_unemployment_ea21_sa.csv"],
        "accepted_indirect",
        "True monthly labor-tightness proxy; higher transformed value means lower unemployment and tighter labor markets.",
        "Negative of the monthly seasonally adjusted euro-area unemployment rate.",
        "Labor tightness is an indirect wage-pressure proxy, not compensation or wage growth.",
    ),
    Candidate(
        "comp_employment_expectations",
        "eurostat_ecfin_eei_ea20",
        "European Commission employment expectations indicator",
        "compensation",
        "indirect",
        "ln_compensation_ea20_real_q_observed",
        "quarterly_yoy_growth",
        3,
        4,
        "Eurostat/DG ECFIN BCS",
        "eurostat_ecfin_employment_expectations_ea20.csv",
        SOURCE_URLS["eurostat_ecfin_employment_expectations_ea20.csv"],
        "accepted_indirect",
        "Timely monthly expected-employment pressure proxy from harmonised business surveys.",
        "Monthly euro-area employment expectations indicator over the next three months.",
        "Survey expectations are indirect wage-pressure evidence and can revise with seasonal adjustment.",
    ),
    Candidate(
        "comp_services_employment_expectations",
        "eurostat_ecfin_services_employment_expectations_ea20",
        "European Commission services employment expectations",
        "compensation",
        "indirect",
        "ln_compensation_ea20_real_q_observed",
        "quarterly_yoy_growth",
        3,
        4,
        "Eurostat/DG ECFIN BCS",
        "eurostat_ecfin_services_employment_expectations_ea20.csv",
        SOURCE_URLS["eurostat_ecfin_services_employment_expectations_ea20.csv"],
        "accepted_indirect",
        "Monthly services-sector employment expectations add a services wage-pressure timing proxy.",
        "Monthly euro-area services employment expectations balance.",
        "It captures expected services employment, not observed services wages.",
    ),
    Candidate(
        "comp_ces_real_income_expectations",
        "ecb_ces_real_income_expectations_12m_median",
        "ECB CES real household income expectations",
        "compensation",
        "diagnostic_short_sample",
        "ln_compensation_ea20_real_q_observed",
        "quarterly_yoy_growth",
        3,
        4,
        "ECB CES",
        "ecb_ces_income_expectations_12m_median.csv",
        SOURCE_URLS["ecb_ces_income_expectations_12m_median.csv"],
        "accepted_diagnostic_short_sample",
        "Monthly household income-pressure expectations are observable, but the public aggregate sample starts late.",
        "Weighted median expected household income growth over the next 12 months minus HICP inflation.",
        "Short public CES sample makes it unsuitable as the main long-window compensation proxy.",
    ),
    Candidate(
        "comp_ces_unemployment_expectations",
        "ecb_ces_unemployment_expectations_12m_median",
        "ECB CES expected unemployment rate",
        "compensation",
        "diagnostic_short_sample",
        "ln_compensation_ea20_real_q_observed",
        "quarterly_yoy_growth",
        2,
        4,
        "ECB CES",
        "ecb_ces_unemployment_expectations_12m_median.csv",
        SOURCE_URLS["ecb_ces_unemployment_expectations_12m_median.csv"],
        "accepted_diagnostic_short_sample",
        "Monthly household labor-market expectations are useful as a short-window expectation diagnostic.",
        "Weighted median expected unemployment rate over the next 12 months.",
        "Short sample and expectation construct prevent main compensation use.",
    ),
    Candidate(
        "comp_wage_tracker_coverage",
        "ecb_wage_tracker_coverage_pct",
        "ECB Wage Tracker coverage",
        "compensation",
        "rejected",
        "ln_compensation_ea20_real_q_observed",
        "quarterly_yoy_growth",
        1,
        5,
        "ECB EWT",
        "ecb_wage_tracker_coverage.csv",
        SOURCE_URLS["ecb_wage_tracker_coverage.csv"],
        "rejected_not_compensation",
        "Coverage is a source-quality diagnostic, not a wage-pressure response variable.",
        "Share/coverage diagnostic for the ECB Wage Tracker.",
        "Useful for revision and representativeness checks only.",
    ),
    Candidate(
        "comp_retail_volume",
        "ln_retail_de_chained_index",
        "German retail volume",
        "compensation",
        "rejected",
        "ln_compensation_ea20_real_q_observed",
        "quarterly_level",
        1,
        2,
        "Eurostat local workbook",
        "10 volume of sales in wholesale and retail trade .xlsx",
        "",
        "rejected",
        "Monthly real-activity/purchasing-power proxy, not a compensation or wage construct.",
        "Retail-volume real activity.",
        "It is not a wage, payroll, labor-income, or compensation construct.",
    ),
    Candidate(
        "housing_house_price_quarterly_observed",
        "ln_house_price_de_real_q_observed",
        "German real house-price index, quarter-end observed",
        "housing",
        "rejected",
        "ln_house_price_de_real_q_observed",
        "quarterly_level",
        5,
        5,
        "OECD/BIS/official local quarterly source",
        "germany_residential_prices_quarterly.csv",
        "",
        "rejected_nonmonthly",
        "Conceptually direct, but observed only at quarter-end; the monthly thesis layer does not interpolate it.",
        "Quarterly observed real house-price level.",
        "Sparse quarter-end observations are not a valid monthly transmission proxy without interpolation.",
    ),
    Candidate(
        "comp_compensation_per_employee_quarterly_observed",
        "ln_compensation_ea20_real_q_observed",
        "Euro area real compensation per employee, quarter-end observed",
        "compensation",
        "rejected",
        "ln_compensation_ea20_real_q_observed",
        "quarterly_level",
        5,
        5,
        "ECB/Eurostat local quarterly workbook",
        "9. Compensation per employee.xlsx",
        "",
        "rejected_nonmonthly",
        "Conceptually direct, but observed only at quarter-end; the monthly thesis layer does not interpolate it.",
        "Quarterly observed real compensation per employee.",
        "Sparse quarter-end observations are not a valid monthly compensation proxy without interpolation.",
    ),
)

UNAVAILABLE_CANDIDATES = (
    ("residential REIT index", "housing", "not in local official raw set; broad equity alternatives would weaken housing-specific interpretation"),
    ("property-company equity index", "housing", "not in local official raw set; DAX is too broad to stand in for property companies"),
    ("Eurostat house-price expectations", "housing", "not in local raw set as a monthly official series"),
    ("mortgage approval volumes", "housing", "not in local raw set; ECB portal contains related MIR/BSI house-purchase lending volumes instead"),
    ("housing sentiment indicators", "housing", "not in local raw set as a reproducible monthly official series"),
    ("construction-sector equity index", "housing", "not in local official raw set"),
    ("housing-finance conditions", "housing", "not in local raw set beyond house-purchase lending volumes"),
    ("mortgage spreads", "housing", "not in local raw set as a reproducible monthly official spread series"),
    ("new mortgage issuance", "housing", "proxied by ECB MIR pure new loans for house purchase where available"),
    ("residential lending standards", "housing", "ECB Bank Lending Survey is quarterly and therefore not accepted as a monthly LP response"),
    ("Eurostat labour-cost index", "compensation", "quarterly, not a monthly compensation proxy"),
    ("Eurostat compensation per employee", "compensation", "national-accounts compensation per employee is quarterly, not monthly"),
    ("Eurostat job vacancy rate", "compensation", "job vacancy statistics are quarterly, so they are rejected for monthly LP responses"),
    ("sector-specific ECB negotiated wages", "compensation", "ECB EWT API exposes only total-economy monthly wage-tracker series in this vintage"),
    ("services ECB negotiated wage pressure", "compensation", "no separate monthly services EWT wage series is exposed; services employment expectations are retained only as an indirect proxy"),
    ("core negotiated wage pressure outside ex-one-offs", "compensation", "the available monthly core-like EWT measure is the excluding-one-offs series; no additional official core EWT series is exposed"),
    ("Eurostat services wage bill", "compensation", "searched STS services wage-bill dimensions do not return usable euro-area/German monthly observations in the official API query"),
    ("Eurostat retail wage bill", "compensation", "searched STS trade wage-bill dimensions do not return usable euro-area/German monthly observations in the official API query"),
    ("payroll/employment-income micro proxy", "compensation", "no reproducible public monthly official euro-area payroll micro proxy was found"),
    ("Indeed wage tracker", "compensation", "not retained because the public official-source reproducibility standard is not met"),
    ("PMI employment subindices", "compensation", "not retained because the series are proprietary and not reproducible from official public sources"),
    ("negotiated pay settlements outside ECB Wage Tracker", "compensation", "not in local raw set"),
    ("monthly compensation per employee", "compensation", "not available as a real monthly series in local or pulled official sources"),
)


def ensure_dirs() -> None:
    for path in (
        OUTPUT_DIR,
        FINAL_DIAGNOSTICS,
        FINAL_PROXY_VALIDATION,
        FINAL_COMPENSATION,
        FINAL_COMPENSATION_FIGURES,
        DOCS_DIR,
        PROXY_RAW_DIR,
    ):
        path.mkdir(parents=True, exist_ok=True)


def load_monthly() -> pd.DataFrame:
    data = pd.read_csv(MONTHLY_DATASET, parse_dates=["date"]).sort_values("date").reset_index(drop=True)
    for column in data.columns:
        if column not in {"date", "month", "quarter", "lp_monthly_regime", "regime", "identification_regime"}:
            data[column] = pd.to_numeric(data[column], errors="coerce")
    return data


def month_count(start: pd.Timestamp, end: pd.Timestamp) -> int:
    return (int(end.year) - int(start.year)) * 12 + int(end.month) - int(start.month) + 1


def coverage_metrics(data: pd.DataFrame, variable: str) -> dict[str, object]:
    if variable not in data.columns:
        return {
            "available": False,
            "observations": 0,
            "missing": data.shape[0],
            "sample_start": "",
            "sample_end": "",
            "monthly_continuity": 0.0,
            "missingness_share": 1.0,
            "max_month_gap": np.nan,
        }
    observed = data.loc[data[variable].notna(), ["date", variable]].copy()
    if observed.empty:
        return {
            "available": False,
            "observations": 0,
            "missing": data.shape[0],
            "sample_start": "",
            "sample_end": "",
            "monthly_continuity": 0.0,
            "missingness_share": 1.0,
            "max_month_gap": np.nan,
        }
    dates = observed["date"].sort_values()
    expected = month_count(dates.iloc[0], dates.iloc[-1])
    month_index = dates.dt.to_period("M").astype(int)
    gaps = month_index.diff().dropna()
    return {
        "available": True,
        "observations": int(observed.shape[0]),
        "missing": int(data.shape[0] - observed.shape[0]),
        "sample_start": str(dates.iloc[0].date()),
        "sample_end": str(dates.iloc[-1].date()),
        "monthly_continuity": float(observed.shape[0] / expected) if expected else np.nan,
        "missingness_share": float(1.0 - observed.shape[0] / data.shape[0]),
        "max_month_gap": int(gaps.max()) if not gaps.empty else 1,
    }


def candidate_volatility(data: pd.DataFrame, variable: str) -> float:
    if variable not in data.columns:
        return np.nan
    series = data[variable].dropna().astype(float)
    if series.shape[0] < 3:
        return np.nan
    return float(series.diff().dropna().std())


def quarterly_corr(data: pd.DataFrame, candidate: Candidate) -> tuple[float, str, int]:
    if candidate.variable not in data.columns or candidate.target_variable not in data.columns:
        return np.nan, "not_available", 0
    q = (
        data.groupby("quarter", as_index=False)
        .agg(proxy=(candidate.variable, "mean"), target=(candidate.target_variable, "last"))
        .sort_values("quarter")
    )
    if candidate.target_transform == "quarterly_yoy_growth":
        q["target_metric"] = 100.0 * (q["target"] - q["target"].shift(4))
        method = "proxy_level_to_quarterly_target_yoy_log_growth"
    else:
        q["target_metric"] = q["target"]
        method = "proxy_quarter_average_to_quarterly_target_level"
    clean = q.dropna(subset=["proxy", "target_metric"])
    if clean.shape[0] < 8 or clean["proxy"].nunique() < 3 or clean["target_metric"].nunique() < 3:
        return np.nan, method, int(clean.shape[0])
    return float(clean["proxy"].corr(clean["target_metric"])), method, int(clean.shape[0])


def add_lags(data: pd.DataFrame, variable: str) -> pd.DataFrame:
    frame = data.copy()
    for column in (variable, "inflation_ea20_mom", "dfr_mavg"):
        if column not in frame.columns:
            continue
        for lag in (1, 2):
            frame[f"L{lag}_{column}"] = frame[column].shift(lag)
    return frame


def fit_lp(data: pd.DataFrame, response: str, shock: str, horizon: int, min_obs: int = 48) -> dict[str, float]:
    if response not in data.columns or shock not in data.columns:
        return {"coef": np.nan, "se": np.nan, "p": np.nan, "nobs": 0}
    frame = add_lags(data, response)
    outcome = f"lp_{response}_h{horizon}"
    frame[outcome] = frame[response].shift(-horizon) - frame[response].shift(1)
    controls = [
        f"L1_{response}",
        f"L2_{response}",
        "L1_inflation_ea20_mom",
        "L2_inflation_ea20_mom",
        "L1_dfr_mavg",
        "L2_dfr_mavg",
    ]
    controls = [column for column in controls if column in frame.columns]
    required = [outcome, shock, *controls]
    clean = frame.dropna(subset=required)
    if clean.shape[0] < max(min_obs, len(controls) + 12) or clean[shock].nunique(dropna=True) < 3:
        return {"coef": np.nan, "se": np.nan, "p": np.nan, "nobs": int(clean.shape[0])}
    y = clean[outcome].to_numpy(dtype=float)
    x, names = add_constant(clean[[shock, *controls]].to_numpy(dtype=float), [shock, *controls])
    model = fit_ols_hac(y, x, names, maxlags=horizon + 1)
    return {
        "coef": float(model.params[shock]),
        "se": float(model.bse[shock]),
        "p": float(model.pvalues[shock]),
        "nobs": int(clean.shape[0]),
    }


def transmission_metrics(data: pd.DataFrame, variable: str) -> dict[str, object]:
    shock_sd = float(data.loc[data[PRIMARY_SHOCK].notna(), PRIMARY_SHOCK].std())
    rows = []
    for horizon in HORIZONS:
        fit = fit_lp(data, variable, PRIMARY_SHOCK, horizon)
        rows.append({"horizon": horizon, **fit})
    frame = pd.DataFrame(rows)
    signs = np.sign(frame["coef"].dropna())
    signs = signs[signs != 0]
    majority_share = np.nan
    majority_sign = ""
    if not signs.empty:
        majority = signs.value_counts().idxmax()
        majority_share = float((signs == majority).mean())
        majority_sign = "positive" if majority > 0 else "negative"
    h6 = frame.loc[frame["horizon"].eq(6)].iloc[0].to_dict()
    return {
        "h6_response_1sd": h6.get("coef", np.nan) * shock_sd if pd.notna(h6.get("coef", np.nan)) else np.nan,
        "h6_se_1sd": h6.get("se", np.nan) * shock_sd if pd.notna(h6.get("se", np.nan)) else np.nan,
        "h6_p_value": h6.get("p", np.nan),
        "h6_nobs": int(h6.get("nobs", 0)),
        "horizon_sign_stability": majority_share,
        "majority_response_sign": majority_sign,
    }


def event_clean_shocks(data: pd.DataFrame) -> pd.DataFrame:
    if not EVENT_SCREEN.exists():
        return data
    screen = pd.read_csv(EVENT_SCREEN, parse_dates=["event_date"])
    screen = screen.loc[screen["monthly_identification_window"]].copy()
    screen["date"] = screen["event_date"].dt.to_period("M").dt.to_timestamp("M")
    screen["target_easing"] = -pd.to_numeric(screen["target_factor"], errors="coerce")
    clean = (
        screen.loc[~screen["contamination_flag"]]
        .groupby("date", as_index=False)["target_easing"]
        .sum()
        .rename(columns={"target_easing": "target_factor_clean_monthly_easing"})
    )
    contaminated = (
        screen.loc[screen["contamination_flag"]]
        .groupby("date", as_index=False)["target_easing"]
        .sum()
        .rename(columns={"target_easing": "target_factor_contaminated_monthly_easing"})
    )
    out = data.merge(clean, on="date", how="left").merge(contaminated, on="date", how="left")
    out["target_factor_clean_monthly_easing"] = out["target_factor_clean_monthly_easing"].fillna(0.0)
    out["target_factor_contaminated_monthly_easing"] = out["target_factor_contaminated_monthly_easing"].fillna(0.0)
    return out


def contamination_metric(data: pd.DataFrame, variable: str) -> dict[str, object]:
    all_fit = fit_lp(data, variable, PRIMARY_SHOCK, 6)
    clean_fit = fit_lp(data, variable, "target_factor_clean_monthly_easing", 6)
    contaminated_fit = fit_lp(data, variable, "target_factor_contaminated_monthly_easing", 6)
    all_coef = all_fit["coef"]
    clean_coef = clean_fit["coef"]
    contaminated_coef = contaminated_fit["coef"]
    if pd.isna(all_coef) or pd.isna(clean_coef):
        ratio = np.nan
        flag = "not_enough_clean_event_variation"
    else:
        ratio = float(abs(clean_coef - all_coef) / max(abs(all_coef), 1e-12))
        flag = "stable_to_info_screen" if np.sign(clean_coef) == np.sign(all_coef) and ratio <= 1.0 else "sensitive_to_info_screen"
    return {
        "h6_clean_event_coef": clean_coef,
        "h6_contaminated_event_coef": contaminated_coef,
        "information_effect_susceptibility": ratio,
        "information_effect_flag": flag,
    }


def subperiod_stability(data: pd.DataFrame, variable: str) -> float:
    periods = [
        data.loc[data["date"] <= pd.Timestamp("2019-12-31")],
        data.loc[data["date"] >= pd.Timestamp("2020-01-31")],
    ]
    signs = []
    for subset in periods:
        fit = fit_lp(subset, variable, PRIMARY_SHOCK, 6, min_obs=24)
        if pd.notna(fit["coef"]) and not math.isclose(float(fit["coef"]), 0.0, abs_tol=1e-12):
            signs.append(np.sign(fit["coef"]))
    if not signs:
        return np.nan
    return float(max(signs.count(1.0), signs.count(-1.0)) / len(signs))


def regime_stability(data: pd.DataFrame, variable: str) -> float:
    if "lp_monthly_regime" not in data.columns:
        return np.nan
    signs = []
    for _, subset in data.groupby("lp_monthly_regime", dropna=False):
        fit = fit_lp(subset, variable, PRIMARY_SHOCK, 6, min_obs=20)
        if pd.notna(fit["coef"]) and not math.isclose(float(fit["coef"]), 0.0, abs_tol=1e-12):
            signs.append(np.sign(fit["coef"]))
    if not signs:
        return np.nan
    return float(max(signs.count(1.0), signs.count(-1.0)) / len(signs))


def continuity_score(value: float) -> int:
    if pd.isna(value):
        return 0
    if value >= 0.98:
        return 5
    if value >= 0.90:
        return 4
    if value >= 0.75:
        return 3
    if value >= 0.50:
        return 2
    return 1


def corr_score(value: float) -> int:
    if pd.isna(value):
        return 0
    absolute = abs(float(value))
    if absolute >= 0.7:
        return 5
    if absolute >= 0.5:
        return 4
    if absolute >= 0.3:
        return 3
    if absolute >= 0.15:
        return 2
    return 1


def missingness_score(value: float) -> int:
    if pd.isna(value):
        return 0
    if value <= 0.05:
        return 5
    if value <= 0.10:
        return 4
    if value <= 0.25:
        return 3
    if value <= 0.50:
        return 2
    return 1


def volatility_score(value: float) -> int:
    if pd.isna(value) or value <= 0:
        return 0
    if value <= 0.01:
        return 3
    if value <= 0.25:
        return 5
    if value <= 2.5:
        return 4
    if value <= 10:
        return 3
    return 2


def ar1_stationarity_score(data: pd.DataFrame, variable: str) -> tuple[float, int]:
    if variable not in data.columns:
        return np.nan, 0
    series = data[variable].dropna().astype(float)
    if series.shape[0] < 12 or series.nunique() < 3:
        return np.nan, 0
    ar1 = float(series.autocorr(lag=1))
    abs_ar1 = abs(ar1)
    if pd.isna(abs_ar1):
        return np.nan, 0
    if abs_ar1 <= 0.80:
        score = 5
    elif abs_ar1 <= 0.90:
        score = 4
    elif abs_ar1 <= 0.97:
        score = 3
    elif abs_ar1 <= 0.99:
        score = 2
    else:
        score = 1
    return ar1, score


def volatility_noise_ratio(data: pd.DataFrame, variable: str) -> tuple[float, int]:
    if variable not in data.columns:
        return np.nan, 0
    series = data[variable].dropna().astype(float)
    if series.shape[0] < 12:
        return np.nan, 0
    signal = float(series.rolling(12, min_periods=6).mean().dropna().std())
    noise = float(series.diff().dropna().std())
    if not np.isfinite(signal) or not np.isfinite(noise) or noise <= 0:
        return np.nan, 0
    ratio = signal / noise
    if ratio >= 2.0:
        score = 5
    elif ratio >= 1.25:
        score = 4
    elif ratio >= 0.75:
        score = 3
    elif ratio >= 0.35:
        score = 2
    else:
        score = 1
    return float(ratio), score


def stable_seed(*parts: object) -> int:
    payload = "|".join(str(part) for part in parts).encode("utf-8")
    return int(hashlib.sha256(payload).hexdigest()[:8], 16)


def bootstrap_sign_robustness(
    data: pd.DataFrame,
    variable: str,
    horizon: int = 6,
    reps: int = 199,
    min_obs: int = 48,
) -> tuple[float, float, float, int]:
    if variable not in data.columns or PRIMARY_SHOCK not in data.columns:
        return np.nan, np.nan, np.nan, 0
    frame = add_lags(data, variable)
    outcome = f"lp_{variable}_h{horizon}"
    frame[outcome] = frame[variable].shift(-horizon) - frame[variable].shift(1)
    controls = [
        f"L1_{variable}",
        f"L2_{variable}",
        "L1_inflation_ea20_mom",
        "L2_inflation_ea20_mom",
        "L1_dfr_mavg",
        "L2_dfr_mavg",
    ]
    controls = [column for column in controls if column in frame.columns]
    required = [outcome, PRIMARY_SHOCK, *controls]
    clean = frame.dropna(subset=required)
    if clean.shape[0] < max(min_obs, len(controls) + 12) or clean[PRIMARY_SHOCK].nunique(dropna=True) < 3:
        return np.nan, np.nan, np.nan, int(clean.shape[0])
    y = clean[outcome].to_numpy(dtype=float)
    x, names = add_constant(clean[[PRIMARY_SHOCK, *controls]].to_numpy(dtype=float), [PRIMARY_SHOCK, *controls])
    model = fit_ols_hac(y, x, names, maxlags=horizon + 1)
    beta = np.asarray([model.params[name] for name in names], dtype=float)
    fitted = x @ beta
    resid = np.asarray(model.resid, dtype=float)
    resid = resid - np.nanmean(resid)
    point = float(model.params[PRIMARY_SHOCK])
    if math.isclose(point, 0.0, abs_tol=1e-12):
        return np.nan, np.nan, np.nan, int(clean.shape[0])
    rng = np.random.default_rng(stable_seed("comp_boot", variable, horizon, reps))
    draws: list[float] = []
    for _ in range(reps):
        weights = rng.choice([-1.0, 1.0], size=resid.shape[0])
        y_star = fitted + resid * weights
        try:
            boot = fit_ols_hac(y_star, x, names, maxlags=horizon + 1)
        except np.linalg.LinAlgError:
            continue
        coef = float(boot.params[PRIMARY_SHOCK])
        if np.isfinite(coef):
            draws.append(coef)
    if len(draws) < max(60, reps // 3):
        return np.nan, np.nan, np.nan, int(clean.shape[0])
    values = np.asarray(draws, dtype=float)
    sign_share = float((np.sign(values) == np.sign(point)).mean())
    return (
        sign_share,
        float(np.percentile(values, 5)),
        float(np.percentile(values, 95)),
        int(clean.shape[0]),
    )


def stability_score(value: float) -> int:
    if pd.isna(value):
        return 0
    if value >= 0.8:
        return 5
    if value >= 0.6:
        return 4
    if value >= 0.5:
        return 3
    return 1


def info_score(flag: str) -> int:
    if flag == "stable_to_info_screen":
        return 5
    if flag == "not_enough_clean_event_variation":
        return 2
    return 1


def build_manifest() -> pd.DataFrame:
    rows = []
    for path in sorted(PROXY_RAW_DIR.glob("*.csv")):
        if path.name in {"source_manifest.csv", "source_manifest_refinement.csv"}:
            continue
        hasher = hashlib.sha256()
        with path.open("rb") as handle:
            for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                hasher.update(chunk)
        rows.append(
            {
                "file_name": path.name,
                "path": str(path.relative_to(ROOT)),
                "source_url": SOURCE_URLS.get(path.name, ""),
                "size_bytes": path.stat().st_size,
                "sha256": hasher.hexdigest(),
                "raw_overwrite_policy": "never overwrite; add a new dated/vintage file instead",
            }
        )
    manifest = pd.DataFrame(rows)
    manifest.to_csv(PROXY_RAW_DIR / "source_manifest.csv", index=False)
    return manifest


def build_tournament() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    data = event_clean_shocks(load_monthly())
    rows = []
    for candidate in CANDIDATES:
        coverage = coverage_metrics(data, candidate.variable)
        corr, corr_method, corr_n = quarterly_corr(data, candidate)
        transmission = transmission_metrics(data, candidate.variable)
        contamination = contamination_metric(data, candidate.variable)
        sub_stability = subperiod_stability(data, candidate.variable)
        reg_stability = regime_stability(data, candidate.variable)
        volatility = candidate_volatility(data, candidate.variable)
        scores = {
            "economic_interpretability_score": candidate.economic_relevance,
            "monthly_continuity_score": continuity_score(coverage["monthly_continuity"]),
            "missingness_score": missingness_score(coverage["missingness_share"]),
            "volatility_realism_score": volatility_score(volatility),
            "response_stability_score": stability_score(transmission["horizon_sign_stability"]),
            "persistence_score": stability_score(transmission["horizon_sign_stability"]),
            "target_concept_correlation_score": corr_score(corr),
            "sensitivity_robustness_score": stability_score(sub_stability),
            "contamination_sensitivity_score": info_score(contamination["information_effect_flag"]),
            "regime_consistency_score": stability_score(reg_stability),
        }
        total_score = (
            4 * scores["economic_interpretability_score"]
            + 4 * scores["monthly_continuity_score"]
            + 3 * scores["missingness_score"]
            + 2 * scores["volatility_realism_score"]
            + 3 * scores["response_stability_score"]
            + 2 * scores["persistence_score"]
            + 3 * scores["target_concept_correlation_score"]
            + 2 * scores["sensitivity_robustness_score"]
            + 2 * scores["contamination_sensitivity_score"]
            + 2 * scores["regime_consistency_score"]
        )
        rows.append(
            {
                "candidate_id": candidate.candidate_id,
                "variable": candidate.variable,
                "label": candidate.label,
                "side": candidate.side,
                "role": candidate.role,
                "source": candidate.source,
                "source_file": candidate.source_file,
                "source_url": candidate.source_url,
                "target_variable": candidate.target_variable,
                "decision": candidate.decision,
                "decision_reason": candidate.decision_reason,
                "conceptual_object": candidate.conceptual_object,
                "retained_limitations": candidate.retained_limitations,
                "volatility_first_difference": volatility,
                "quarterly_target_correlation": corr,
                "quarterly_correlation_method": corr_method,
                "quarterly_correlation_observations": corr_n,
                "subperiod_sign_stability": sub_stability,
                "regime_sign_stability": reg_stability,
                "validation_score": total_score,
                **coverage,
                **transmission,
                **contamination,
                **scores,
            }
        )
    tournament = pd.DataFrame(rows).sort_values(["side", "decision", "validation_score"], ascending=[True, True, False])
    accepted = tournament.loc[tournament["decision"].str.startswith("accepted")].copy()
    rejected = pd.concat(
        [
            tournament.loc[~tournament["decision"].str.startswith("accepted")].copy(),
            pd.DataFrame(
                [
                    {
                        "candidate_id": f"unavailable_{i+1}",
                        "variable": "",
                        "label": label,
                        "side": side,
                        "role": "unavailable",
                        "source": "",
                        "source_file": "",
                        "source_url": "",
                        "target_variable": "",
                        "decision": "rejected_unavailable_or_nonmonthly",
                        "decision_reason": reason,
                        "conceptual_object": "Candidate proxy requested in the refinement agenda.",
                        "retained_limitations": "Not retained in the active monthly empirical layer.",
                    }
                    for i, (label, side, reason) in enumerate(UNAVAILABLE_CANDIDATES)
                ]
            ),
        ],
        ignore_index=True,
        sort=False,
    )
    return tournament, accepted, rejected


def fmt(value: object, digits: int = 3) -> str:
    if pd.isna(value):
        return ""
    if isinstance(value, (float, np.floating)):
        return f"{float(value):.{digits}f}"
    return str(value)


def markdown_table(frame: pd.DataFrame, columns: list[str], max_rows: int = 20) -> str:
    if frame.empty:
        return "_No available rows._"
    display = frame.loc[:, [column for column in columns if column in frame.columns]].head(max_rows)
    header = "| " + " | ".join(display.columns) + " |"
    divider = "| " + " | ".join(["---"] * len(display.columns)) + " |"
    rows = ["| " + " | ".join(fmt(row[column]) for column in display.columns) + " |" for _, row in display.iterrows()]
    return "\n".join([header, divider, *rows])


def write_doc(tournament: pd.DataFrame, accepted: pd.DataFrame, rejected: pd.DataFrame) -> None:
    canonical = accepted.loc[accepted["decision"].eq("accepted_canonical")].copy()
    text = f"""# Proxy Selection

This note records the monthly proxy choices. No quarterly housing or compensation series is turned into artificial monthly data. A proxy is used only when it is observed monthly or transparently constructed from monthly data.

## Main Selections

{markdown_table(canonical, ["side", "variable", "label", "conceptual_object", "source", "sample_start", "sample_end", "monthly_continuity", "quarterly_target_correlation", "horizon_sign_stability", "information_effect_flag", "validation_score"], 10)}

## Accepted Proxies

{markdown_table(accepted, ["side", "role", "variable", "label", "conceptual_object", "source", "observations", "monthly_continuity", "quarterly_target_correlation", "decision_reason"], 20)}

## Retained Limitations

{markdown_table(accepted, ["variable", "retained_limitations"], 20)}

## Rejected Or Unavailable Proxies

{markdown_table(rejected, ["side", "label", "variable", "decision", "decision_reason"], 40)}

## Selection Criteria

Each candidate is scored on economic relevance, monthly continuity, interpretability, response stability, correlation with the lower-frequency target, subperiod stability, and sensitivity to information-effect events. The score helps document measurement choices; it is not a mechanical claim filter.

## Interpretation Boundary

Accepted housing proxies measure housing finance, not residential prices. Accepted compensation proxies measure negotiated wage pressure, not compensation per employee or welfare. The final empirical claim may compare persistence in housing-finance and wage-pressure responses to ECB surprises, but exact housing-price, compensation, welfare, or redistribution magnitudes remain outside clean identification scope.

## Source Notes

- ECB house-purchase lending growth: `BSI.M.U2.Y.U.A22.A.I.U2.2250.Z01.A`.
- ECB pure new loans for house purchase: `MIR.M.U2.B.A2C.A.B.A.2250.EUR.P`.
- ECB Wage Tracker monthly series: headline `EWT.M.U2.N.WT.INWS._T.4F0.GY`; excluding one-offs `EWT.M.U2.N.WT.INWX._T.4F0.GY`; unsmoothed one-offs `EWT.M.U2.N.WT.INWR._T.4F0.GY`.
- Eurostat labour-cost indicators are quarterly and therefore rejected for the monthly comparison layer.
"""
    (DOCS_DIR / "proxy_validation.md").write_text(text, encoding="utf-8")


def proxy_scorecard(tournament: pd.DataFrame) -> pd.DataFrame:
    score_cols = [
        "economic_interpretability_score",
        "monthly_continuity_score",
        "missingness_score",
        "volatility_realism_score",
        "response_stability_score",
        "persistence_score",
        "target_concept_correlation_score",
        "sensitivity_robustness_score",
        "contamination_sensitivity_score",
        "regime_consistency_score",
    ]
    columns = [
        "candidate_id",
        "side",
        "role",
        "variable",
        "label",
        "decision",
        "validation_score",
        *score_cols,
        "conceptual_object",
        "retained_limitations",
        "decision_reason",
    ]
    return tournament.loc[:, [column for column in columns if column in tournament.columns]].copy()


def proxy_stability_metrics(tournament: pd.DataFrame) -> pd.DataFrame:
    columns = [
        "candidate_id",
        "side",
        "variable",
        "label",
        "decision",
        "h6_response_1sd",
        "h6_se_1sd",
        "h6_p_value",
        "horizon_sign_stability",
        "majority_response_sign",
        "subperiod_sign_stability",
        "regime_sign_stability",
        "h6_clean_event_coef",
        "h6_contaminated_event_coef",
        "information_effect_susceptibility",
        "information_effect_flag",
    ]
    return tournament.loc[:, [column for column in columns if column in tournament.columns]].copy()


def significance_stability(data: pd.DataFrame, variable: str) -> tuple[float, float, int]:
    fits = [fit_lp(data, variable, PRIMARY_SHOCK, horizon) for horizon in HORIZONS]
    frame = pd.DataFrame(fits)
    estimated = frame.loc[frame["coef"].notna()].copy()
    if estimated.empty:
        return np.nan, np.nan, 0
    p10_share = float((estimated["p"] <= 0.10).mean())
    p20_share = float((estimated["p"] <= 0.20).mean())
    return p10_share, p20_share, int(estimated.shape[0])


def cumulative_persistence_metric(data: pd.DataFrame, variable: str) -> tuple[float, float]:
    shock_sd = float(data.loc[data[PRIMARY_SHOCK].notna(), PRIMARY_SHOCK].std())
    coefs = []
    for horizon in HORIZONS:
        fit = fit_lp(data, variable, PRIMARY_SHOCK, horizon)
        if pd.notna(fit["coef"]):
            coefs.append(float(fit["coef"]) * shock_sd)
    if not coefs:
        return np.nan, np.nan
    cumulative = float(np.nansum(coefs))
    abs_cumulative = float(np.nansum(np.abs(coefs)))
    return cumulative, abs_cumulative


def rolling_window_sign_stability(data: pd.DataFrame, variable: str, horizon: int = 6, window: int = 84) -> float:
    if variable not in data.columns:
        return np.nan
    valid = data.dropna(subset=[variable, PRIMARY_SHOCK]).reset_index(drop=True)
    if valid.shape[0] < window:
        return np.nan
    signs = []
    for end in range(window, valid.shape[0] + 1):
        subset = valid.iloc[end - window : end].copy()
        fit = fit_lp(subset, variable, PRIMARY_SHOCK, horizon, min_obs=max(36, window // 2))
        if pd.notna(fit["coef"]) and not math.isclose(float(fit["coef"]), 0.0, abs_tol=1e-12):
            signs.append(np.sign(fit["coef"]))
    if not signs:
        return np.nan
    return float(max(signs.count(1.0), signs.count(-1.0)) / len(signs))


def recursive_window_sign_stability(data: pd.DataFrame, variable: str, horizon: int = 6, start: int = 72) -> float:
    if variable not in data.columns:
        return np.nan
    valid = data.dropna(subset=[variable, PRIMARY_SHOCK]).reset_index(drop=True)
    if valid.shape[0] < start:
        return np.nan
    signs = []
    for end in range(start, valid.shape[0] + 1, 6):
        subset = valid.iloc[:end].copy()
        fit = fit_lp(subset, variable, PRIMARY_SHOCK, horizon, min_obs=max(36, start // 2))
        if pd.notna(fit["coef"]) and not math.isclose(float(fit["coef"]), 0.0, abs_tol=1e-12):
            signs.append(np.sign(fit["coef"]))
    if not signs:
        return np.nan
    return float(max(signs.count(1.0), signs.count(-1.0)) / len(signs))


def revision_risk_score(source: str, role: str) -> int:
    source_l = source.lower()
    role_l = role.lower()
    if "eurostat" in source_l and "sts" in source_l:
        return 4
    if "eurostat" in source_l or "ecb ewt" in source_l:
        return 5
    if "ecb ces" in source_l:
        return 3
    if "diagnostic" in role_l:
        return 3
    return 4


def compensation_proxy_scorecard(tournament: pd.DataFrame, rejected: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    data = event_clean_shocks(load_monthly())
    comp = tournament.loc[tournament["side"].eq("compensation")].copy()
    rows = []
    for _, row in comp.iterrows():
        variable = str(row["variable"])
        cumulative, abs_cumulative = cumulative_persistence_metric(data, variable)
        p10_share, p20_share, estimated_horizons = significance_stability(data, variable)
        rolling_stability = rolling_window_sign_stability(data, variable)
        recursive_stability = recursive_window_sign_stability(data, variable)
        ar1, stationarity_score_value = ar1_stationarity_score(data, variable)
        signal_noise, signal_noise_score = volatility_noise_ratio(data, variable)
        boot_sign, boot_ci90_low, boot_ci90_high, boot_nobs = bootstrap_sign_robustness(data, variable)
        freq_score = 5 if row.get("monthly_continuity_score", 0) >= 4 and "q_observed" not in variable else 1
        revision_score = revision_risk_score(str(row.get("source", "")), str(row.get("role", "")))
        score_parts = {
            "shock_sensitivity_score": corr_score(abs(row.get("h6_response_1sd", np.nan))),
            "directional_consistency_score": stability_score(row.get("horizon_sign_stability", np.nan)),
            "cumulative_persistence_score": corr_score(abs_cumulative),
            "hac_significance_stability_score": stability_score(p10_share),
            "contamination_sensitivity_score": info_score(str(row.get("information_effect_flag", ""))),
            "rolling_window_stability_score": stability_score(rolling_stability),
            "recursive_window_stability_score": stability_score(recursive_stability),
            "economic_interpretability_score": row.get("economic_interpretability_score", 0),
            "frequency_integrity_score": freq_score,
            "revision_risk_score": revision_score,
            "regime_consistency_score": row.get("regime_consistency_score", 0),
            "stationarity_behavior_score": stationarity_score_value,
            "bootstrap_robustness_score": stability_score(boot_sign),
            "volatility_noise_ratio_score": signal_noise_score,
        }
        weighted_total = (
            3 * score_parts["shock_sensitivity_score"]
            + 3 * score_parts["directional_consistency_score"]
            + 3 * score_parts["cumulative_persistence_score"]
            + 2 * score_parts["hac_significance_stability_score"]
            + 2 * score_parts["contamination_sensitivity_score"]
            + 2 * score_parts["rolling_window_stability_score"]
            + 2 * score_parts["recursive_window_stability_score"]
            + 4 * score_parts["economic_interpretability_score"]
            + 4 * score_parts["frequency_integrity_score"]
            + 2 * score_parts["revision_risk_score"]
            + 2 * score_parts["regime_consistency_score"]
            + 2 * score_parts["stationarity_behavior_score"]
            + 2 * score_parts["bootstrap_robustness_score"]
            + 2 * score_parts["volatility_noise_ratio_score"]
        )
        canonical_status = "not_selected"
        if variable == "ecb_wage_tracker_ex_oneoffs_real_yoy":
            canonical_status = "primary_canonical_compensation_proxy"
        elif variable == "eurostat_sts_industry_wage_bill_de_real_yoy":
            canonical_status = "secondary_robustness_compensation_proxy"
        elif variable == "ecb_wage_tracker_ex_oneoffs_real_yoy_ma3":
            canonical_status = "noise_control_robustness_proxy"
        rows.append(
            {
                "candidate_id": row["candidate_id"],
                "variable": variable,
                "label": row["label"],
                "role": row["role"],
                "source": row["source"],
                "decision": row["decision"],
                "canonical_status": canonical_status,
                "acceptance_status": "accepted" if str(row["decision"]).startswith("accepted") else "rejected",
                "decision_reason": row["decision_reason"],
                "shock_sensitivity_h6_1sd": row.get("h6_response_1sd", np.nan),
                "directional_consistency": row.get("horizon_sign_stability", np.nan),
                "cumulative_persistence": cumulative,
                "abs_cumulative_persistence": abs_cumulative,
                "hac_p10_horizon_share": p10_share,
                "hac_p20_horizon_share": p20_share,
                "estimated_horizons": estimated_horizons,
                "contamination_sensitivity": row.get("information_effect_susceptibility", np.nan),
                "contamination_flag": row.get("information_effect_flag", ""),
                "rolling_window_stability": rolling_stability,
                "recursive_window_stability": recursive_stability,
                "ar1_stationarity_proxy": ar1,
                "bootstrap_sign_stability_h6": boot_sign,
                "bootstrap_ci90_low_h6_raw": boot_ci90_low,
                "bootstrap_ci90_high_h6_raw": boot_ci90_high,
                "bootstrap_nobs_h6": boot_nobs,
                "volatility_noise_ratio": signal_noise,
                "economic_interpretability": row.get("conceptual_object", ""),
                "frequency_integrity": "true_monthly_observed_or_transformed_from_true_monthly"
                if freq_score >= 4
                else "not_true_monthly_or_insufficient_monthly_integrity",
                "revision_risk": "low" if revision_score >= 4 else "medium",
                "regime_consistency": row.get("regime_sign_stability", np.nan),
                "residual_limitation": row.get("retained_limitations", ""),
                "compensation_proxy_score": weighted_total,
                "total_score": weighted_total,
                "frequency_validity_score": freq_score,
                "sample_coverage_score": row.get("monthly_continuity_score", 0),
                "stationarity_behavior_score": stationarity_score_value,
                "transmission_persistence_score": score_parts["cumulative_persistence_score"],
                "sign_consistency_score": score_parts["directional_consistency_score"],
                "regime_stability_score": row.get("regime_consistency_score", 0),
                "bootstrap_robustness_score": score_parts["bootstrap_robustness_score"],
                "clean_event_sensitivity_score": score_parts["contamination_sensitivity_score"],
                "volatility_noise_ratio_score": signal_noise_score,
                **score_parts,
            }
        )
    scorecard = pd.DataFrame(rows).sort_values("compensation_proxy_score", ascending=False)
    if not scorecard.empty:
        scorecard["rank"] = scorecard["compensation_proxy_score"].rank(method="dense", ascending=False).astype(int)
    rankings = scorecard.loc[
        scorecard["decision"].str.startswith("accepted"),
        [
            "rank",
            "candidate_id",
            "variable",
            "label",
            "role",
            "source",
            "decision",
            "canonical_status",
            "acceptance_status",
            "compensation_proxy_score",
            "total_score",
            "shock_sensitivity_h6_1sd",
            "directional_consistency",
            "cumulative_persistence",
            "hac_p10_horizon_share",
            "contamination_flag",
            "rolling_window_stability",
            "recursive_window_stability",
            "bootstrap_sign_stability_h6",
            "ar1_stationarity_proxy",
            "volatility_noise_ratio",
            "frequency_integrity",
            "revision_risk",
            "residual_limitation",
        ],
    ].copy()
    rankings = rankings.sort_values(["rank", "variable"])
    unavailable = rejected.loc[
        rejected["side"].eq("compensation") & rejected["role"].fillna("").eq("unavailable")
    ].copy()
    rejection_cols = [
        "candidate_id",
        "variable",
        "label",
        "role",
        "source",
        "source_file",
        "source_url",
        "decision",
        "decision_reason",
        "retained_limitations",
    ]
    rejections = pd.concat(
        [
            scorecard.loc[~scorecard["decision"].str.startswith("accepted")].rename(
                columns={"residual_limitation": "retained_limitations"}
            ),
            unavailable,
        ],
        ignore_index=True,
        sort=False,
    )
    rejections = rejections.loc[:, [column for column in rejection_cols if column in rejections.columns]].copy()
    return scorecard, rankings, rejections


def write_compensation_proxy_doc(scorecard: pd.DataFrame, rankings: pd.DataFrame, rejections: pd.DataFrame) -> None:
    canonical = rankings.loc[
        rankings["canonical_status"].isin(
            [
                "primary_canonical_compensation_proxy",
                "secondary_robustness_compensation_proxy",
                "noise_control_robustness_proxy",
            ]
        )
    ].copy()
    text = f"""# Compensation Proxy Selection

This note explains the monthly compensation-side measures. Every retained proxy is observed monthly or is a transparent transformation of monthly data.

## Main Compensation Selection

{markdown_table(canonical, ["rank", "canonical_status", "variable", "label", "role", "source", "compensation_proxy_score", "residual_limitation"], 12)}

The main compensation proxy is `ecb_wage_tracker_ex_oneoffs_real_yoy`: nominal ECB negotiated wage pressure excluding one-off payments minus HICP inflation. It is selected because it is the most interpretable monthly wage-pressure measure for persistent compensation dynamics, even when the mechanical scorecard ranks the narrower German industry wage-bill proxy higher on shock sensitivity.

The secondary check is `eurostat_sts_industry_wage_bill_de_real_yoy`. It is a hard observed monthly wage-bill indicator and therefore valuable as a payroll-cost check, but it is not the main proxy because its German industry scope is narrower than the euro-area negotiated-wage concept.

No composite index is selected. The available candidates measure different constructs, and combining negotiated wages, sector wage bills, labor-market tightness, and expectations would obscure the measurement boundary more than it would strengthen it. The 3-month wage-tracker average remains a transparent noise-control check, not a new source series.

## Full Ranking

{markdown_table(rankings, ["rank", "variable", "label", "role", "source", "canonical_status", "compensation_proxy_score", "directional_consistency", "cumulative_persistence", "hac_p10_horizon_share", "bootstrap_sign_stability_h6", "contamination_flag", "frequency_integrity"], 30)}

## Rejected Or Diagnostic-Only Candidates

{markdown_table(rejections, ["label", "variable", "decision", "decision_reason"], 40)}

## Selection Logic

The scorecard evaluates frequency, coverage, stationarity, persistence, sign consistency, regime stability, bootstrap checks, economic interpretation, clean-event sensitivity, and noise. The ranking documents measurement quality rather than searching for significance.

## Residual Limitations

Even the best monthly compensation proxies are not observed monthly compensation per employee. ECB wage trackers measure negotiated wage pressure, STS wage-bill data are sector/geography narrower, and CES income expectations have a short public sample. The thesis can compare financial-transmission persistence with wage-pressure persistence, but it cannot claim exact compensation, welfare, or redistribution magnitudes.
"""
    (DOCS_DIR / "compensation_proxy_validation.md").write_text(text, encoding="utf-8")
    (FINAL_COMPENSATION / "compensation_proxy_summary.md").write_text(text, encoding="utf-8")


def compensation_stability_metrics(scorecard: pd.DataFrame) -> pd.DataFrame:
    columns = [
        "rank",
        "candidate_id",
        "variable",
        "label",
        "decision",
        "canonical_status",
        "directional_consistency",
        "cumulative_persistence",
        "abs_cumulative_persistence",
        "hac_p10_horizon_share",
        "hac_p20_horizon_share",
        "bootstrap_sign_stability_h6",
        "bootstrap_ci90_low_h6_raw",
        "bootstrap_ci90_high_h6_raw",
        "contamination_sensitivity",
        "contamination_flag",
        "rolling_window_stability",
        "recursive_window_stability",
        "regime_consistency",
        "ar1_stationarity_proxy",
        "volatility_noise_ratio",
        "frequency_integrity",
        "residual_limitation",
    ]
    return scorecard.loc[:, [column for column in columns if column in scorecard.columns]].copy()


def write_compensation_rank_plot(rankings: pd.DataFrame) -> None:
    if rankings.empty:
        return
    display = rankings.sort_values("rank").head(10).copy()
    labels = display["label"].astype(str).str.replace(", real", "", regex=False)
    values = display["compensation_proxy_score"].astype(float)
    colors = [
        "#1f4e79" if status == "primary_canonical_compensation_proxy" else
        "#4f7f3f" if status == "secondary_robustness_compensation_proxy" else
        "#8aa6c1"
        for status in display["canonical_status"].astype(str)
    ]
    fig, ax = plt.subplots(figsize=(10.5, 5.8))
    ax.barh(range(len(display)), values, color=colors)
    ax.set_yticks(range(len(display)), labels)
    ax.invert_yaxis()
    ax.set_xlabel("Compensation proxy score")
    ax.set_title("Monthly Compensation Proxy Tournament")
    ax.grid(axis="x", alpha=0.22)
    ax.spines[["top", "right"]].set_visible(False)
    fig.tight_layout()
    fig.savefig(FINAL_COMPENSATION_FIGURES / "compensation_proxy_rankings.png", dpi=180)
    plt.close(fig)


def write_outputs(tournament: pd.DataFrame, accepted: pd.DataFrame, rejected: pd.DataFrame, manifest: pd.DataFrame) -> None:
    comp_scorecard, comp_rankings, comp_rejections = compensation_proxy_scorecard(tournament, rejected)
    comp_accepted = comp_scorecard.loc[comp_scorecard["decision"].str.startswith("accepted")].copy()
    comp_stability = compensation_stability_metrics(comp_scorecard)
    for target in (OUTPUT_DIR, FINAL_DIAGNOSTICS):
        tournament.to_csv(target / "proxy_validation_tournament.csv", index=False)
        accepted.to_csv(target / "proxy_validation_accepted.csv", index=False)
        rejected.to_csv(target / "proxy_validation_rejected.csv", index=False)
        proxy_scorecard(tournament).to_csv(target / "proxy_scorecard.csv", index=False)
        proxy_stability_metrics(tournament).to_csv(target / "proxy_stability_metrics.csv", index=False)
    comp_accepted.to_csv(FINAL_COMPENSATION / "accepted_compensation_proxies.csv", index=False)
    comp_rejections.to_csv(FINAL_COMPENSATION / "rejected_compensation_proxies.csv", index=False)
    comp_scorecard.to_csv(FINAL_COMPENSATION / "compensation_scorecard.csv", index=False)
    comp_stability.to_csv(FINAL_COMPENSATION / "compensation_stability_metrics.csv", index=False)
    comp_rankings.to_csv(FINAL_COMPENSATION / "compensation_proxy_rankings.csv", index=False)
    write_doc(tournament, accepted, rejected)
    write_compensation_proxy_doc(comp_scorecard, comp_rankings, comp_rejections)
    write_compensation_rank_plot(comp_rankings)
    manifest.to_csv(FINAL_DIAGNOSTICS / "monthly_proxy_source_manifest.csv", index=False)


def main() -> None:
    ensure_dirs()
    manifest = build_manifest()
    tournament, accepted, rejected = build_tournament()
    write_outputs(tournament, accepted, rejected, manifest)
    print(f"Wrote proxy tournament: {OUTPUT_DIR / 'proxy_validation_tournament.csv'}")
    print(f"Wrote proxy validation memo: {DOCS_DIR / 'proxy_validation.md'}")


if __name__ == "__main__":
    main()
