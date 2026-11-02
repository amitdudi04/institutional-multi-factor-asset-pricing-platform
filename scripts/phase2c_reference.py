"""Independent QR/Bartlett reference; no production fitting or matrix builders."""

import numpy as np
from scipy.linalg import qr, solve_triangular
from scipy.stats import t as student_t


def reference_fit(y, factors, lag=3, minimum=24):
    y = np.asarray(y, dtype=float)
    factors = np.asarray(factors, dtype=float)
    x = np.column_stack([np.ones(len(y)), factors])
    n, k = x.shape
    if n < minimum or n <= k or lag < 0 or lag >= n:
        raise ValueError("Insufficient observations or invalid lag")
    if not np.isfinite(x).all() or not np.isfinite(y).all():
        raise ValueError("Nonfinite matrix")
    q, r, pivot = qr(x, mode="economic", pivoting=True)
    rank = int(np.linalg.matrix_rank(x))
    if rank != k:
        raise ValueError("Rank deficient design")
    beta = np.empty(k)
    beta[pivot] = solve_triangular(r, q.T @ y)
    inverse_r = solve_triangular(r, np.eye(k))
    bread = np.empty((k, k))
    bread[np.ix_(pivot, pivot)] = inverse_r @ inverse_r.T
    fitted = x @ beta
    residual = y - fitted
    scores = x * residual[:, None]
    meat = np.zeros((k, k))
    # Accumulate observations independently rather than reusing a covariance API.
    for observation in scores:
        meat += np.outer(observation, observation)
    for j in range(1, lag + 1):
        weight = 1 - j / (lag + 1)
        for i in range(j, n):
            cross = np.outer(scores[i], scores[i - j])
            meat += weight * (cross + cross.T)
    covariance = bread @ meat @ bread * n / (n - k)
    se = np.sqrt(np.diag(covariance))
    statistic = beta / se
    p = 2 * student_t.sf(np.abs(statistic), n - k)
    critical = student_t.ppf(0.975, n - k)
    sse = float(residual @ residual)
    sst = float(np.sum((y - y.mean()) ** 2))
    if sst <= 0:
        raise ValueError("Constant dependent return")
    r2 = 1 - sse / sst
    standardized = (factors - factors.mean(axis=0)) / factors.std(axis=0)
    scaled = np.column_stack([np.ones(n), standardized])
    condition = float(np.linalg.cond(x))
    scaled_condition = float(np.linalg.cond(scaled))
    correlation = np.atleast_2d(np.corrcoef(factors, rowvar=False))
    vif = np.diag(np.linalg.inv(correlation)) if k > 2 else np.ones(1)
    max_correlation = float(np.max(np.abs(correlation - np.eye(k - 1))))
    normal = float(np.linalg.norm(x.T @ residual, ord=np.inf))
    normal_scaled = normal / max(1.0, float(np.linalg.norm(x, ord=2) * np.linalg.norm(y)))
    return dict(
        beta=beta,
        se=se,
        t=statistic,
        p=p,
        lower=beta - critical * se,
        upper=beta + critical * se,
        covariance=covariance,
        fitted=fitted,
        residual=residual,
        n=n,
        k=k,
        df=n - k,
        sse=sse,
        sst=sst,
        r2=r2,
        adj=1 - (1 - r2) * (n - 1) / (n - k),
        condition=condition,
        scaled_condition=scaled_condition,
        max_vif=float(vif.max()),
        max_regressor_correlation=max_correlation,
        normal=normal,
        normal_scaled=normal_scaled,
        residual_mean=float(residual.mean()),
        alpha_mean_identity=float(y.mean() - np.dot(beta[1:], factors.mean(axis=0))),
        mean_y=float(y.mean()),
        mean_factor_contribution=float(np.dot(beta[1:], factors.mean(axis=0))),
    )


def holm(p):
    """Holm familywise adjustment; no independence assumption, conditional on valid p."""
    p = np.asarray(p, dtype=float)
    if not np.isfinite(p).all() or (p < 0).any() or (p > 1).any():
        raise ValueError("Invalid p-values")
    order = np.argsort(p, kind="stable")
    result = np.empty(len(p))
    result[order] = np.minimum(1, np.maximum.accumulate(p[order] * (len(p) - np.arange(len(p)))))
    return result
