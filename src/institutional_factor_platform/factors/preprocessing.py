"""Cross-sectional, date-local factor preprocessing."""

from math import nan

import pandas as pd

from institutional_factor_platform.exceptions import DataQualityError
from institutional_factor_platform.factors.config import PreprocessingConfig


def winsorize(series: pd.Series, lower: float, upper: float) -> pd.Series:
    observed = series.dropna()
    if observed.empty:
        return series.astype(float)
    return series.clip(observed.quantile(lower), observed.quantile(upper))


def normalize(series: pd.Series, method: str, ddof: int) -> pd.Series:
    value = series.astype(float)
    if method in {"none", "winsorized"}:
        return value
    if method == "robust_zscore":
        median = value.median()
        mad = (value - median).abs().median()
        return (value - median) / (1.4826 * mad) if mad > 0 else value * nan
    if method == "zscore":
        deviation = value.std(ddof=ddof)
        return (value - value.mean()) / deviation if deviation > 0 else value * nan
    if method == "minmax":
        span = value.max() - value.min()
        return (value - value.min()) / span if span > 0 else value * nan
    ranks = value.rank(method="average", na_option="keep")
    if method == "rank":
        return ranks
    if method == "percentile":
        return ranks / value.notna().sum()
    raise DataQualityError(f"Unsupported normalization method: {method}")


def preprocess_characteristics(
    characteristics: pd.DataFrame,
    factor_ids: tuple[str, ...],
    config: PreprocessingConfig,
) -> pd.DataFrame:
    records: list[pd.DataFrame] = []
    for factor_id in factor_ids:
        grouping = ["date"]
        if config.neutralize_by != "none":
            grouping.append(config.neutralize_by)
        for group_key, group in characteristics.groupby(grouping, sort=True):
            computation_date = group_key[0] if isinstance(group_key, tuple) else group_key
            raw = group[factor_id]
            eligible = raw.notna().sum() >= config.minimum_cross_section
            clipped = winsorize(raw, config.winsor_lower, config.winsor_upper)
            transformed = normalize(clipped, config.method, config.ddof) if eligible else raw * nan
            records.append(
                pd.DataFrame(
                    {
                        "security_id": group["security_id"].to_numpy(),
                        "date": computation_date,
                        "factor_id": factor_id,
                        "raw_value": raw.to_numpy(),
                        "winsorized_value": clipped.to_numpy(),
                        "normalized_value": transformed.to_numpy(),
                        "normalization_method": (
                            config.method
                            if config.neutralize_by == "none"
                            else f"{config.method}|neutralized:{config.neutralize_by}"
                        ),
                        "available_at": group["available_at"].to_numpy(),
                        "factor_version": "1.0.0",
                    }
                )
            )
    return pd.concat(records, ignore_index=True)
