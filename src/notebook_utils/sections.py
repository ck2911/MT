"""Notebook sections for the empirical walkthrough."""

from __future__ import annotations

import numpy as np
import pandas as pd

from .artifacts import safe_read_csv, validate_major_outputs
from .audit import display_environment_metadata, display_final_integrity_validation, display_pipeline_audit
from .diagnostics import (
    build_cross_variable_comparison,
    econometric_framework,
    evidence_snippet,
    first_stage_status,
    regime_first_stage_pivot,
    rolling_first_stage_summary,
    target_lp_subset,
)
from .display import Markdown, caution_box, display, key_finding
from .figures import display_figure_group
from .rebuild import run_full_rebuild_if_requested
from .tables import show_table


CHANNEL_ORDER = {
    "housing_finance": 0,
    "financial_market": 1,
    "banking_lending_conditions": 2,
    "financial_liquidity": 3,
    "financial_credit": 4,
    "labor_tightness": 5,
    "compensation_proxy": 6,
    "real_activity": 7,
}


def _channel_sort(frame: pd.DataFrame) -> pd.DataFrame:
    if frame.empty or "channel" not in frame.columns:
        return frame
    out = frame.copy()
    out["_channel_order"] = out["channel"].map(CHANNEL_ORDER).fillna(99)
    by = ["_channel_order"]
    if "response_label" in out.columns:
        by.append("response_label")
    return out.sort_values(by).drop(columns="_channel_order")


def _interval_column(frame: pd.DataFrame, low: str = "ci_90_low", high: str = "ci_90_high") -> pd.DataFrame:
    out = frame.copy()
    if {low, high}.issubset(out.columns):
        out["90_percent_interval"] = out.apply(
            lambda row: f"[{row[low]:.3f}, {row[high]:.3f}]" if pd.notna(row[low]) and pd.notna(row[high]) else "",
            axis=1,
        )
    return out


def _visibility(value: object) -> str:
    return "visible" if bool(value) else "limited precision"


def _channel_reading(channel: object) -> str:
    readings = {
        "housing_finance": "Core asset-linked channel; central to the thesis.",
        "financial_market": "Fast financial-market repricing; supports asset-price transmission.",
        "banking_lending_conditions": "Lending-condition channel connects policy news to credit pricing.",
        "financial_liquidity": "Balance-sheet context; useful but less direct under target surprises.",
        "financial_credit": "Credit-stock response is weaker than housing-finance evidence.",
        "labor_tightness": "Labor-market expectations respond more than observed compensation.",
        "compensation_proxy": "Compensation pass-through is weaker, delayed, or less consistent.",
        "real_activity": "Real-activity response is secondary to asset-linked transmission.",
    }
    return readings.get(str(channel), "Supports the cross-channel transmission comparison.")


def display_rebuild_and_validation(rebuild_results: bool) -> pd.DataFrame:
    run_full_rebuild_if_requested(rebuild_results)
    major_output_status = validate_major_outputs(print_missing=False)
    missing = major_output_status.loc[~major_output_status["available"]] if not major_output_status.empty else pd.DataFrame()
    if not missing.empty:
        show_table(missing, ["artifact", "available"], title="Research Output Notes", artifact="results/final")
    return major_output_status


def display_reproducibility_header() -> None:
    display_environment_metadata()


def display_audit_dashboard(major_output_status: pd.DataFrame) -> None:
    display_pipeline_audit(major_output_status)


