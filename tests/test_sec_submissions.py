import json
import zipfile
from datetime import UTC, date, datetime
from io import BytesIO

import httpx
import pytest

from institutional_factor_platform.data.config import load_phase1_config
from institutional_factor_platform.data.domain import DataSource, RetrievalRequest
from institutional_factor_platform.data.sources.base import HttpTransport
from institutional_factor_platform.data.sources.sec_submissions import SecSubmissionsAdapter
from institutional_factor_platform.exceptions import RetrievalError


def _adapter() -> SecSubmissionsAdapter:
    settings = load_phase1_config().sources.sec.model_copy(
        update={"contact_email": "owner@example.invalid"}
    )
    transport = HttpTransport(
        load_phase1_config().runtime,
        httpx.Client(transport=httpx.MockTransport(lambda _: httpx.Response(200))),
    )
    return SecSubmissionsAdapter(settings, transport, now=lambda: datetime(2026, 8, 18, tzinfo=UTC))


def _payload(acceptance: str = "2024-02-01T16:30:00-05:00") -> bytes:
    return json.dumps(
        {
            "cik": "1",
            "name": "Synthetic Registrant",
            "filings": {
                "recent": {
                    "accessionNumber": ["0000000001-24-000001"],
                    "filingDate": ["2024-02-01"],
                    "reportDate": ["2023-12-31"],
                    "acceptanceDateTime": [acceptance],
                    "form": ["10-K"],
                    "primaryDocument": ["annual-report.htm"],
                    "isXBRL": [1],
                    "isInlineXBRL": [1],
                }
            },
        }
    ).encode()


def test_sec_submissions_preserves_filing_identity_and_authenticated_acceptance() -> None:
    records = _adapter().standardize(_payload(), RetrievalRequest(DataSource.SEC_EDGAR, "1"))
    assert len(records) == 1
    assert records[0]["cik"] == "0000000001"
    assert records[0]["report_date"] == date(2023, 12, 31)
    assert records[0]["acceptance_datetime_text"] == "2024-02-01T16:30:00-05:00"
    assert records[0]["availability_timestamp"] == datetime(2024, 2, 1, 21, 30, tzinfo=UTC)
    assert records[0]["availability_quality"] == "SOURCE_TIMESTAMP"


def test_sec_submissions_does_not_infer_timezone_from_naive_acceptance() -> None:
    records = _adapter().standardize(
        _payload("2024-02-01T16:30:00"), RetrievalRequest(DataSource.SEC_EDGAR, "1")
    )
    assert records[0]["availability_timestamp"] == datetime.max.replace(
        year=2024, month=2, day=1, tzinfo=UTC
    )
    assert records[0]["availability_quality"] == "INFERRED_DATE_LEVEL"

    malformed = json.loads(_payload())
    malformed["filings"]["recent"]["form"] = []
    with pytest.raises(RetrievalError, match="inconsistent lengths"):
        _adapter().standardize(
            json.dumps(malformed).encode(), RetrievalRequest(DataSource.SEC_EDGAR, "1")
        )


def test_sec_submissions_retrieval_preserves_supplemental_provider_payloads() -> None:
    primary = json.loads(_payload())
    primary["filings"]["files"] = [{"name": "CIK0000000001-submissions-001.json", "filingCount": 1}]
    supplemental = dict(primary["filings"]["recent"])
    supplemental["accessionNumber"] = ["0000000001-20-000001"]
    supplemental["filingDate"] = ["2020-02-01"]
    supplemental["reportDate"] = ["2019-12-31"]

    def response(request: httpx.Request) -> httpx.Response:
        content = supplemental if request.url.path.endswith("submissions-001.json") else primary
        return httpx.Response(200, json=content)

    settings = load_phase1_config().sources.sec.model_copy(
        update={"contact_email": "owner@example.invalid"}
    )
    adapter = SecSubmissionsAdapter(
        settings,
        HttpTransport(
            load_phase1_config().runtime,
            httpx.Client(transport=httpx.MockTransport(response)),
        ),
        now=lambda: datetime(2026, 8, 18, tzinfo=UTC),
    )
    request = RetrievalRequest(DataSource.SEC_EDGAR, "1")
    payload = adapter.retrieve(request)
    with zipfile.ZipFile(BytesIO(payload)) as archive:
        assert archive.namelist() == [
            "primary.json",
            "CIK0000000001-submissions-001.json",
        ]
        assert json.loads(archive.read("primary.json")) == primary
        assert json.loads(archive.read(archive.namelist()[1])) == supplemental
    records = adapter.standardize(payload, request)
    assert {row["accession_number"] for row in records} == {
        "0000000001-24-000001",
        "0000000001-20-000001",
    }


def test_sec_submissions_preserves_historical_row_without_primary_document() -> None:
    payload = json.loads(_payload())
    payload["filings"]["recent"]["primaryDocument"] = [""]
    records = _adapter().standardize(
        json.dumps(payload).encode(), RetrievalRequest(DataSource.SEC_EDGAR, "1")
    )
    assert records[0]["primary_document"] is None
    assert records[0]["schema_version"] == "1.1.0"
