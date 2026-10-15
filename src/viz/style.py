"""Thesis visual design system.

One shared visual language for every figure in the thesis. Presentation only.
Nothing in this module reads, computes, or alters an estimate.

Design targets a serif, restrained, ECB-working-paper aesthetic that matches the
document body font (Times New Roman, 12 pt, 1.5 spacing, 2.5 cm margins).

Figures are designed at their final printed size so that type inside a figure
matches the surrounding caption type. The text block is 16 cm wide, and the
default figure include width is 0.88 of that, so the canonical single-panel
width is about 5.5 inches.
"""

from __future__ import annotations

from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.font_manager as fm
import matplotlib.pyplot as plt

# --------------------------------------------------------------------- palette
# Restrained academic palette. Navy carries the estimate, steel carries
# uncertainty, brick is the single contrast accent, greys carry structure.
NAVY = "#1F3B57"
NAVY_LIGHT = "#41627F"
STEEL = "#AFC2D1"
STEEL_FILL = "#DCE5EC"
BRICK = "#9C4722"
BRICK_LIGHT = "#C08163"
OLIVE = "#5F6B4A"
INK = "#22282C"
GREY = "#6E7B85"
GREY_LIGHT = "#AAB4BB"
RULE = "#3F484E"
GRID = "#E7EBEE"
POSITIVE = NAVY
NEGATIVE = BRICK

# Sequential ramp for matrices, light to deep navy. No rainbow.
SEQUENTIAL = ["#F4F7F9", "#DCE5EC", "#B9CBD9", "#8EA9BF", "#5F82A0", "#3A5F7F", "#1F3B57"]
# Diverging ramp, brick through neutral to navy, for signed matrices.
DIVERGING = ["#9C4722", "#C08163", "#E3C8B8", "#F2F2F0", "#C3D2DD", "#7E9CB4", "#1F3B57"]

# ----------------------------------------------------------------------- sizes
TEXT_WIDTH_IN = 6.30      # 16 cm text block
INCLUDE_FRACTION = 0.80   # the single \thesisfigure include width

# Every figure canvas is exactly the printed include width, so LaTeX scales all
# figures by 1.0 and type inside a figure prints at the size set here. Saving
# with a tight bounding box would let the canvas grow with the longest tick
# label, which would make each figure scale differently and type sizes drift
# across the thesis. Width is therefore fixed and only height varies.
FIG_WIDTH = TEXT_WIDTH_IN * INCLUDE_FRACTION   # 5.04 in = 362.9 pt
FIG_WIDTH_WIDE = FIG_WIDTH                     # kept as an alias, same width
GOLDEN = 0.618

FS_LABEL = 9.5
FS_TICK = 8.5
FS_LEGEND = 8.5
FS_ANNOT = 8.0
FS_SMALL = 7.5

LW_MAIN = 1.5
LW_THIN = 0.7
LW_HAIR = 0.55
MS_MAIN = 3.6

DPI_RASTER = 400


def _serif_family() -> list[str]:
    """Prefer the document font, then the closest available serif fallbacks."""
    available = {f.name for f in fm.fontManager.ttflist}
    preferred = ["Times New Roman", "STIX Two Text", "Nimbus Roman",
                 "TeX Gyre Termes", "Charter", "DejaVu Serif"]
    chosen = [name for name in preferred if name in available]
    return chosen or ["serif"]


def apply_style() -> None:
    """Install the thesis rcParams. Call once before building figures."""
    family = _serif_family()
    plt.rcdefaults()
    plt.rcParams.update({
        "font.family": "serif",
        "font.serif": family,
        "mathtext.fontset": "custom",
        "mathtext.rm": family[0],
        "mathtext.it": f"{family[0]}:italic",
        "mathtext.bf": f"{family[0]}:bold",

        "figure.figsize": (FIG_WIDTH, FIG_WIDTH * GOLDEN),
        "figure.dpi": 120,
        "figure.facecolor": "white",
        "savefig.facecolor": "white",
        "savefig.dpi": DPI_RASTER,
        # No tight bbox: the canvas must stay exactly FIG_WIDTH wide.
        "savefig.bbox": None,
        "savefig.pad_inches": 0.0,

        "axes.facecolor": "white",
        "axes.edgecolor": RULE,
        "axes.linewidth": LW_HAIR,
        "axes.labelcolor": INK,
        "axes.labelsize": FS_LABEL,
        "axes.labelpad": 5.0,
        "axes.titlesize": FS_LABEL,      # titles are normally left to the caption
        "axes.titleweight": "normal",
        "axes.titlecolor": INK,
        "axes.spines.top": False,
        "axes.spines.right": False,
        "axes.axisbelow": True,
        "axes.prop_cycle": plt.cycler(color=[NAVY, BRICK, OLIVE, NAVY_LIGHT, GREY]),

        "grid.color": GRID,
        "grid.linewidth": 0.5,
        "grid.alpha": 1.0,

        "xtick.color": INK,
        "ytick.color": INK,
        "xtick.labelsize": FS_TICK,
        "ytick.labelsize": FS_TICK,
        "xtick.direction": "out",
        "ytick.direction": "out",
        "xtick.major.size": 2.8,
        "ytick.major.size": 2.8,
        "xtick.major.width": LW_HAIR,
        "ytick.major.width": LW_HAIR,
        "xtick.minor.size": 1.6,
        "ytick.minor.size": 1.6,

        "legend.fontsize": FS_LEGEND,
        "legend.frameon": False,
        "legend.handlelength": 1.6,
        "legend.handletextpad": 0.55,
        "legend.labelspacing": 0.35,
        "legend.columnspacing": 1.2,
        "legend.borderaxespad": 0.2,

        "lines.linewidth": LW_MAIN,
        "lines.markersize": MS_MAIN,
        "lines.solid_capstyle": "round",

        "patch.linewidth": 0.0,
        "hatch.linewidth": 0.5,
        "text.color": INK,
    })


