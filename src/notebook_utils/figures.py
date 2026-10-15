"""Figure lookup and display helpers."""

from __future__ import annotations

import base64
import html
import mimetypes
from pathlib import Path

from .artifacts import warn_missing
from .display import HTML, Markdown, display
from .paths import artifact_path, rel

FIGURE_GROUPS = {
    "Identification Diagnostics": [
        "results/final/figures/instrument_quarter_density.png",
        "results/final/figures/instrument_regime_histograms.png",
        "results/final/figures/quarterly_surprise_rolling_variance.png",
    ],
    "Baseline Normalized IRFs": [
        "results/final/figures/baseline/monthly_irf_ln_ecb_assets_ea_stock.png",
        "results/final/figures/baseline/monthly_irf_ln_dax_real_de.png",
        "results/final/figures/baseline/monthly_irf_ln_nfc_loans_ea_stock.png",
        "results/final/figures/baseline/monthly_irf_ecb_mir_mortgage_lending_spread_dfr.png",
        "results/final/figures/baseline/monthly_irf_ecb_mir_nfc_lending_spread_dfr.png",
        "results/final/figures/baseline/monthly_irf_ecb_house_purchase_growth_yoy.png",
        "results/final/figures/baseline/monthly_irf_ln_ecb_house_purchase_pure_new_loans.png",
        "results/final/figures/baseline/monthly_irf_ecb_wage_tracker_ex_oneoffs_real_yoy.png",
        "results/final/figures/baseline/monthly_irf_eurostat_sts_industry_wage_bill_de_real_yoy.png",
        "results/final/figures/baseline/monthly_irf_eurostat_ecfin_eei_ea20.png",
    ],
    "Comparative Transmission Analysis": [
        "results/final/figures/enhancement/comparative_irf_panel.png",
        "results/final/figures/enhancement/horizon_durability_matrix.png",
        "results/final/figures/enhancement/sign_persistence_map.png",
        "results/final/figures/enhancement/conceptual_affordability_transmission_flow.png",
    ],
    "Cumulative IRFs": [
        "results/final/figures/cumulative/cumulative_interval_ln_ecb_assets_ea_stock.png",
        "results/final/figures/cumulative/cumulative_interval_ln_dax_real_de.png",
        "results/final/figures/cumulative/cumulative_interval_ln_nfc_loans_ea_stock.png",
        "results/final/figures/cumulative/cumulative_interval_ecb_mir_mortgage_lending_spread_dfr.png",
        "results/final/figures/cumulative/cumulative_interval_ecb_mir_nfc_lending_spread_dfr.png",
        "results/final/figures/cumulative/cumulative_interval_ecb_house_purchase_growth_yoy.png",
        "results/final/figures/cumulative/cumulative_interval_ln_ecb_house_purchase_pure_new_loans.png",
        "results/final/figures/cumulative/cumulative_interval_ecb_wage_tracker_ex_oneoffs_real_yoy.png",
        "results/final/figures/cumulative/cumulative_interval_eurostat_sts_industry_wage_bill_de_real_yoy.png",
        "results/final/figures/cumulative/cumulative_interval_eurostat_ecfin_eei_ea20.png",
    ],
    "Uncertainty And Precision": [
        "results/final/figures/uncertainty/significance_heatmap.png",
        "results/final/figures/uncertainty/uncertainty_width_comparison.png",
        "results/final/figures/uncertainty/uncertainty_fan_ln_ecb_assets_ea_stock.png",
        "results/final/figures/uncertainty/uncertainty_fan_ln_dax_real_de.png",
        "results/final/figures/uncertainty/uncertainty_fan_ln_nfc_loans_ea_stock.png",
        "results/final/figures/uncertainty/uncertainty_fan_ecb_mir_mortgage_lending_spread_dfr.png",
        "results/final/figures/uncertainty/uncertainty_fan_ecb_mir_nfc_lending_spread_dfr.png",
        "results/final/figures/uncertainty/uncertainty_fan_ecb_house_purchase_growth_yoy.png",
        "results/final/figures/uncertainty/uncertainty_fan_ln_ecb_house_purchase_pure_new_loans.png",
        "results/final/figures/uncertainty/uncertainty_fan_ecb_wage_tracker_ex_oneoffs_real_yoy.png",
        "results/final/figures/uncertainty/uncertainty_fan_eurostat_sts_industry_wage_bill_de_real_yoy.png",
        "results/final/figures/uncertainty/uncertainty_fan_eurostat_ecfin_eei_ea20.png",
    ],
    "Mechanism And Banking": [
        "results/final/figures/banking/banking_peak_timing.png",
        "results/final/figures/mechanism/sequential_timing_response_map.png",
    ],
    "Stability And Robustness": [
        "results/final/figures/enhancement/robustness_summary.png",
        "results/final/figures/enhancement/robustness_consistency_matrix.png",
        "results/final/figures/stability/clean_vs_contaminated_h6.png",
        "results/final/figures/stability/persistence_confidence_matrix.png",
        "results/final/figures/stability/rolling_stability_h6_ecb_house_purchase_growth_yoy.png",
        "results/final/figures/stability/rolling_stability_h6_ln_ecb_house_purchase_pure_new_loans.png",
        "results/final/figures/stability/rolling_stability_h6_ecb_wage_tracker_ex_oneoffs_real_yoy.png",
        "results/final/figures/stability/rolling_stability_h6_ln_dax_real_de.png",
    ],
    "Proxy And Regime": [
        "results/final/figures/compensation/compensation_proxy_rankings.png",
        "results/final/figures/regimes/regime_h6_response_comparison.png",
    ],
}

