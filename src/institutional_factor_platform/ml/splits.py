"""Purged, embargoed financial dataset splitting without random shuffle."""

from dataclasses import dataclass

import pandas as pd

from institutional_factor_platform.exceptions import DataQualityError, TemporalIntegrityError


@dataclass(frozen=True)
class TemporalFold:
    fold: int
    train_dates: tuple[pd.Timestamp, ...]
    validation_dates: tuple[pd.Timestamp, ...]
    test_dates: tuple[pd.Timestamp, ...]


def temporal_folds(
    rows: pd.DataFrame,
    *,
    method: str,
    train_periods: int,
    validation_periods: int,
    test_periods: int,
    rolling_periods: int | None = None,
    embargo_periods: int = 0,
) -> tuple[TemporalFold, ...]:
    required = {"formation_date", "target_start", "target_end"}
    if set(rows.columns) < required:
        raise DataQualityError("Temporal split input lacks target-window identity")
    dates = tuple(sorted(pd.to_datetime(rows["formation_date"], utc=True).unique()))
    needed = train_periods + validation_periods + test_periods + embargo_periods * 2
    if len(dates) < needed:
        raise DataQualityError("Insufficient dates for requested temporal split")
    starts = [0] if method == "holdout" else list(range(0, len(dates) - needed + 1, test_periods))
    folds: list[TemporalFold] = []
    for number, start in enumerate(starts):
        train_end = start + train_periods
        if method == "expanding" or method == "walk_forward":
            train = dates[:train_end]
        elif method == "rolling":
            width = rolling_periods or train_periods
            train = dates[max(0, train_end - width) : train_end]
        else:
            train = dates[start:train_end]
        validation_start = train_end + embargo_periods
        validation = dates[validation_start : validation_start + validation_periods]
        test_start = validation_start + validation_periods + embargo_periods
        test = dates[test_start : test_start + test_periods]
        if len(test) != test_periods:
            continue
        folds.append(TemporalFold(number, tuple(train), tuple(validation), tuple(test)))
    if not folds:
        raise DataQualityError("No complete temporal fold could be constructed")
    return tuple(folds)


def assign_and_purge(rows: pd.DataFrame, fold: TemporalFold, *, purge: bool = True) -> pd.DataFrame:
    result = rows.copy()
    formation = pd.to_datetime(result["formation_date"], utc=True)
    starts = pd.to_datetime(result["target_start"], utc=True)
    ends = pd.to_datetime(result["target_end"], utc=True)
    result["partition"] = "unused"
    result.loc[formation.isin(fold.train_dates), "partition"] = "train"
    result.loc[formation.isin(fold.validation_dates), "partition"] = "validation"
    result.loc[formation.isin(fold.test_dates), "partition"] = "test"
    if purge:
        validation_start = min(fold.validation_dates)
        test_start = min(fold.test_dates)
        overlap = result["partition"].eq("train") & (ends >= validation_start)
        overlap |= result["partition"].eq("validation") & (ends >= test_start)
        result.loc[overlap, "partition"] = "purged"
    active = result[result["partition"].isin(["train", "validation", "test"])]
    if active.empty or not {"train", "validation", "test"}.issubset(set(active["partition"])):
        raise TemporalIntegrityError("Purging removed a required split partition")
    train_end = ends[result["partition"].eq("train")].max()
    validation_formation = formation[result["partition"].eq("validation")].min()
    validation_end = ends[result["partition"].eq("validation")].max()
    test_formation = formation[result["partition"].eq("test")].min()
    if train_end >= validation_formation or validation_end >= test_formation:
        raise TemporalIntegrityError("Target windows overlap validation or test boundaries")
    result["fold"] = fold.fold
    result["target_start"] = starts
    result["target_end"] = ends
    return result


def reject_random_financial_split(method: str) -> None:
    if method.lower() in {"random", "shuffle", "stratified_random"}:
        raise TemporalIntegrityError("Random financial splitting is prohibited")
