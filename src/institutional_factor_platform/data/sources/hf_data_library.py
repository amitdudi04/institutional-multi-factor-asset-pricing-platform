"""HF Data Library CC BY 4.0 daily-market adapter."""

import hashlib
import io
import json
from collections.abc import Callable
from datetime import UTC, datetime
from itertools import pairwise
from pathlib import Path
from typing import cast
from urllib.parse import urlencode

import pyarrow.parquet as pq

from institutional_factor_platform.data.config import HFDataLibrarySettings
from institutional_factor_platform.data.domain import DataSource, RetrievalRequest
from institutional_factor_platform.data.security_master import SecurityMappingStore
from institutional_factor_platform.data.sources.base import HttpTransport, SourceAdapter
from institutional_factor_platform.exceptions import RetrievalError


class HFDataLibraryAdapter(SourceAdapter[bytes]):
    source = DataSource.HF_DATA_LIBRARY
    base_url = "https://api.hfdatalibrary.com/v1"
    expected_columns = ("datetime", "Open", "High", "Low", "Close", "Volume", "source")
    maximum_splice_return = 0.5

    def inventory(self) -> dict[str, object]:
        """Build a dated, checksummed public coverage manifest without claiming universe status."""
        symbols_payload = self.transport.get(f"{self.base_url}/symbols")
        metadata_payload = self.transport.get("https://hfdatalibrary.com/data/ticker_meta.json")
        try:
            symbols = json.loads(symbols_payload)["symbols"]
            metadata = json.loads(metadata_payload)
        except (json.JSONDecodeError, KeyError, TypeError) as exc:
            raise RetrievalError("HF public inventory response is invalid.") from exc
        if not isinstance(symbols, list) or not isinstance(metadata, dict):
            raise RetrievalError("HF public inventory response has an invalid shape.")
        records: list[dict[str, object]] = []
        for item in symbols:
            if not isinstance(item, dict) or not isinstance(item.get("ticker"), str):
                raise RetrievalError("HF public symbol inventory has an invalid row.")
            ticker = item["ticker"].strip().upper()
            classification = metadata.get(ticker)
            if not isinstance(classification, dict) or classification.get("type") not in {
                "Stock",
                "ETF",
            }:
                raise RetrievalError(f"HF classification is missing or invalid for {ticker}.")
            selected = classification["type"] == "Stock"
            records.append(
                {
                    "ticker": ticker,
                    "version": self.settings.version,
                    "size": int(item["size_bytes"]),
                    "last_modified": str(item["last_modified"]),
                    "selected": selected,
                    "reason": "covered stock" if selected else "ETF excluded by project policy",
                }
            )
        if len(records) != len(metadata) or len({str(row["ticker"]) for row in records}) != len(
            records
        ):
            raise RetrievalError("HF inventory sources do not reconcile one-to-one.")
        return {
            "schema_version": "1.0.0",
            "retrieval_time": self.now().isoformat(),
            "source": self.source.value,
            "source_urls": [
                f"{self.base_url}/symbols",
                "https://hfdatalibrary.com/data/ticker_meta.json",
            ],
            "symbols_sha256": hashlib.sha256(symbols_payload).hexdigest(),
            "metadata_sha256": hashlib.sha256(metadata_payload).hexdigest(),
            "record_count": len(records),
            "selected_count": sum(bool(row["selected"]) for row in records),
            "rejected_count": sum(not bool(row["selected"]) for row in records),
            "records": records,
        }

    def __init__(
        self,
        settings: HFDataLibrarySettings,
        transport: HttpTransport,
        mapping_store: SecurityMappingStore | None = None,
        now: Callable[[], datetime] = lambda: datetime.now(UTC),
    ) -> None:
        self.settings = settings
        self.transport = transport
        self.mapping_store = mapping_store
        self.now = now

    def mapping_authority_path(self) -> Path | None:
        return self.mapping_store.path if self.mapping_store is not None else None

    def retrieve(self, request: RetrievalRequest) -> bytes:
        if request.dataset != "daily_market" or len(request.identifiers) != 1:
            raise RetrievalError("HF daily retrieval requires exactly one ticker.")
        ticker = request.identifiers[0].strip().upper()
        query = urlencode(
            {"timeframe": "daily", "format": "parquet", "version": self.settings.version}
        )
        token_bytes = self.transport.get(
            f"{self.base_url}/download-token/{ticker}?{query}",
            headers={"X-API-Key": self.settings.require_api_key()},
        )
        try:
            signed_url = str(json.loads(token_bytes)["url"])
        except (json.JSONDecodeError, KeyError, TypeError) as exc:
            raise RetrievalError("HF download-token response is invalid.") from exc
        if not signed_url.startswith(f"{self.base_url}/download/"):
            raise RetrievalError("HF signed download URL has an unexpected origin.")
        return self.transport.get(signed_url)

    def standardize(
        self, payload: bytes, request: RetrievalRequest
    ) -> tuple[dict[str, object], ...]:
        ticker = request.identifiers[0].strip().upper()
        try:
            table = pq.read_table(io.BytesIO(payload))
        except Exception as exc:
            raise RetrievalError("HF response is not valid Parquet.") from exc
        if tuple(table.column_names) != self.expected_columns:
            raise RetrievalError("HF daily Parquet schema changed.")
        metadata = table.schema.metadata or {}
        if b"citation" not in metadata or b"iex_attribution" not in metadata:
            raise RetrievalError("HF attribution metadata is missing.")
        if self.mapping_store is None:
            raise RetrievalError(f"HF mapping authority is required for {ticker}.")
        retrieved = self.now()
        records: list[dict[str, object]] = []
        for row in table.to_pylist():
            timestamp = row["datetime"]
            trading_date = timestamp.date()
            if request.date_range is not None and not (
                request.date_range.start <= trading_date <= request.date_range.end
            ):
                continue
            upstream_source = str(row["source"]).strip().lower()
            if upstream_source not in {"pitrading", "iex"}:
                raise RetrievalError("HF daily Parquet contains an unknown upstream source.")
            security_id = self.mapping_store.resolve(self.source.value, ticker, trading_date).value
            records.append(
                {
                    "security_id": security_id,
                    "ticker": ticker,
                    "trading_date": trading_date,
                    "open": float(row["Open"]) if row["Open"] is not None else None,
                    "high": float(row["High"]) if row["High"] is not None else None,
                    "low": float(row["Low"]) if row["Low"] is not None else None,
                    "close": float(row["Close"]),
                    "adjusted_close": float(row["Close"]),
                    "volume": int(row["Volume"]) if row["Volume"] is not None else None,
                    "dividend": None,
                    "split_factor": None,
                    "currency": "USD",
                    # Preserve the documented consolidated-tape/IEX structural break.
                    "source": f"{self.source.value}:{upstream_source}",
                    "retrieval_timestamp": retrieved,
                    "schema_version": "1.0.0",
                }
            )
        if not records:
            raise RetrievalError("HF daily Parquet contains no records in the requested interval.")
        for previous, current in pairwise(records):
            if previous["source"] == current["source"]:
                continue
            prior_close = cast(float, previous["close"])
            splice_return = cast(float, current["close"]) / prior_close - 1.0
            if abs(splice_return) > self.maximum_splice_return:
                raise RetrievalError(
                    "HF adjusted-price continuity fails at the documented source splice."
                )
        return tuple(records)