RESPONSE_LABELS = {
    "ln_ecb_assets_ea_stock": "ECB assets",
    "ln_dax_real_de": "real DAX",
    "ln_nfc_loans_ea_stock": "NFC credit",
    "ln_hh_loans_ea_stock": "household credit",
    "ecb_mir_mortgage_lending_spread_dfr": "mortgage lending spread",
    "ecb_mir_nfc_lending_spread_dfr": "NFC lending spread",
    "ecb_mir_mortgage_lending_rate": "mortgage lending rate",
    "ecb_mir_nfc_lending_rate": "NFC lending rate",
    "ecb_house_purchase_growth_yoy": "house-purchase lending growth",
    "ln_ecb_house_purchase_pure_new_loans": "pure new house-purchase loans",
    "ecb_wage_tracker_ex_oneoffs_real_yoy": "real wage tracker excluding one-offs",
    "eurostat_sts_industry_wage_bill_de_real_yoy": "German industry real wage bill growth",
    "eurostat_ecfin_eei_ea20": "employment expectations",
}

BASELINE_INTERPRETATIONS = {
    "ln_ecb_assets_ea_stock": "The balance-sheet response is modest under target-rate surprises, helping separate policy-rate news from pure asset-purchase shocks.",
    "ln_dax_real_de": "The real DAX response is negative under the target-surprise specification, so this figure should be read as mixed financial-market evidence rather than a clean asset-price amplification result.",
    "ln_nfc_loans_ea_stock": "NFC credit reacts weakly, suggesting productive-credit expansion is not the dominant propagation path.",
    "ln_hh_loans_ea_stock": "Household credit is less central than housing-finance prices and flows, reinforcing the asymmetry across balance-sheet channels.",
    "ecb_mir_mortgage_lending_spread_dfr": "Mortgage spreads move visibly after easing surprises, linking monetary news to housing-finance conditions and affordability pressure.",
    "ecb_mir_nfc_lending_spread_dfr": "NFC spreads respond, but the broader evidence is less persistent than the housing-finance channel.",
    "ecb_mir_mortgage_lending_rate": "Mortgage lending rates shift only moderately, so the stronger housing signal comes through finance quantities and spreads.",
    "ecb_mir_nfc_lending_rate": "NFC lending rates show limited pass-through, consistent with weaker productive-credit transmission.",
    "ecb_house_purchase_growth_yoy": "House-purchase lending growth responds strongly and persistently, supporting the thesis of dominant housing-linked transmission.",
    "ln_ecb_house_purchase_pure_new_loans": "New house-purchase lending is less precise but remains directionally relevant to the housing-finance channel.",
    "ecb_wage_tracker_ex_oneoffs_real_yoy": "Real negotiated wage pressure remains muted relative to housing and financial channels, indicating incomplete compensation pass-through.",
    "eurostat_sts_industry_wage_bill_de_real_yoy": "Industry wage-bill growth is useful robustness evidence, but its volatility makes the compensation channel less clean than asset-linked responses.",
    "eurostat_ecfin_eei_ea20": "Employment expectations respond earlier than wages, but the signal is less central than the housing-finance response.",
}

