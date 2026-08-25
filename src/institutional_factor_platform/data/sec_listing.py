"""Conservative projection of SEC-tagged cover facts into listing evidence."""

import re
from dataclasses import dataclass
from datetime import date, datetime

from institutional_factor_platform.data.domain import (
    IssuerId,
    IssuerListingMapping,
    MappingEvidence,
    MappingStatus,
)
from institutional_factor_platform.data.security_master import SymbolHistoryStore
from institutional_factor_platform.exceptions import SecurityMappingError

_TICKER = re.compile(r"[A-Z0-9][A-Z0-9.-]{0,11}")
_VENUES = {
    "NASDAQ": "XNAS",
    "NASDAQ STOCK MARKET LLC": "XNAS",
    "THE NASDAQ STOCK MARKET LLC": "XNAS",
    "NEW YORK STOCK EXCHANGE": "XNYS",
    "NYSE": "XNYS",
    "NYSE AMERICAN": "XASE",
    "NYSE AMERICAN LLC": "XASE",
}


@dataclass(frozen=True, slots=True)
class SecListingCandidate:
    issuer_id: IssuerId
    cik: str
    ticker: str
    security_title: str
    exchange_name: str
    mic: str
    filing_date: date
    accession_number: str
    context_ref: str
    dimensions_json: str
    retrieval_timestamp: datetime


@dataclass(frozen=True, slots=True)
class LegacySecTickerObservation:
    issuer_id: IssuerId
    cik: str
    tickers: tuple[str, ...]
    filing_date: date
    accession_number: str
    context_ref: str
    retrieval_timestamp: datetime


def project_legacy_sec_ticker_observations(
    records: tuple[dict[str, object], ...],
) -> tuple[LegacySecTickerObservation, ...]:
    """Project dimensionless legacy DEI ticker anchors without inferring a venue."""
    grouped: dict[tuple[str, str], list[dict[str, object]]] = {}
    for row in records:
        if row.get("concept") == "TradingSymbol" and row.get("dimensions_json") == "{}":
            grouped.setdefault(
                (str(row.get("cik", "")), str(row.get("accession_number", ""))), []
            ).append(row)
    output: list[LegacySecTickerObservation] = []
    for (cik, accession), rows in sorted(grouped.items()):
        ticker_sets = {_split_legacy_tickers(str(row.get("value", ""))) for row in rows}
        if len(ticker_sets) != 1:
            raise SecurityMappingError("Legacy SEC filing contains conflicting ticker anchors.")
        filing_dates = {row.get("filing_date") for row in rows}
        retrieval_times = {row.get("retrieval_timestamp") for row in rows}
        context_refs = {str(row.get("context_ref", "")) for row in rows}
        if (
            not cik.isdigit()
            or not accession
            or len(filing_dates) != 1
            or len(retrieval_times) != 1
            or len(context_refs) != 1
        ):
            raise SecurityMappingError("Legacy SEC ticker anchor lacks exact filing identity.")
        filing_date = next(iter(filing_dates))
        retrieved = next(iter(retrieval_times))
        if not isinstance(filing_date, date) or not isinstance(retrieved, datetime):
            raise SecurityMappingError("Legacy SEC ticker anchor has invalid timing.")
        if retrieved.tzinfo is None:
            raise SecurityMappingError("Legacy SEC ticker anchor retrieval time is naive.")
        output.append(
            LegacySecTickerObservation(
                IssuerId.from_cik(cik),
                cik.zfill(10),
                next(iter(ticker_sets)),
                filing_date,
                accession,
                next(iter(context_refs)),
                retrieved,
            )
        )
    return tuple(output)


