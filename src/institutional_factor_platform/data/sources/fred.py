"""FRED CSV adapter preserving source frequency and missing observations."""

import csv
from collections.abc import Callable
from datetime import UTC, datetime
from io import StringIO
from typing import ClassVar

from institutional_factor_platform.data.domain import DataSource, RetrievalRequest
from institutional_factor_platform.data.sources.base import HttpTransport, SourceAdapter
from institutional_factor_platform.exceptions import RetrievalError


class FredAdapter(SourceAdapter[bytes]):
    source = DataSource.FRED
    approved_series: ClassVar[dict[str, tuple[str, str]]] = {
        "DGS3MO": ("percent per annum", "daily"),
        "TB3MS": ("percent per annum", "monthly"),
    }

    def __init__(
        self,
        transport: HttpTransport,
        now: Callable[[], datetime] = lambda: datetime.now(UTC),
    ) -> None:
        self.transport = transport
        self.now = now

    def retrieve(self, request: RetrievalRequest) -> bytes:
        if request.dataset not in self.approved_series:
            raise RetrievalError(f"Unapproved FRED series: {request.dataset}")
        url = f"https://fred.stlouisfed.org/graph/fredgraph.csv?id={request.dataset}"
        if request.date_range:
            start = request.date_range.start.isoformat()
            end = request.date_range.end.isoformat()
            url += f"&cosd={start}&coed={end}"
        return self.transport.get(url)

    def standardize(
        self, payload: bytes, request: RetrievalRequest
    ) -> tuple[dict[str, object], ...]:
        text = payload.decode("utf-8-sig")
        reader = csv.DictReader(StringIO(text))
        if not reader.fieldnames or request.dataset not in reader.fieldnames:
            raise RetrievalError(f"FRED response missing expected column {request.dataset}")
        unit, frequency = self.approved_series[request.dataset]
        retrieved = self.now()
        records: list[dict[str, object]] = []
        for row in reader:
            raw = row[request.dataset].strip()
            missing = raw in {"", ".", "NA", "NaN"}
            records.append(
                {
                    "series_id": request.dataset,
                    "observation_date": datetime.strptime(row["DATE"], "%Y-%m-%d").date(),
                    "value": None if missing else float(raw),
                    "source_unit": unit,
                    "frequency": frequency,
                    "seasonal_adjustment": "not seasonally adjusted",
                    "source": self.source.value,
                    "retrieval_timestamp": retrieved,
                    "availability_timestamp": None,
                    "missing_value": missing,
                    "schema_version": "1.0.0",
                }
            )
        if not records:
            raise RetrievalError("FRED returned an empty response.")
        return tuple(records)
