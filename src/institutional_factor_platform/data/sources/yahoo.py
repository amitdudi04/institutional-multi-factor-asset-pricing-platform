"""Bounded yfinance adapter for daily OHLCV, dividends, and splits."""

from collections.abc import Callable
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import pandas as pd
import yfinance as yf

from institutional_factor_platform.data.domain import DataSource, RetrievalRequest
from institutional_factor_platform.data.security_master import SecurityMappingStore
from institutional_factor_platform.data.sources.base import SourceAdapter
from institutional_factor_platform.exceptions import PartialRetrievalError, RetrievalError

DownloadFunction = Callable[..., pd.DataFrame]


class YahooFinanceAdapter(SourceAdapter[pd.DataFrame]):
    source = DataSource.YAHOO_FINANCE

    def __init__(
        self,
        download: DownloadFunction = yf.download,
        mapping_store: SecurityMappingStore | None = None,
        now: Callable[[], datetime] = lambda: datetime.now(UTC),
    ) -> None:
        self.download = download
        self.mapping_store = mapping_store
        self.now = now

    def mapping_authority_path(self) -> Path | None:
        return self.mapping_store.path if self.mapping_store is not None else None

    def retrieve(self, request: RetrievalRequest) -> pd.DataFrame:
        if not request.identifiers or request.date_range is None:
            raise RetrievalError("Yahoo retrieval requires tickers and explicit date range.")
        frame = self.download(
            list(request.identifiers),
            start=request.date_range.start.isoformat(),
            end=request.date_range.end.isoformat(),
            interval="1d",
            actions=True,
            auto_adjust=False,
            group_by="ticker",
            progress=False,
            threads=False,
            timeout=request.parameters.get("timeout", 30),
        )
        if frame.empty:
            raise RetrievalError("Yahoo Finance returned an empty response.")
        return frame

    def standardize(
        self, payload: pd.DataFrame, request: RetrievalRequest
    ) -> tuple[dict[str, object], ...]:
        retrieved = self.retrieval_timestamp(self.now)
        records: list[dict[str, object]] = []
        failures: list[str] = []
        multiple = isinstance(payload.columns, pd.MultiIndex)
        for ticker in request.identifiers:
            try:
                frame = payload[ticker] if multiple else payload
            except KeyError:
                failures.append(ticker)
                continue
            frame = frame.dropna(how="all")
            if frame.empty:
                failures.append(ticker)
                continue
            if request.parameters.get("security_ids") is not None:
                raise RetrievalError(
                    "Yahoo caller-supplied security IDs are prohibited; use persisted mappings."
                )
            if self.mapping_store is None:
                raise RetrievalError(f"Yahoo mapping authority is required for {ticker}.")
            for index, row in frame.iterrows():
                try:
                    security_id = self.mapping_store.resolve(
                        self.source.value, ticker, index.date()
                    ).value
                except Exception as exc:
                    raise RetrievalError(
                        f"Yahoo listing mapping is unresolved or ambiguous for {ticker}."
                    ) from exc
                records.append(
                    {
                        "security_id": security_id,
                        "ticker": ticker,
                        "trading_date": index.date(),
                        "open": _float_or_none(row.get("Open")),
                        "high": _float_or_none(row.get("High")),
                        "low": _float_or_none(row.get("Low")),
                        "close": _float_or_none(row.get("Close")),
                        "adjusted_close": _float_or_none(row.get("Adj Close")),
                        "volume": _int_or_none(row.get("Volume")),
                        "dividend": _float_or_none(row.get("Dividends")) or 0.0,
                        "split_factor": _float_or_none(row.get("Stock Splits")) or 0.0,
                        "currency": request.parameters.get("currency", "USD"),
                        "source": self.source.value,
                        "retrieval_timestamp": retrieved,
                        "schema_version": "1.0.0",
                    }
                )
        if failures and records:
            raise PartialRetrievalError(f"Yahoo partial ticker failure: {', '.join(failures)}")
        if not records:
            raise RetrievalError("Yahoo response contains no usable ticker records.")
        return tuple(records)


def _float_or_none(value: Any) -> float | None:
    return None if value is None or pd.isna(value) else float(value)


def _int_or_none(value: Any) -> int | None:
    return None if value is None or pd.isna(value) else int(value)
