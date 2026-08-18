"""Conservative projection of SEC-tagged cover facts into listing evidence."""

import re
from dataclasses import dataclass
from datetime import date, datetime

from institutional_factor_platform.data.domain import IssuerId
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


def _is_common_equity(title: str) -> bool:
    normalized = " ".join(title.lower().split())
    rejected = ("note", "bond", "preferred", "depositary", "warrant", "unit")
    return ("common stock" in normalized or "capital stock" in normalized) and not any(
        term in normalized for term in rejected
    )
