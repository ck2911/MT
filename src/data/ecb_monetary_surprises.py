from __future__ import annotations

import argparse
import hashlib
import math
import os
import tempfile
import re
import urllib.request
import zipfile
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Iterable
from xml.etree import ElementTree as ET

ROOT = Path(__file__).resolve().parents[2]
os.environ.setdefault("MPLCONFIGDIR", str(Path(tempfile.gettempdir()) / "thesis_model_mpl_cache"))

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import statsmodels.api as sm
from scipy import stats


RAW_DIR = ROOT / "data" / "raw" / "eu_de" / "ecb_monetary_surprises"
PROCESSED_DIR = ROOT / "data" / "processed" / "eu_de"
DIAGNOSTICS_ROOT = ROOT / "results" / "diagnostics"
RESULTS_DIR = DIAGNOSTICS_ROOT / "ecb_monetary_surprises"
FIG_DIR = RESULTS_DIR / "figures"
DOCS_DIR = ROOT / "results" / "final" / "memos"  # working notes; docs/ holds only the curated notes
CANONICAL_DATASET = PROCESSED_DIR / "final_quarterly_model_dataset.csv"

CURRENT_FACTOR_VINTAGE = "2025-10-30"
AUDIT_DATE = "2026-05-15"

SOURCE_URLS = {
    "ea_mpd_workbook": "https://www.ecb.europa.eu/pub/pdf/annex/Dataset_EA-MPD.xlsx",
    "abgmr_factor_page": "https://gragusa.org/factors/",
    "press_release_factors": f"https://gragusa.org/factors/data/press_release_factors_{CURRENT_FACTOR_VINTAGE}.csv",
    "press_conference_factors": f"https://gragusa.org/factors/data/press_conference_factors_{CURRENT_FACTOR_VINTAGE}.csv",
    "all_vintages_zip": "https://gragusa.org/factors/factors.zip",
}

FACTOR_COLUMNS = ["timing_factor", "target_factor", "fg_factor", "qe_factor"]
FACTOR_LABELS = {
    "timing_factor": "timing",
    "target_factor": "target",
    "fg_factor": "fg",
    "qe_factor": "qe",
}
DIRECT_AGGREGATIONS = ["quarterly_sum", "quarterly_mean", "quarterly_abs_sum", "quarterly_signed_cumulative"]
MONTHLY_BRIDGE_AGGREGATIONS = ["monthly_sum", "monthly_mean", "monthly_abs_sum"]
AGGREGATIONS = DIRECT_AGGREGATIONS
REQUIRED_FIRST_STAGE_TARGETS = [
    "d_wx_shadow_rate",
    "d_dfr_eop",
    "d_ln_ecb_assets_ea_stock",
    "d_ecb_assets_ea_qavg",
    "d_ln_hh_loans_ea_stock",
    "d_ln_nfc_loans_ea_stock",
    "d_ln_house_price_de_real",
]
OPTIONAL_FIRST_STAGE_SOURCE_COLUMNS = ["financial_conditions_index", "credit_spread_proxy", "term_spread"]
POLICY_TARGETS = REQUIRED_FIRST_STAGE_TARGETS
OFFICIAL_LPIV_BASELINE_INSTRUMENT = "target_factor_market_magnitude_weighted_quarterly_sum"

REGIME_WINDOWS = {
    "pre_qe": ("2005Q1", "2014Q1"),
    "qe_era": ("2014Q2", "2019Q4"),
    "covid": ("2020Q1", "2021Q4"),
    "tightening": ("2022Q1", "2025Q4"),
}

