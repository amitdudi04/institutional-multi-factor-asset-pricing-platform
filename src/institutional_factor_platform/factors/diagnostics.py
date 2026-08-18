"""Deterministic, non-graphical diagnostics for reviewable Phase 2 outputs."""

from math import sqrt

import pandas as pd

from institutional_factor_platform.factors.portfolio import NON_PORTFOLIO_FACTORS


def build_factor_diagnostics(
    factors: pd.DataFrame, portfolios: pd.DataFrame, rolling_window: int
) -> dict[str, object]:
    """Produce serializable coverage, outlier, turnover, correlation, and return diagnostics."""
    coverage = (
        factors.groupby("factor_id")["raw_value"].agg(observed="count", total="size").reset_index()
    )
    coverage["coverage_ratio"] = coverage["observed"] / coverage["total"]
    estimability = [
        {
            "factor_id": str(row.factor_id),
            "status": (
                "ESTIMABLE" if int(row.observed) > 0 else "NOT ESTIMABLE FROM DEFENSIBLE INPUTS"
            ),
            "observed": int(row.observed),
            "total": int(row.total),
        }
        for row in coverage.itertuples(index=False)
    ]
    outliers = (
        factors.assign(
            changed=factors["raw_value"].notna()
            & factors["winsorized_value"].notna()
            & factors["raw_value"].ne(factors["winsorized_value"])
        )
        .groupby("factor_id")["changed"]
        .sum()
        .astype(int)
    )
    matrix = factors.pivot_table(
        index=["security_id", "date"], columns="factor_id", values="raw_value"
    )
    correlation = matrix.corr(min_periods=2)

    memberships = factors.dropna(subset=["score_value"]).copy()
    memberships = memberships.loc[~memberships["factor_id"].isin(NON_PORTFOLIO_FACTORS)]
    memberships["month"] = pd.to_datetime(memberships["date"]).dt.to_period("M")
    memberships = memberships.loc[
        memberships["date"].eq(memberships.groupby("month")["date"].transform("max"))
    ].drop(columns="month")
    memberships["percentile"] = memberships.groupby(["factor_id", "date"])["score_value"].rank(
        method="first", pct=True
    )
    memberships["top"] = memberships["percentile"] > 2 / 3
    turnover_records: list[dict[str, object]] = []
    for factor_id, group in memberships.loc[memberships["top"]].groupby("factor_id"):
        previous: set[str] | None = None
        values: list[float] = []
        for _, dated in group.groupby("date", sort=True):
            current = set(dated["security_id"])
            if previous is not None and (previous or current):
                values.append(len(previous.symmetric_difference(current)) / len(previous | current))
            previous = current
        turnover_records.append(
            {
                "factor_id": factor_id,
                "mean_top_quantile_turnover": _finite_or_none(pd.Series(values).mean()),
            }
        )

    group_records: list[dict[str, object]] = []
    monotonicity_records: list[dict[str, object]] = []
    rolling_records: list[dict[str, object]] = []
    for (factor_id, quantile), group in portfolios.groupby(["factor_id", "quantile"]):
        active = group["active_return"]
        deviation = active.std(ddof=1)
        t_stat = (
            active.mean() / (deviation / sqrt(len(active)))
            if len(active) > 1 and deviation > 0
            else None
        )
        group_records.append(
            {
                "factor_id": factor_id,
                "quantile": int(quantile),
                "observations": len(active),
                "mean_return": _finite_or_none(group["value_weighted_return"].mean()),
                "mean_active_return": _finite_or_none(active.mean()),
                "active_return_t_stat": _finite_or_none(t_stat),
            }
        )
        rolling = active.rolling(rolling_window, min_periods=2).mean().dropna()
        rolling_records.append(
            {
                "factor_id": factor_id,
                "quantile": int(quantile),
                "last_rolling_active_return": _finite_or_none(
                    rolling.iloc[-1] if not rolling.empty else None
                ),
            }
        )
    for factor_id, group in portfolios.groupby("factor_id"):
        quantile_means = group.groupby("quantile")["value_weighted_return"].mean()
        monotonicity_records.append(
            {
                "factor_id": factor_id,
                "quantile_return_rank_correlation": _finite_or_none(
                    quantile_means.index.to_series().rank().corr(quantile_means.rank())
                ),
            }
        )

    return {
        "schema_version": "1.0.0",
        "coverage": _records(coverage),
        "estimability": estimability,
        "winsorized_outlier_counts": outliers.to_dict(),
        "pairwise_raw_correlations": {
            row: {column: _finite_or_none(value) for column, value in values.items()}
            for row, values in correlation.to_dict(orient="index").items()
        },
        "top_quantile_turnover": turnover_records,
        "portfolio_group_returns_and_significance": group_records,
        "portfolio_monotonicity": monotonicity_records,
        "rolling_active_performance": rolling_records,
        "plot_data_hooks": [
            "coverage",
            "estimability",
            "pairwise_raw_correlations",
            "portfolio_group_returns_and_significance",
            "rolling_active_performance",
        ],
        "limitations": [
            "Diagnostics are descriptive and do not constitute an asset-pricing conclusion.",
            "No transaction-cost estimate is applied because the Phase 2 cost decision "
            "is unapproved.",
        ],
    }


def _records(frame: pd.DataFrame) -> list[dict[str, object]]:
    return [
        {str(key): _finite_or_none(value) for key, value in record.items()}
        for record in frame.to_dict(orient="records")
    ]


def _finite_or_none(value: object) -> object:
    if value is None or pd.isna(value):
        return None
    if isinstance(value, float) and not float("-inf") < value < float("inf"):
        return None
    return value.item() if hasattr(value, "item") else value
