#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
import re
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
FINAL_ROOT = ROOT / "results" / "final"
CANONICAL_NOTEBOOK = ROOT / "1. thesis_master_notebook.ipynb"

REQUIRED_DIRS = (
    FINAL_ROOT / "figures",
    FINAL_ROOT / "tables",
    FINAL_ROOT / "diagnostics",
    FINAL_ROOT / "robustness",
    FINAL_ROOT / "regime",
    FINAL_ROOT / "stability",
    FINAL_ROOT / "uncertainty",
    FINAL_ROOT / "mechanism",
    FINAL_ROOT / "proxy_validation",
    FINAL_ROOT / "proxy_validation" / "compensation",
    FINAL_ROOT / "memos",
    FINAL_ROOT / "figures" / "baseline",
    FINAL_ROOT / "figures" / "cumulative",
    FINAL_ROOT / "figures" / "uncertainty",
    FINAL_ROOT / "figures" / "regimes",
    FINAL_ROOT / "figures" / "stability",
    FINAL_ROOT / "figures" / "mechanism",
    FINAL_ROOT / "figures" / "compensation",
    FINAL_ROOT / "figures" / "banking",
)

ALLOWED_DOCS = {
    "project_map.md",
    "final_methodology.md",
    "final_claims_boundary.md",
    "final_causality_framework.md",
    "final_empirical_findings.md",
    "final_identification_statement.md",
    "final_delivery_report.md",
    "model_governance.md",
    "thesis_master_outline.md",
    "final_figure_registry.md",
    "final_table_registry.md",
    "source_to_claim_mapping.md",
    "data_source_verification.md",
    "results_hierarchy.md",
}

ALLOWED_SCRIPTS = {
    "run_full_pipeline.py",
    "final_empirical_audit.py",
    "run_first_stage_tournament.py",
    "run_information_effect_screening.py",
    "run_proxy_validation.py",
    "run_monthly_reduced_form_lp.py",
    # Diagnostic layer. Re-fits the baseline local projections and tests their
    # residuals. It changes no coefficient and writes only to results/final/uncertainty/.
    "run_residual_diagnostics.py",
    # Presentation layer. Re-renders figures from the canonical artifacts in the
    # shared visual style. It estimates nothing and writes no CSV.
    "rebuild_figures.py",
    # Do-file. Reproduces the thesis tables in thesis order and numbering from the
    # canonical artifacts. It estimates nothing and writes only to results/final/thesis_tables/.
    "reproduce_thesis_tables.py",
}

