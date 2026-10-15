"""Rebuilt figures for the three largest figure families: baseline impulse
responses, cumulative response intervals, and uncertainty fans.

Presentation only. Every number plotted here is read unmodified from the
canonical CSVs that scripts/run_monthly_reduced_form_lp.py already wrote;
nothing in this module recomputes, resamples, or reorders an estimate.

FAMILY 1 - baseline impulse responses
    Source: results/final/tables/monthly_reduced_form_lp_coefficients.csv
    Filter: response == <response>, shock == "target_factor_monthly_easing"
    Series: coefficient with a 90 % HAC band (ci_90_low, ci_90_high)
    Mirrors write_svg_irf() in scripts/run_monthly_reduced_form_lp.py.

FAMILY 2 - cumulative response intervals
    Source: results/final/uncertainty/dependence_aware_cumulative_intervals.csv
    Filter: response == <response>, source_method == "moving_block"
    Series: a 90 % moving-block band (cumulative_ci_90_low/high); the center
    line is the interval midpoint, exactly as write_cumulative_interval_svg()
    plots it (that file carries no separate point-estimate column).
    Mirrors write_cumulative_interval_svg().

FAMILY 3 - uncertainty fans
    Source: results/final/uncertainty/moving_block_bootstrap_irfs.csv
    Filter: response == <response>
    Series: coefficient_common_sample with nested 68 / 90 / 95 % bands.
    Mirrors write_uncertainty_fan_svg().

Run as a script to (re)build all 30 PNGs (plus 30 PDF twins):
    python -m src.viz.fig_irf
"""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.viz import style as S

# --------------------------------------------------------------------- inputs
COEFFICIENTS_CSV = ROOT / "results" / "final" / "tables" / "monthly_reduced_form_lp_coefficients.csv"
DEPENDENCE_CUMULATIVE_CSV = ROOT / "results" / "final" / "uncertainty" / "dependence_aware_cumulative_intervals.csv"
MOVING_BLOCK_BOOTSTRAP_CSV = ROOT / "results" / "final" / "uncertainty" / "moving_block_bootstrap_irfs.csv"

# -------------------------------------------------------------------- outputs
FIG_DIR = ROOT / "results" / "final" / "figures"
BASELINE_DIR = FIG_DIR / "baseline"
CUMULATIVE_DIR = FIG_DIR / "cumulative"
UNCERTAINTY_DIR = FIG_DIR / "uncertainty"

TARGET_SHOCK = "target_factor_monthly_easing"

# The cumulative family carries the longest y-axis label in the thesis,
# "Cumulative response to a one-SD easing surprise", which sets 2.61 in of type
# along the axis. A y-axis label is centred on the axes, so the axes itself has
# to be at least that tall or the label runs off the fixed-width canvas. At the
# house golden ratio the axes is only 2.14 in high and the label overflowed the
# top edge by 0.19 in. The canvas width is fixed at S.FIG_WIDTH for every
# figure in the thesis, so the extra room is taken in height instead: this ratio
# leaves the axes 2.76 in high, about 0.12 in clear of the label.
CUMULATIVE_RATIO = 0.74