CUMULATIVE_INTERPRETATIONS = {
    "ln_ecb_assets_ea_stock": "Cumulative balance-sheet effects remain limited under the target-surprise design, sharpening the focus on market and housing transmission.",
    "ln_dax_real_de": "The cumulative real DAX response remains negative in the target-surprise specification, pointing to information effects or specification-specific equity repricing rather than simple QE-style asset inflation.",
    "ln_nfc_loans_ea_stock": "Cumulative NFC credit remains economically weak, which weighs against a productive-credit-dominance interpretation.",
    "ecb_mir_mortgage_lending_spread_dfr": "Mortgage-spread persistence connects easing surprises to housing-finance conditions over several horizons.",
    "ecb_mir_nfc_lending_spread_dfr": "NFC spread persistence is visible, though less central to the thesis than housing-linked responses.",
    "ecb_house_purchase_growth_yoy": "The cumulative housing-finance response is large and durable, making it the clearest asset-linked result in the notebook.",
    "ln_ecb_house_purchase_pure_new_loans": "Cumulative new-loan volumes are less precise, so they complement rather than replace the stronger housing-credit-growth result.",
    "ecb_wage_tracker_ex_oneoffs_real_yoy": "Cumulative wage pressure is weaker and fades at longer horizons, consistent with muted real compensation transmission.",
    "eurostat_sts_industry_wage_bill_de_real_yoy": "The wage-bill proxy shows movement but remains noisier than the core housing and financial-condition channels.",
    "eurostat_ecfin_eei_ea20": "Labor expectations accumulate in the short run but do not overturn the asset-versus-compensation asymmetry.",
}

UNCERTAINTY_INTERPRETATIONS = {
    "ln_ecb_assets_ea_stock": "Uncertainty bands show that balance-sheet responses are less precisely estimated than the strongest housing-finance effects.",
    "ln_dax_real_de": "The fan chart shows that the DAX result is visible at longer horizons but directionally at odds with a simple equity-boost narrative.",
    "ln_nfc_loans_ea_stock": "Credit-stock uncertainty is wide relative to the signal, supporting a restrained productive-credit interpretation.",
    "ecb_mir_mortgage_lending_spread_dfr": "Mortgage-spread bands preserve a visible housing-finance pricing response.",
    "ecb_mir_nfc_lending_spread_dfr": "NFC-spread bands show a measurable lending-condition response with more modest thesis weight.",
    "ecb_house_purchase_growth_yoy": "Housing-credit-growth uncertainty remains comparatively tight, reinforcing it as the central empirical result.",
    "ln_ecb_house_purchase_pure_new_loans": "New-loan uncertainty is wider, so this figure is best read as supporting housing-finance evidence.",
    "ecb_wage_tracker_ex_oneoffs_real_yoy": "Wage-tracker intervals show weaker and less persistent pass-through than the housing-finance responses.",
    "eurostat_sts_industry_wage_bill_de_real_yoy": "Wage-bill uncertainty reflects a volatile labor-income proxy rather than a clean compensation channel.",
    "eurostat_ecfin_eei_ea20": "Employment-expectation uncertainty leaves the labor channel informative but secondary to asset-linked transmission.",
}

SPECIAL_INTERPRETATIONS = {
    "comparative_irf_panel": (
        "Comparative IRF Panel",
        "The panel makes the asymmetry visible: housing and financial-condition responses dominate the weaker compensation pass-through.",
    ),
    "horizon_durability_matrix": (
        "Horizon Durability Matrix",
        "Durability is strongest in housing-finance and lending-condition channels, while wage responses are less persistent.",
    ),
    "sign_persistence_map": (
        "Sign Persistence Map",
        "The sign map highlights more stable asset-linked responses than compensation dynamics, supporting the thesis hierarchy.",
    ),
    "conceptual_affordability_transmission_flow": (
        "Affordability Transmission Flow",
        "The flow figure links monetary easing to asset prices, housing finance, and affordability pressure rather than broad wage gains.",
    ),
    "robustness_summary": (
        "Robustness Summary",
        "Robustness evidence preserves the main asymmetry while keeping exact magnitudes secondary.",
    ),
    "robustness_consistency_matrix": (
        "Robustness Consistency Matrix",
        "The consistency matrix shows that the thesis result is not driven by a single robustness choice.",
    ),
}


