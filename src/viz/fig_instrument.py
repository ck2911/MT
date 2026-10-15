"""Rebuilt figures for the instrument diagnostics and the compensation proxy
tournament.

Presentation only. Every number plotted here is read unmodified from the
canonical CSVs that src/data/ecb_monetary_surprises.py and
scripts/run_proxy_validation.py already wrote; nothing in this module
recomputes an estimate. The one exception is the rolling-variance panel,
which reproduces the identical rolling(8, min_periods=4).var() transform
that crisis_clustering_outputs() in src/data/ecb_monetary_surprises.py
already applies for its own (differently styled) version of the same chart --
that is a display transform of raw factor sums, not a new estimate.

FIGURE 1 - instrument_quarter_density.png
    Source: results/final/diagnostics/quarter_density_diagnostics.csv
    Series: event_count by quarter (date)
    Mirrors the bottom panel written inside crisis_clustering_outputs()
    in src/data/ecb_monetary_surprises.py (the ax.plot(..., drawstyle=
    "steps-mid") call saved as quarter_density.png before being copied to
    the final name by scripts/run_full_pipeline.py).

FIGURE 2 - instrument_regime_histograms.png
    Source: data/processed/eu_de/ecb_surprise_event_level.csv
    Series: event-level timing_factor values, faceted by regime
    Mirrors the two stacked bar panels written inside
    crisis_clustering_outputs() (saved as regime_histograms.png), redesigned
    as small multiples of the actual instrument distribution per regime
    instead of two aggregate bar charts, per the design brief.

FIGURE 3 - quarterly_surprise_rolling_variance.png
    Source: data/processed/eu_de/ecb_surprise_quarterly.csv
    Series: 8-quarter rolling variance (min_periods=4) of each of the four
    quarterly factor sums (timing, target, forward guidance, QE)
    Mirrors the rolling-variance loop inside crisis_clustering_outputs().

FIGURE 4 - compensation/compensation_proxy_rankings.png
    Source: results/final/proxy_validation/compensation/compensation_proxy_rankings.csv
    Series: compensation_proxy_score by proxy, in scorecard rank order
    Mirrors write_compensation_rank_plot() in scripts/run_proxy_validation.py.

Run as a script to (re)build all 4 PNGs (plus their 4 PDF twins):
    python -m src.viz.fig_instrument
"""

from __future__ import annotations

import sys
from pathlib import Path

import matplotlib.dates as mdates
import matplotlib.patches as mpatches
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.viz import style as S

# --------------------------------------------------------------------- inputs
QUARTER_DENSITY_CSV = ROOT / "results" / "final" / "diagnostics" / "quarter_density_diagnostics.csv"
EVENT_LEVEL_CSV = ROOT / "data" / "processed" / "eu_de" / "ecb_surprise_event_level.csv"
QUARTERLY_CSV = ROOT / "data" / "processed" / "eu_de" / "ecb_surprise_quarterly.csv"
COMPENSATION_RANKINGS_CSV = (
    ROOT / "results" / "final" / "proxy_validation" / "compensation" / "compensation_proxy_rankings.csv"
)

# -------------------------------------------------------------------- outputs
FIG_DIR = ROOT / "results" / "final" / "figures"
COMPENSATION_FIG_DIR = FIG_DIR / "compensation"

# ---------------------------------------------------------------- vocabulary
# Chronological display order for the six identification regimes. This is a
# presentation-layer sequencing choice (small-multiples panel order), not a
# reordering of any estimate or ranking.
REGIME_ORDER = ["pre_gfc", "gfc", "euro_crisis", "qe_era", "covid", "tightening_regime"]
REGIME_LABELS = {
    "pre_gfc": "Pre-GFC",
    "gfc": "Global financial crisis",
    "euro_crisis": "Euro-area crisis",
    "qe_era": "QE era",
    "covid": "Covid-19",
    "tightening_regime": "Tightening regime",
}

FACTOR_COLUMNS = ["timing_factor_quarterly_sum", "target_factor_quarterly_sum",
                  "fg_factor_quarterly_sum", "qe_factor_quarterly_sum"]
