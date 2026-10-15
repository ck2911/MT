#!/usr/bin/env python3
from __future__ import annotations

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

from src.lpiv.ols_hac import add_constant, fit_ols_hac

MONTHLY_DATASET = ROOT / "data" / "processed" / "eu_de" / "final_monthly_model_dataset.csv"
OUTPUT_DIR = ROOT / "results" / "identification_rebuild"
FINAL_DIAGNOSTICS = ROOT / "results" / "final" / "diagnostics"
DOCS_DIR = ROOT / "results" / "final" / "memos"  # working notes; docs/ holds only the curated notes

INSTRUMENT_CANDIDATES = (
    "timing_factor_monthly_easing",
    "target_factor_monthly_easing",
    "fg_factor_monthly_easing",
    "qe_factor_monthly_easing",
    "weighted_composite_monthly_easing",
)

TREATMENT_CANDIDATES = {
    "d_wx_shadow_rate": {
        "label": "shadow rate",
        "family": "policy-rate bridge",
        "interpretation": "Monthly change in the Wu-Xia shadow rate; best local proxy for the stance variable in the lower-bound period.",
    },
    "d_dfr_eop": {
        "label": "deposit facility rate, end of month",
        "family": "policy-rate bridge",
        "interpretation": "Observed policy-rate implementation; conventional short-rate channel, but discrete and often unchanged.",
    },
    "d_dfr_mavg": {
        "label": "deposit facility rate, monthly average",
        "family": "policy-rate bridge",
        "interpretation": "Monthly-average policy-rate implementation; smoother than end-of-month DFR but still mechanically administered.",
    },
    "d_ln_ecb_assets_ea_stock": {
        "label": "ECB assets, log end-of-month stock",
        "family": "liquidity stock",
        "interpretation": "Balance-sheet/liquidity response candidate; retained as secondary because it is a persistent implementation stock.",
    },
    "d_ln_ecb_assets_ea_mavg": {
        "label": "ECB assets, log monthly average",
        "family": "liquidity stock",
        "interpretation": "Monthly-average balance-sheet response candidate; secondary, not a preferred causal treatment.",
    },
    "d_ln_dax_real_de": {
        "label": "real DAX",
        "family": "macro-financial response",
        "interpretation": "QE-sensitive market response bridge; useful for transmission timing, not a policy implementation variable.",
    },
    "d_ln_hh_loans_ea_stock": {
        "label": "household credit",
        "family": "credit response",
        "interpretation": "Transmission response candidate; should not be confused with the policy innovation.",
    },
    "d_ln_nfc_loans_ea_stock": {
        "label": "NFC credit",
        "family": "credit response",
        "interpretation": "Transmission response candidate for productive credit; not a policy variable.",
    },
    "d_ln_retail_de_chained_index": {
        "label": "German retail volume",
        "family": "purchasing-power proxy",
        "interpretation": "Monthly real-activity/purchasing-power proxy. It is not compensation and should not be narrated as wages.",
    },
}

UNAVAILABLE_CANDIDATES = (
    ("2Y Bund yield", "not present in raw or processed local data", "do not proxy mechanically with DFR"),
    ("ESTR / EONIA", "not present in raw or processed local data", "DFR is only an administered-rate proxy"),
    ("term spread", "not present in raw or processed local data", "requires yield-curve source before inclusion"),
    ("sovereign spread", "not present in raw or processed local data", "requires sovereign-yield source before inclusion"),
    ("excess liquidity", "not present as official series", "ECB assets are retained only as a liquidity-stock proxy"),
    ("liquidity spreads", "not present in raw or processed local data", "requires money-market spread source before inclusion"),
)


@dataclass(frozen=True)
class FirstStageFit:
    observations: int
    sample_start: str
    sample_end: str
    coefficient: float
    std_error_hac: float
    t_stat_hac: float
    p_value_hac: float
    first_stage_f_stat: float
    partial_r_squared: float
    full_r_squared: float
    sign: str