def _extract_response_key(rel_path: str) -> str:
    stem = Path(rel_path).stem
    for prefix in ("monthly_irf_", "cumulative_interval_", "uncertainty_fan_", "rolling_stability_h6_"):
        if stem.startswith(prefix):
            return stem[len(prefix) :]
    return stem


def figure_caption(rel_path: str) -> tuple[str, str]:
    key = _extract_response_key(rel_path)
    label = RESPONSE_LABELS.get(key, key.replace("_", " "))
    stem = Path(rel_path).stem
    if stem in SPECIAL_INTERPRETATIONS:
        return SPECIAL_INTERPRETATIONS[stem]
    if "/baseline/" in rel_path:
        return (
            f"Baseline IRF: {label}",
            BASELINE_INTERPRETATIONS.get(key, "The IRF links the response path to the thesis comparison between asset-linked and compensation channels."),
        )
    if "/cumulative/" in rel_path:
        return (
            f"Cumulative Response: {label}",
            CUMULATIVE_INTERPRETATIONS.get(key, "The cumulative response summarizes persistence and clarifies the cross-channel thesis comparison."),
        )
    if "/uncertainty/uncertainty_fan_" in rel_path:
        return (
            f"Uncertainty Fan: {label}",
            UNCERTAINTY_INTERPRETATIONS.get(key, "The uncertainty band indicates how much precision supports the economic interpretation."),
        )
    if rel_path.endswith("significance_heatmap.png"):
        return (
            "Horizon Visibility Heatmap",
            "The heatmap shows where responses are most visible, with housing and lending-condition channels standing out relative to wages.",
        )
    if rel_path.endswith("uncertainty_width_comparison.png"):
        return (
            "Bootstrap Width Comparison",
            "Interval widths vary by bootstrap choice, but the asset-versus-compensation ranking remains the main object of interpretation.",
        )
    if "instrument" in rel_path or "surprise" in rel_path:
        return (
            Path(rel_path).stem.replace("_", " ").title(),
            "The surprise distribution supports a usable high-frequency identification design for monthly transmission analysis.",
        )
    if "/banking/" in rel_path:
        return (
            "Banking Peak Timing",
            "The timing order connects policy surprises to lending conditions and housing finance before broad compensation gains emerge.",
        )
    if "/mechanism/" in rel_path:
        return (
            "Sequential Timing Response Map",
            "The sequence emphasizes financial and housing channels as the main propagation path from monetary news to household balance sheets.",
        )
    if "/stability/" in rel_path:
        return (
            Path(rel_path).stem.replace("_", " ").title(),
            "Window evidence supports the direction of the main result while keeping long-horizon magnitudes interpretive rather than mechanical.",
        )
    if "/compensation/" in rel_path:
        return (
            "Compensation Proxy Tournament",
            "The proxy comparison explains why wage pressure is measured indirectly and why compensation results receive less weight than asset channels.",
        )
    if "/regimes/" in rel_path:
        return (
            "Regime Response Comparison",
            "Regime patterns suggest post-COVID amplification in asset-linked channels, while wage pass-through remains less consistent.",
        )
    return (
        Path(rel_path).stem.replace("_", " ").title(),
        "The figure contributes to the thesis comparison between asset-price transmission and weaker labor-income pass-through.",
    )


def display_figure(rel_path: str, width: int = 900) -> None:
    path = artifact_path(rel_path)
    if not path.exists():
        warn_missing(path)
        return
    title, interpretation = figure_caption(rel_path)
    mime_type = mimetypes.guess_type(path.name)[0] or "image/png"
    encoded = base64.b64encode(path.read_bytes()).decode("ascii")
    display(Markdown(f"#### {title}"))
    display(
        HTML(
            f"<img src='data:{html.escape(mime_type)};base64,{encoded}' "
            f"alt='{html.escape(title)}' "
            f"style='width:{int(width)}px; max-width:100%; height:auto;'>"
        )
    )
    display(
        HTML(
            "<div class='thesis-figure-note'>"
            f"{html.escape(interpretation)}"
            "</div>"
        )
    )


def display_figure_group(group_name: str, width: int = 900) -> None:
    display(Markdown(f"### {group_name}"))
    for rel_path in FIGURE_GROUPS.get(group_name, []):
        display_figure(rel_path, width=width)