XLSX_NS = {"a": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
REL_NS = {"r": "http://schemas.openxmlformats.org/package/2006/relationships"}


@dataclass(frozen=True)
class FactorSources:
    press_release_path: Path
    press_conference_path: Path
    workbook_path: Path | None
    press_release_vintage: str
    press_conference_vintage: str
    workbook_vintage: str


def ensure_directories() -> None:
    for directory in (RAW_DIR, PROCESSED_DIR, DIAGNOSTICS_ROOT, RESULTS_DIR, FIG_DIR, DOCS_DIR):
        directory.mkdir(parents=True, exist_ok=True)


def sha256_file(path: Path) -> str:
    hasher = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


def safe_download(url: str, destination: Path) -> Path:
    """Download a raw source file without overwriting an existing file."""

    destination.parent.mkdir(parents=True, exist_ok=True)
    if destination.exists():
        return destination
    tmp = destination.with_suffix(destination.suffix + ".tmp")
    urllib.request.urlretrieve(url, tmp)  # noqa: S310 - user-controlled thesis source URLs are explicit constants.
    tmp.replace(destination)
    return destination


def maybe_download_sources() -> None:
    retrieval_stamp = date.today().isoformat()
    safe_download(SOURCE_URLS["ea_mpd_workbook"], RAW_DIR / f"Dataset_EA-MPD_{retrieval_stamp}.xlsx")
    safe_download(
        SOURCE_URLS["press_release_factors"],
        RAW_DIR / f"press_release_factors_{CURRENT_FACTOR_VINTAGE}.csv",
    )
    safe_download(
        SOURCE_URLS["press_conference_factors"],
        RAW_DIR / f"press_conference_factors_{CURRENT_FACTOR_VINTAGE}.csv",
    )
    safe_download(SOURCE_URLS["all_vintages_zip"], RAW_DIR / f"gragusa_factors_all_vintages_{retrieval_stamp}.zip")


def latest_matching(pattern: str, required: bool = True) -> Path | None:
    matches = sorted(RAW_DIR.glob(pattern))
    if not matches:
        if required:
            raise FileNotFoundError(f"No raw ECB monetary-surprise file matches {pattern} in {RAW_DIR}")
        return None
    return matches[-1]


def vintage_from_filename(path: Path | None) -> str:
    if path is None:
        return "not_available"
    match = re.search(r"(\d{4}-\d{2}-\d{2})", path.name)
    return match.group(1) if match else "unknown"


def locate_sources() -> FactorSources:
    press_release = latest_matching("press_release_factors_*.csv")
    press_conference = latest_matching("press_conference_factors_*.csv")
    workbook = latest_matching("Dataset_EA-MPD_*.xlsx", required=False)
    return FactorSources(
        press_release_path=press_release,
        press_conference_path=press_conference,
        workbook_path=workbook,
        press_release_vintage=vintage_from_filename(press_release),
        press_conference_vintage=vintage_from_filename(press_conference),
        workbook_vintage=vintage_from_filename(workbook),
    )


def write_raw_readme(sources: FactorSources) -> None:
    lines = [
        "# ECB Monetary Surprise Sources",
        "",
        "This directory stores raw ECB high-frequency monetary-policy surprise sources for the EU/DE thesis.",
        "Raw files are kept unchanged once downloaded.",
        "",
        "## Sources",
        "",
        f"- ECB EA-MPD workbook: {SOURCE_URLS['ea_mpd_workbook']}",
        f"- ABGMR factor page: {SOURCE_URLS['abgmr_factor_page']}",
        f"- Current press-release factor CSV: {SOURCE_URLS['press_release_factors']}",
        f"- Current press-conference factor CSV: {SOURCE_URLS['press_conference_factors']}",
        f"- ABGMR all-vintages ZIP: {SOURCE_URLS['all_vintages_zip']}",
        "",
        "## Working Vintage",
        "",
        f"- Press release factors: `{sources.press_release_path.name}`",
        f"- Press conference factors: `{sources.press_conference_path.name}`",
        f"- EA-MPD workbook: `{sources.workbook_path.name if sources.workbook_path else 'not_available'}`",
        "",
        "## Source Notes",
        "",
        "- The ABGMR factor files split the policy-decision and communication windows: `target` is in the press-release file; `timing`, `fg`, and `qe` are in the press-conference file.",
        "- The ECB EA-MPD workbook is used for event validation and lightweight Jarocinski-Karadi-style sign screening through `OIS_6M` and `STOXX50` in the monetary-event window.",
        "- The thesis shock is the monthly sum of the target factor, sign-flipped so that positive values are easing surprises (`target_factor_monthly_easing`). The other factors and aggregation rules are robustness checks.",
        "",
    ]
    (RAW_DIR / "SOURCES.md").write_text("\n".join(lines), encoding="utf-8")


def write_source_manifest(sources: FactorSources) -> None:
    records = []
    url_by_name = {
        sources.press_release_path.name: SOURCE_URLS["press_release_factors"],
        sources.press_conference_path.name: SOURCE_URLS["press_conference_factors"],
    }
    if sources.workbook_path is not None:
        url_by_name[sources.workbook_path.name] = SOURCE_URLS["ea_mpd_workbook"]
    for zip_path in sorted(RAW_DIR.glob("gragusa_factors_all_vintages_*.zip")):
        url_by_name[zip_path.name] = SOURCE_URLS["all_vintages_zip"]
    for path in sorted(RAW_DIR.iterdir()):
        if not path.is_file() or path.name.startswith("."):
            continue
        if path.name == "source_manifest.csv":
            continue
        records.append(
            {
                "file_name": path.name,
                "path": str(path.relative_to(ROOT)),
                "source_url": url_by_name.get(path.name, ""),
                "source_vintage": vintage_from_filename(path),
                "size_bytes": path.stat().st_size,
                "sha256": sha256_file(path),
                "raw_overwrite_policy": "never overwrite; add a new dated/vintage file instead",
            }
        )
    pd.DataFrame(records).to_csv(RAW_DIR / "source_manifest.csv", index=False)


def load_factor_csv(path: Path, required_columns: Iterable[str]) -> pd.DataFrame:
    data = pd.read_csv(path)
    missing = [column for column in required_columns if column not in data.columns]
    if missing:
        raise KeyError(f"{path.name} is missing required columns: {missing}")
    data["event_date"] = pd.to_datetime(data["date"], errors="coerce")
    malformed = data["event_date"].isna().sum()
    if malformed:
        raise ValueError(f"{path.name} contains {malformed} malformed event dates.")
    data = data.drop(columns=["date"]).sort_values("event_date")
    for column in required_columns:
        if column != "date":
            data[column] = pd.to_numeric(data[column], errors="coerce")
    return data


def load_abgmr_factors(sources: FactorSources) -> pd.DataFrame:
    press_release = load_factor_csv(sources.press_release_path, ["date", "target"])
    press_release = press_release.rename(columns={"target": "target_factor"})
    press_conference = load_factor_csv(sources.press_conference_path, ["date", "timing", "fg", "qe"])
    press_conference = press_conference.rename(
        columns={"timing": "timing_factor", "fg": "fg_factor", "qe": "qe_factor"}
    )
    factors = pd.merge(press_release, press_conference, on="event_date", how="outer", validate="one_to_one")
    factors = factors.sort_values("event_date")
    factors["abgmr_source_vintage"] = (
        f"press_release={sources.press_release_vintage};press_conference={sources.press_conference_vintage}"
    )
    return factors


def _xlsx_shared_strings(zip_handle: zipfile.ZipFile) -> list[str]:
    if "xl/sharedStrings.xml" not in zip_handle.namelist():
        return []
    root = ET.fromstring(zip_handle.read("xl/sharedStrings.xml"))
    strings: list[str] = []
    for item in root.findall("a:si", XLSX_NS):
        strings.append("".join(text.text or "" for text in item.findall(".//a:t", XLSX_NS)))
    return strings


def _xlsx_col_index(cell_ref: str) -> int:
    match = re.match(r"([A-Z]+)", cell_ref)
    if not match:
        return 0
    index = 0
    for char in match.group(1):
        index = index * 26 + ord(char) - 64
    return index - 1


def _parse_excel_date(value: object) -> pd.Timestamp:
    if value is None or value == "":
        return pd.NaT
    try:
        return pd.Timestamp("1899-12-30") + pd.to_timedelta(float(value), unit="D")
    except (TypeError, ValueError):
        return pd.to_datetime(value, dayfirst=True, errors="coerce")


def read_xlsx_sheet(path: Path, sheet_xml: str) -> pd.DataFrame:
    """Read a simple worksheet from xlsx without depending on openpyxl."""

    with zipfile.ZipFile(path) as zip_handle:
        shared_strings = _xlsx_shared_strings(zip_handle)
        root = ET.fromstring(zip_handle.read(sheet_xml))
    rows: list[list[object]] = []
    for row in root.findall(".//a:sheetData/a:row", XLSX_NS):
        values: list[object] = []
        for cell in row.findall("a:c", XLSX_NS):
            index = _xlsx_col_index(cell.attrib.get("r", "A"))
            while len(values) <= index:
                values.append(None)
            value_node = cell.find("a:v", XLSX_NS)
            value: object = None if value_node is None else value_node.text
            if cell.attrib.get("t") == "s" and value is not None:
                value = shared_strings[int(value)]
            values[index] = value
        rows.append(values)
    if not rows:
        return pd.DataFrame()
    max_width = max(len(row) for row in rows)
    rows = [row + [None] * (max_width - len(row)) for row in rows]
    header = [column if column not in (None, "") else f"unnamed_{i}" for i, column in enumerate(rows[0])]
    data = pd.DataFrame(rows[1:], columns=header)
    if "date" in data.columns:
        data["event_date"] = data["date"].map(_parse_excel_date)
        data = data.drop(columns=["date"])
    for column in data.columns:
        if column != "event_date":
            data[column] = pd.to_numeric(data[column], errors="coerce")
    return data.sort_values("event_date")


def load_eampd_workbook(sources: FactorSources) -> pd.DataFrame:
    if sources.workbook_path is None:
        return pd.DataFrame(columns=["event_date", "ois_6m_mew", "stoxx50_mew", "eampd_source_vintage"])
    monetary_event = read_xlsx_sheet(sources.workbook_path, "xl/worksheets/sheet4.xml")
    keep = [column for column in ["event_date", "OIS_1M", "OIS_6M", "STOXX50", "SX7E"] if column in monetary_event.columns]
    monetary_event = monetary_event[keep].rename(
        columns={
            "OIS_1M": "ois_1m_mew",
            "OIS_6M": "ois_6m_mew",
            "STOXX50": "stoxx50_mew",
            "SX7E": "bank_stoxx_mew",
        }
    )
    monetary_event["eampd_source_vintage"] = f"EA-MPD_workbook_retrieved={sources.workbook_vintage}"
    return monetary_event.dropna(subset=["event_date"]).drop_duplicates("event_date").sort_values("event_date")


def quarter_end_from_period(period: pd.Period) -> pd.Timestamp:
    return period.to_timestamp(how="end").normalize()


def tag_regime_from_period(period: pd.Period) -> str:
    if period <= pd.Period("2008Q2"):
        return "pre_gfc"
    if period <= pd.Period("2009Q4"):
        return "gfc"
    if period <= pd.Period("2014Q4"):
        return "euro_crisis"
    if period <= pd.Period("2019Q4"):
        return "qe_era"
    if period <= pd.Period("2022Q2"):
        return "covid"
    return "tightening_regime"


def missing_flags(row: pd.Series) -> str:
    flags = []
    if row.get("event_not_in_abgmr_factor_files", False):
        flags.append("event_not_in_abgmr_factor_files")
    for column in ["target_factor", "timing_factor", "fg_factor"]:
        if pd.isna(row.get(column)):
            flags.append(f"missing_{column}")
    if pd.isna(row.get("qe_factor")):
        if row["event_date"] < pd.Timestamp("2014-01-01"):
            flags.append("qe_not_applicable_pre_2014")
        else:
            flags.append("missing_qe_factor")
    if pd.isna(row.get("ois_6m_mew")):
        flags.append("missing_eampd_ois_6m")
    if pd.isna(row.get("stoxx50_mew")):
        flags.append("missing_eampd_stoxx50")
    return "ok" if not flags else ";".join(flags)


def classify_meeting_type(row: pd.Series) -> str:
    has_release = pd.notna(row.get("target_factor"))
    has_conference = any(pd.notna(row.get(column)) for column in ["timing_factor", "fg_factor", "qe_factor"])
    if has_release and has_conference:
        return "press_release_plus_conference"
    if has_release:
        return "press_release_only"
    if has_conference:
        return "press_conference_only"
    return "ea_mpd_event_without_abgmr_factor"


def sign_with_zero(value: object, tolerance: float = 1e-12) -> float:
    if pd.isna(value):
        return np.nan
    numeric = float(value)
    if abs(numeric) <= tolerance:
        return 0.0
    return 1.0 if numeric > 0 else -1.0


def information_effect_classification(row: pd.Series) -> str:
    rate_sign = sign_with_zero(row.get("rate_surprise_for_screen"))
    equity_sign = sign_with_zero(row.get("equity_response_for_screen"))
    if pd.isna(rate_sign) or pd.isna(equity_sign):
        return "not_classified_missing_market_response"
    if rate_sign == 0 or equity_sign == 0:
        return "ambiguous_zero_response"
    if rate_sign == equity_sign:
        return "potential_information_shock"
    return "potential_pure_monetary_shock"


def build_event_level(factors: pd.DataFrame, eampd: pd.DataFrame) -> pd.DataFrame:
    factor_start = factors["event_date"].min()
    factor_end = factors["event_date"].max()
    if not eampd.empty:
        eampd_in_range = eampd.loc[eampd["event_date"].between(factor_start, factor_end)].copy()
        base_dates = pd.DataFrame({"event_date": sorted(set(factors["event_date"]).union(eampd_in_range["event_date"]))})
    else:
        eampd_in_range = eampd
        base_dates = pd.DataFrame({"event_date": sorted(factors["event_date"].dropna().unique())})

    events = base_dates.merge(factors, on="event_date", how="left", validate="one_to_one")
    if not eampd_in_range.empty:
        events = events.merge(eampd_in_range, on="event_date", how="left", validate="one_to_one")
    else:
        events["eampd_source_vintage"] = "not_available"

    events["event_not_in_abgmr_factor_files"] = events[FACTOR_COLUMNS].isna().all(axis=1)
    events["event_quarter"] = events["event_date"].dt.to_period("Q").astype(str)
    events["event_quarter_end"] = events["event_date"].dt.to_period("Q").map(quarter_end_from_period)
    events["regime"] = events["event_date"].dt.to_period("Q").map(tag_regime_from_period)
    events["source_vintage"] = np.where(
        events["event_not_in_abgmr_factor_files"],
        events.get("eampd_source_vintage", "EA-MPD_only"),
        events["abgmr_source_vintage"].fillna("ABGMR_unknown"),
    )
    events["meeting_type"] = events.apply(classify_meeting_type, axis=1)
    events["missing_flag"] = events.apply(missing_flags, axis=1)
    events["event_id"] = events["event_date"].dt.strftime("ECB_%Y%m%d")
    events["rate_surprise_for_screen"] = events["ois_6m_mew"].where(events["ois_6m_mew"].notna(), events["timing_factor"])
    events["equity_response_for_screen"] = events["stoxx50_mew"]
    events["jk_screen_classification"] = events.apply(information_effect_classification, axis=1)
    events["potential_information_shock"] = events["jk_screen_classification"].eq("potential_information_shock")
    events["potential_pure_monetary_shock"] = events["jk_screen_classification"].eq("potential_pure_monetary_shock")

    ordered_columns = [
        "event_date",
        "event_quarter",
        "event_quarter_end",
        "timing_factor",
        "target_factor",
        "fg_factor",
        "qe_factor",
        "source_vintage",
        "meeting_type",
        "missing_flag",
        "event_id",
        "regime",
        "ois_1m_mew",
        "ois_6m_mew",
        "stoxx50_mew",
        "bank_stoxx_mew",
        "rate_surprise_for_screen",
        "equity_response_for_screen",
        "jk_screen_classification",
        "potential_information_shock",
        "potential_pure_monetary_shock",
        "event_not_in_abgmr_factor_files",
    ]
    for column in ordered_columns:
        if column not in events.columns:
            events[column] = np.nan
    return events[ordered_columns].sort_values("event_date")


def aggregate_quarterly(events: pd.DataFrame) -> pd.DataFrame:
    periods = pd.period_range(
        events["event_date"].min().to_period("Q"),
        events["event_date"].max().to_period("Q"),
        freq="Q",
    )
    quarterly = pd.DataFrame({"quarter_period": periods})
    quarterly["date"] = quarterly["quarter_period"].map(quarter_end_from_period)
    quarterly["quarter"] = quarterly["quarter_period"].astype(str)
    quarterly["regime"] = quarterly["quarter_period"].map(tag_regime_from_period)

    grouped = events.groupby(events["event_date"].dt.to_period("Q"))
    event_counts = grouped.size().rename("event_count")
    missing_factor_counts = grouped["event_not_in_abgmr_factor_files"].sum().rename("events_without_abgmr_factor_count")
    quarterly = quarterly.merge(event_counts, left_on="quarter_period", right_index=True, how="left")
    quarterly = quarterly.merge(missing_factor_counts, left_on="quarter_period", right_index=True, how="left")
    quarterly["event_count"] = quarterly["event_count"].fillna(0).astype(int)
    quarterly["events_without_abgmr_factor_count"] = quarterly["events_without_abgmr_factor_count"].fillna(0).astype(int)
    quarterly["missing_quarter_flag"] = quarterly["event_count"].eq(0)

    for factor in FACTOR_COLUMNS:
        valid_count = grouped[factor].count().rename(f"{factor}_event_count")
        quarterly = quarterly.merge(valid_count, left_on="quarter_period", right_index=True, how="left")
        quarterly[f"{factor}_event_count"] = quarterly[f"{factor}_event_count"].fillna(0).astype(int)

        values = grouped[factor].agg(
            quarterly_sum="sum",
            quarterly_mean="mean",
            quarterly_abs_sum=lambda x: x.abs().sum(min_count=1),
            quarterly_signed_cumulative="sum",
        )
        values = values.rename(columns={name: f"{factor}_{name}" for name in AGGREGATIONS})
        quarterly = quarterly.merge(values, left_on="quarter_period", right_index=True, how="left")

    for factor in FACTOR_COLUMNS:
        for aggregation in AGGREGATIONS:
            column = f"{factor}_{aggregation}"
            if column in quarterly.columns:
                quarterly[column] = quarterly[column].where(quarterly[f"{factor}_event_count"].gt(0))
        quarterly[f"{factor}_absolute_sum"] = quarterly[f"{factor}_quarterly_abs_sum"]
        quarterly[f"{factor}_signed_cumulative"] = quarterly[f"{factor}_quarterly_signed_cumulative"]

    quarterly["baseline_instrument"] = quarterly["target_factor_quarterly_sum"]
    quarterly["baseline_instrument_name"] = "target_factor_quarterly_sum"
    quarterly = quarterly.drop(columns=["quarter_period"])
    return quarterly


def month_end_from_period(period: pd.Period) -> pd.Timestamp:
    return period.to_timestamp(how="end").normalize()


def tag_identification_regime(quarter: str | pd.Period) -> str:
    period = pd.Period(quarter, freq="Q") if not isinstance(quarter, pd.Period) else quarter
    for regime, (start, end) in REGIME_WINDOWS.items():
        if pd.Period(start, freq="Q") <= period <= pd.Period(end, freq="Q"):
            return regime
    return "outside_identification_windows"


def aggregate_monthly(events: pd.DataFrame) -> pd.DataFrame:
    periods = pd.period_range(
        events["event_date"].min().to_period("M"),
        events["event_date"].max().to_period("M"),
        freq="M",
    )
    monthly = pd.DataFrame({"month_period": periods})
    monthly["date"] = monthly["month_period"].map(month_end_from_period)
    monthly["month"] = monthly["month_period"].astype(str)
    monthly["quarter"] = monthly["month_period"].dt.to_timestamp().dt.to_period("Q").astype(str)
    monthly["regime"] = monthly["quarter"].map(lambda value: tag_regime_from_period(pd.Period(value, freq="Q")))
    monthly["identification_regime"] = monthly["quarter"].map(tag_identification_regime)

    grouped = events.groupby(events["event_date"].dt.to_period("M"))
    monthly = monthly.merge(grouped.size().rename("event_count"), left_on="month_period", right_index=True, how="left")
    monthly["event_count"] = monthly["event_count"].fillna(0).astype(int)
    monthly["missing_month_flag"] = monthly["event_count"].eq(0)

    for factor in FACTOR_COLUMNS:
        valid_count = grouped[factor].count().rename(f"{factor}_event_count")
        monthly = monthly.merge(valid_count, left_on="month_period", right_index=True, how="left")
        monthly[f"{factor}_event_count"] = monthly[f"{factor}_event_count"].fillna(0).astype(int)
        values = grouped[factor].agg(
            monthly_sum="sum",
            monthly_mean="mean",
            monthly_abs_sum=lambda x: x.abs().sum(min_count=1),
        )
        values = values.rename(columns={name: f"{factor}_{name}" for name in MONTHLY_BRIDGE_AGGREGATIONS})
        monthly = monthly.merge(values, left_on="month_period", right_index=True, how="left")
        for aggregation in MONTHLY_BRIDGE_AGGREGATIONS:
            column = f"{factor}_{aggregation}"
            monthly[column] = monthly[column].where(monthly[f"{factor}_event_count"].gt(0))
        monthly[f"{factor}_monthly_cumulative"] = monthly[f"{factor}_monthly_sum"].fillna(0).cumsum()

    composite_inputs = []
    for factor in FACTOR_COLUMNS:
        z = standardize_series(monthly[f"{factor}_monthly_sum"])
        composite_inputs.append(z.rename(factor))
    composite_input = pd.concat(composite_inputs, axis=1)
    monthly["weighted_composite_monthly_sum"] = composite_input.mean(axis=1, skipna=True)
    monthly["weighted_composite_monthly_mean"] = monthly["weighted_composite_monthly_sum"]
    monthly["weighted_composite_monthly_abs_sum"] = monthly["weighted_composite_monthly_sum"].abs()
    monthly["weighted_composite_monthly_cumulative"] = monthly["weighted_composite_monthly_sum"].fillna(0).cumsum()
    return monthly.drop(columns=["month_period"])


def aggregate_quarterly_bridge(monthly: pd.DataFrame) -> pd.DataFrame:
    bridge = (
        monthly.groupby("quarter", as_index=False)
        .agg(
            date=("date", "max"),
            regime=("regime", "last"),
            identification_regime=("identification_regime", "last"),
            monthly_event_count=("event_count", "sum"),
            missing_months_in_quarter=("missing_month_flag", "sum"),
        )
        .sort_values("date")
    )
    for factor in [*FACTOR_COLUMNS, "weighted_composite"]:
        source = f"{factor}_monthly_sum"
        if source not in monthly.columns:
            continue
        grouped = monthly.groupby("quarter")[source]
        values = grouped.agg(
            monthly_sum="sum",
            monthly_mean="mean",
            monthly_abs_sum=lambda x: x.abs().sum(min_count=1),
        )
        values = values.rename(columns={name: f"{factor}_{name}" for name in MONTHLY_BRIDGE_AGGREGATIONS})
        bridge = bridge.merge(values, on="quarter", how="left")
    return bridge


def standardize_series(series: pd.Series) -> pd.Series:
    clean = series.dropna()
    if clean.shape[0] < 2:
        return pd.Series(np.nan, index=series.index)
    sd = clean.std(ddof=1)
    if pd.isna(sd) or np.isclose(sd, 0.0):
        return pd.Series(np.nan, index=series.index)
    return (series - clean.mean()) / sd


def orient_series_to_reference(series: pd.Series, reference: pd.Series) -> pd.Series:
    aligned = pd.concat([series, reference], axis=1).dropna()
    if aligned.shape[0] >= 3 and aligned.iloc[:, 0].corr(aligned.iloc[:, 1]) < 0:
        return -series
    return series


def build_composite_shocks(quarterly: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    composite = quarterly[["date", "quarter", "regime", "event_count"]].copy()
    source_columns = {
        "timing": "timing_factor_quarterly_sum",
        "fg": "fg_factor_quarterly_sum",
        "qe": "qe_factor_quarterly_sum",
    }
    z_inputs = pd.DataFrame(index=quarterly.index)
    raw_inputs = pd.DataFrame(index=quarterly.index)
    for label, column in source_columns.items():
        raw_inputs[label] = quarterly[column]
        z_inputs[label] = standardize_series(quarterly[column]).fillna(0.0)

    matrix = z_inputs[["timing", "fg", "qe"]].to_numpy(dtype=float)
    u, singular_values, vt = np.linalg.svd(matrix, full_matrices=False)
    pc1_raw = pd.Series(u[:, 0] * singular_values[0], index=quarterly.index, name="composite_pca_timing_fg_qe")
    pc1 = pc1_raw.copy()
    loadings = pd.Series(vt[0, :], index=["timing", "fg", "qe"], name="loading")
    aligned = pd.concat([pc1_raw, quarterly["qe_factor_quarterly_sum"]], axis=1).dropna()
    if aligned.shape[0] >= 3 and aligned.iloc[:, 0].corr(aligned.iloc[:, 1]) < 0:
        pc1 = -pc1_raw
        loadings = -loadings
    explained = singular_values**2 / np.sum(singular_values**2)

    raw_variances = raw_inputs.var(skipna=True, ddof=1).replace(0, np.nan)
    inverse_weights = (1 / raw_variances).replace([np.inf, -np.inf], np.nan).fillna(0)
    inverse_weights = inverse_weights / inverse_weights.abs().sum()
    equal_weights = pd.Series({"timing": 1 / 3, "fg": 1 / 3, "qe": 1 / 3})
    qe_heavy_weights = pd.Series({"timing": 0.2, "fg": 0.2, "qe": 0.6})

    composite["composite_pca_timing_fg_qe"] = pc1
    composite["composite_equal_weight_timing_fg_qe"] = z_inputs.mul(equal_weights, axis=1).sum(axis=1)
    composite["composite_inverse_variance_timing_fg_qe"] = z_inputs.mul(inverse_weights, axis=1).sum(axis=1)
    composite["composite_qe_heavy_timing_fg_qe"] = z_inputs.mul(qe_heavy_weights, axis=1).sum(axis=1)

    loadings_table = pd.DataFrame(
        {
            "component": "composite_pca_timing_fg_qe",
            "factor": loadings.index,
            "loading": loadings.values,
            "variance_explained": explained[0],
        }
    )
    weights_table = pd.DataFrame(
        [
            {"composite": "composite_equal_weight_timing_fg_qe", "factor": factor, "weight": weight}
            for factor, weight in equal_weights.items()
        ]
        + [
            {"composite": "composite_inverse_variance_timing_fg_qe", "factor": factor, "weight": weight}
            for factor, weight in inverse_weights.items()
        ]
        + [
            {"composite": "composite_qe_heavy_timing_fg_qe", "factor": factor, "weight": weight}
            for factor, weight in qe_heavy_weights.items()
        ]
    )
    return composite, loadings_table, weights_table


def build_weighted_shocks(events: pd.DataFrame) -> pd.DataFrame:
    weighted_events = events[["event_date", "event_quarter", "regime"]].copy()
    crisis_regimes = {"gfc", "euro_crisis", "covid", "tightening_regime"}
    qe_abs_mean = events["qe_factor"].abs().mean(skipna=True)
    qe_event_weight = 1 + events["qe_factor"].abs().fillna(0) / qe_abs_mean if qe_abs_mean else pd.Series(1.0, index=events.index)
    for factor in FACTOR_COLUMNS:
        mean_abs = events[factor].abs().mean(skipna=True)
        magnitude_weight = events[factor].abs() / mean_abs if mean_abs else pd.Series(np.nan, index=events.index)
        crisis_weight = np.where(events["regime"].isin(crisis_regimes), 1.5, 1.0)
        weighted_events[f"{factor}_market_magnitude_weighted"] = events[factor] * magnitude_weight
        weighted_events[f"{factor}_crisis_weighted"] = events[factor] * crisis_weight
        weighted_events[f"{factor}_qe_event_weighted"] = events[factor] * qe_event_weight

    grouped = weighted_events.groupby("event_quarter")
    weighted = (
        grouped.size()
        .rename("event_count")
        .reset_index()
        .rename(columns={"event_quarter": "quarter"})
        .sort_values("quarter")
    )
    weighted["date"] = pd.PeriodIndex(weighted["quarter"], freq="Q").map(quarter_end_from_period)
    weighted["regime"] = pd.PeriodIndex(weighted["quarter"], freq="Q").map(tag_regime_from_period)
    weighted["identification_regime"] = weighted["quarter"].map(tag_identification_regime)
    for factor in FACTOR_COLUMNS:
        for scheme in ["market_magnitude_weighted", "crisis_weighted", "qe_event_weighted"]:
            column = f"{factor}_{scheme}"
            values = grouped[column].sum(min_count=1).rename(f"{factor}_{scheme}_quarterly_sum")
            weighted = weighted.merge(values, left_on="quarter", right_index=True, how="left")
    return weighted


def build_lpiv_quarterly_contract(
    quarterly: pd.DataFrame,
    quarterly_bridge: pd.DataFrame,
    composite: pd.DataFrame,
    weighted: pd.DataFrame,
) -> pd.DataFrame:
    """Return the self-contained quarterly surprise table used by LP-IV.

    The LP-IV layer reads one quarterly surprise table. Weighted, bridge, and
    composite constructions are folded into that table so the response code
    does not have to chase separate source files.
    """

    contract = quarterly.copy()
    for frame in (quarterly_bridge, composite, weighted):
        candidate_columns = ["date", "quarter"] + [
            column for column in frame.columns if column not in {"date", "quarter"} and column not in contract.columns
        ]
        candidate_columns = list(dict.fromkeys(candidate_columns))
        if len(candidate_columns) <= 2:
            continue
        contract = contract.merge(frame[candidate_columns], on=["date", "quarter"], how="left")

    if OFFICIAL_LPIV_BASELINE_INSTRUMENT in contract.columns:
        contract["baseline_instrument"] = contract[OFFICIAL_LPIV_BASELINE_INSTRUMENT]
        contract["baseline_instrument_name"] = OFFICIAL_LPIV_BASELINE_INSTRUMENT
    return contract


def load_canonical_dataset() -> pd.DataFrame:
    data = pd.read_csv(CANONICAL_DATASET, parse_dates=["date"]).sort_values("date")
    return data


def ar1_residual(series: pd.Series) -> pd.Series:
    clean = series.dropna()
    if len(clean) < 12 or clean.nunique() < 3:
        return pd.Series(index=series.index, dtype=float)
    y = clean.iloc[1:]
    x = sm.add_constant(clean.shift(1).dropna().loc[y.index])
    model = sm.OLS(y, x).fit()
    residuals = pd.Series(index=series.index, dtype=float)
    residuals.loc[y.index] = model.resid
    return residuals


def make_policy_target_frame(quarterly: pd.DataFrame) -> pd.DataFrame:
    canonical = load_canonical_dataset()
    merged = canonical.merge(quarterly, on=["date", "quarter"], how="left", suffixes=("", "_instrument"))
    merged["d_wx_shadow_rate"] = merged["wx_shadow_rate"].diff()
    merged["d_dfr_eop"] = merged["dfr_eop"].diff()
    merged["d_ln_ecb_assets_ea_stock"] = merged["ln_ecb_assets_ea_stock"].diff()
    merged["d_ecb_assets_ea_qavg"] = merged["ecb_assets_ea_qavg"].diff()
    merged["d_ln_hh_loans_ea_stock"] = merged["ln_hh_loans_ea_stock"].diff()
    merged["d_ln_nfc_loans_ea_stock"] = merged["ln_nfc_loans_ea_stock"].diff()
    merged["d_ln_house_price_de_real"] = merged["ln_house_price_de_real"].diff()
    for source_column in OPTIONAL_FIRST_STAGE_SOURCE_COLUMNS:
        if source_column in merged.columns:
            merged[f"d_{source_column}"] = merged[source_column].diff()
    merged["resid_d_wx_shadow_rate_ar1"] = ar1_residual(merged["d_wx_shadow_rate"])
    merged["resid_d_ln_ecb_assets_ea_stock_ar1"] = ar1_residual(merged["d_ln_ecb_assets_ea_stock"])
    merged["resid_d_dfr_eop_ar1"] = ar1_residual(merged["d_dfr_eop"])
    merged["identification_regime"] = merged["quarter"].map(tag_identification_regime)
    return merged


def available_first_stage_targets(policy_frame: pd.DataFrame) -> list[str]:
    targets = [target for target in REQUIRED_FIRST_STAGE_TARGETS if target in policy_frame.columns]
    for source_column in OPTIONAL_FIRST_STAGE_SOURCE_COLUMNS:
        target = f"d_{source_column}"
        if target in policy_frame.columns:
            targets.append(target)
    return targets


def instrument_columns(quarterly: pd.DataFrame) -> list[str]:
    columns = []
    for factor in FACTOR_COLUMNS:
        for aggregation in AGGREGATIONS:
            column = f"{factor}_{aggregation}"
            if column in quarterly.columns:
                columns.append(column)
    return columns


def weak_instrument_note(f_stat: float) -> str:
    if pd.isna(f_stat):
        return "not_available"
    if f_stat < 10:
        return "weak_instrument_warning_below_rule_of_thumb_10"
    if f_stat < 16.38:
        return "passes_F10_but_below_stock_yogo_style_16_38_caution"
    return "passes_conventional_F10_and_stock_yogo_style_16_38_screen"


def target_sample_mask(data: pd.DataFrame, target: str) -> tuple[pd.Series, str]:
    if target == "d_wx_shadow_rate":
        return data["baseline_sample"].eq(True), "baseline_2005q1_2022q2"
    return data["robustness_sample"].eq(True), "robustness_2005q1_2025q4"


def run_first_stage_regression(data: pd.DataFrame, instrument: str, target: str) -> dict[str, object]:
    clean = data.dropna(subset=[instrument, target])
    row: dict[str, object] = {
        "observations": int(clean.shape[0]),
        "coef": np.nan,
        "std_error": np.nan,
        "sign": "",
        "t_stat": np.nan,
        "p_value": np.nan,
        "F_stat": np.nan,
        "partial_R2": np.nan,
        "instrument_target_correlation": np.nan,
        "weak_instrument_interpretation": "not_enough_data",
    }
    if clean.shape[0] >= 12 and clean[instrument].nunique() > 2 and clean[target].nunique() > 2:
        x = sm.add_constant(clean[instrument])
        model = sm.OLS(clean[target], x).fit()
        t_stat = float(model.tvalues.iloc[1])
        f_stat = float(t_stat**2)
        coef = float(model.params.iloc[1])
        row.update(
            {
                "coef": coef,
                "std_error": float(model.bse.iloc[1]),
                "sign": "positive" if coef > 0 else "negative" if coef < 0 else "zero",
                "t_stat": t_stat,
                "p_value": float(model.pvalues.iloc[1]),
                "F_stat": f_stat,
                "partial_R2": float((t_stat**2) / ((t_stat**2) + model.df_resid)) if model.df_resid > 0 else np.nan,
                "instrument_target_correlation": float(clean[instrument].corr(clean[target])),
                "weak_instrument_interpretation": weak_instrument_note(f_stat),
            }
        )
    return row


def first_stage_diagnostics(policy_frame: pd.DataFrame, quarterly: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for instrument in instrument_columns(quarterly):
        for target in available_first_stage_targets(policy_frame):
            data = policy_frame[["date", "quarter", "baseline_sample", "robustness_sample", instrument, target]].copy()
            mask, sample = target_sample_mask(data, target)
            data = data.loc[mask]
            clean = data.dropna(subset=[instrument, target])
            fs = run_first_stage_regression(data, instrument, target)
            row = {
                "instrument": instrument,
                "policy_target": target,
                "sample": sample,
                "nobs": int(clean.shape[0]),
                "sample_start": clean["quarter"].min() if not clean.empty else "",
                "sample_end": clean["quarter"].max() if not clean.empty else "",
                "coefficient": fs["coef"],
                "std_error": fs["std_error"],
                "t_stat": fs["t_stat"],
                "p_value": fs["p_value"],
                "first_stage_f_stat": fs["F_stat"],
                "partial_r_squared": fs["partial_R2"],
                "instrument_policy_correlation": fs["instrument_target_correlation"],
                "weak_instrument_interpretation": fs["weak_instrument_interpretation"],
            "stock_yogo_style_note": "Formal Stock-Yogo critical values are not exact for LP-IV; F screens are used as cautionary evidence.",
            }
            rows.append(row)
    return pd.DataFrame(rows)


def candidate_specs(
    quarterly: pd.DataFrame,
    quarterly_bridge: pd.DataFrame,
    composite: pd.DataFrame,
    weighted: pd.DataFrame,
) -> list[dict[str, str]]:
    specs: list[dict[str, str]] = []
    for factor in FACTOR_COLUMNS:
        for aggregation in DIRECT_AGGREGATIONS:
            column = f"{factor}_{aggregation}"
            if column in quarterly.columns:
                specs.append(
                    {
                        "instrument": column,
                        "factor": FACTOR_LABELS[factor],
                        "aggregation": aggregation,
                        "architecture": "direct_quarterly",
                    }
                )
    for factor in FACTOR_COLUMNS:
        for aggregation in MONTHLY_BRIDGE_AGGREGATIONS:
            column = f"{factor}_{aggregation}"
            if column in quarterly_bridge.columns:
                specs.append(
                    {
                        "instrument": column,
                        "factor": FACTOR_LABELS[factor],
                        "aggregation": aggregation,
                        "architecture": "monthly_bridge_quarterly",
                    }
                )
    for aggregation in MONTHLY_BRIDGE_AGGREGATIONS:
        column = f"weighted_composite_{aggregation}"
        if column in quarterly_bridge.columns:
            specs.append(
                {
                    "instrument": column,
                    "factor": "weighted_composite",
                    "aggregation": aggregation,
                    "architecture": "monthly_bridge_quarterly",
                }
            )
    for column in composite.columns:
        if column.startswith("composite_"):
            specs.append(
                {
                    "instrument": column,
                    "factor": "composite",
                    "aggregation": column.replace("composite_", ""),
                    "architecture": "composite_quarterly",
                }
            )
    for factor in FACTOR_COLUMNS:
        for scheme in ["market_magnitude_weighted", "crisis_weighted", "qe_event_weighted"]:
            column = f"{factor}_{scheme}_quarterly_sum"
            if column in weighted.columns:
                specs.append(
                    {
                        "instrument": column,
                        "factor": FACTOR_LABELS[factor],
                        "aggregation": scheme,
                        "architecture": "weighted_event_quarterly",
                    }
                )
    return specs


def attach_candidate_frames(
    policy_frame: pd.DataFrame,
    quarterly_bridge: pd.DataFrame,
    composite: pd.DataFrame,
    weighted: pd.DataFrame,
    specs: list[dict[str, str]],
) -> pd.DataFrame:
    merged = policy_frame.copy()
    present = set(merged.columns)
    for frame in [quarterly_bridge, composite, weighted]:
        columns = ["date", "quarter"] + [
            spec["instrument"] for spec in specs if spec["instrument"] in frame.columns and spec["instrument"] not in present
        ]
        columns = list(dict.fromkeys(columns))
        if len(columns) <= 2:
            continue
        merged = merged.merge(frame[columns], on=["date", "quarter"], how="left")
        present.update(columns)
    return merged


def build_instrument_strength_matrix(
    policy_frame: pd.DataFrame,
    specs: list[dict[str, str]],
) -> pd.DataFrame:
    rows = []
    targets = available_first_stage_targets(policy_frame)
    for spec in specs:
        instrument = spec["instrument"]
        if instrument not in policy_frame.columns:
            continue
        for target in targets:
            mask, sample = target_sample_mask(policy_frame, target)
            data = policy_frame.loc[mask, ["date", "quarter", instrument, target]].copy()
            fs = run_first_stage_regression(data, instrument, target)
            rows.append(
                {
                    "factor": spec["factor"],
                    "aggregation": spec["aggregation"],
                    "target_equation": target,
                    "sample": sample,
                    "F_stat": fs["F_stat"],
                    "partial_R2": fs["partial_R2"],
                    "coef": fs["coef"],
                    "sign": fs["sign"],
                    "p_value": fs["p_value"],
                    "observations": fs["observations"],
                    "t_stat": fs["t_stat"],
                    "architecture": spec["architecture"],
                    "instrument": instrument,
                    "weak_instrument_interpretation": fs["weak_instrument_interpretation"],
                }
            )
    matrix = pd.DataFrame(rows)
    sort_columns = ["F_stat", "partial_R2"]
    return matrix.sort_values(sort_columns, ascending=False, na_position="last")


def excel_column_name(index: int) -> str:
    name = ""
    index += 1
    while index:
        index, remainder = divmod(index - 1, 26)
        name = chr(65 + remainder) + name
    return name


def xml_escape(value: object) -> str:
    text = "" if pd.isna(value) else str(value)
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
        .replace("'", "&apos;")
    )


def write_simple_xlsx(data: pd.DataFrame, path: Path, sheet_name: str = "strength_matrix") -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    rows = [list(data.columns)] + data.astype(object).where(pd.notna(data), "").values.tolist()
    sheet_rows = []
    for row_idx, row in enumerate(rows, start=1):
        cells = []
        for col_idx, value in enumerate(row):
            ref = f"{excel_column_name(col_idx)}{row_idx}"
            if isinstance(value, (int, float, np.integer, np.floating)) and not pd.isna(value):
                cells.append(f'<c r="{ref}"><v>{value}</v></c>')
            else:
                cells.append(f'<c r="{ref}" t="inlineStr"><is><t>{xml_escape(value)}</t></is></c>')
        sheet_rows.append(f'<row r="{row_idx}">{"".join(cells)}</row>')
    dimension = f"A1:{excel_column_name(max(len(data.columns) - 1, 0))}{len(rows)}"
    worksheet = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">'
        f'<dimension ref="{dimension}"/><sheetData>{"".join(sheet_rows)}</sheetData></worksheet>'
    )
    workbook = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" '
        'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">'
        f'<sheets><sheet name="{xml_escape(sheet_name[:31])}" sheetId="1" r:id="rId1"/></sheets></workbook>'
    )
    rels = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
        '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="xl/workbook.xml"/>'
        "</Relationships>"
    )
    workbook_rels = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
        '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet1.xml"/>'
        "</Relationships>"
    )
    content_types = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
        '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
        '<Default Extension="xml" ContentType="application/xml"/>'
        '<Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/>'
        '<Override PartName="/xl/worksheets/sheet1.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>'
        "</Types>"
    )
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as xlsx:
        xlsx.writestr("[Content_Types].xml", content_types)
        xlsx.writestr("_rels/.rels", rels)
        xlsx.writestr("xl/workbook.xml", workbook)
        xlsx.writestr("xl/_rels/workbook.xml.rels", workbook_rels)
        xlsx.writestr("xl/worksheets/sheet1.xml", worksheet)