def ensure_dirs() -> None:
    for path in (OUTPUT_DIR, FINAL_DIAGNOSTICS, DOCS_DIR):
        path.mkdir(parents=True, exist_ok=True)


def load_monthly_data(path: Path = MONTHLY_DATASET) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(f"Missing monthly model dataset: {path}")
    data = pd.read_csv(path, parse_dates=["date"]).sort_values("date").reset_index(drop=True)
    for column in data.columns:
        if column not in {"date", "month", "quarter", "lp_monthly_regime", "regime", "identification_regime"}:
            data[column] = pd.to_numeric(data[column], errors="coerce")
    return data


def add_lags(data: pd.DataFrame) -> pd.DataFrame:
    frame = data.copy()
    lag_sources = set(TREATMENT_CANDIDATES).union({"inflation_ea20_mom"})
    for source in sorted(lag_sources):
        if source not in frame.columns:
            continue
        for lag in (1, 2):
            frame[f"L{lag}_{source}"] = frame[source].shift(lag)
    return frame


def controls_for_target(data: pd.DataFrame, target: str) -> list[str]:
    controls = [f"L1_{target}", f"L2_{target}", "inflation_ea20_mom", "L1_inflation_ea20_mom"]
    return [column for column in controls if column in data.columns]


def safe_sign(value: float) -> str:
    if pd.isna(value):
        return ""
    if math.isclose(float(value), 0.0, abs_tol=1e-12):
        return "zero"
    return "positive" if value > 0 else "negative"


def fit_first_stage(
    data: pd.DataFrame,
    target: str,
    instrument: str,
    controls: list[str],
    min_obs: int = 36,
) -> FirstStageFit:
    required = [target, instrument, *controls]
    clean = data.dropna(subset=required).copy()
    empty = FirstStageFit(
        observations=int(clean.shape[0]),
        sample_start="",
        sample_end="",
        coefficient=np.nan,
        std_error_hac=np.nan,
        t_stat_hac=np.nan,
        p_value_hac=np.nan,
        first_stage_f_stat=np.nan,
        partial_r_squared=np.nan,
        full_r_squared=np.nan,
        sign="",
    )
    if clean.shape[0] < max(min_obs, len(controls) + 8):
        return empty
    if clean[target].nunique(dropna=True) < 3 or clean[instrument].nunique(dropna=True) < 3:
        return empty

    y = clean[target].astype(float).to_numpy()
    full_x, full_names = add_constant(clean[[instrument, *controls]].astype(float).to_numpy(), [instrument, *controls])
    restricted_x, restricted_names = add_constant(clean[controls].astype(float).to_numpy(), controls)
    full = fit_ols_hac(y, full_x, full_names, maxlags=3)
    restricted = fit_ols_hac(y, restricted_x, restricted_names, maxlags=0)

    restricted_rss = float(np.sum(restricted.resid**2))
    unrestricted_rss = float(np.sum(full.resid**2))
    improvement = max(0.0, restricted_rss - unrestricted_rss)
    denominator = unrestricted_rss / max(int(full.df_resid), 1)
    f_stat = np.nan if denominator <= 0 else improvement / denominator
    partial_r2 = np.nan if restricted_rss <= 0 else max(0.0, min(1.0, improvement / restricted_rss))
    coef = float(full.params[instrument])

    return FirstStageFit(
        observations=int(clean.shape[0]),
        sample_start=str(clean["month"].iloc[0]) if "month" in clean else str(clean["date"].min().date()),
        sample_end=str(clean["month"].iloc[-1]) if "month" in clean else str(clean["date"].max().date()),
        coefficient=coef,
        std_error_hac=float(full.bse[instrument]),
        t_stat_hac=float(full.tvalues[instrument]),
        p_value_hac=float(full.pvalues[instrument]),
        first_stage_f_stat=float(f_stat),
        partial_r_squared=float(partial_r2),
        full_r_squared=float(full.rsquared),
        sign=safe_sign(coef),
    )


