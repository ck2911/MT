"""Notebook imports collected in one place."""

from __future__ import annotations

import sys

from .artifacts import ARTIFACT_WARNINGS, validate_major_outputs
from .display import audit_box, caution_box, configure_notebook, key_finding
from .figures import FIGURE_GROUPS, display_figure, display_figure_group
from .paths import DATA, DOCS, FINAL, NOTEBOOK, PIPELINE_SCRIPT, RAW, ROOT
from .rebuild import run_full_rebuild_if_requested
from .sections import (
    display_audit_dashboard,
    display_baseline_irf_figures,
    display_cross_variable_comparison,
    display_cumulative_irf_figures,
    display_data_coverage,
    display_final_validation,
    display_first_stage_dashboard,
    display_hypothesis_evaluation,
    display_information_effects,
    display_instrument_validity,
    display_intermediation_dashboard,
    display_irf_and_persistence_summaries,
    display_regime_analysis,
    display_rebuild_and_validation,
    display_reproducibility_header,
    display_robustness_dashboard,
    display_sequential_transmission_mapping,
    display_source_manifest,
    display_specification_registry,
    display_stability_dashboard,
    display_uncertainty_matrix_and_figures,
    display_variable_dictionary,
)
from .tables import show_table


def show_runtime_header() -> None:
    print(f"Resolved project root: {ROOT}")
    print(f"Notebook path: {NOTEBOOK}")
    print(f"Python executable: {sys.executable}")


__all__ = [
    "ARTIFACT_WARNINGS",
    "DATA",
    "DOCS",
    "FIGURE_GROUPS",
    "FINAL",
    "NOTEBOOK",
    "PIPELINE_SCRIPT",
    "RAW",
    "ROOT",
    "audit_box",
    "caution_box",
    "configure_notebook",
    "display_audit_dashboard",
    "display_baseline_irf_figures",
    "display_cross_variable_comparison",
    "display_cumulative_irf_figures",
    "display_data_coverage",
    "display_figure",
    "display_figure_group",
    "display_final_validation",
    "display_first_stage_dashboard",
    "display_hypothesis_evaluation",
    "display_information_effects",
    "display_instrument_validity",
    "display_intermediation_dashboard",
    "display_irf_and_persistence_summaries",
    "display_regime_analysis",
    "display_rebuild_and_validation",
    "display_reproducibility_header",
    "display_robustness_dashboard",
    "display_sequential_transmission_mapping",
    "display_source_manifest",
    "display_specification_registry",
    "display_stability_dashboard",
    "display_uncertainty_matrix_and_figures",
    "display_variable_dictionary",
    "key_finding",
    "run_full_rebuild_if_requested",
    "show_runtime_header",
    "show_table",
    "validate_major_outputs",
]
