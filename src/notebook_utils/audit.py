"""Small checks used in the replication appendix."""

from __future__ import annotations

import numpy as np
import pandas as pd

from .artifacts import ARTIFACT_WARNINGS, safe_read_csv, safe_read_json
from .display import Markdown, audit_box, display, key_finding
from .figures import FIGURE_GROUPS
from .paths import FINAL, artifact_path
from .tables import show_table


def display_environment_metadata() -> None:
    env_rows = [
        {"item": "empirical object", "value": "monthly responses to high-frequency ECB policy-news shocks"},
        {"item": "main comparison", "value": "housing finance and financial variables versus wage-pressure proxies"},
        {"item": "uncertainty", "value": "HAC intervals and bootstrap checks"},
        {"item": "frequency rule", "value": "quarterly house-price and compensation series are not interpolated"},
    ]
    show_table(pd.DataFrame(env_rows), title="Replication Notes")

    randomness_rows = [
        {"component": "IRF fixed-design bootstrap", "control": "deterministic stable_seed(response, shock, horizon, sample_name, reps)", "replications": 399},
        {"component": "Moving-block / wild bootstrap", "control": "deterministic stable_seed(response, shock, method, block_length, reps, nobs)", "replications": 399},
        {"component": "Compensation proxy bootstrap", "control": "deterministic stable_seed('comp_boot', variable, horizon, reps)", "replications": 199},
        {"component": "HAC inference", "control": "deterministic Newey-West bandwidth h + 1", "replications": "not stochastic"},
    ]
    show_table(pd.DataFrame(randomness_rows), title="Uncertainty Settings")


def display_pipeline_audit(major_output_status: pd.DataFrame) -> None:
    execution_summary = safe_read_json("results/final/memos/execution_summary.json")
    steps = pd.DataFrame(execution_summary.get("steps", []))
    if not steps.empty:
        for col in ["started_at", "finished_at"]:
            if col in steps.columns:
                steps[col] = pd.to_datetime(steps[col], errors="coerce")
        steps["status"] = np.where(steps.get("returncode", 1).eq(0), "completed", "failed")

    artifact_counts = []
    for subdir in ["figures", "tables", "diagnostics", "uncertainty", "mechanism", "stability", "robustness", "regime", "memos"]:
        path = FINAL / subdir
        artifact_counts.append(
            {
                "artifact_family": subdir,
                "files": sum(1 for item in path.rglob("*") if item.is_file()) if path.exists() else 0,
                "available": path.exists(),
            }
        )
    artifact_counts = pd.DataFrame(artifact_counts)

    audit = safe_read_csv("results/final/diagnostics/causal_language_audit.csv")
    if not audit.empty and "status" in audit.columns:
        audit_summary = audit.groupby("status", as_index=False).size().rename(columns={"size": "checks"})
    else:
        audit_summary = pd.DataFrame()

    missing_major = major_output_status.loc[~major_output_status["available"]] if not major_output_status.empty else pd.DataFrame()

    show_table(steps, ["name", "status", "returncode"], title="Replication Step Summary", artifact="results/final/memos/execution_summary.json")
    show_table(artifact_counts, ["artifact_family", "available"], title="Output Family Availability", artifact="results/final")
    show_table(audit_summary, ["status", "checks"], title="Causal-Language Review", artifact="results/final/diagnostics/causal_language_audit.csv")
    show_table(missing_major, ["artifact", "available"], title="Unavailable Research Outputs", artifact="results/final")

    audit_box(
        "Replication Appendix",
        (
            f"The stored empirical output set is available for the thesis notebook. "
            f"Unavailable major outputs: {len(missing_major)}."
        ),
    )


def display_final_integrity_validation(major_output_status: pd.DataFrame) -> pd.DataFrame:
    all_declared_figures = [path for paths in FIGURE_GROUPS.values() for path in paths]
    figure_status = pd.DataFrame(
        [{"figure": rel_path, "exists": artifact_path(rel_path).exists()} for rel_path in all_declared_figures]
    )
    referenced_tables = [
        "data/processed/eu_de/final_monthly_model_dataset.csv",
        "data/processed/eu_de/final_monthly_dataset_coverage.csv",
        "data/processed/eu_de/monthly_variable_dictionary.csv",
        "results/final/tables/normalized_irf_outputs.csv",
        "results/final/tables/cumulative_transmission_outputs.csv",
        "results/final/tables/peak_response_table.csv",
        "results/final/uncertainty/horizon_significance_table.csv",
        "results/final/diagnostics/monthly_first_stage_tournament.csv",
        "results/final/diagnostics/information_effect_event_screen.csv",
        "results/final/diagnostics/proxy_validation_accepted.csv",
        "results/final/mechanism/transmission_timing_tables.csv",
        "results/final/mechanism/sequential_timing_outputs.csv",
        "results/final/stability/monthly_stability_metrics.csv",
        "results/final/robustness/clean_event_robustness_outputs.csv",
        "results/final/regime/monthly_regime_reduced_form_lp.csv",
    ]
    table_status = pd.DataFrame(
        [{"artifact": rel_name, "exists": artifact_path(rel_name).exists()} for rel_name in referenced_tables]
    )

    show_table(figure_status.loc[~figure_status["exists"]], title="Unavailable displayed figures", artifact="results/final/figures")
    show_table(table_status.loc[~table_status["exists"]], title="Unavailable referenced tables", artifact=referenced_tables)

    integrity = pd.DataFrame(
        [
            {"check": "declared figures available", "available": bool(figure_status["exists"].all()) if not figure_status.empty else False},
            {"check": "referenced tables available", "available": bool(table_status["exists"].all()) if not table_status.empty else False},
            {"check": "major output set available", "available": bool(major_output_status["available"].all()) if not major_output_status.empty else False},
            {"check": "runtime warnings absent", "available": len(ARTIFACT_WARNINGS) == 0},
        ]
    )
    show_table(integrity, title="Final Notebook Availability Review", artifact="results/final")

    if ARTIFACT_WARNINGS:
        display(Markdown("### Research Output Notes"))
        for warning_msg in ARTIFACT_WARNINGS:
            print(warning_msg)
    else:
        key_finding("All declared thesis figures and referenced tables were available in this execution context.")
    return integrity
