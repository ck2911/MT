"""Project-root and result-path helpers."""

from __future__ import annotations

import os
import sys
from pathlib import Path

ROOT_MARKERS = (
    "1. thesis_master_notebook.ipynb",
    "scripts/run_full_pipeline.py",
    "data",
)


def _candidate_start_paths() -> list[Path]:
    starts: list[Path] = []
    try:
        starts.append(Path.cwd().resolve())
    except Exception:
        pass

    notebook_hint = globals().get("__vsc_ipynb_file__") or globals().get("__file__")
    if notebook_hint:
        try:
            starts.append(Path(notebook_hint).resolve().parent)
        except Exception:
            pass

    env_hint = os.environ.get("THESIS_MODEL_ROOT")
    if env_hint:
        try:
            starts.append(Path(env_hint).resolve())
        except Exception:
            pass

    unique: list[Path] = []
    for start in starts:
        if start not in unique:
            unique.append(start)
    return unique


def _has_project_markers(candidate: Path) -> bool:
    return all((candidate / marker).exists() for marker in ROOT_MARKERS)


def find_project_root() -> Path:
    diagnostics: list[str] = []
    for start in _candidate_start_paths():
        for candidate in [start, *start.parents]:
            diagnostics.append(str(candidate))
            if _has_project_markers(candidate):
                return candidate

    marker_text = "\n  - ".join(ROOT_MARKERS)
    tried = "\n  - ".join(dict.fromkeys(diagnostics))
    raise FileNotFoundError(
        "Could not locate THESIS_Model project root.\n"
        f"Required markers:\n  - {marker_text}\n"
        f"Candidate directories checked:\n  - {tried}\n"
        "Set THESIS_MODEL_ROOT if the project was moved."
    )


ROOT = find_project_root()
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

DATA = ROOT / "data" / "processed" / "eu_de"
RAW = ROOT / "data" / "raw" / "eu_de"
FINAL = ROOT / "results" / "final"
DOCS = ROOT / "docs"
NOTEBOOK = ROOT / "1. thesis_master_notebook.ipynb"
PIPELINE_SCRIPT = ROOT / "scripts" / "run_full_pipeline.py"


def rel(path: Path | str) -> str:
    candidate = Path(path)
    try:
        return str(candidate.resolve().relative_to(ROOT))
    except Exception:
        return str(candidate)


def artifact_path(*parts: str | Path) -> Path:
    if len(parts) == 1:
        path = Path(parts[0])
        return path if path.is_absolute() else ROOT / path
    return ROOT.joinpath(*[str(part) for part in parts])


def artifact_label(path: Path | str) -> str:
    return rel(artifact_path(path))
