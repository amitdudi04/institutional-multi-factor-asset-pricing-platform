"""Versioned PyArrow contracts for Phase 1 standardized tables."""

from dataclasses import dataclass

import pyarrow as pa

from institutional_factor_platform.exceptions import SchemaValidationError


@dataclass(frozen=True, slots=True)
class TableContract:
    name: str
    version: str
    schema: pa.Schema
    primary_key: tuple[str, ...]
    temporal_semantics: dict[str, str]

    def validate_schema(self, table: pa.Table) -> None:
        if table.column_names != self.schema.names:
            raise SchemaValidationError(
                f"{self.name} columns differ from contract: "
                f"expected {self.schema.names}, got {table.column_names}"
            )
        try:
            table.cast(self.schema)
        except (pa.ArrowInvalid, pa.ArrowNotImplementedError) as exc:
            raise SchemaValidationError(f"{self.name} type mismatch: {exc}") from exc


UTC_TS = pa.timestamp("us", tz="UTC")
DATE = pa.date32()


SECURITY_MASTER = TableContract(
    "security_master",
    "1.0.0",
    pa.schema(
        [
            ("security_id", pa.string(), False),
            ("ticker", pa.string(), False),
            ("normalized_ticker", pa.string(), False),
            ("issuer_name", pa.string(), False),
            ("exchange", pa.string(), False),
            ("mic", pa.string()),
            ("asset_type", pa.string(), False),
            ("listing_type", pa.string(), False),
            ("currency", pa.string(), False),
            ("country", pa.string(), False),
            ("sector", pa.string()),
            ("industry", pa.string()),
            ("primary_listing", pa.bool_(), False),
            ("active", pa.bool_(), False),
            ("listing_start_date", DATE),
            ("listing_end_date", DATE),
            ("source", pa.string(), False),
            ("source_identifier", pa.string(), False),
            ("retrieval_timestamp", UTC_TS, False),
            ("availability_timestamp", UTC_TS, False),
            ("schema_version", pa.string(), False),
            ("metadata_quality_status", pa.string(), False),
        ]
    ),
    ("security_id",),
    {"availability_timestamp": "earliest permitted research availability"},
)

DAILY_MARKET = TableContract(
    "daily_market",
    "1.0.0",
    pa.schema(
        [
            ("security_id", pa.string(), False),
            ("ticker", pa.string(), False),
            ("trading_date", DATE, False),
            ("open", pa.float64()),
            ("high", pa.float64()),
            ("low", pa.float64()),
            ("close", pa.float64(), False),
            ("adjusted_close", pa.float64()),
            ("volume", pa.int64()),
            ("dividend", pa.float64()),
            ("split_factor", pa.float64()),
            ("currency", pa.string()),
            ("source", pa.string(), False),
            ("retrieval_timestamp", UTC_TS, False),
            ("schema_version", pa.string(), False),
        ]
    ),
    ("security_id", "trading_date"),
    {"trading_date": "exchange-local session date", "retrieval_timestamp": "provider retrieval"},
)

CORPORATE_ACTIONS = TableContract(
    "corporate_actions",
    "1.0.0",
    pa.schema(
        [
            ("security_id", pa.string(), False),
            ("action_id", pa.string(), False),
            ("action_type", pa.string(), False),
            ("effective_date", DATE, False),
            ("value", pa.float64(), False),
            ("currency", pa.string()),
            ("source", pa.string(), False),
            ("retrieval_timestamp", UTC_TS, False),
            ("schema_version", pa.string(), False),
        ]
    ),
    ("security_id", "action_id"),
    {"effective_date": "provider action effective date"},
)

MACRO_OBSERVATIONS = TableContract(
    "macro_observations",
    "1.0.0",
    pa.schema(
        [
            ("series_id", pa.string(), False),
            ("observation_date", DATE, False),
            ("value", pa.float64()),
            ("source_unit", pa.string(), False),
            ("frequency", pa.string(), False),
            ("seasonal_adjustment", pa.string()),
            ("source", pa.string(), False),
            ("retrieval_timestamp", UTC_TS, False),
            ("availability_timestamp", UTC_TS),
            ("missing_value", pa.bool_(), False),
            ("schema_version", pa.string(), False),
        ]
    ),
    ("series_id", "observation_date"),
    {"observation_date": "source observation period", "availability_timestamp": "release if known"},
)

FRENCH_FACTORS = TableContract(
    "french_factor_returns",
    "1.0.0",
    pa.schema(
        [
            ("factor_date", DATE, False),
            ("factor_name", pa.string(), False),
            ("factor_value", pa.float64(), False),
            ("frequency", pa.string(), False),
            ("source_unit", pa.string(), False),
            ("standardized_unit", pa.string(), False),
            ("dataset_identifier", pa.string(), False),
            ("source", pa.string(), False),
            ("retrieval_timestamp", UTC_TS, False),
            ("schema_version", pa.string(), False),
        ]
    ),
    ("dataset_identifier", "factor_date", "factor_name"),
    {"factor_date": "published factor-return date"},
)

