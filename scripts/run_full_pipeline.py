#!/usr/bin/env python3
"""Rebuild every empirical output of the thesis from the data in data/raw/.

Run from the repository root:

    python3 scripts/run_full_pipeline.py

The steps run in the fixed order listed in main(). Canonical outputs are
written to results/final/ and overwritten in place on every run. The working
folders results/identification_rebuild/ and results/diagnostics/ are
intermediate: the copies that matter are placed in results/final/ during the
run, and the working folders are removed at the end. A run therefore leaves
exactly one set of outputs behind.
"""
from __future__ import annotations

import argparse
import csv
import json
import os
import shutil
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "results"
FINAL_ROOT = RESULTS / "final"
CANONICAL_NOTEBOOK = ROOT / "1. thesis_master_notebook.ipynb"
CANONICAL_NOTEBOOK_REL = CANONICAL_NOTEBOOK.relative_to(ROOT).as_posix()

FINAL_DIRS = {
    "figures": FINAL_ROOT / "figures",
    "tables": FINAL_ROOT / "tables",
    "diagnostics": FINAL_ROOT / "diagnostics",
    "robustness": FINAL_ROOT / "robustness",
    "regime": FINAL_ROOT / "regime",
    "stability": FINAL_ROOT / "stability",
    "uncertainty": FINAL_ROOT / "uncertainty",
    "mechanism": FINAL_ROOT / "mechanism",
    "proxy_validation": FINAL_ROOT / "proxy_validation",
    "proxy_validation_compensation": FINAL_ROOT / "proxy_validation" / "compensation",
    "memos": FINAL_ROOT / "memos",
    "figures_baseline": FINAL_ROOT / "figures" / "baseline",
    "figures_cumulative": FINAL_ROOT / "figures" / "cumulative",
    "figures_uncertainty": FINAL_ROOT / "figures" / "uncertainty",
    "figures_regimes": FINAL_ROOT / "figures" / "regimes",
    "figures_stability": FINAL_ROOT / "figures" / "stability",
    "figures_mechanism": FINAL_ROOT / "figures" / "mechanism",
    "figures_compensation": FINAL_ROOT / "figures" / "compensation",
    "figures_banking": FINAL_ROOT / "figures" / "banking",
}

# Working folders written by the estimation scripts. Nothing reads them after
# the run, and the audit rejects them if they remain, so they are removed.
INTERMEDIATE_OUTPUT_DIRS = (
    RESULTS / "identification_rebuild",
    RESULTS / "diagnostics",
)

# Instrument diagnostics written by src/data/ecb_monetary_surprises.py. The
# figure step and the notebook read them from results/final/diagnostics/.
ECB_DIAGNOSTICS = RESULTS / "diagnostics" / "ecb_monetary_surprises"
INSTRUMENT_DIAGNOSTICS = (
    (ECB_DIAGNOSTICS / "first_stage_relevance.csv", "first_stage_relevance.csv"),
    (ECB_DIAGNOSTICS / "event_coverage_by_regime.csv", "event_coverage_by_regime.csv"),
    (ECB_DIAGNOSTICS / "event_coverage_by_year_quarter_regime.csv", "event_coverage_by_year_quarter_regime.csv"),
    (ECB_DIAGNOSTICS / "surprise_distribution_diagnostics.csv", "surprise_distribution_diagnostics.csv"),
    (ECB_DIAGNOSTICS / "quarter_density_diagnostics.csv", "quarter_density_diagnostics.csv"),
    (ECB_DIAGNOSTICS / "instrument_strength_matrix.csv", "instrument_strength_matrix.csv"),
    (RESULTS / "diagnostics" / "regime_specific_identification.csv", "regime_specific_identification.csv"),
)


@dataclass
class StepResult:
    name: str
    returncode: int
    started_at: str
    finished_at: str
    command: list[str]


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def ensure_final_dirs() -> None:
    for directory in FINAL_DIRS.values():
        directory.mkdir(parents=True, exist_ok=True)


def run_step(name: str, command: list[str], env: dict[str, str]) -> StepResult:
    started = utc_now()
    print(f"\n[{started.isoformat()}] {name}")
    print(" ".join(command))
    completed = subprocess.run(command, cwd=ROOT, env=env, check=False)
    finished = utc_now()
    if completed.returncode != 0:
        raise RuntimeError(f"{name} failed with exit code {completed.returncode}")
    return StepResult(
        name=name,
        returncode=completed.returncode,
        started_at=started.isoformat(),
        finished_at=finished.isoformat(),
        # Log the interpreter by name only, so the summary carries no local path.
        command=["python3" if part == sys.executable else part for part in command],
    )


def copy_instrument_diagnostics() -> None:
    """Copy the instrument diagnostics into results/final/diagnostics/.

    This runs straight after the shock builder because the figure step reads
    quarter_density_diagnostics.csv from results/final/. With --skip-instrument
    the working folder does not exist and the copies already in results/final/
    are kept.
    """
    for source, name in INSTRUMENT_DIAGNOSTICS:
        if source.exists():
            shutil.copy2(source, FINAL_DIRS["diagnostics"] / name)


