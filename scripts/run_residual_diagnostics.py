#!/usr/bin/env python3
"""Residual diagnostics for the baseline monthly local projections.

Diagnostic layer. No thesis coefficient is changed here. The script re-fits the
baseline local projections exactly as scripts/run_monthly_reduced_form_lp.py
does (same dataset, same controls, same sample rules, same HAC bandwidth) and
tests the residuals of every canonical response at every horizon:

* serial correlation beyond the HAC bandwidth: a Ljung-Box statistic built from
  the twelve autocorrelations at lags h+2 ... h+13, just outside the Newey-West
  bandwidth h+1 that the baseline standard errors already cover. Correlation up
  to lag h is expected by construction, because the horizons overlap;
* heteroskedasticity: Koenker's studentized Breusch-Pagan LM test of the squared
  residuals on the regressors;
* conditional heteroskedasticity: Engle's ARCH LM test with twelve lags;
* normality: Jarque-Bera.

It also checks that the long-difference left-hand side y(t+h) - y(t-1) and a
level left-hand side y(t+h) give the same shock coefficient, which they must
because y(t-1) is itself a control, and it reports the first-order
autocorrelation of the monthly shock series.

Outputs (results/final/uncertainty/):
  residual_diagnostics.csv          one row per response and horizon
  residual_diagnostics_summary.csv  one row per response, listing the horizons
                                    at which each test rejects at 5 percent
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats
from statsmodels.stats.diagnostic import het_arch
from statsmodels.tsa.stattools import acf

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

import run_monthly_reduced_form_lp as lp  # noqa: E402
from src.lpiv.ols_hac import add_constant, fit_ols_hac  # noqa: E402

SHOCK = "target_factor_monthly_easing"
EXTRA_LAGS = 12
ALPHA = 0.05
OUT_LONG = lp.FINAL_UNCERTAINTY / "residual_diagnostics.csv"
OUT_SUMMARY = lp.FINAL_UNCERTAINTY / "residual_diagnostics_summary.csv"


def koenker_breusch_pagan(resid: np.ndarray, x: np.ndarray) -> tuple[float, float]:
    """Studentized Breusch-Pagan LM test: n * R^2 of e^2 on the regressors."""
    e2 = resid ** 2
    xtx_inv = np.linalg.pinv(x.T @ x)
    fitted = x @ (xtx_inv @ x.T @ e2)
    tss = float(((e2 - e2.mean()) ** 2).sum())
    rss = float(((e2 - fitted) ** 2).sum())
    r2 = np.nan if tss <= 0 else 1.0 - rss / tss
    df = x.shape[1] - 1
    lm = float(e2.shape[0] * r2)
    return lm, float(stats.chi2.sf(lm, df))


def ljung_box_band(resid: np.ndarray, first_lag: int, n_lags: int) -> tuple[float, float]:
    """Ljung-Box statistic restricted to lags first_lag ... first_lag + n_lags - 1."""
    n = resid.shape[0]
    rho = acf(resid, nlags=first_lag + n_lags - 1, fft=False)
    q = n * (n + 2) * sum(rho[k] ** 2 / (n - k) for k in range(first_lag, first_lag + n_lags))
    return float(q), float(stats.chi2.sf(q, n_lags))


def main() -> int:
    data = lp.load_data()
    shock_ar1 = float(data[SHOCK].dropna().autocorr(1))
    rows: list[dict[str, object]] = []
    max_beta_gap = 0.0
    for response in lp.CANONICAL_COMPARISON_RESPONSES:
        if response not in data.columns:
            continue
        label, channel, _role = lp.response_meta(response)
        frame = lp.add_lags(data, (response,))
        controls = [
            c
            for c in (
                f"L1_{response}",
                f"L2_{response}",
                "L1_inflation_ea20_mom",
                "L2_inflation_ea20_mom",
                "L1_dfr_mavg",
                "L2_dfr_mavg",
            )
            if c in frame.columns
        ]
        for h in lp.HORIZONS:
            outcome = lp.outcome_column(response, h)
            frame[outcome] = frame[response].shift(-h) - frame[response].shift(1)
            frame["_level_outcome"] = frame[response].shift(-h)
            clean = frame.dropna(subset=[outcome, SHOCK, *controls]).copy()
            if clean.shape[0] < max(48, len(controls) + 12) or clean[SHOCK].nunique() < 3:
                continue
            y = clean[outcome].to_numpy(dtype=float)
            x, names = add_constant(clean[[SHOCK, *controls]].to_numpy(dtype=float), [SHOCK, *controls])
            model = fit_ols_hac(y, x, names, maxlags=h + 1)
            level_model = fit_ols_hac(clean["_level_outcome"].to_numpy(dtype=float), x, names, maxlags=h + 1)
            max_beta_gap = max(max_beta_gap, abs(model.params[SHOCK] - level_model.params[SHOCK]))
            resid = np.asarray(model.resid, dtype=float)
            lb_q, lb_p = ljung_box_band(resid, h + 2, EXTRA_LAGS)
            bp_lm, bp_p = koenker_breusch_pagan(resid, x)
            arch_lm, arch_p, _f, _fp = het_arch(resid, nlags=EXTRA_LAGS)
            jb = stats.jarque_bera(resid)
            rows.append(
                {
                    "response": response,
                    "response_label": label,
                    "channel": channel,
                    "shock": SHOCK,
                    "horizon_months": h,
                    "nobs": int(clean.shape[0]),
                    "hac_bandwidth": h + 1,
                    "lb_first_lag": h + 2,
                    "lb_n_lags": EXTRA_LAGS,
                    "lb_beyond_bandwidth_q": lb_q,
                    "lb_beyond_bandwidth_p": lb_p,
                    "koenker_bp_lm": bp_lm,
                    "koenker_bp_p": bp_p,
                    "arch_lm_12": float(arch_lm),
                    "arch_lm_12_p": float(arch_p),
                    "jarque_bera": float(jb.statistic),
                    "jarque_bera_p": float(jb.pvalue),
                    "resid_skewness": float(stats.skew(resid)),
                    "resid_excess_kurtosis": float(stats.kurtosis(resid)),
                    "beta_longdiff_minus_level": float(model.params[SHOCK] - level_model.params[SHOCK]),
                    "shock_ar1_full_sample": shock_ar1,
                }
            )
    long = pd.DataFrame(rows)
    long.to_csv(OUT_LONG, index=False)

    def rejecting(group: pd.DataFrame, col: str) -> str:
        hs = [str(int(r.horizon_months)) for r in group.sort_values("horizon_months").itertuples() if getattr(r, col) < ALPHA]
        return ", ".join(hs) if hs else "none"

    summary_rows = []
    for response, group in long.groupby("response", sort=False):
        summary_rows.append(
            {
                "response": response,
                "response_label": group["response_label"].iloc[0],
                "nobs_h0": int(group.sort_values("horizon_months")["nobs"].iloc[0]),
                "serial_corr_beyond_bandwidth_horizons": rejecting(group, "lb_beyond_bandwidth_p"),
                "heteroskedasticity_horizons": rejecting(group, "koenker_bp_p"),
                "arch_horizons": rejecting(group, "arch_lm_12_p"),
                "non_normal_horizons": rejecting(group, "jarque_bera_p"),
                "n_horizons": int(group.shape[0]),
            }
        )
    pd.DataFrame(summary_rows).to_csv(OUT_SUMMARY, index=False)
    print(f"wrote {OUT_LONG} ({long.shape[0]} rows) and {OUT_SUMMARY}")
    print(f"shock AR(1), full sample: {shock_ar1:.3f}")
    print(f"max |beta(long difference) - beta(level)| across all cells: {max_beta_gap:.2e}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
