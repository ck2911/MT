# Composite Shock Design

Composite shocks are checks unless the first-stage evidence supports them.

## Variants Constructed

- `composite_pca_timing_fg_qe`: first principal component of standardized timing, forward-guidance, and QE quarterly shocks.
- `composite_equal_weight_timing_fg_qe`: standardized equal-weight sum.
- `composite_inverse_variance_timing_fg_qe`: standardized sum using inverse raw-variance weights.
- `composite_qe_heavy_timing_fg_qe`: standardized weighted sum with QE weight 0.6 and timing/FG weights 0.2 each.

## PCA Loading Structure

| instrument | target_equation | coef | partial_R2 |
| --- | --- | --- | --- |
| composite_pca_timing_fg_qe | timing | 0.723 | 0.444 |
| composite_pca_timing_fg_qe | fg | -0.678 | 0.444 |
| composite_pca_timing_fg_qe | qe | 0.133 | 0.444 |

## Weighted-Sum Weights

| instrument | target_equation | coef |
| --- | --- | --- |
| composite_equal_weight_timing_fg_qe | timing | 0.333 |
| composite_equal_weight_timing_fg_qe | fg | 0.333 |
| composite_equal_weight_timing_fg_qe | qe | 0.333 |
| composite_inverse_variance_timing_fg_qe | timing | 0.538 |
| composite_inverse_variance_timing_fg_qe | fg | 0.145 |
| composite_inverse_variance_timing_fg_qe | qe | 0.317 |
| composite_qe_heavy_timing_fg_qe | timing | 0.200 |
| composite_qe_heavy_timing_fg_qe | fg | 0.200 |
| composite_qe_heavy_timing_fg_qe | qe | 0.600 |

## First-Stage Leaders

| instrument | target_equation | sample | F_stat | partial_R2 | coef | p_value |
| --- | --- | --- | --- | --- | --- | --- |
| composite_qe_heavy_timing_fg_qe | d_dfr_eop | robustness_2005q1_2025q4 | 4.532 | 0.053 | -0.150 | 0.036 |
| composite_qe_heavy_timing_fg_qe | d_ln_nfc_loans_ea_stock | robustness_2005q1_2025q4 | 2.160 | 0.026 | -0.004 | 0.146 |
| composite_equal_weight_timing_fg_qe | d_ln_nfc_loans_ea_stock | robustness_2005q1_2025q4 | 1.213 | 0.015 | -0.003 | 0.274 |
| composite_equal_weight_timing_fg_qe | d_dfr_eop | robustness_2005q1_2025q4 | 1.179 | 0.014 | -0.078 | 0.281 |
| composite_pca_timing_fg_qe | d_ln_ecb_assets_ea_stock | robustness_2005q1_2025q4 | 0.789 | 0.010 | -0.006 | 0.377 |
| composite_inverse_variance_timing_fg_qe | d_ln_hh_loans_ea_stock | robustness_2005q1_2025q4 | 0.765 | 0.009 | -0.001 | 0.384 |
| composite_inverse_variance_timing_fg_qe | d_ln_ecb_assets_ea_stock | robustness_2005q1_2025q4 | 0.679 | 0.008 | -0.010 | 0.412 |
| composite_inverse_variance_timing_fg_qe | d_dfr_eop | robustness_2005q1_2025q4 | 0.584 | 0.007 | -0.048 | 0.447 |
| composite_pca_timing_fg_qe | d_ln_hh_loans_ea_stock | robustness_2005q1_2025q4 | 0.558 | 0.007 | -0.001 | 0.457 |
| composite_inverse_variance_timing_fg_qe | d_ln_nfc_loans_ea_stock | robustness_2005q1_2025q4 | 0.471 | 0.006 | -0.002 | 0.495 |

## Regime Stability Leaders

| instrument | factor | max_regime_F | median_regime_F | stable_sign_share | strong_regime_count |
| --- | --- | --- | --- | --- | --- |
| composite_qe_heavy_timing_fg_qe | composite | 13.682637796202629 | 0.3789862032798671 | 0.4642857142857143 | 1 |
| composite_inverse_variance_timing_fg_qe | composite | 12.144928471137435 | 0.45525855429422896 | 0.4642857142857143 | 1 |
| composite_pca_timing_fg_qe | composite | 7.172613920532421 | 0.4881630597392075 | 0.42857142857142855 | 0 |
| composite_equal_weight_timing_fg_qe | composite | 4.7573745839549355 | 0.17671279233039772 | 0.42857142857142855 | 0 |