def remove_intermediate_outputs() -> None:
    for directory in INTERMEDIATE_OUTPUT_DIRS:
        if directory.exists():
            shutil.rmtree(directory)


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def write_execution_memos(step_results: list[StepResult]) -> None:
    monthly_tournament = read_csv(FINAL_DIRS["diagnostics"] / "monthly_first_stage_tournament.csv")
    monthly_lp = read_csv(FINAL_DIRS["tables"] / "monthly_reduced_form_lp_coefficients.csv")
    proxy_rows = read_csv(FINAL_DIRS["diagnostics"] / "proxy_validation_tournament.csv")
    stability_rows = read_csv(FINAL_DIRS["stability"] / "monthly_directional_stability_matrix.csv")

    top_monthly_bridge = ""
    if monthly_tournament:
        top = monthly_tournament[0]
        top_monthly_bridge = (
            f"{top.get('target', '')} via {top.get('instrument', '')} "
            f"(F={top.get('first_stage_f_stat', '')}, status={top.get('final_screen', '')})"
        )
    summary = {
        "finished_at": utc_now().isoformat(),
        "canonical_notebook": CANONICAL_NOTEBOOK_REL,
        "canonical_output_root": "results/final",
        "monthly_first_stage_top_bridge": top_monthly_bridge,
        "monthly_reduced_form_cells": len(monthly_lp),
        "proxy_validation_candidates": len(proxy_rows),
        "monthly_stability_cells": len(stability_rows),
        "steps": [result.__dict__ for result in step_results],
    }
    (FINAL_DIRS["memos"] / "execution_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")

    lines = [
        "# Execution Summary",
        "",
        f"Main notebook: `{CANONICAL_NOTEBOOK_REL}`.",
        "Main outputs: `results/final/`.",
        "",
        "## Rebuild Steps",
        "",
    ]
    for index, result in enumerate(step_results, start=1):
        lines.append(f"{index}. {result.name} - completed with exit code {result.returncode}.")
    lines.extend(
        [
            "",
            "## Empirical Outputs",
            "",
            f"- Monthly first-stage top bridge: {top_monthly_bridge or 'not available'}.",
            f"- Monthly reduced-form LP cells: {len(monthly_lp)}.",
            f"- Proxy candidates screened: {len(proxy_rows)}.",
            f"- Monthly stability matrix cells: {len(stability_rows)}.",
            "",
            "Hard-IV treatment claims remain gated. The thesis interpretation is monthly reduced-form and tied to the ECB policy-news shock.",
        ]
    )
    (FINAL_DIRS["memos"] / "execution_summary.md").write_text("\n".join(lines) + "\n", encoding="utf-8")

    synthesis = [
        "# Empirical Synthesis",
        "",
        "The thesis uses monthly high-frequency ECB monetary-policy surprises rather than a quarterly ECB-assets IV treatment.",
        "",
        "The monthly first-stage screen does not support a hard-IV treatment bridge. The empirical layer is therefore reduced-form dynamic transmission from policy-news shocks.",
        "",
        "Housing and compensation are not interpolated into monthly data. The final comparison uses monthly housing-finance and real negotiated-wage-pressure proxies, with exact house-price, compensation, welfare, and redistribution magnitudes outside the claim boundary.",
    ]
    (FINAL_DIRS["memos"] / "final_empirical_synthesis.md").write_text("\n".join(synthesis) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Rebuild the thesis empirical results.")
    parser.add_argument("--skip-data", action="store_true", help="Do not rebuild processed data.")
    parser.add_argument("--skip-instrument", action="store_true", help="Do not rebuild ECB surprise inputs.")
    parser.add_argument("--skip-audit", action="store_true", help="Do not check final empirical outputs.")
    args = parser.parse_args()

    env = os.environ.copy()
    env["MPLCONFIGDIR"] = str(Path(tempfile.gettempdir()) / "thesis_model_mpl_cache")
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    ensure_final_dirs()

    step_results: list[StepResult] = []
    try:
        if not args.skip_data:
            step_results.append(run_step("Rebuild processed EU/DE data", ["Rscript", "src/data/build_final_dataset.R"], env))
        if not args.skip_instrument:
            step_results.append(
                run_step("Build ECB external-instrument shocks", [sys.executable, "-m", "src.data.ecb_monetary_surprises"], env)
            )
        copy_instrument_diagnostics()
        step_results.append(run_step("Build monthly model dataset", ["Rscript", "src/data/build_monthly_model_dataset.R"], env))
        step_results.append(run_step("Run monthly first-stage tournament", [sys.executable, "scripts/run_first_stage_tournament.py"], env))
        step_results.append(run_step("Run information-effect screening", [sys.executable, "scripts/run_information_effect_screening.py"], env))
        step_results.append(run_step("Screen monthly proxies", [sys.executable, "scripts/run_proxy_validation.py"], env))
        step_results.append(run_step("Run monthly reduced-form LP layer", [sys.executable, "scripts/run_monthly_reduced_form_lp.py"], env))
        # Diagnostic layer. Re-fits the baseline local projections and tests their
        # residuals. It changes no coefficient and writes only to results/final/uncertainty/.
        step_results.append(run_step("Run residual diagnostics on the baseline local projections", [sys.executable, "scripts/run_residual_diagnostics.py"], env))

        # Presentation layer. These steps only re-render figures and tables from
        # the canonical artifacts written above. They never estimate anything and
        # never write a CSV, so the empirical outputs are unaffected.
        step_results.append(run_step("Render thesis figures in the shared visual style", [sys.executable, "scripts/rebuild_figures.py"], env))
        step_results.append(run_step("Render enhancement figures", ["Rscript", "LATEX/scripts/create_enhancement_figures.R"], env))
        step_results.append(run_step("Generate thesis-facing LaTeX tables", [sys.executable, "LATEX/scripts/generate_thesis_tables.py"], env))

        write_execution_memos(step_results)
        remove_intermediate_outputs()

        if not args.skip_audit:
            step_results.append(run_step("Check final empirical outputs", [sys.executable, "scripts/final_empirical_audit.py"], env))
            write_execution_memos(step_results)
    except RuntimeError as exc:
        print(f"\nPipeline failed: {exc}", file=sys.stderr)
        return 1

    print("\nThesis empirical rebuild completed.")
    print(f"Final outputs: {FINAL_ROOT.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
