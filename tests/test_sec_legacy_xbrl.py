from datetime import UTC, date, datetime

import httpx
import pyarrow as pa
import pytest

from institutional_factor_platform.data.config import load_phase1_config
from institutional_factor_platform.data.contracts import SEC_LEGACY_XBRL
from institutional_factor_platform.data.domain import DataSource, RetrievalRequest
from institutional_factor_platform.data.sources.base import HttpTransport
from institutional_factor_platform.data.sources.sec_legacy_xbrl import SecLegacyXbrlAdapter
from institutional_factor_platform.exceptions import RetrievalError

CIK = "0000320193"
ACCESSION = "0000320193-12-000001"
PRIMARY = "aapl-20110924x10k.htm"


def _adapter(handler: object | None = None) -> SecLegacyXbrlAdapter:
    settings = load_phase1_config().sources.sec.model_copy(
        update={"contact_email": "owner@example.invalid"}
    )
    transport = httpx.MockTransport(handler if callable(handler) else lambda _: httpx.Response(200))
    return SecLegacyXbrlAdapter(
        settings,
        HttpTransport(load_phase1_config().runtime, httpx.Client(transport=transport)),
        now=lambda: datetime(2026, 8, 18, tzinfo=UTC),
    )


def _request() -> RetrievalRequest:
    return RetrievalRequest(
        DataSource.SEC_EDGAR,
        CIK,
        parameters={"accession_number": ACCESSION, "primary_document": PRIMARY},
    )


def _xml(*, cik: str = CIK, conflict: bool = False, namespace_year: int = 2011) -> bytes:
    duplicate = (
        '<dei:TradingSymbol contextRef="class-a">APLX</dei:TradingSymbol>'
        if conflict
        else '<dei:TradingSymbol contextRef="class-a">AAPL</dei:TradingSymbol>'
    )
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<xbrli:xbrl xmlns:xbrli="http://www.xbrl.org/2003/instance"
 xmlns:xbrldi="http://xbrl.org/2006/xbrldi"
 xmlns:dei="http://xbrl.sec.gov/dei/{namespace_year}"
 xmlns:iso4217="http://www.xbrl.org/2003/iso4217"
 xmlns:aapl="http://example.invalid/aapl">
 <xbrli:context id="class-a">
  <xbrli:entity><xbrli:identifier scheme="http://www.sec.gov/CIK">{cik}</xbrli:identifier>
   <xbrli:segment>
    <xbrldi:explicitMember dimension="dei:StatementClassOfStockAxis">
     aapl:CommonStockMember
    </xbrldi:explicitMember>
   </xbrli:segment>
  </xbrli:entity>
  <xbrli:period><xbrli:instant>2011-09-24</xbrli:instant></xbrli:period>
 </xbrli:context>
 <xbrli:unit id="shares"><xbrli:measure>xbrli:shares</xbrli:measure></xbrli:unit>
 <xbrli:unit id="usd"><xbrli:measure>iso4217:USD</xbrli:measure></xbrli:unit>
 <dei:DocumentType contextRef="class-a">10-K</dei:DocumentType>
 <dei:EntityCentralIndexKey contextRef="class-a">{cik}</dei:EntityCentralIndexKey>
 <dei:EntityRegistrantName contextRef="class-a">Apple Inc.</dei:EntityRegistrantName>
 <dei:TradingSymbol contextRef="class-a">AAPL</dei:TradingSymbol>
 <dei:TradingSymbol contextRef="class-a">AAPL</dei:TradingSymbol>
 {duplicate}
 <dei:SecurityExchangeName contextRef="class-a">NASDAQ</dei:SecurityExchangeName>
 <dei:Security12bTitle contextRef="class-a">Common Stock</dei:Security12bTitle>
 <dei:EntityCommonStockSharesOutstanding
  contextRef="class-a" unitRef="shares" decimals="-3">
  1000000
 </dei:EntityCommonStockSharesOutstanding>
 <dei:EntityPublicFloat contextRef="class-a" unitRef="usd" decimals="-6">
  500000000
 </dei:EntityPublicFloat>
 <aapl:UnsupportedFact contextRef="class-a">ignored</aapl:UnsupportedFact>
</xbrli:xbrl>""".encode()


def _submission(
    *,
    instance: bytes | None = None,
    accession: str = ACCESSION,
    instances: int = 1,
) -> bytes:
    header = f"""<SEC-HEADER>