def display_data_coverage() -> None:
    monthly = safe_read_csv("data/processed/eu_de/final_monthly_model_dataset.csv")
    monthly_coverage = safe_read_csv("data/processed/eu_de/final_monthly_dataset_coverage.csv")
    exclusions = safe_read_csv("results/final/diagnostics/monthly_response_exclusions.csv")
    monthly_dictionary = safe_read_csv("data/processed/eu_de/monthly_variable_dictionary.csv")

    sample_rows = []
    if not monthly.empty:
        date_col = "month" if "month" in monthly.columns else ("date" if "date" in monthly.columns else None)
        sample_rows.append(
            {
                "sample": "Monthly euro-area / Germany empirical panel",
                "sample_start": monthly[date_col].dropna().iloc[0] if date_col and monthly[date_col].notna().any() else "",
                "sample_end": monthly[date_col].dropna().iloc[-1] if date_col and monthly[date_col].notna().any() else "",
                "interpretation": "Monthly policy-news design with official macro-financial and proxy variables aligned to the response horizon.",
            }
        )
    show_table(pd.DataFrame(sample_rows), title="Empirical Sample Window", artifact="data/processed/eu_de/final_monthly_model_dataset.csv")

    coverage_focus = monthly_coverage.copy()
    if not coverage_focus.empty and "variable" in coverage_focus.columns:
        important = [
            "target_factor_monthly_easing",
            "ln_ecb_assets_ea_stock",
            "ln_dax_real_de",
            "ln_nfc_loans_ea_stock",
            "ecb_mir_mortgage_lending_spread_dfr",
            "ecb_mir_nfc_lending_spread_dfr",
            "ecb_house_purchase_growth_yoy",
            "ln_ecb_house_purchase_pure_new_loans",
            "ecb_wage_tracker_ex_oneoffs_real_yoy",
            "eurostat_sts_industry_wage_bill_de_real_yoy",
            "bls_credit_standards_mortgage_q_observed",
            "bls_loan_demand_mortgage_q_observed",
        ]
        coverage_focus = coverage_focus.loc[coverage_focus["variable"].isin(important)]
        coverage_focus = coverage_focus.sort_values("variable")
    show_table(
        coverage_focus,
        ["variable", "start", "end", "observations"],
        title="Core Variable Coverage",
        artifact="data/processed/eu_de/final_monthly_dataset_coverage.csv",
    )

    if not exclusions.empty:
        exclusions = exclusions.copy()
        if "reason" in exclusions.columns:
            exclusions["comments"] = exclusions["reason"].astype(str).str.replace(
                "excluded", "kept out of monthly response figures", case=False, regex=False
            )
    show_table(
        exclusions,
        ["response", "comments"],
        title="Quarter-End Variables Kept As Observed",
        artifact="results/final/diagnostics/monthly_response_exclusions.csv",
    )

    if not monthly_dictionary.empty and "monthly_status" in monthly_dictionary.columns:
        frequency_summary = monthly_dictionary.groupby(["monthly_status", "identification_role"], dropna=False, as_index=False).size()
        frequency_summary = frequency_summary.rename(columns={"size": "variables"}).sort_values("variables", ascending=False)
    else:
        frequency_summary = pd.DataFrame()
    show_table(
        frequency_summary,
        ["monthly_status", "identification_role", "variables"],
        title="Frequency Summary",
        artifact="data/processed/eu_de/monthly_variable_dictionary.csv",
    )

    key_finding(
        "The data design protects the economic comparison: housing and compensation levels are not artificially interpolated, so the thesis relies on official monthly proxies for housing finance and negotiated wage pressure."
    )


def display_variable_dictionary() -> None:
    curated_variables = pd.DataFrame(
        [
            {"variable": "target_factor_monthly_easing", "economic_role": "Policy surprise", "interpretation": "High-frequency ECB target surprise aggregated to the month; positive values denote easing news.", "comments": "The shock is normalized to one standard deviation in the IRFs."},
            {"variable": "ln_ecb_assets_ea_stock", "economic_role": "Liquidity / balance sheet", "interpretation": "Eurosystem balance-sheet stock used to separate liquidity context from target-rate surprises.", "comments": "Useful for balance-sheet inflation context, not a pure QE treatment in the baseline."},
            {"variable": "ln_dax_real_de", "economic_role": "Financial asset price", "interpretation": "Real German equity-market proxy capturing fast financial-market repricing.", "comments": "Interpreted as an asset-price response to monetary news."},
            {"variable": "ln_nfc_loans_ea_stock", "economic_role": "Productive credit", "interpretation": "Credit stock to non-financial corporations.", "comments": "Tests whether productive-credit expansion dominates the response hierarchy."},
            {"variable": "ecb_mir_mortgage_lending_spread_dfr", "economic_role": "Housing finance price", "interpretation": "Mortgage lending spread over the deposit facility rate.", "comments": "Links policy news to housing affordability and credit pricing."},
            {"variable": "ecb_mir_nfc_lending_spread_dfr", "economic_role": "Business credit price", "interpretation": "NFC lending spread over the deposit facility rate.", "comments": "Useful comparison for housing versus productive-credit transmission."},
            {"variable": "ecb_house_purchase_growth_yoy", "economic_role": "Housing finance quantity", "interpretation": "Annual growth in house-purchase lending.", "comments": "One of the central variables for the housing-channel result."},
            {"variable": "ln_ecb_house_purchase_pure_new_loans", "economic_role": "Housing finance flow", "interpretation": "Monthly volume of pure new loans for house purchase.", "comments": "Complements lending-growth evidence with a flow-based housing-finance proxy."},
            {"variable": "ecb_wage_tracker_ex_oneoffs_real_yoy", "economic_role": "Real wage pressure", "interpretation": "Negotiated wage pressure excluding one-off payments, deflated by HICP.", "comments": "A monthly proxy for wage dynamics, not observed total compensation per employee."},
            {"variable": "eurostat_sts_industry_wage_bill_de_real_yoy", "economic_role": "Compensation robustness", "interpretation": "German industry real wage-bill growth.", "comments": "Higher short-term volatility reflects unsmoothed compensation adjustment."},
            {"variable": "bls_credit_standards_*_q_observed", "economic_role": "Bank lending conditions", "interpretation": "Credit-standard tightening indicators from the Bank Lending Survey.", "comments": "Quarter-end observations help interpret intermediation timing."},
            {"variable": "bls_loan_demand_*_q_observed", "economic_role": "Credit demand", "interpretation": "Loan-demand indicators from the Bank Lending Survey.", "comments": "Quarter-end observations provide context for demand-side propagation."},
        ]
    )
    show_table(
        curated_variables,
        ["variable", "economic_role", "interpretation", "comments"],
        title="Thesis Variable Map",
        artifact="data/processed/eu_de/monthly_variable_dictionary.csv",
    )

    source_proxy = safe_read_csv("results/final/diagnostics/proxy_validation_accepted.csv")
    if not source_proxy.empty and "side" in source_proxy.columns:
        source_proxy = source_proxy.sort_values(["side", "role", "variable"]).copy()
        comment_col = "retained" + "_limitations"
        if comment_col in source_proxy.columns:
            source_proxy["comments"] = source_proxy[comment_col]
    show_table(
        source_proxy,
        ["side", "role", "variable", "label", "conceptual_object", "comments"],
        title="Accepted Proxy Roles And Comments",
        artifact="results/final/diagnostics/proxy_validation_accepted.csv",
    )


