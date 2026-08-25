"""Strict owner-supplied CSV, Parquet, and JSON ingestion without guessing."""

import csv
import io
import json
from pathlib import Path

import pyarrow as pa
import pyarrow.csv as pacsv
import pyarrow.parquet as pq
from pyarrow import BufferReader

from institutional_factor_platform.data.contracts import CONTRACTS, TableContract
from institutional_factor_platform.data.domain import DataSource, RetrievalRequest
from institutional_factor_platform.data.sources.base import SourceAdapter
from institutional_factor_platform.exceptions import RetrievalError, UnsupportedDatasetError

REQUIRED_METADATA = {
    "path",
    "schema",
    "contract_version",
    "source_name",
    "source_ownership",
    "units",
    "date_semantics",
    "security_identifier_semantics",
}

UNIT_RULES: dict[str, dict[str, set[str]]] = {
    "daily_market": {
        "open": {"USD", "currency:USD"},
        "high": {"USD", "currency:USD"},
        "low": {"USD", "currency:USD"},
        "close": {"USD", "currency:USD"},
        "adjusted_close": {"USD", "currency:USD"},
        "volume": {"shares"},
        "dividend": {"USD", "currency:USD"},
        "split_factor": {"ratio"},
    },
    "corporate_actions": {"value": {"USD", "currency:USD", "ratio"}},
    "macro_observations": {"value": {"percent", "percent_per_annum", "decimal", "index", "USD"}},
    "french_factor_returns": {"factor_value": {"decimal"}},
    "sec_financial_facts": {"value": {"xbrl_source_unit"}},
    "security_master": {"security_id": {"not_applicable"}},
    "factor_market_input": {
        "price_basis": {"split_adjusted"},
        "return_basis": {"total_return"},
        "return": {"decimal_return"},
        "price": {"USD"},
        "high": {"USD"},
        "low": {"USD"},
        "volume": {"shares"},
        "shares_outstanding": {"shares"},
        "market_return": {"decimal_return"},
        "risk_free": {"decimal_return"},
        "benchmark_return": {"decimal_return"},
    },
    "factor_fundamental_input": {
        field: {"USD"}
        for field in (
            "book_equity",
            "net_income",
            "operating_cash_flow",
            "dividends",
            "shareholder_equity",
            "total_assets",
            "gross_profit",
            "operating_income",
            "revenue",
            "average_assets",
            "total_accruals",
            "total_debt",
            "interest_expense",
            "prior_total_assets",
            "capex",
            "prior_capex",
            "net_equity_issuance",
            "working_capital",
            "prior_working_capital",
        )
    },
}