ACCESSION NUMBER: {accession}
CONFORMED SUBMISSION TYPE: 10-K
FILED AS OF DATE: 20120125
ACCEPTANCE-DATETIME: 20120125170000
CENTRAL INDEX KEY: {CIK}
</SEC-HEADER>
""".encode()
    document = instance if instance is not None else _xml()
    blocks = b"".join(
        b"<DOCUMENT>\n<TYPE>EX-101.INS\n<FILENAME>instance"
        + str(index).encode()
        + b".xml\n<TEXT>"
        + document
        + b"</TEXT>\n</DOCUMENT>\n"
        for index in range(instances)
    )
    return header + blocks


def _sgml_wrapped_xml() -> bytes:
    return b"<XBRL>\n" + _xml() + b"\n</XBRL>"


def test_legacy_xbrl_extracts_governed_identity_shares_and_dimensions() -> None:
    records = _adapter().standardize(_submission(), _request())
    assert [row["concept"] for row in records] == [
        "DocumentType",
        "EntityCentralIndexKey",
        "EntityRegistrantName",
        "TradingSymbol",
        "SecurityExchangeName",
        "Security12bTitle",
        "EntityCommonStockSharesOutstanding",
        "EntityPublicFloat",
    ]
    shares = next(row for row in records if row["concept"] == "EntityCommonStockSharesOutstanding")
    assert shares["value"] == "1000000"
    assert shares["unit_measure"] == "xbrli:shares"
    assert shares["context_instant"] == date(2011, 9, 24)
    assert shares["dimensions_json"] == (
        '{"dei:StatementClassOfStockAxis":"aapl:CommonStockMember"}'
    )
    assert len(shares["instance_sha256"]) == 64
    SEC_LEGACY_XBRL.validate_schema(pa.Table.from_pylist(records, schema=SEC_LEGACY_XBRL.schema))
    rebound = _adapter().standardize_at(
        _submission(), _request(), datetime(2026, 8, 18, 8, 5, tzinfo=UTC)
    )
    assert records[0]["instance_sha256"] == rebound[0]["instance_sha256"]


def test_legacy_xbrl_retrieval_uses_only_the_complete_official_submission() -> None:
    observed: list[str] = []

    def response(request: httpx.Request) -> httpx.Response:
        observed.append(str(request.url))
        return httpx.Response(200, content=_submission())

    assert _adapter(response).retrieve(_request()) == _submission()
    assert observed == [
        "https://www.sec.gov/Archives/edgar/data/320193/000032019312000001/0000320193-12-000001.txt"
    ]


@pytest.mark.parametrize("instances, message", [(0, "no legacy"), (2, "ambiguous")])
def test_legacy_xbrl_rejects_missing_or_ambiguous_instances(instances: int, message: str) -> None:
    with pytest.raises(RetrievalError, match=message):
        _adapter().standardize(_submission(instances=instances), _request())


def test_legacy_xbrl_rejects_wrong_identity_malformed_and_conflicting_evidence() -> None:
    with pytest.raises(RetrievalError, match="identity"):
        _adapter().standardize(_submission(accession="0000320193-12-000002"), _request())
    with pytest.raises(RetrievalError, match="registrant"):
        _adapter().standardize(_submission(instance=_xml(cik="0000000001")), _request())
    with pytest.raises(RetrievalError, match="malformed"):
        _adapter().standardize(_submission(instance=b"<xbrli:xbrl>"), _request())
    with pytest.raises(RetrievalError, match="conflicting duplicate"):
        _adapter().standardize(_submission(instance=_xml(conflict=True)), _request())
    with pytest.raises(RetrievalError, match="prohibited"):
        _adapter().standardize(
            _submission(instance=b"<!DOCTYPE x [<!ENTITY a 'x'>]><x/>"), _request()
        )


def test_legacy_xbrl_accepts_governed_dei_namespace_variation() -> None:
    records = _adapter().standardize(_submission(instance=_xml(namespace_year=2018)), _request())
    assert any(row["concept"] == "TradingSymbol" and row["value"] == "AAPL" for row in records)
    wrapped = _adapter().standardize(_submission(instance=_sgml_wrapped_xml()), _request())
    assert any(row["concept"] == "TradingSymbol" for row in wrapped)
    historical = _xml().replace(b"http://xbrl.sec.gov/dei/2011", b"http://xbrl.us/dei/2009-01-31")
    assert any(
        row["concept"] == "TradingSymbol"
        for row in _adapter().standardize(_submission(instance=historical), _request())
    )


def test_legacy_xbrl_preserves_but_does_not_promote_dimensional_subsidiary_cik() -> None:
    extra = f"""
 <xbrli:context id="document">
  <xbrli:entity><xbrli:identifier scheme="http://www.sec.gov/CIK">{CIK}</xbrli:identifier>
  </xbrli:entity>
  <xbrli:period><xbrli:instant>2011-09-24</xbrli:instant></xbrli:period>
 </xbrli:context>
 <dei:EntityCentralIndexKey contextRef="document">{CIK}</dei:EntityCentralIndexKey>
 <xbrli:context id="subsidiary">
  <xbrli:entity><xbrli:identifier scheme="http://www.sec.gov/CIK">{CIK}</xbrli:identifier>
   <xbrli:segment><xbrldi:explicitMember dimension="dei:LegalEntityAxis">
    aapl:SubsidiaryMember
   </xbrldi:explicitMember></xbrli:segment>
  </xbrli:entity>
  <xbrli:period><xbrli:instant>2011-09-24</xbrli:instant></xbrli:period>
 </xbrli:context>
 <dei:EntityCentralIndexKey contextRef="subsidiary">0000000001</dei:EntityCentralIndexKey>
""".encode()
    instance = _xml().replace(b"</xbrli:xbrl>", extra + b"</xbrli:xbrl>")
    records = _adapter().standardize(_submission(instance=instance), _request())
    ciks = [row for row in records if row["concept"] == "EntityCentralIndexKey"]
    assert {row["value"] for row in ciks} == {CIK, "0000000001"}
    assert {row["dimensions_json"] for row in ciks} == {
        "{}",
        '{"dei:StatementClassOfStockAxis":"aapl:CommonStockMember"}',
        '{"dei:LegalEntityAxis":"aapl:SubsidiaryMember"}',
    }