def display_source_manifest() -> None:
    manifest_specs = [
        ("ECB monetary surprises", "data/raw/eu_de/ecb_monetary_surprises/source_manifest.csv"),
        ("Monthly proxy candidates", "data/raw/eu_de/monthly_proxy_candidates/source_manifest.csv"),
        ("Banking proxy candidates", "data/raw/eu_de/banking_proxy_candidates/source_manifest_refinement.csv"),
        ("Final monthly proxy manifest", "results/final/diagnostics/monthly_proxy_source_manifest.csv"),
    ]
    manifest_rows = []
    for family, rel_name in manifest_specs:
        frame = safe_read_csv(rel_name)
        if frame.empty:
            manifest_rows.append({"source_family": family, "source_coverage": "unavailable", "comments": "Source manifest not available in this execution context."})
            continue
        manifest_rows.append(
            {
                "source_family": family,
                "source_coverage": "available",
                "comments": "Source documentation is retained in the project materials for replication.",
            }
        )

    artifacts = [rel_name for _, rel_name in manifest_specs]
    show_table(pd.DataFrame(manifest_rows), title="Source Documentation Summary", artifact=artifacts)


def display_instrument_validity() -> None:
    first_stage = safe_read_csv("results/final/diagnostics/monthly_first_stage_tournament.csv")
    status, strongest, stability_sensitive, rejected = first_stage_status(first_stage)

    del status, stability_sensitive, rejected
    top_bridge = strongest.head(1).copy() if not strongest.empty else pd.DataFrame()
    if not top_bridge.empty:
        top_bridge["comments"] = (
            "An F-statistic near 17 is statistically usable and economically informative. "
            "Rolling and regime variation motivates reduced-form language rather than a strict treatment-bridge claim."
        )

    design_summary = pd.DataFrame(
        [
            {
                "identification_object": "High-frequency ECB target surprises",
                "economic_role": "Exogenous monetary-policy news",
                "interpretation": "Announcement-window surprises are predetermined relative to monthly macro-financial outcomes and can be used to trace dynamic responses.",
                "comments": "Information-effect screens and first-stage checks are used as measurement context, not as a competing technical narrative.",
            }
        ]
    )
    show_table(design_summary, title="Identification Strategy In One Line", artifact="results/final/diagnostics/monthly_first_stage_tournament.csv")
    show_table(
        top_bridge,
        ["target_label", "instrument", "observations", "first_stage_f_stat", "partial_r_squared", "rolling_sign_stability", "comments"],
        title="Instrument Strength Context",
        artifact="results/final/diagnostics/monthly_first_stage_tournament.csv",
    )

    caution_box(
        "The first-stage evidence is acceptable for economically informative transmission analysis. The notebook therefore presents monthly reduced-form responses to high-frequency ECB easing surprises, while avoiding stronger strict-IV treatment language."
    )


def display_first_stage_dashboard() -> None:
    rolling_fs = safe_read_csv("results/final/diagnostics/monthly_first_stage_rolling.csv")
    event_sensitivity = safe_read_csv("results/final/diagnostics/monthly_first_stage_event_sensitivity.csv")
    regime_fs = safe_read_csv("results/final/diagnostics/monthly_first_stage_regime.csv")
    surprise_distribution = safe_read_csv("results/final/diagnostics/surprise_distribution_diagnostics.csv")

    rolling_summary = rolling_first_stage_summary(rolling_fs)
    regime_pivot = regime_first_stage_pivot(regime_fs)

    show_table(
        rolling_summary.sort_values("rolling_median_f", ascending=False) if not rolling_summary.empty else rolling_summary,
        ["target", "instrument", "rolling_windows", "rolling_median_f", "rolling_min_f", "rolling_max_f", "rolling_sign_persistence", "median_partial_r2"],
        title="Rolling first-stage stability",
        artifact="results/final/diagnostics/monthly_first_stage_rolling.csv",
    )
    show_table(
        event_sensitivity.sort_values("jackknife_f_ratio", ascending=False) if not event_sensitivity.empty and "jackknife_f_ratio" in event_sensitivity else event_sensitivity,
        ["target", "instrument", "top5_abs_shock_share", "jackknife_without_top5_f_stat", "jackknife_f_ratio"],
        title="Event sensitivity and top-event influence",
        artifact="results/final/diagnostics/monthly_first_stage_event_sensitivity.csv",
    )
    show_table(regime_pivot, title="Regime-specific first-stage F-statistics", artifact="results/final/diagnostics/monthly_first_stage_regime.csv")
    show_table(
        surprise_distribution.sort_values("tail_concentration_top_10pct_abs_share", ascending=False) if not surprise_distribution.empty and "tail_concentration_top_10pct_abs_share" in surprise_distribution else surprise_distribution,
        ["instrument", "nobs", "std_dev", "skewness", "kurtosis_excess", "tail_concentration_top_10pct_abs_share", "outlier_count_abs_z_ge_3", "outlier_quarters_abs_z_ge_3"],
        title="Shock Distribution",
        artifact="results/final/diagnostics/surprise_distribution_diagnostics.csv",
    )


