"""Refresh thesis results from inside the notebook when needed."""

from __future__ import annotations

import shutil
import subprocess
import sys

from .artifacts import warn_missing
from .display import Markdown, display
from .paths import PIPELINE_SCRIPT, ROOT

# R packages the data build and the enhancement figures need.
R_PACKAGES = ("readxl", "dplyr", "tidyr", "jsonlite", "ggplot2")


def _tail(text: str, max_chars: int = 12000) -> str:
    if not text:
        return ""
    return text if len(text) <= max_chars else text[-max_chars:]


def _r_ready() -> tuple[bool, str]:
    """Check that Rscript and the required R packages are available."""
    if shutil.which("Rscript") is None:
        return False, "R (Rscript) was not found on this computer"
    packages = ", ".join(f'"{name}"' for name in R_PACKAGES)
    check = subprocess.run(
        ["Rscript", "-e", f"quit(status = !all(sapply(c({packages}), requireNamespace, quietly = TRUE)))"],
        capture_output=True,
        text=True,
        check=False,
    )
    if check.returncode != 0:
        return False, "one or more R packages are missing (" + ", ".join(R_PACKAGES) + ")"
    return True, ""


def _show_stored(reason: str) -> None:
    display(
        Markdown(
            f"_Full re-estimation skipped: {reason}. The notebook continues with the stored results in "
            "`results/final/`, which are the results reported in the thesis. See README.md, section 1, "
            "to install R and enable it._"
        )
    )


def run_full_rebuild_if_requested(rebuild_results: bool) -> None:
    if not rebuild_results:
        return

    if not PIPELINE_SCRIPT.exists():
        warn_missing(PIPELINE_SCRIPT)
        _show_stored("scripts/run_full_pipeline.py is missing")
        return

    ready, reason = _r_ready()
    if not ready:
        _show_stored(reason)
        return

    display(Markdown("_Refreshing the stored empirical outputs before rendering the notebook._"))
    completed = subprocess.run(
        [sys.executable, str(PIPELINE_SCRIPT)],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    if completed.returncode != 0:
        if completed.stdout:
            print("\n--- captured stdout (tail) ---")
            print(_tail(completed.stdout))
        if completed.stderr:
            print("\n--- captured stderr (tail) ---")
            print(_tail(completed.stderr))
        _show_stored(f"the rebuild stopped with exit code {completed.returncode} (output above)")
        return
    display(Markdown("_Empirical outputs refreshed; rendering thesis presentation._"))
