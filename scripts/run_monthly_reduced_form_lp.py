#!/usr/bin/env python3
from __future__ import annotations

import math
import os
import tempfile
import re
import hashlib
import sys
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
EVENT_SCREEN = ROOT / "results" / "final" / "diagnostics" / "information_effect_event_screen.csv"
OUTPUT_DIR = ROOT / "results" / "identification_rebuild"
FINAL_TABLES = ROOT / "results" / "final" / "tables"
FINAL_DIAGNOSTICS = ROOT / "results" / "final" / "diagnostics"
FINAL_FIGURES = ROOT / "results" / "final" / "figures"
FINAL_REGIME = ROOT / "results" / "final" / "regime"
FINAL_STABILITY = ROOT / "results" / "final" / "stability"
FINAL_ROBUSTNESS = ROOT / "results" / "final" / "robustness"
FINAL_UNCERTAINTY = ROOT / "results" / "final" / "uncertainty"
FINAL_MECHANISM = ROOT / "results" / "final" / "mechanism"
DOCS_DIR = ROOT / "results" / "final" / "memos"  # working notes; docs/ holds only the curated notes

FINAL_FIGURE_DIRS = {
    "baseline": FINAL_FIGURES / "baseline",
    "cumulative": FINAL_FIGURES / "cumulative",
    "uncertainty": FINAL_FIGURES / "uncertainty",
    "regimes": FINAL_FIGURES / "regimes",
    "stability": FINAL_FIGURES / "stability",
    "mechanism": FINAL_FIGURES / "mechanism",
    "compensation": FINAL_FIGURES / "compensation",
    "banking": FINAL_FIGURES / "banking",
}

PRIMARY_SHOCKS = (
    "target_factor_monthly_easing",
    "timing_factor_monthly_easing",
    "fg_factor_monthly_easing",
    "qe_factor_monthly_easing",
    "weighted_composite_monthly_easing",
)

RESPONSE_SPECS = {
    "ln_ecb_assets_ea_stock": ("ECB assets", "financial_liquidity", "monthly"),
    "ln_dax_real_de": ("real DAX", "financial_market", "monthly"),
    "ln_hh_loans_ea_stock": ("household credit", "financial_credit", "monthly_fallback"),
    "ln_nfc_loans_ea_stock": ("NFC credit", "financial_credit", "monthly"),
    "ecb_mir_mortgage_lending_rate": ("mortgage lending rate", "banking_lending_conditions", "monthly"),
    "ecb_mir_nfc_lending_rate": ("NFC lending rate", "banking_lending_conditions", "monthly"),
    "ecb_mir_mortgage_lending_spread_dfr": ("mortgage lending spread", "banking_lending_conditions", "monthly"),
    "ecb_mir_nfc_lending_spread_dfr": ("NFC lending spread", "banking_lending_conditions", "monthly"),
    "ln_retail_de_chained_index": ("retail volume", "real_activity", "monthly"),
    "ecb_house_purchase_growth_yoy": ("house-purchase lending growth", "housing_finance", "canonical_proxy"),
    "ln_ecb_house_purchase_pure_new_loans": ("pure new house-purchase loans", "housing_finance", "short_window_proxy"),
    "ecb_wage_tracker_ex_oneoffs_real_yoy": ("real wage tracker excl. one-offs", "compensation_proxy", "canonical_proxy"),
    "ecb_wage_tracker_headline_real_yoy": ("real wage tracker headline", "compensation_proxy", "robustness_proxy"),
    "ecb_wage_tracker_unsmoothed_oneoffs_real_yoy": (
        "real wage tracker unsmoothed one-offs",
        "compensation_proxy",
        "robustness_proxy",
    ),
    "ecb_wage_tracker_ex_oneoffs_real_yoy_ma3": ("real wage tracker excl. one-offs, 3m avg", "compensation_proxy", "robustness_proxy"),
    "ecb_wage_tracker_ex_oneoffs_real_yoy_momentum_3m": ("real wage tracker excl. one-offs, 3m momentum", "compensation_proxy", "diagnostic_proxy"),
    "eurostat_sts_industry_wage_bill_de_real_yoy": ("German industry real wage bill growth", "compensation_proxy", "sector_robustness_proxy"),
    "eurostat_labor_tightness_unemployment_inv": ("inverse unemployment labor tightness", "labor_tightness", "indirect_compensation_proxy"),
    "eurostat_ecfin_eei_ea20": ("employment expectations", "labor_tightness", "indirect_compensation_proxy"),
    "eurostat_ecfin_services_employment_expectations_ea20": (
        "services employment expectations",
        "labor_tightness",
        "indirect_compensation_proxy",
    ),
    "ecb_ces_real_income_expectations_12m_median": (
        "real household income expectations",
        "household_income_pressure",
        "short_window_diagnostic_proxy",
    ),
    "ecb_ces_unemployment_expectations_12m_median": (
        "CES expected unemployment",
        "labor_tightness",
        "short_window_diagnostic_proxy",
    ),
}

CANONICAL_COMPARISON_RESPONSES = (
    "ln_ecb_assets_ea_stock",
    "ln_dax_real_de",
    "ecb_mir_mortgage_lending_spread_dfr",
    "ecb_mir_nfc_lending_spread_dfr",
    "ln_nfc_loans_ea_stock",
    "ecb_house_purchase_growth_yoy",
    "ln_ecb_house_purchase_pure_new_loans",
    "ecb_wage_tracker_ex_oneoffs_real_yoy",
    "eurostat_sts_industry_wage_bill_de_real_yoy",
    "eurostat_ecfin_eei_ea20",
)

EXCLUDED_RESPONSES = {
    "ln_house_price_de_real_q_observed": "Quarterly housing series is sparse at quarter-end only; not interpolated.",
    "ln_compensation_ea20_real_q_observed": "Quarterly compensation series is sparse at quarter-end only; not interpolated.",
}

HORIZONS = (0, 1, 3, 6, 12, 24)
Z90 = 1.6448536269514722
Z68 = 0.994457883209753
Z95 = 1.959963984540054
BOOTSTRAP_REPLICATIONS = 399

SEQUENTIAL_PATHWAYS = (
    {
        "pathway": "mortgage_spread_to_house_purchase_growth",
        "upstream": "ecb_mir_mortgage_lending_spread_dfr",
        "downstream": "ecb_house_purchase_growth_yoy",
        "upstream_horizon": 1,
        "downstream_horizon": 6,
        "interpretation": "mortgage funding conditions and housing-finance timing",
    },
    {
        "pathway": "nfc_lending_spread_to_nfc_credit",
        "upstream": "ecb_mir_nfc_lending_spread_dfr",
        "downstream": "ln_nfc_loans_ea_stock",
        "upstream_horizon": 1,
        "downstream_horizon": 6,
        "interpretation": "corporate lending conditions and credit-expansion timing",
    },
    {
        "pathway": "liquidity_to_nfc_credit",
        "upstream": "ln_ecb_assets_ea_stock",
        "downstream": "ln_nfc_loans_ea_stock",
        "upstream_horizon": 1,
        "downstream_horizon": 3,
        "interpretation": "liquidity and bank-credit timing",
    },
    {
        "pathway": "household_credit_to_house_purchase_growth",
        "upstream": "ln_hh_loans_ea_stock",
        "downstream": "ecb_house_purchase_growth_yoy",
        "upstream_horizon": 1,
        "downstream_horizon": 3,
        "interpretation": "household credit and housing-finance timing",
    },
    {
        "pathway": "house_purchase_growth_to_new_mortgage_flow",
        "upstream": "ecb_house_purchase_growth_yoy",
        "downstream": "ln_ecb_house_purchase_pure_new_loans",
        "upstream_horizon": 1,
        "downstream_horizon": 3,
        "interpretation": "housing-credit growth and new mortgage-flow timing",
    },
    {
        "pathway": "nfc_credit_to_wage_pressure",
        "upstream": "ln_nfc_loans_ea_stock",
        "downstream": "ecb_wage_tracker_ex_oneoffs_real_yoy",
        "upstream_horizon": 2,
        "downstream_horizon": 6,
        "interpretation": "business-credit and negotiated-wage timing",
    },
    {
        "pathway": "employment_expectations_to_wage_pressure",
        "upstream": "eurostat_ecfin_eei_ea20",
        "downstream": "ecb_wage_tracker_ex_oneoffs_real_yoy",
        "upstream_horizon": 1,
        "downstream_horizon": 6,
        "interpretation": "labor-expectations and negotiated-wage timing",
    },
    {
        "pathway": "market_conditions_to_wage_pressure",
        "upstream": "ln_dax_real_de",
        "downstream": "ecb_wage_tracker_ex_oneoffs_real_yoy",
        "upstream_horizon": 1,
        "downstream_horizon": 6,
        "interpretation": "market-financing conditions and negotiated-wage timing",
    },
)


def ensure_dirs() -> None:
    for path in (
        OUTPUT_DIR,
        FINAL_TABLES,
        FINAL_DIAGNOSTICS,
        FINAL_FIGURES,
        FINAL_REGIME,
        FINAL_STABILITY,
        FINAL_ROBUSTNESS,
        FINAL_UNCERTAINTY,
        FINAL_MECHANISM,
        DOCS_DIR,
        *FINAL_FIGURE_DIRS.values(),
    ):
        path.mkdir(parents=True, exist_ok=True)


def load_data() -> pd.DataFrame:
    if not MONTHLY_DATASET.exists():
        raise FileNotFoundError(f"Missing monthly model dataset: {MONTHLY_DATASET}")
    data = pd.read_csv(MONTHLY_DATASET, parse_dates=["date"]).sort_values("date").reset_index(drop=True)
    for column in data.columns:
        if column not in {"date", "month", "quarter", "lp_monthly_regime", "regime", "identification_regime"}:
            data[column] = pd.to_numeric(data[column], errors="coerce")
    return add_clean_event_shocks(data)


def add_clean_event_shocks(data: pd.DataFrame) -> pd.DataFrame:
    if not EVENT_SCREEN.exists():
        return data
    screen = pd.read_csv(EVENT_SCREEN, parse_dates=["event_date"])
    screen = screen.loc[screen["monthly_identification_window"]].copy()
    screen["date"] = screen["event_date"].dt.to_period("M").dt.to_timestamp("M")
    screen["target_easing"] = -pd.to_numeric(screen["target_factor"], errors="coerce")
    pieces = []
    for flag, name in (
        (False, "target_factor_clean_monthly_easing"),
        (True, "target_factor_contaminated_monthly_easing"),
    ):
        piece = (
            screen.loc[screen["contamination_flag"].eq(flag)]
            .groupby("date", as_index=False)["target_easing"]
            .sum()
            .rename(columns={"target_easing": name})
        )
        pieces.append(piece)
    out = data.copy()
    for piece in pieces:
        out = out.merge(piece, on="date", how="left")
    for column in ("target_factor_clean_monthly_easing", "target_factor_contaminated_monthly_easing"):
        if column in out.columns:
            out[column] = out[column].fillna(0.0)
    return out


def response_meta(response: str) -> tuple[str, str, str]:
    return RESPONSE_SPECS.get(response, (response, "other", "monthly"))


def add_lags(data: pd.DataFrame, responses: tuple[str, ...]) -> pd.DataFrame:
    frame = data.copy()
    lag_sources = set(responses).union({"inflation_ea20_mom", "dfr_mavg"})
    for source in sorted(lag_sources):
        if source not in frame.columns:
            continue
        for lag in (1, 2):
            frame[f"L{lag}_{source}"] = frame[source].shift(lag)
    return frame


def outcome_column(response: str, horizon: int) -> str:
    return f"lp_{response}_h{horizon}"


def shock_scale(data: pd.DataFrame, shock: str) -> float:
    if shock not in data.columns:
        return np.nan
    series = data.loc[data[shock].notna(), shock].astype(float)
    if series.shape[0] < 3:
        return np.nan
    scale = float(series.std())
    return scale if scale > 0 else np.nan