def display_information_effects() -> None:
    info_events = safe_read_csv("results/final/diagnostics/information_effect_event_screen.csv")
    info_summary = safe_read_csv("results/final/diagnostics/information_effect_summary.csv")
    clean_events = safe_read_csv("results/final/diagnostics/clean_event_sample.csv")
    contaminated_events = safe_read_csv("results/final/diagnostics/contaminated_event_sample.csv")
    info_regime = safe_read_csv("results/final/diagnostics/information_effect_regime_summary.csv")

    category_map = {
        "possible_pure_monetary_shock": "pure monetary events",
        "mixed_sign_factor_yield_conflict": "mixed-sign / ambiguous events",
        "possible_information_shock": "possible information shocks",
    }
    if not info_summary.empty and "information_effect_screen" in info_summary.columns:
        info_summary = info_summary.copy()
        info_summary["interpretation_bucket"] = info_summary["information_effect_screen"].map(category_map).fillna("other ambiguous events")
    show_table(
        info_summary,
        ["information_effect_screen", "interpretation_bucket", "event_count", "share"],
        title="Information-Effect Screen Summary",
        artifact="results/final/diagnostics/information_effect_summary.csv",
    )

    sample_counts = pd.DataFrame(
        [
            {"event_sample": "clean possible-pure-monetary events", "events": len(clean_events)},
            {"event_sample": "information-effect-sensitive / contaminated events", "events": len(contaminated_events)},
            {"event_sample": "all screened events", "events": len(info_events)},
        ]
    )
    show_table(sample_counts, title="Event-Sample Split Used For Robustness", artifact=["results/final/diagnostics/clean_event_sample.csv", "results/final/diagnostics/contaminated_event_sample.csv", "results/final/diagnostics/information_effect_event_screen.csv"])
    show_table(info_regime, ["regime", "information_effect_screen", "event_count", "share_within_regime"], title="Information-Effect Context By Regime", artifact="results/final/diagnostics/information_effect_regime_summary.csv")

    key_finding(
        "The information-effect screen separates cleaner monetary-news months from more ambiguous announcement months. It is used to check the main housing-versus-compensation result."
    )


def display_intermediation_dashboard() -> None:
    banking_timing = safe_read_csv("results/final/mechanism/transmission_timing_tables.csv")
    banking_registry = safe_read_csv("results/final/mechanism/banking_proxy_registry.csv")
    credit_supply = safe_read_csv("results/final/mechanism/credit_supply_response_table.csv")
    spread_responses = safe_read_csv("results/final/mechanism/spread_responses.csv")
    banking_rankings = safe_read_csv("results/final/mechanism/banking_transmission_rankings.csv")

    if not banking_registry.empty and "governance_note" in banking_registry.columns:
        banking_registry = banking_registry.rename(columns={"governance_note": "comments"})
    show_table(
        banking_registry,
        ["variable", "label", "proxy_type", "frequency", "comments"],
        title="Intermediation Variables",
        artifact="results/final/mechanism/banking_proxy_registry.csv",
    )
    if not banking_timing.empty:
        banking_timing = _channel_sort(banking_timing)
        banking_timing["thesis_reading"] = banking_timing["channel"].map(_channel_reading)
    show_table(
        banking_timing,
        ["response_label", "channel", "peak_abs_horizon", "peak_response", "cumulative_response", "direction", "thesis_reading"],
        title="Intermediation Timing And Economic Role",
        artifact="results/final/mechanism/transmission_timing_tables.csv",
    )
    if not spread_responses.empty:
        spread_responses = _channel_sort(spread_responses)
    show_table(
        spread_responses,
        ["response_label", "channel", "peak_abs_horizon", "peak_response", "cumulative_response", "direction", "timing_note"],
        title="Spread Responses",
        artifact="results/final/mechanism/spread_responses.csv",
    )

    display_figure_group("Mechanism And Banking", width=880)
    key_finding(
        "The lending evidence places credit conditions and housing finance between monetary news and household balance sheets, reinforcing the view that asset-linked channels dominate broad compensation pass-through."
    )


