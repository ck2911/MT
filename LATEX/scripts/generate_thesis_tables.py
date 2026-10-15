#!/usr/bin/env python3
"""Generate thesis-facing LaTeX tables from the canonical pipeline outputs.

Presentation only. No estimation happens here. Every number written by this
script is read directly from results/final/ so the thesis tables stay traceable
to the repository. Output goes to LATEX/tables/gen_*.tex.
"""

from __future__ import annotations

import csv
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
FINAL = ROOT / "results" / "final"
OUT = ROOT / "LATEX" / "tables"
OUT.mkdir(parents=True, exist_ok=True)

HORIZONS = ["0", "1", "3", "6", "12", "24"]
SHOCK = "target_factor_monthly_easing"


def read(path: Path) -> list[dict]:
    with path.open(newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def num(value: str | None) -> float | None:
    if value is None or value == "":
        return None
    try:
        return float(value)
    except ValueError:
        return None


def fmt(value: str | None, digits: int = 3) -> str:
    parsed = num(value)
    if parsed is None:
        return "--"
    return f"{parsed:.{digits}f}"


def stars(p_value: str | None) -> str:
    parsed = num(p_value)
    if parsed is None:
        return ""
    if parsed < 0.01:
        return r"\sym{***}"
    if parsed < 0.05:
        return r"\sym{**}"
    if parsed < 0.10:
        return r"\sym{*}"
    return ""


def tex_escape(text: str) -> str:
    out = text.replace("&", r"\&").replace("%", r"\%").replace("_", r"\_")
    return out.replace("#", r"\#")


def write_table(name: str, body: str) -> None:
    (OUT / name).write_text(body, encoding="utf-8")
    print(f"wrote {name}")


# ------------------------------------------------------------- siunitx helpers
def snum(text: str, suffix: str = "") -> str:
    """Wrap a formatted numeric cell for an ``S`` column.

    ``fmt``/``stars``/raw CSV lookups fall back to the literal string ``"--"``
    when a value is missing. An ``S`` column cannot parse that as a number, so
    it is braced to be typeset as inert text instead. Any other value is left
    exactly as formatted (siunitx aligns on the decimal point and appends
    trailing markers such as significance stars on its own).
    """
    if text == "--":
        return "{--}"
    return text + suffix


def s_cols(n: int, table_format: str, space_text_post: str = "") -> str:
    """``n`` repeated siunitx ``S`` columns sharing one ``table-format``.

    ``space_text_post`` reserves room after the number for the widest trailing
    marker (significance stars, a dagger) via siunitx's own
    ``table-space-text-post`` key, so the marker cannot push the column past
    the width ``table-format`` reserves and force an overfull line.
    """
    opts = f"table-format={table_format}"
    if space_text_post:
        opts += f", table-space-text-post={{{space_text_post}}}"
    return " ".join(f"S[{opts}]" for _ in range(n))


def horizon_header(horizons: list[str], first_col: int = 2, label: str = "Response") -> list[str]:
    """A two-row header for tables whose columns are a horizon grid.

    Produces a ``\\cmidrule``-spanned "Horizon in months" group header over
    the horizon columns, with the individual horizon values as a plain
    numeric sub-header, in place of bare ``h0``, ``h1``, ... column labels.
    """
    last_col = first_col + len(horizons) - 1
    sub = " & ".join(f"\\multicolumn{{1}}{{c}}{{{h}}}" for h in horizons)
    return [
        r"    & \multicolumn{" + str(len(horizons)) + r"}{c}{Horizon in months} \\",
        r"    \cmidrule(lr){" + str(first_col) + "-" + str(last_col) + "}",
        f"    {label} & " + sub + r" \\",
    ]


# The ten canonical comparison responses, ordered along the transmission chain
# used throughout the thesis: housing credit, intermediation, market and
# liquidity, then the compensation-linked block.
CANONICAL_ORDER = [
    "ecb_house_purchase_growth_yoy",
    "ln_ecb_house_purchase_pure_new_loans",
    "ecb_mir_mortgage_lending_spread_dfr",
    "ecb_mir_nfc_lending_spread_dfr",
    "ln_nfc_loans_ea_stock",
    "ln_dax_real_de",
    "ln_ecb_assets_ea_stock",
    "ecb_wage_tracker_ex_oneoffs_real_yoy",
    "eurostat_sts_industry_wage_bill_de_real_yoy",
    "eurostat_ecfin_eei_ea20",
]


def canonical_responses() -> list[tuple[str, str]]:
    """Ordered (response, label) pairs for the canonical comparison set."""
    labels: dict[str, str] = {}
    for name in ("tables/cumulative_persistence_table.csv",
                 "tables/normalized_irf_outputs.csv"):
        for row in read(FINAL / name):
            labels.setdefault(row["response"], row.get("response_label") or row["response"])
    return [(r, labels.get(r, r.replace("_", " "))) for r in CANONICAL_ORDER]


def horizons_in(path: Path) -> list[str]:
    """Horizons actually present in an artifact, in ascending order."""
    found = {row["horizon_months"] for row in read(path) if row.get("horizon_months")}
    return sorted(found, key=lambda h: int(float(h)))


# ---------------------------------------------------------------- baseline IRFs
def baseline_irfs() -> None:
    rows = [r for r in read(FINAL / "tables" / "normalized_irf_outputs.csv")
            if r["shock"] == SHOCK and r.get("sample_name", "full") == "full"]
    grid: dict[tuple[str, str], dict] = {}
    for row in rows:
        grid[(row["response"], row["horizon_months"])] = row

    lines = [
        r"\begin{table}[htbp]",
        r"  \centering",
        r"  \caption{Baseline monthly impulse responses to a one-standard-deviation ECB easing surprise}",
        r"  \label{tab:normalized-irf-output}",
        r"  \footnotesize",
        r"  \setstretch{1.0}",
        r"  \setlength{\tabcolsep}{4pt}",
        r"  \begin{tabular}{@{}l "
        + s_cols(len(HORIZONS), "-1.3", space_text_post=r"\sym{***}")
        + r"@{}}",
        r"    \toprule",
    ] + horizon_header(HORIZONS) + [
        r"    \midrule",
    ]
    for response, label in canonical_responses():
        coefs, errs = [], []
        for h in HORIZONS:
            row = grid.get((response, h))
            if row is None:
                coefs.append("{--}")
                errs.append("")
                continue
            coefs.append(snum(fmt(row.get("coefficient")), stars(row.get("p_value"))))
            errs.append("{(" + fmt(row.get('std_error_hac')) + ")}")
        lines.append(f"    {tex_escape(label)} & " + " & ".join(coefs) + r" \\")
        lines.append(r"     & " + " & ".join(errs) + r" \\[0.3em]")
    lines += [
        r"    \bottomrule",
        r"  \end{tabular}",
        r"  \vspace{0.3em}",
        r"  \begin{minipage}{\textwidth}\footnotesize\setstretch{1.0}",
        r"  Notes: Local-projection coefficients scaled to a one-standard-deviation easing",
        r"  surprise. HAC (Newey--West) standard errors in parentheses.",
        r"  \sym{*}~$p<0.10$, \sym{**}~$p<0.05$, \sym{***}~$p<0.01$.",
        r"  Source: own calculations.",
        r"  \end{minipage}",
        r"\end{table}",
    ]
    write_table("gen_baseline_irfs.tex", "\n".join(lines) + "\n")


# ------------------------------------------------------- cumulative persistence
def cumulative_persistence() -> None:
    source = FINAL / "tables" / "cumulative_persistence_table.csv"
    rows = read(source)
    grid = {(r["response"], r["horizon_months"]): r for r in rows}
    hz = horizons_in(source)

    lines = [
        r"\begin{table}[htbp]",
        r"  \centering",
        r"  \caption{Accumulated responses at the medium and long horizons}",
        r"  \label{tab:cumulative-persistence}",
        r"  \footnotesize",
        r"  \setstretch{1.0}",
        r"  \setlength{\tabcolsep}{5pt}",
        r"  \begin{tabular}{@{}l "
        + s_cols(len(hz), "-1.3", space_text_post=r"$^{\dagger}$")
        + r"@{}}",
        r"    \toprule",
    ] + horizon_header(hz) + [
        r"    \midrule",
    ]
    for response, label in canonical_responses():
        cells = []
        for h in hz:
            row = grid.get((response, h))
            if row is None:
                cells.append("{--}")
                continue
            marker = ""
            flag = str(row.get("ci_90_excludes_zero", "")).strip().lower()
            if flag in {"true", "1", "yes"}:
                marker = r"$^{\dagger}$"
            cells.append(snum(fmt(row.get("cumulative_response")), marker))
        lines.append(f"    {tex_escape(label)} & " + " & ".join(cells) + r" \\")
    lines += [
        r"    \bottomrule",
        r"  \end{tabular}",
        r"  \vspace{0.3em}",
        r"  \begin{minipage}{\textwidth}\footnotesize\setstretch{1.0}",
        r"  Notes: Running sum of the normalized impulse responses through each horizon.",
        r"  Intervals combine the horizon-level HAC standard errors under an independence",
        r"  approximation across horizons. $^{\dagger}$ marks accumulated responses whose 90 percent",
        r"  HAC interval excludes zero. \Cref{tab:bootstrap-cumulative} reports the dependence-aware",
        r"  bootstrap intervals for the same accumulated responses.",
        r"  Source: own calculations.",
        r"  \end{minipage}",
        r"\end{table}",
    ]
    write_table("gen_cumulative_persistence.tex", "\n".join(lines) + "\n")


# ------------------------------------------- bootstrap cumulative intervals
def bootstrap_cumulative() -> None:
    """Accumulated responses with 90 percent intervals from the joint bootstraps.

    Source: results/final/uncertainty/dependence_aware_cumulative_intervals.csv,
    target shock only. One row per response and bootstrap method, one column
    per reported horizon, each cell an interval; a dagger marks exclusion of zero.
    """
    rows = [r for r in read(FINAL / "uncertainty" / "dependence_aware_cumulative_intervals.csv")
            if r.get("shock") == SHOCK]
    grid = {(r["response"], r["source_method"], r["horizon_months"]): r for r in rows}
    hz = [h for h in ("6", "12", "24")
          if any(k[2] == h for k in grid)]
    methods = (("moving_block", "moving block"), ("wild", "wild"))

    def interval(row: dict | None) -> str:
        if row is None:
            return "--"
        low = num(row.get("cumulative_ci_90_low"))
        high = num(row.get("cumulative_ci_90_high"))
        if low is None or high is None:
            return "--"
        marker = r"$^{\dagger}$" if (low > 0 or high < 0) else ""
        return f"[{low:.3f}, {high:.3f}]{marker}"

    lines = [
        r"\begin{table}[htbp]",
        r"  \centering",
        r"  \caption{Accumulated responses: 90 percent intervals from the dependence-aware bootstraps}",
        r"  \label{tab:bootstrap-cumulative}",
        r"  \footnotesize",
        r"  \setstretch{1.0}",
        r"  \setlength{\tabcolsep}{4pt}",
        r"  \begin{tabular}{@{}ll" + "c" * len(hz) + r"@{}}",
        r"    \toprule",
        r"    & & \multicolumn{" + str(len(hz)) + r"}{c}{Horizon in months} \\",
        r"    \cmidrule(lr){3-" + str(2 + len(hz)) + "}",
        r"    Response & Bootstrap & " + " & ".join(hz) + r" \\",
        r"    \midrule",
    ]
    for response, label in canonical_responses():
        for i, (method, method_label) in enumerate(methods):
            cells = [interval(grid.get((response, method, h))) for h in hz]
            name = tex_escape(label) if i == 0 else ""
            tail = r" \\" if i < len(methods) - 1 else r" \\[0.3em]"
            lines.append(f"    {name} & {method_label} & " + " & ".join(cells) + tail)
    lines += [
        r"    \bottomrule",
        r"  \end{tabular}",
        r"  \vspace{0.3em}",
        r"  \begin{minipage}{\textwidth}\footnotesize\setstretch{1.0}",
        r"  Notes: Percentile intervals for the running sum of the normalized responses to the",
        r"  target easing surprise from 399 joint replications that resample the residuals of all",
        r"  six horizons together, in moving blocks of twelve months or with wild sign flips.",
        r"  $^{\dagger}$ marks intervals that exclude zero. Compare with the HAC intervals under",
        r"  the independence approximation in \Cref{tab:cumulative-persistence}.",
        r"  Source: own calculations.",
        r"  \end{minipage}",
        r"\end{table}",
    ]
    write_table("gen_bootstrap_cumulative.tex", "\n".join(lines) + "\n")


# ------------------------------------------------------------- peak  responses
def peak_responses() -> None:
    rows = {r["response"]: r for r in read(FINAL / "tables" / "peak_response_table.csv")}
    lines = [
        r"\begin{table}[htbp]",
        r"  \centering",
        r"  \caption{Peak response magnitude and timing}",
        r"  \label{tab:peak-response}",
        r"  \footnotesize",
        r"  \setstretch{1.0}",
        r"  \setlength{\tabcolsep}{4pt}",
        r"  \begin{tabular}{@{}l"
        r" S[table-format=2.0]"
        r" S[table-format=-1.3]"
        r" @{\hspace{0.4em}[}S[table-format=-1.3]"
        r"@{,\ }S[table-format=-1.3]@{]\hspace{0.4em}}"
        r" S[table-format=1.3]"
        r" S[table-format=3.0]@{}}",
        r"    \toprule",
        r"    Response & \multicolumn{1}{c}{Peak $h$} & \multicolumn{1}{c}{Peak} & "
        r"\multicolumn{2}{c}{90\% interval} & \multicolumn{1}{c}{$p$} & \multicolumn{1}{c}{$N$} \\",
        r"    \cmidrule(lr){4-5}",
        r"    \midrule",
    ]
    for response, label in canonical_responses():
        row = rows.get(response)
        if row is None:
            continue
        lines.append(
            f"    {tex_escape(label)} & {snum(str(row.get('peak_horizon_months','--')))} & "
            f"{snum(fmt(row.get('peak_response')))} & "
            f"{snum(fmt(row.get('ci_90_low')))} & {snum(fmt(row.get('ci_90_high')))} & "
            f"{snum(fmt(row.get('p_value')))} & {snum(str(row.get('nobs','--')))} \\\\"
        )
    lines += [
        r"    \bottomrule",
        r"  \end{tabular}",
        r"  \vspace{0.3em}",
        r"  \begin{minipage}{\textwidth}\footnotesize\setstretch{1.0}",
        r"  Notes: Largest absolute normalized response across the reported horizons, with",
        r"  its HAC 90 percent interval and estimation sample size.",
        r"  Source: own calculations.",
        r"  \end{minipage}",
        r"\end{table}",
    ]
    write_table("gen_peak_responses.tex", "\n".join(lines) + "\n")


# ------------------------------------------------------- monthly first stage
def first_stage() -> None:
    path = FINAL / "diagnostics" / "monthly_first_stage_tournament.csv"
    rows = read(path)
    for row in rows:
        row["_f"] = num(row.get("first_stage_f_stat")) or 0.0
    rows.sort(key=lambda r: r["_f"], reverse=True)
    top = rows[:8]

    lines = [
        r"\begin{table}[htbp]",
        r"  \centering",
        r"  \caption{Monthly first-stage relevance of the strongest candidate policy bridges}",
        r"  \label{tab:instrument-strength-matrix}",
        r"  \footnotesize",
        r"  \setstretch{1.0}",
        r"  \setlength{\tabcolsep}{5pt}",
        r"  \begin{tabular}{@{}ll"
        r" S[table-format=2.2]"
        r" S[table-format=1.3]"
        r" S[table-format=3.0]"
        r" l@{}}",
        r"    \toprule",
        r"    Surprise factor & Policy target & \multicolumn{1}{c}{$F$} & "
        r"\multicolumn{1}{c}{Partial $R^2$} & \multicolumn{1}{c}{$N$} & Screen \\",
        r"    \midrule",
    ]
    for row in top:
        verdict = (row.get("final_screen") or "").replace("_", " ")
        factor = (row.get("instrument") or "").replace("_monthly_easing", "").replace("_", " ")
        target = row.get("target_label") or (row.get("target") or "").replace("_", " ")
        lines.append(
            f"    {tex_escape(factor)} & "
            f"{tex_escape(target)} & "
            f"{snum(fmt(row.get('first_stage_f_stat'), 2))} & "
            f"{snum(fmt(row.get('partial_r_squared')))} & "
            f"{snum(str(row.get('observations','--')))} & {tex_escape(verdict)} \\\\"
        )
    lines += [
        r"    \bottomrule",
        r"  \end{tabular}",
        r"  \vspace{0.3em}",
        r"  \begin{minipage}{\textwidth}\footnotesize\setstretch{1.0}",
        r"  Notes: Eight strongest bridges from the monthly first-stage tournament, ranked by",
        r"  $F$-statistic. No candidate clears the strength and stability screen jointly, which",
        r"  is why the thesis reports reduced-form responses to policy news.",
        r"  Source: own calculations.",
        r"  \end{minipage}",
        r"\end{table}",
    ]
    write_table("gen_first_stage.tex", "\n".join(lines) + "\n")


# ----------------------------------------------------- information-effect screen
def information_screen() -> None:
    rows = read(FINAL / "diagnostics" / "information_effect_summary.csv")
    lines = [
        r"\begin{table}[htbp]",
        r"  \centering",
        r"  \caption{Information-effect classification of ECB announcement events}",
        r"  \label{tab:information-effect-screen}",
        r"  \footnotesize",
        r"  \setstretch{1.0}",
        r"  \setlength{\tabcolsep}{6pt}",
        r"  \begin{tabular}{@{}l S[table-format=3.0] S[table-format=3.1]@{}}",
        r"    \toprule",
        r"    Event classification & \multicolumn{1}{c}{Events} & \multicolumn{1}{c}{Share (\%)} \\",
        r"    \midrule",
    ]
    total = 0
    for row in rows:
        label = (row.get("information_effect_screen") or "").replace("_", " ")
        count = row.get("event_count", "--")
        share = num(row.get("share"))
        share_txt = f"{share * 100:.1f}" if share is not None else "--"
        try:
            total += int(count)
        except (TypeError, ValueError):
            pass
        lines.append(f"    {tex_escape(label)} & {snum(str(count))} & {snum(share_txt)} \\\\")
    lines += [
        r"    \midrule",
        f"    Total & {total} & 100.0 \\\\",
        r"    \bottomrule",
        r"  \end{tabular}",
        r"  \vspace{0.3em}",
        r"  \begin{minipage}{\textwidth}\footnotesize\setstretch{1.0}",
        r"  Notes: Events are classified by comparing the sign of the rate factor with the",
        r"  yield and equity responses in the announcement window. Counts cover the full",
        r"  event archive.",
        r"  Source: own calculations.",
        r"  \end{minipage}",
        r"\end{table}",
    ]
    write_table("gen_information_screen.tex", "\n".join(lines) + "\n")


# --------------------------------------------------------- sequential  timing
def sequential_timing() -> None:
    rows = read(FINAL / "mechanism" / "sequential_timing_outputs.csv")
    lines = [
        r"\begin{table}[htbp]",
        r"  \centering",
        r"  \caption{Ordered timing associations along the intermediation chain}",
        r"  \label{tab:sequential-transmission}",
        r"  \footnotesize",
        r"  \setstretch{1.0}",
        r"  \setlength{\tabcolsep}{5pt}",
        r"  \begin{tabular}{@{}ll"
        r" S[table-format=1.0]"
        r" S[table-format=1.0]"
        r" S[table-format=-2.3]"
        r" S[table-format=1.3]@{}}",
        r"    \toprule",
        r"    Upstream & Downstream & \multicolumn{1}{c}{$h_u$} & \multicolumn{1}{c}{$h_d$} & "
        r"\multicolumn{1}{c}{$\lambda$} & \multicolumn{1}{c}{$p$} \\",
        r"    \midrule",
    ]
    for row in rows:
        lines.append(
            f"    {tex_escape(row.get('upstream_label',''))} & "
            f"{tex_escape(row.get('downstream_label',''))} & "
            f"{snum(str(row.get('upstream_horizon_months','--')))} & "
            f"{snum(str(row.get('downstream_horizon_months','--')))} & "
            f"{snum(fmt(row.get('upstream_to_downstream_conditional_coef')))} & "
            f"{snum(fmt(row.get('upstream_to_downstream_conditional_p')))} \\\\"
        )
    lines += [
        r"    \bottomrule",
        r"  \end{tabular}",
        r"  \vspace{0.3em}",
        r"  \begin{minipage}{\textwidth}\footnotesize\setstretch{1.0}",
        r"  Notes: $\lambda$ is the association between an earlier upstream movement and a",
        r"  later downstream movement, holding the policy-news shock fixed. This is ordered",
        r"  timing evidence and not structural mediation.",
        r"  Source: own calculations.",
        r"  \end{minipage}",
        r"\end{table}",
    ]
    write_table("gen_sequential_timing.tex", "\n".join(lines) + "\n")


# ------------------------------------------------------- bootstrap sensitivity
def bootstrap_sensitivity() -> None:
    rows = read(FINAL / "uncertainty" / "bootstrap_sensitivity_summary.csv")
    grid = {(r["response"], r["horizon_months"]): r for r in rows}
    lines = [
        r"\begin{table}[htbp]",
        r"  \centering",
        r"  \caption{Bootstrap interval width relative to the wild bootstrap}",
        r"  \label{tab:bootstrap-sensitivity}",
        r"  \footnotesize",
        r"  \setstretch{1.0}",
        r"  \setlength{\tabcolsep}{4pt}",
        r"  \begin{tabular}{@{}l " + s_cols(len(HORIZONS), "1.2") + r"@{}}",
        r"    \toprule",
    ] + horizon_header(HORIZONS) + [
        r"    \midrule",
    ]
    for response, label in canonical_responses():
        cells = []
        for h in HORIZONS:
            row = grid.get((response, h))
            cells.append("{--}" if row is None else fmt(row.get("width_ratio_mbb_to_wild"), 2))
        lines.append(f"    {tex_escape(label)} & " + " & ".join(cells) + r" \\")
    lines += [
        r"    \bottomrule",
        r"  \end{tabular}",
        r"  \vspace{0.3em}",
        r"  \begin{minipage}{\textwidth}\footnotesize\setstretch{1.0}",
        r"  Notes: Ratio of the moving-block to the wild bootstrap 90 percent interval width.",
        r"  Values above one indicate that the dependence-aware moving-block interval is the",
        r"  more conservative of the two.",
        r"  Source: own calculations.",
        r"  \end{minipage}",
        r"\end{table}",
    ]
    write_table("gen_bootstrap_sensitivity.tex", "\n".join(lines) + "\n")


# -------------------------------------------------- descriptives + correlations
DATA = ROOT / "data" / "processed" / "eu_de" / "final_monthly_model_dataset.csv"
SHOCK_LABEL = "ECB easing surprise"


def stat_variables() -> list[tuple[str, str]]:
    """Shock plus the ten canonical responses, with display labels."""
    return [(SHOCK, SHOCK_LABEL)] + canonical_responses()


CONTROL_VARIABLES = [
    ("inflation_ea20_yoy_pct", "EA20 annual HICP inflation"),
    ("dfr_mavg", "Deposit facility rate, monthly average"),
]


def load_series(extra: list[tuple[str, str]] | None = None) -> dict[str, list[float | None]]:
    rows = read(DATA)
    wanted = stat_variables() + (extra or [])
    out: dict[str, list[float | None]] = {}
    for name, _ in wanted:
        out[name] = [num(r.get(name)) for r in rows]
    return out


def descriptive_stats() -> None:
    series = load_series(CONTROL_VARIABLES)

    def row_for(name: str, label: str) -> str:
        vals = [v for v in series[name] if v is not None]
        n = len(vals)
        mean = sum(vals) / n
        sd = (sum((v - mean) ** 2 for v in vals) / (n - 1)) ** 0.5
        return (f"    {tex_escape(label)} & {n} & {mean:.3f} & {sd:.3f} & "
                f"{min(vals):.3f} & {max(vals):.3f} \\\\")

    lines = [
        r"\begin{table}[htbp]",
        r"  \centering",
        r"  \caption{Descriptive statistics for the shock and the canonical response variables}",
        r"  \label{tab:descriptive-stats}",
        r"  \footnotesize",
        r"  \setstretch{1.0}",
        r"  \setlength{\tabcolsep}{5pt}",
        r"  \begin{tabular}{@{}l"
        r" S[table-format=3.0]"
        r" S[table-format=-3.3]"
        r" S[table-format=2.3]"
        r" S[table-format=-3.3]"
        r" S[table-format=-3.3]@{}}",
        r"    \toprule",
        r"    Variable & \multicolumn{1}{c}{$N$} & \multicolumn{1}{c}{Mean} & \multicolumn{1}{c}{SD} & "
        r"\multicolumn{1}{c}{Min} & \multicolumn{1}{c}{Max} \\",
        r"    \midrule",
    ]
    lines.append(r"    \multicolumn{6}{@{}l}{\emph{Shock and response variables}} \\")
    for name, label in stat_variables():
        lines.append(row_for(name, label))
    lines.append(r"    \midrule")
    lines.append(r"    \multicolumn{6}{@{}l}{\emph{Control variables}} \\")
    for name, label in CONTROL_VARIABLES:
        lines.append(row_for(name, label))
    lines += [
        r"    \bottomrule",
        r"  \end{tabular}",
        r"  \vspace{0.3em}",
        r"  \begin{minipage}{\textwidth}\footnotesize\setstretch{1.0}",
        r"  Notes: Monthly observations, January 2005 through October 2025. Units follow the",
        r"  variable definitions in this chapter. Sample sizes differ because the pure-new-loan,",
        r"  wage-tracker, and wage-bill series start later than the panel. The local projections",
        r"  also control for two lags of the response variable itself.",
        r"  Source: own calculations.",
        r"  \end{minipage}",
        r"\end{table}",
    ]
    write_table("gen_descriptive_stats.tex", "\n".join(lines) + "\n")


def correlations() -> None:
    from math import erfc, sqrt

    series = load_series()
    names = [n for n, _ in stat_variables()]
    labels = {n: l for n, l in stat_variables()}

    def corr(a: str, b: str) -> tuple[float, int] | None:
        pairs = [(x, y) for x, y in zip(series[a], series[b])
                 if x is not None and y is not None]
        n = len(pairs)
        if n < 3:
            return None
        xs, ys = [p[0] for p in pairs], [p[1] for p in pairs]
        mx, my = sum(xs) / n, sum(ys) / n
        sxy = sum((x - mx) * (y - my) for x, y in pairs)
        sxx = sum((x - mx) ** 2 for x in xs)
        syy = sum((y - my) ** 2 for y in ys)
        if sxx == 0 or syy == 0:
            return None
        return sxy / sqrt(sxx * syy), n

    def cell(a: str, b: str) -> str:
        result = corr(a, b)
        if result is None:
            return "--"
        r, n = result
        if abs(r) >= 1.0:
            return f"{r:.2f}"
        t = abs(r) * sqrt((n - 2) / (1 - r * r))
        p = erfc(t / sqrt(2.0))
        return f"{r:.2f}" + (r"\sym{*}" if p < 0.05 else "")

    k = len(names)
    head = " & ".join(f"\\multicolumn{{1}}{{c}}{{({i + 1})}}" for i in range(k - 1))
    lines = [
        r"\begin{table}[htbp]",
        r"  \centering",
        r"  \caption{Pairwise correlations among the shock and the canonical response variables}",
        r"  \label{tab:correlations}",
        r"  \scriptsize",
        r"  \setstretch{1.0}",
        r"  \setlength{\tabcolsep}{3pt}",
        r"  \begin{tabular}{@{}l"
        + " "
        + s_cols(k - 1, "-1.2", space_text_post=r"\sym{*}")
        + r"@{}}",
        r"    \toprule",
        r"    Variable & " + head + r" \\",
        r"    \midrule",
    ]
    for i, name in enumerate(names):
        cells = [snum(cell(name, names[j])) if j < i else "" for j in range(k - 1)]
        lines.append(
            f"    ({i + 1}) {tex_escape(labels[name])} & " + " & ".join(cells) + r" \\"
        )
    lines += [
        r"    \bottomrule",
        r"  \end{tabular}",
        r"  \vspace{0.3em}",
        r"  \begin{minipage}{\textwidth}\footnotesize\setstretch{1.0}",
        r"  Notes: Pearson correlations on pairwise complete monthly observations.",
        r"  \sym{*}~$p<0.05$. Sample sizes vary across pairs because several series start",
        r"  later than the panel.",
        r"  Source: own calculations.",
        r"  \end{minipage}",
        r"\end{table}",
    ]
    write_table("gen_correlations.tex", "\n".join(lines) + "\n")


# ------------------------------------------------------- residual diagnostics
def residual_diagnostics() -> None:
    """Horizons at which each residual test rejects at 5 percent, per response."""
    rows = read(FINAL / "uncertainty" / "residual_diagnostics.csv")
    by: dict[str, list[dict]] = {}
    for row in rows:
        by.setdefault(row["response"], []).append(row)

    def rejecting(group: list[dict], column: str) -> str:
        ordered = sorted(group, key=lambda r: int(r["horizon_months"]))
        hs = [r["horizon_months"] for r in ordered if num(r[column]) is not None and num(r[column]) < 0.05]
        if len(hs) == len(ordered):
            return "all"
        return ", ".join(hs) if hs else "none"

    lines = [
        r"\begin{table}[htbp]",
        r"  \centering",
        r"  \caption{Residual diagnostics for the baseline local projections}",
        r"  \label{tab:residual-diagnostics}",
        r"  \footnotesize",
        r"  \setstretch{1.0}",
        r"  \setlength{\tabcolsep}{4pt}",
        r"  \begin{tabular}{@{}l r l l l l@{}}",
        r"    \toprule",
        r"    & & \multicolumn{4}{c}{Horizons (months) at which the test rejects at 5 percent} \\",
        r"    \cmidrule(lr){3-6}",
        r"    Response & \multicolumn{1}{c}{$N$} & Serial corr. & Heterosk. & ARCH & Non-normal \\",
        r"    \midrule",
    ]
    for response, label in canonical_responses():
        group = by.get(response, [])
        if not group:
            continue
        n0 = sorted(group, key=lambda r: int(r["horizon_months"]))[0]["nobs"]
        lines.append(
            f"    {tex_escape(label)} & {n0} & {rejecting(group, 'lb_beyond_bandwidth_p')} & "
            f"{rejecting(group, 'koenker_bp_p')} & {rejecting(group, 'arch_lm_12_p')} & {rejecting(group, 'jarque_bera_p')} \\\\"
        )
    lines += [
        r"    \bottomrule",
        r"  \end{tabular}",
        r"  \vspace{0.3em}",
        r"  \begin{minipage}{\textwidth}\footnotesize\setstretch{1.0}",
        r"  Notes: Baseline target-shock regressions, full sample. $N$ is the estimation sample at $h=0$.",
        r"  Serial corr.: Ljung--Box test on the twelve residual autocorrelations at lags $h+2$ to $h+13$,",
        r"  just beyond the Newey--West bandwidth $h+1$. Heterosk.: Koenker's studentized Breusch--Pagan",
        r"  test of the squared residuals on the regressors. ARCH: Engle's LM test with twelve lags.",
        r"  Non-normal: Jarque--Bera. ``all'' means every one of the six horizons. Source: own calculations.",
        r"  \end{minipage}",
        r"\end{table}",
    ]
    write_table("gen_residual_diagnostics.tex", "\n".join(lines) + "\n")


if __name__ == "__main__":
    baseline_irfs()
    cumulative_persistence()
    peak_responses()
    first_stage()
    information_screen()
    sequential_timing()
    bootstrap_sensitivity()
    bootstrap_cumulative()
    descriptive_stats()
    correlations()
    residual_diagnostics()
    print("done")
