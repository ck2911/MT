# Reduced-Form Specification

## Estimand

The empirical object is the dynamic response to a high-frequency ECB monetary-policy surprise aggregated to the month. The main shock is `target_factor_monthly_easing`; timing, forward-guidance, QE, and weighted-composite surprises are alternatives.

## Local Projection

```text
y_{t+h} - y_{t-1}
  = alpha_h + beta_h * surprise_t
    + phi_1 y_{t-1} + phi_2 y_{t-2}
    + gamma_1 inflation_{t-1} + gamma_2 inflation_{t-2}
    + delta_1 dfr_{t-1} + delta_2 dfr_{t-2}
    + epsilon_{t+h}
```

Horizon grid: `0, 1, 3, 6, 12, 24` months. Inference uses HAC/Newey-West covariance with horizon-specific bandwidth `h + 1`. The specification is not tuned by response variable.

## Normalization

`coefficient` is the response to a one-standard-deviation surprise shock. `raw_coefficient_per_unit_shock` preserves the unscaled regression coefficient. `coefficient_10bp_equiv` is an optional basis-point interpretation, conditional on treating factor units as basis points.

## Cumulative Responses

Cumulative tables sum normalized horizon coefficients. Cumulative confidence intervals use an independence approximation for the summed standard errors and are interpreted as descriptive persistence, not exact structural multipliers.

## Uncertainty

Each IRF row reports HAC/Newey-West confidence intervals with horizon-specific bandwidth `h + 1`; 68%, 90%, and 95% bands are retained. Target-shock IRFs also report feasible circular-block residual percentile bootstrap intervals. Moving-block, wild, block-length, and horizon-dependence checks are used to judge whether the persistence comparison is stable.

## Regime Decomposition

Regime estimates split the sample into pre-QE, QE, COVID, and tightening windows. They describe heterogeneity but are not separate regime treatment effects.

## Frequency Choice

No quarterly housing or compensation series is interpolated. The monthly comparison uses observed monthly housing-finance and wage-pressure proxies.
