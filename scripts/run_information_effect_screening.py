#!/usr/bin/env python3
from __future__ import annotations

import os
import tempfile
from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
os.environ.setdefault("MPLCONFIGDIR", str(Path(tempfile.gettempdir()) / "thesis_model_mpl_cache"))

EVENT_DATA = ROOT / "data" / "processed" / "eu_de" / "ecb_surprise_event_level.csv"
OUTPUT_DIR = ROOT / "results" / "identification_rebuild"
FINAL_DIAGNOSTICS = ROOT / "results" / "final" / "diagnostics"
DOCS_DIR = ROOT / "results" / "final" / "memos"  # working notes; docs/ holds only the curated notes


def sign_label(value: object, tolerance: float = 1e-12) -> str:
    if pd.isna(value):
        return "missing"
    numeric = float(value)
    if abs(numeric) <= tolerance:
        return "zero"
    return "positive" if numeric > 0 else "negative"


def classify(row: pd.Series) -> str:
    yield_sign = row["yield_response_sign"]
    equity_sign = row["equity_response_sign"]
    factor_sign = row["rate_factor_sign"]
    if "missing" in {yield_sign, equity_sign}:
        return "not_classified_missing_market_response"
    if "zero" in {yield_sign, equity_sign}:
        return "ambiguous_zero_response"
    if factor_sign not in {"missing", "zero"} and factor_sign != yield_sign:
        return "mixed_sign_factor_yield_conflict"
    if yield_sign == equity_sign:
        return "possible_information_shock"
    return "possible_pure_monetary_shock"


def load_events() -> pd.DataFrame:
    if not EVENT_DATA.exists():
        raise FileNotFoundError(f"Missing event-level surprise data: {EVENT_DATA}")
    events = pd.read_csv(EVENT_DATA, parse_dates=["event_date"])
    for column in [
        "target_factor",
        "timing_factor",
        "fg_factor",
        "qe_factor",
        "ois_1m_mew",
        "ois_6m_mew",
        "stoxx50_mew",
        "bank_stoxx_mew",
    ]:
        if column in events.columns:
            events[column] = pd.to_numeric(events[column], errors="coerce")
    events["rate_factor_for_screen"] = events["target_factor"].where(events["target_factor"].notna(), events["timing_factor"])
    events["yield_response_for_screen"] = events["ois_6m_mew"].where(events["ois_6m_mew"].notna(), events["timing_factor"])
    events["equity_response_for_screen"] = events["stoxx50_mew"]
    events["rate_factor_sign"] = events["rate_factor_for_screen"].map(sign_label)
    events["yield_response_sign"] = events["yield_response_for_screen"].map(sign_label)
    events["equity_response_sign"] = events["equity_response_for_screen"].map(sign_label)
    events["information_effect_screen"] = events.apply(classify, axis=1)
    events["ois_movement"] = events["yield_response_for_screen"]
    events["equity_window_response"] = events["equity_response_for_screen"]
    events["contamination_classification"] = events["information_effect_screen"]
    events["contamination_flag"] = events["information_effect_screen"].isin(
        {
            "possible_information_shock",
            "mixed_sign_factor_yield_conflict",
            "ambiguous_zero_response",
            "not_classified_missing_market_response",
        }
    )
    events["monthly_identification_window"] = events["event_date"].between("2005-01-01", "2025-10-31")
    return events


