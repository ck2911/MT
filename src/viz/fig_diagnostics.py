"""Rebuilt diagnostic, stability, regime and mechanism figures.

Presentation only. Every number plotted here is read unmodified from the
canonical CSVs that scripts/run_monthly_reduced_form_lp.py already wrote;
nothing in this module recomputes, resamples, re-sorts, or reclassifies an
estimate.

FAMILY 1 - rolling H6 stability (4 responses)
    Source: results/final/stability/monthly_rolling_window_lp.csv
    Filter: response == <response>, horizon_months == 6
    Series: coefficient against window_end, in chronological order.
    Mirrors write_rolling_stability_charts().

FAMILY 2 - clean vs contaminated H6 responses
    Source: results/final/stability/monthly_directional_stability_long.csv
    Filter: horizon_months == 6, sample_name in {full, clean_events_only,
    contaminated_events_only}
    Mirrors write_clean_event_chart(): one horizontal bar group per response,
    one bar per sample, same three columns, same pivot.

FAMILY 3 - uncertainty width comparison (moving-block vs wild bootstrap)
    Source: results/final/uncertainty/bootstrap_sensitivity_summary.csv
    Filter: horizon_months in {6, 12, 24}
    Series: width_ratio_mbb_to_wild by response, one line per response.
    Mirrors write_uncertainty_comparison_panel().

FAMILY 4 - regime H6 response comparison
    Source: results/final/regime/monthly_regime_reduced_form_lp.csv
    Filter: shock == target_factor_monthly_easing, horizon_months == 6,
    response in CANONICAL_COMPARISON_RESPONSES
    The original write_regime_chart() drew an imshow/RdBu heatmap that
    already used a diverging colormap to carry sign. Re-encoded here as three
    small-multiple horizontal bar panels, one per regime (pre-QE / QE /
    tightening; the covid column is not reproduced because every canonical
    response is NaN for that regime at h6, exactly as in the original pivot),
    bars colored navy for a positive coefficient and brick for a negative one
    to preserve that same sign information, with the identical `%.3g` value
    labels the heatmap printed in each cell. Same rows, same columns, same
    values; only the geometry changed. Each panel is barely an inch wide once
    three of them share the fixed canvas, which is not enough to set a bar and
    an eight-character number end to end, so the value label sits on the empty
    side of the zero rule, against its own bar's baseline.
    Mirrors write_regime_chart().

FAMILY 5 - banking and credit peak-timing evidence
    Source: results/final/mechanism/banking_timing_matrix.csv
    Filter: channel in {banking_lending_conditions, bank_lending_survey,
    financial_credit, housing_finance}, peak_abs_horizon not null
    Mirrors write_banking_timing_chart().

FAMILY 6 - sequential timing response map (mechanism pathways)
    Source: results/final/mechanism/intermediation_sequence_summary.csv
    Filter: status == estimated (all 8 pathways)
    The original write_mechanism_sequence_chart() was an upstream-vs-downstream
    scatter with every label colliding into an illegible pile: seven of the
    eight pathways have both coefficients within +/-0.15 of zero, while one
    pathway (employment_expectations_to_wage_pressure) has an upstream
    coefficient of 1.17, so a shared linear axis crushes the other seven to a
    single point at the origin. Re-encoded as a horizontal dumbbell chart, one
    row per pathway, the upstream and downstream response as two dots joined
    by a thin connector on a shared symmetric-log x-axis (identical
    coefficients, identical units; only the pixel mapping is nonlinear, and
    that nonlinearity is disclosed on the axis label). Every pathway is
    retained; none is dropped, merged, or relabeled - the y-axis label is the
    same `pathway` string with underscores turned into words, same
    transformation write_mechanism_sequence_chart() already applied before
    annotating each scatter point. Rows are sorted by downstream horizon
    (ascending) then pathway name (ascending): the three h3 pathways
    (household_credit_to_house_purchase_growth,
    house_purchase_growth_to_new_mortgage_flow, liquidity_to_nfc_credit) come
    first, then the five h6 pathways in alphabetical order. Upstream and
    downstream horizons are printed as small text at the right end of each
    row.
    Mirrors write_mechanism_sequence_chart().

Run as a script to (re)build all 9 PNGs (plus their 9 PDF twins):
    python -m src.viz.fig_diagnostics
"""

