#!/usr/bin/env python3
"""Rebuild every thesis-facing figure in the shared visual style.

Presentation only. This script reads the canonical artifacts under
results/final/ and data/processed/ and rewrites the figure files. It never
estimates anything, never writes a CSV, and never changes a value.

Each figure is written twice under the same basename: the PNG that the figure
contract in scripts/final_empirical_audit.py and the notebook figure registry
expect, and a PDF vector twin that the LaTeX build includes.

The R-generated figures under results/final/figures/enhancement/ are produced by
LATEX/scripts/create_enhancement_figures.R, which shares the same design
language and is run as a separate pipeline step.

Usage:
    python scripts/rebuild_figures.py
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.viz import style as S  # noqa: E402
from src.viz import fig_diagnostics, fig_instrument, fig_irf, fig_matrices  # noqa: E402

BUILDERS = (
    ("impulse responses, cumulative intervals, uncertainty fans", fig_irf.build_all),
    ("significance and persistence matrices", fig_matrices.build_all),
    ("stability, regime, banking and mechanism diagnostics", fig_diagnostics.build_all),
    ("instrument and proxy diagnostics", fig_instrument.build_all),
)


def main() -> int:
    S.apply_style()
    written: list[Path] = []
    failed: list[tuple[str, Exception]] = []

    for description, builder in BUILDERS:
        try:
            paths = builder() or []
            written.extend(Path(p) for p in paths)
            print(f"[ok]   {description}: {len(paths)} files")
        except Exception as exc:  # keep going so one family cannot block the rest
            failed.append((description, exc))
            print(f"[fail] {description}: {exc}", file=sys.stderr)

    png = sum(1 for p in written if p.suffix == ".png")
    pdf = sum(1 for p in written if p.suffix == ".pdf")
    print(f"\nfigures written: {png} png, {pdf} pdf")

    if failed:
        print(f"{len(failed)} figure family(ies) failed", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