def weak_class(f_stat: float) -> str:
    if pd.isna(f_stat):
        return "not_available"
    if f_stat >= 16.38:
        return "strong_F16"
    if f_stat >= 10:
        return "usable_F10"
    if f_stat >= 5:
        return "borderline"
    return "weak"


def rolling_relevance(data: pd.DataFrame, target: str, instrument: str, controls: list[str]) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    required = [target, instrument, *controls]
    clean = data.dropna(subset=required).reset_index(drop=True)
    window = 60
    min_obs = 48
    for end in range(window, clean.shape[0] + 1):
        sample = clean.iloc[end - window : end].copy()
        fit = fit_first_stage(sample, target, instrument, controls, min_obs=min_obs)
        rows.append(
            {
                "target": target,
                "instrument": instrument,
                "window": window,
                "rolling_start": sample["month"].iloc[0],
                "rolling_end": sample["month"].iloc[-1],
                "observations": fit.observations,
                "first_stage_f_stat": fit.first_stage_f_stat,
                "partial_r_squared": fit.partial_r_squared,
                "coefficient": fit.coefficient,
                "sign": fit.sign,
            }
        )
    return pd.DataFrame(rows)


def regime_relevance(data: pd.DataFrame, target: str, instrument: str, controls: list[str]) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    for regime, subset in data.groupby("lp_monthly_regime", dropna=False):
        fit = fit_first_stage(subset, target, instrument, controls, min_obs=18)
        rows.append(
            {
                "target": target,
                "instrument": instrument,
                "regime": regime,
                "observations": fit.observations,
                "sample_start": fit.sample_start,
                "sample_end": fit.sample_end,
                "first_stage_f_stat": fit.first_stage_f_stat,
                "partial_r_squared": fit.partial_r_squared,
                "coefficient": fit.coefficient,
                "sign": fit.sign,
                "relevance_class": weak_class(fit.first_stage_f_stat),
            }
        )
    return pd.DataFrame(rows)


def event_sensitivity(data: pd.DataFrame, target: str, instrument: str, controls: list[str], baseline_f: float) -> dict[str, float]:
    required = [target, instrument, *controls]
    clean = data.dropna(subset=required).copy()
    if clean.empty:
        return {
            "top5_abs_shock_share": np.nan,
            "jackknife_without_top5_f_stat": np.nan,
            "jackknife_f_ratio": np.nan,
        }
    abs_shock = clean[instrument].abs()
    total_abs = abs_shock.sum()
    top_n = max(1, min(5, math.ceil(clean.shape[0] * 0.05)))
    top_index = abs_shock.nlargest(top_n).index
    top_share = float(abs_shock.loc[top_index].sum() / total_abs) if total_abs and not np.isclose(total_abs, 0.0) else np.nan
    jackknife_fit = fit_first_stage(clean.drop(index=top_index), target, instrument, controls, min_obs=36)
    ratio = (
        float(jackknife_fit.first_stage_f_stat / baseline_f)
        if pd.notna(jackknife_fit.first_stage_f_stat) and pd.notna(baseline_f) and baseline_f > 0
        else np.nan
    )
    return {
        "top5_abs_shock_share": top_share,
        "jackknife_without_top5_f_stat": jackknife_fit.first_stage_f_stat,
        "jackknife_f_ratio": ratio,
    }