class OwnerSuppliedAdapter(SourceAdapter[bytes]):
    source = DataSource.OWNER_SUPPLIED

    def __init__(self) -> None:
        self._mapping_authority: Path | None = None

    def mapping_authority_path(self) -> Path | None:
        return self._mapping_authority

    def retrieve(self, request: RetrievalRequest) -> bytes:
        _contract(request)
        path = Path(str(request.parameters["path"])).resolve()
        if not path.is_file():
            raise RetrievalError(f"Owner-supplied file does not exist: {path}")
        if path.suffix.lower() not in {".csv", ".json", ".parquet"}:
            raise UnsupportedDatasetError(f"Unsupported owner file format: {path.suffix}")
        return path.read_bytes()

    def standardize(
        self, payload: bytes, request: RetrievalRequest
    ) -> tuple[dict[str, object], ...]:
        contract = _contract(request)
        mapping_value = request.parameters.get("mapping_authority_path")
        self._mapping_authority = Path(str(mapping_value)).resolve() if mapping_value else None
        suffix = Path(str(request.parameters["path"])).suffix.lower()
        try:
            if suffix == ".csv":
                header = next(csv.reader(io.StringIO(payload.decode("utf-8-sig"))))
                _exact_columns(header, contract)
                table = pacsv.read_csv(
                    BufferReader(payload),
                    convert_options=pacsv.ConvertOptions(column_types=contract.schema),
                )
            elif suffix == ".json":
                value = json.loads(payload)
                if not isinstance(value, list) or not all(isinstance(row, dict) for row in value):
                    raise UnsupportedDatasetError(
                        "Owner JSON must be a list of schema-defined records."
                    )
                if value:
                    _exact_columns(list(value[0]), contract)
                    if any(set(row) != set(contract.schema.names) for row in value):
                        raise UnsupportedDatasetError("Owner JSON rows have inconsistent columns.")
                table = pa.Table.from_pylist(value)
                table = table.select(contract.schema.names).cast(contract.schema)
            elif suffix == ".parquet":
                table = pq.read_table(BufferReader(payload))
                _exact_columns(table.column_names, contract)
                if not table.schema.equals(contract.schema, check_metadata=False):
                    raise UnsupportedDatasetError(
                        "Owner Parquet schema does not exactly match contract."
                    )
            else:
                raise UnsupportedDatasetError(f"Unsupported owner file format: {suffix}")
        except (UnicodeDecodeError, csv.Error, json.JSONDecodeError, pa.ArrowException) as exc:
            raise RetrievalError(
                f"Owner file cannot be parsed under {contract.name}: {exc}"
            ) from exc
        contract.validate_schema(table)
        if contract.name == "factor_fundamental_input" and table.num_rows:
            observed_fields = {str(value) for value in table.column("field").to_pylist()}
            declared_fields = set(request.parameters["units"])
            if observed_fields != declared_fields:
                raise UnsupportedDatasetError(
                    "Fundamental unit metadata must exactly cover observed fields; "
                    f"missing={sorted(observed_fields - declared_fields)}, "
                    f"extra={sorted(declared_fields - observed_fields)}."
                )
        return tuple(table.to_pylist())


def _contract(request: RetrievalRequest) -> TableContract:
    missing = sorted(REQUIRED_METADATA - set(request.parameters))
    if missing:
        raise UnsupportedDatasetError(f"Owner metadata is incomplete; missing {missing}.")
    schema = str(request.parameters["schema"])
    if schema not in CONTRACTS:
        raise UnsupportedDatasetError(f"Explicit approved schema required; got {schema!r}.")
    contract = CONTRACTS[schema]
    if (
        contract.name in {"factor_market_input", "factor_fundamental_input"}
        and not str(request.parameters.get("mapping_authority_path", "")).strip()
    ):
        raise UnsupportedDatasetError(
            "Phase 2 owner inputs require an explicit persisted mapping_authority_path."
        )
    if request.parameters["contract_version"] != contract.version:
        raise UnsupportedDatasetError(
            f"Owner contract version {request.parameters['contract_version']!r} is unsupported; "
            f"expected {contract.version}."
        )
    for field in (
        "source_name",
        "source_ownership",
        "date_semantics",
        "security_identifier_semantics",
    ):
        if not str(request.parameters[field]).strip():
            raise UnsupportedDatasetError(f"Owner metadata {field} must be explicit.")
    units = request.parameters["units"]
    if not isinstance(units, dict) or not units:
        raise UnsupportedDatasetError(
            "Owner metadata units must be a non-empty field-to-unit mapping."
        )
    rules = UNIT_RULES[contract.name]
    unknown_fields = set(units) - set(rules)
    missing_fields = set(rules) - set(units)
    partial_fundamentals = contract.name == "factor_fundamental_input"
    if unknown_fields or (missing_fields and not partial_fundamentals):
        raise UnsupportedDatasetError(
            "Owner unit metadata must exactly cover unit-bearing contract fields; "
            f"missing={sorted(missing_fields)}, extra={sorted(unknown_fields)}."
        )
    for field, value in units.items():
        normalized = str(value).strip()
        if normalized not in rules[field]:
            raise UnsupportedDatasetError(
                f"Owner unit {value!r} is incompatible with {contract.name}.{field}; "
                f"allowed={sorted(rules[field])}."
            )
    return contract


def _exact_columns(columns: list[str], contract: TableContract) -> None:
    if columns != contract.schema.names:
        missing = sorted(set(contract.schema.names) - set(columns))
        extra = sorted(set(columns) - set(contract.schema.names))
        raise UnsupportedDatasetError(
            f"Owner columns must exactly match {contract.name}; missing={missing}, extra={extra}."
        )