# The exact 10 responses covered by all three families (CANONICAL_COMPARISON_RESPONSES
# in scripts/run_monthly_reduced_form_lp.py), reproduced here read-only for filenames.
RESPONSES: tuple[str, ...] = (
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


def _clean_filename(value: str) -> str:
    """Same slugging rule as clean_filename() in the pipeline script."""
    import re

    return re.sub(r"[^A-Za-z0-9_]+", "_", value).strip("_")


# ------------------------------------------------------------- family 1: IRFs
def baseline_irf(response: str) -> Path:
    """Point IRF with a 90 % HAC band, for one response, one target-shock series."""
    coefficients = pd.read_csv(COEFFICIENTS_CSV)
    frame = coefficients.loc[
        coefficients["response"].eq(response) & coefficients["shock"].eq(TARGET_SHOCK)
    ].dropna(subset=["coefficient", "ci_90_low", "ci_90_high"])
    frame = frame.sort_values("horizon_months")

    h = frame["horizon_months"].to_numpy(dtype=float)
    b = frame["coefficient"].to_numpy(dtype=float)
    lo = frame["ci_90_low"].to_numpy(dtype=float)
    hi = frame["ci_90_high"].to_numpy(dtype=float)

    fig, ax = S.panel()
    ax.fill_between(h, lo, hi, color=S.STEEL_FILL, edgecolor=S.STEEL, linewidth=S.LW_HAIR,
                     label="90 % HAC interval", zorder=1.8)
    S.zero_line(ax)
    ax.plot(h, b, color=S.NAVY, linewidth=S.LW_MAIN, zorder=3, marker="o", markersize=S.MS_MAIN,
            markerfacecolor="white", markeredgecolor=S.NAVY, markeredgewidth=1.1,
            label="Impulse response")
    S.horizon_axis(ax, h)
    ax.set_ylabel("Response to a one-SD easing surprise")
    S.legend_below(ax, ncol=2)

    out_path = BASELINE_DIR / f"monthly_irf_{_clean_filename(response)}.png"
    S.save(fig, out_path)
    return out_path


# ------------------------------------------------ family 2: cumulative intervals
def cumulative_interval(response: str) -> Path:
    """Cumulative 90 % moving-block band, center at the interval midpoint.

    The source CSV carries no separate cumulative point-estimate column, so
    the midpoint-of-band center line reproduces exactly what
    write_cumulative_interval_svg() plots today.
    """
    dependence_cumulative = pd.read_csv(DEPENDENCE_CUMULATIVE_CSV)
    frame = dependence_cumulative.loc[
        dependence_cumulative["response"].eq(response)
        & dependence_cumulative["source_method"].eq("moving_block")
    ].dropna(subset=["cumulative_ci_90_low", "cumulative_ci_90_high"])
    frame = frame.sort_values("horizon_months")

    h = frame["horizon_months"].to_numpy(dtype=float)
    lo = frame["cumulative_ci_90_low"].to_numpy(dtype=float)
    hi = frame["cumulative_ci_90_high"].to_numpy(dtype=float)
    center = (lo + hi) / 2.0

    fig, ax = S.panel(ratio=CUMULATIVE_RATIO)
    ax.fill_between(h, lo, hi, color=S.STEEL_FILL, edgecolor=S.STEEL, linewidth=S.LW_HAIR,
                     label="90 % moving-block interval", zorder=1.8)
    S.zero_line(ax)
    ax.plot(h, center, color=S.NAVY, linewidth=S.LW_MAIN, zorder=3, marker="o", markersize=S.MS_MAIN,
            markerfacecolor="white", markeredgecolor=S.NAVY, markeredgewidth=1.1,
            label="Cumulative response (interval midpoint)")
    S.horizon_axis(ax, h)
    ax.set_ylabel("Cumulative response to a one-SD easing surprise")
    S.legend_below(ax, ncol=1)

    out_path = CUMULATIVE_DIR / f"cumulative_interval_{_clean_filename(response)}.png"
    S.save(fig, out_path)
    return out_path


# ---------------------------------------------------- family 3: uncertainty fans
def uncertainty_fan(response: str) -> Path:
    """Nested 68 / 90 / 95 % moving-block bootstrap bands around the central estimate."""
    moving_block_bootstrap = pd.read_csv(MOVING_BLOCK_BOOTSTRAP_CSV)
    frame = moving_block_bootstrap.loc[moving_block_bootstrap["response"].eq(response)].dropna(
        subset=["coefficient_common_sample", "ci_90_low", "ci_90_high"]
    )
    frame = frame.sort_values("horizon_months")

    h = frame["horizon_months"].to_numpy(dtype=float)
    center = frame["coefficient_common_sample"].to_numpy(dtype=float)
    lo95 = frame["ci_95_low"].to_numpy(dtype=float)
    hi95 = frame["ci_95_high"].to_numpy(dtype=float)
    lo90 = frame["ci_90_low"].to_numpy(dtype=float)
    hi90 = frame["ci_90_high"].to_numpy(dtype=float)
    lo68 = frame["ci_68_low"].to_numpy(dtype=float)
    hi68 = frame["ci_68_high"].to_numpy(dtype=float)

    fig, ax = S.panel()
    ax.fill_between(h, lo95, hi95, color=S.STEEL_FILL, edgecolor="none",
                     label="95 % HAC interval", zorder=1.4)
    ax.fill_between(h, lo90, hi90, color=S.STEEL, alpha=0.55, edgecolor="none",
                     label="90 % HAC interval", zorder=1.6)
    ax.fill_between(h, lo68, hi68, color=S.NAVY_LIGHT, alpha=0.35, edgecolor="none",
                     label="68 % HAC interval", zorder=1.8)
    S.zero_line(ax)
    ax.plot(h, center, color=S.NAVY, linewidth=S.LW_MAIN, zorder=3, marker="o", markersize=S.MS_MAIN,
            markerfacecolor="white", markeredgecolor=S.NAVY, markeredgewidth=1.1,
            label="Central estimate")
    S.horizon_axis(ax, h)
    ax.set_ylabel("Response to a one-SD easing surprise")
    S.legend_below(ax, ncol=2)

    out_path = UNCERTAINTY_DIR / f"uncertainty_fan_{_clean_filename(response)}.png"
    S.save(fig, out_path)
    return out_path


# ------------------------------------------------------------------------ all
def build_all() -> list[Path]:
    """Write all 30 PNGs (plus their 30 PDF twins) and return the PNG paths."""
    S.apply_style()
    written: list[Path] = []
    for response in RESPONSES:
        written.append(baseline_irf(response))
    for response in RESPONSES:
        written.append(cumulative_interval(response))
    for response in RESPONSES:
        written.append(uncertainty_fan(response))
    return written


if __name__ == "__main__":
    paths = build_all()
    for path in paths:
        print(path)
