"""Versioned Phase 2 input and output contracts."""

import pyarrow as pa

from institutional_factor_platform.data.contracts import (
    FACTOR_FUNDAMENTAL_INPUT,
    FACTOR_MARKET_INPUT,
)

MARKET_SCHEMA = FACTOR_MARKET_INPUT.schema

FUNDAMENTAL_SCHEMA = FACTOR_FUNDAMENTAL_INPUT.schema

FACTOR_SCHEMA = pa.schema(
    [
        pa.field("security_id", pa.string(), nullable=False),
        pa.field("date", pa.date32(), nullable=False),
        pa.field("factor_id", pa.string(), nullable=False),
        pa.field("raw_value", pa.float64()),
        pa.field("winsorized_value", pa.float64()),
        pa.field("normalized_value", pa.float64()),
        pa.field("score_value", pa.float64()),
        pa.field("normalization_method", pa.string(), nullable=False),
        pa.field("available_at", pa.timestamp("us", tz="UTC"), nullable=False),
        pa.field("factor_version", pa.string(), nullable=False),
    ]
)

FACTOR_PORTFOLIO_SCHEMA = pa.schema(
    [
        pa.field("formation_date", pa.date32(), nullable=False),
        pa.field("date", pa.date32(), nullable=False),
        pa.field("factor_id", pa.string(), nullable=False),
        pa.field("quantile", pa.int8(), nullable=False),
        pa.field("security_count", pa.int32(), nullable=False),
        pa.field("value_weighted_return", pa.float64(), nullable=False),
        pa.field("benchmark_return", pa.float64(), nullable=False),
        pa.field("active_return", pa.float64(), nullable=False),
        pa.field("available_at", pa.timestamp("us", tz="UTC"), nullable=False),
        pa.field("factor_version", pa.string(), nullable=False),
    ]
)

MARKET_REQUIRED_UNITS = {
    "price_basis": "split_adjusted",
    "return_basis": "total_return",
    "return": "decimal_return",
    "price": "USD",
    "high": "USD",
    "low": "USD",
    "volume": "shares",
    "shares_outstanding": "shares",
    "market_return": "decimal_return",
    "risk_free": "decimal_return",
    "benchmark_return": "decimal_return",
}

REQUIRED_FUNDAMENTAL_FIELDS = frozenset(
    {
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
    }
)