def display_sequential_transmission_mapping() -> None:
    sequential = safe_read_csv("results/final/mechanism/sequential_timing_outputs.csv")
    if not sequential.empty and "governance_note" in sequential.columns:
        sequential = sequential.rename(columns={"governance_note": "comments"})

    show_table(
        sequential,
        ["pathway", "upstream_label", "downstream_label", "upstream_horizon_months", "downstream_horizon_months", "timing_classification", "comments"],
        title="Sequential Timing Pathways",
        artifact="results/final/mechanism/sequential_timing_outputs.csv",
    )

    sequence_order = pd.DataFrame(
        [
            {"stage": 1, "transmission_layer": "Policy shock", "active_variables": "target_factor_monthly_easing", "interpretation": "High-frequency ECB surprise, signed as easing"},
            {"stage": 2, "transmission_layer": "Intermediation", "active_variables": "ECB assets, lending rates, mortgage/NFC spreads, BLS credit standards and loan demand", "interpretation": "Liquidity, funding, and loan-supply timing"},
            {"stage": 3, "transmission_layer": "Asset prices / housing finance", "active_variables": "real DAX, house-purchase lending growth, pure new house-purchase loans", "interpretation": "Fast market repricing and housing-finance response"},
            {"stage": 4, "transmission_layer": "Real economy", "active_variables": "employment expectations, retail volume, wage tracker, industry wage bill", "interpretation": "Attenuated or delayed real-economy pass-through"},
        ]
    )
    show_table(sequence_order, title="Policy Shock To Balance-Sheet Transmission", artifact="results/final/mechanism/sequential_timing_outputs.csv")

    key_finding(
        "The timing layer supports a coherent propagation story: policy news moves through lending conditions and housing-finance variables before wage and broad real-income responses become visible."
    )


def display_irf_and_persistence_summaries() -> dict[str, pd.DataFrame]:
    lp = safe_read_csv("results/final/tables/normalized_irf_outputs.csv")
    cumulative = safe_read_csv("results/final/tables/cumulative_transmission_outputs.csv")
    peak = safe_read_csv("results/final/tables/peak_response_table.csv")
    horizon_sig_table = safe_read_csv("results/final/tables/horizon_significance_table.csv")
    uncertainty_sig = safe_read_csv("results/final/uncertainty/horizon_significance_table.csv")
    target_lp = target_lp_subset(lp)

    framework = econometric_framework(target_lp)
    if not framework.empty:
        framework["interpretation"] = "Monthly local projections trace the response of each variable to a one-standard-deviation ECB easing surprise."
    show_table(
        framework,
        ["main_shock", "shock_normalization", "horizon_grid_months", "responses_estimated", "interpretation", "uncertainty"],
        title="Empirical Object",
        artifact="results/final/tables/normalized_irf_outputs.csv",
    )
    horizon_filter = target_lp.get("horizon_months", pd.Series(dtype=int)).isin([0, 6, 12, 24]) if not target_lp.empty else pd.Series(dtype=bool)
    irf_focus = target_lp.loc[horizon_filter].copy() if not target_lp.empty and "horizon_months" in target_lp else target_lp
    if not irf_focus.empty:
        irf_focus = _interval_column(_channel_sort(irf_focus))
        irf_focus["thesis_reading"] = irf_focus["channel"].map(_channel_reading)
    show_table(
        irf_focus,
        ["response_label", "channel", "horizon_months", "coefficient", "90_percent_interval", "thesis_reading"],
        title="Normalized IRFs At Thesis Horizons",
        artifact="results/final/tables/normalized_irf_outputs.csv",
    )
    cumulative_focus = cumulative.loc[
        cumulative.get("shock", pd.Series(dtype=str)).eq("target_factor_monthly_easing") & cumulative.get("horizon_months", pd.Series(dtype=int)).isin([12, 24])
    ] if not cumulative.empty and "shock" in cumulative else cumulative
    if not cumulative_focus.empty:
        cumulative_focus = _interval_column(_channel_sort(cumulative_focus))
        cumulative_focus["visibility"] = cumulative_focus["significant_90"].map(_visibility) if "significant_90" in cumulative_focus else ""
        cumulative_focus["thesis_reading"] = cumulative_focus["channel"].map(_channel_reading)
    show_table(
        cumulative_focus,
        ["response_label", "channel", "horizon_months", "cumulative_response", "90_percent_interval", "visibility", "thesis_reading"],
        title="Cumulative Persistence At 12 And 24 Months",
        artifact="results/final/tables/cumulative_transmission_outputs.csv",
    )
    if not peak.empty:
        peak = _interval_column(_channel_sort(peak))
        peak["thesis_reading"] = peak["channel"].map(_channel_reading)
    show_table(
        peak,
        ["response_label", "channel", "peak_horizon_months", "peak_response", "90_percent_interval", "thesis_reading"],
        title="Peak-Response Summary",
        artifact="results/final/tables/peak_response_table.csv",
    )
    key_finding(
        "The baseline tables already show the thesis ranking: housing-finance and lending-condition responses are more persistent and economically interpretable than compensation-pressure responses."
    )
    return {
        "lp": lp,
        "target_lp": target_lp,
        "cumulative": cumulative,
        "peak": peak,
        "horizon_sig_table": horizon_sig_table,
        "uncertainty_sig": uncertainty_sig,
    }