SEC_FACTS = TableContract(
    "sec_financial_facts",
    "3.1.0",
    pa.schema(
        [
            ("issuer_id", pa.string(), False),
            ("security_id", pa.string()),
            ("ticker", pa.string()),
            ("cik", pa.string(), False),
            ("entity_name", pa.string(), False),
            ("taxonomy", pa.string(), False),
            ("concept", pa.string(), False),
            ("label", pa.string()),
            ("description", pa.string()),
            ("unit", pa.string(), False),
            ("value", pa.float64(), False),
            ("fiscal_year", pa.int32()),
            ("fiscal_period", pa.string()),
            ("period_start", DATE),
            ("period_end", DATE, False),
            ("filing_date", DATE, False),
            ("form", pa.string(), False),
            ("accession_number", pa.string()),
            ("frame", pa.string()),
            ("source", pa.string(), False),
            ("retrieval_timestamp", UTC_TS, False),
            ("availability_timestamp", UTC_TS, False),
            ("availability_quality", pa.string(), False),
            ("schema_version", pa.string(), False),
        ]
    ),
    (
        "cik",
        "taxonomy",
        "concept",
        "unit",
        "period_start",
        "period_end",
        "filing_date",
        "accession_number",
    ),
    {"filing_date": "SEC filing date", "availability_timestamp": "not before filing"},
)

SEC_SUBMISSIONS = TableContract(
    "sec_filing_submissions",
    "1.1.0",
    pa.schema(
        [
            ("issuer_id", pa.string(), False),
            ("cik", pa.string(), False),
            ("entity_name", pa.string(), False),
            ("accession_number", pa.string(), False),
            ("filing_date", DATE, False),
            ("report_date", DATE),
            ("acceptance_datetime_text", pa.string()),
            ("form", pa.string(), False),
            ("primary_document", pa.string()),
            ("is_xbrl", pa.bool_(), False),
            ("is_inline_xbrl", pa.bool_(), False),
            ("availability_timestamp", UTC_TS, False),
            ("availability_quality", pa.string(), False),
            ("retrieval_timestamp", UTC_TS, False),
            ("schema_version", pa.string(), False),
        ]
    ),
    ("cik", "accession_number"),
    {
        "filing_date": "SEC filing date",
        "acceptance_datetime_text": "verbatim SEC submissions value; no timezone inferred",
        "availability_timestamp": "acceptance only when offset-authenticated, else filing date",
    },
)

LISTING_LIFECYCLE = TableContract(
    "listing_lifecycle",
    "1.0.0",
    pa.schema(
        [
            ("symbol", pa.string(), False),
            ("name", pa.string(), False),
            ("exchange", pa.string(), False),
            ("asset_type", pa.string(), False),
            ("ipo_date", DATE),
            ("delisting_date", DATE),
            ("status", pa.string(), False),
            ("source_duplicate_count", pa.int64(), False),
            ("as_of_date", DATE, False),
            ("source", pa.string(), False),
            ("retrieval_timestamp", UTC_TS, False),
            ("schema_version", pa.string(), False),
        ]
    ),
    (
        "symbol",
        "name",
        "exchange",
        "ipo_date",
        "delisting_date",
        "as_of_date",
        "status",
    ),
    {"as_of_date": "requested historical listing-state date"},
)

FACTOR_MARKET_INPUT = TableContract(
    "factor_market_input",
    "1.0.0",
    pa.schema(
        [
            ("security_id", pa.string(), False),
            ("date", DATE, False),
            ("available_at", UTC_TS, False),
            ("eligible", pa.bool_(), False),
            ("eligibility_available_at", UTC_TS, False),
            ("sector", pa.string(), False),
            ("industry", pa.string(), False),
            ("classification_available_at", UTC_TS, False),
            ("return", pa.float64()),
            ("price", pa.float64()),
            ("high", pa.float64()),
            ("low", pa.float64()),
            ("volume", pa.float64()),
            ("shares_outstanding", pa.float64()),
            ("exchange", pa.string(), False),
            ("market_return", pa.float64()),
            ("risk_free", pa.float64()),
            ("benchmark_return", pa.float64()),
        ]
    ),
    ("security_id", "date"),
    {
        "available_at": "market observation availability",
        "eligibility_available_at": "point-in-time universe membership availability",
        "classification_available_at": "point-in-time classification availability",
    },
)

FACTOR_FUNDAMENTAL_INPUT = TableContract(
    "factor_fundamental_input",
    "1.0.0",
    pa.schema(
        [
            ("security_id", pa.string(), False),
            ("period_end", DATE, False),
            ("available_at", UTC_TS, False),
            ("field", pa.string(), False),
            ("value", pa.float64(), False),
            ("unit", pa.string(), False),
        ]
    ),
    ("security_id", "available_at", "field"),
    {"available_at": "actual filing or owner-evidenced public availability"},
)

CONTRACTS = {
    contract.name: contract
    for contract in [
        SECURITY_MASTER,
        DAILY_MARKET,
        CORPORATE_ACTIONS,
        MACRO_OBSERVATIONS,
        FRENCH_FACTORS,
        SEC_FACTS,
        SEC_SUBMISSIONS,
        LISTING_LIFECYCLE,
        FACTOR_MARKET_INPUT,
        FACTOR_FUNDAMENTAL_INPUT,
    ]
}
