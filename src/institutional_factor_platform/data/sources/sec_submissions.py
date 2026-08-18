"""SEC submissions metadata adapter for filing identity and cover-document discovery."""

import json
import re
import zipfile
from collections.abc import Callable
from datetime import UTC, date, datetime, time
from io import BytesIO

from institutional_factor_platform.data.config import SecSettings
from institutional_factor_platform.data.domain import DataSource, IssuerId, RetrievalRequest
from institutional_factor_platform.data.sources.base import HttpTransport, SourceAdapter
from institutional_factor_platform.exceptions import RetrievalError


class SecSubmissionsAdapter(SourceAdapter[bytes]):
    source = DataSource.SEC_EDGAR

    def __init__(
        self,
        settings: SecSettings,
        transport: HttpTransport,
        now: Callable[[], datetime] = lambda: datetime.now(UTC),
    ) -> None:
        self.settings = settings
        self.transport = transport
        self.now = now

    def retrieve(self, request: RetrievalRequest) -> bytes:
        cik = request.dataset.zfill(10)
        if len(cik) != 10 or not cik.isdigit():
            raise RetrievalError(f"Invalid SEC CIK: {request.dataset}")
        headers = {
            "User-Agent": self.settings.require_live_user_agent(),
            "Accept-Encoding": "gzip, deflate",
        }
        primary = self.transport.get(
            f"https://data.sec.gov/submissions/CIK{cik}.json",
            headers=headers,
        )
        try:
            data = json.loads(primary)
        except json.JSONDecodeError as exc:
            raise RetrievalError(f"Invalid SEC submissions JSON: {exc}") from exc
        filings = data.get("filings")
        supplemental = filings.get("files", []) if isinstance(filings, dict) else []
        if not isinstance(supplemental, list):
            raise RetrievalError("SEC submissions supplemental-file index is invalid.")
        buffer = BytesIO()
        with zipfile.ZipFile(buffer, "w", compression=zipfile.ZIP_STORED) as archive:
            archive.writestr(_zip_info("primary.json"), primary)
            for item in supplemental:
                name = item.get("name") if isinstance(item, dict) else None
                if not isinstance(name, str) or not re.fullmatch(
                    rf"CIK{cik}-submissions-\d{{3}}\.json", name
                ):
                    raise RetrievalError("SEC submissions supplemental filename is unsafe.")
                content = self.transport.get(
                    f"https://data.sec.gov/submissions/{name}", headers=headers
                )
                archive.writestr(_zip_info(name), content)
        return buffer.getvalue()

    def standardize(
        self, payload: bytes, request: RetrievalRequest
    ) -> tuple[dict[str, object], ...]:
        data, supplemental = _parse_payload(payload)
        cik = str(data.get("cik", "")).zfill(10)
        entity = data.get("name")
        filings = data.get("filings")
        recent = filings.get("recent") if isinstance(filings, dict) else None
        if not cik.isdigit() or not entity or not isinstance(recent, dict):
            raise RetrievalError("SEC submissions lacks required registrant or filing metadata.")
        retrieved = self.now()
        issuer_id = IssuerId.from_cik(cik).value
        records: list[dict[str, object]] = []
        records.extend(_standardize_arrays(recent, cik, str(entity), issuer_id, retrieved))
        for arrays in supplemental:
            records.extend(_standardize_arrays(arrays, cik, str(entity), issuer_id, retrieved))
        if not records:
            raise RetrievalError("SEC submissions contains no filings.")
        return tuple(records)


def _standardize_arrays(
    arrays: dict[str, object],
    cik: str,
    entity: str,
    issuer_id: str,
    retrieved: datetime,
) -> list[dict[str, object]]:
    required = (
        "accessionNumber",
        "filingDate",
        "reportDate",
        "acceptanceDateTime",
        "form",
        "primaryDocument",
        "isXBRL",
        "isInlineXBRL",
    )
    columns = {name: arrays.get(name) for name in required}
    if not all(isinstance(value, list) for value in columns.values()):
        raise RetrievalError("SEC submissions filing arrays are incomplete.")
    lengths = {len(value) for value in columns.values() if isinstance(value, list)}
    if len(lengths) != 1:
        raise RetrievalError("SEC submissions filing arrays have inconsistent lengths.")
    records: list[dict[str, object]] = []
    for index in range(next(iter(lengths), 0)):
        accession = str(columns["accessionNumber"][index]).strip()  # type: ignore[index]
        filing_text = str(columns["filingDate"][index]).strip()  # type: ignore[index]
        form = str(columns["form"][index]).strip()  # type: ignore[index]
        primary_document = str(columns["primaryDocument"][index]).strip()  # type: ignore[index]
        if not accession or not filing_text or not form:
            raise RetrievalError("SEC submissions filing identity contains an empty field.")
        try:
            filing_date = date.fromisoformat(filing_text)
        except ValueError as exc:
            raise RetrievalError("SEC submissions filing date is invalid.") from exc
        report_text = str(columns["reportDate"][index]).strip()  # type: ignore[index]
        acceptance_text = str(columns["acceptanceDateTime"][index]).strip()  # type: ignore[index]
        availability, quality = _availability(acceptance_text, filing_date)
        records.append(
            {
                "issuer_id": issuer_id,
                "cik": cik,
                "entity_name": entity,
                "accession_number": accession,
                "filing_date": filing_date,
                "report_date": date.fromisoformat(report_text) if report_text else None,
                "acceptance_datetime_text": acceptance_text or None,
                "form": form,
                "primary_document": primary_document or None,
                "is_xbrl": bool(int(columns["isXBRL"][index])),  # type: ignore[index]
                "is_inline_xbrl": bool(int(columns["isInlineXBRL"][index])),  # type: ignore[index]
                "availability_timestamp": availability,
                "availability_quality": quality,
                "retrieval_timestamp": retrieved,
                "schema_version": "1.1.0",
            }
        )
    return records


def _parse_payload(payload: bytes) -> tuple[dict[str, object], list[dict[str, object]]]:
    try:
        if payload.startswith(b"PK"):
            with zipfile.ZipFile(BytesIO(payload)) as archive:
                names = archive.namelist()
                if not names or names[0] != "primary.json" or len(names) != len(set(names)):
                    raise RetrievalError("SEC submissions bundle layout is invalid.")
                primary = json.loads(archive.read("primary.json"))
                supplemental = [json.loads(archive.read(name)) for name in names[1:]]
        else:
            primary = json.loads(payload)
            supplemental = []
    except (json.JSONDecodeError, KeyError, zipfile.BadZipFile) as exc:
        raise RetrievalError(f"Invalid SEC submissions payload: {exc}") from exc
    if not isinstance(primary, dict) or not all(isinstance(item, dict) for item in supplemental):
        raise RetrievalError("SEC submissions payload objects are invalid.")
    return primary, supplemental


def _zip_info(name: str) -> zipfile.ZipInfo:
    info = zipfile.ZipInfo(name, date_time=(1980, 1, 1, 0, 0, 0))
    info.compress_type = zipfile.ZIP_STORED
    return info


def _availability(value: str, filing_date: date) -> tuple[datetime, str]:
    if value:
        try:
            parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError:
            parsed = None
        if parsed is not None and parsed.tzinfo is not None:
            return parsed.astimezone(UTC), "SOURCE_TIMESTAMP"
    return datetime.combine(filing_date, time.max, tzinfo=UTC), "INFERRED_DATE_LEVEL"