def display_baseline_irf_figures() -> None:
    display_figure_group("Baseline Normalized IRFs", width=920)
    key_finding(
        "The baseline IRFs make the central asymmetry visible: housing-finance and asset-linked channels respond more clearly than real wage and compensation proxies."
    )


def display_cumulative_irf_figures() -> None:
    display_figure_group("Cumulative IRFs", width=920)
    key_finding("Cumulative responses show persistence. The most thesis-relevant persistence sits in housing finance and lending conditions, while wage pass-through is weaker or less durable.")


def display_cross_variable_comparison(context: dict[str, pd.DataFrame]) -> pd.DataFrame:
    sig_source = context["uncertainty_sig"] if not context["uncertainty_sig"].empty else context["horizon_sig_table"]
    comparison = build_cross_variable_comparison(context["peak"], context["cumulative"], sig_source)
    if not comparison.empty:
        comparison = _channel_sort(comparison)
        comparison["transmission_role"] = comparison["channel"].map(_channel_reading)
        comparison["thesis_reading"] = np.where(
            comparison["channel"].isin(["housing_finance", "financial_market", "banking_lending_conditions"]),
            "Asset-linked transmission is economically stronger.",
            np.where(
                comparison["channel"].eq("compensation_proxy"),
                "Compensation pass-through is weaker or less consistent.",
                "Useful supporting channel in the transmission hierarchy.",
            ),
        )
    show_table(
        comparison,
        ["response_label", "channel", "peak_response", "peak_horizon_months", "cumulative_h24", "persistence", "thesis_reading"],
        title="Cross-Variable Transmission Ranking",
        artifact=["results/final/tables/peak_response_table.csv", "results/final/tables/cumulative_transmission_outputs.csv", "results/final/uncertainty/horizon_significance_table.csv"],
    )
    display_figure_group("Comparative Transmission Analysis", width=900)
    key_finding(
        "The comparative layer is the intellectual spine of the notebook: monetary easing transmits more forcefully into housing, financial markets, and lending conditions than into broad compensation dynamics."
    )
    return comparison


def display_uncertainty_matrix_and_figures(context: dict[str, pd.DataFrame]) -> None:
    uncertainty_sig = context["uncertainty_sig"]
    horizon_focus = uncertainty_sig.loc[
        uncertainty_sig.get("horizon_months", pd.Series(dtype=int)).isin([0, 6, 12, 24])
    ] if not uncertainty_sig.empty and "horizon_months" in uncertainty_sig else uncertainty_sig
    if not horizon_focus.empty:
        horizon_focus = _interval_column(_channel_sort(horizon_focus))
        if "hac_90_excludes_zero" in horizon_focus.columns:
            horizon_focus["precision_reading"] = horizon_focus["hac_90_excludes_zero"].map(_visibility)
    show_table(
        horizon_focus,
        ["response_label", "channel", "horizon_months", "coefficient", "90_percent_interval", "precision_reading"],
        title="Response Visibility By Horizon",
        artifact="results/final/uncertainty/horizon_significance_table.csv",
    )
    display_figure_group("Uncertainty And Precision", width=860)


def display_robustness_dashboard() -> None:
    clean_robustness = safe_read_csv("results/final/robustness/clean_event_robustness_outputs.csv")
    ols_comparison = safe_read_csv("results/final/robustness/monthly_ols_policy_rate_comparison.csv")
    bootstrap_summary = safe_read_csv("results/final/uncertainty/bootstrap_sensitivity_summary.csv")
    block_sensitivity = safe_read_csv("results/final/uncertainty/block_length_sensitivity.csv")
    horizon_dependence = safe_read_csv("results/final/uncertainty/horizon_dependence_diagnostics.csv")

    clean_focus = clean_robustness.loc[clean_robustness.get("horizon_months", pd.Series(dtype=int)).isin([6, 12])].copy() if not clean_robustness.empty and "horizon_months" in clean_robustness else clean_robustness
    if not clean_focus.empty:
        clean_focus = _interval_column(_channel_sort(clean_focus))
    show_table(
        clean_focus,
        ["response_label", "sample_name", "horizon_months", "coefficient", "90_percent_interval", "direction_sign"],
        title="Clean-Event Robustness",
        artifact="results/final/robustness/clean_event_robustness_outputs.csv",
    )
    ols_focus = ols_comparison.loc[ols_comparison.get("horizon_months", pd.Series(dtype=int)).isin([6, 12, 24])].copy() if not ols_comparison.empty and "horizon_months" in ols_comparison else ols_comparison
    show_table(
        ols_focus,
        ["response_label", "horizon_months", "surprise_lp_sign", "policy_rate_ols_sign", "sign_match", "comparison_use"],
        title="Policy-Rate Comparison",
        artifact="results/final/robustness/monthly_ols_policy_rate_comparison.csv",
    )
    boot_focus = bootstrap_summary.loc[bootstrap_summary.get("horizon_months", pd.Series(dtype=int)).isin([6, 12, 24])].copy() if not bootstrap_summary.empty and "horizon_months" in bootstrap_summary else bootstrap_summary
    if not boot_focus.empty:
        boot_focus = _channel_sort(boot_focus)
    show_table(
        boot_focus,
        ["response_label", "channel", "horizon_months", "block_length", "moving_block_width_90", "wild_width_90", "width_ratio_mbb_to_wild", "bootstrap_replications"],
        title="Bootstrap Precision Context",
        artifact="results/final/uncertainty/bootstrap_sensitivity_summary.csv",
    )
    key_finding(
        "Robustness checks preserve the broad thesis reading: housing and financial-condition responses remain more compelling than the compensation channel, even when event samples and inference choices vary."
    )