def project_sec_listing_candidates(
    records: tuple[dict[str, object], ...],
) -> tuple[SecListingCandidate, ...]:
    """Return only exact same-context common-stock triples; never infer missing facts."""
    grouped: dict[tuple[str, str, str], list[dict[str, object]]] = {}
    for row in records:
        key = (
            str(row.get("cik", "")),
            str(row.get("accession_number", "")),
            str(row.get("context_ref", "")),
        )
        grouped.setdefault(key, []).append(row)
    candidates: list[SecListingCandidate] = []
    for (cik, accession, context_ref), rows in grouped.items():
        values = {
            concept: {
                str(row.get("value", "")).strip() for row in rows if row.get("concept") == concept
            }
            for concept in ("Security12bTitle", "TradingSymbol", "SecurityExchangeName")
        }
        if any(len(items) != 1 for items in values.values()):
            continue
        title = next(iter(values["Security12bTitle"]))
        if not _is_common_equity(title):
            continue
        ticker = next(iter(values["TradingSymbol"])).upper()
        if not _TICKER.fullmatch(ticker):
            raise SecurityMappingError("SEC filing contains an invalid common-stock ticker.")
        exchange = next(iter(values["SecurityExchangeName"]))
        mic = _VENUES.get(" ".join(exchange.upper().split()))
        if mic is None:
            raise SecurityMappingError(f"SEC filing contains an unsupported exchange: {exchange}")
        representative = rows[0]
        filing_date = representative.get("filing_date")
        retrieved = representative.get("retrieval_timestamp")
        if not cik.isdigit() or not isinstance(filing_date, date):
            raise SecurityMappingError("SEC listing candidate lacks filing identity.")
        if not isinstance(retrieved, datetime) or retrieved.tzinfo is None:
            raise SecurityMappingError("SEC listing candidate lacks an aware retrieval timestamp.")
        dimensions = {str(row.get("dimensions_json", "")) for row in rows}
        if len(dimensions) != 1:
            raise SecurityMappingError("SEC same-context listing facts disagree on dimensions.")
        candidates.append(
            SecListingCandidate(
                issuer_id=IssuerId.from_cik(cik),
                cik=cik.zfill(10),
                ticker=ticker,
                security_title=title,
                exchange_name=exchange,
                mic=mic,
                filing_date=filing_date,
                accession_number=accession,
                context_ref=context_ref,
                dimensions_json=next(iter(dimensions)),
                retrieval_timestamp=retrieved,
            )
        )
    identities = [(item.issuer_id, item.ticker, item.filing_date) for item in candidates]
    if len(identities) != len(set(identities)):
        raise SecurityMappingError("SEC filing contains duplicate common-stock listing candidates.")
    return tuple(sorted(candidates, key=lambda item: (item.cik, item.ticker)))


def bind_sec_listing_candidates(
    candidates: tuple[SecListingCandidate, ...], symbol_history: SymbolHistoryStore
) -> tuple[IssuerListingMapping, ...]:
    """Bind one filing's candidates only through an existing exact symbol authority."""
    accessions = {candidate.accession_number for candidate in candidates}
    if len(accessions) > 1:
        raise SecurityMappingError(
            "SEC candidate binding requires one filing; reconcile repeated observations separately."
        )
    mappings: list[IssuerListingMapping] = []
    for candidate in candidates:
        security_id = symbol_history.resolve(candidate.ticker, candidate.mic, candidate.filing_date)
        mappings.append(
            IssuerListingMapping(
                issuer_id=candidate.issuer_id,
                security_id=security_id,
                valid_from=candidate.filing_date,
                valid_to=None,
                status=MappingStatus.RESOLVED,
                evidence=MappingEvidence.SEC_FILING,
                provenance=(
                    f"SEC accession {candidate.accession_number}; "
                    f"context {candidate.context_ref}; {candidate.security_title}; "
                    f"{candidate.exchange_name}"
                ),
                retrieval_timestamp=candidate.retrieval_timestamp,
            )
        )
    return tuple(
        sorted(
            mappings,
            key=lambda item: (
                item.issuer_id.value,
                item.security_id.value if item.security_id else "",
            ),
        )
    )


def _is_common_equity(title: str) -> bool:
    normalized = " ".join(title.lower().split())
    rejected = ("note", "bond", "preferred", "depositary", "warrant", "unit")
    return ("common stock" in normalized or "capital stock" in normalized) and not any(
        term in normalized for term in rejected
    )


def _split_legacy_tickers(value: str) -> tuple[str, ...]:
    tickers = tuple(sorted({item.strip().upper() for item in value.split(",") if item.strip()}))
    if not tickers or any(_TICKER.fullmatch(item) is None for item in tickers):
        raise SecurityMappingError("Legacy SEC filing contains an invalid ticker anchor.")
    return tickers