def fit_lp(
    data: pd.DataFrame,
    response: str,
    shock: str,
    horizon: int,
    sample_name: str,
    min_obs: int = 48,
) -> dict[str, object]:
    frame = data.copy()
    label, channel, role = response_meta(response)
    outcome = outcome_column(response, horizon)
    if response not in frame.columns or shock not in frame.columns:
        return empty_row(response, label, channel, role, shock, horizon, sample_name, np.nan, 0, "")

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
    clean = frame.dropna(subset=required).copy()
    scale = shock_scale(clean, shock)
    base = empty_row(
        response,
        label,
        channel,
        role,
        shock,
        horizon,
        sample_name,
        scale,
        int(clean.shape[0]),
        ",".join(controls),
    )
    if clean.empty:
        return base
    base["sample_start"] = clean["month"].iloc[0]
    base["sample_end"] = clean["month"].iloc[-1]
    if clean.shape[0] < max(min_obs, len(controls) + 12) or clean[shock].nunique(dropna=True) < 3:
        return base

    y = clean[outcome].to_numpy(dtype=float)
    x, names = add_constant(clean[[shock, *controls]].to_numpy(dtype=float), [shock, *controls])
    model = fit_ols_hac(y, x, names, maxlags=horizon + 1)
    raw_coef = float(model.params[shock])
    raw_se = float(model.bse[shock])
    scaled_coef = raw_coef * scale
    scaled_se = raw_se * scale
    base.update(
        {
            "raw_coefficient_per_unit_shock": raw_coef,
            "raw_std_error_hac": raw_se,
            "coefficient": scaled_coef,
            "std_error_hac": scaled_se,
            "t_stat": float(model.tvalues[shock]),
            "p_value": float(model.pvalues[shock]),
            "ci_90_low": scaled_coef - Z90 * scaled_se,
            "ci_90_high": scaled_coef + Z90 * scaled_se,
            "ci_95_low": scaled_coef - Z95 * scaled_se,
            "ci_95_high": scaled_coef + Z95 * scaled_se,
            "ci_68_low": scaled_coef - Z68 * scaled_se,
            "ci_68_high": scaled_coef + Z68 * scaled_se,
            "coefficient_10bp_equiv": raw_coef * 10.0,
            "std_error_10bp_equiv": raw_se * 10.0,
            "r_squared": float(model.rsquared),
            "ci_method": "HAC_Newey_West_horizon_bandwidth",
            "horizon_consistent_bandwidth": horizon + 1,
        }
    )
    return base


def empty_row(
    response: str,
    label: str,
    channel: str,
    role: str,
    shock: str,
    horizon: int,
    sample_name: str,
    scale: float,
    nobs: int,
    controls: str,
) -> dict[str, object]:
    return {
        "response": response,
        "response_label": label,
        "channel": channel,
        "response_role": role,
        "shock": shock,
        "horizon_months": horizon,
        "sample_name": sample_name,
        "controls": controls,
        "nobs": int(nobs),
        "sample_start": "",
        "sample_end": "",
        "raw_coefficient_per_unit_shock": np.nan,
        "raw_std_error_hac": np.nan,
        "coefficient": np.nan,
        "std_error_hac": np.nan,
        "t_stat": np.nan,
        "p_value": np.nan,
        "ci_90_low": np.nan,
        "ci_90_high": np.nan,
        "ci_95_low": np.nan,
        "ci_95_high": np.nan,
        "ci_68_low": np.nan,
        "ci_68_high": np.nan,
        "bootstrap_ci_90_low": np.nan,
        "bootstrap_ci_90_high": np.nan,
        "bootstrap_ci_68_low": np.nan,
        "bootstrap_ci_68_high": np.nan,
        "bootstrap_ci_95_low": np.nan,
        "bootstrap_ci_95_high": np.nan,
        "bootstrap_replications": 0,
        "bootstrap_method": "not_run",
        "ci_method": "HAC_Newey_West_horizon_bandwidth",
        "horizon_consistent_bandwidth": horizon + 1,
        "coefficient_10bp_equiv": np.nan,
        "std_error_10bp_equiv": np.nan,
        "shock_scale_raw_units": scale,
        "shock_normalization": "1_sd_surprise",
        "optional_10bp_scaling_note": "10bp equivalent assumes factor units are basis points.",
        "r_squared": np.nan,
        "hac_bandwidth": horizon + 1,
        "interpretation_layer": "reduced_form_dynamic_transmission",
    }


def lp_design(
    data: pd.DataFrame,
    response: str,
    shock: str,
    horizon: int,
    min_obs: int = 48,
) -> tuple[np.ndarray, np.ndarray, list[str], float] | None:
    if response not in data.columns or shock not in data.columns:
        return None
    frame = add_lags(data, (response,))
    outcome = outcome_column(response, horizon)
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
    clean = frame.dropna(subset=required).copy()
    if clean.shape[0] < max(min_obs, len(controls) + 12) or clean[shock].nunique(dropna=True) < 3:
        return None
    scale = shock_scale(clean, shock)
    if pd.isna(scale):
        return None
    y = clean[outcome].to_numpy(dtype=float)
    x, names = add_constant(clean[[shock, *controls]].to_numpy(dtype=float), [shock, *controls])
    return y, x, names, float(scale)


def stable_seed(*parts: object) -> int:
    payload = "|".join(str(part) for part in parts).encode("utf-8")
    return int(hashlib.sha256(payload).hexdigest()[:8], 16)


def circular_block_residuals(resid: np.ndarray, block_length: int, rng: np.random.Generator) -> np.ndarray:
    nobs = resid.shape[0]
    starts = rng.integers(0, nobs, size=int(math.ceil(nobs / block_length)))
    draws = []
    for start in starts:
        idx = (np.arange(block_length) + start) % nobs
        draws.extend(resid[idx].tolist())
    return np.asarray(draws[:nobs], dtype=float)