REQUIRED_FILES = (
    CANONICAL_NOTEBOOK,
    ROOT / "data" / "processed" / "eu_de" / "final_monthly_model_dataset.csv",
    FINAL_ROOT / "tables" / "monthly_reduced_form_lp_coefficients.csv",
    FINAL_ROOT / "tables" / "monthly_reduced_form_lp_cumulative.csv",
    FINAL_ROOT / "tables" / "normalized_irf_outputs.csv",
    FINAL_ROOT / "tables" / "cumulative_transmission_outputs.csv",
    FINAL_ROOT / "diagnostics" / "monthly_first_stage_tournament.csv",
    FINAL_ROOT / "diagnostics" / "monthly_first_stage_rolling.csv",
    FINAL_ROOT / "diagnostics" / "monthly_first_stage_regime.csv",
    FINAL_ROOT / "diagnostics" / "information_effect_event_screen.csv",
    FINAL_ROOT / "diagnostics" / "clean_event_sample.csv",
    FINAL_ROOT / "diagnostics" / "contaminated_event_sample.csv",
    FINAL_ROOT / "diagnostics" / "information_effect_summary.csv",
    FINAL_ROOT / "diagnostics" / "monthly_response_exclusions.csv",
    FINAL_ROOT / "diagnostics" / "proxy_validation_tournament.csv",
    FINAL_ROOT / "diagnostics" / "proxy_validation_accepted.csv",
    FINAL_ROOT / "diagnostics" / "proxy_validation_rejected.csv",
    FINAL_ROOT / "diagnostics" / "causal_language_audit.csv",
    FINAL_ROOT / "regime" / "monthly_regime_reduced_form_lp.csv",
    FINAL_ROOT / "regime" / "monthly_regime_cumulative_transmission.csv",
    FINAL_ROOT / "stability" / "monthly_directional_stability_matrix.csv",
    FINAL_ROOT / "stability" / "monthly_persistence_ranking_stability.csv",
    FINAL_ROOT / "stability" / "monthly_rolling_window_lp.csv",
    FINAL_ROOT / "stability" / "monthly_recursive_window_lp.csv",
    FINAL_ROOT / "stability" / "monthly_stability_metrics.csv",
    FINAL_ROOT / "robustness" / "monthly_ols_policy_rate_comparison.csv",
    FINAL_ROOT / "robustness" / "clean_event_robustness_outputs.csv",
    FINAL_ROOT / "uncertainty" / "confidence_band_irfs.csv",
    FINAL_ROOT / "uncertainty" / "cumulative_uncertainty_irfs.csv",
    FINAL_ROOT / "uncertainty" / "horizon_significance_table.csv",
    FINAL_ROOT / "uncertainty" / "significance_heatmap.csv",
    FINAL_ROOT / "uncertainty" / "persistence_confidence_matrix.csv",
    FINAL_ROOT / "mechanism" / "sequential_transmission_outputs.csv",
    FINAL_ROOT / "mechanism" / "sequential_timing_outputs.csv",
    FINAL_ROOT / "mechanism" / "banking_transmission_summary.md",
    FINAL_ROOT / "mechanism" / "lending_conditions_responses.csv",
    FINAL_ROOT / "mechanism" / "spread_responses.csv",
    FINAL_ROOT / "mechanism" / "transmission_timing_tables.csv",
    FINAL_ROOT / "mechanism" / "banking_proxy_registry.csv",
    FINAL_ROOT / "proxy_validation" / "compensation" / "accepted_compensation_proxies.csv",
    FINAL_ROOT / "proxy_validation" / "compensation" / "rejected_compensation_proxies.csv",
    FINAL_ROOT / "proxy_validation" / "compensation" / "compensation_scorecard.csv",
    FINAL_ROOT / "proxy_validation" / "compensation" / "compensation_stability_metrics.csv",
    FINAL_ROOT / "proxy_validation" / "compensation" / "compensation_proxy_rankings.csv",
    FINAL_ROOT / "proxy_validation" / "compensation" / "compensation_proxy_summary.md",
    FINAL_ROOT / "memos" / "execution_summary.md",
    ROOT / "docs" / "data_source_verification.md",
)

REQUIRED_MONTHLY_RESPONSES = (
    "ln_ecb_assets_ea_stock",
    "ln_dax_real_de",
    "ln_hh_loans_ea_stock",
    "ln_nfc_loans_ea_stock",
    "ln_retail_de_chained_index",
    "ecb_house_purchase_growth_yoy",
    "ln_ecb_house_purchase_pure_new_loans",
    "ecb_wage_tracker_ex_oneoffs_real_yoy",
)

ACTIVE_OUTPUT_DIRS = (
    ROOT / "results" / "lpiv",
    ROOT / "results" / "diagnostics",
    ROOT / "results" / "identification_rebuild",
    ROOT / "results" / ".matplotlib",
    ROOT / "results" / "stress_testing",
    ROOT / "results" / "cointegration",
    ROOT / "results" / "stationarity",
    ROOT / "results" / "svecm",
    ROOT / "results" / "irf",
    ROOT / "results" / "robustness",
    ROOT / "results" / "data_quality",
)

DEPRECATED_ACTIVE_DIRS = (
    ROOT / "src" / "svecm",
    ROOT / "src" / "cointegration",
    ROOT / "src" / "irf",
    ROOT / "src" / "transformations",
    ROOT / "src" / "plotting",
    ROOT / "src" / "diagnostics",
    ROOT / "notebooks",
)

FORBIDDEN_LANGUAGE_PATTERNS = {
    "forbidden QE inequality claim": re.compile(r"\bQE caused inequality\b", re.IGNORECASE),
    "forbidden ECB housing claim": re.compile(r"\bECB created (the )?housing crisis\b", re.IGNORECASE),
    "forbidden redistribution claim": re.compile(r"\bpolicy redistributed wealth\b", re.IGNORECASE),
    "forbidden bank mediation claim": re.compile(r"\bbank mediation proven\b", re.IGNORECASE),
    "forbidden affordability claim": re.compile(r"\bECB caused affordability collapse\b", re.IGNORECASE),
    "forbidden mechanical bank redistribution claim": re.compile(
        r"\bbanks transmitted redistribution mechanically\b", re.IGNORECASE
    ),
    "inequality causality claim": re.compile(r"\b(causes|caused|causing)\s+inequality\b", re.IGNORECASE),
    "welfare identification claim": re.compile(r"\bwelfare effects?\s+(are\s+)?identified\b", re.IGNORECASE),
    "proof language": re.compile(r"\b(proves|proven)\b", re.IGNORECASE),
    "strong causal effect language": re.compile(r"\bstrong causal effect\b", re.IGNORECASE),
}