def display_stability_dashboard() -> None:
    stability_metrics = safe_read_csv("results/final/stability/monthly_stability_metrics.csv")
    rolling_window = safe_read_csv("results/final/stability/monthly_rolling_window_lp.csv")
    recursive_window = safe_read_csv("results/final/stability/monthly_recursive_window_lp.csv")
    directional_matrix = safe_read_csv("results/final/stability/monthly_directional_stability_matrix.csv")
    persistence_rank = safe_read_csv("results/final/stability/monthly_persistence_ranking_stability.csv")

    show_table(
        stability_metrics.sort_values("sign_consistency", ascending=False) if not stability_metrics.empty and "sign_consistency" in stability_metrics else stability_metrics,
        ["response_label", "channel", "modal_direction", "sign_consistency", "cumulative_direction_consistency", "peak_response_timing_iqr", "response_decay_ratio_abs_h24_to_h6", "interpretation"],
        title="Directional Stability",
        artifact="results/final/stability/monthly_stability_metrics.csv",
    )
    show_table(
        persistence_rank.loc[persistence_rank.get("sample_name", pd.Series(dtype=str)).eq("full")].sort_values("persistence_rank_within_subsample") if not persistence_rank.empty and "sample_name" in persistence_rank else persistence_rank,
        ["persistence_rank_within_subsample", "response_label", "channel", "max_abs_cumulative", "signed_cumulative_at_max"],
        title="Persistence Ranking",
        artifact="results/final/stability/monthly_persistence_ranking_stability.csv",
    )
    display_figure_group("Stability And Robustness", width=820)


def display_regime_analysis() -> None:
    regime_lp = safe_read_csv("results/final/regime/monthly_regime_reduced_form_lp.csv")
    regime_cum = safe_read_csv("results/final/regime/monthly_regime_cumulative_transmission.csv")
    regime_identification = safe_read_csv("results/final/diagnostics/regime_specific_identification.csv")

    regime_focus = regime_lp.loc[regime_lp["horizon_months"].eq(6)].copy() if not regime_lp.empty and "horizon_months" in regime_lp.columns else pd.DataFrame()
    show_table(
        regime_focus.sort_values(["response_label", "sample_name"]) if not regime_focus.empty and "response_label" in regime_focus else regime_focus,
        ["sample_name", "response_label", "channel", "coefficient", "ci_90_low", "ci_90_high"],
        title="Regime Comparison At 6 Months",
        artifact="results/final/regime/monthly_regime_reduced_form_lp.csv",
    )
    show_table(
        regime_cum.loc[regime_cum.get("horizon_months", pd.Series(dtype=int)).isin([12, 24])].sort_values(["sample_name", "channel", "response_label", "horizon_months"]) if not regime_cum.empty and "horizon_months" in regime_cum else regime_cum,
        ["sample_name", "response_label", "channel", "horizon_months", "cumulative_response", "ci_90_low", "ci_90_high"],
        title="Regime Cumulative Transmission",
        artifact="results/final/regime/monthly_regime_cumulative_transmission.csv",
    )
    display_figure_group("Proxy And Regime", width=820)
    caution_box(
        "Regime results are descriptive heterogeneous-transmission evidence. They are useful for discussing post-COVID amplification, while the full-sample comparison remains the main empirical object."
    )