FACTOR_LABELS = {
    "timing_factor_quarterly_sum": "Timing",
    "target_factor_quarterly_sum": "Target",
    "fg_factor_quarterly_sum": "Forward guidance",
    "qe_factor_quarterly_sum": "QE",
}
FACTOR_COLORS = {
    "timing_factor_quarterly_sum": S.NAVY,
    "target_factor_quarterly_sum": S.BRICK,
    "fg_factor_quarterly_sum": S.OLIVE,
    "qe_factor_quarterly_sum": S.NAVY_LIGHT,
}

STATUS_LABELS = {
    "primary_canonical_compensation_proxy": "Primary canonical proxy",
    "secondary_robustness_compensation_proxy": "Secondary robustness check",
    "noise_control_robustness_proxy": "Noise-control check",
    "not_selected": "Not selected",
}
STATUS_COLORS = {
    "primary_canonical_compensation_proxy": S.NAVY,
    "secondary_robustness_compensation_proxy": S.NAVY_LIGHT,
    "noise_control_robustness_proxy": S.STEEL,
    "not_selected": S.GREY_LIGHT,
}


def _date_axis(ax, *, interval_years: int = 3) -> None:
    """Yearly ticks for a quarterly time axis, kept sparse enough to read."""
    ax.xaxis.set_major_locator(mdates.YearLocator(interval_years))
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
    ax.set_xlabel("Year")


# ------------------------------------------------------------- layout helpers
# The canvas is exactly S.FIG_WIDTH wide and can no longer grow to fit whatever
# is drawn below the axes, so a note has to be wrapped to the room that is
# actually there and the layout engine has to be told to keep that room free.
# Presentation only: nothing below reads or alters a plotted value.

def _wrap_to_width(fig, text: str, avail_pt: float, fontsize: float) -> list[str]:
    """Break text into the fewest lines that each fit within avail_pt points."""
    renderer = fig.canvas.get_renderer()
    probe = fig.text(0.0, 0.0, "", fontsize=fontsize)

    def width_pt(candidate: str) -> float:
        probe.set_text(candidate)
        return probe.get_window_extent(renderer).width / fig.dpi * 72.0

    lines: list[str] = []
    current = ""
    for word in text.split():
        trial = f"{current} {word}".strip()
        if current and width_pt(trial) > avail_pt:
            lines.append(current)
            current = word
        else:
            current = trial
    if current:
        lines.append(current)
    probe.remove()
    return lines


def _note_below(fig, ax, text: str, *, pad_pt: float = 3.5) -> None:
    """Small note under the panel, in a band the layout engine keeps clear.

    The note is attached to the figure rather than to the axes, because on a
    constrained-layout figure only the reserved band is certain to sit inside
    the fixed canvas. It stays left-aligned with the panel, as S.note draws it.
    An outside legend is pinned to the bottom of the canvas by the layout
    engine and does not move when the band is reserved, so the note is placed
    in the strip directly above it.
    """
    engine = fig.get_layout_engine()
    fig.canvas.draw()
    height = fig.bbox.height
    pad_frac = pad_pt / 72.0 / fig.get_figheight()

    base = pad_frac
    for legend in fig.legends:
        top = legend.get_window_extent(fig.canvas.get_renderer()).y1 / height
        base = max(base, top + pad_frac)

    left_in = ax.get_position().x0 * fig.get_figwidth()
    avail_pt = (fig.get_figwidth() - left_in) * 72.0 - 4.0
    lines = _wrap_to_width(fig, text, avail_pt, S.FS_SMALL)
    note_top = base + (len(lines) * S.FS_SMALL * 1.3) / 72.0 / fig.get_figheight()

    # Grow the reserved band from nothing until the panel and its x label clear
    # the note. Measured rather than assumed, because an outside legend already
    # takes a strip of its own out of the rect the engine is given, and starting
    # from zero keeps that strip from being counted twice as white space.
    bottom = pad_frac
    for _ in range(6):
        engine.set(rect=(0.0, bottom, 1.0, 1.0 - bottom))
        fig.canvas.draw()
        deficit = note_top + pad_frac - ax.get_tightbbox(fig.canvas.get_renderer()).y0 / height
        if deficit <= 0.0:
            break
        bottom += deficit

    fig.text(ax.get_position().x0, base, "\n".join(lines), ha="left",
             va="bottom", linespacing=1.3, fontsize=S.FS_SMALL, color=S.GREY)


