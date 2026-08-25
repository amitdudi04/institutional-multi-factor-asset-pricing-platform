"""Controlled model-signal evaluation delegated to the Phase 4 backtest engine."""

import numpy as np
import pandas as pd

from institutional_factor_platform.backtest.costs import TransactionCostModel
from institutional_factor_platform.backtest.engine import BacktestResult, run_backtest
from institutional_factor_platform.exceptions import DataQualityError
from institutional_factor_platform.numeric import FloatArray


def evaluate_ranked_signal(
    authenticated_predictions: pd.DataFrame,
    authenticated_returns: pd.DataFrame,
    authenticated_benchmark: pd.Series,
    costs: TransactionCostModel,
    *,
    selection_fraction: float,
    window: int,
) -> BacktestResult:
    required = {"formation_date", "security_id", "prediction", "authentication_status"}
    if set(authenticated_predictions.columns) < required:
        raise DataQualityError("Economic evaluation requires authenticated prediction identity")
    if set(authenticated_predictions["authentication_status"]) != {"PASS"}:
        raise DataQualityError("Unauthenticated prediction cannot enter Phase 4")
    if not 0 < selection_fraction <= 1:
        raise DataQualityError("Selection fraction must be explicit and bounded")
    predictions = authenticated_predictions.copy()
    predictions["formation_date"] = pd.to_datetime(predictions["formation_date"])

    def allocator(history: pd.DataFrame, previous: FloatArray) -> FloatArray:
        formation = pd.Timestamp(history.index[-1])
        available = predictions.loc[predictions["formation_date"].eq(formation)]
        if available.empty:
            raise DataQualityError("Authenticated prediction is missing at formation time")
        if available["security_id"].duplicated().any():
            raise DataQualityError("Prediction universe contains duplicate security identity")
        unknown = set(available["security_id"].astype(str)) - set(history.columns.astype(str))
        if unknown:
            raise DataQualityError("Prediction universe contains an unauthenticated return asset")
        ranks = available.set_index("security_id")["prediction"].reindex(history.columns).dropna()
        if ranks.empty:
            raise DataQualityError("No authenticated prediction aligns with the return universe")
        count = max(1, int(np.ceil(len(ranks) * selection_fraction)))
        selected = set(ranks.nlargest(count).index)
        return np.array([1 / count if asset in selected else 0.0 for asset in history.columns])

    return run_backtest(
        authenticated_returns,
        authenticated_benchmark,
        allocator,
        costs,
        window=window,
    )