def regime_specific_identification(
    policy_frame: pd.DataFrame,
    specs: list[dict[str, str]],
    strength_matrix: pd.DataFrame,
) -> pd.DataFrame:
    full_sign = strength_matrix.set_index(["instrument", "target_equation"])["sign"].to_dict()
    rows = []
    for spec in specs:
        instrument = spec["instrument"]
        if instrument not in policy_frame.columns:
            continue
        total_abs = policy_frame[instrument].abs().sum(skipna=True)
        for target in available_first_stage_targets(policy_frame):
            target_mask, sample = target_sample_mask(policy_frame, target)
            for regime, (start, end) in REGIME_WINDOWS.items():
                q = pd.PeriodIndex(policy_frame["quarter"], freq="Q")
                regime_mask = (q >= pd.Period(start, freq="Q")) & (q <= pd.Period(end, freq="Q"))
                data = policy_frame.loc[target_mask & regime_mask, ["date", "quarter", "event_count", instrument, target]]
                fs = run_first_stage_regression(data, instrument, target)
                sign_key = (instrument, target)
                full = full_sign.get(sign_key, "")
                regime_sign = fs["sign"]
                rows.append(
                    {
                        "factor": spec["factor"],
                        "aggregation": spec["aggregation"],
                        "architecture": spec["architecture"],
                        "instrument": instrument,
                        "target_equation": target,
                        "sample": sample,
                        "regime": regime,
                        "regime_start": start,
                        "regime_end": end,
                        "F_stat": fs["F_stat"],
                        "partial_R2": fs["partial_R2"],
                        "coef": fs["coef"],
                        "sign": regime_sign,
                        "full_sample_sign": full,
                        "sign_stability": "stable" if full and regime_sign and full == regime_sign else "unstable_or_unavailable",
                        "p_value": fs["p_value"],
                        "observations": fs["observations"],
                        "instrument_variance": data[instrument].var(skipna=True, ddof=1),
                        "event_count": int(data["event_count"].fillna(0).sum()) if "event_count" in data else np.nan,
                        "shock_abs_sum": data[instrument].abs().sum(skipna=True),
                        "shock_concentration_share": data[instrument].abs().sum(skipna=True) / total_abs
                        if total_abs and not np.isclose(total_abs, 0.0)
                        else np.nan,
                    }
                )
    return pd.DataFrame(rows)


