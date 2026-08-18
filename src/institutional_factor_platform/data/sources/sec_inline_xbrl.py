"""Official SEC filing-document adapter for tagged listing and share-class evidence."""

import json
import re
import zipfile
from collections.abc import Callable
from datetime import UTC, date, datetime, time
from html.parser import HTMLParser
from io import BytesIO

from institutional_factor_platform.data.config import SecSettings
from institutional_factor_platform.data.domain import DataSource, IssuerId, RetrievalRequest
from institutional_factor_platform.data.sources.base import HttpTransport, SourceAdapter
from institutional_factor_platform.exceptions import RetrievalError

_ACCESSION = re.compile(r"\d{10}-\d{2}-\d{6}")
_DOCUMENT = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]{0,254}")
_APPROVED_CONCEPTS = frozenset(
    {
        "DocumentType",
        "EntityRegistrantName",
        "Security12bTitle",
        "SecurityExchangeName",
        "TradingSymbol",
    }
)


class SecInlineXbrlAdapter(SourceAdapter[bytes]):
    """Preserve a complete submission and extract only exact tagged DEI cover facts."""

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
        cik, accession, primary_document = _request_identity(request)
        headers = {
            "User-Agent": self.settings.require_live_user_agent(),
            "Accept-Encoding": "gzip, deflate",
        }
        accession_compact = accession.replace("-", "")
        root = f"https://www.sec.gov/Archives/edgar/data/{int(cik)}/{accession_compact}"
        complete = self.transport.get(f"{root}/{accession}.txt", headers=headers)
        document = self.transport.get(f"{root}/{primary_document}", headers=headers)
        buffer = BytesIO()
        with zipfile.ZipFile(buffer, "w", compression=zipfile.ZIP_STORED) as archive:
            archive.writestr(_zip_info("complete-submission.txt"), complete)
            archive.writestr(_zip_info("primary-document.html"), document)
        return buffer.getvalue()

    def standardize(
        self, payload: bytes, request: RetrievalRequest
    ) -> tuple[dict[str, object], ...]:
        cik, accession, primary_document = _request_identity(request)
        complete, document = _parse_bundle(payload)
        filing_date, form, acceptance_text = _filing_header(complete, cik, accession)
        parser = _InlineXbrlParser()
        try:
            parser.feed(document.decode("utf-8-sig"))
            parser.close()
        except (UnicodeDecodeError, ValueError) as exc:
            raise RetrievalError(
                f"SEC primary document is not valid UTF-8 inline XBRL: {exc}"
            ) from exc
        facts = parser.records()
        if not facts:
            raise RetrievalError(
                "SEC primary document contains no approved tagged DEI cover facts."
            )
        document_types = {str(fact["value"]) for fact in facts if fact["concept"] == "DocumentType"}
        if document_types != {form}:
            raise RetrievalError(
                "SEC inline DocumentType does not match the complete-submission header."
            )
        retrieved = self.retrieval_timestamp(self.now)
        availability = datetime.combine(filing_date, time.max, tzinfo=UTC)
        issuer_id = IssuerId.from_cik(cik).value
        return tuple(
            {
                "issuer_id": issuer_id,
                "cik": cik,
                "accession_number": accession,
                "filing_date": filing_date,
                "acceptance_datetime_text": acceptance_text,
                "form": form,
                "primary_document": primary_document,
                "fact_ordinal": ordinal,
                "concept": fact["concept"],
                "context_ref": fact["context_ref"],
                "context_period_start": fact["period_start"],
                "context_period_end": fact["period_end"],
                "context_instant": fact["instant"],
                "dimensions_json": fact["dimensions_json"],
                "value": fact["value"],
                "source": self.source.value,
                "retrieval_timestamp": retrieved,
                "availability_timestamp": availability,
                "availability_quality": "INFERRED_DATE_LEVEL",
                "schema_version": "1.0.0",
            }
            for ordinal, fact in enumerate(facts, start=1)
        )


