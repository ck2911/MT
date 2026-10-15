from __future__ import annotations

from dataclasses import dataclass
from math import erfc, sqrt

import numpy as np


@dataclass(frozen=True)
class OLSHACResult:
    names: list[str]
    params: dict[str, float]
    bse: dict[str, float]
    tvalues: dict[str, float]
    pvalues: dict[str, float]
    resid: np.ndarray
    rsquared: float
    df_resid: int


def _normal_p_value(t_stat: float) -> float:
    if not np.isfinite(t_stat):
        return np.nan
    return erfc(abs(float(t_stat)) / sqrt(2.0))


def add_constant(matrix: np.ndarray, names: list[str]) -> tuple[np.ndarray, list[str]]:
    x = np.asarray(matrix, dtype=float)
    if x.ndim == 1:
        x = x.reshape(-1, 1)
    return np.column_stack([np.ones(x.shape[0]), x]), ["const", *names]


def fit_ols_hac(y: np.ndarray, x: np.ndarray, names: list[str], maxlags: int = 0) -> OLSHACResult:
    y_arr = np.asarray(y, dtype=float).reshape(-1)
    x_arr = np.asarray(x, dtype=float)
    if x_arr.ndim == 1:
        x_arr = x_arr.reshape(-1, 1)
    if y_arr.shape[0] != x_arr.shape[0]:
        raise ValueError("y and x must have the same number of observations")
    if x_arr.shape[1] != len(names):
        raise ValueError("names must match the number of columns in x")

    nobs, nvars = x_arr.shape
    xtx_inv = np.linalg.pinv(x_arr.T @ x_arr)
    beta = xtx_inv @ x_arr.T @ y_arr
    resid = y_arr - x_arr @ beta
    df_resid = max(nobs - nvars, 0)

    centered = y_arr - np.mean(y_arr)
    tss = float(centered @ centered)
    rss = float(resid @ resid)
    rsquared = np.nan if tss <= 0 else 1.0 - rss / tss

    maxlags = max(0, int(maxlags))
    score = x_arr * resid[:, None]
    meat = score.T @ score
    for lag in range(1, min(maxlags, nobs - 1) + 1):
        weight = 1.0 - lag / (maxlags + 1.0)
        gamma = score[lag:].T @ score[:-lag]
        meat += weight * (gamma + gamma.T)

    cov = xtx_inv @ meat @ xtx_inv
    diagonal = np.diag(cov)
    se = np.sqrt(np.where(diagonal >= 0, diagonal, np.nan))
    tvalues = np.divide(beta, se, out=np.full_like(beta, np.nan), where=se > 0)

    params = {name: float(value) for name, value in zip(names, beta)}
    bse = {name: float(value) for name, value in zip(names, se)}
    t_stats = {name: float(value) for name, value in zip(names, tvalues)}
    pvalues = {name: _normal_p_value(value) for name, value in t_stats.items()}

    return OLSHACResult(
        names=names,
        params=params,
        bse=bse,
        tvalues=t_stats,
        pvalues=pvalues,
        resid=resid,
        rsquared=float(rsquared),
        df_resid=int(df_resid),
    )