def distribution_diagnostics(quarterly: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    rows = []
    outliers = []
    for instrument in instrument_columns(quarterly):
        series = quarterly.set_index("quarter")[instrument].dropna()
        if series.empty:
            continue
        abs_series = series.abs()
        top_n = max(1, math.ceil(series.shape[0] * 0.10))
        total_abs = abs_series.sum()
        mean = series.mean()
        sd = series.std(ddof=1)
        zscores = (series - mean) / sd if sd and not np.isclose(sd, 0.0) else series * np.nan
        outlier_quarters = zscores.loc[zscores.abs() >= 3].index.tolist()
        rows.append(
            {
                "instrument": instrument,
                "nobs": int(series.shape[0]),
                "mean": float(mean),
                "variance": float(series.var(ddof=1)),
                "std_dev": float(sd),
                "skewness": float(stats.skew(series, bias=False)) if series.shape[0] >= 3 else np.nan,
                "kurtosis_excess": float(stats.kurtosis(series, fisher=True, bias=False)) if series.shape[0] >= 4 else np.nan,
                "tail_concentration_top_10pct_abs_share": float(abs_series.nlargest(top_n).sum() / total_abs)
                if total_abs != 0
                else np.nan,
                "outlier_quarters_abs_z_ge_3": ",".join(outlier_quarters),
                "outlier_count_abs_z_ge_3": len(outlier_quarters),
            }
        )
        for quarter, zscore in zscores.loc[zscores.abs() >= 3].items():
            value = series.loc[quarter]
            outliers.append(
                {
                    "instrument": instrument,
                    "quarter": quarter,
                    "value": float(value),
                    "zscore": float(zscore),
                    "regime": tag_regime_from_period(pd.Period(quarter)),
                }
            )
    return pd.DataFrame(rows), pd.DataFrame(outliers)


def factor_variance_by_period(quarterly: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for instrument in instrument_columns(quarterly):
        factor_name = next((FACTOR_LABELS[factor] for factor in FACTOR_COLUMNS if instrument.startswith(f"{factor}_")), "")
        aggregation_name = next((aggregation for aggregation in AGGREGATIONS if instrument.endswith(f"_{aggregation}")), "")
        clean = quarterly[["quarter", "regime", instrument]].dropna()
        groups = [("all_periods", clean)]
        groups.extend((regime, group) for regime, group in clean.groupby("regime"))
        for period_name, group in groups:
            rows.append(
                {
                    "instrument": instrument,
                    "period": period_name,
                    "aggregation": aggregation_name,
                    "factor": factor_name,
                    "n_quarters": int(group.shape[0]),
                    "mean": float(group[instrument].mean()) if not group.empty else np.nan,
                    "variance": float(group[instrument].var(ddof=1)) if group.shape[0] > 1 else np.nan,
                    "std_dev": float(group[instrument].std(ddof=1)) if group.shape[0] > 1 else np.nan,
                }
            )
    return pd.DataFrame(rows)


def event_validation_audit(events: pd.DataFrame, factors: pd.DataFrame, eampd: pd.DataFrame) -> pd.DataFrame:
    factor_dates = pd.DatetimeIndex(factors["event_date"].dropna().drop_duplicates())
    eampd_dates = pd.DatetimeIndex(eampd["event_date"].dropna().drop_duplicates()) if not eampd.empty else pd.DatetimeIndex([])
    in_range_eampd = eampd_dates[(eampd_dates >= factor_dates.min()) & (eampd_dates <= factor_dates.max())]
    eampd_not_factor = in_range_eampd.difference(factor_dates)
    factor_not_eampd = factor_dates.difference(in_range_eampd) if len(in_range_eampd) else pd.DatetimeIndex([])

    gap_days = factor_dates.sort_values().to_series().diff().dt.days.dropna()
    large_gaps = gap_days.loc[gap_days > 70]
    post_2014 = events.loc[events["event_date"] >= pd.Timestamp("2014-01-01")]
    qe_coverage = post_2014["qe_factor"].notna().mean() if not post_2014.empty else np.nan
    covid_events = events.loc[events["event_date"].between("2020-01-01", "2022-06-30")]
    tightening_transition = events.loc[events["event_date"].between("2022-07-01", "2022-12-31")]

    outlier_details = []
    for factor in FACTOR_COLUMNS:
        clean = events[["event_date", factor]].dropna()
        if clean.shape[0] < 12:
            continue
        z = (clean[factor] - clean[factor].mean()) / clean[factor].std(ddof=1)
        flagged = clean.loc[z.abs() >= 4, "event_date"].dt.strftime("%Y-%m-%d").tolist()
        if flagged:
            outlier_details.append(f"{factor}:{','.join(flagged)}")

    rows = [
        {
            "audit_item": "duplicate_event_dates_cleaned_event_level",
            "status": "pass" if not events["event_date"].duplicated().any() else "review",
            "value": int(events["event_date"].duplicated().sum()),
            "details": "",
        },
        {
            "audit_item": "eampd_events_without_abgmr_factor_within_factor_range",
            "status": "review" if len(eampd_not_factor) else "pass",
            "value": len(eampd_not_factor),
            "details": ",".join(d.strftime("%Y-%m-%d") for d in eampd_not_factor),
        },
        {
            "audit_item": "abgmr_factor_dates_not_found_in_eampd_workbook",
            "status": "review" if len(factor_not_eampd) else "pass",
            "value": len(factor_not_eampd),
            "details": ",".join(d.strftime("%Y-%m-%d") for d in factor_not_eampd),
        },
        {
            "audit_item": "inter_meeting_gaps_over_70_days",
            "status": "review" if not large_gaps.empty else "pass",
            "value": int(large_gaps.shape[0]),
            "details": ",".join(f"{idx.strftime('%Y-%m-%d')}:{int(days)}d" for idx, days in large_gaps.items()),
        },
        {
            "audit_item": "post_2014_qe_factor_coverage",
            "status": "pass" if pd.notna(qe_coverage) and qe_coverage >= 0.95 else "review",
            "value": float(qe_coverage) if pd.notna(qe_coverage) else np.nan,
            "details": "Share of post-2014 event rows with non-missing QE factor.",
        },
        {
            "audit_item": "covid_policy_event_count_2020q1_2022q2",
            "status": "pass" if covid_events.shape[0] > 0 else "review",
            "value": int(covid_events.shape[0]),
            "details": ",".join(covid_events["event_date"].dt.strftime("%Y-%m-%d").tolist()),
        },
        {
            "audit_item": "pepp_emergency_2020_03_18_present",
            "status": "review" if pd.Timestamp("2020-03-18") not in set(events["event_date"]) else "pass",
            "value": int(pd.Timestamp("2020-03-18") in set(events["event_date"])),
            "details": "EA-MPD/ABGMR factor source does not include every unscheduled ECB emergency announcement.",
        },
        {
            "audit_item": "tightening_transition_event_count_2022h2",
            "status": "pass" if tightening_transition.shape[0] > 0 else "review",
            "value": int(tightening_transition.shape[0]),
            "details": ",".join(tightening_transition["event_date"].dt.strftime("%Y-%m-%d").tolist()),
        },
        {
            "audit_item": "factor_outlier_events_abs_z_ge_4",
            "status": "review" if outlier_details else "pass",
            "value": len(outlier_details),
            "details": ";".join(outlier_details),
        },
    ]
    return pd.DataFrame(rows)


def coverage_tables(events: pd.DataFrame, quarterly: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    coverage = quarterly[
        [
            "date",
            "quarter",
            "regime",
            "event_count",
            "events_without_abgmr_factor_count",
            "missing_quarter_flag",
            "timing_factor_event_count",
            "target_factor_event_count",
            "fg_factor_event_count",
            "qe_factor_event_count",
        ]
    ].copy()
    coverage["year"] = coverage["quarter"].str.slice(0, 4).astype(int)
    regime_summary = (
        events.groupby(["regime", "jk_screen_classification"], dropna=False)
        .size()
        .reset_index(name="event_count")
        .sort_values(["regime", "jk_screen_classification"])
    )
    total_by_regime = regime_summary.groupby("regime")["event_count"].transform("sum")
    regime_summary["share_within_regime"] = regime_summary["event_count"] / total_by_regime
    return coverage, regime_summary


def crisis_clustering_outputs(quarterly: pd.DataFrame, events: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    crisis_regimes = {"gfc", "euro_crisis", "covid"}
    concentration_rows = []
    for instrument in instrument_columns(quarterly):
        clean = quarterly[["quarter", "regime", instrument]].dropna()
        total_abs = clean[instrument].abs().sum()
        for regime, group in clean.groupby("regime"):
            regime_abs = group[instrument].abs().sum()
            concentration_rows.append(
                {
                    "instrument": instrument,
                    "regime": regime,
                    "n_quarters": int(group.shape[0]),
                    "abs_sum": float(regime_abs),
                    "share_of_total_abs": float(regime_abs / total_abs) if total_abs != 0 else np.nan,
                    "is_crisis_regime": regime in crisis_regimes,
                }
            )
        crisis_abs = clean.loc[clean["regime"].isin(crisis_regimes), instrument].abs().sum()
        concentration_rows.append(
            {
                "instrument": instrument,
                "regime": "all_crisis_regimes",
                "n_quarters": int(clean.loc[clean["regime"].isin(crisis_regimes)].shape[0]),
                "abs_sum": float(crisis_abs),
                "share_of_total_abs": float(crisis_abs / total_abs) if total_abs != 0 else np.nan,
                "is_crisis_regime": True,
            }
        )
    concentration = pd.DataFrame(concentration_rows)

    quarter_density = quarterly[["date", "quarter", "regime", "event_count", "missing_quarter_flag"]].copy()
    quarter_density["events_per_quarter_bin"] = pd.cut(
        quarter_density["event_count"],
        bins=[-0.1, 0, 1, 2, 3, 10],
        labels=["0", "1", "2", "3", "4+"],
    )

    event_counts = events.groupby("regime").size().sort_index()
    fig, axes = plt.subplots(2, 1, figsize=(11, 8), constrained_layout=True)
    event_counts.plot(kind="bar", ax=axes[0], color="#4c78a8", title="ECB Surprise Event Count by Regime")
    timing_abs = (
        quarterly.groupby("regime")["timing_factor_quarterly_sum"]
        .apply(lambda x: x.abs().sum())
        .reindex(event_counts.index)
    )
    timing_abs.plot(kind="bar", ax=axes[1], color="#f58518", title="Absolute Timing-Factor Surprise by Regime")
    for ax in axes:
        ax.grid(axis="y", alpha=0.25)
        ax.set_xlabel("")
    fig.savefig(FIG_DIR / "regime_histograms.png", dpi=170)
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(12, 5), constrained_layout=True)
    for factor in ["timing_factor", "target_factor", "fg_factor", "qe_factor"]:
        column = f"{factor}_quarterly_sum"
        quarterly.set_index("date")[column].rolling(8, min_periods=4).var().plot(ax=ax, label=factor)
    ax.set_title("Eight-Quarter Rolling Variance of Quarterly-Sum ECB Surprise Factors")
    ax.grid(True, alpha=0.25)
    ax.legend(loc="upper left", ncols=2)
    fig.savefig(FIG_DIR / "quarterly_surprise_rolling_variance.png", dpi=170)
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(12, 4), constrained_layout=True)
    quarterly.set_index("date")["event_count"].plot(ax=ax, drawstyle="steps-mid", color="#54a24b")
    ax.set_title("ECB Surprise Event Density by Quarter")
    ax.set_ylabel("event count")
    ax.grid(True, alpha=0.25)
    fig.savefig(FIG_DIR / "quarter_density.png", dpi=170)
    plt.close(fig)

    return concentration, quarter_density


def information_effect_outputs(events: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    event_flags = events[
        [
            "event_id",
            "event_date",
            "event_quarter",
            "regime",
            "timing_factor",
            "rate_surprise_for_screen",
            "equity_response_for_screen",
            "jk_screen_classification",
            "potential_information_shock",
            "potential_pure_monetary_shock",
        ]
    ].copy()
    quarter_flags = (
        event_flags.groupby(["event_quarter", "regime", "jk_screen_classification"])
        .size()
        .unstack(fill_value=0)
        .reset_index()
    )
    for column in [
        "potential_information_shock",
        "potential_pure_monetary_shock",
        "ambiguous_zero_response",
        "not_classified_missing_market_response",
    ]:
        if column not in quarter_flags.columns:
            quarter_flags[column] = 0
    quarter_flags["classified_event_count"] = (
        quarter_flags["potential_information_shock"] + quarter_flags["potential_pure_monetary_shock"]
    )
    quarter_flags["information_share"] = np.where(
        quarter_flags["classified_event_count"] > 0,
        quarter_flags["potential_information_shock"] / quarter_flags["classified_event_count"],
        np.nan,
    )
    regime_summary = (
        event_flags.groupby(["regime", "jk_screen_classification"])
        .size()
        .reset_index(name="event_count")
        .sort_values(["regime", "jk_screen_classification"])
    )
    regime_summary["share_within_regime"] = regime_summary["event_count"] / regime_summary.groupby("regime")[
        "event_count"
    ].transform("sum")
    return event_flags, quarter_flags, regime_summary


def top_strength_rows(
    strength_matrix: pd.DataFrame,
    factor: str | None = None,
    target_contains: list[str] | None = None,
    architecture: str | None = None,
    n: int = 5,
) -> pd.DataFrame:
    data = strength_matrix.copy()
    if factor is not None:
        data = data.loc[data["factor"].eq(factor)]
    if architecture is not None:
        data = data.loc[data["architecture"].eq(architecture)]
    if target_contains:
        pattern = "|".join(re.escape(item) for item in target_contains)
        data = data.loc[data["target_equation"].str.contains(pattern, regex=True)]
    return data.sort_values("F_stat", ascending=False, na_position="last").head(n)


def format_strength_table(data: pd.DataFrame, columns: list[str] | None = None) -> str:
    if data.empty:
        return "_No available rows._"
    display_columns = columns or ["instrument", "target_equation", "sample", "F_stat", "partial_R2", "coef", "p_value"]
    display = data[display_columns].copy()
    for column in ["F_stat", "partial_R2", "coef", "p_value"]:
        if column in display.columns:
            display[column] = display[column].map(lambda value: "" if pd.isna(value) else f"{value:.3f}")
    header = "| " + " | ".join(display.columns) + " |"
    divider = "| " + " | ".join(["---"] * len(display.columns)) + " |"
    rows = ["| " + " | ".join(str(value) for value in row) + " |" for row in display.to_numpy()]
    return "\n".join([header, divider, *rows])


def candidate_group_summary(strength_matrix: pd.DataFrame) -> pd.DataFrame:
    def group_name(row: pd.Series) -> str:
        if row["architecture"] == "monthly_bridge_quarterly":
            return "monthly_bridge"
        if row["architecture"] == "composite_quarterly":
            return "composite"
        if row["architecture"] == "weighted_event_quarterly":
            return "weighted_variants"
        return row["factor"]

    grouped = strength_matrix.copy()
    grouped["candidate"] = grouped.apply(group_name, axis=1)
    summary = (
        grouped.sort_values("F_stat", ascending=False, na_position="last")
        .groupby("candidate", as_index=False)
        .first()
    )
    summary["strength"] = pd.cut(
        summary["F_stat"],
        bins=[-np.inf, 5, 10, 16.38, np.inf],
        labels=["weak", "borderline", "usable_F10", "strong_F16"],
    ).astype(str)
    economic_fit = {
        "timing": "conventional rate-news fit, weak balance-sheet fit",
        "qe": "closest fit to balance-sheet transmission",
        "fg": "communication channel robustness",
        "target": "short-rate target shock robustness",
        "composite": "captures shared ECB surprise variation",
        "monthly_bridge": "tests whether quarterly aggregation destroyed signal",
        "weighted_variants": "tests event-intensity and crisis leverage",
        "weighted_composite": "monthly composite bridge",
    }
    summary["economic_fit"] = summary["candidate"].map(economic_fit).fillna("robustness candidate")
    summary["feasible"] = np.where(summary["F_stat"] >= 10, "yes", np.where(summary["F_stat"] >= 5, "weak_caution", "no"))
    return summary[
        [
            "candidate",
            "instrument",
            "target_equation",
            "architecture",
            "aggregation",
            "F_stat",
            "partial_R2",
            "strength",
            "economic_fit",
            "feasible",
        ]
    ].sort_values("F_stat", ascending=False, na_position="last")


def regime_stability_summary(regime_results: pd.DataFrame) -> pd.DataFrame:
    if regime_results.empty:
        return pd.DataFrame()
    return (
        regime_results.assign(strong_regime=lambda x: x["F_stat"].ge(10))
        .groupby(["instrument", "factor", "architecture"], as_index=False)
        .agg(
            max_regime_F=("F_stat", "max"),
            median_regime_F=("F_stat", "median"),
            stable_sign_share=("sign_stability", lambda x: (x == "stable").mean()),
            strong_regime_count=("strong_regime", "sum"),
        )
        .sort_values("max_regime_F", ascending=False, na_position="last")
    )


def write_strength_outputs(strength_matrix: pd.DataFrame) -> None:
    csv_path = DIAGNOSTICS_ROOT / "instrument_strength_matrix.csv"
    xlsx_path = DIAGNOSTICS_ROOT / "instrument_strength_matrix.xlsx"
    strength_matrix.to_csv(csv_path, index=False)
    write_simple_xlsx(strength_matrix, xlsx_path)
    strength_matrix.to_csv(RESULTS_DIR / "instrument_strength_matrix.csv", index=False)


def write_qe_vs_timing_memo(strength_matrix: pd.DataFrame) -> None:
    thesis_targets = ["d_ln_ecb_assets_ea_stock", "d_ecb_assets_ea_qavg", "d_ln_hh_loans_ea_stock", "d_ln_nfc_loans_ea_stock", "d_ln_house_price_de_real"]
    qe_best = top_strength_rows(strength_matrix, factor="qe", target_contains=thesis_targets, n=8)
    timing_best = top_strength_rows(strength_matrix, factor="timing", target_contains=thesis_targets, n=8)
    qe_max = qe_best["F_stat"].max(skipna=True) if not qe_best.empty else np.nan
    timing_max = timing_best["F_stat"].max(skipna=True) if not timing_best.empty else np.nan
    answer = (
        "QE provides materially stronger identification than timing for this thesis design."
        if pd.notna(qe_max) and pd.notna(timing_max) and qe_max > timing_max * 1.25
        else "QE does not materially dominate timing across the thesis targets under the current screens."
    )
    text = f"""# QE vs Timing Identification

This note compares QE-centered ECB surprise measures with conventional timing surprises. It does not estimate response paths.

## Answer

{answer}

Best QE first-stage F-stat across ECB asset, loan, and housing targets: `{qe_max:.3f}`.

Best timing first-stage F-stat across the same target family: `{timing_max:.3f}`.

## QE Candidate Leaders

{format_strength_table(qe_best)}

## Timing Candidate Leaders

{format_strength_table(timing_best)}

## Interpretation

QE is economically natural for a balance-sheet transmission thesis, but it still has to show relevance. If QE strength appears mainly against DFR and not against ECB assets, household loans, NFC loans, or housing, it is not enough to carry the design by itself.
"""
    (DOCS_DIR / "qe_vs_timing_identification_assessment.md").write_text(text, encoding="utf-8")


def write_composite_design_doc(
    strength_matrix: pd.DataFrame,
    loadings: pd.DataFrame,
    weights: pd.DataFrame,
    regime_results: pd.DataFrame,
) -> None:
    composite_best = top_strength_rows(strength_matrix, architecture="composite_quarterly", n=10)
    composite_regime = regime_stability_summary(regime_results)
    composite_regime = composite_regime.loc[composite_regime["architecture"].eq("composite_quarterly")].head(8)
    text = f"""# Composite Shock Design

Composite shocks are checks unless the first-stage evidence supports them.

## Variants Constructed

- `composite_pca_timing_fg_qe`: first principal component of standardized timing, forward-guidance, and QE quarterly shocks.
- `composite_equal_weight_timing_fg_qe`: standardized equal-weight sum.
- `composite_inverse_variance_timing_fg_qe`: standardized sum using inverse raw-variance weights.
- `composite_qe_heavy_timing_fg_qe`: standardized weighted sum with QE weight 0.6 and timing/FG weights 0.2 each.

## PCA Loading Structure

{format_strength_table(loadings.rename(columns={"component": "instrument", "factor": "target_equation", "loading": "coef", "variance_explained": "partial_R2"}), ["instrument", "target_equation", "coef", "partial_R2"])}

## Weighted-Sum Weights

{format_strength_table(weights.rename(columns={"composite": "instrument", "factor": "target_equation", "weight": "coef"}), ["instrument", "target_equation", "coef"])}

## First-Stage Leaders

{format_strength_table(composite_best)}

## Regime Stability Leaders

{format_strength_table(composite_regime, ["instrument", "factor", "max_regime_F", "median_regime_F", "stable_sign_share", "strong_regime_count"])}
"""
    (DOCS_DIR / "composite_instrument_design.md").write_text(text, encoding="utf-8")


def write_regime_stability_doc(regime_results: pd.DataFrame) -> None:
    leaders = regime_results.sort_values("F_stat", ascending=False, na_position="last").head(12)
    stability = regime_stability_summary(regime_results).head(12)
    text = f"""# Regime Identification Stability

Regime-specific checks split the sample into pre-QE, QE, COVID, and tightening windows. Small-regime first stages are screening evidence, not structural estimates.

## Regime First-Stage Leaders

{format_strength_table(leaders, ["instrument", "factor", "aggregation", "target_equation", "regime", "F_stat", "partial_R2", "observations", "sign_stability"])}

## Stability Summary

{format_strength_table(stability, ["instrument", "factor", "architecture", "max_regime_F", "median_regime_F", "stable_sign_share", "strong_regime_count"])}

## Reading Rule

An instrument that is strong only in one short regime is not automatically a main instrument. It is a candidate for regime-restricted checks.
"""
    (DOCS_DIR / "regime_identification_stability.md").write_text(text, encoding="utf-8")


def write_weighting_design_doc(strength_matrix: pd.DataFrame) -> None:
    weighted_best = top_strength_rows(strength_matrix, architecture="weighted_event_quarterly", n=12)
    text = f"""# Shock Weighting

The weighting layer tests whether equal event weighting weakens relevance.

## Schemes

- Market-magnitude weighting: each event shock is multiplied by its absolute surprise size relative to the factor's mean absolute event surprise.
- Crisis weighting: GFC, sovereign-crisis, COVID, and tightening-regime events receive a 1.5 multiplier.
- QE-event weighting: events with larger QE surprises receive larger weights, applied across factor families to test balance-sheet-signal concentration.

## First-Stage Leaders

{format_strength_table(weighted_best)}

## Interpretation

Weighted variants are not automatically preferred. They must improve relevance without making identification depend mechanically on crisis leverage or QE-only events.
"""
    (DOCS_DIR / "shock_weighting_design.md").write_text(text, encoding="utf-8")


def write_information_screening_doc(info_events: pd.DataFrame, info_regime_summary: pd.DataFrame) -> None:
    counts = info_events["jk_screen_classification"].value_counts().rename_axis("classification").reset_index(name="event_count")
    text = f"""# Information-Effect Screen

This is a lightweight Jarocinski-Karadi-style screen, not a full decomposition.

## Event Logic

- Same-sign rate and equity responses are flagged as potential central-bank information shocks.
- Opposite-sign rate and equity responses are flagged as potential pure monetary shocks.
- Zero or missing market responses are flagged as ambiguous or unclassified.

## Event Counts

{format_strength_table(counts.rename(columns={"classification": "instrument", "event_count": "observations"}), ["instrument", "observations"])}

## Regime Summary

{format_strength_table(info_regime_summary.rename(columns={"regime": "instrument", "jk_screen_classification": "target_equation", "event_count": "observations", "share_within_regime": "partial_R2"}), ["instrument", "target_equation", "observations", "partial_R2"])}

## Use in Thesis

These flags support interpretation and robustness checks only. They do not replace the ABGMR external instrument or expand the causal claim.
"""
    (DOCS_DIR / "information_effect_screening.md").write_text(text, encoding="utf-8")


def write_final_identification_recommendation(
    strength_matrix: pd.DataFrame,
    regime_results: pd.DataFrame,
) -> None:
    decision = candidate_group_summary(strength_matrix)
    stability = regime_stability_summary(regime_results)
    if not decision.empty and not stability.empty:
        stability_best = (
            stability.sort_values("max_regime_F", ascending=False, na_position="last")
            .groupby("instrument", as_index=False)
            .first()[["instrument", "stable_sign_share", "strong_regime_count"]]
        )
        decision = decision.merge(stability_best, on="instrument", how="left")
        decision["stability"] = np.where(
            decision["stable_sign_share"].ge(0.5) & decision["strong_regime_count"].ge(1),
            "regime_supported",
            np.where(decision["stable_sign_share"].ge(0.5), "sign_stable_but_weak", "unstable_or_not_supported"),
        )
    else:
        decision["stability"] = "not_available"
    decision.to_csv(DIAGNOSTICS_ROOT / "external_identification_decision_matrix.csv", index=False)

    official = strength_matrix.loc[
        (strength_matrix["instrument"] == OFFICIAL_LPIV_BASELINE_INSTRUMENT)
        & (strength_matrix["target_equation"] == "d_ecb_assets_ea_qavg")
    ].copy()
    selected = (
        official.sort_values("F_stat", ascending=False, na_position="last").iloc[0]
        if not official.empty
        else pd.Series(dtype=object)
    )

    selected_regime = regime_results.loc[
        (regime_results["instrument"] == selected.get("instrument"))
        & (regime_results["target_equation"] == selected.get("target_equation"))
    ]
    max_concentration = selected_regime["shock_concentration_share"].max(skipna=True) if not selected_regime.empty else np.nan
    stable_share = (selected_regime["sign_stability"] == "stable").mean() if not selected_regime.empty else np.nan
    viability = "LP-IV identification is retained, but first-stage checks must be read before response interpretation."
    recommendation = (
        f"LP-IV instrument: `{OFFICIAL_LPIV_BASELINE_INSTRUMENT}` against `d_ecb_assets_ea_qavg`."
    )

    text = f"""# External Identification Recommendation

This note summarizes the ECB external-instrument choice. It does not estimate responses or force weak-IV interpretation.

## Decision

{viability}

{recommendation}

## Decision Matrix

{format_strength_table(decision, ["candidate", "strength", "stability", "F_stat", "partial_R2", "economic_fit", "feasible"])}

## Required Fields

- Factor choice: `{selected.get('factor', 'none') if not selected.empty else 'none'}`
- Aggregation: `{selected.get('aggregation', 'none') if not selected.empty else 'none'}`
- Frequency/design: `{selected.get('architecture', 'none') if not selected.empty else 'none'}`
- First-stage target: `{selected.get('target_equation', 'none') if not selected.empty else 'none'}`
- Regime restrictions: `{f"required for review; max regime shock concentration is {max_concentration:.1%}" if pd.notna(max_concentration) else "not available"}`
- Weighting: `{selected.get('aggregation', 'none') if not selected.empty else 'none'}`
- LP-IV status: `{viability}`

## Closed Phases

Deprecated SVECM experiments, FEVDs, historical decompositions, counterfactuals, welfare claims, and policy conclusions remain archived.
"""
    (DOCS_DIR / "final_external_identification_recommendation.md").write_text(text, encoding="utf-8")


def write_aggregation_philosophy() -> None:
    text = f"""# ECB Surprise Aggregation

This note explains how event surprises are aggregated before response estimation.

## Main Rule

The main aggregation is the market-magnitude weighted quarterly sum of the ABGMR `target` factor:

`{OFFICIAL_LPIV_BASELINE_INSTRUMENT}`.

The reason is theoretical: high-frequency ECB surprises are flow/news shocks. If more than one Governing Council event occurs in a quarter, the quarterly economy receives multiple pieces of monetary-policy information. Summing preserves that cumulative information arrival, while averaging would shrink quarters with several events merely because the ECB met more often.

## Check Exports

The code also exports check transformations for every factor:

- `quarterly_mean`: scale robustness that checks whether results depend on meeting-count intensity.
- `absolute_sum`: intensity-only robustness that ignores the easing/tightening sign and measures shock magnitude.
- `signed_cumulative`: final within-quarter cumulative signed surprise after sorting events by date. At a quarterly endpoint this equals the signed quarterly sum, but it is exported separately to make the cumulative-news interpretation clear.

## Main And Check Roles

The main external instrument is:

```text
{OFFICIAL_LPIV_BASELINE_INSTRUMENT}
```

The `timing_factor`, `fg_factor`, and `qe_factor` series are kept for decomposition and transmission checks. They are not intended to enter the main LP-IV simultaneously.

The lightweight Jarocinski-Karadi-style screen uses signs of `OIS_6M` and `STOXX50` from the EA-MPD monetary-event window. It informs interpretation but does not replace the main instrument.
"""
    (DOCS_DIR / "ecb_surprise_aggregation_philosophy.md").write_text(text, encoding="utf-8")


def summarize_first_stage(first_stage: pd.DataFrame, instrument: str, target: str) -> pd.Series | None:
    subset = first_stage.loc[(first_stage["instrument"] == instrument) & (first_stage["policy_target"] == target)]
    if subset.empty:
        return None
    return subset.iloc[0]


def write_assessment_memo(
    events: pd.DataFrame,
    quarterly: pd.DataFrame,
    first_stage: pd.DataFrame,
    distribution: pd.DataFrame,
    crisis_concentration: pd.DataFrame,
    validation: pd.DataFrame,
    info_regime_summary: pd.DataFrame,
) -> None:
    timing_wx = summarize_first_stage(first_stage, "timing_factor_quarterly_sum", "d_wx_shadow_rate")
    timing_assets = summarize_first_stage(first_stage, "timing_factor_quarterly_sum", "d_ln_ecb_assets_ea_stock")
    timing_dfr = summarize_first_stage(first_stage, "timing_factor_quarterly_sum", "d_dfr_eop")
    timing_distribution = distribution.loc[distribution["instrument"] == "timing_factor_quarterly_sum"]
    crisis_row = crisis_concentration.loc[
        (crisis_concentration["instrument"] == "timing_factor_quarterly_sum")
        & (crisis_concentration["regime"] == "all_crisis_regimes")
    ]
    coverage_start = events["event_date"].min().date()
    coverage_end = events["event_date"].max().date()
    event_count = events.shape[0]
    quarter_count = quarterly.shape[0]
    missing_quarters = int(quarterly["missing_quarter_flag"].sum())
    source_gap = validation.loc[validation["audit_item"] == "eampd_events_without_abgmr_factor_within_factor_range"]
    qe_coverage = validation.loc[validation["audit_item"] == "post_2014_qe_factor_coverage"]
    pepp_row = validation.loc[validation["audit_item"] == "pepp_emergency_2020_03_18_present"]

    def fs_line(row: pd.Series | None) -> str:
        if row is None or pd.isna(row["first_stage_f_stat"]):
            return "not available"
        return (
            f"F={row['first_stage_f_stat']:.2f}, partial R2={row['partial_r_squared']:.3f}, "
            f"coef={row['coefficient']:.4f}, p={row['p_value']:.3f}, "
            f"{row['weak_instrument_interpretation']}"
        )

    crisis_share = float(crisis_row["share_of_total_abs"].iloc[0]) if not crisis_row.empty else np.nan
    tail_share = (
        float(timing_distribution["tail_concentration_top_10pct_abs_share"].iloc[0])
        if not timing_distribution.empty
        else np.nan
    )
    outliers = (
        str(timing_distribution["outlier_quarters_abs_z_ge_3"].iloc[0])
        if not timing_distribution.empty
        else ""
    )
    qe_value = float(qe_coverage["value"].iloc[0]) if not qe_coverage.empty else np.nan
    pepp_status = pepp_row["status"].iloc[0] if not pepp_row.empty else "not_available"
    source_gap_details = source_gap["details"].iloc[0] if not source_gap.empty else ""

    memo = f"""# ECB External-Instrument Pre-Estimation Note

This note closes the external-instrument preparation stage. It does not estimate response paths or write thesis conclusions.

## Source and Coverage

- Working factor vintage: ABGMR `{CURRENT_FACTOR_VINTAGE}`.
- Event coverage after cleaning: {event_count} event rows from {coverage_start} to {coverage_end}.
- Quarterly export coverage: {quarter_count} quarters, with {missing_quarters} no-event quarters.
- ECB EA-MPD coverage gap: `{source_gap_details or 'none'}`.
- Post-2014 QE factor coverage: {qe_value:.1%}.
- PEPP emergency 2020-03-18 in source event list: `{pepp_status}`. This is flagged because EA-MPD/ABGMR factors do not necessarily include every unscheduled emergency announcement.

## 1. Is the instrument strong enough?

Source check for the timing-factor first stage, using `timing_factor_quarterly_sum`:

- Wu-Xia shadow-rate change: {fs_line(timing_wx)}
- ECB asset log growth: {fs_line(timing_assets)}
- DFR change: {fs_line(timing_dfr)}

Current LP-IV instrument: `{OFFICIAL_LPIV_BASELINE_INSTRUMENT}` against `d_ecb_assets_ea_qavg`. The timing-factor rows above are source checks only.

## 2. Is quarterly aggregation defensible?

Yes, the `quarterly_sum` rule is defensible for the thesis design. ECB surprises are high-frequency news-flow shocks. Multiple meetings in a quarter represent cumulative policy-information arrivals, so summing is the most natural quarterly mapping. The code also exports `quarterly_mean`, `absolute_sum`, and `signed_cumulative` variants to test whether conclusions depend on meeting density, sign, or cumulative-news treatment.

## 3. Does identification depend excessively on crisis periods?

For the timing factor, crisis regimes account for {crisis_share:.1%} of total absolute quarterly surprise mass. The top decile of absolute timing surprises accounts for {tail_share:.1%} of total absolute mass. Outlier quarters with |z| >= 3: `{outliers or 'none'}`.

This means crisis leverage must be reported explicitly. Regime concentration, rolling variance, and quarter-density checks are reviewed before estimation.

## 4. Is the main instrument stable across QE, COVID, and tightening?

The source covers the QE era, COVID period, and 2022 tightening transition. QE factors are populated after 2014, and the 2022H2 tightening events are present. The COVID emergency-announcement check is cautious because the PEPP emergency date is not present in the ABGMR factor event list.

The lightweight JK-style sign screen is preserved as an interpretation layer. It flags potential central-bank information events from rate/equity comovement but is not used as the main identification source.

## 5. Final pre-estimation recommendation

- LP-IV instrument: `{OFFICIAL_LPIV_BASELINE_INSTRUMENT}`.
- Checks: weighted shocks, signed cumulative variants, quarterly means, and monthly bridge variants.
- Excluded from the main design: simultaneous multi-factor instruments, full Jarocinski-Karadi replication, and DAX as a main response.

Next step: response estimation with first-stage, rolling, regime, horizon, and weak-IV checks.
"""
    (DOCS_DIR / "ecb_external_instrument_pre_estimation_assessment.md").write_text(memo, encoding="utf-8")


def write_outputs(
    events: pd.DataFrame,
    quarterly: pd.DataFrame,
    monthly: pd.DataFrame,
    quarterly_bridge: pd.DataFrame,
    composite: pd.DataFrame,
    weighted: pd.DataFrame,
    first_stage: pd.DataFrame,
    strength_matrix: pd.DataFrame,
    regime_results: pd.DataFrame,
    composite_loadings: pd.DataFrame,
    composite_weights: pd.DataFrame,
    distribution: pd.DataFrame,
    outliers: pd.DataFrame,
    variance_by_period: pd.DataFrame,
    validation: pd.DataFrame,
    coverage: pd.DataFrame,
    regime_coverage: pd.DataFrame,
    crisis_concentration: pd.DataFrame,
    quarter_density: pd.DataFrame,
    info_events: pd.DataFrame,
    info_quarters: pd.DataFrame,
    info_regime_summary: pd.DataFrame,
) -> None:
    events.to_csv(PROCESSED_DIR / "ecb_surprise_event_level.csv", index=False)
    quarterly.to_csv(PROCESSED_DIR / "ecb_surprise_quarterly.csv", index=False)
    monthly.to_csv(PROCESSED_DIR / "ecb_surprise_monthly.csv", index=False)
    quarterly_bridge.to_csv(PROCESSED_DIR / "ecb_surprise_quarterly_bridge.csv", index=False)
    composite.to_csv(PROCESSED_DIR / "ecb_composite_shocks.csv", index=False)
    weighted.to_csv(PROCESSED_DIR / "ecb_weighted_shocks.csv", index=False)
    first_stage.to_csv(RESULTS_DIR / "first_stage_relevance.csv", index=False)
    write_strength_outputs(strength_matrix)
    regime_results.to_csv(DIAGNOSTICS_ROOT / "regime_specific_identification.csv", index=False)
    regime_results.to_csv(RESULTS_DIR / "regime_specific_identification.csv", index=False)
    composite_loadings.to_csv(RESULTS_DIR / "composite_loading_structure.csv", index=False)
    composite_weights.to_csv(RESULTS_DIR / "composite_weight_structure.csv", index=False)
    distribution.to_csv(RESULTS_DIR / "surprise_distribution_diagnostics.csv", index=False)
    outliers.to_csv(RESULTS_DIR / "surprise_outlier_quarters.csv", index=False)
    variance_by_period.to_csv(RESULTS_DIR / "factor_variance_by_period.csv", index=False)
    validation.to_csv(RESULTS_DIR / "event_validation_audit.csv", index=False)
    coverage.to_csv(RESULTS_DIR / "event_coverage_by_year_quarter_regime.csv", index=False)
    regime_coverage.to_csv(RESULTS_DIR / "event_coverage_by_regime.csv", index=False)
    crisis_concentration.to_csv(RESULTS_DIR / "crisis_concentration.csv", index=False)
    quarter_density.to_csv(RESULTS_DIR / "quarter_density_diagnostics.csv", index=False)
    info_events.to_csv(RESULTS_DIR / "information_effect_event_flags.csv", index=False)
    info_events.to_csv(DIAGNOSTICS_ROOT / "information_effect_flags.csv", index=False)
    info_quarters.to_csv(RESULTS_DIR / "information_effect_quarter_flags.csv", index=False)
    info_regime_summary.to_csv(RESULTS_DIR / "information_effect_regime_summary.csv", index=False)


def run_pipeline(download: bool = False) -> None:
    ensure_directories()
    if download:
        maybe_download_sources()
    sources = locate_sources()
    write_raw_readme(sources)
    write_source_manifest(sources)
    factors = load_abgmr_factors(sources)
    eampd = load_eampd_workbook(sources)
    events = build_event_level(factors, eampd)
    quarterly = aggregate_quarterly(events)
    monthly = aggregate_monthly(events)
    quarterly_bridge = aggregate_quarterly_bridge(monthly)
    composite, composite_loadings, composite_weights = build_composite_shocks(quarterly)
    weighted = build_weighted_shocks(events)
    quarterly_lpiv = build_lpiv_quarterly_contract(quarterly, quarterly_bridge, composite, weighted)
    policy_frame = make_policy_target_frame(quarterly_lpiv)
    specs = candidate_specs(quarterly, quarterly_bridge, composite, weighted)
    strength_policy_frame = attach_candidate_frames(policy_frame, quarterly_bridge, composite, weighted, specs)
    first_stage = first_stage_diagnostics(policy_frame, quarterly)
    strength_matrix = build_instrument_strength_matrix(strength_policy_frame, specs)
    regime_results = regime_specific_identification(strength_policy_frame, specs, strength_matrix)
    distribution, outliers = distribution_diagnostics(quarterly)
    variance_by_period = factor_variance_by_period(quarterly)
    validation = event_validation_audit(events, factors, eampd)
    coverage, regime_coverage = coverage_tables(events, quarterly)
    crisis_concentration, quarter_density = crisis_clustering_outputs(quarterly, events)
    info_events, info_quarters, info_regime_summary = information_effect_outputs(events)
    write_outputs(
        events,
        quarterly_lpiv,
        monthly,
        quarterly_bridge,
        composite,
        weighted,
        first_stage,
        strength_matrix,
        regime_results,
        composite_loadings,
        composite_weights,
        distribution,
        outliers,
        variance_by_period,
        validation,
        coverage,
        regime_coverage,
        crisis_concentration,
        quarter_density,
        info_events,
        info_quarters,
        info_regime_summary,
    )
    write_aggregation_philosophy()
    write_assessment_memo(
        events,
        quarterly,
        first_stage,
        distribution,
        crisis_concentration,
        validation,
        info_regime_summary,
    )
    write_qe_vs_timing_memo(strength_matrix)
    write_composite_design_doc(strength_matrix, composite_loadings, composite_weights, regime_results)
    write_regime_stability_doc(regime_results)
    write_weighting_design_doc(strength_matrix)
    write_information_screening_doc(info_events, info_regime_summary)
    write_final_identification_recommendation(strength_matrix, regime_results)
    print("ECB monetary surprise build complete.")
    print(f"Event-level data: {PROCESSED_DIR / 'ecb_surprise_event_level.csv'}")
    print(f"Quarterly data: {PROCESSED_DIR / 'ecb_surprise_quarterly.csv'}")
    print(f"Monthly data: {PROCESSED_DIR / 'ecb_surprise_monthly.csv'}")
    print(f"Strength matrix: {DIAGNOSTICS_ROOT / 'instrument_strength_matrix.csv'}")
    print(f"Diagnostics: {RESULTS_DIR}")
    print(f"Assessment memo: {DOCS_DIR / 'ecb_external_instrument_pre_estimation_assessment.md'}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build ECB external-instrument surprise data and diagnostics.")
    parser.add_argument(
        "--download",
        action="store_true",
        help="Download current raw sources if they are not already present. Existing raw files are never overwritten.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    run_pipeline(download=args.download)


if __name__ == "__main__":
    main()