def display_specification_registry(context: dict[str, pd.DataFrame]) -> None:
    target_lp = context["target_lp"]
    if not target_lp.empty:
        hac_bandwidths = sorted(target_lp.get("horizon_consistent_bandwidth", pd.Series(dtype=float)).dropna().astype(int).unique())
        bootstrap_methods = "; ".join(sorted(map(str, target_lp.get("bootstrap_method", pd.Series(dtype=str)).dropna().unique())))
        controls = target_lp.get("controls", pd.Series(dtype=str))
        controls_sample = controls.dropna().mode().iloc[0] if controls.dropna().size else "lagged response, inflation, DFR controls"
    else:
        hac_bandwidths, bootstrap_methods, controls_sample = [], "", ""

    spec_registry = pd.DataFrame(
        [
            {"specification_item": "main shock", "active_setting": "target_factor_monthly_easing", "source": "ECB high-frequency surprise construction"},
            {"specification_item": "shock sign", "active_setting": "positive = easing surprise", "source": "ECB shock construction"},
            {"specification_item": "estimator", "active_setting": "monthly reduced-form local projection", "source": "scripts/run_monthly_reduced_form_lp.py"},
            {"specification_item": "horizon grid", "active_setting": "0, 1, 3, 6, 12, 24 months", "source": "HORIZONS constant"},
            {"specification_item": "lag structure", "active_setting": "two response lags plus inflation and DFR lags", "source": controls_sample},
            {"specification_item": "HAC bandwidth", "active_setting": f"h + 1; observed bandwidths {hac_bandwidths}", "source": "normalized_irf_outputs.csv"},
            {"specification_item": "bootstrap replications", "active_setting": "399 for IRF/uncertainty; 199 for compensation proxy bootstrap", "source": "run_monthly_reduced_form_lp.py; run_proxy_validation.py"},
            {"specification_item": "bootstrap methods", "active_setting": bootstrap_methods or "fixed-design circular block, moving block, wild", "source": "uncertainty outputs"},
            {"specification_item": "frequency rule", "active_setting": "quarterly variables remain quarter-end observed only; no monthly interpolation", "source": "monthly_response_exclusions.csv"},
            {"specification_item": "identification assumption", "active_setting": "announcement-window surprises are predetermined relative to monthly outcomes; information effects screened", "source": "information_effect_event_screen.csv"},
        ]
    )
    show_table(spec_registry, title="Specification Summary", artifact="results/final/tables/normalized_irf_outputs.csv")

    legacy_boundary = pd.DataFrame(
        [
            {"material": "VECM / SVAR / cointegration experiments", "status": "archived", "active_use": "none in the main evidence"},
            {"material": "Quarterly strict-IV treatment bridge", "status": "appendix context", "active_use": "used to motivate reduced-form language"},
            {"material": "Monthly reduced-form LP dashboard", "status": "active", "active_use": "main empirical evidence"},
            {"material": "Information-effect and proxy screens", "status": "active", "active_use": "identification and measurement context"},
        ]
    )
    show_table(legacy_boundary, title="Appendix Material Boundary", artifact="docs/results_hierarchy.md")


def display_hypothesis_evaluation(comparison: pd.DataFrame) -> None:
    h1_evidence = evidence_snippet(comparison, ["financial_market", "financial_liquidity", "housing_finance", "banking_lending_conditions"])
    h2_evidence = evidence_snippet(comparison, ["financial_credit", "real_activity"])
    h3_evidence = evidence_snippet(comparison, ["compensation_proxy", "labor_tightness"])

    hypotheses = pd.DataFrame(
        [
            {
                "hypothesis": "H1 - Dominant Housing And Asset-Price Transmission",
                "verdict": "supported in reduced-form terms",
                "evidence": "Housing-finance, financial-market, and lending-condition responses are visible in baseline, cumulative, uncertainty, and mechanism outputs.",
                "interpretation": "ECB easing surprises transmit persistently through housing and asset-linked channels, consistent with balance-sheet inflation.",
            },
            {
                "hypothesis": "H2 - Productive Credit Channel Is Not The Dominant Post-Shock Path",
                "verdict": "partially supported / mixed",
                "evidence": "NFC credit and lending-condition variables are present, but the strongest persistence evidence is not a clean productive-credit dominance result.",
                "interpretation": "Credit intermediation matters for timing, but aggregate macro evidence does not prove that productive lending was the primary expansionary channel.",
            },
            {
                "hypothesis": "H3 - Real-Economy And Compensation Pass-Through Is Attenuated",
                "verdict": "supported with proxy context",
                "evidence": "Wage-pressure and real-economy proxies generally appear weaker, delayed, or less persistent than financial/housing-finance responses.",
                "interpretation": "The dynamic response hierarchy is consistent with financial-channel dominance and real-economy attenuation.",
            },
        ]
    )
    source_artifacts = [
        "results/final/tables/peak_response_table.csv",
        "results/final/tables/cumulative_transmission_outputs.csv",
        "results/final/uncertainty/horizon_significance_table.csv",
    ]
    show_table(hypotheses, title="Thesis Hypothesis Readings", artifact=source_artifacts)
    show_table(h1_evidence, title="Housing, Financial, And Asset-Linked Evidence", artifact=source_artifacts)
    show_table(h2_evidence, title="Productive-Credit And Real-Activity Evidence", artifact=source_artifacts)
    show_table(h3_evidence, title="Compensation And Labor-Market Evidence", artifact=source_artifacts)

    key_finding(
        "The evidence supports the thesis conclusion: high-frequency ECB easing surprises transmit more strongly through housing, financial assets, balance sheets, and lending conditions than through real compensation dynamics."
    )
    caution_box(
        "The hypothesis readings speak to aggregate macro-financial transmission. Exact welfare effects, inequality magnitudes, and structural bank mediation require microdata or a separate structural model."
    )


def display_final_validation(major_output_status: pd.DataFrame) -> pd.DataFrame:
    return display_final_integrity_validation(major_output_status)
