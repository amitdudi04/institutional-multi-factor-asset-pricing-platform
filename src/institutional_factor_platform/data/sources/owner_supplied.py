"""Strict owner-supplied CSV, Parquet, and JSON ingestion."""

import csv
import json
from pathlib import Path

import pyarrow.parquet as pq
from pyarrow import BufferReader

from institutional_factor_platform.data.contracts import CONTRACTS
from institutional_factor_platform.data.domain import DataSource, RetrievalRequest
from institutional_factor_platform.data.sources.base import SourceAdapter
from institutional_factor_platform.exceptions import RetrievalError, UnsupportedDatasetError


class OwnerSuppliedAdapter(SourceAdapter[bytes]):
    source = DataSource.OWNER_SUPPLIED

    def retrieve(self, request: RetrievalRequest) -> bytes:
        value = request.parameters.get("path")
        if not value:
            raise RetrievalError("Owner-supplied retrieval requires parameters.path.")
        path = Path(str(value)).resolve()
        if not path.is_file():
            raise RetrievalError(f"Owner-supplied file does not exist: {path}")
        if path.suffix.lower() not in {".csv", ".json", ".parquet"}:
            raise UnsupportedDatasetError(f"Unsupported owner file format: {path.suffix}")
        return path.read_bytes()

    def standardize(
        self, payload: bytes, request: RetrievalRequest
    ) -> tuple[dict[str, object], ...]:
        schema = str(request.parameters.get("schema", ""))
        if schema not in CONTRACTS:
            raise UnsupportedDatasetError(f"Explicit approved schema required; got {schema!r}.")
        suffix = Path(str(request.parameters.get("path"))).suffix.lower()
        if suffix == ".csv":
            text = payload.decode("utf-8-sig")
            return tuple(dict(row) for row in csv.DictReader(text.splitlines()))
        if suffix == ".json":
            value = json.loads(payload)
            if not isinstance(value, list) or not all(isinstance(row, dict) for row in value):
                raise UnsupportedDatasetError(
                    "Owner JSON must be a list of schema-defined records."
                )
            return tuple(value)
        table = pq.read_table(BufferReader(payload))
        return tuple(table.to_pylist())