def summarize_rolling(rolling: pd.DataFrame, full_signs: pd.DataFrame) -> pd.DataFrame:
    if rolling.empty:
        return pd.DataFrame()
    sign_lookup = full_signs.set_index(["target", "instrument"])["sign"].to_dict()

    def sign_stability(group: pd.DataFrame) -> float:
        key = group.name if isinstance(group.name, tuple) else ("", "")
        sign = sign_lookup.get(key, "")
        signs = group["sign"].replace("", np.nan).dropna()
        if not sign or signs.empty:
            return np.nan
        return float((signs == sign).mean())

    return (
        rolling.groupby(["target", "instrument"], as_index=False)
        .agg(
            rolling_windows=("first_stage_f_stat", "count"),
            rolling_median_f=("first_stage_f_stat", "median"),
            rolling_min_f=("first_stage_f_stat", "min"),
            rolling_max_f=("first_stage_f_stat", "max"),
            rolling_sign_stability=("sign", lambda x: np.nan),
        )
        .drop(columns=["rolling_sign_stability"])
        .merge(
            rolling.groupby(["target", "instrument"]).apply(sign_stability).rename("rolling_sign_stability").reset_index(),
            on=["target", "instrument"],
            how="left",
        )
    )


def summarize_regimes(regime: pd.DataFrame, full_signs: pd.DataFrame) -> pd.DataFrame:
    if regime.empty:
        return pd.DataFrame()
    sign_lookup = full_signs.set_index(["target", "instrument"])["sign"].to_dict()

    def stable_share(group: pd.DataFrame) -> float:
        key = group.name if isinstance(group.name, tuple) else ("", "")
        sign = sign_lookup.get(key, "")
        signs = group.loc[group["observations"].ge(18), "sign"].replace("", np.nan).dropna()
        if not sign or signs.empty:
            return np.nan
        return float((signs == sign).mean())

    return (
        regime.groupby(["target", "instrument"], as_index=False)
        .agg(
            regime_count=("regime", "count"),
            regime_estimated_count=("first_stage_f_stat", lambda x: int(x.notna().sum())),
            regime_max_f=("first_stage_f_stat", "max"),
            regime_median_f=("first_stage_f_stat", "median"),
        )
        .merge(
            regime.groupby(["target", "instrument"]).apply(stable_share).rename("regime_sign_stability").reset_index(),
            on=["target", "instrument"],
            how="left",
        )
    )


def final_screen(row: pd.Series) -> str:
    f_stat = row.get("first_stage_f_stat", np.nan)
    rolling_sign = row.get("rolling_sign_stability", np.nan)
    jackknife = row.get("jackknife_f_ratio", np.nan)
    if pd.isna(f_stat):
        return "not_available"
    if f_stat >= 10 and (pd.isna(rolling_sign) or rolling_sign >= 0.6) and (pd.isna(jackknife) or jackknife >= 0.5):
        return "candidate"
    if f_stat >= 5:
        return "fragile_candidate"
    return "reject_weak_relevance"