def bootstrap_lp_percentiles(
    data: pd.DataFrame,
    response: str,
    shock: str,
    horizon: int,
    sample_name: str,
    min_obs: int = 48,
    reps: int = BOOTSTRAP_REPLICATIONS,
) -> dict[str, object]:
    design = lp_design(data, response, shock, horizon, min_obs=min_obs)
    if design is None:
        return {}
    y, x, names, scale = design
    if shock not in names:
        return {}
    model = fit_ols_hac(y, x, names, maxlags=horizon + 1)
    beta = np.asarray([model.params[name] for name in names], dtype=float)
    fitted = x @ beta
    resid = np.asarray(model.resid, dtype=float)
    resid = resid - np.nanmean(resid)
    rng = np.random.default_rng(stable_seed(response, shock, horizon, sample_name, reps))
    draws: list[float] = []
    block_length = max(3, horizon + 1)
    for _ in range(reps):
        y_star = fitted + circular_block_residuals(resid, block_length, rng)
        try:
            boot = fit_ols_hac(y_star, x, names, maxlags=horizon + 1)
        except np.linalg.LinAlgError:
            continue
        coef = float(boot.params[shock]) * scale
        if np.isfinite(coef):
            draws.append(coef)
    if len(draws) < max(80, reps // 3):
        return {}
    values = np.asarray(draws, dtype=float)
    return {
        "bootstrap_ci_68_low": float(np.percentile(values, 16)),
        "bootstrap_ci_68_high": float(np.percentile(values, 84)),
        "bootstrap_ci_90_low": float(np.percentile(values, 5)),
        "bootstrap_ci_90_high": float(np.percentile(values, 95)),
        "bootstrap_ci_95_low": float(np.percentile(values, 2.5)),
        "bootstrap_ci_95_high": float(np.percentile(values, 97.5)),
        "bootstrap_replications": int(len(draws)),
        "bootstrap_method": f"fixed_design_circular_block_residual_percentile_b{block_length}",
    }


def add_bootstrap_intervals(data: pd.DataFrame, coefficients: pd.DataFrame) -> pd.DataFrame:
    out = coefficients.copy()
    target_mask = out["sample_name"].eq("full") & out["shock"].eq("target_factor_monthly_easing")
    for index, row in out.loc[target_mask].iterrows():
        if pd.isna(row["coefficient"]):
            continue
        intervals = bootstrap_lp_percentiles(
            data,
            str(row["response"]),
            str(row["shock"]),
            int(row["horizon_months"]),
            str(row["sample_name"]),
        )
        for key, value in intervals.items():
            out.at[index, key] = value
    out.loc[out["bootstrap_replications"].fillna(0).astype(int).gt(0), "bootstrap_feasible"] = True
    out["bootstrap_feasible"] = out["bootstrap_feasible"].fillna(False)
    return out


def automatic_block_length(nobs: int, max_horizon: int = max(HORIZONS)) -> int:
    return int(max(6, round(nobs ** (1 / 3)), min(12, max(3, max_horizon // 2))))


def moving_block_indices(nobs: int, block_length: int, rng: np.random.Generator) -> np.ndarray:
    starts = rng.integers(0, max(nobs - block_length + 1, 1), size=int(math.ceil(nobs / block_length)))
    draws: list[int] = []
    for start in starts:
        draws.extend(range(start, min(start + block_length, nobs)))
    while len(draws) < nobs:
        start = int(rng.integers(0, max(nobs - block_length + 1, 1)))
        draws.extend(range(start, min(start + block_length, nobs)))
    return np.asarray(draws[:nobs], dtype=int)


def joint_horizon_design(
    data: pd.DataFrame,
    response: str,
    shock: str,
    horizons: tuple[int, ...] = HORIZONS,
    min_obs: int = 48,
) -> dict[str, object] | None:
    if response not in data.columns or shock not in data.columns:
        return None
    frame = add_lags(data, (response,))
    outcome_cols = []
    for horizon in horizons:
        outcome = outcome_column(response, horizon)
        frame[outcome] = frame[response].shift(-horizon) - frame[response].shift(1)
        outcome_cols.append(outcome)
    controls = [
        f"L1_{response}",
        f"L2_{response}",
        "L1_inflation_ea20_mom",
        "L2_inflation_ea20_mom",
        "L1_dfr_mavg",
        "L2_dfr_mavg",
    ]
    controls = [column for column in controls if column in frame.columns]
    required = [*outcome_cols, shock, *controls]
    clean = frame.dropna(subset=required).copy()
    if clean.shape[0] < max(min_obs, len(controls) + 12) or clean[shock].nunique(dropna=True) < 3:
        return None
    scale = shock_scale(clean, shock)
    if pd.isna(scale):
        return None
    x, names = add_constant(clean[[shock, *controls]].to_numpy(dtype=float), [shock, *controls])
    y_by_horizon = {horizon: clean[outcome_column(response, horizon)].to_numpy(dtype=float) for horizon in horizons}
    fits = {horizon: fit_ols_hac(y, x, names, maxlags=horizon + 1) for horizon, y in y_by_horizon.items()}
    residual_matrix = np.column_stack([np.asarray(fits[horizon].resid, dtype=float) for horizon in horizons])
    residual_matrix = residual_matrix - np.nanmean(residual_matrix, axis=0)
    fitted_matrix = np.column_stack(
        [
            x @ np.asarray([fits[horizon].params[name] for name in names], dtype=float)
            for horizon in horizons
        ]
    )
    return {
        "clean": clean,
        "x": x,
        "names": names,
        "scale": float(scale),
        "fits": fits,
        "residual_matrix": residual_matrix,
        "fitted_matrix": fitted_matrix,
        "horizons": horizons,
    }


def joint_bootstrap_irfs(
    data: pd.DataFrame,
    response: str,
    shock: str = "target_factor_monthly_easing",
    method: str = "moving_block",
    block_length: int | None = None,
    reps: int = BOOTSTRAP_REPLICATIONS,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    design = joint_horizon_design(data, response, shock)
    if design is None:
        return pd.DataFrame(), pd.DataFrame()
    x = design["x"]
    names = design["names"]
    scale = float(design["scale"])
    residual_matrix = design["residual_matrix"]
    fitted_matrix = design["fitted_matrix"]
    horizons = tuple(int(h) for h in design["horizons"])
    nobs = residual_matrix.shape[0]
    chosen_block = automatic_block_length(nobs) if block_length is None else int(block_length)
    rng = np.random.default_rng(stable_seed(response, shock, method, chosen_block, reps, nobs))
    draws = {horizon: [] for horizon in horizons}
    cumulative_draws = {horizon: [] for horizon in horizons}
    for _ in range(reps):
        if method == "wild":
            weights = rng.choice([-1.0, 1.0], size=nobs)
            boot_resid = residual_matrix * weights[:, None]
        else:
            idx = moving_block_indices(nobs, chosen_block, rng)
            boot_resid = residual_matrix[idx, :]
        cumulative = 0.0
        for col, horizon in enumerate(horizons):
            y_star = fitted_matrix[:, col] + boot_resid[:, col]
            try:
                boot = fit_ols_hac(y_star, x, names, maxlags=horizon + 1)
            except np.linalg.LinAlgError:
                continue
            coef = float(boot.params[shock]) * scale
            if np.isfinite(coef):
                draws[horizon].append(coef)
                cumulative += coef
                cumulative_draws[horizon].append(cumulative)
    rows = []
    cumulative_rows = []
    label, channel, role = response_meta(response)
    for horizon in horizons:
        values = np.asarray(draws[horizon], dtype=float)
        cvalues = np.asarray(cumulative_draws[horizon], dtype=float)
        if values.shape[0] < max(80, reps // 3):
            continue
        fit = design["fits"][horizon]
        point = float(fit.params[shock]) * scale
        rows.append(
            {
                "response": response,
                "response_label": label,
                "channel": channel,
                "response_role": role,
                "shock": shock,
                "horizon_months": horizon,
                "coefficient_common_sample": point,
                "ci_68_low": float(np.percentile(values, 16)),
                "ci_68_high": float(np.percentile(values, 84)),
                "ci_90_low": float(np.percentile(values, 5)),
                "ci_90_high": float(np.percentile(values, 95)),
                "ci_95_low": float(np.percentile(values, 2.5)),
                "ci_95_high": float(np.percentile(values, 97.5)),
                "bootstrap_replications": int(values.shape[0]),
                "bootstrap_method": method,
                "block_length": chosen_block if method != "wild" else 0,
                "block_length_rule": "automatic_max_6_n_cuberoot_half_max_horizon" if block_length is None and method != "wild" else "manual_or_not_applicable",
                "nobs_common_horizon_sample": nobs,
                "interpretation_layer": "dependence_aware_reduced_form_uncertainty",
            }
        )
        if cvalues.shape[0] >= max(80, reps // 3):
            cumulative_rows.append(
                {
                    "response": response,
                    "response_label": label,
                    "channel": channel,
                    "shock": shock,
                    "horizon_months": horizon,
                    "cumulative_ci_68_low": float(np.percentile(cvalues, 16)),
                    "cumulative_ci_68_high": float(np.percentile(cvalues, 84)),
                    "cumulative_ci_90_low": float(np.percentile(cvalues, 5)),
                    "cumulative_ci_90_high": float(np.percentile(cvalues, 95)),
                    "cumulative_ci_95_low": float(np.percentile(cvalues, 2.5)),
                    "cumulative_ci_95_high": float(np.percentile(cvalues, 97.5)),
                    "bootstrap_replications": int(cvalues.shape[0]),
                    "bootstrap_method": method,
                    "block_length": chosen_block if method != "wild" else 0,
                    "interval_note": "joint horizon residual resampling preserves empirical cross-horizon residual covariance",
                }
            )
    return pd.DataFrame(rows), pd.DataFrame(cumulative_rows)


def dependence_aware_uncertainty(data: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    responses = tuple(response for response in CANONICAL_COMPARISON_RESPONSES if response in data.columns)
    mb_rows = []
    mb_cum_rows = []
    wild_rows = []
    wild_cum_rows = []
    for response in responses:
        mb, mb_cum = joint_bootstrap_irfs(data, response, method="moving_block")
        wild, wild_cum = joint_bootstrap_irfs(data, response, method="wild")
        mb_rows.append(mb)
        mb_cum_rows.append(mb_cum.assign(source_method="moving_block") if not mb_cum.empty else mb_cum)
        wild_rows.append(wild)
        wild_cum_rows.append(wild_cum.assign(source_method="wild") if not wild_cum.empty else wild_cum)
    moving_block = pd.concat([frame for frame in mb_rows if not frame.empty], ignore_index=True) if mb_rows else pd.DataFrame()
    moving_cumulative = pd.concat([frame for frame in mb_cum_rows if not frame.empty], ignore_index=True) if mb_cum_rows else pd.DataFrame()
    wild = pd.concat([frame for frame in wild_rows if not frame.empty], ignore_index=True) if wild_rows else pd.DataFrame()
    wild_cumulative = pd.concat([frame for frame in wild_cum_rows if not frame.empty], ignore_index=True) if wild_cum_rows else pd.DataFrame()
    sensitivity_rows = []
    for response in responses:
        for block in (4, 6, 9, 12, None):
            table, _ = joint_bootstrap_irfs(data, response, method="moving_block", block_length=block, reps=199)
            if table.empty:
                continue
            focus = table.loc[table["horizon_months"].isin([6, 12, 24])].copy()
            focus["interval_width_90"] = focus["ci_90_high"] - focus["ci_90_low"]
            focus["sensitivity_block_length"] = focus["block_length"]
            focus["block_length_setting"] = "auto" if block is None else str(block)
            sensitivity_rows.append(
                focus[
                    [
                        "response",
                        "response_label",
                        "channel",
                        "horizon_months",
                        "block_length_setting",
                        "sensitivity_block_length",
                        "interval_width_90",
                        "bootstrap_replications",
                    ]
                ]
            )
    block_sensitivity = pd.concat(sensitivity_rows, ignore_index=True) if sensitivity_rows else pd.DataFrame()
    if not moving_block.empty and not wild.empty:
        width_mb = moving_block.assign(width_90=lambda x: x["ci_90_high"] - x["ci_90_low"])
        width_wild = wild.assign(width_90=lambda x: x["ci_90_high"] - x["ci_90_low"])
        summary = (
            width_mb.merge(
                width_wild[["response", "horizon_months", "width_90"]].rename(columns={"width_90": "wild_width_90"}),
                on=["response", "horizon_months"],
                how="left",
            )
            .rename(columns={"width_90": "moving_block_width_90"})
            .assign(width_ratio_mbb_to_wild=lambda x: x["moving_block_width_90"] / x["wild_width_90"])
        )
    else:
        summary = pd.DataFrame()
    cumulative_all = pd.concat([moving_cumulative, wild_cumulative], ignore_index=True) if not moving_cumulative.empty or not wild_cumulative.empty else pd.DataFrame()
    diagnostics = horizon_dependence_diagnostics(data, responses)
    return moving_block, wild, summary, block_sensitivity, diagnostics, cumulative_all


def horizon_dependence_diagnostics(data: pd.DataFrame, responses: tuple[str, ...]) -> pd.DataFrame:
    rows = []
    for response in responses:
        design = joint_horizon_design(data, response, "target_factor_monthly_easing")
        if design is None:
            continue
        residual_matrix = design["residual_matrix"]
        horizons = tuple(int(h) for h in design["horizons"])
        corr = np.corrcoef(residual_matrix, rowvar=False)
        adjacent = []
        for i in range(len(horizons) - 1):
            adjacent.append(float(corr[i, i + 1]))
        rows.append(
            {
                "response": response,
                "response_label": response_meta(response)[0],
                "channel": response_meta(response)[1],
                "nobs_common_horizon_sample": int(residual_matrix.shape[0]),
                "mean_adjacent_horizon_residual_corr": float(np.nanmean(adjacent)) if adjacent else np.nan,
                "max_abs_horizon_residual_corr": float(np.nanmax(np.abs(corr[np.triu_indices_from(corr, k=1)]))),
                "horizon_grid": ",".join(str(h) for h in horizons),
                "diagnostic_note": "Residual correlations motivate joint horizon bootstrap cumulative intervals.",
            }
        )
    return pd.DataFrame(rows)


def cumulative_table(coefficients: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    group_cols = ["sample_name", "response", "shock"]
    for (sample_name, response, shock), group in coefficients.groupby(group_cols, dropna=False):
        running = 0.0
        running_var = 0.0
        for _, row in group.sort_values("horizon_months").iterrows():
            coef = row["coefficient"]
            se = row["std_error_hac"]
            if pd.isna(coef) or pd.isna(se):
                continue
            running += float(coef)
            running_var += float(se) ** 2
            cumulative_se = math.sqrt(running_var)
            rows.append(
                {
                    "sample_name": sample_name,
                    "response": response,
                    "response_label": row["response_label"],
                    "channel": row["channel"],
                    "response_role": row["response_role"],
                    "shock": shock,
                    "horizon_months": int(row["horizon_months"]),
                    "cumulative_response": running,
                    "cumulative_se_independence_approx": cumulative_se,
                    "ci_90_low": running - Z90 * cumulative_se,
                    "ci_90_high": running + Z90 * cumulative_se,
                    "ci_95_low": running - Z95 * cumulative_se,
                    "ci_95_high": running + Z95 * cumulative_se,
                    "ci_68_low": running - Z68 * cumulative_se,
                    "ci_68_high": running + Z68 * cumulative_se,
                    "significant_90": (running - Z90 * cumulative_se > 0) or (running + Z90 * cumulative_se < 0),
                    "significant_95": (running - Z95 * cumulative_se > 0) or (running + Z95 * cumulative_se < 0),
                    "shock_normalization": "1_sd_surprise",
                    "ci_method": "sum_of_horizon_betas_with_independence_se_approximation",
                    "interpretation_layer": "reduced_form_dynamic_transmission",
                }
            )
    return pd.DataFrame(rows)


def run_lp(
    data: pd.DataFrame,
    sample_name: str,
    responses: tuple[str, ...],
    shocks: tuple[str, ...],
    min_obs: int = 48,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    frame = add_lags(data, responses)
    rows = []
    for response in responses:
        if response not in frame.columns:
            continue
        for shock in shocks:
            if shock not in frame.columns:
                continue
            for horizon in HORIZONS:
                rows.append(fit_lp(frame, response, shock, horizon, sample_name, min_obs=min_obs))
    coefficients = pd.DataFrame(rows)
    cumulative = cumulative_table(coefficients)
    return coefficients, cumulative


def regime_decomposition(data: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    frames = []
    cumulative_frames = []
    for regime, subset in data.groupby("lp_monthly_regime", dropna=False):
        coeff, cum = run_lp(
            subset.copy(),
            f"regime_{regime}",
            tuple(RESPONSE_SPECS),
            ("target_factor_monthly_easing",),
            min_obs=20,
        )
        frames.append(coeff)
        cumulative_frames.append(cum)
    return pd.concat(frames, ignore_index=True), pd.concat(cumulative_frames, ignore_index=True)


def subsample_frame(data: pd.DataFrame, name: str) -> tuple[pd.DataFrame, str]:
    frame = data.copy()
    shock = "target_factor_monthly_easing"
    if name == "full":
        return frame, shock
    if name == "exclude_covid":
        return frame.loc[~frame["lp_monthly_regime"].eq("covid")].copy(), shock
    if name == "exclude_qe_launch":
        mask = frame["date"].between("2015-01-31", "2015-06-30")
        return frame.loc[~mask].copy(), shock
    if name == "exclude_crisis_windows":
        crisis = (
            frame["date"].between("2008-09-30", "2009-06-30")
            | frame["date"].between("2011-07-31", "2012-12-31")
            | frame["date"].between("2020-03-31", "2021-12-31")
        )
        return frame.loc[~crisis].copy(), shock
    if name == "exclude_extreme_shock_outliers":
        top = frame[shock].abs().nlargest(5).index
        return frame.drop(index=top).copy(), shock
    if name == "clean_events_only":
        return frame, "target_factor_clean_monthly_easing"
    if name == "contaminated_events_only":
        return frame, "target_factor_contaminated_monthly_easing"
    raise ValueError(f"Unknown subsample: {name}")


def sign_label(value: object) -> str:
    if pd.isna(value):
        return ""
    numeric = float(value)
    if math.isclose(numeric, 0.0, abs_tol=1e-12):
        return "zero"
    return "positive" if numeric > 0 else "negative"


def stability_layer(data: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    subsamples = (
        "full",
        "exclude_covid",
        "exclude_qe_launch",
        "exclude_crisis_windows",
        "exclude_extreme_shock_outliers",
        "clean_events_only",
        "contaminated_events_only",
    )
    stability_frames = []
    cumulative_frames = []
    for name in subsamples:
        subset, shock = subsample_frame(data, name)
        coeff, cum = run_lp(subset, name, CANONICAL_COMPARISON_RESPONSES, (shock,), min_obs=36)
        coeff["direction_sign"] = coeff["coefficient"].map(sign_label)
        stability_frames.append(coeff)
        cumulative_frames.append(cum)

    stability = pd.concat(stability_frames, ignore_index=True)
    cumulative = pd.concat(cumulative_frames, ignore_index=True)
    sign_matrix = stability.pivot_table(
        index=["response", "response_label", "channel", "horizon_months"],
        columns="sample_name",
        values="direction_sign",
        aggfunc="first",
    ).reset_index()
    ranking = (
        cumulative.loc[cumulative["horizon_months"].isin([12, 24])]
        .assign(abs_cumulative=lambda x: x["cumulative_response"].abs())
        .groupby(["sample_name", "response", "response_label", "channel"], as_index=False)
        .agg(max_abs_cumulative=("abs_cumulative", "max"), signed_cumulative_at_max=("cumulative_response", "last"))
    )
    ranking["persistence_rank_within_subsample"] = ranking.groupby("sample_name")["max_abs_cumulative"].rank(
        method="dense", ascending=False
    )
    return stability, cumulative, sign_matrix, ranking


def rolling_recursive_layer(data: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    rows_rolling = []
    rows_recursive = []
    responses = (
        "ecb_house_purchase_growth_yoy",
        "ln_ecb_house_purchase_pure_new_loans",
        "ecb_wage_tracker_ex_oneoffs_real_yoy",
        "ln_dax_real_de",
    )
    for response in responses:
        frame = add_lags(data, (response,))
        valid = frame.dropna(subset=[response, "target_factor_monthly_easing"]).reset_index(drop=True)
        for horizon in (6, 12):
            window = 84
            for end in range(window, valid.shape[0] + 1):
                sample = valid.iloc[end - window : end].copy()
                fit = fit_lp(sample, response, "target_factor_monthly_easing", horizon, f"rolling_{window}m", min_obs=48)
                rows_rolling.append(
                    {
                        "response": response,
                        "response_label": response_meta(response)[0],
                        "horizon_months": horizon,
                        "window_start": sample["month"].iloc[0],
                        "window_end": sample["month"].iloc[-1],
                        "coefficient": fit["coefficient"],
                        "direction_sign": sign_label(fit["coefficient"]),
                        "nobs": fit["nobs"],
                    }
                )
            start = 60
            for end in range(start, valid.shape[0] + 1, 6):
                sample = valid.iloc[:end].copy()
                fit = fit_lp(sample, response, "target_factor_monthly_easing", horizon, "recursive", min_obs=48)
                rows_recursive.append(
                    {
                        "response": response,
                        "response_label": response_meta(response)[0],
                        "horizon_months": horizon,
                        "window_start": sample["month"].iloc[0],
                        "window_end": sample["month"].iloc[-1],
                        "coefficient": fit["coefficient"],
                        "direction_sign": sign_label(fit["coefficient"]),
                        "nobs": fit["nobs"],
                    }
                )
    return pd.DataFrame(rows_rolling), pd.DataFrame(rows_recursive)


def ols_policy_rate_comparison(data: pd.DataFrame, baseline: pd.DataFrame) -> pd.DataFrame:
    coeff, _ = run_lp(data, "policy_rate_ols_comparison", CANONICAL_COMPARISON_RESPONSES, ("d_dfr_eop",), min_obs=48)
    target = baseline.loc[baseline["shock"].eq("target_factor_monthly_easing")].copy()
    comparison = target.merge(
        coeff[["response", "horizon_months", "coefficient", "p_value", "nobs"]].rename(
            columns={
                "coefficient": "policy_rate_ols_coefficient",
                "p_value": "policy_rate_ols_p_value",
                "nobs": "policy_rate_ols_nobs",
            }
        ),
        on=["response", "horizon_months"],
        how="left",
    )
    comparison["surprise_lp_sign"] = comparison["coefficient"].map(sign_label)
    comparison["policy_rate_ols_sign"] = comparison["policy_rate_ols_coefficient"].map(sign_label)
    comparison["sign_match"] = comparison["surprise_lp_sign"].eq(comparison["policy_rate_ols_sign"])
    comparison["comparison_use"] = "qualitative_direction_check_not_causal_validation"
    return comparison


def significance_label(row: pd.Series) -> str:
    coef = row.get("coefficient", np.nan)
    p_value = row.get("p_value", np.nan)
    if pd.isna(coef) or pd.isna(p_value):
        return "not_estimated"
    sign = "positive" if float(coef) > 0 else "negative" if float(coef) < 0 else "zero"
    if float(p_value) <= 0.05:
        return f"{sign}_p05"
    if float(p_value) <= 0.10:
        return f"{sign}_p10"
    return f"{sign}_not_significant"


def build_uncertainty_tables(
    coefficients: pd.DataFrame,
    cumulative: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    target = coefficients.loc[coefficients["shock"].eq("target_factor_monthly_easing")].copy()
    target["significance_bucket"] = target.apply(significance_label, axis=1)
    target["hac_90_excludes_zero"] = (target["ci_90_low"] > 0) | (target["ci_90_high"] < 0)
    target["hac_95_excludes_zero"] = (target["ci_95_low"] > 0) | (target["ci_95_high"] < 0)
    target["bootstrap_90_excludes_zero"] = (target["bootstrap_ci_90_low"] > 0) | (target["bootstrap_ci_90_high"] < 0)
    horizon_table = target.loc[
        :,
        [
            "response",
            "response_label",
            "channel",
            "horizon_months",
            "coefficient",
            "std_error_hac",
            "p_value",
            "ci_90_low",
            "ci_90_high",
            "ci_95_low",
            "ci_95_high",
            "bootstrap_ci_90_low",
            "bootstrap_ci_90_high",
            "bootstrap_replications",
            "significance_bucket",
            "hac_90_excludes_zero",
            "hac_95_excludes_zero",
            "bootstrap_90_excludes_zero",
        ],
    ].copy()
    heatmap = horizon_table.pivot_table(
        index=["response", "response_label", "channel"],
        columns="horizon_months",
        values="significance_bucket",
        aggfunc="first",
    ).reset_index()
    heatmap.columns = [f"h{int(col)}" if isinstance(col, (int, float)) else str(col) for col in heatmap.columns]

    target_cumulative = cumulative.loc[cumulative["shock"].eq("target_factor_monthly_easing")].copy()
    target_cumulative["cumulative_direction"] = target_cumulative["cumulative_response"].map(sign_label)
    target_cumulative["cumulative_90_excludes_zero"] = (
        (target_cumulative["ci_90_low"] > 0) | (target_cumulative["ci_90_high"] < 0)
    )
    target_cumulative["cumulative_95_excludes_zero"] = (
        (target_cumulative["ci_95_low"] > 0) | (target_cumulative["ci_95_high"] < 0)
    )
    persistence = target_cumulative.pivot_table(
        index=["response", "response_label", "channel"],
        columns="horizon_months",
        values="cumulative_90_excludes_zero",
        aggfunc="first",
    ).reset_index()
    persistence.columns = [f"h{int(col)}_cum90" if isinstance(col, (int, float)) else str(col) for col in persistence.columns]
    return horizon_table, heatmap, persistence


def build_peak_response_table(coefficients: pd.DataFrame) -> pd.DataFrame:
    target = coefficients.loc[coefficients["shock"].eq("target_factor_monthly_easing")].dropna(subset=["coefficient"]).copy()
    if target.empty:
        return pd.DataFrame()
    target["abs_response"] = target["coefficient"].abs()
    idx = target.groupby(["response", "response_label", "channel"], dropna=False)["abs_response"].idxmax()
    return target.loc[
        idx,
        [
            "response",
            "response_label",
            "channel",
            "horizon_months",
            "coefficient",
            "ci_90_low",
            "ci_90_high",
            "p_value",
            "nobs",
            "bootstrap_ci_90_low",
            "bootstrap_ci_90_high",
        ],
    ].rename(columns={"horizon_months": "peak_horizon_months", "coefficient": "peak_response"})


def build_cumulative_persistence_table(cumulative: pd.DataFrame) -> pd.DataFrame:
    target = cumulative.loc[
        cumulative["shock"].eq("target_factor_monthly_easing") & cumulative["horizon_months"].isin([6, 12, 24])
    ].copy()
    if target.empty:
        return target
    target["cumulative_direction"] = target["cumulative_response"].map(sign_label)
    target["ci_90_excludes_zero"] = (target["ci_90_low"] > 0) | (target["ci_90_high"] < 0)
    return target.loc[
        :,
        [
            "response",
            "response_label",
            "channel",
            "horizon_months",
            "cumulative_response",
            "ci_90_low",
            "ci_90_high",
            "ci_95_low",
            "ci_95_high",
            "cumulative_direction",
            "ci_90_excludes_zero",
        ],
    ]


def build_stability_metrics(stability: pd.DataFrame, stability_cumulative: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for (response, label, channel), group in stability.groupby(["response", "response_label", "channel"], dropna=False):
        estimated = group.dropna(subset=["coefficient"]).copy()
        if estimated.empty:
            continue
        signs = estimated["direction_sign"].replace("", np.nan).dropna()
        sign_consistency = np.nan
        modal_sign = ""
        if not signs.empty:
            modal_sign = str(signs.value_counts().idxmax())
            sign_consistency = float((signs == modal_sign).mean())
        peak_rows = estimated.loc[estimated.groupby("sample_name")["coefficient"].apply(lambda x: x.abs().idxmax()).values]
        peak_timing_iqr = float(peak_rows["horizon_months"].quantile(0.75) - peak_rows["horizon_months"].quantile(0.25))
        response_cum = stability_cumulative.loc[stability_cumulative["response"].eq(response)].dropna(
            subset=["cumulative_response"]
        )
        cumulative_signs = response_cum.loc[response_cum["horizon_months"].isin([12, 24]), "cumulative_response"].map(sign_label)
        cumulative_direction_consistency = np.nan
        if not cumulative_signs.empty:
            cumulative_direction_consistency = float((cumulative_signs == cumulative_signs.value_counts().idxmax()).mean())
        h6 = estimated.loc[estimated["horizon_months"].eq(6), "coefficient"].abs().median()
        h24 = estimated.loc[estimated["horizon_months"].eq(24), "coefficient"].abs().median()
        decay_ratio = float(h24 / h6) if pd.notna(h6) and h6 > 0 and pd.notna(h24) else np.nan
        rows.append(
            {
                "response": response,
                "response_label": label,
                "channel": channel,
                "modal_direction": modal_sign,
                "sign_consistency": sign_consistency,
                "cumulative_direction_consistency": cumulative_direction_consistency,
                "peak_response_timing_iqr": peak_timing_iqr,
                "response_decay_ratio_abs_h24_to_h6": decay_ratio,
                "estimated_cells": int(estimated.shape[0]),
                "interpretation": "directional robustness, not exact magnitude invariance",
            }
        )
    return pd.DataFrame(rows)


def fit_sequential_pathway(data: pd.DataFrame, spec: dict[str, object]) -> dict[str, object]:
    upstream = str(spec["upstream"])
    downstream = str(spec["downstream"])
    upstream_h = int(spec["upstream_horizon"])
    downstream_h = int(spec["downstream_horizon"])
    shock = "target_factor_monthly_easing"
    base = {
        "pathway": spec["pathway"],
        "upstream": upstream,
        "upstream_label": response_meta(upstream)[0],
        "downstream": downstream,
        "downstream_label": response_meta(downstream)[0],
        "upstream_horizon_months": upstream_h,
        "downstream_horizon_months": downstream_h,
        "interpretation": spec["interpretation"],
        "governance_note": "Timing evidence only; this is not structural bank-channel identification.",
        "timing_classification": "",
    }
    if upstream not in data.columns or downstream not in data.columns or shock not in data.columns:
        return {**base, "status": "missing_required_series"}

    frame = add_lags(data, (upstream, downstream))
    frame["upstream_change"] = frame[upstream].shift(-upstream_h) - frame[upstream].shift(1)
    frame["downstream_change"] = frame[downstream].shift(-downstream_h) - frame[downstream].shift(1)
    controls = [
        f"L1_{upstream}",
        f"L2_{upstream}",
        f"L1_{downstream}",
        f"L2_{downstream}",
        "L1_inflation_ea20_mom",
        "L2_inflation_ea20_mom",
        "L1_dfr_mavg",
        "L2_dfr_mavg",
    ]
    controls = [column for column in controls if column in frame.columns]
    required = ["upstream_change", "downstream_change", shock, *controls]
    clean = frame.dropna(subset=required).copy()
    if clean.shape[0] < max(48, len(controls) + 12) or clean[shock].nunique(dropna=True) < 3:
        return {**base, "status": "insufficient_monthly_variation", "nobs": int(clean.shape[0])}

    shock_fit = fit_lp(frame, upstream, shock, upstream_h, "sequential_upstream", min_obs=48)
    downstream_fit = fit_lp(frame, downstream, shock, downstream_h, "sequential_downstream", min_obs=48)
    y = clean["downstream_change"].to_numpy(dtype=float)
    x, names = add_constant(
        clean[["upstream_change", shock, *controls]].to_numpy(dtype=float),
        ["upstream_change", shock, *controls],
    )
    model = fit_ols_hac(y, x, names, maxlags=downstream_h + 1)
    return {
        **base,
        "status": "estimated",
        "nobs": int(clean.shape[0]),
        "shock_to_upstream_coef": shock_fit["coefficient"],
        "shock_to_upstream_p": shock_fit["p_value"],
        "shock_to_downstream_coef": downstream_fit["coefficient"],
        "shock_to_downstream_p": downstream_fit["p_value"],
        "upstream_to_downstream_conditional_coef": float(model.params["upstream_change"]),
        "upstream_to_downstream_conditional_se_hac": float(model.bse["upstream_change"]),
        "upstream_to_downstream_conditional_p": float(model.pvalues["upstream_change"]),
        "conditional_shock_coef": float(model.params[shock]),
        "conditional_shock_p": float(model.pvalues[shock]),
        "controls": ",".join(controls),
        "timing_classification": "ordered_dynamic_transmission" if upstream_h < downstream_h else "same_or_reverse_timing",
    }


def sequential_transmission_analysis(data: pd.DataFrame) -> pd.DataFrame:
    return pd.DataFrame([fit_sequential_pathway(data, spec) for spec in SEQUENTIAL_PATHWAYS])


BANKING_TIMING_VARIABLES = (
    "ecb_mir_mortgage_lending_spread_dfr",
    "ecb_mir_nfc_lending_spread_dfr",
    "ecb_mir_mortgage_lending_rate",
    "ecb_mir_nfc_lending_rate",
    "ln_hh_loans_ea_stock",
    "ln_nfc_loans_ea_stock",
    "ecb_house_purchase_growth_yoy",
    "ln_ecb_house_purchase_pure_new_loans",
    "ecb_wage_tracker_ex_oneoffs_real_yoy",
    "eurostat_ecfin_eei_ea20",
)

BLS_VARIABLES = {
    "bls_credit_standards_mortgage_q_observed": "BLS mortgage credit standards",
    "bls_credit_standards_nfc_q_observed": "BLS enterprise credit standards",
    "bls_credit_standards_consumer_q_observed": "BLS consumer-credit standards",
    "bls_loan_demand_mortgage_q_observed": "BLS mortgage loan demand",
    "bls_loan_demand_nfc_q_observed": "BLS enterprise loan demand",
    "bls_loan_demand_consumer_q_observed": "BLS consumer-credit demand",
}

BANKING_REGISTRY = {
    "ecb_mir_mortgage_lending_rate": (
        "ECB MIR mortgage lending rate",
        "monthly",
        "lending_rate",
        "Monthly observed annualised agreed rate on new euro-area house-purchase loans.",
    ),
    "ecb_mir_nfc_lending_rate": (
        "ECB MIR NFC lending rate",
        "monthly",
        "lending_rate",
        "Monthly observed annualised agreed rate on new euro-area NFC loans.",
    ),
    "ecb_mir_mortgage_lending_spread_dfr": (
        "Mortgage lending spread over DFR",
        "monthly",
        "lending_spread",
        "Computed as monthly MIR mortgage lending rate minus monthly average DFR.",
    ),
    "ecb_mir_nfc_lending_spread_dfr": (
        "NFC lending spread over DFR",
        "monthly",
        "lending_spread",
        "Computed as monthly MIR NFC lending rate minus monthly average DFR.",
    ),
    "ln_hh_loans_ea_stock": (
        "Household credit stock",
        "monthly",
        "credit_stock",
        "Monthly ECB MFI loans to households; broad fallback credit stock.",
    ),
    "ln_nfc_loans_ea_stock": (
        "NFC credit stock",
        "monthly",
        "credit_stock",
        "Monthly ECB adjusted MFI loans to non-financial corporations.",
    ),
    "ecb_house_purchase_growth_yoy": (
        "House-purchase lending growth",
        "monthly",
        "housing_finance",
        "Monthly ECB annual growth in loans for house purchase.",
    ),
    "ln_ecb_house_purchase_pure_new_loans": (
        "Pure new house-purchase loans",
        "monthly",
        "housing_finance",
        "Monthly ECB MIR pure new loans for house purchase; shorter public sample.",
    ),
    **{
        variable: (
            label,
            "quarterly_observed",
            "bank_lending_survey",
            "ECB BLS quarter-end observation only; no monthly interpolation or filling.",
        )
        for variable, label in BLS_VARIABLES.items()
    },
}


def earliest_response_timing(coefficients: pd.DataFrame, response: str) -> dict[str, object]:
    frame = coefficients.loc[
        coefficients["response"].eq(response) & coefficients["shock"].eq("target_factor_monthly_easing")
    ].dropna(subset=["coefficient"])
    label, channel, role = response_meta(response)
    if frame.empty:
        return {
            "response": response,
            "response_label": label,
            "channel": channel,
            "response_role": role,
            "status": "not_estimated",
        }
    frame = frame.sort_values("horizon_months").copy()
    frame["abs_response"] = frame["coefficient"].abs()
    peak = frame.loc[frame["abs_response"].idxmax()]
    sig = frame.loc[frame["p_value"].le(0.10)]
    cumulative = float(frame["coefficient"].sum())
    return {
        "response": response,
        "response_label": label,
        "channel": channel,
        "response_role": role,
        "status": "estimated",
        "earliest_estimated_horizon": int(frame["horizon_months"].min()),
        "earliest_p10_horizon": int(sig["horizon_months"].min()) if not sig.empty else np.nan,
        "peak_abs_horizon": int(peak["horizon_months"]),
        "peak_response": float(peak["coefficient"]),
        "cumulative_response": cumulative,
        "direction": sign_label(cumulative),
        "p10_horizon_share": float(frame["p_value"].le(0.10).mean()),
        "estimated_horizons": int(frame.shape[0]),
        "frequency_integrity": "monthly_observed",
        "interpretation_layer": "ordered_timing_evidence",
    }


def fit_quarterly_observed_timing(data: pd.DataFrame, variable: str) -> dict[str, object]:
    label = BLS_VARIABLES.get(variable, variable)
    base = {
        "response": variable,
        "response_label": label,
        "channel": "bank_lending_survey",
        "response_role": "quarterly_observed_regime_tag",
        "frequency_integrity": "quarter_end_observed_only_no_interpolation",
        "interpretation_layer": "mixed_frequency_timing_tag",
    }
    if variable not in data.columns:
        return {**base, "status": "missing"}
    frame = data.loc[data[variable].notna()].copy()
    frame = frame.dropna(subset=[variable, "target_factor_monthly_easing"])
    if frame.shape[0] < 40 or frame["target_factor_monthly_easing"].nunique(dropna=True) < 3:
        return {**base, "status": "insufficient_quarter_end_variation", "nobs": int(frame.shape[0])}
    frame[f"L1_{variable}"] = frame[variable].shift(1)
    clean = frame.dropna(subset=[f"L1_{variable}"]).copy()
    y = clean[variable].to_numpy(dtype=float)
    x, names = add_constant(clean[["target_factor_monthly_easing", f"L1_{variable}"]].to_numpy(dtype=float), ["target_factor_monthly_easing", f"L1_{variable}"])
    model = fit_ols_hac(y, x, names, maxlags=2)
    scale = shock_scale(clean, "target_factor_monthly_easing")
    coef = float(model.params["target_factor_monthly_easing"]) * scale
    return {
        **base,
        "status": "estimated_quarter_end_only",
        "nobs": int(clean.shape[0]),
        "coefficient_1sd": coef,
        "std_error_hac_1sd": float(model.bse["target_factor_monthly_easing"]) * scale,
        "p_value": float(model.pvalues["target_factor_monthly_easing"]),
        "direction": sign_label(coef),
        "timing_note": "BLS is quarterly and appears only on quarter-end months; no monthly filling is used.",
    }


def build_banking_proxy_registry(data: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for variable, (label, frequency, proxy_type, note) in BANKING_REGISTRY.items():
        if variable in data.columns:
            observed = data.loc[data[variable].notna(), ["date", variable]].copy()
            observations = int(observed.shape[0])
            sample_start = str(observed["date"].min().date()) if observations else ""
            sample_end = str(observed["date"].max().date()) if observations else ""
        else:
            observations = 0
            sample_start = ""
            sample_end = ""
        rows.append(
            {
                "variable": variable,
                "label": label,
                "proxy_type": proxy_type,
                "frequency": frequency,
                "frequency_integrity": "quarter_end_observed_only_no_interpolation"
                if frequency == "quarterly_observed"
                else "monthly_observed_or_documented_monthly_transform",
                "observations": observations,
                "sample_start": sample_start,
                "sample_end": sample_end,
                "included_in_monthly_lp": variable in RESPONSE_SPECS,
                "included_in_timing_layer": variable in BANKING_TIMING_VARIABLES or variable in BLS_VARIABLES,
                "governance_note": note,
            }
        )
    return pd.DataFrame(rows)


def banking_timing_layer(data: pd.DataFrame, coefficients: pd.DataFrame, sequential_outputs: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    monthly_rows = [earliest_response_timing(coefficients, variable) for variable in BANKING_TIMING_VARIABLES if variable in data.columns]
    bls_rows = [fit_quarterly_observed_timing(data, variable) for variable in BLS_VARIABLES]
    timing_matrix = pd.DataFrame([*monthly_rows, *bls_rows])
    credit_supply = timing_matrix.loc[
        timing_matrix["channel"].isin(["banking_lending_conditions", "financial_credit", "housing_finance", "bank_lending_survey"])
    ].copy()
    if not credit_supply.empty:
        credit_supply["supply_timing_rank"] = credit_supply["peak_abs_horizon"].rank(method="dense", na_option="bottom")
    rankings = timing_matrix.loc[timing_matrix["status"].astype(str).str.startswith("estimated")].copy()
    if not rankings.empty:
        rankings["persistence_strength"] = rankings.get("cumulative_response", pd.Series(np.nan, index=rankings.index)).abs()
        rankings["early_timing_score"] = rankings["earliest_p10_horizon"].fillna(rankings["peak_abs_horizon"]).rank(method="dense", ascending=True, na_option="bottom")
        rankings["persistence_rank"] = rankings["persistence_strength"].rank(method="dense", ascending=False, na_option="bottom")
        rankings["intermediation_timing_score"] = rankings["early_timing_score"] + rankings["persistence_rank"]
        rankings = rankings.sort_values(["intermediation_timing_score", "response"])
    sequence = sequential_outputs.copy()
    if not sequence.empty:
        sequence["sequence_class"] = np.where(
            sequence["status"].eq("estimated") & sequence["timing_classification"].eq("ordered_dynamic_transmission"),
            "timing_consistent_financial_propagation",
            "not_estimated_or_timing_weak",
        )
        sequence["language_guardrail"] = "ordered timing evidence only"
    return timing_matrix, credit_supply, rankings, sequence


def write_matrix_svg(frame: pd.DataFrame, path: Path, title: str, value_columns: list[str]) -> None:
    if frame.empty:
        return
    if not value_columns:
        return
    frame = frame.copy()
    labels = frame["response_label"].astype(str).tolist() if "response_label" in frame.columns else frame.iloc[:, 0].astype(str).tolist()
    color_scores = {
        "positive_p05": 2,
        "positive_p10": 1,
        "positive_not_significant": 0.35,
        "negative_p05": -2,
        "negative_p10": -1,
        "negative_not_significant": -0.35,
        "zero_not_significant": 0,
        "not_estimated": np.nan,
        True: 1.5,
        False: 0,
    }
    values = np.asarray(
        [[color_scores.get(row.get(column, "not_estimated"), np.nan) for column in value_columns] for _, row in frame.iterrows()],
        dtype=float,
    )
    keep = ~np.all(np.isnan(values), axis=1)
    if not keep.any():
        return
    frame = frame.loc[keep].reset_index(drop=True)
    values = values[keep]
    labels = [label for label, include in zip(labels, keep) if include]
    fig_h = max(4.8, 0.38 * len(labels) + 1.6)
    fig_w = max(8.5, 0.75 * len(value_columns) + 4.8)
    fig, ax = plt.subplots(figsize=(fig_w, fig_h))
    cmap = plt.get_cmap("RdBu")
    masked = np.ma.masked_invalid(values)
    ax.imshow(masked, aspect="auto", cmap=cmap, vmin=-2, vmax=2)
    ax.set_xticks(range(len(value_columns)), value_columns)
    ax.set_yticks(range(len(labels)), labels)
    ax.tick_params(axis="x", rotation=0, labelsize=9)
    ax.tick_params(axis="y", labelsize=9)
    for row_idx, (_, row) in enumerate(frame.iterrows()):
        for col_idx, column in enumerate(value_columns):
            raw = row.get(column, "not_estimated")
            score = color_scores.get(raw, np.nan)
            display = (
                str(raw)
                .replace("positive_p05", "+ p<.05")
                .replace("positive_p10", "+ p<.10")
                .replace("positive_not_significant", "+")
                .replace("negative_p05", "- p<.05")
                .replace("negative_p10", "- p<.10")
                .replace("negative_not_significant", "-")
                .replace("zero_not_significant", "0")
                .replace("_", " ")
            )
            if isinstance(raw, (bool, np.bool_)):
                display = "90%" if bool(raw) else ""
            text_color = "#ffffff" if pd.notna(score) and abs(float(score)) >= 1.2 else "#111111"
            ax.text(col_idx, row_idx, display, ha="center", va="center", fontsize=7.5, color=text_color)
    ax.set_title(title, loc="left", fontsize=14, fontweight="bold")
    ax.set_xlabel("Horizon")
    for spine in ax.spines.values():
        spine.set_visible(False)
    fig.tight_layout()
    fig.savefig(path.with_suffix(".png"), dpi=180)
    plt.close(fig)


def clean_filename(value: str) -> str:
    return re.sub(r"[^A-Za-z0-9_]+", "_", value).strip("_")


def write_svg_irf(coefficients: pd.DataFrame, response: str) -> None:
    frame = coefficients.loc[
        coefficients["response"].eq(response) & coefficients["shock"].eq("target_factor_monthly_easing")
    ].dropna(subset=["coefficient", "ci_90_low", "ci_90_high"])
    if frame.empty:
        return
    frame = frame.sort_values("horizon_months")
    xs = frame["horizon_months"].to_numpy(dtype=float)
    ys = frame["coefficient"].to_numpy(dtype=float)
    lo = frame["ci_90_low"].to_numpy(dtype=float)
    hi = frame["ci_90_high"].to_numpy(dtype=float)
    label = response_meta(response)[0]
    fig, ax = plt.subplots(figsize=(8.6, 5.1))
    ax.fill_between(xs, lo, hi, color="#7aa6c2", alpha=0.28, label="90% HAC interval")
    ax.plot(xs, ys, color="#174a7c", linewidth=2.6, marker="o", label="IRF")
    ax.axhline(0, color="#202020", linewidth=1.2)
    ax.set_title(f"{label}: Response to 1 SD ECB Target Surprise", loc="left", fontsize=14, fontweight="bold")
    ax.set_xlabel("Horizon in months")
    ax.set_ylabel("Response, 1 SD shock")
    ax.set_xticks(xs)
    ax.grid(axis="y", alpha=0.24)
    ax.legend(frameon=False, loc="best")
    ax.spines[["top", "right"]].set_visible(False)
    fig.tight_layout()
    fig.savefig(FINAL_FIGURE_DIRS["baseline"] / f"monthly_irf_{clean_filename(response)}.png", dpi=180)
    plt.close(fig)


def write_uncertainty_fan_svg(intervals: pd.DataFrame, response: str) -> None:
    frame = intervals.loc[intervals["response"].eq(response)].dropna(subset=["coefficient_common_sample", "ci_90_low", "ci_90_high"])
    if frame.empty:
        return
    frame = frame.sort_values("horizon_months")
    xs = frame["horizon_months"].to_numpy(dtype=float)
    center = frame["coefficient_common_sample"].to_numpy(dtype=float)
    lo95 = frame["ci_95_low"].to_numpy(dtype=float)
    hi95 = frame["ci_95_high"].to_numpy(dtype=float)
    lo90 = frame["ci_90_low"].to_numpy(dtype=float)
    hi90 = frame["ci_90_high"].to_numpy(dtype=float)
    lo68 = frame["ci_68_low"].to_numpy(dtype=float)
    hi68 = frame["ci_68_high"].to_numpy(dtype=float)
    label = response_meta(response)[0]
    fig, ax = plt.subplots(figsize=(8.8, 5.2))
    ax.fill_between(xs, lo95, hi95, color="#ccd8e4", alpha=0.68, label="95%")
    ax.fill_between(xs, lo90, hi90, color="#8eb5d1", alpha=0.56, label="90%")
    ax.fill_between(xs, lo68, hi68, color="#376f9f", alpha=0.25, label="68%")
    ax.plot(xs, center, color="#143d63", linewidth=2.6)
    ax.axhline(0, color="#202020", linewidth=1.2)
    ax.set_title(f"{label}: Moving-Block Uncertainty Fan", loc="left", fontsize=14, fontweight="bold")
    ax.set_xlabel("Horizon in months")
    ax.set_ylabel("Response, 1 SD shock")
    ax.set_xticks(xs)
    ax.grid(axis="y", alpha=0.24)
    ax.legend(frameon=False, ncol=3, loc="best")
    ax.spines[["top", "right"]].set_visible(False)
    fig.tight_layout()
    fig.savefig(FINAL_FIGURE_DIRS["uncertainty"] / f"uncertainty_fan_{clean_filename(response)}.png", dpi=180)
    plt.close(fig)


def write_cumulative_interval_svg(cumulative_intervals: pd.DataFrame, response: str) -> None:
    if cumulative_intervals.empty:
        return
    frame = cumulative_intervals.loc[
        cumulative_intervals["response"].eq(response) & cumulative_intervals["source_method"].eq("moving_block")
    ].dropna(subset=["cumulative_ci_90_low", "cumulative_ci_90_high"])
    if frame.empty:
        return
    frame = frame.sort_values("horizon_months")
    xs = frame["horizon_months"].to_numpy(dtype=float)
    lo = frame["cumulative_ci_90_low"].to_numpy(dtype=float)
    hi = frame["cumulative_ci_90_high"].to_numpy(dtype=float)
    center = (lo + hi) / 2
    fig, ax = plt.subplots(figsize=(8.6, 5.0))
    ax.fill_between(xs, lo, hi, color="#8eb5d1", alpha=0.36, label="90% moving-block interval")
    ax.plot(xs, center, color="#174a7c", linewidth=2.6, marker="o")
    ax.axhline(0, color="#202020", linewidth=1.2)
    ax.set_title(
        f"{response_meta(response)[0]}: Cumulative Persistence",
        loc="left",
        fontsize=14,
        fontweight="bold",
    )
    ax.set_xlabel("Horizon in months")
    ax.set_ylabel("Cumulative response, 1 SD shock")
    ax.set_xticks(xs)
    ax.grid(axis="y", alpha=0.24)
    ax.legend(frameon=False, loc="best")
    ax.spines[["top", "right"]].set_visible(False)
    fig.tight_layout()
    fig.savefig(FINAL_FIGURE_DIRS["cumulative"] / f"cumulative_interval_{clean_filename(response)}.png", dpi=180)
    plt.close(fig)


def write_rolling_stability_charts(rolling: pd.DataFrame) -> None:
    if rolling.empty:
        return
    for response, frame in rolling.groupby("response"):
        focus = frame.loc[frame["horizon_months"].eq(6)].dropna(subset=["coefficient"]).copy()
        if focus.empty:
            continue
        focus["window_end"] = pd.to_datetime(focus["window_end"])
        fig, ax = plt.subplots(figsize=(9.4, 4.7))
        ax.plot(focus["window_end"], focus["coefficient"], color="#174a7c", linewidth=2.0)
        ax.axhline(0, color="#202020", linewidth=1.1)
        ax.set_title(f"{response_meta(response)[0]}: Rolling 84-Month H6 Stability", loc="left", fontsize=13.5, fontweight="bold")
        ax.set_xlabel("Window end")
        ax.set_ylabel("H6 response, 1 SD shock")
        ax.grid(axis="y", alpha=0.24)
        ax.spines[["top", "right"]].set_visible(False)
        fig.tight_layout()
        fig.savefig(FINAL_FIGURE_DIRS["stability"] / f"rolling_stability_h6_{clean_filename(response)}.png", dpi=170)
        plt.close(fig)


def write_clean_event_chart(stability: pd.DataFrame) -> None:
    if stability.empty:
        return
    focus = stability.loc[
        stability["sample_name"].isin(["full", "clean_events_only", "contaminated_events_only"])
        & stability["horizon_months"].eq(6)
    ].dropna(subset=["coefficient"]).copy()
    if focus.empty:
        return
    pivot = focus.pivot_table(index="response_label", columns="sample_name", values="coefficient", aggfunc="first")
    pivot = pivot.reindex(columns=["full", "clean_events_only", "contaminated_events_only"])
    fig, ax = plt.subplots(figsize=(10.2, max(4.8, 0.42 * len(pivot) + 1.4)))
    y = np.arange(len(pivot))
    width = 0.24
    colors = ["#174a7c", "#4f7f3f", "#a65e2e"]
    for idx, column in enumerate(pivot.columns):
        ax.barh(y + (idx - 1) * width, pivot[column], height=width, color=colors[idx], label=column.replace("_", " "))
    ax.axvline(0, color="#202020", linewidth=1.1)
    ax.set_yticks(y, pivot.index)
    ax.invert_yaxis()
    ax.set_xlabel("H6 response, 1 SD shock")
    ax.set_title("Clean vs Contaminated Event Responses", loc="left", fontsize=14, fontweight="bold")
    ax.legend(frameon=False)
    ax.grid(axis="x", alpha=0.22)
    ax.spines[["top", "right"]].set_visible(False)
    fig.tight_layout()
    fig.savefig(FINAL_FIGURE_DIRS["stability"] / "clean_vs_contaminated_h6.png", dpi=180)
    plt.close(fig)


def write_uncertainty_comparison_panel(bootstrap_sensitivity: pd.DataFrame) -> None:
    if bootstrap_sensitivity.empty or "width_ratio_mbb_to_wild" not in bootstrap_sensitivity.columns:
        return
    focus = bootstrap_sensitivity.loc[bootstrap_sensitivity["horizon_months"].isin([6, 12, 24])].copy()
    focus = focus.dropna(subset=["width_ratio_mbb_to_wild"])
    if focus.empty:
        return
    fig, ax = plt.subplots(figsize=(10.4, 5.4))
    for label, group in focus.groupby("response_label"):
        ax.plot(group["horizon_months"], group["width_ratio_mbb_to_wild"], marker="o", linewidth=1.8, label=label)
    ax.axhline(1.0, color="#202020", linewidth=1.1)
    ax.set_title("Moving-Block vs Wild Bootstrap Widths", loc="left", fontsize=14, fontweight="bold")
    ax.set_xlabel("Horizon in months")
    ax.set_ylabel("90% interval width ratio")
    ax.set_xticks([6, 12, 24])
    ax.grid(axis="y", alpha=0.24)
    ax.legend(frameon=False, fontsize=8, ncol=2)
    ax.spines[["top", "right"]].set_visible(False)
    fig.tight_layout()
    fig.savefig(FINAL_FIGURE_DIRS["uncertainty"] / "uncertainty_width_comparison.png", dpi=180)
    plt.close(fig)


def write_regime_chart(regime_coefficients: pd.DataFrame) -> None:
    if regime_coefficients.empty:
        return
    focus = regime_coefficients.loc[
        regime_coefficients["shock"].eq("target_factor_monthly_easing")
        & regime_coefficients["horizon_months"].eq(6)
        & regime_coefficients["response"].isin(CANONICAL_COMPARISON_RESPONSES)
    ].dropna(subset=["coefficient"]).copy()
    if focus.empty:
        return
    focus["regime"] = focus["sample_name"].str.replace("regime_", "", regex=False)
    pivot = focus.pivot_table(index="response_label", columns="regime", values="coefficient", aggfunc="first")
    preferred = [column for column in ["pre_qe", "qe", "covid", "tightening"] if column in pivot.columns]
    pivot = pivot.reindex(columns=preferred)
    if pivot.empty or not len(pivot.columns):
        return
    fig, ax = plt.subplots(figsize=(10.4, max(4.8, 0.42 * len(pivot) + 1.5)))
    matrix = pivot.to_numpy(dtype=float)
    scale = float(np.nanmax(np.abs(matrix))) if np.isfinite(matrix).any() else 1.0
    if math.isclose(scale, 0.0):
        scale = 1.0
    im = ax.imshow(matrix, aspect="auto", cmap="RdBu", vmin=-scale, vmax=scale)
    ax.set_xticks(range(len(pivot.columns)), pivot.columns)
    ax.set_yticks(range(len(pivot.index)), pivot.index)
    ax.set_title("Regime H6 Response Comparison", loc="left", fontsize=14, fontweight="bold")
    for row in range(pivot.shape[0]):
        for col in range(pivot.shape[1]):
            value = pivot.iloc[row, col]
            if pd.notna(value):
                ax.text(col, row, f"{value:.3g}", ha="center", va="center", fontsize=8)
    fig.colorbar(im, ax=ax, shrink=0.82, label="H6 response")
    fig.tight_layout()
    fig.savefig(FINAL_FIGURE_DIRS["regimes"] / "regime_h6_response_comparison.png", dpi=180)
    plt.close(fig)


def write_banking_timing_chart(timing_matrix: pd.DataFrame) -> None:
    if timing_matrix.empty:
        return
    focus = timing_matrix.loc[timing_matrix["channel"].isin(["banking_lending_conditions", "bank_lending_survey", "financial_credit", "housing_finance"])].copy()
    focus = focus.dropna(subset=["peak_abs_horizon"], how="all")
    if focus.empty:
        return
    focus = focus.sort_values(["channel", "peak_abs_horizon"], na_position="last")
    values = pd.to_numeric(focus["peak_abs_horizon"], errors="coerce")
    fig, ax = plt.subplots(figsize=(10.4, max(4.8, 0.42 * len(focus) + 1.5)))
    ax.barh(focus["response_label"], values, color="#376f9f")
    ax.set_xlabel("Peak absolute response horizon")
    ax.set_title("Banking and Credit Timing Evidence", loc="left", fontsize=14, fontweight="bold")
    ax.grid(axis="x", alpha=0.22)
    ax.spines[["top", "right"]].set_visible(False)
    fig.tight_layout()
    fig.savefig(FINAL_FIGURE_DIRS["banking"] / "banking_peak_timing.png", dpi=180)
    plt.close(fig)


def write_mechanism_sequence_chart(sequence: pd.DataFrame) -> None:
    if sequence.empty or "shock_to_upstream_coef" not in sequence.columns:
        return
    focus = sequence.loc[sequence["status"].eq("estimated")].copy()
    if focus.empty:
        return
    x = pd.to_numeric(focus["shock_to_upstream_coef"], errors="coerce")
    y = pd.to_numeric(focus["shock_to_downstream_coef"], errors="coerce")
    fig, ax = plt.subplots(figsize=(8.6, 5.4))
    ax.scatter(x, y, s=68, color="#174a7c", alpha=0.86)
    for _, row in focus.iterrows():
        ax.annotate(str(row["pathway"]).replace("_", "\n"), (row["shock_to_upstream_coef"], row["shock_to_downstream_coef"]), fontsize=7, xytext=(4, 4), textcoords="offset points")
    ax.axhline(0, color="#202020", linewidth=1.0)
    ax.axvline(0, color="#202020", linewidth=1.0)
    ax.set_xlabel("Shock to upstream response")
    ax.set_ylabel("Shock to downstream response")
    ax.set_title("Sequential Timing: Upstream vs Downstream Responses", loc="left", fontsize=14, fontweight="bold")
    ax.grid(alpha=0.22)
    ax.spines[["top", "right"]].set_visible(False)
    fig.tight_layout()
    fig.savefig(FINAL_FIGURE_DIRS["mechanism"] / "sequential_timing_response_map.png", dpi=180)
    plt.close(fig)


def fmt(value: object, digits: int = 4) -> str:
    if pd.isna(value):
        return ""
    if isinstance(value, (float, np.floating)):
        return f"{float(value):.{digits}f}"
    return str(value)


def markdown_table(frame: pd.DataFrame, columns: list[str], max_rows: int = 24) -> str:
    if frame.empty:
        return "_No available rows._"
    display = frame.loc[:, [column for column in columns if column in frame.columns]].head(max_rows)
    header = "| " + " | ".join(display.columns) + " |"
    divider = "| " + " | ".join(["---"] * len(display.columns)) + " |"
    rows = ["| " + " | ".join(fmt(row[column]) for column in display.columns) + " |" for _, row in display.iterrows()]
    return "\n".join([header, divider, *rows])


def write_markdown(coefficients: pd.DataFrame, cumulative: pd.DataFrame) -> None:
    target = coefficients.loc[coefficients["shock"].eq("target_factor_monthly_easing")].copy()
    target = target.sort_values(["channel", "response", "horizon_months"])
    excluded = pd.DataFrame(
        [{"response": key, "reason": value} for key, value in EXCLUDED_RESPONSES.items()]
    )
    top_cum = (
        cumulative.loc[
            cumulative["shock"].eq("target_factor_monthly_easing") & cumulative["horizon_months"].isin([12, 24])
        ]
        .sort_values(["horizon_months", "channel", "response"])
        .copy()
    )
    text = f"""# Monthly Reduced-Form Local Projections

This step estimates monthly responses to high-frequency ECB policy surprises. Coefficients are reported for a one-standard-deviation ECB surprise; unscaled coefficients are also kept for reference.

## Primary Target-Shock IRFs

{markdown_table(target, ["response_label", "channel", "horizon_months", "coefficient", "std_error_hac", "ci_90_low", "ci_90_high", "bootstrap_ci_90_low", "bootstrap_ci_90_high", "p_value", "nobs"], 36)}

## Cumulative Responses

{markdown_table(top_cum, ["response_label", "channel", "horizon_months", "cumulative_response", "ci_90_low", "ci_90_high"], 24)}

## Uncertainty

IRF tables include HAC/Newey-West confidence bands with horizon-specific bandwidth `h + 1`. Target-shock IRFs also include feasible circular-block residual percentile bootstrap intervals. Moving-block and wild bootstrap checks are used for cumulative bands. Cumulative responses support persistence language, not exact structural multipliers.

## Excluded Quarterly-Only Responses

{markdown_table(excluded, ["response", "reason"], 10)}

## Interpretation

Use this language: ECB monetary-policy surprises generate dynamic response patterns in monthly financial, housing-finance, real-activity, and negotiated-wage-pressure variables.

Avoid this language: these LPs identify structural QE treatment effects, exact housing-price effects, compensation-per-employee treatment effects, welfare effects, or redistribution magnitudes.
"""
    (DOCS_DIR / "monthly_reduced_form_lp.md").write_text(text, encoding="utf-8")


def write_specification_doc() -> None:
    text = """# Reduced-Form Specification

## Estimand

The empirical object is the dynamic response to a high-frequency ECB monetary-policy surprise aggregated to the month. The main shock is `target_factor_monthly_easing`; timing, forward-guidance, QE, and weighted-composite surprises are alternatives.

## Local Projection

```text
y_{t+h} - y_{t-1}
  = alpha_h + beta_h * surprise_t
    + phi_1 y_{t-1} + phi_2 y_{t-2}
    + gamma_1 inflation_{t-1} + gamma_2 inflation_{t-2}
    + delta_1 dfr_{t-1} + delta_2 dfr_{t-2}
    + epsilon_{t+h}
```

Horizon grid: `0, 1, 3, 6, 12, 24` months. Inference uses HAC/Newey-West covariance with horizon-specific bandwidth `h + 1`. The specification is not tuned by response variable.

## Normalization

`coefficient` is the response to a one-standard-deviation surprise shock. `raw_coefficient_per_unit_shock` preserves the unscaled regression coefficient. `coefficient_10bp_equiv` is an optional basis-point interpretation, conditional on treating factor units as basis points.

## Cumulative Responses

Cumulative tables sum normalized horizon coefficients. Cumulative confidence intervals use an independence approximation for the summed standard errors and are interpreted as descriptive persistence, not exact structural multipliers.

## Uncertainty

Each IRF row reports HAC/Newey-West confidence intervals with horizon-specific bandwidth `h + 1`; 68%, 90%, and 95% bands are retained. Target-shock IRFs also report feasible circular-block residual percentile bootstrap intervals. Moving-block, wild, block-length, and horizon-dependence checks are used to judge whether the persistence comparison is stable.

## Regime Decomposition

Regime estimates split the sample into pre-QE, QE, COVID, and tightening windows. They describe heterogeneity but are not separate regime treatment effects.

## Frequency Choice

No quarterly housing or compensation series is interpolated. The monthly comparison uses observed monthly housing-finance and wage-pressure proxies.
"""
    (DOCS_DIR / "final_reduced_form_specification.md").write_text(text, encoding="utf-8")


def write_bootstrap_doc(diagnostics: pd.DataFrame, block_sensitivity: pd.DataFrame) -> None:
    text = f"""# Bootstrap Methodology

The response tables keep HAC/Newey-West intervals and add dependence-aware bootstrap checks. The bootstrap changes uncertainty assessment, not the estimand.

## Methods

- Moving-block bootstrap: residual vectors are resampled in adjacent time blocks using a common draw across horizons for each response.
- Wild bootstrap: residual vectors are multiplied by common Rademacher shocks across horizons, preserving heteroskedasticity-sensitive cross-horizon comovement.
- Automatic block length: `max(6, round(n^(1/3)), min(12, max_horizon / 2))`; sensitivity checks report block lengths 4, 6, 9, 12, and automatic.
- Cumulative intervals: cumulative draws sum bootstrapped horizon coefficients from the same resample path, so horizon dependence is carried into the percentile envelope.

## Horizon Dependence Diagnostics

{markdown_table(diagnostics, ["response_label", "channel", "nobs_common_horizon_sample", "mean_adjacent_horizon_residual_corr", "max_abs_horizon_residual_corr"], 20)}

## Block-Length Sensitivity Preview

{markdown_table(block_sensitivity, ["response_label", "horizon_months", "block_length_setting", "interval_width_90", "bootstrap_replications"], 30)}

## Interpretation

Bootstrap ribbons and fan charts show sampling uncertainty under serial dependence, overlapping horizons, and small monthly samples. They support the persistence comparison but do not create new structural estimates.
"""
    (DOCS_DIR / "bootstrap_methodology.md").write_text(text, encoding="utf-8")


def write_intermediation_doc(
    timing_matrix: pd.DataFrame,
    credit_supply: pd.DataFrame,
    rankings: pd.DataFrame,
    sequence: pd.DataFrame,
) -> None:
    text = f"""# Banking And Lending Timing

This layer adds banking and lending evidence to the monthly response estimates. It is timing evidence for financial propagation, not a bank-channel treatment effect.

## Banking Timing Matrix

{markdown_table(timing_matrix, ["response_label", "channel", "frequency_integrity", "earliest_p10_horizon", "peak_abs_horizon", "cumulative_response", "direction", "status"], 30)}

## Credit Supply Response Table

{markdown_table(credit_supply, ["response_label", "channel", "frequency_integrity", "peak_response", "coefficient_1sd", "p_value", "timing_note"], 30)}

## Transmission Ranking

{markdown_table(rankings, ["response_label", "channel", "intermediation_timing_score", "early_timing_score", "persistence_rank", "direction", "frequency_integrity"], 30)}

## Sequential Timing Summary

{markdown_table(sequence, ["pathway", "upstream_label", "downstream_label", "shock_to_upstream_coef", "shock_to_downstream_coef", "timing_classification", "sequence_class", "language_guardrail"], 30)}

## Interpretation Boundary

Banking and lending variables are evaluated for whether they respond earlier or more persistently than housing-finance and wage-pressure proxies. That supports an intermediation reading, but not bank-to-distribution treatment-effect claims, exact structural magnitudes, or welfare interpretation.
"""
    (DOCS_DIR / "intermediation_mechanism_assessment.md").write_text(text, encoding="utf-8")
    (FINAL_MECHANISM / "banking_transmission_summary.md").write_text(text, encoding="utf-8")


def write_outputs(
    data: pd.DataFrame,
    coefficients: pd.DataFrame,
    cumulative: pd.DataFrame,
    regime_coefficients: pd.DataFrame,
    regime_cumulative: pd.DataFrame,
    stability: pd.DataFrame,
    stability_cumulative: pd.DataFrame,
    sign_matrix: pd.DataFrame,
    ranking: pd.DataFrame,
    rolling: pd.DataFrame,
    recursive: pd.DataFrame,
    ols_comparison: pd.DataFrame,
    horizon_significance: pd.DataFrame,
    significance_heatmap: pd.DataFrame,
    persistence_confidence: pd.DataFrame,
    peak_responses: pd.DataFrame,
    cumulative_persistence: pd.DataFrame,
    stability_metrics: pd.DataFrame,
    sequential_outputs: pd.DataFrame,
    moving_block_bootstrap: pd.DataFrame,
    wild_bootstrap: pd.DataFrame,
    bootstrap_sensitivity: pd.DataFrame,
    block_length_sensitivity: pd.DataFrame,
    horizon_dependence: pd.DataFrame,
    dependence_cumulative: pd.DataFrame,
    banking_timing_matrix: pd.DataFrame,
    credit_supply_response: pd.DataFrame,
    banking_transmission_rankings: pd.DataFrame,
    intermediation_sequence_summary: pd.DataFrame,
    banking_proxy_registry: pd.DataFrame,
) -> None:
    coefficients.to_csv(OUTPUT_DIR / "monthly_reduced_form_lp_coefficients.csv", index=False)
    cumulative.to_csv(OUTPUT_DIR / "monthly_reduced_form_lp_cumulative.csv", index=False)
    coefficients.to_csv(FINAL_TABLES / "monthly_reduced_form_lp_coefficients.csv", index=False)
    cumulative.to_csv(FINAL_TABLES / "monthly_reduced_form_lp_cumulative.csv", index=False)
    coefficients.to_csv(FINAL_TABLES / "normalized_irf_outputs.csv", index=False)
    cumulative.to_csv(FINAL_TABLES / "cumulative_transmission_outputs.csv", index=False)

    regime_coefficients.to_csv(OUTPUT_DIR / "monthly_regime_reduced_form_lp.csv", index=False)
    regime_cumulative.to_csv(OUTPUT_DIR / "monthly_regime_cumulative_transmission.csv", index=False)
    regime_coefficients.to_csv(FINAL_REGIME / "monthly_regime_reduced_form_lp.csv", index=False)
    regime_cumulative.to_csv(FINAL_REGIME / "monthly_regime_cumulative_transmission.csv", index=False)

    stability.to_csv(FINAL_STABILITY / "monthly_directional_stability_long.csv", index=False)
    stability_cumulative.to_csv(FINAL_STABILITY / "monthly_cumulative_stability_long.csv", index=False)
    sign_matrix.to_csv(FINAL_STABILITY / "monthly_directional_stability_matrix.csv", index=False)
    ranking.to_csv(FINAL_STABILITY / "monthly_persistence_ranking_stability.csv", index=False)
    rolling.to_csv(FINAL_STABILITY / "monthly_rolling_window_lp.csv", index=False)
    recursive.to_csv(FINAL_STABILITY / "monthly_recursive_window_lp.csv", index=False)
    stability_metrics.to_csv(FINAL_STABILITY / "monthly_stability_metrics.csv", index=False)
    stability_metrics.to_csv(FINAL_TABLES / "stability_metrics.csv", index=False)

    ols_comparison.to_csv(FINAL_ROBUSTNESS / "monthly_ols_policy_rate_comparison.csv", index=False)
    clean_event = stability.loc[
        stability["sample_name"].isin(["full", "clean_events_only", "contaminated_events_only"])
    ].copy()
    clean_event.to_csv(FINAL_ROBUSTNESS / "clean_event_robustness_outputs.csv", index=False)

    horizon_significance.to_csv(FINAL_UNCERTAINTY / "horizon_significance_table.csv", index=False)
    significance_heatmap.to_csv(FINAL_UNCERTAINTY / "significance_heatmap.csv", index=False)
    persistence_confidence.to_csv(FINAL_UNCERTAINTY / "persistence_confidence_matrix.csv", index=False)
    coefficients.to_csv(FINAL_UNCERTAINTY / "confidence_band_irfs.csv", index=False)
    cumulative.to_csv(FINAL_UNCERTAINTY / "cumulative_uncertainty_irfs.csv", index=False)
    moving_block_bootstrap.to_csv(FINAL_UNCERTAINTY / "moving_block_bootstrap_irfs.csv", index=False)
    wild_bootstrap.to_csv(FINAL_UNCERTAINTY / "wild_bootstrap_irfs.csv", index=False)
    bootstrap_sensitivity.to_csv(FINAL_UNCERTAINTY / "bootstrap_sensitivity_summary.csv", index=False)
    block_length_sensitivity.to_csv(FINAL_UNCERTAINTY / "block_length_sensitivity.csv", index=False)
    horizon_dependence.to_csv(FINAL_UNCERTAINTY / "horizon_dependence_diagnostics.csv", index=False)
    dependence_cumulative.to_csv(FINAL_UNCERTAINTY / "dependence_aware_cumulative_intervals.csv", index=False)
    peak_responses.to_csv(FINAL_TABLES / "peak_response_table.csv", index=False)
    cumulative_persistence.to_csv(FINAL_TABLES / "cumulative_persistence_table.csv", index=False)
    horizon_significance.to_csv(FINAL_TABLES / "horizon_significance_table.csv", index=False)

    sequential_outputs.to_csv(FINAL_MECHANISM / "sequential_transmission_outputs.csv", index=False)
    sequential_outputs.to_csv(FINAL_MECHANISM / "sequential_timing_outputs.csv", index=False)
    sequential_outputs.to_csv(FINAL_TABLES / "sequential_transmission_outputs.csv", index=False)
    banking_timing_matrix.to_csv(FINAL_MECHANISM / "banking_timing_matrix.csv", index=False)
    banking_timing_matrix.to_csv(FINAL_MECHANISM / "transmission_timing_tables.csv", index=False)
    credit_supply_response.to_csv(FINAL_MECHANISM / "credit_supply_response_table.csv", index=False)
    lending_conditions = credit_supply_response.loc[
        credit_supply_response["channel"].isin(["banking_lending_conditions", "bank_lending_survey"])
    ].copy()
    lending_conditions.to_csv(FINAL_MECHANISM / "lending_conditions_responses.csv", index=False)
    spread_responses = banking_timing_matrix.loc[
        banking_timing_matrix["response"].astype(str).str.contains("spread", case=False, na=False)
    ].copy()
    spread_responses.to_csv(FINAL_MECHANISM / "spread_responses.csv", index=False)
    banking_transmission_rankings.to_csv(FINAL_MECHANISM / "banking_transmission_rankings.csv", index=False)
    intermediation_sequence_summary.to_csv(FINAL_MECHANISM / "intermediation_sequence_summary.csv", index=False)
    banking_proxy_registry.to_csv(FINAL_MECHANISM / "banking_proxy_registry.csv", index=False)

    missing = pd.DataFrame(
        [{"response": key, "status": "excluded_no_monthly_interpolation", "reason": value} for key, value in EXCLUDED_RESPONSES.items()]
    )
    missing.to_csv(FINAL_DIAGNOSTICS / "monthly_response_exclusions.csv", index=False)

    for response in CANONICAL_COMPARISON_RESPONSES:
        write_svg_irf(coefficients, response)
        write_uncertainty_fan_svg(moving_block_bootstrap, response)
        write_cumulative_interval_svg(dependence_cumulative, response)
    heat_cols = [column for column in significance_heatmap.columns if re.fullmatch(r"h[0-9]+", column)]
    write_matrix_svg(
        significance_heatmap,
        FINAL_FIGURE_DIRS["uncertainty"] / "significance_heatmap.png",
        "Horizon Significance",
        heat_cols,
    )
    persistence_cols = [column for column in persistence_confidence.columns if re.fullmatch(r"h[0-9]+_cum90", column)]
    write_matrix_svg(
        persistence_confidence,
        FINAL_FIGURE_DIRS["stability"] / "persistence_confidence_matrix.png",
        "Cumulative 90% Confidence Persistence",
        persistence_cols,
    )
    write_rolling_stability_charts(rolling)
    write_clean_event_chart(stability)
    write_uncertainty_comparison_panel(bootstrap_sensitivity)
    write_regime_chart(regime_coefficients)
    write_banking_timing_chart(banking_timing_matrix)
    write_mechanism_sequence_chart(intermediation_sequence_summary)
    write_markdown(coefficients, cumulative)
    write_specification_doc()
    write_bootstrap_doc(horizon_dependence, block_length_sensitivity)
    write_intermediation_doc(
        banking_timing_matrix,
        credit_supply_response,
        banking_transmission_rankings,
        intermediation_sequence_summary,
    )


def main() -> None:
    ensure_dirs()
    data = load_data()
    available_responses = tuple(response for response in RESPONSE_SPECS if response in data.columns)
    coefficients, cumulative = run_lp(data, "full", available_responses, PRIMARY_SHOCKS)
    coefficients = add_bootstrap_intervals(data, coefficients)
    cumulative = cumulative_table(coefficients)
    regime_coefficients, regime_cumulative = regime_decomposition(data)
    stability, stability_cumulative, sign_matrix, ranking = stability_layer(data)
    rolling, recursive = rolling_recursive_layer(data)
    ols_comparison = ols_policy_rate_comparison(data, coefficients)
    horizon_significance, significance_heatmap, persistence_confidence = build_uncertainty_tables(coefficients, cumulative)
    (
        moving_block_bootstrap,
        wild_bootstrap,
        bootstrap_sensitivity,
        block_length_sensitivity,
        horizon_dependence,
        dependence_cumulative,
    ) = dependence_aware_uncertainty(data)
    peak_responses = build_peak_response_table(coefficients)
    cumulative_persistence = build_cumulative_persistence_table(cumulative)
    stability_metrics = build_stability_metrics(stability, stability_cumulative)
    sequential_outputs = sequential_transmission_analysis(data)
    (
        banking_timing_matrix,
        credit_supply_response,
        banking_transmission_rankings,
        intermediation_sequence_summary,
    ) = banking_timing_layer(data, coefficients, sequential_outputs)
    banking_proxy_registry = build_banking_proxy_registry(data)
    write_outputs(
        data,
        coefficients,
        cumulative,
        regime_coefficients,
        regime_cumulative,
        stability,
        stability_cumulative,
        sign_matrix,
        ranking,
        rolling,
        recursive,
        ols_comparison,
        horizon_significance,
        significance_heatmap,
        persistence_confidence,
        peak_responses,
        cumulative_persistence,
        stability_metrics,
        sequential_outputs,
        moving_block_bootstrap,
        wild_bootstrap,
        bootstrap_sensitivity,
        block_length_sensitivity,
        horizon_dependence,
        dependence_cumulative,
        banking_timing_matrix,
        credit_supply_response,
        banking_transmission_rankings,
        intermediation_sequence_summary,
        banking_proxy_registry,
    )
    print(f"Wrote normalized monthly reduced-form LP table: {FINAL_TABLES / 'normalized_irf_outputs.csv'}")
    print(f"Wrote final specification memo: {DOCS_DIR / 'final_reduced_form_specification.md'}")


if __name__ == "__main__":
    main()