from __future__ import annotations

import re
import sys
import textwrap
from pathlib import Path

import matplotlib.pyplot as plt
import matplotlib.transforms as mtransforms
import numpy as np
import pandas as pd
from matplotlib.patches import Patch
from matplotlib.ticker import MaxNLocator

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.viz import style as S

# --------------------------------------------------------------------- inputs
ROLLING_CSV = ROOT / "results" / "final" / "stability" / "monthly_rolling_window_lp.csv"
STABILITY_LONG_CSV = ROOT / "results" / "final" / "stability" / "monthly_directional_stability_long.csv"
BOOTSTRAP_SENSITIVITY_CSV = ROOT / "results" / "final" / "uncertainty" / "bootstrap_sensitivity_summary.csv"
REGIME_CSV = ROOT / "results" / "final" / "regime" / "monthly_regime_reduced_form_lp.csv"
BANKING_TIMING_CSV = ROOT / "results" / "final" / "mechanism" / "banking_timing_matrix.csv"
SEQUENCE_CSV = ROOT / "results" / "final" / "mechanism" / "intermediation_sequence_summary.csv"

# -------------------------------------------------------------------- outputs
FIG_DIR = ROOT / "results" / "final" / "figures"
STABILITY_DIR = FIG_DIR / "stability"
UNCERTAINTY_DIR = FIG_DIR / "uncertainty"
REGIMES_DIR = FIG_DIR / "regimes"
BANKING_DIR = FIG_DIR / "banking"
MECHANISM_DIR = FIG_DIR / "mechanism"

TARGET_SHOCK = "target_factor_monthly_easing"

# The same 10 responses used throughout the pipeline script
# (CANONICAL_COMPARISON_RESPONSES), reproduced here read-only for filtering.
CANONICAL_COMPARISON_RESPONSES: tuple[str, ...] = (
    "ln_ecb_assets_ea_stock",
    "ln_dax_real_de",
    "ecb_mir_mortgage_lending_spread_dfr",
    "ecb_mir_nfc_lending_spread_dfr",
    "ln_nfc_loans_ea_stock",
    "ecb_house_purchase_growth_yoy",
    "ln_ecb_house_purchase_pure_new_loans",
    "ecb_wage_tracker_ex_oneoffs_real_yoy",
    "eurostat_sts_industry_wage_bill_de_real_yoy",
    "eurostat_ecfin_eei_ea20",
)

# The four responses covered by the rolling-stability figure family
# (enumerated from the pre-rebuild figures/stability/ directory).
ROLLING_RESPONSES: tuple[str, ...] = (
    "ecb_house_purchase_growth_yoy",
    "ecb_wage_tracker_ex_oneoffs_real_yoy",
    "ln_dax_real_de",
    "ln_ecb_house_purchase_pure_new_loans",
)

BANKING_CHANNELS: tuple[str, ...] = (
    "banking_lending_conditions",
    "bank_lending_survey",
    "financial_credit",
    "housing_finance",
)

REGIME_ORDER: tuple[str, ...] = ("pre_qe", "qe", "covid", "tightening")
REGIME_PANEL_LABEL = {
    "pre_qe": "Pre-QE regime",
    "qe": "QE regime",
    "covid": "Covid regime",
    "tightening": "Tightening regime",
}


def clean_filename(value: str) -> str:
    """Same slugging rule as clean_filename() in the pipeline script."""
    return re.sub(r"[^A-Za-z0-9_]+", "_", value).strip("_")


def _xgrid(ax) -> None:
    """Vertical hairline grid only, for horizontal bar charts where the value
    axis is x. Mirrors the intent of S.hgrid() but on the axis that actually
    carries the estimates in a barh chart."""
    ax.grid(True, axis="x", color=S.GRID, linewidth=0.5, zorder=0.5)
    ax.grid(False, axis="y")