def build_tournament(data: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    rows: list[dict[str, object]] = []
    rolling_frames: list[pd.DataFrame] = []
    regime_frames: list[pd.DataFrame] = []
    event_rows: list[dict[str, object]] = []

    for target, meta in TREATMENT_CANDIDATES.items():
        if target not in data.columns:
            continue
        controls = controls_for_target(data, target)
        for instrument in INSTRUMENT_CANDIDATES:
            if instrument not in data.columns:
                continue
            fit = fit_first_stage(data, target, instrument, controls)
            sensitivity = event_sensitivity(data, target, instrument, controls, fit.first_stage_f_stat)
            row = {
                "target": target,
                "target_label": meta["label"],
                "target_family": meta["family"],
                "instrument": instrument,
                "controls": ",".join(controls),
                "observations": fit.observations,
                "sample_start": fit.sample_start,
                "sample_end": fit.sample_end,
                "coefficient": fit.coefficient,
                "std_error_hac": fit.std_error_hac,
                "t_stat_hac": fit.t_stat_hac,
                "p_value_hac": fit.p_value_hac,
                "first_stage_f_stat": fit.first_stage_f_stat,
                "partial_r_squared": fit.partial_r_squared,
                "full_r_squared": fit.full_r_squared,
                "sign": fit.sign,
                "relevance_class": weak_class(fit.first_stage_f_stat),
                "interpretation": meta["interpretation"],
            }
            row.update(sensitivity)
            rows.append(row)
            event_rows.append({"target": target, "instrument": instrument, **sensitivity})
            rolling_frames.append(rolling_relevance(data, target, instrument, controls))
            regime_frames.append(regime_relevance(data, target, instrument, controls))

    full = pd.DataFrame(rows)
    rolling = pd.concat(rolling_frames, ignore_index=True) if rolling_frames else pd.DataFrame()
    regimes = pd.concat(regime_frames, ignore_index=True) if regime_frames else pd.DataFrame()
    if full.empty:
        return full, rolling, regimes, pd.DataFrame(event_rows)

    rolling_summary = summarize_rolling(rolling, full)
    regime_summary = summarize_regimes(regimes, full)
    tournament = (
        full.merge(rolling_summary, on=["target", "instrument"], how="left")
        .merge(regime_summary, on=["target", "instrument"], how="left")
        .sort_values(["first_stage_f_stat", "partial_r_squared"], ascending=False, na_position="last")
    )
    tournament["final_screen"] = tournament.apply(final_screen, axis=1)
    tournament["rank"] = np.arange(1, tournament.shape[0] + 1)
    return tournament, rolling, regimes, pd.DataFrame(event_rows)


def format_number(value: object, digits: int = 3) -> str:
    if pd.isna(value):
        return ""
    if isinstance(value, (int, np.integer)):
        return str(int(value))
    if isinstance(value, (float, np.floating)):
        return f"{float(value):.{digits}f}"
    return str(value)


def markdown_table(frame: pd.DataFrame, columns: list[str], max_rows: int = 12) -> str:
    if frame.empty:
        return "_No available rows._"
    display = frame.loc[:, [column for column in columns if column in frame.columns]].head(max_rows).copy()
    header = "| " + " | ".join(display.columns) + " |"
    divider = "| " + " | ".join(["---"] * len(display.columns)) + " |"
    rows = []
    for _, row in display.iterrows():
        rows.append("| " + " | ".join(format_number(row[column]) for column in display.columns) + " |")
    return "\n".join([header, divider, *rows])


def write_outputs(tournament: pd.DataFrame, rolling: pd.DataFrame, regimes: pd.DataFrame, event_sensitivity_frame: pd.DataFrame) -> None:
    tournament_path = OUTPUT_DIR / "monthly_first_stage_tournament.csv"
    rolling_path = OUTPUT_DIR / "monthly_first_stage_rolling.csv"
    regime_path = OUTPUT_DIR / "monthly_first_stage_regime.csv"
    event_path = OUTPUT_DIR / "monthly_first_stage_event_sensitivity.csv"
    tournament.to_csv(tournament_path, index=False)
    rolling.to_csv(rolling_path, index=False)
    regimes.to_csv(regime_path, index=False)
    event_sensitivity_frame.to_csv(event_path, index=False)

    tournament.to_csv(FINAL_DIAGNOSTICS / "monthly_first_stage_tournament.csv", index=False)
    rolling.to_csv(FINAL_DIAGNOSTICS / "monthly_first_stage_rolling.csv", index=False)
    regimes.to_csv(FINAL_DIAGNOSTICS / "monthly_first_stage_regime.csv", index=False)
    event_sensitivity_frame.to_csv(FINAL_DIAGNOSTICS / "monthly_first_stage_event_sensitivity.csv", index=False)
    write_markdown(tournament)


def write_markdown(tournament: pd.DataFrame) -> None:
    unavailable = pd.DataFrame(
        UNAVAILABLE_CANDIDATES,
        columns=["requested_candidate", "status", "governance_decision"],
    )
    target_best = (
        tournament.sort_values(["first_stage_f_stat", "partial_r_squared"], ascending=False, na_position="last")
        .groupby(["target", "target_label", "target_family"], as_index=False)
        .first()
        .sort_values("first_stage_f_stat", ascending=False, na_position="last")
    )
    accepted = tournament.loc[tournament["final_screen"].eq("candidate")].copy()
    fragile = tournament.loc[tournament["final_screen"].eq("fragile_candidate")].copy()
    top_policy = tournament.loc[tournament["target_family"].eq("policy-rate bridge")].head(10)
    top_liquidity = tournament.loc[tournament["target_family"].eq("liquidity stock")].head(10)
    top_responses = tournament.loc[~tournament["target_family"].isin(["policy-rate bridge", "liquidity stock"])].head(10)

    selected_line = "No candidate clears the full stability screen."
    if not accepted.empty:
        selected = accepted.sort_values(["first_stage_f_stat", "rolling_sign_stability"], ascending=False).iloc[0]
        selected_line = (
            f"The strongest screen-passing bridge is `{selected['target']}` instrumented by "
            f"`{selected['instrument']}` (F={selected['first_stage_f_stat']:.2f}, "
            f"partial R2={selected['partial_r_squared']:.3f})."
        )
    elif not fragile.empty:
        selected = fragile.sort_values(["first_stage_f_stat", "rolling_sign_stability"], ascending=False).iloc[0]
        selected_line = (
            f"No bridge passes the full stability screen. The least weak fragile candidate is "
            f"`{selected['target']}` with `{selected['instrument']}` "
            f"(F={selected['first_stage_f_stat']:.2f})."
        )

    unavailable_display = unavailable.rename(columns={"governance_decision": "note"})

    text = f"""# First-Stage Screen

This screen asks whether ECB policy-news shocks are strong enough to instrument monthly bridge variables. It is a relevance check, not a response result.

## Decision

{selected_line}

ECB asset stocks remain useful liquidity responses. They are not selected as the main treatment just because the older quarterly design used them.

## Available Candidate Winners

{markdown_table(target_best, ["target", "target_family", "instrument", "observations", "first_stage_f_stat", "partial_r_squared", "rolling_sign_stability", "jackknife_f_ratio", "final_screen"], 15)}

## Requested Candidates Not Locally Available

{markdown_table(unavailable_display, ["requested_candidate", "status", "note"], 10)}

## Policy-Rate Bridge Leaders

{markdown_table(top_policy, ["target", "instrument", "observations", "first_stage_f_stat", "partial_r_squared", "coefficient", "sign", "rolling_sign_stability", "final_screen"], 10)}

## Liquidity-Stock Leaders

{markdown_table(top_liquidity, ["target", "instrument", "observations", "first_stage_f_stat", "partial_r_squared", "coefficient", "sign", "rolling_sign_stability", "final_screen"], 10)}

## Transmission-Response Leaders

{markdown_table(top_responses, ["target", "target_family", "instrument", "observations", "first_stage_f_stat", "partial_r_squared", "coefficient", "sign", "rolling_sign_stability", "final_screen"], 10)}

## Reading Rules

- `candidate`: F >= 10 and no stability screen failure.
- `fragile_candidate`: F >= 5 but below the main relevance gate or stability is thin.
- `reject_weak_relevance`: F < 5.
- Rolling relevance uses 60-month windows.
- Event sensitivity drops the five largest absolute instrument months and recomputes the first stage.

## Interpretation

If no bridge variable remains strong after stability and event-sensitivity checks, the thesis should use monthly reduced-form local projections and treat the high-frequency surprises as policy-news shocks rather than forcing a structural IV claim.
"""
    (DOCS_DIR / "first_stage_tournament.md").write_text(text, encoding="utf-8")


def main() -> None:
    ensure_dirs()
    data = add_lags(load_monthly_data())
    tournament, rolling, regimes, event_sensitivity_frame = build_tournament(data)
    write_outputs(tournament, rolling, regimes, event_sensitivity_frame)
    print(f"Wrote first-stage tournament: {OUTPUT_DIR / 'monthly_first_stage_tournament.csv'}")
    print(f"Wrote tournament memo: {DOCS_DIR / 'first_stage_tournament.md'}")


if __name__ == "__main__":
    main()
