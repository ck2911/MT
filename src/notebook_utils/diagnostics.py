"""Small diagnostic summaries for notebook tables."""

from __future__ import annotations

import numpy as np
import pandas as pd


def first_stage_status(first_stage: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    if first_stage.empty:
        empty = pd.DataFrame()
        return empty, empty, empty, empty
    status = first_stage.groupby(["final_screen", "relevance_class"], dropna=False, as_index=False).size()
    status = status.rename(columns={"size": "instrument_target_pairs"})
    strongest = first_stage.sort_values("first_stage_f_stat", ascending=False)
    stability_sensitive = first_stage.loc[first_stage.get("final_screen", "").astype(str).str.contains("frag", case=False, na=False)]
    rejected = first_stage.loc[first_stage.get("final_screen", "").astype(str).str.contains("reject", case=False, na=False)]
    return status, strongest, stability_sensitive, rejected


def rolling_first_stage_summary(rolling_fs: pd.DataFrame) -> pd.DataFrame:
    if rolling_fs.empty:
        return pd.DataFrame()
    return rolling_fs.groupby(["target", "instrument"], as_index=False).agg(
        rolling_windows=("window", "count"),
        rolling_median_f=("first_stage_f_stat", "median"),
        rolling_min_f=("first_stage_f_stat", "min"),
        rolling_max_f=("first_stage_f_stat", "max"),
        rolling_sign_persistence=("sign", lambda s: s.value_counts(normalize=True).max() if len(s.dropna()) else np.nan),
        median_partial_r2=("partial_r_squared", "median"),
    )


def regime_first_stage_pivot(regime_fs: pd.DataFrame) -> pd.DataFrame:
    if regime_fs.empty:
        return pd.DataFrame()
    return regime_fs.pivot_table(index=["target", "instrument"], columns="regime", values="first_stage_f_stat", aggfunc="median").reset_index()


def target_lp_subset(lp: pd.DataFrame) -> pd.DataFrame:
    if lp.empty:
        return pd.DataFrame()
    return lp.loc[lp.get("shock", "").eq("target_factor_monthly_easing")].copy()


def econometric_framework(target_lp: pd.DataFrame) -> pd.DataFrame:
    if target_lp.empty:
        return pd.DataFrame()
    normalization = "1_sd_surprise"
    if "shock_normalization" in target_lp and target_lp["shock_normalization"].dropna().size:
        normalization = target_lp["shock_normalization"].dropna().mode().iloc[0]
    horizons = ""
    if "horizon_months" in target_lp:
        horizons = ", ".join(map(str, sorted(target_lp["horizon_months"].dropna().astype(int).unique())))
    return pd.DataFrame(
        [
            {
                "main_shock": "target_factor_monthly_easing",
                "shock_normalization": normalization,
                "horizon_grid_months": horizons,
                "responses_estimated": target_lp["response"].nunique() if "response" in target_lp else 0,
                "lp_cells": len(target_lp),
                "uncertainty": "HAC/Newey-West plus bootstrap bands where feasible",
            }
        ]
    )


def build_cross_variable_comparison(peak: pd.DataFrame, cumulative: pd.DataFrame, significance: pd.DataFrame) -> pd.DataFrame:
    if peak.empty:
        return pd.DataFrame()
    comparison = peak.copy()

    if not significance.empty and {"response", "horizon_months"}.issubset(significance.columns):
        rows = []
        group_cols = ["response", "response_label", "channel"]
        for (resp, label, channel), grp in significance.groupby(group_cols, dropna=False):
            flag = grp.get("hac_90_excludes_zero", pd.Series(False, index=grp.index)).fillna(False).astype(bool)
            rows.append(
                {
                    "response": resp,
                    "response_label": label,
                    "channel": channel,
                    "significant_horizons_90": int(flag.sum()),
                    "first_significant_horizon": grp.loc[flag, "horizon_months"].min() if flag.any() else np.nan,
                }
            )
        sig_summary = pd.DataFrame(rows)
        comparison = comparison.merge(sig_summary[["response", "significant_horizons_90", "first_significant_horizon"]], on="response", how="left")

    if not cumulative.empty and {"response", "horizon_months"}.issubset(cumulative.columns):
        h24 = cumulative.loc[
            cumulative.get("shock", pd.Series(dtype=str)).eq("target_factor_monthly_easing") & cumulative["horizon_months"].eq(24),
            ["response", "cumulative_response", "significant_90"],
        ].rename(columns={"cumulative_response": "cumulative_h24", "significant_90": "cumulative_h24_significant_90"})
        comparison = comparison.merge(h24, on="response", how="left")

    comparison["persistence"] = np.select(
        [
            comparison.get("cumulative_h24_significant_90", pd.Series(False, index=comparison.index)).fillna(False),
            comparison.get("significant_horizons_90", pd.Series(0, index=comparison.index)).fillna(0).ge(2),
        ],
        ["persistent cumulative", "multi-horizon visible"],
        default="limited / uncertain",
    )
    return comparison


def evidence_snippet(comparison: pd.DataFrame, channel_filter: list[str]) -> pd.DataFrame:
    if comparison.empty or "channel" not in comparison.columns:
        return pd.DataFrame()
    cols = [
        col
        for col in [
            "response_label",
            "channel",
            "peak_response",
            "peak_horizon_months",
            "significant_horizons_90",
            "cumulative_h24",
            "persistence",
        ]
        if col in comparison.columns
    ]
    return comparison.loc[comparison["channel"].isin(channel_filter), cols].sort_values(["channel", "response_label"])