# ------------------------------------------------------------------- utilities
def zero_line(ax, *, horizontal: bool = True) -> None:
    """Thin reference line at zero, drawn beneath the data."""
    fn = ax.axhline if horizontal else ax.axvline
    fn(0.0, color=RULE, linewidth=0.75, zorder=1.6)


def hgrid(ax) -> None:
    """Horizontal hairline grid only. Vertical rules add noise on horizon axes."""
    ax.grid(True, axis="y", color=GRID, linewidth=0.5, zorder=0.5)
    ax.grid(False, axis="x")


def tidy(ax, *, offset: float = 5.0) -> None:
    """Detach the remaining spines slightly so the frame reads lighter."""
    for side in ("left", "bottom"):
        ax.spines[side].set_position(("outward", offset))
        ax.spines[side].set_linewidth(LW_HAIR)
        ax.spines[side].set_color(RULE)


def horizon_axis(ax, horizons, *, label: str = "Horizon in months") -> None:
    """Tick only at the estimated horizons and keep the true linear spacing."""
    values = [float(h) for h in horizons]
    ax.set_xticks(values)
    ax.set_xticklabels([f"{int(v)}" for v in values])
    span = max(values) - min(values) if len(values) > 1 else 1.0
    ax.set_xlim(min(values) - 0.04 * span, max(values) + 0.04 * span)
    ax.set_xlabel(label)


def legend_below(ax, *, ncol: int = 2, y: float = -0.22) -> None:
    """Legend under the panel, frameless, so it never covers an interval band.

    On a constrained-layout figure the legend is attached to the figure with an
    outside location, which is the only placement the layout engine reserves
    room for. Without that, a legend hung below the axes would be clipped now
    that the canvas width is fixed. The `y` argument is kept for call-site
    compatibility and is used only in the non-constrained fallback.
    """
    fig = ax.get_figure()
    handles, labels = ax.get_legend_handles_labels()
    if not handles:
        return
    engine = getattr(fig, "get_layout_engine", lambda: None)()
    if engine is not None:
        fig.legend(handles, labels, loc="outside lower center", ncol=ncol,
                   frameon=False, fontsize=FS_LEGEND)
    else:
        ax.legend(handles, labels, loc="upper center", bbox_to_anchor=(0.5, y),
                  ncol=ncol, frameon=False, fontsize=FS_LEGEND)


def note(ax, text: str, *, y: float = -0.34) -> None:
    """Small left-aligned note under the panel for units or scaling remarks."""
    ax.text(0.0, y, text, transform=ax.transAxes, ha="left", va="top",
            fontsize=FS_SMALL, color=GREY)


# Abbreviations that must stay capitalised so figure labels match the thesis
# terminology and the List of Abbreviations.
_ABBREV = {
    "nfc": "NFC", "ecb": "ECB", "dax": "DAX", "ea": "EA", "ea20": "EA20",
    "hicp": "HICP", "dfr": "DFR", "qe": "QE", "irf": "IRF", "lp": "LP",
    "gfc": "GFC", "bls": "BLS", "mir": "MIR", "svar": "SVAR", "var": "VAR",
    "hac": "HAC", "covid": "COVID",
}


def pretty_label(text: str) -> str:
    """Turn a raw identifier into thesis-consistent label text.

    Underscores become spaces, the pathway connector reads as words, and known
    abbreviations keep the capitalisation used in the List of Abbreviations.
    Everything else stays lower case, matching the response labels already
    carried in the canonical CSVs.
    """
    cleaned = str(text).replace("_to_", " to ").replace("_", " ").strip()
    return " ".join(_ABBREV.get(word.lower(), word) for word in cleaned.split())


def horizon_pair(upstream, downstream) -> str:
    """Format an upstream/downstream horizon pair as the thesis writes it."""
    def one(value) -> str:
        try:
            return f"h{int(float(value))}"
        except (TypeError, ValueError):
            return str(value)
    return f"{one(upstream)} → {one(downstream)}"


def save(fig, path: Path, *, also_pdf: bool = True) -> list[Path]:
    """Write the raster the pipeline contract expects plus a vector twin.

    The PNG keeps the existing filename and satisfies the figure contract in the
    audit script and the notebook figure registry. The PDF is what LaTeX
    includes, so the printed thesis is vector throughout.
    """
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    written = [path]
    fig.savefig(path, dpi=DPI_RASTER)
    if also_pdf:
        pdf_path = path.with_suffix(".pdf")
        fig.savefig(pdf_path)
        written.append(pdf_path)
    plt.close(fig)
    return written


def panel(width: float = FIG_WIDTH, ratio: float = GOLDEN):
    """Single panel with the house proportions.

    Width is forced to FIG_WIDTH so every figure scales identically in LaTeX.
    Constrained layout fits axis labels and the outside legend inside that fixed
    canvas instead of letting the canvas grow.
    """
    fig, ax = plt.subplots(figsize=(FIG_WIDTH, FIG_WIDTH * ratio),
                           layout="constrained")
    fig.get_layout_engine().set(w_pad=0.02, h_pad=0.02,
                                wspace=0.02, hspace=0.02)
    hgrid(ax)
    tidy(ax)
    return fig, ax
