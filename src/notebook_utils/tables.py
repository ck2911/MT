"""Compact table display for the notebook."""

from __future__ import annotations

import html
from pathlib import Path
from typing import Iterable

import pandas as pd

from .display import HTML, Markdown, display
from .formatting import format_frame, select_existing

MAX_DISPLAY_ROWS = 8

COLUMN_LABELS = {
    "active_setting": "Active setting",
    "active_variables": "Active variables",
    "available": "Available",
    "channel": "Economic channel",
    "ci_90_high": "90% interval high",
    "ci_90_low": "90% interval low",
    "coefficient": "Response",
    "comments": "Comments",
    "conceptual_object": "Economic interpretation",
    "cumulative_h24": "24-month cumulative response",
    "cumulative_response": "Cumulative response",
    "decision": "Role",
    "direction": "Direction",
    "direction_sign": "Direction",
    "economic_role": "Economic role",
    "end": "Sample end",
    "evidence": "Evidence",
    "final_screen": "Assessment",
    "first_stage_f_stat": "First-stage F-stat",
    "first_significant_horizon": "First visible horizon",
    "frequency_integrity": "Frequency treatment",
    "horizon_months": "Horizon (months)",
    "interpretation": "Interpretation",
    "interpretation_layer": "Interpretation layer",
    "label": "Label",
    "modal_direction": "Direction",
    "observations": "Observations",
    "partial_r_squared": "Partial R-squared",
    "peak_abs_horizon": "Peak horizon",
    "peak_horizon_months": "Peak horizon",
    "peak_response": "Peak response",
    "persistence": "Persistence reading",
    "persistence_rank_within_subsample": "Persistence rank",
    "precision_reading": "Precision reading",
    "response_label": "Variable",
    "role": "Role",
    "rolling_sign_stability": "Rolling sign stability",
    "sample_end": "Sample end",
    "sample_name": "Sample",
    "sample_start": "Sample start",
    "side": "Domain",
    "sign_consistency": "Sign consistency",
    "significant_horizons_90": "Visible horizons",
    "start": "Sample start",
    "status": "Status",
    "target_label": "Policy bridge",
    "thesis_reading": "Thesis reading",
    "timing_classification": "Timing reading",
    "timing_note": "Timing note",
    "transmission_layer": "Transmission layer",
    "transmission_role": "Transmission role",
    "upstream_label": "Earlier response",
    "downstream_label": "Later response",
    "variable": "Variable",
    "verdict": "Reading",
}


def _display_columns(frame: pd.DataFrame) -> pd.DataFrame:
    return frame.rename(columns={column: COLUMN_LABELS.get(column, column.replace("_", " ").title()) for column in frame.columns})


def show_table(
    frame: pd.DataFrame | None,
    columns: list[str] | tuple[str, ...] | None = None,
    n: int = MAX_DISPLAY_ROWS,
    title: str | None = None,
    artifact: str | Path | Iterable[str | Path] | None = None,
    note: str | None = None,
) -> pd.DataFrame:
    """Display a compact, wrapped table."""

    del n  # Keep one table-length rule throughout the notebook.
    if title:
        display(Markdown(f"**{title}**"))

    if frame is None or frame.empty:
        display(Markdown("_No rows available from the current artifact set._"))
        return pd.DataFrame()

    source = frame
    out = source.copy()
    if columns:
        out = select_existing(out, columns)
    out = format_frame(out.head(MAX_DISPLAY_ROWS))

    table_html = _display_columns(out).to_html(index=False, escape=True, border=0, classes="thesis-table")
    display(HTML(f"<div class='thesis-table-wrap'>{table_html}</div>"))

    if note:
        display(HTML(f"<div class='thesis-note'>{html.escape(note)}</div>"))
    return out
