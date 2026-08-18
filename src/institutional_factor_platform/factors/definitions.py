"""Versioned institutional characteristic definitions and computations."""

from dataclasses import dataclass
from math import inf, log, nan, prod, sqrt

import pandas as pd

from institutional_factor_platform.factors.config import FactorConfig

FACTOR_VERSION = "1.0.0"


@dataclass(frozen=True, slots=True)
class FactorDefinition:
    factor_id: str
    definition: str
    formula: str
    rationale: str
    required_inputs: tuple[str, ...]
    unit: str
    direction: int
    research_notes: str


def _definition(
    factor_id: str,
    formula: str,
    rationale: str,
    inputs: tuple[str, ...],
    unit: str = "ratio",
    direction: int = 1,
    notes: str = "Project-specific characteristic; not an official provider factor.",
) -> FactorDefinition:
    return FactorDefinition(
        factor_id, factor_id.replace("_", " "), formula, rationale, inputs, unit, direction, notes
    )


FACTOR_DEFINITIONS: tuple[FactorDefinition, ...] = (
    _definition(
        "market_return",
        "approved broad-market total return",
        "Common market state",
        ("market_return",),
        "decimal_return",
    ),
    _definition(
        "excess_return",
        "market total return - risk-free return",
        "Broad-market return above cash",
        ("market_return", "risk_free"),
        "decimal_return",
    ),
    _definition(
        "risk_free_rate",
        "frequency-matched approved risk-free simple return",
        "Cash return and excess-return reference",
        ("risk_free",),
        "decimal_return",
    ),
    _definition(
        "rolling_market_beta",
        "rolling cov(return, market)/var(market)",
        "Systematic market sensitivity",
        ("return", "market_return"),
    ),
    _definition(
        "market_cap",
        "price * shares outstanding",
        "Equity scale",
        ("price", "shares_outstanding"),
        "USD",
        -1,
    ),
    _definition(
        "log_market_cap",
        "ln(market capitalization)",
        "Compressed firm scale",
        ("price", "shares_outstanding"),
        "log_USD",
        -1,
    ),
    _definition(
        "size_small",
        "market cap <= NYSE 30th percentile",
        "Small-cap membership",
        ("market_cap", "exchange"),
        "indicator",
    ),
    _definition(
        "size_mid",
        "NYSE 30th < market cap < NYSE 70th",
        "Mid-cap membership",
        ("market_cap", "exchange"),
        "indicator",
    ),
    _definition(
        "size_large",
        "market cap >= NYSE 70th percentile",
        "Large-cap membership",
        ("market_cap", "exchange"),
        "indicator",
    ),
    _definition(
        "book_to_market",
        "book equity / market capitalization",
        "Accounting value relative to price",
        ("book_equity", "market_cap"),
    ),
    _definition(
        "price_to_book",
        "market capitalization / book equity",
        "Price paid per book dollar",
        ("book_equity", "market_cap"),
        direction=-1,
    ),
    _definition(
        "earnings_yield",
        "net income / market capitalization",
        "Earnings cheapness",
        ("net_income", "market_cap"),
    ),
    _definition(
        "cash_flow_yield",
        "operating cash flow / market capitalization",
        "Cash-flow cheapness",
        ("operating_cash_flow", "market_cap"),
    ),
    _definition(
        "dividend_yield",
        "dividends / market capitalization",
        "Cash distribution yield",
        ("dividends", "market_cap"),
    ),
    _definition(
        "momentum_1m",
        "compound return over 21 sessions",
        "Short-horizon continuation",
        ("return",),
        "decimal_return",
    ),
    _definition(
        "momentum_3m",
        "compound return over 63 sessions",
        "Quarterly continuation",
        ("return",),
        "decimal_return",
    ),
    _definition(
        "momentum_6m",
        "compound return over 126 sessions",
        "Medium-horizon continuation",
        ("return",),
        "decimal_return",
    ),
    _definition(
        "momentum_12_1m",
        "compound return months 12 through 2",
        "Canonical momentum with one-month skip",
        ("return",),
        "decimal_return",
    ),
    _definition(
        "momentum_12m",
        "compound return over 252 sessions",
        "Annual continuation",
        ("return",),
        "decimal_return",
    ),
    _definition(
        "momentum_24m",
        "compound return over 504 sessions",
        "Long-horizon continuation",
        ("return",),
        "decimal_return",
    ),
    _definition(
        "residual_momentum",
        "compound residual return after rolling market beta",
        "Market-orthogonal continuation",
        ("return", "market_return"),
        "decimal_return",
    ),
    _definition(
        "roe",
        "net income / shareholder equity",
        "Profitability of equity capital",
        ("net_income", "shareholder_equity"),
    ),
    _definition(
        "roa",
        "net income / total assets",
        "Profitability of assets",
        ("net_income", "total_assets"),
    ),
    _definition(
        "gross_profitability",
        "gross profit / total assets",
        "Production profitability",
        ("gross_profit", "total_assets"),
    ),
    _definition(
        "operating_margin",
        "operating income / revenue",
        "Operating efficiency",
        ("operating_income", "revenue"),
    ),
    _definition(
        "net_margin", "net income / revenue", "Bottom-line efficiency", ("net_income", "revenue")
    ),
    _definition(
        "asset_turnover",
        "revenue / average assets",
        "Asset utilization",
        ("revenue", "average_assets"),
    ),
    _definition(
        "accruals",
        "total accruals / total assets",
        "Non-cash earnings intensity",
        ("total_accruals", "total_assets"),
        direction=-1,
    ),
    _definition(
        "leverage",
        "total debt / total assets",
        "Balance-sheet leverage",
        ("total_debt", "total_assets"),
        direction=-1,
    ),
    _definition(
        "debt_to_equity",
        "total debt / shareholder equity",
        "Debt burden relative to equity",
        ("total_debt", "shareholder_equity"),
        direction=-1,
    ),
    _definition(
        "interest_coverage",
        "operating income / interest expense",
        "Debt-service capacity",
        ("operating_income", "interest_expense"),
    ),
    _definition(
        "asset_growth",
        "total assets / prior total assets - 1",
        "Investment intensity",
        ("total_assets", "prior_total_assets"),
        "growth",
        -1,
    ),
    _definition(
        "capex_growth",
        "capital expenditure / prior capital expenditure - 1",
        "Capital investment expansion",
        ("capex", "prior_capex"),
        "growth",
        -1,
    ),
    _definition(
        "equity_issuance",
        "net equity issuance / shareholder equity",
        "External equity financing",
        ("net_equity_issuance", "shareholder_equity"),
        direction=-1,
    ),
    _definition(
        "working_capital_growth",
        "working capital / prior working capital - 1",
        "Operating investment expansion",
        ("working_capital", "prior_working_capital"),
        "growth",
        -1,
    ),
    _definition(
        "rolling_volatility",
        "annualized rolling standard deviation",
        "Total realized risk",
        ("return",),
        "annualized_volatility",
        -1,
    ),
    _definition(
        "downside_volatility",
        "annualized rolling standard deviation of negative returns",
        "Downside realized risk",
        ("return",),
        "annualized_volatility",
        -1,
    ),
    _definition(
        "semi_variance",
        "annualized mean squared negative return",
        "Downside dispersion",
        ("return",),
        "annualized_variance",
        -1,
    ),
    _definition(
        "beta",
        "rolling market beta",
        "Systematic sensitivity",
        ("return", "market_return"),
        direction=-1,
    ),
    _definition(
        "idiosyncratic_volatility",
        "annualized volatility of market residual",
        "Non-market risk",
        ("return", "market_return"),
        "annualized_volatility",
        -1,
    ),
    _definition(
        "average_dollar_volume",
        "rolling mean price * volume",
        "Tradable dollar activity",
        ("price", "volume"),
        "USD",
    ),
    _definition(
        "turnover",
        "volume / shares outstanding",
        "Trading intensity",
        ("volume", "shares_outstanding"),
    ),
    _definition(
        "amihud_illiquidity",
        "abs(return) / dollar volume",
        "Price impact per dollar",
        ("return", "price", "volume"),
        "inverse_USD",
        -1,
    ),
    _definition(
        "bid_ask_proxy",
        "(high-low) / midpoint",
        "Range-based spread proxy",
        ("high", "low"),
        direction=-1,
    ),
    _definition(
        "rolling_beta", "rolling market beta", "Systematic risk", ("return", "market_return")
    ),
    _definition(
        "rolling_correlation",
        "rolling correlation with market",
        "Market co-movement",
        ("return", "market_return"),
    ),
    _definition(
        "tracking_error",
        "annualized volatility of return-benchmark",
        "Active return risk",
        ("return", "benchmark_return"),
        "annualized_volatility",
        -1,
    ),
    _definition(
        "downside_beta",
        "cov(return, market)/var(market) on negative-market dates",
        "Bear-market sensitivity",
        ("return", "market_return"),
        direction=-1,
    ),
)