# ------------------------------------------------------------- layout plumbing
# The canvas is exactly S.FIG_WIDTH wide and savefig no longer trims to a tight
# bounding box, so nothing may rely on the canvas growing to fit its type. Every
# margin below is therefore reserved in inches from the measured size of the type
# that has to sit in it - y tick labels, axis labels, panel headings, the legend
# block and, in the dumbbell chart, the horizon annotations drawn to the right of
# the axes. Only the height varies with the number of rows; the width never does.
# Same idiom as fig_matrices.
LEFT_PAD_IN = 0.05          # gap between the canvas edge and the longest y label
RIGHT_PAD_IN = 0.06         # gap right of the last thing drawn
TOP_PAD_IN = 0.10           # headroom above the panel (no in-figure title)
BOTTOM_PAD_IN = 0.08        # breathing room below the legend
LEGEND_GAP_IN = 0.14        # gap between the axis label and the legend block
TICK_PAD_PT = 3.5           # matplotlib default gap between tick and label
TICK_LEN_PT = 2.8           # major tick mark, drawn outward from the spine
SPINE_OFFSET_PT = 5.0       # S.tidy() detaches the spines by this much
LEGEND_ROW_IN = 1.35 * S.FS_LEGEND / 72.0   # legend row pitch at the house size

LEGEND_KW = dict(frameon=False, fontsize=S.FS_LEGEND)


def _measure(strings, fontsize: float) -> tuple[float, float]:
    """Largest rendered width and height of these strings, in inches."""
    fig = plt.figure(figsize=(S.FIG_WIDTH, 1.0))
    renderer = fig.canvas.get_renderer()
    widths, heights = [], []
    for text in strings:
        artist = fig.text(0.0, 0.0, str(text), fontsize=fontsize)
        box = artist.get_window_extent(renderer=renderer)
        artist.remove()
        widths.append(box.width / fig.dpi)
        heights.append(box.height / fig.dpi)
    plt.close(fig)
    return max(widths), max(heights)


