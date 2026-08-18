"""Kenneth French Data Library adapter for approved published factor datasets."""

import csv
import io
import zipfile
from collections.abc import Callable
from datetime import UTC, datetime
from typing import ClassVar

from institutional_factor_platform.data.domain import DataSource, RetrievalRequest
from institutional_factor_platform.data.sources.base import HttpTransport, SourceAdapter
from institutional_factor_platform.exceptions import RetrievalError


class KennethFrenchAdapter(SourceAdapter[bytes]):
    source = DataSource.KENNETH_FRENCH
    approved: ClassVar[set[str]] = {
        "F-F_Research_Data_5_Factors_2x3_daily",
        "F-F_Momentum_Factor_daily",
    }

    def __init__(
        self,
        transport: HttpTransport,
        now: Callable[[], datetime] = lambda: datetime.now(UTC),
    ) -> None:
        self.transport = transport
        self.now = now

    def retrieve(self, request: RetrievalRequest) -> bytes:
        if request.dataset not in self.approved:
            raise RetrievalError(f"Unapproved Kenneth French dataset: {request.dataset}")
        url = (
            f"https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/ftp/{request.dataset}_CSV.zip"
        )
        return self.transport.get(url)

    def standardize(
        self, payload: bytes, request: RetrievalRequest
    ) -> tuple[dict[str, object], ...]:
        try:
            with zipfile.ZipFile(io.BytesIO(payload)) as archive:
                names = archive.namelist()
                if len(names) != 1:
                    raise RetrievalError("French archive must contain exactly one data file.")
                text = archive.read(names[0]).decode("utf-8-sig", errors="strict")
        except (zipfile.BadZipFile, UnicodeDecodeError) as exc:
            raise RetrievalError(f"Invalid Kenneth French archive: {exc}") from exc
        lines = text.splitlines()
        header_index = next(
            (i for i, line in enumerate(lines) if line.lstrip().startswith(",")), None
        )
        if header_index is None:
            raise RetrievalError("French response lacks a factor header.")
        reader = csv.reader(lines[header_index:])
        header = [cell.strip() for cell in next(reader)]
        factor_names = header[1:]
        retrieved = self.retrieval_timestamp(self.now)
        records: list[dict[str, object]] = []
        for row in reader:
            if not row or not row[0].strip().isdigit() or len(row[0].strip()) != 8:
                break
            factor_date = datetime.strptime(row[0].strip(), "%Y%m%d").date()
            for factor, raw in zip(factor_names, row[1:], strict=True):
                value = raw.strip()
                if not value or value in {"-99.99", "-999"}:
                    raise RetrievalError(f"Missing French factor value for {factor_date} {factor}")
                records.append(
                    {
                        "factor_date": factor_date,
                        "factor_name": factor,
                        "factor_value": float(value) / 100.0,
                        "frequency": "daily",
                        "source_unit": "percent",
                        "standardized_unit": "decimal_return",
                        "dataset_identifier": request.dataset,
                        "source": self.source.value,
                        "retrieval_timestamp": retrieved,
                        "schema_version": "1.0.0",
                    }
                )
        if not records:
            raise RetrievalError("French dataset contains no daily records.")
        return tuple(records)