PREFERRED_LANGUAGE_TERMS = (
    "persistent transmission",
    "persistent reduced-form transmission",
    "financial-channel dominance",
    "timing-consistent propagation",
    "reduced-form response",
    "differential transmission persistence",
    "housing-finance-related responses",
    "suggestive distributional implications",
    "dynamic transmission asymmetry",
)


@dataclass
class Finding:
    level: str
    check: str
    message: str


def rel(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


def has_files(path: Path) -> bool:
    return path.exists() and any(child.is_file() for child in path.rglob("*"))


def read_csv_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def check_required_paths(findings: list[Finding]) -> None:
    for directory in REQUIRED_DIRS:
        if not directory.is_dir():
            findings.append(Finding("error", "required directory", f"Missing {rel(directory)}"))
    for path in REQUIRED_FILES:
        if not path.exists():
            findings.append(Finding("error", "required file", f"Missing {rel(path)}"))


def check_no_parallel_output_universes(findings: list[Finding]) -> None:
    for directory in ACTIVE_OUTPUT_DIRS:
        if directory.exists():
            findings.append(
                Finding(
                    "error",
                    "parallel outputs",
                    f"Old output tree still exists: {rel(directory)}",
                )
            )


def check_deprecated_architecture(findings: list[Finding]) -> None:
    for directory in DEPRECATED_ACTIVE_DIRS:
        if has_files(directory):
            findings.append(
                Finding("error", "deprecated design", f"Old active design files remain: {rel(directory)}")
            )



def check_active_surface(findings: list[Finding]) -> None:
    docs_dir = ROOT / "docs"
    if docs_dir.exists():
        for path in docs_dir.iterdir():
            if path.is_dir():
                findings.append(Finding("error", "docs surface", f"Unexpected docs subdirectory remains active: {rel(path)}"))
            elif path.name not in ALLOWED_DOCS:
                findings.append(Finding("error", "docs surface", f"Unexpected docs file remains active: {rel(path)}"))

    scripts_dir = ROOT / "scripts"
    if scripts_dir.exists():
        for path in scripts_dir.iterdir():
            if path.is_file() and path.name not in ALLOWED_SCRIPTS:
                findings.append(Finding("error", "scripts surface", f"Unexpected script remains active: {rel(path)}"))

    proxy_validation_dir = ROOT / "proxy_validation"
    if has_files(proxy_validation_dir):
        findings.append(
            Finding(
                "error",
                "proxy validation surface",
                f"Root proxy-validation mirror remains active: {rel(proxy_validation_dir)}",
            )
        )


def check_identification_rebuild_visibility(findings: list[Finding]) -> None:
    tournament = FINAL_ROOT / "diagnostics" / "monthly_first_stage_tournament.csv"
    lp = FINAL_ROOT / "tables" / "monthly_reduced_form_lp_coefficients.csv"
    info = FINAL_ROOT / "diagnostics" / "information_effect_event_screen.csv"
    exclusions = FINAL_ROOT / "diagnostics" / "monthly_response_exclusions.csv"
    proxy_validation = FINAL_ROOT / "diagnostics" / "proxy_validation_tournament.csv"
    clean_events = FINAL_ROOT / "diagnostics" / "clean_event_sample.csv"
    contaminated_events = FINAL_ROOT / "diagnostics" / "contaminated_event_sample.csv"
    if not tournament.exists() or not lp.exists() or not info.exists():
        return

    tournament_rows = read_csv_rows(tournament)
    required_tournament = {"target", "instrument", "first_stage_f_stat", "partial_r_squared", "final_screen"}
    missing_tournament = required_tournament.difference(tournament_rows[0].keys()) if tournament_rows else required_tournament
    if missing_tournament:
        findings.append(Finding("error", "first-stage tournament", f"Tournament missing columns: {sorted(missing_tournament)}"))
    if not any(row.get("final_screen") in {"fragile_candidate", "reject_weak_relevance", "candidate"} for row in tournament_rows):
        findings.append(Finding("error", "first-stage tournament", "Tournament does not expose candidate classification."))

    lp_rows = read_csv_rows(lp)
    expected_min_cells = len(REQUIRED_MONTHLY_RESPONSES) * 5
    if len(lp_rows) < expected_min_cells:
        findings.append(Finding("error", "monthly LP shape", f"Monthly LP has {len(lp_rows)} rows, expected at least {expected_min_cells}"))
    responses = {row.get("response", "") for row in lp_rows}
    missing_responses = set(REQUIRED_MONTHLY_RESPONSES).difference(responses)
    if missing_responses:
        findings.append(Finding("error", "monthly LP responses", f"Missing responses: {sorted(missing_responses)}"))

    info_rows = read_csv_rows(info)
    required_info = {"rate_factor_sign", "yield_response_sign", "equity_response_sign", "information_effect_screen"}
    missing_info = required_info.difference(info_rows[0].keys()) if info_rows else required_info
    if missing_info:
        findings.append(Finding("error", "information-effect screen", f"Screen missing columns: {sorted(missing_info)}"))

    if exclusions.exists():
        excluded = {row.get("response", "") for row in read_csv_rows(exclusions)}
        for response in {"ln_house_price_de_real_q_observed", "ln_compensation_ea20_real_q_observed"}:
            if response not in excluded:
                findings.append(Finding("error", "monthly response exclusions", f"{response} exclusion is not documented"))

    if proxy_validation.exists():
        proxy_rows = read_csv_rows(proxy_validation)
        required_proxy = {"variable", "decision", "monthly_continuity", "quarterly_target_correlation", "information_effect_flag"}
        missing_proxy = required_proxy.difference(proxy_rows[0].keys()) if proxy_rows else required_proxy
        if missing_proxy:
            findings.append(Finding("error", "proxy validation", f"Proxy tournament missing columns: {sorted(missing_proxy)}"))
        accepted = {row.get("variable", "") for row in proxy_rows if row.get("decision", "").startswith("accepted")}
        for variable in {"ecb_house_purchase_growth_yoy", "ecb_wage_tracker_ex_oneoffs_real_yoy"}:
            if variable not in accepted:
                findings.append(Finding("error", "proxy validation", f"Canonical proxy not accepted: {variable}"))

    for path in (clean_events, contaminated_events):
        if path.exists():
            rows = read_csv_rows(path)
            required_event = {"rate_factor_sign", "ois_movement", "equity_window_response", "contamination_classification"}
            missing_event = required_event.difference(rows[0].keys()) if rows else required_event
            if missing_event:
                findings.append(Finding("error", "event samples", f"{rel(path)} missing columns: {sorted(missing_event)}"))


def check_notebook_surface(findings: list[Finding]) -> None:
    notebook = CANONICAL_NOTEBOOK
    if not notebook.exists():
        return
    text = notebook.read_text(encoding="utf-8")
    if "ECB Monetary-Surprise Transmission: Empirical Thesis Companion" not in text:
        findings.append(Finding("error", "notebook sections", "Notebook missing thesis title."))

    section_requirements = {
        "research motivation": ("Research Motivation", "Executive Research Overview"),
        "data and variable construction": ("Data And Variable Construction", "Data And Provenance"),
        "identification strategy": ("Identification Strategy", "Identification Evidence"),
        "baseline results": ("Baseline Results", "Main Empirical Results"),
        "comparative transmission analysis": ("Comparative Transmission Analysis", "Transmission Mechanism"),
        "robustness": ("Robustness", "Robustness, Stability, And Regime Analysis"),
        "interpretation": ("Interpretation", "Hypothesis Evaluation"),
        "conclusion": ("Final Thesis-Level Conclusion",),
        "replication appendix": (
            "Appendix: Replication Notes",
            "Appendix A: Specification Registry And Legacy Boundary",
            "Reproducibility",
        ),
    }
    missing_roles = [
        role for role, accepted_headings in section_requirements.items() if not any(heading in text for heading in accepted_headings)
    ]
    if missing_roles:
        findings.append(Finding("error", "notebook sections", f"Notebook missing thesis section roles: {missing_roles}"))
    if '"output_type": "error"' in text:
        findings.append(Finding("error", "notebook execution", "Notebook contains an error output."))


def check_final_table_contracts(findings: list[Finding]) -> None:
    contracts = {
        FINAL_ROOT / "tables" / "monthly_reduced_form_lp_coefficients.csv": {
            "response",
            "shock",
            "horizon_months",
            "coefficient",
            "raw_coefficient_per_unit_shock",
            "shock_normalization",
            "std_error_hac",
            "ci_90_low",
            "ci_90_high",
            "ci_95_low",
            "ci_95_high",
            "bootstrap_method",
            "p_value",
            "interpretation_layer",
        },
        FINAL_ROOT / "tables" / "monthly_reduced_form_lp_cumulative.csv": {
            "response",
            "shock",
            "horizon_months",
            "cumulative_response",
            "ci_90_low",
            "ci_90_high",
            "ci_method",
        },
        FINAL_ROOT / "stability" / "monthly_directional_stability_matrix.csv": {
            "response",
            "horizon_months",
            "full",
            "exclude_covid",
            "clean_events_only",
        },
        FINAL_ROOT / "regime" / "monthly_regime_reduced_form_lp.csv": {
            "response",
            "sample_name",
            "horizon_months",
            "coefficient",
            "shock_normalization",
            "interpretation_layer",
        },
        FINAL_ROOT / "diagnostics" / "monthly_first_stage_tournament.csv": {
            "target",
            "instrument",
            "first_stage_f_stat",
            "partial_r_squared",
            "final_screen",
        },
        FINAL_ROOT / "uncertainty" / "horizon_significance_table.csv": {
            "response",
            "horizon_months",
            "ci_90_low",
            "ci_90_high",
            "significance_bucket",
        },
        FINAL_ROOT / "mechanism" / "sequential_transmission_outputs.csv": {
            "pathway",
            "upstream",
            "downstream",
            "governance_note",
            "timing_classification",
        },
        FINAL_ROOT / "mechanism" / "banking_proxy_registry.csv": {
            "variable",
            "label",
            "proxy_type",
            "frequency_integrity",
            "observations",
            "governance_note",
        },
        FINAL_ROOT / "proxy_validation" / "compensation" / "compensation_scorecard.csv": {
            "variable",
            "decision",
            "canonical_status",
            "frequency_validity_score",
            "sample_coverage_score",
            "stationarity_behavior_score",
            "transmission_persistence_score",
            "sign_consistency_score",
            "regime_stability_score",
            "bootstrap_robustness_score",
            "economic_interpretability_score",
            "clean_event_sensitivity_score",
            "volatility_noise_ratio_score",
            "total_score",
            "rank",
        },
    }
    for path, required_columns in contracts.items():
        if not path.exists():
            continue
        rows = read_csv_rows(path)
        if not rows:
            findings.append(Finding("error", "table contract", f"{rel(path)} is empty"))
            continue
        missing = required_columns.difference(rows[0].keys())
        if missing:
            findings.append(Finding("error", "table contract", f"{rel(path)} missing columns: {sorted(missing)}"))
        seen = set()
        duplicates = 0
        for row in rows:
            key = tuple(row.items())
            if key in seen:
                duplicates += 1
            seen.add(key)
        if duplicates:
            findings.append(Finding("error", "table contract", f"{rel(path)} has duplicate rows: {duplicates}"))


def check_final_figure_contract(findings: list[Finding]) -> None:
    figure_dir = FINAL_ROOT / "figures"
    if not figure_dir.exists():
        return
    required_subdirs = ("baseline", "cumulative", "uncertainty", "regimes", "stability", "mechanism", "compensation", "banking")
    for name in required_subdirs:
        subdir = figure_dir / name
        if not subdir.is_dir():
            findings.append(Finding("error", "figure hierarchy", f"Missing final figure subdirectory: {rel(subdir)}"))
        elif not any(subdir.glob("*.png")):
            findings.append(Finding("warning", "figure hierarchy", f"No PNG figures found in {rel(subdir)}"))
    svgs = list(figure_dir.rglob("*.svg"))
    if svgs:
        findings.append(
            Finding(
                "error",
                "figure hierarchy",
                f"SVG figures remain under final outputs; use PNG figures for thesis output: {[rel(path) for path in svgs[:8]]}",
            )
        )


def check_stale_outputs(findings: list[Finding]) -> None:
    summary = FINAL_ROOT / "memos" / "execution_summary.json"
    if not summary.exists():
        return
    try:
        payload = json.loads(summary.read_text(encoding="utf-8"))
        run_finished = datetime.fromisoformat(payload["finished_at"])
    except (KeyError, json.JSONDecodeError, ValueError) as exc:
        findings.append(Finding("error", "execution summary", f"Execution summary JSON is not parseable: {exc}"))
        return

    stale: list[str] = []
    for path in REQUIRED_FILES:
        if path in {
            FINAL_ROOT / "diagnostics" / "causal_language_audit.csv",
            FINAL_ROOT / "memos" / "execution_summary.md",
        }:
            continue
        try:
            path.relative_to(FINAL_ROOT)
        except ValueError:
            continue
        if path.exists() and path.is_file() and path.stat().st_mtime > run_finished.timestamp() + 60:
            stale.append(rel(path))
    if stale:
        findings.append(Finding("warning", "stale output", f"Files appear newer than execution summary: {stale}"))


def language_scan_files() -> list[Path]:
    scan_roots = [
        ROOT / "README.md",
        ROOT / "docs",
        FINAL_ROOT / "memos",
        CANONICAL_NOTEBOOK,
    ]
    files: list[Path] = []
    for item in scan_roots:
        if item.is_file():
            files.append(item)
        elif item.is_dir():
            files.extend(path for path in item.rglob("*") if path.is_file() and path.suffix in {".md", ".ipynb"})
    return sorted(files)


def check_forbidden_language(findings: list[Finding]) -> None:
    files = language_scan_files()

    for path in files:
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        for label, pattern in FORBIDDEN_LANGUAGE_PATTERNS.items():
            match = pattern.search(text)
            if match:
                findings.append(
                    Finding("error", "forbidden language", f"{label} in {rel(path)}: `{match.group(0)}`")
                )


def write_causal_language_audit() -> None:
    FINAL_ROOT.joinpath("diagnostics").mkdir(parents=True, exist_ok=True)
    rows: list[dict[str, str]] = []
    for path in language_scan_files():
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        for label, pattern in FORBIDDEN_LANGUAGE_PATTERNS.items():
            matches = list(pattern.finditer(text))
            rows.append(
                {
                    "file": rel(path),
                    "check_type": "forbidden_phrase",
                    "language_rule": label,
                    "match_count": str(len(matches)),
                    "status": "fail" if matches else "pass",
                    "example": matches[0].group(0) if matches else "",
                }
            )
        for term in PREFERRED_LANGUAGE_TERMS:
            rows.append(
                {
                    "file": rel(path),
                    "check_type": "preferred_phrase_presence",
                    "language_rule": term,
                    "match_count": str(text.lower().count(term.lower())),
                    "status": "observed" if term.lower() in text.lower() else "not_observed",
                    "example": term if term.lower() in text.lower() else "",
                }
            )
    if not rows:
        rows.append(
            {
                "file": "",
                "check_type": "audit_scope",
                "language_rule": "no readable files",
                "match_count": "0",
                "status": "warning",
                "example": "",
            }
        )
    path = FINAL_ROOT / "diagnostics" / "causal_language_audit.csv"
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=["file", "check_type", "language_rule", "match_count", "status", "example"],
        )
        writer.writeheader()
        writer.writerows(rows)


def run_audit() -> list[Finding]:
    findings: list[Finding] = []
    check_required_paths(findings)
    check_active_surface(findings)
    check_no_parallel_output_universes(findings)
    check_deprecated_architecture(findings)
    check_identification_rebuild_visibility(findings)
    check_notebook_surface(findings)
    check_final_table_contracts(findings)
    check_final_figure_contract(findings)
    check_stale_outputs(findings)
    check_forbidden_language(findings)
    return findings


def main() -> int:
    parser = argparse.ArgumentParser(description="Check the final thesis empirical outputs.")
    parser.add_argument("--json", action="store_true", help="Print machine-readable findings.")
    args = parser.parse_args()

    write_causal_language_audit()
    findings = run_audit()
    error_count = sum(1 for finding in findings if finding.level == "error")

    if args.json:
        print(json.dumps([finding.__dict__ for finding in findings], indent=2))
    else:
        if findings:
            print("Final empirical check findings:")
            for finding in findings:
                print(f"- [{finding.level.upper()}] {finding.check}: {finding.message}")
        else:
            print("Final empirical check passed: notebook, outputs, docs, and instrument-strength context are in place.")

    return 1 if error_count else 0


if __name__ == "__main__":
    sys.exit(main())