class _InlineXbrlParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.contexts: dict[str, dict[str, object]] = {}
        self.facts: list[dict[str, str]] = []
        self.continuations: dict[str, str] = {}
        self._context_id: str | None = None
        self._capture: tuple[str, str | None] | None = None
        self._text: list[str] = []
        self._fact: dict[str, str] | None = None

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        values = {key.lower(): value or "" for key, value in attrs}
        lowered = tag.lower()
        if lowered.endswith(":context"):
            context_id = values.get("id", "").strip()
            if context_id:
                self._context_id = context_id
                self.contexts[context_id] = {"dimensions": {}}
        elif self._context_id and lowered.endswith(
            (":startdate", ":enddate", ":instant", ":explicitmember")
        ):
            self._capture = (lowered.rsplit(":", 1)[-1], values.get("dimension"))
            self._text = []
        elif lowered.endswith(":nonnumeric"):
            name = values.get("name", "")
            concept = name.rsplit(":", 1)[-1]
            if concept in _APPROVED_CONCEPTS:
                context_ref = values.get("contextref", "").strip()
                if not context_ref:
                    raise ValueError("Tagged DEI cover fact lacks contextRef")
                self._fact = {
                    "concept": concept,
                    "context_ref": context_ref,
                    "continued_at": values.get("continuedat", "").strip(),
                }
                self._text = []
        elif lowered.endswith(":continuation"):
            continuation_id = values.get("id", "").strip()
            if continuation_id:
                self._capture = ("continuation", continuation_id)
                self._text = []

    def handle_data(self, data: str) -> None:
        if self._fact is not None or self._capture is not None:
            self._text.append(data)

    def handle_endtag(self, tag: str) -> None:
        lowered = tag.lower()
        if self._fact is not None and lowered.endswith(":nonnumeric"):
            self._fact["value"] = _normalized_text(self._text)
            self.facts.append(self._fact)
            self._fact = None
            self._text = []
        elif self._capture is not None and lowered.endswith(f":{self._capture[0]}"):
            kind, attribute = self._capture
            value = _normalized_text(self._text)
            if kind == "continuation" and attribute:
                self.continuations[attribute] = value
            elif self._context_id and kind == "explicitmember" and attribute:
                dimensions = self.contexts[self._context_id]["dimensions"]
                if isinstance(dimensions, dict):
                    dimensions[attribute] = value
            elif self._context_id:
                self.contexts[self._context_id][kind] = value
            self._capture = None
            self._text = []
        if lowered.endswith(":context"):
            self._context_id = None

    def records(self) -> list[dict[str, object]]:
        records: list[dict[str, object]] = []
        for fact in self.facts:
            context = self.contexts.get(fact["context_ref"])
            if context is None:
                raise RetrievalError("Tagged DEI cover fact references a missing XBRL context.")
            value = fact["value"]
            continued_at = fact["continued_at"]
            if continued_at:
                if continued_at not in self.continuations:
                    raise RetrievalError("Tagged DEI cover fact continuation is missing.")
                value = " ".join(f"{value} {self.continuations[continued_at]}".split())
            if not value:
                raise RetrievalError("Tagged DEI cover fact has an empty value.")
            dimensions = context.get("dimensions", {})
            records.append(
                {
                    "concept": fact["concept"],
                    "context_ref": fact["context_ref"],
                    "period_start": _date_or_none(context.get("startdate")),
                    "period_end": _date_or_none(context.get("enddate")),
                    "instant": _date_or_none(context.get("instant")),
                    "dimensions_json": json.dumps(
                        dimensions, sort_keys=True, separators=(",", ":")
                    ),
                    "value": value,
                }
            )
        return records


def _request_identity(request: RetrievalRequest) -> tuple[str, str, str]:
    cik = request.dataset.zfill(10)
    accession = str(request.parameters.get("accession_number", "")).strip()
    primary_document = str(request.parameters.get("primary_document", "")).strip()
    if len(cik) != 10 or not cik.isdigit():
        raise RetrievalError(f"Invalid SEC CIK: {request.dataset}")
    if not _ACCESSION.fullmatch(accession):
        raise RetrievalError("SEC accession number is invalid.")
    if not _DOCUMENT.fullmatch(primary_document) or ".." in primary_document:
        raise RetrievalError("SEC primary-document name is unsafe.")
    return cik, accession, primary_document


def _parse_bundle(payload: bytes) -> tuple[bytes, bytes]:
    try:
        with zipfile.ZipFile(BytesIO(payload)) as archive:
            if archive.namelist() != ["complete-submission.txt", "primary-document.html"]:
                raise RetrievalError("SEC filing bundle layout is invalid.")
            return archive.read("complete-submission.txt"), archive.read("primary-document.html")
    except (KeyError, zipfile.BadZipFile) as exc:
        raise RetrievalError(f"Invalid SEC filing bundle: {exc}") from exc


def _filing_header(payload: bytes, cik: str, accession: str) -> tuple[date, str, str | None]:
    text = payload.decode("latin-1")
    accession_value = _header_value(text, "ACCESSION NUMBER")
    filing_value = _header_value(text, "FILED AS OF DATE")
    form = _header_value(text, "CONFORMED SUBMISSION TYPE")
    acceptance = _optional_header_value(text, "ACCEPTANCE-DATETIME")
    ciks = set(re.findall(r"CENTRAL INDEX KEY:\s*(\d{1,10})", text))
    if accession_value != accession or cik.lstrip("0") not in {value.lstrip("0") for value in ciks}:
        raise RetrievalError("SEC filing bundle identity does not match the request.")
    try:
        filing_date = datetime.strptime(filing_value, "%Y%m%d").date()
    except ValueError as exc:
        raise RetrievalError("SEC filing header date is invalid.") from exc
    return filing_date, form, acceptance


def _header_value(text: str, label: str) -> str:
    value = _optional_header_value(text, label)
    if not value:
        raise RetrievalError(f"SEC filing header lacks {label}.")
    return value


def _optional_header_value(text: str, label: str) -> str | None:
    match = re.search(rf"(?m)^\s*{re.escape(label)}:\s*(\S.*?)\s*$", text)
    return match.group(1).strip() if match else None


def _date_or_none(value: object) -> date | None:
    if not isinstance(value, str) or not value:
        return None
    try:
        return date.fromisoformat(value)
    except ValueError as exc:
        raise RetrievalError("SEC XBRL context contains an invalid date.") from exc


def _normalized_text(values: list[str]) -> str:
    return " ".join("".join(values).split())


def _zip_info(name: str) -> zipfile.ZipInfo:
    info = zipfile.ZipInfo(name, date_time=(1980, 1, 1, 0, 0, 0))
    info.compress_type = zipfile.ZIP_STORED
    return info