# ------------------------------------------------------- figure 1: quarter density
def instrument_quarter_density() -> Path:
    """Count of identified ECB surprise events per quarter, over the full sample."""
    frame = pd.read_csv(QUARTER_DENSITY_CSV, parse_dates=["date"]).sort_values("date")

    fig, ax = S.panel(width=S.FIG_WIDTH, ratio=0.52)
    ax.bar(
        frame["date"], frame["event_count"],
        width=78, color=S.STEEL_FILL, edgecolor=S.NAVY, linewidth=S.LW_HAIR,
        zorder=2, align="center",
    )
    ax.yaxis.set_major_locator(plt.MaxNLocator(integer=True))
    _date_axis(ax)
    ax.set_ylabel("Identified events per quarter")
    _note_below(fig, ax, "Quarterly count of ECB monetary policy events entering the surprise-factor identification, 2002-2025.")

    out_path = FIG_DIR / "instrument_quarter_density.png"
    S.save(fig, out_path)
    return out_path


# ---------------------------------------------------- figure 2: regime histograms
def instrument_regime_histograms() -> Path:
    """Small multiples of the event-level timing-factor distribution, by regime."""
    events = pd.read_csv(EVENT_LEVEL_CSV)
    values_all = events["timing_factor"].dropna().to_numpy(dtype=float)
    span = max(abs(values_all.min()), abs(values_all.max()))
    bins = np.linspace(-span, span, 21)

    regimes = [r for r in REGIME_ORDER if r in events["regime"].unique()]
    n = len(regimes)
    ncols = 3
    nrows = int(np.ceil(n / ncols))

    # Height carries the extra room the fixed canvas width cannot give: a panel
    # column is only about a third of 5.04 in wide, so the regime label is set
    # over two lines and the shared y limit gains headroom for it.
    fig, axes = plt.subplots(
        nrows, ncols, figsize=(S.FIG_WIDTH, S.FIG_WIDTH * 0.68),
        sharex=True, sharey=True,
    )
    axes_flat = np.atleast_1d(axes).ravel()

    tallest = 0
    for i, regime in enumerate(regimes):
        ax = axes_flat[i]
        values = events.loc[events["regime"].eq(regime), "timing_factor"].dropna().to_numpy(dtype=float)
        counts, _, _ = ax.hist(values, bins=bins, color=S.STEEL_FILL, edgecolor=S.NAVY,
                               linewidth=S.LW_HAIR, zorder=2)
        tallest = max(tallest, float(np.max(counts)) if len(counts) else 0.0)
        S.zero_line(ax, horizontal=False)
        ax.grid(True, axis="y", color=S.GRID, linewidth=0.5, zorder=0.5)
        S.tidy(ax, offset=3.0)
        ax.text(
            0.06, 0.97, f"{REGIME_LABELS.get(regime, regime)}\n(n={len(values)})",
            transform=ax.transAxes, ha="left", va="top", fontsize=S.FS_ANNOT, color=S.INK,
            linespacing=1.25,
            bbox=dict(facecolor="white", edgecolor="none", alpha=0.75, pad=1.5),
        )
        ax.label_outer()
        if i % ncols == 0:
            ax.set_ylabel("Event count")

    # Shared axis, so one headroom setting keeps every label clear of its bars.
    axes_flat[0].set_ylim(0.0, tallest * 1.42)

    for j in range(n, len(axes_flat)):
        axes_flat[j].set_visible(False)

    # tight_layout is kept for the grid, with the margins re-tuned for the fixed
    # width: pad reserves the outer rule of white, the shared x label sits just
    # under the bottom row instead of at the canvas edge, and a narrow w_pad
    # gives each panel enough width for its label.
    fig.supxlabel("Timing-factor surprise, event level", fontsize=S.FS_LABEL, y=0.022)
    fig.tight_layout(rect=(0.0, 0.0, 1.0, 1.0), pad=0.55, w_pad=0.45, h_pad=1.0)

    out_path = FIG_DIR / "instrument_regime_histograms.png"
    S.save(fig, out_path)
    return out_path


