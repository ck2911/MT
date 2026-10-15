"""Formatting helpers for compact tables."""

from __future__ import annotations

import pandas as pd

VALUE_REPLACEMENTS = {
    "fragile_candidate": "usable with stability caveat",
    "strong_F16": "acceptable F-stat",
    "usable_F10": "usable F-stat",
    "borderline": "moderate",
    "rejected_weak_or_unstable": "not retained",
    "negative_not_significant": "negative, limited precision",
    "positive_not_significant": "positive, limited precision",
    "not_significant": "limited precision",
    "directional robustness, not exact magnitude invariance": "Direction is fairly stable; magnitudes are best read comparatively.",
    "ARCHIVED / LEGACY": "archived",
    "ARCHIVED / DIAGNOSTIC ONLY": "appendix context",
    "ACTIVE": "active",
}


TEXT_REPLACEMENTS = (
    ("retained limitations", "comments"),
    ("retained limitation", "comment"),
    ("Retained limitations", "Comments"),
    ("fragile", "stability-sensitive"),
    ("Fragile", "Stability-sensitive"),
    ("weak-IV", "instrument-strength"),
    ("Weak-IV", "Instrument-strength"),
    ("not statistically significant", "estimated with limited precision"),
    ("insignificant", "limited in precision"),
    ("hard-IV", "strict IV"),
    ("hard treatment-bridge", "strict treatment-bridge"),
    ("validation", "measurement review"),
    ("Validation", "Measurement review"),
)


def select_existing(frame: pd.DataFrame, columns: list[str] | tuple[str, ...]) -> pd.DataFrame:
    if frame is None or frame.empty:
        return pd.DataFrame()
    return frame[[col for col in columns if col in frame.columns]].copy()


def soften_value(value: object) -> object:
    if not isinstance(value, str):
        return value
    if value in VALUE_REPLACEMENTS:
        return VALUE_REPLACEMENTS[value]
    out = value
    for old, new in TEXT_REPLACEMENTS:
        out = out.replace(old, new)
    return out


def _compact_value(value: object, max_chars: int = 140) -> object:
    out = soften_value(value)
    if isinstance(out, str) and len(out) > max_chars:
        return out[: max_chars - 3] + "..."
    return out


def format_frame(frame: pd.DataFrame, max_text_chars: int = 140) -> pd.DataFrame:
    out = frame.copy()
    for col in out.select_dtypes(include=["float", "float64", "float32"]).columns:
        out[col] = out[col].round(4)
    object_cols = out.select_dtypes(include=["object"]).columns
    for col in object_cols:
        out[col] = out[col].map(lambda value: _compact_value(value, max_text_chars))
    return out


def sort_if_present(frame: pd.DataFrame, by: str | list[str], ascending: bool = True) -> pd.DataFrame:
    if frame is None or frame.empty:
        return pd.DataFrame()
    columns = [by] if isinstance(by, str) else by
    if all(column in frame.columns for column in columns):
        return frame.sort_values(columns, ascending=ascending)
    return frame