def summaries(screen: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    summary = (
        screen.groupby("information_effect_screen")
        .size()
        .reset_index(name="event_count")
        .sort_values("event_count", ascending=False)
    )
    summary["share"] = summary["event_count"] / summary["event_count"].sum()
    regime = (
        screen.groupby(["regime", "information_effect_screen"], dropna=False)
        .size()
        .reset_index(name="event_count")
        .sort_values(["regime", "information_effect_screen"])
    )
    regime["share_within_regime"] = regime["event_count"] / regime.groupby("regime")["event_count"].transform("sum")
    return summary, regime


def fmt(value: object) -> str:
    if pd.isna(value):
        return ""
    if isinstance(value, (float, np.floating)):
        return f"{float(value):.3f}"
    return str(value)


def markdown_table(frame: pd.DataFrame, columns: list[str], max_rows: int = 20) -> str:
    if frame.empty:
        return "_No available rows._"
    display = frame.loc[:, [column for column in columns if column in frame.columns]].head(max_rows)
    header = "| " + " | ".join(display.columns) + " |"
    divider = "| " + " | ".join(["---"] * len(display.columns)) + " |"
    rows = ["| " + " | ".join(fmt(row[column]) for column in display.columns) + " |" for _, row in display.iterrows()]
    return "\n".join([header, divider, *rows])


def write_outputs(events: pd.DataFrame, summary: pd.DataFrame, regime: pd.DataFrame) -> None:
    for path in (OUTPUT_DIR, FINAL_DIAGNOSTICS, DOCS_DIR):
        path.mkdir(parents=True, exist_ok=True)
    columns = [
        "event_id",
        "event_date",
        "event_quarter",
        "regime",
        "target_factor",
        "timing_factor",
        "ois_1m_mew",
        "ois_6m_mew",
        "stoxx50_mew",
        "rate_factor_for_screen",
        "yield_response_for_screen",
        "equity_response_for_screen",
        "ois_movement",
        "equity_window_response",
        "rate_factor_sign",
        "yield_response_sign",
        "equity_response_sign",
        "information_effect_screen",
        "contamination_classification",
        "contamination_flag",
        "monthly_identification_window",
    ]
    screen = events[columns].copy()
    clean = screen.loc[screen["monthly_identification_window"] & ~screen["contamination_flag"]].copy()
    contaminated = screen.loc[screen["monthly_identification_window"] & screen["contamination_flag"]].copy()
    screen.to_csv(OUTPUT_DIR / "information_effect_event_screen.csv", index=False)
    clean.to_csv(OUTPUT_DIR / "clean_event_sample.csv", index=False)
    contaminated.to_csv(OUTPUT_DIR / "contaminated_event_sample.csv", index=False)
    summary.to_csv(OUTPUT_DIR / "information_effect_summary.csv", index=False)
    regime.to_csv(OUTPUT_DIR / "information_effect_regime_summary.csv", index=False)
    screen.to_csv(FINAL_DIAGNOSTICS / "information_effect_event_screen.csv", index=False)
    clean.to_csv(FINAL_DIAGNOSTICS / "clean_event_sample.csv", index=False)
    contaminated.to_csv(FINAL_DIAGNOSTICS / "contaminated_event_sample.csv", index=False)
    summary.to_csv(FINAL_DIAGNOSTICS / "information_effect_summary.csv", index=False)
    regime.to_csv(FINAL_DIAGNOSTICS / "information_effect_regime_summary.csv", index=False)
    write_doc(screen, summary, regime)


def write_doc(screen: pd.DataFrame, summary: pd.DataFrame, regime: pd.DataFrame) -> None:
    active = screen.loc[screen["monthly_identification_window"]].copy()
    active_summary = (
        active.groupby("information_effect_screen")
        .size()
        .reset_index(name="event_count")
        .sort_values("event_count", ascending=False)
    )
    active_summary["share"] = active_summary["event_count"] / active_summary["event_count"].sum()
    flagged = active.loc[active["contamination_flag"]].sort_values("event_date").tail(12)
    flagged = flagged.copy()
    flagged["event_date"] = pd.to_datetime(flagged["event_date"]).dt.strftime("%Y-%m-%d")
    text = f"""# Information-Effect Screen

This screen compares three event-level signs:

- rate-factor sign: `target_factor` when available, otherwise `timing_factor`;
- yield-window sign: `OIS_6M` from the EA-MPD monetary-event window when available;
- equity-window sign: `STOXX50` from the same event window.

Same-sign yield and equity moves are flagged as possible central-bank information shocks. Opposite-sign yield and equity moves are treated as possible pure monetary shocks. Factor-yield sign conflicts and missing/zero market windows are contamination flags, not exclusions by themselves.

## Full Event Screen

{markdown_table(summary, ["information_effect_screen", "event_count", "share"], 10)}

## Monthly Identification Window

{markdown_table(active_summary, ["information_effect_screen", "event_count", "share"], 10)}

## Regime Summary

{markdown_table(regime, ["regime", "information_effect_screen", "event_count", "share_within_regime"], 24)}

## Recent Flagged Events

{markdown_table(flagged, ["event_date", "event_quarter", "regime", "rate_factor_sign", "yield_response_sign", "equity_response_sign", "information_effect_screen"], 12)}

## Use In The Thesis

These flags identify events whose market reaction may contain central-bank information or sign conflicts. They do not prove exogeneity. They are used to check whether the main housing-versus-compensation result survives cleaner event samples.
"""
    (DOCS_DIR / "information_effect_screening.md").write_text(text, encoding="utf-8")


def main() -> None:
    events = load_events()
    summary, regime = summaries(events)
    write_outputs(events, summary, regime)
    print(f"Wrote information-effect screen: {OUTPUT_DIR / 'information_effect_event_screen.csv'}")
    print(f"Wrote information-effect memo: {DOCS_DIR / 'information_effect_screening.md'}")


if __name__ == "__main__":
    main()
