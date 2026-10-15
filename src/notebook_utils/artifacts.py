"""Load result files without interrupting the notebook."""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from .paths import artifact_path, rel

ARTIFACT_WARNINGS: list[str] = []

EXPECTED_MAJOR_OUTPUTS = [
    "results/final",
    "results/final/figures",
    "results/final/tables/normalized_irf_outputs.csv",
    "results/final/tables/cumulative_transmission_outputs.csv",
    "results/final/tables/peak_response_table.csv",
    "results/final/tables/horizon_significance_table.csv",
    "results/final/diagnostics/monthly_first_stage_tournament.csv",
    "results/final/diagnostics/monthly_first_stage_rolling.csv",
    "results/final/diagnostics/monthly_first_stage_event_sensitivity.csv",
    "results/final/diagnostics/monthly_first_stage_regime.csv",
    "results/final/diagnostics/information_effect_event_screen.csv",
    "results/final/diagnostics/information_effect_summary.csv",
    "results/final/diagnostics/proxy_validation_accepted.csv",
    "results/final/diagnostics/proxy_validation_rejected.csv",
    "results/final/diagnostics/causal_language_audit.csv",
    "results/final/uncertainty/bootstrap_sensitivity_summary.csv",
    "results/final/uncertainty/horizon_dependence_diagnostics.csv",
    "results/final/uncertainty/significance_heatmap.csv",
    "results/final/stability/monthly_stability_metrics.csv",
    "results/final/stability/monthly_rolling_window_lp.csv",
    "results/final/robustness/clean_event_robustness_outputs.csv",
    "results/final/robustness/monthly_ols_policy_rate_comparison.csv",
    "results/final/regime/monthly_regime_reduced_form_lp.csv",
    "results/final/mechanism/transmission_timing_tables.csv",
    "results/final/mechanism/sequential_timing_outputs.csv",
    "results/final/mechanism/banking_proxy_registry.csv",
    "results/final/memos/execution_summary.json",
    "results/final/memos/execution_summary.md",
]


def _record_warning(message: str) -> None:
    ARTIFACT_WARNINGS.append(message)


def warn_missing(path: Path | str) -> None:
    _record_warning(f"Expected research output is unavailable: {rel(path)}")


def warn_load(path: Path | str, exc: Exception) -> None:
    _record_warning(f"Could not read research output: {rel(path)}. Reason: {exc}")


def _attach_artifact(frame: pd.DataFrame, path: Path) -> pd.DataFrame:
    frame.attrs["artifact_path"] = rel(path)
    frame.attrs["artifact_paths"] = [rel(path)]
    return frame


def with_artifacts(frame: pd.DataFrame, artifacts: list[str | Path] | tuple[str | Path, ...]) -> pd.DataFrame:
    frame = frame.copy()
    frame.attrs["artifact_paths"] = [rel(artifact_path(path)) for path in artifacts]
    if len(frame.attrs["artifact_paths"]) == 1:
        frame.attrs["artifact_path"] = frame.attrs["artifact_paths"][0]
    return frame


def safe_read_csv(*parts: str | Path, **kwargs: object) -> pd.DataFrame:
    path = artifact_path(*parts)
    if not path.exists():
        warn_missing(path)
        return _attach_artifact(pd.DataFrame(), path)
    try:
        return _attach_artifact(pd.read_csv(path, **kwargs), path)
    except Exception as exc:
        warn_load(path, exc)
        return _attach_artifact(pd.DataFrame(), path)


def safe_read_json(*parts: str | Path) -> dict:
    path = artifact_path(*parts)
    if not path.exists():
        warn_missing(path)
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        warn_load(path, exc)
        return {}


def safe_read_text(*parts: str | Path, max_chars: int | None = None) -> str:
    path = artifact_path(*parts)
    if not path.exists():
        warn_missing(path)
        return ""
    try:
        text = path.read_text(encoding="utf-8")
        return text if max_chars is None else text[:max_chars]
    except Exception as exc:
        warn_load(path, exc)
        return ""


def validate_major_outputs(print_missing: bool = False) -> pd.DataFrame:
    rows = []
    for rel_name in EXPECTED_MAJOR_OUTPUTS:
        path = artifact_path(rel_name)
        is_dir_expected = rel_name.endswith("/") or path.suffix == ""
        available = path.is_dir() if is_dir_expected else path.exists()
        rows.append(
            {
                "artifact": rel_name,
                "kind": "directory" if is_dir_expected else "file",
                "available": bool(available),
            }
        )
        if print_missing and not available:
            warn_missing(path)
    return pd.DataFrame(rows)
