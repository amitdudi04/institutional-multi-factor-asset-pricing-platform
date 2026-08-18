import zipfile
from datetime import UTC, date, datetime
from io import BytesIO

import httpx
import pyarrow as pa
import pytest

from institutional_factor_platform.data.config import load_phase1_config
from institutional_factor_platform.data.contracts import SEC_INLINE_XBRL
from institutional_factor_platform.data.domain import DataSource, RetrievalRequest
from institutional_factor_platform.data.sources.base import HttpTransport
from institutional_factor_platform.data.sources.sec_inline_xbrl import SecInlineXbrlAdapter
from institutional_factor_platform.exceptions import RetrievalError

CIK = "0001652044"
ACCESSION = "0001652044-24-000022"
DOCUMENT = "goog-20231231.htm"


def _complete(accession: str = ACCESSION, cik: str = CIK) -> bytes:
    return f"""<SEC-HEADER>
ACCESSION NUMBER: {accession}
CONFORMED SUBMISSION TYPE: 10-K
FILED AS OF DATE: 20240130
ACCEPTANCE-DATETIME: 20240130172115
CENTRAL INDEX KEY: {cik}
</SEC-HEADER>
""".encode()


def _document(context_ref: str = "class-a", document_type: str = "10-K") -> bytes:
    return f"""<!doctype html>
<html xmlns:ix="http://www.xbrl.org/2013/inlineXBRL">
<body>
<xbrli:context id="class-a">
  <xbrli:entity><xbrli:segment>
    <xbrldi:explicitMember dimension="dei:StatementClassOfStockAxis">
      goog:ClassACommonStockMember
    </xbrldi:explicitMember>
  </xbrli:segment></xbrli:entity>
  <xbrli:period><xbrli:instant>2023-12-31</xbrli:instant></xbrli:period>
</xbrli:context>
<ix:nonNumeric name="dei:DocumentType" contextRef="class-a">{document_type}</ix:nonNumeric>
<ix:nonNumeric name="dei:TradingSymbol" contextRef="{context_ref}">GOOGL</ix:nonNumeric>
<ix:nonNumeric name="dei:SecurityExchangeName" contextRef="class-a">NASDAQ</ix:nonNumeric>
<ix:nonNumeric name="dei:Security12bTitle" contextRef="class-a" continuedAt="title-rest">
  Class A
</ix:nonNumeric>
<ix:continuation id="title-rest">Common Stock</ix:continuation>
<ix:nonNumeric name="us-gaap:RevenueFromContractWithCustomerExcludingAssessedTax"
 contextRef="class-a">999</ix:nonNumeric>
</body></html>""".encode()


def _adapter(handler: object | None = None) -> SecInlineXbrlAdapter:
    settings = load_phase1_config().sources.sec.model_copy(
        update={"contact_email": "owner@example.invalid"}
    )
    transport = (
        httpx.MockTransport(handler)
        if callable(handler)
        else httpx.MockTransport(lambda _: httpx.Response(200))
    )
    return SecInlineXbrlAdapter(
        settings,
        HttpTransport(load_phase1_config().runtime, httpx.Client(transport=transport)),
        now=lambda: datetime(2026, 8, 18, tzinfo=UTC),
    )


def _request(**parameters: str) -> RetrievalRequest:
    return RetrievalRequest(
        DataSource.SEC_EDGAR,
        CIK,
        parameters={
            "accession_number": ACCESSION,
            "primary_document": DOCUMENT,
            **parameters,
        },
    )


def _bundle(complete: bytes | None = None, document: bytes | None = None) -> bytes:
    buffer = BytesIO()
    with zipfile.ZipFile(buffer, "w", compression=zipfile.ZIP_STORED) as archive:
        archive.writestr("complete-submission.txt", complete or _complete())
        archive.writestr("primary-document.html", document or _document())
    return buffer.getvalue()


def test_sec_inline_xbrl_preserves_exact_context_and_filters_to_approved_dei() -> None:
    records = _adapter().standardize(_bundle(), _request())
    assert [record["concept"] for record in records] == [
        "DocumentType",
        "TradingSymbol",
        "SecurityExchangeName",
        "Security12bTitle",
    ]
    assert records[1]["value"] == "GOOGL"
    assert records[1]["context_instant"] == date(2023, 12, 31)
    assert records[1]["dimensions_json"] == (
        '{"dei:StatementClassOfStockAxis":"goog:ClassACommonStockMember"}'
    )
    assert records[3]["value"] == "Class A Common Stock"
    assert records[0]["filing_date"] == date(2024, 1, 30)
    assert records[0]["availability_timestamp"] == datetime.max.replace(
        year=2024, month=1, day=30, tzinfo=UTC
    )
    table = pa.Table.from_pylist(records, schema=SEC_INLINE_XBRL.schema)
    SEC_INLINE_XBRL.validate_schema(table)

    bound_time = datetime(2026, 8, 18, 8, 5, 4, 841479, tzinfo=UTC)
    rebound = _adapter().standardize_at(_bundle(), _request(), bound_time)
    assert {record["retrieval_timestamp"] for record in rebound} == {bound_time}
    with pytest.raises(RetrievalError, match="timezone-aware"):
        _adapter().standardize_at(_bundle(), _request(), datetime(2026, 8, 18))


def test_sec_inline_xbrl_retrieval_uses_safe_official_archive_paths() -> None:
    observed: list[str] = []

    def response(request: httpx.Request) -> httpx.Response:
        observed.append(str(request.url))
        content = _complete() if request.url.path.endswith(".txt") else _document()
        return httpx.Response(200, content=content)

    payload = _adapter(response).retrieve(_request())
    assert observed == [
        "https://www.sec.gov/Archives/edgar/data/1652044/000165204424000022/0001652044-24-000022.txt",
        "https://www.sec.gov/Archives/edgar/data/1652044/000165204424000022/goog-20231231.htm",
    ]
    with zipfile.ZipFile(BytesIO(payload)) as archive:
        assert archive.namelist() == ["complete-submission.txt", "primary-document.html"]


def test_sec_inline_xbrl_rejects_unsafe_or_mismatched_evidence() -> None:
    with pytest.raises(RetrievalError, match="unsafe"):
        _adapter().retrieve(_request(primary_document="../secret"))
    with pytest.raises(RetrievalError, match="identity"):
        _adapter().standardize(
            _bundle(complete=_complete(accession="0001652044-24-000023")), _request()
        )
    with pytest.raises(RetrievalError, match="missing XBRL context"):
        _adapter().standardize(_bundle(document=_document("absent")), _request())
    with pytest.raises(RetrievalError, match="DocumentType"):
        _adapter().standardize(_bundle(document=_document(document_type="8-K")), _request())
    with pytest.raises(RetrievalError, match="Invalid SEC filing bundle"):
        _adapter().standardize(b"not-a-zip", _request())
