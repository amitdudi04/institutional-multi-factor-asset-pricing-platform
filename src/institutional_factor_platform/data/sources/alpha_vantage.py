"""Alpha Vantage free historical listing-lifecycle adapter."""

import csv
from collections import Counter
from collections.abc import Callable
from datetime import UTC, date, datetime
from io import StringIO
from urllib.parse import urlencode

from institutional_factor_platform.data.config import AlphaVantageSettings
from institutional_factor_platform.data.domain import DataSource, RetrievalRequest
from institutional_factor_platform.data.sources.base import HttpTransport, SourceAdapter
from institutional_factor_platform.exceptions import RetrievalError


class AlphaVantageListingAdapter(SourceAdapter[bytes]):
    source = DataSource.ALPHA_VANTAGE
    columns = ("symbol", "name", "exchange", "assetType", "ipoDate", "delistingDate", "status")

    def __init__(
        self,
        settings: AlphaVantageSettings,
        transport: HttpTransport,
        now: Callable[[], datetime] = lambda: datetime.now(UTC),
    ) -> None:
        self.settings = settings
        self.transport = transport
        self.now = now

    def retrieve(self, request: RetrievalRequest) -> bytes:
        if request.dataset != "listing_status":
            raise RetrievalError(f"Unsupported Alpha Vantage dataset: {request.dataset}")
        state = str(request.parameters.get("state", "active"))
        if state not in {"active", "delisted"}:
            raise RetrievalError("Alpha Vantage listing state must be active or delisted.")
        as_of = request.parameters.get("date")
        if as_of is not None:
            try:
                parsed = date.fromisoformat(str(as_of))
            except ValueError as exc:
                raise RetrievalError("Alpha Vantage listing date must be ISO-8601.") from exc
            if parsed <= date(2010, 1, 1):
                raise RetrievalError(
                    "Alpha Vantage historical listing date must be after 2010-01-01."
                )
        query = {
            "function": "LISTING_STATUS",
            "state": state,
            "apikey": self.settings.require_api_key(),
        }
        if as_of is not None:
            query["date"] = str(as_of)
        return self.transport.get("https://www.alphavantage.co/query?" + urlencode(query))

    def standardize(
        self, payload: bytes, request: RetrievalRequest
    ) -> tuple[dict[str, object], ...]:
        text = payload.decode("utf-8-sig")
        if text.lstrip().startswith("{"):
            raise RetrievalError("Alpha Vantage returned an error or rate-limit response.")
        reader = csv.DictReader(StringIO(text))
        if tuple(reader.fieldnames or ()) != self.columns:
            raise RetrievalError("Alpha Vantage listing response schema changed.")
        retrieved = self.now()
        as_of = date.fromisoformat(str(request.parameters.get("date", retrieved.date())))
        rows = [
            (
                row["symbol"].strip(),
                row["name"].strip(),
                row["exchange"].strip(),
                row["assetType"].strip(),
                row["ipoDate"].strip(),
                row["delistingDate"].strip(),
                row["status"].strip().lower(),
            )
            for row in reader
            if row.get("symbol", "").strip()
        ]
        counts = Counter(rows)
        records = tuple(
            {
                "symbol": symbol,
                "name": name,
                "exchange": exchange,
                "asset_type": asset_type,
                "ipo_date": _date(ipo_date),
                "delisting_date": _date(delisting_date),
                "status": status,
                "source_duplicate_count": count,
                "as_of_date": as_of,
                "source": self.source.value,
                "retrieval_timestamp": retrieved,
                "schema_version": "1.0.0",
            }
            for (
                symbol,
                name,
                exchange,
                asset_type,
                ipo_date,
                delisting_date,
                status,
            ), count in sorted(counts.items())
        )
        if not records:
            raise RetrievalError("Alpha Vantage returned no listing records.")
        return records


def _date(value: str) -> date | None:
    value = value.strip()
    return None if not value or value == "null" else date.fromisoformat(value)