# -------------------------------------------------- figure 3: rolling variance
def quarterly_surprise_rolling_variance() -> Path:
    """Eight-quarter rolling variance of each quarterly factor sum."""
    quarterly = pd.read_csv(QUARTERLY_CSV, parse_dates=["date"]).sort_values("date").set_index("date")

    fig, ax = S.panel(width=S.FIG_WIDTH, ratio=0.58)
    for column in FACTOR_COLUMNS:
        rolling_var = quarterly[column].rolling(8, min_periods=4).var()
        ax.plot(
            quarterly.index, rolling_var,
            color=FACTOR_COLORS[column], linewidth=S.LW_MAIN, label=FACTOR_LABELS[column], zorder=3,
        )
    _date_axis(ax)
    ax.set_ylabel("8-quarter rolling variance")
    # Legend first: it is attached to the figure and the layout engine reserves
    # its strip, so the note band below it must be reserved after that.
    S.legend_below(ax, ncol=4)
    _note_below(fig, ax, "Rolling variance of the quarterly factor sum, 8-quarter window with a 4-quarter minimum.")

    out_path = FIG_DIR / "quarterly_surprise_rolling_variance.png"
    S.save(fig, out_path)
    return out_path


# ----------------------------------------------- figure 4: compensation ranking
def compensation_proxy_rankings() -> Path:
    """Horizontal ranked bar chart of the compensation proxy scorecard."""
    rankings = pd.read_csv(COMPENSATION_RANKINGS_CSV)
    rankings = rankings.sort_values(["rank", "variable"], kind="stable")

    labels = rankings["label"].astype(str).str.replace(", real", "", regex=False)
    values = rankings["compensation_proxy_score"].astype(float)
    statuses = rankings["canonical_status"].astype(str)
    colors = [STATUS_COLORS.get(s, S.GREY_LIGHT) for s in statuses]

    # The proxy names run to about 200 pt, more than half the fixed canvas
    # width, so the panel is made taller and the layout engine is left to
    # reserve the whole label column. The small rect inset keeps the longest
    # name off the paper edge rather than flush against it.
    fig, ax = S.panel(width=S.FIG_WIDTH, ratio=0.86)
    fig.get_layout_engine().set(rect=(0.006, 0.0, 0.988, 1.0))
    ax.grid(False, axis="y")
    ax.barh(range(len(rankings)), values, color=colors, edgecolor=S.RULE, linewidth=S.LW_HAIR, zorder=2)
    ax.set_yticks(range(len(rankings)))
    ax.set_yticklabels(labels, fontsize=S.FS_TICK)
    ax.invert_yaxis()
    ax.grid(True, axis="x", color=S.GRID, linewidth=0.5, zorder=0.5)
    S.tidy(ax)
    ax.set_xlabel("Compensation proxy score")

    present_statuses = [s for s in STATUS_LABELS if s in statuses.unique()]
    handles = [mpatches.Patch(facecolor=STATUS_COLORS[s], edgecolor=S.RULE, linewidth=S.LW_HAIR,
                               label=STATUS_LABELS[s]) for s in present_statuses]
    # Centred on the canvas, not on the (right-shifted) axes, and attached to the
    # figure so the constrained layout reserves the strip it needs.
    fig.legend(handles=handles, loc="outside lower center", ncol=2,
               frameon=False, fontsize=S.FS_LEGEND)

    out_path = COMPENSATION_FIG_DIR / "compensation_proxy_rankings.png"
    S.save(fig, out_path)
    return out_path


# ------------------------------------------------------------------------ all
def build_all() -> list[Path]:
    """Write all 4 PNGs (plus their 4 PDF twins) and return the PNG paths."""
    S.apply_style()
    return [
        instrument_quarter_density(),
        instrument_regime_histograms(),
        quarterly_surprise_rolling_variance(),
        compensation_proxy_rankings(),
    ]


if __name__ == "__main__":
    paths = build_all()
    for path in paths:
        print(path)