DEFINITION_BY_ID = {item.factor_id: item for item in FACTOR_DEFINITIONS}


def _safe_div(numerator: pd.Series, denominator: pd.Series) -> pd.Series:
    result = numerator / denominator.where(denominator != 0)
    return result.replace([inf, -inf], nan)


def _compound(series: pd.Series, window: int, minimum: int) -> pd.Series:
    return (1.0 + series).rolling(window, min_periods=minimum).apply(prod, raw=True) - 1.0


def compute_characteristics(panel: pd.DataFrame, config: FactorConfig) -> pd.DataFrame:
    """Compute the complete Phase 2 factor catalog without forward information."""
    frame = panel.sort_values(["security_id", "date"]).copy()
    group = frame.groupby("security_id", sort=False, group_keys=False)
    windows = config.windows
    minimum = windows.minimum_observations
    result = frame[["security_id", "date", "available_at", "sector", "industry"]].copy()
    result["market_return"] = frame["market_return"]
    result["excess_return"] = frame["market_return"] - frame["risk_free"]
    result["risk_free_rate"] = frame["risk_free"]
    rolling_cov = (
        group.apply(
            lambda part: (
                part["return"]
                .rolling(windows.one_year, min_periods=minimum)
                .cov(part["market_return"])
            ),
            include_groups=False,
        )
        .reset_index(level=0, drop=True)
        .sort_index()
    )
    rolling_var = group["market_return"].transform(
        lambda value: value.rolling(windows.one_year, min_periods=minimum).var()
    )
    beta = _safe_div(rolling_cov, rolling_var)
    result["rolling_market_beta"] = beta
    shares = frame["shares_outstanding"]
    result["market_cap"] = frame["price"] * shares
    result["log_market_cap"] = result["market_cap"].where(result["market_cap"] > 0).map(log)
    nyse = frame["exchange"].eq(config.breakpoints.exchange)
    breakpoints = (
        result.loc[nyse]
        .groupby("date")["market_cap"]
        .quantile([config.breakpoints.small_quantile, config.breakpoints.large_quantile])
        .unstack()
    )
    small = result["date"].map(breakpoints.get(config.breakpoints.small_quantile))
    large = result["date"].map(breakpoints.get(config.breakpoints.large_quantile))
    result["size_small"] = (result["market_cap"] <= small).astype(float).where(small.notna())
    result["size_mid"] = (
        ((result["market_cap"] > small) & (result["market_cap"] < large))
        .astype(float)
        .where(small.notna() & large.notna())
    )
    result["size_large"] = (result["market_cap"] >= large).astype(float).where(large.notna())

    ratios = {
        "book_to_market": ("book_equity", "market_cap", False),
        "price_to_book": ("market_cap", "book_equity", False),
        "earnings_yield": ("net_income", "market_cap", False),
        "cash_flow_yield": ("operating_cash_flow", "market_cap", False),
        "dividend_yield": ("dividends", "market_cap", False),
        "roe": ("net_income", "shareholder_equity", False),
        "roa": ("net_income", "total_assets", False),
        "gross_profitability": ("gross_profit", "total_assets", False),
        "operating_margin": ("operating_income", "revenue", False),
        "net_margin": ("net_income", "revenue", False),
        "asset_turnover": ("revenue", "average_assets", False),
        "accruals": ("total_accruals", "total_assets", False),
        "leverage": ("total_debt", "total_assets", False),
        "debt_to_equity": ("total_debt", "shareholder_equity", False),
        "interest_coverage": ("operating_income", "interest_expense", False),
        "asset_growth": ("total_assets", "prior_total_assets", True),
        "capex_growth": ("capex", "prior_capex", True),
        "equity_issuance": ("net_equity_issuance", "shareholder_equity", False),
        "working_capital_growth": ("working_capital", "prior_working_capital", True),
    }

    def available_column(name: str) -> pd.Series:
        if name in result:
            return result[name]
        if name in frame:
            return frame[name]
        return pd.Series(nan, index=frame.index, dtype="float64")

    for name, (numerator, denominator, subtract_one) in ratios.items():
        numerator_value = available_column(numerator)
        denominator_value = available_column(denominator)
        value = _safe_div(numerator_value, denominator_value)
        result[name] = value - 1.0 if subtract_one else value

    for name, window in (
        ("momentum_1m", windows.short),
        ("momentum_3m", windows.medium),
        ("momentum_6m", windows.half_year),
        ("momentum_12m", windows.one_year),
        ("momentum_24m", windows.two_year),
    ):
        result[name] = group["return"].transform(
            lambda value, w=window: _compound(value, w, minimum)
        )
    result["momentum_12_1m"] = group["return"].transform(
        lambda value: _compound(
            value.shift(windows.short), windows.one_year - windows.short, minimum
        )
    )
    residual = frame["return"] - beta * frame["market_return"]
    result["residual_momentum"] = residual.groupby(frame["security_id"]).transform(
        lambda value: _compound(
            value.shift(windows.short), windows.one_year - windows.short, minimum
        )
    )
    annual = sqrt(config.annualization_periods)
    result["rolling_volatility"] = (
        group["return"].transform(
            lambda value: value.rolling(windows.one_year, min_periods=minimum).std()
        )
        * annual
    )
    result["downside_volatility"] = (
        group["return"].transform(
            lambda value: (
                value.where(value < 0).rolling(windows.one_year, min_periods=minimum).std()
            )
        )
        * annual
    )
    result["semi_variance"] = (
        group["return"].transform(
            lambda value: (
                value.where(value < 0).pow(2).rolling(windows.one_year, min_periods=minimum).mean()
            )
        )
        * config.annualization_periods
    )
    result["beta"] = beta
    residual_daily = frame["return"] - beta * frame["market_return"]
    result["idiosyncratic_volatility"] = (
        residual_daily.groupby(frame["security_id"]).transform(
            lambda value: value.rolling(windows.one_year, min_periods=minimum).std()
        )
        * annual
    )
    dollar_volume = frame["price"] * frame["volume"]
    result["average_dollar_volume"] = dollar_volume.groupby(frame["security_id"]).transform(
        lambda value: value.rolling(windows.short, min_periods=minimum).mean()
    )
    result["turnover"] = _safe_div(frame["volume"], shares)
    result["amihud_illiquidity"] = _safe_div(frame["return"].abs(), dollar_volume)
    result["bid_ask_proxy"] = _safe_div(
        frame["high"] - frame["low"], (frame["high"] + frame["low"]) / 2.0
    )
    result["rolling_beta"] = beta
    result["rolling_correlation"] = (
        group.apply(
            lambda part: (
                part["return"]
                .rolling(windows.one_year, min_periods=minimum)
                .corr(part["market_return"])
            ),
            include_groups=False,
        )
        .reset_index(level=0, drop=True)
        .sort_index()
    )
    active = frame["return"] - frame["benchmark_return"]
    result["tracking_error"] = (
        active.groupby(frame["security_id"]).transform(
            lambda value: value.rolling(windows.one_year, min_periods=minimum).std()
        )
        * annual
    )

    def downside(part: pd.DataFrame) -> pd.Series:
        negative = part["market_return"].where(part["market_return"] < 0)
        covariance = (
            part["return"]
            .where(negative.notna())
            .rolling(windows.one_year, min_periods=minimum)
            .cov(negative)
        )
        variance = negative.rolling(windows.one_year, min_periods=minimum).var()
        return _safe_div(covariance, variance)

    result["downside_beta"] = (
        group.apply(downside, include_groups=False).reset_index(level=0, drop=True).sort_index()
    )
    return result
