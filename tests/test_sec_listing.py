from datetime import UTC, date, datetime
from pathlib import Path

import pytest

from institutional_factor_platform.data.domain import (
    DataSource,
    MappingEvidence,
    SecurityId,
    SymbolHistoryRecord,
)
from institutional_factor_platform.data.sec_listing import (
    SecListingCandidate,
    bind_sec_listing_candidates,
    project_sec_listing_candidates,
)
from institutional_factor_platform.data.security_master import SymbolHistoryStore
from institutional_factor_platform.exceptions import SecurityMappingError


def _context(
    context: str,
    title: str,
    ticker: str,
    exchange: str = "Nasdaq",
    dimensions: str = "{}",
) -> list[dict[str, object]]:
    common: dict[str, object] = {
        "cik": "0000789019",
        "accession_number": "0001193125-26-323660",
        "context_ref": context,
        "filing_date": date(2026, 7, 29),
        "retrieval_timestamp": datetime(2026, 8, 18, tzinfo=UTC),
        "dimensions_json": dimensions,
    }
    return [
        {**common, "concept": "Security12bTitle", "value": title},
        {**common, "concept": "TradingSymbol", "value": ticker},
        {**common, "concept": "SecurityExchangeName", "value": exchange},
    ]


def test_sec_listing_projection_excludes_debt_with_reused_equity_ticker() -> None:
    records = tuple(
        _context("stock", "Common stock, $0.00000625 par value per share", "MSFT")
        + _context("note", "3.125% Notes due 2028", "MSFT")
    )
    candidates = project_sec_listing_candidates(records)
    assert len(candidates) == 1
    assert candidates[0].ticker == "MSFT"
    assert candidates[0].mic == "XNAS"
    assert candidates[0].context_ref == "stock"


def test_sec_listing_projection_preserves_multiple_common_share_classes() -> None:
    class_a = _context(
        "class-a",
        "Class A Common Stock, $0.001 par value",
        "GOOGL",
        "Nasdaq Stock Market LLC",
        '{"us-gaap:StatementClassOfStockAxis":"us-gaap:CommonClassAMember"}',
    )
    class_c = _context(
        "class-c",
        "Class C Capital Stock, $0.001 par value",
        "GOOG",
        "Nasdaq Stock Market LLC",
        '{"us-gaap:StatementClassOfStockAxis":"goog:CapitalClassCMember"}',
    )
    candidates = project_sec_listing_candidates(tuple(class_a + class_c))
    assert [item.ticker for item in candidates] == ["GOOG", "GOOGL"]


def test_sec_listing_projection_fails_on_unknown_venue_or_conflicting_triple() -> None:
    with pytest.raises(SecurityMappingError, match="unsupported exchange"):
        project_sec_listing_candidates(
            tuple(_context("stock", "Common Stock", "MSFT", "Unknown Venue"))
        )
    incomplete = tuple(_context("stock", "Common Stock", "MSFT")[:-1])
    assert project_sec_listing_candidates(incomplete) == ()
    original = _context("stock", "Common Stock", "MSFT")
    conflicting = (*original, {**original[1], "value": "MSFZ"})
    assert project_sec_listing_candidates(conflicting) == ()


def test_sec_listing_candidates_bind_only_through_exact_symbol_history(tmp_path: Path) -> None:
    records = tuple(_context("stock", "Common Stock", "MSFT"))
    candidate = project_sec_listing_candidates(records)[0]
    listing = SecurityId.assign()
    symbols = SymbolHistoryStore(tmp_path / "symbols.json")
    record = SymbolHistoryRecord(
        security_id=listing,
        ticker="MSFT",
        exchange="XNAS",
        mic="XNAS",
        valid_from=date(2020, 1, 1),
        valid_to=None,
        source=DataSource.SEC_EDGAR,
        source_identifier="0001193125-26-323660",
        retrieval_timestamp=datetime(2026, 8, 18, tzinfo=UTC),
        evidence_reference="synthetic SEC filing fixture",
    )
    symbols.persist((record,))
    mappings = bind_sec_listing_candidates((candidate,), symbols)
    assert mappings[0].security_id == listing
    assert mappings[0].evidence is MappingEvidence.SEC_FILING
    assert mappings[0].valid_from == date(2026, 7, 29)
    wrong = SymbolHistoryStore(tmp_path / "wrong-symbols.json")
    wrong.persist(
        (
            SymbolHistoryRecord(
                security_id=listing,
                ticker="OTHER",
                exchange="XNAS",
                mic="XNAS",
                valid_from=record.valid_from,
                valid_to=None,
                source=record.source,
                source_identifier=record.source_identifier,
                retrieval_timestamp=record.retrieval_timestamp,
                evidence_reference=record.evidence_reference,
            ),
        )
    )
    with pytest.raises(SecurityMappingError, match="unresolved or ambiguous"):
        bind_sec_listing_candidates((candidate,), wrong)
    another_filing = SecListingCandidate(
        issuer_id=candidate.issuer_id,
        cik=candidate.cik,
        ticker=candidate.ticker,
        security_title=candidate.security_title,
        exchange_name=candidate.exchange_name,
        mic=candidate.mic,
        filing_date=date(2026, 8, 1),
        accession_number="0001193125-26-999999",
        context_ref=candidate.context_ref,
        dimensions_json=candidate.dimensions_json,
        retrieval_timestamp=candidate.retrieval_timestamp,
    )
    with pytest.raises(SecurityMappingError, match="one filing"):
        bind_sec_listing_candidates((candidate, another_filing), symbols)
