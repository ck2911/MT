"""Rebuilt categorical-matrix figures: horizon significance and persistence.

Presentation only. Every cell plotted here is read unmodified from the
canonical CSVs that scripts/run_monthly_reduced_form_lp.py already wrote;
nothing in this module recomputes, resamples, re-sorts, or reclassifies an
estimate. The set of retained rows, the set of columns, and their order are
exactly what write_matrix_svg() in that script keeps: rows where every
column reads "not_estimated" are dropped (matching its
``~np.all(np.isnan(values), axis=1)`` filter), nothing else is filtered.

FIGURE 1 - horizon significance heatmap
    Source: results/final/uncertainty/significance_heatmap.csv
    Columns: response, response_label, channel, h0, h1, h3, h6, h12, h24
    Cell values (unchanged categorical labels): positive_p05, positive_p10,
    positive_not_significant, zero_not_significant, negative_not_significant,
    negative_p10, negative_p05, not_estimated.
    Mirrors write_matrix_svg(significance_heatmap, ..., heat_cols).

FIGURE 2 - cumulative persistence-confidence matrix
    Source: results/final/uncertainty/persistence_confidence_matrix.csv
    Columns: response, response_label, channel, h0_cum90 .. h24_cum90
    Cell values: booleans, True where the cumulative 90 % HAC interval
    through that horizon excludes zero.
    Mirrors write_matrix_svg(persistence_confidence, ..., persistence_cols).

Run as a script to (re)build both PNGs (plus their 2 PDF twins):
    python -m src.viz.fig_matrices
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from matplotlib.patches import Patch, Rectangle

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.viz import style as S

import matplotlib.pyplot as plt

# --------------------------------------------------------------------- inputs
SIGNIFICANCE_CSV = ROOT / "results" / "final" / "uncertainty" / "significance_heatmap.csv"
PERSISTENCE_CSV = ROOT / "results" / "final" / "uncertainty" / "persistence_confidence_matrix.csv"

# -------------------------------------------------------------------- outputs
SIGNIFICANCE_PNG = ROOT / "results" / "final" / "figures" / "uncertainty" / "significance_heatmap.png"
PERSISTENCE_PNG = ROOT / "results" / "final" / "figures" / "stability" / "persistence_confidence_matrix.png"

# ------------------------------------------------------ significance encoding
# Same seven buckets and the same left-to-right (positive -> zero -> negative)
# reading as color_scores in write_matrix_svg(); only the palette changes,
# from matplotlib's stock RdBu to the house diverging ramp in style.py.
SIG_CATEGORY_ORDER = [
    "positive_p05",
    "positive_p10",
    "positive_not_significant",
    "zero_not_significant",
    "negative_not_significant",
    "negative_p10",
    "negative_p05",
]
SIG_CATEGORY_COLOR = {
    "positive_p05": S.DIVERGING[6],
    "positive_p10": S.DIVERGING[5],
    "positive_not_significant": S.DIVERGING[4],
    "zero_not_significant": S.DIVERGING[3],
    "negative_not_significant": S.DIVERGING[2],
    "negative_p10": S.DIVERGING[1],
    "negative_p05": S.DIVERGING[0],
}
SIG_CATEGORY_TEXT = {
    "positive_p05": "+  p<.05",
    "positive_p10": "+  p<.10",
    "positive_not_significant": "+",
    "zero_not_significant": "0",
    "negative_not_significant": "−",
    "negative_p10": "−  p<.10",
    "negative_p05": "−  p<.05",
}
SIG_CATEGORY_LEGEND_LABEL = {
    "positive_p05": "Positive, p < .05",
    "positive_p10": "Positive, p < .10",
    "positive_not_significant": "Positive, not significant",
    "zero_not_significant": "Approximately zero",
    "negative_not_significant": "Negative, not significant",
    "negative_p10": "Negative, p < .10",
    "negative_p05": "Negative, p < .05",
}
SIG_WHITE_TEXT_CATEGORIES = {"positive_p05", "negative_p05"}
NOT_ESTIMATED_COLOR = S.GREY_LIGHT
NOT_ESTIMATED_TEXT = ""
NOT_ESTIMATED_LEGEND_LABEL = "Not estimated"


def _draw_cells(ax, n_rows: int, n_cols: int, colors: list, texts: list, text_colors: list) -> None:
    """Paint one categorical grid: thin white separators, centered annotations."""
    for row in range(n_rows):
        for col in range(n_cols):
            ax.add_patch(
                Rectangle(
                    (col, row), 1.0, 1.0,
                    facecolor=colors[row][col],
                    edgecolor="white",
                    linewidth=1.4,
                    zorder=1,
                )
            )
            label = texts[row][col]
            if label:
                ax.text(
                    col + 0.5, row + 0.5, label,
                    ha="center", va="center",
                    fontsize=CELL_FS, color=text_colors[row][col],
                    zorder=2,
                )
    ax.set_xlim(0, n_cols)
    ax.set_ylim(n_rows, 0)  # row 0 (first data row) at the top
    ax.set_yticks(np.arange(n_rows) + 0.5)
    ax.set_xticks(np.arange(n_cols) + 0.5)
    for side in ("top", "right", "bottom", "left"):
        ax.spines[side].set_visible(False)
    ax.tick_params(length=0, pad=TICK_PAD_PT)
    ax.grid(False)


# ------------------------------------------------------- figure 1: significance
def significance_heatmap() -> Path:
    """Horizon-by-response significance matrix for the target-factor shock."""
    frame = pd.read_csv(SIGNIFICANCE_CSV)
    horizon_columns = [c for c in frame.columns if re.fullmatch(r"h[0-9]+", c)]
    horizon_columns = sorted(horizon_columns, key=lambda c: int(c[1:]))

    keep = ~(frame[horizon_columns] == "not_estimated").all(axis=1)
    frame = frame.loc[keep].reset_index(drop=True)

    labels = frame["response_label"].astype(str).tolist()
    n_rows, n_cols = len(labels), len(horizon_columns)

    colors = [[None] * n_cols for _ in range(n_rows)]
    texts = [[None] * n_cols for _ in range(n_rows)]
    text_colors = [[None] * n_cols for _ in range(n_rows)]
    present_categories: list[str] = []
    any_not_estimated = False
    for r in range(n_rows):
        for c, column in enumerate(horizon_columns):
            raw = frame.at[r, column]
            if raw == "not_estimated":
                colors[r][c] = NOT_ESTIMATED_COLOR
                texts[r][c] = NOT_ESTIMATED_TEXT
                text_colors[r][c] = S.GREY
                any_not_estimated = True
                continue
            colors[r][c] = SIG_CATEGORY_COLOR[raw]
            texts[r][c] = SIG_CATEGORY_TEXT[raw]
            text_colors[r][c] = "white" if raw in SIG_WHITE_TEXT_CATEGORIES else S.INK
            if raw not in present_categories:
                present_categories.append(raw)

    ordered = [c for c in SIG_CATEGORY_ORDER if c in present_categories]
    handles = [
        Patch(facecolor=SIG_CATEGORY_COLOR[c], edgecolor="none", label=SIG_CATEGORY_LEGEND_LABEL[c])
        for c in ordered
    ]
    if any_not_estimated:
        handles.append(Patch(facecolor=NOT_ESTIMATED_COLOR, edgecolor="none", label=NOT_ESTIMATED_LEGEND_LABEL))

    fig, ax = fig_and_axis(n_rows, labels=labels, handles=handles, ncol=3,
                           xlabel="Horizon in months")
    _draw_cells(ax, n_rows, n_cols, colors, texts, text_colors)
    ax.set_yticklabels(labels, fontsize=S.FS_TICK)
    ax.set_xticklabels([c[1:] for c in horizon_columns], fontsize=S.FS_TICK)

    return S.save(fig, SIGNIFICANCE_PNG)[0]


# -------------------------------------------------------- figure 2: persistence
def persistence_confidence_matrix() -> Path:
    """Cumulative 90 % HAC persistence matrix for the target-factor shock."""
    frame = pd.read_csv(PERSISTENCE_CSV)
    horizon_columns = [c for c in frame.columns if re.fullmatch(r"h[0-9]+_cum90", c)]
    horizon_columns = sorted(horizon_columns, key=lambda c: int(re.match(r"h([0-9]+)_cum90", c).group(1)))

    labels = frame["response_label"].astype(str).tolist()
    n_rows, n_cols = len(labels), len(horizon_columns)

    true_color = S.SEQUENTIAL[6]
    false_color = S.SEQUENTIAL[0]

    colors = [[None] * n_cols for _ in range(n_rows)]
    texts = [[None] * n_cols for _ in range(n_rows)]
    text_colors = [[None] * n_cols for _ in range(n_rows)]
    for r in range(n_rows):
        for c, column in enumerate(horizon_columns):
            value = bool(frame.at[r, column])
            colors[r][c] = true_color if value else false_color
            texts[r][c] = "90%" if value else ""
            text_colors[r][c] = "white"

    handles = [
        Patch(facecolor=true_color, edgecolor="none", label="Cumulative response excludes zero (90 % HAC)"),
        Patch(facecolor=false_color, edgecolor=S.RULE, linewidth=S.LW_HAIR, label="Not distinguishable from zero"),
    ]

    fig, ax = fig_and_axis(n_rows, labels=labels, handles=handles, ncol=2,
                           xlabel="Horizon in months (cumulative through h)")
    _draw_cells(ax, n_rows, n_cols, colors, texts, text_colors)
    ax.set_yticklabels(labels, fontsize=S.FS_TICK)
    ax.set_xticklabels([re.match(r"h([0-9]+)_cum90", c).group(1) for c in horizon_columns], fontsize=S.FS_TICK)

    return S.save(fig, PERSISTENCE_PNG)[0]


# ------------------------------------------------------------------- plumbing
# The canvas width is fixed at S.FIG_WIDTH, so every margin is reserved in
# inches and only the height varies with the number of matrix rows. Nothing may
# rely on a tight bounding box: the y tick labels, the axis label and the legend
# all have to be paid for out of the fixed canvas.
ROW_HEIGHT_IN = 0.300     # physical height of one matrix row, fixed regardless of row count
TOP_MARGIN_IN = 0.10      # thin headroom above the top row (no in-figure title)
LEFT_PAD_IN = 0.05        # safety gap between the canvas edge and the longest y label
RIGHT_PAD_IN = 0.05       # safety gap right of the last column
TICK_PAD_PT = 2.5         # gap between a tick label and the matrix, both axes
LEGEND_GAP_IN = 0.16      # gap between the axis label and the legend block
BOTTOM_PAD_IN = 0.08      # thin breathing room below the legend
LEGEND_SIDE_PAD_IN = 0.06  # minimum clearance the legend keeps from either edge
CELL_FS = S.FS_SMALL      # cell annotations, sized so "+  p<.05" fits one column

LEGEND_KW = dict(frameon=False, fontsize=S.FS_LEGEND, handlelength=1.2,
                 handletextpad=0.5, columnspacing=1.1)


def _text_size_in(fig, renderer, text: str, fontsize: float) -> tuple[float, float]:
    """Rendered width and height of one string, in inches."""
    artist = fig.text(0.0, 0.0, text, fontsize=fontsize)
    box = artist.get_window_extent(renderer=renderer)
    artist.remove()
    return box.width / fig.dpi, box.height / fig.dpi


def _legend_size_in(fig, renderer, handles: list, ncol: int) -> tuple[float, float]:
    """Rendered width and height of the discrete legend block, in inches."""
    legend = fig.legend(handles=handles, ncol=ncol, loc="lower center", **LEGEND_KW)
    fig.canvas.draw()
    box = legend.get_window_extent(renderer=renderer)
    legend.remove()
    return box.width / fig.dpi, box.height / fig.dpi


def fig_and_axis(n_rows: int, *, labels: list, handles: list, ncol: int, xlabel: str):
    """Build the figure/axes with measured fixed-inch margins.

    The left margin is measured from the longest response label, the bottom
    margin from the actual height of the x tick labels, the axis label and the
    legend block, so nothing spills over the fixed-width canvas. Row height is
    constant, so a matrix with more rows gets a taller figure, never a narrower
    one. The legend is attached to the figure and centred on the canvas: the
    axes start almost halfway across the width, so an axes-centred legend would
    hang off the right edge.
    """
    scratch = plt.figure(figsize=(S.FIG_WIDTH, 1.0))
    renderer = scratch.canvas.get_renderer()
    label_w = max(_text_size_in(scratch, renderer, str(t), S.FS_TICK)[0] for t in labels)
    tick_h = _text_size_in(scratch, renderer, "0123456789", S.FS_TICK)[1]
    xlabel_h = _text_size_in(scratch, renderer, xlabel, S.FS_LABEL)[1]
    legend_w, legend_h = _legend_size_in(scratch, renderer, handles, ncol)
    while ncol > 1 and legend_w > S.FIG_WIDTH - 2.0 * LEGEND_SIDE_PAD_IN:
        ncol -= 1
        legend_w, legend_h = _legend_size_in(scratch, renderer, handles, ncol)
    plt.close(scratch)

    tick_pad_in = TICK_PAD_PT / 72.0
    left_in = LEFT_PAD_IN + label_w + tick_pad_in
    axis_bottom_in = (tick_pad_in + tick_h
                      + plt.rcParams["axes.labelpad"] / 72.0 + xlabel_h)
    bottom_in = BOTTOM_PAD_IN + legend_h + LEGEND_GAP_IN + axis_bottom_in
    fig_h = n_rows * ROW_HEIGHT_IN + TOP_MARGIN_IN + bottom_in

    fig, ax = plt.subplots(figsize=(S.FIG_WIDTH, fig_h))
    fig.subplots_adjust(
        left=left_in / S.FIG_WIDTH,
        right=1.0 - RIGHT_PAD_IN / S.FIG_WIDTH,
        top=1.0 - TOP_MARGIN_IN / fig_h,
        bottom=bottom_in / fig_h,
    )
    ax.set_xlabel(xlabel)
    fig.legend(handles=handles, ncol=ncol, loc="lower center",
               bbox_to_anchor=(0.5, BOTTOM_PAD_IN / fig_h),
               bbox_transform=fig.transFigure, **LEGEND_KW)
    return fig, ax


# ------------------------------------------------------------------------ all
def build_all() -> list[Path]:
    """Write both PNGs (plus their PDF twins) and return the PNG paths."""
    S.apply_style()
    return [significance_heatmap(), persistence_confidence_matrix()]


if __name__ == "__main__":
    paths = build_all()
    for path in paths:
        print(path)