def _legend_height_in(labels, ncol: int) -> float:
    """Height reserved for a frameless legend block, in inches."""
    rows = -(-len(labels) // ncol)
    _, line_h = _measure(labels, S.FS_LEGEND)
    return rows * max(line_h, LEGEND_ROW_IN) + 0.06


def _tick_gutter_in() -> float:
    """Distance from the axes edge to the near side of a tick label.

    S.tidy() pushes the spine outward and the tick marks and their labels travel
    with it, so all three pieces have to be paid for.
    """
    return (SPINE_OFFSET_PT + TICK_LEN_PT + TICK_PAD_PT) / 72.0


def _axis_bottom_in(tick_h: float, xlabel_h: float) -> float:
    """Height below the axes taken by tick labels and the x axis label."""
    return (_tick_gutter_in() + tick_h
            + plt.rcParams["axes.labelpad"] / 72.0 + xlabel_h)


def _left_in(label_w: float) -> float:
    """Left margin that shows the longest y tick label in full."""
    return LEFT_PAD_IN + label_w + _tick_gutter_in()


def _canvas_legend(fig, handles, labels, *, ncol: int, fig_h: float) -> None:
    """Legend centred on the canvas, sitting in the reserved bottom margin.

    The panels here start well to the right of the canvas edge, so a legend
    centred on the axes would sit off-centre or, on a multi-panel figure, hang
    over the edge. Anchoring it to the figure keeps it inside the fixed width.
    """
    fig.legend(handles, labels, ncol=ncol, loc="lower center",
               bbox_to_anchor=(0.5, BOTTOM_PAD_IN / fig_h),
               bbox_transform=fig.transFigure, **LEGEND_KW)


def _wrap(labels, width: int) -> list[str]:
    """Break long row labels over lines so the plotting area keeps its width.

    Only whitespace is turned into a line break: the label text itself is
    untouched.
    """
    return ["\n".join(textwrap.wrap(str(label), width=width)) for label in labels]


# ------------------------------------------------- family 1: rolling stability
def rolling_stability_chart(response: str) -> Path:
    """Rolling 84-month H6 coefficient path for one response."""
    rolling = pd.read_csv(ROLLING_CSV)
    frame = rolling.loc[
        rolling["response"].eq(response) & rolling["horizon_months"].eq(6)
    ].dropna(subset=["coefficient"]).copy()
    frame["window_end"] = pd.to_datetime(frame["window_end"])
    frame = frame.sort_values("window_end")

    x = frame["window_end"]
    y = frame["coefficient"].to_numpy(dtype=float)

    fig, ax = S.panel()
    S.zero_line(ax)
    ax.plot(x, y, color=S.NAVY, linewidth=S.LW_MAIN, zorder=3)
    ax.set_xlabel("Rolling 84-month window, end date")
    ax.set_ylabel("H6 response to a one-SD easing surprise")
    fig.autofmt_xdate(rotation=0, ha="center")

    out_path = STABILITY_DIR / f"rolling_stability_h6_{clean_filename(response)}.png"
    return S.save(fig, out_path)[0]


# --------------------------------------------- family 2: clean vs contaminated
def clean_vs_contaminated() -> Path:
    """H6 response under the full sample vs the clean- and contaminated-event
    subsamples, one horizontal bar group per response."""
    stability = pd.read_csv(STABILITY_LONG_CSV)
    focus = stability.loc[
        stability["sample_name"].isin(["full", "clean_events_only", "contaminated_events_only"])
        & stability["horizon_months"].eq(6)
    ].dropna(subset=["coefficient"]).copy()
    pivot = focus.pivot_table(index="response_label", columns="sample_name", values="coefficient", aggfunc="first")
    pivot = pivot.reindex(columns=["full", "clean_events_only", "contaminated_events_only"])

    labels = list(pivot.index)
    n = len(labels)
    y = np.arange(n)
    bar_h = 0.24
    colors = {"full": S.NAVY, "clean_events_only": S.OLIVE, "contaminated_events_only": S.BRICK_LIGHT}
    legend_labels = {
        "full": "Full sample",
        "clean_events_only": "Clean events only",
        "contaminated_events_only": "Contaminated events only",
    }

    fig_h = max(3.4, 0.40 * n + 1.6)
    # Constrained layout fits the long response labels and the legend below the
    # panel inside the fixed canvas width instead of pushing the canvas wider.
    fig, ax = plt.subplots(figsize=(S.FIG_WIDTH, fig_h), layout="constrained")
    fig.get_layout_engine().set(w_pad=0.03, h_pad=0.02)
    for i, column in enumerate(pivot.columns):
        offset = (i - 1) * bar_h
        ax.barh(y + offset, pivot[column].to_numpy(dtype=float), height=bar_h,
                color=colors[column], label=legend_labels[column], zorder=2)
    S.zero_line(ax, horizontal=False)
    _xgrid(ax)
    S.tidy(ax)
    ax.set_yticks(y, labels)
    ax.invert_yaxis()
    ax.set_xlabel("H6 response to a one-SD easing surprise")
    S.legend_below(ax, ncol=3)

    out_path = STABILITY_DIR / "clean_vs_contaminated_h6.png"
    return S.save(fig, out_path)[0]


# ------------------------------------------ family 3: uncertainty comparison
def uncertainty_width_comparison() -> Path:
    """90 % interval width ratio (moving-block to wild bootstrap) by response,
    at horizons 6, 12 and 24 months."""
    bootstrap = pd.read_csv(BOOTSTRAP_SENSITIVITY_CSV)
    focus = bootstrap.loc[bootstrap["horizon_months"].isin([6, 12, 24])].dropna(
        subset=["width_ratio_mbb_to_wild"]
    ).copy()
    responses = sorted(focus["response_label"].unique())

    colors = [S.NAVY, S.BRICK, S.OLIVE, S.NAVY_LIGHT, S.GREY]
    linestyles = ["-", "--"]
    markers = ["o", "s", "^", "D", "v"]

    # Taller than the house ratio: the five-row legend and the two-line y axis
    # label both have to be paid for out of the fixed canvas.
    fig, ax = S.panel(ratio=0.72)
    for i, label in enumerate(responses):
        group = focus.loc[focus["response_label"].eq(label)].sort_values("horizon_months")
        color = colors[i % len(colors)]
        linestyle = linestyles[(i // len(colors)) % len(linestyles)]
        marker = markers[i % len(markers)]
        ax.plot(
            group["horizon_months"], group["width_ratio_mbb_to_wild"],
            color=color, linestyle=linestyle, linewidth=S.LW_THIN,
            marker=marker, markersize=S.MS_MAIN, markerfacecolor="white",
            markeredgecolor=color, markeredgewidth=1.0, label=label, zorder=3,
        )
    ax.axhline(1.0, color=S.RULE, linewidth=0.75, zorder=1.6)
    S.horizon_axis(ax, [6, 12, 24])
    # Two lines: on one line this label is taller than the panel it labels.
    ax.set_ylabel("90 % interval width ratio,\nmoving-block to wild bootstrap")
    S.legend_below(ax, ncol=2)

    out_path = UNCERTAINTY_DIR / "uncertainty_width_comparison.png"
    return S.save(fig, out_path)[0]


# --------------------------------------------------- family 4: regime compare
def regime_response_comparison() -> Path:
    """H6 response by regime, re-encoded from an RdBu heatmap into sign-colored
    small-multiple horizontal bar panels (one panel per regime)."""
    regime = pd.read_csv(REGIME_CSV)
    focus = regime.loc[
        regime["shock"].eq(TARGET_SHOCK)
        & regime["horizon_months"].eq(6)
        & regime["response"].isin(CANONICAL_COMPARISON_RESPONSES)
    ].dropna(subset=["coefficient"]).copy()
    focus["regime"] = focus["sample_name"].str.replace("regime_", "", regex=False)
    pivot = focus.pivot_table(index="response_label", columns="regime", values="coefficient", aggfunc="first")
    columns = [c for c in REGIME_ORDER if c in pivot.columns]
    pivot = pivot.reindex(columns=columns)

    labels = list(pivot.index)
    n = len(labels)
    y = np.arange(n)

    # Three panels have to share one fixed-width canvas, so the response labels
    # are wrapped over two lines (whitespace only, no text changed) to buy the
    # panels their plotting width back.
    row_labels = _wrap(labels, 20)
    value_texts = [f"{v:.3g}" for v in pivot.to_numpy(dtype=float).ravel() if np.isfinite(v)]

    label_w, tick_h = _measure(row_labels, S.FS_TICK)
    value_w, _ = _measure(value_texts, S.FS_SMALL)
    xtick_w, _ = _measure(["-0.00"], S.FS_TICK)
    _, xlabel_h = _measure(["H6 response"], S.FS_LABEL)
    _, heading_h = _measure(list(REGIME_PANEL_LABEL.values()), S.FS_LABEL)

    legend_labels = ["Positive H6 response", "Negative H6 response"]
    handles = [
        Patch(facecolor=S.NAVY, edgecolor="none", label=legend_labels[0]),
        Patch(facecolor=S.BRICK, edgecolor="none", label=legend_labels[1]),
    ]

    left_in = _left_in(label_w)
    # The outermost x tick label is centred on the panel edge, so half of it
    # sticks out past the axes on either side.
    right_in = RIGHT_PAD_IN + 0.5 * xtick_w
    gap_in = 0.5 * xtick_w + 0.14          # keeps neighbouring x tick labels apart
    top_in = TOP_PAD_IN + heading_h
    bottom_in = (BOTTOM_PAD_IN + _legend_height_in(legend_labels, 2) + LEGEND_GAP_IN
                 + _axis_bottom_in(tick_h, xlabel_h))
    row_in = 0.34                          # fits a two-line row label
    fig_h = n * row_in + top_in + bottom_in

    panel_w = (S.FIG_WIDTH - left_in - right_in - (len(columns) - 1) * gap_in) / len(columns)
    fig, axes = plt.subplots(1, len(columns), figsize=(S.FIG_WIDTH, fig_h), sharey=True)
    if len(columns) == 1:
        axes = [axes]
    fig.subplots_adjust(left=left_in / S.FIG_WIDTH,
                        right=1.0 - right_in / S.FIG_WIDTH,
                        top=1.0 - top_in / fig_h,
                        bottom=bottom_in / fig_h,
                        wspace=gap_in / panel_w)

    for ax, column in zip(axes, columns):
        values = pivot[column]
        numeric = values.to_numpy(dtype=float)
        plot_values = np.nan_to_num(numeric, nan=0.0)
        bar_colors = [S.NAVY if (np.isfinite(v) and v >= 0) else S.BRICK for v in numeric]
        ax.barh(y, plot_values, height=0.62, color=bar_colors, zorder=2)
        S.zero_line(ax, horizontal=False)
        _xgrid(ax)
        S.tidy(ax)

        finite = numeric[np.isfinite(numeric)]
        span = float(np.max(np.abs(finite))) if finite.size else 1.0
        limit = 1.10 * span if span > 0 else 0.01
        ax.set_xlim(-limit, limit)
        # Three ticks per panel at most: a panel is barely an inch wide.
        ax.xaxis.set_major_locator(MaxNLocator(nbins=2, symmetric=True))

        # Value labels sit on the empty side of the zero rule, against the bar's
        # own baseline. A panel this narrow cannot hold a bar and an eight
        # character number end to end, so a label at the bar tip would be
        # clipped by the fixed canvas or would run into the next panel. Placed
        # opposite the bar, each label has the whole empty half of its row.
        pad = 0.035 * limit
        for yi, v in zip(y, numeric):
            if not np.isfinite(v):
                continue
            side = -1.0 if v >= 0 else 1.0
            ax.text(side * pad, yi, f"{v:.3g}", va="center",
                    ha="right" if v >= 0 else "left",
                    fontsize=S.FS_SMALL, color=S.INK, zorder=3)
        ax.text(0.5, 1.02, REGIME_PANEL_LABEL[column], transform=ax.transAxes,
                ha="center", va="bottom", fontsize=S.FS_LABEL, color=S.INK)
        ax.set_xlabel("H6 response")

    axes[0].set_yticks(y)
    axes[0].set_yticklabels(row_labels)
    axes[0].invert_yaxis()

    _canvas_legend(fig, handles, legend_labels, ncol=2, fig_h=fig_h)

    out_path = REGIMES_DIR / "regime_h6_response_comparison.png"
    return S.save(fig, out_path)[0]


# --------------------------------------------------- family 5: banking timing
def banking_peak_timing() -> Path:
    """Peak absolute-response horizon for banking- and credit-channel series."""
    timing = pd.read_csv(BANKING_TIMING_CSV)
    focus = timing.loc[timing["channel"].isin(BANKING_CHANNELS)].dropna(subset=["peak_abs_horizon"]).copy()
    focus = focus.sort_values(["channel", "peak_abs_horizon"], na_position="last").reset_index(drop=True)

    labels = focus["response_label"].tolist()
    values = focus["peak_abs_horizon"].to_numpy(dtype=float)
    channels = focus["channel"].tolist()
    n = len(labels)
    y = np.arange(n)

    # Shorter than before: the label column now sits inside the fixed width, so
    # the plotting area is narrower and the old height made the bars very thick.
    fig_h = max(3.0, 0.32 * n + 1.3)
    # Constrained layout keeps the long response labels inside the fixed canvas.
    fig, ax = plt.subplots(figsize=(S.FIG_WIDTH, fig_h), layout="constrained")
    fig.get_layout_engine().set(w_pad=0.03, h_pad=0.02)
    ax.barh(y, values, height=0.6, color=S.NAVY, zorder=2)
    _xgrid(ax)
    S.tidy(ax)
    ax.set_yticks(y, labels)
    ax.invert_yaxis()
    ax.set_xlabel("Peak absolute-response horizon, in months")

    for i in range(1, n):
        if channels[i] != channels[i - 1]:
            ax.axhline(i - 0.5, color=S.RULE, linewidth=S.LW_HAIR, zorder=1)

    out_path = BANKING_DIR / "banking_peak_timing.png"
    return S.save(fig, out_path)[0]


# ---------------------------------------------- family 6: mechanism sequence
def mechanism_sequence_map() -> Path:
    """Upstream vs downstream H-shock response by transmission pathway, as a
    horizontal dumbbell chart on a shared symmetric-log axis."""
    sequence = pd.read_csv(SEQUENCE_CSV)
    focus = sequence.loc[sequence["status"].eq("estimated")].copy()
    focus = focus.sort_values(["downstream_horizon_months", "pathway"]).reset_index(drop=True)

    n = len(focus)
    y = np.arange(n)
    upstream = focus["shock_to_upstream_coef"].to_numpy(dtype=float)
    downstream = focus["shock_to_downstream_coef"].to_numpy(dtype=float)
    # Pathway names run to 42 characters. Wrapped over two lines (whitespace
    # only) they leave the symmetric-log axis enough width for its tick labels.
    row_labels = _wrap([S.pretty_label(p) for p in focus["pathway"]], 24)
    horizon_texts = [S.horizon_pair(r.upstream_horizon_months, r.downstream_horizon_months)
                     for r in focus.itertuples()]

    legend_labels = ["Upstream response", "Downstream response"]
    label_w, _ = _measure(row_labels, S.FS_TICK)
    horizon_w, _ = _measure(horizon_texts, S.FS_SMALL)
    _, symlog_tick_h = _measure([r"$-10^{-1}$"], S.FS_TICK)
    _, xlabel_h = _measure(["Response to a one-SD easing surprise (symmetric-log scale)"], S.FS_LABEL)

    left_in = _left_in(label_w)
    # The horizon annotations are drawn just outside the axes on the right, at
    # ANNOT_X in axes coordinates. Their column has to be reserved here or the
    # fixed canvas simply cuts it off.
    annot_x = 1.02
    right_in = ((RIGHT_PAD_IN + horizon_w + (annot_x - 1.0) * (S.FIG_WIDTH - left_in))
                / (1.0 + (annot_x - 1.0)))
    bottom_in = (BOTTOM_PAD_IN + _legend_height_in(legend_labels, 2) + LEGEND_GAP_IN
                 + _axis_bottom_in(symlog_tick_h, xlabel_h))
    fig_h = n * 0.42 + TOP_PAD_IN + bottom_in

    fig, ax = plt.subplots(figsize=(S.FIG_WIDTH, fig_h))
    fig.subplots_adjust(left=left_in / S.FIG_WIDTH,
                        right=1.0 - right_in / S.FIG_WIDTH,
                        top=1.0 - TOP_PAD_IN / fig_h,
                        bottom=bottom_in / fig_h)
    for yi, u, d in zip(y, upstream, downstream):
        ax.plot([u, d], [yi, yi], color=S.GREY, linewidth=S.LW_THIN, zorder=2)
    ax.scatter(upstream, y, s=32, color=S.STEEL, edgecolor=S.NAVY, linewidth=0.8,
               zorder=3, label="Upstream response")
    ax.scatter(downstream, y, s=32, color=S.NAVY, edgecolor=S.NAVY, linewidth=0.8,
               zorder=3, label="Downstream response")

    ax.set_xscale("symlog", linthresh=0.002, linscale=1.0)
    ax.axvline(0, color=S.RULE, linewidth=0.75, zorder=1)
    _xgrid(ax)
    S.tidy(ax)
    ax.set_yticks(y)
    ax.set_yticklabels(row_labels)
    ax.invert_yaxis()
    ax.set_xlabel("Response to a one-SD easing surprise (symmetric-log scale)")

    trans = mtransforms.blended_transform_factory(ax.transAxes, ax.transData)
    for yi, text in zip(y, horizon_texts):
        ax.text(annot_x, yi, text, transform=trans, ha="left", va="center",
                fontsize=S.FS_SMALL, color=S.GREY, clip_on=False)

    handles, legend_handle_labels = ax.get_legend_handles_labels()
    _canvas_legend(fig, handles, legend_handle_labels, ncol=2, fig_h=fig_h)

    out_path = MECHANISM_DIR / "sequential_timing_response_map.png"
    return S.save(fig, out_path)[0]


# ------------------------------------------------------------------------ all
def build_all() -> list[Path]:
    """Write all 9 PNGs (plus their 9 PDF twins) and return the PNG paths."""
    S.apply_style()
    written: list[Path] = []
    for response in ROLLING_RESPONSES:
        written.append(rolling_stability_chart(response))
    written.append(clean_vs_contaminated())
    written.append(uncertainty_width_comparison())
    written.append(regime_response_comparison())
    written.append(banking_peak_timing())
    written.append(mechanism_sequence_map())
    return written


if __name__ == "__main__":
    paths = build_all()
    for path in paths:
        print(path)
