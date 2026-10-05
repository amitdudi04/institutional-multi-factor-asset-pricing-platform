"""Parser for legacy SEC XBRL instances embedded in complete submissions."""

import hashlib
import re
import xml.etree.ElementTree as ET
from collections.abc import Callable
from datetime import UTC, date, datetime, time
from decimal import Decimal, InvalidOperation

from institutional_factor_platform.data.config import SecSettings
from institutional_factor_platform.data.domain import DataSource, IssuerId, RetrievalRequest
from institutional_factor_platform.data.sources.base import HttpTransport, SourceAdapter
from institutional_factor_platform.data.sources.sec_inline_xbrl import (
    _filing_header,
    _request_identity,
)
from institutional_factor_platform.exceptions import RetrievalError

PARSER_VERSION = "1.0.0"
_APPROVED = frozenset(
    {
        "DocumentType",
        "EntityCentralIndexKey",
        "EntityRegistrantName",
        "Security12bTitle",
        "SecurityExchangeName",
        "TradingSymbol",
        "EntityCommonStockSharesOutstanding",
        "EntityPublicFloat",
    }
)
_NUMERIC = frozenset({"EntityCommonStockSharesOutstanding", "EntityPublicFloat"})


class SecLegacyXbrlAdapter(SourceAdapter[bytes]):
    """Preserve one complete filing and parse one unambiguous EX-101.INS attachment."""

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
        cik, accession, _ = _request_identity(request)
        headers = {
            "User-Agent": self.settings.require_live_user_agent(),
            "Accept-Encoding": "gzip, deflate",
        }
        compact = accession.replace("-", "")
        return self.transport.get(
            f"https://www.sec.gov/Archives/edgar/data/{int(cik)}/{compact}/{accession}.txt",
            headers=headers,
        )

    def standardize(
        self, payload: bytes, request: RetrievalRequest
    ) -> tuple[dict[str, object], ...]:
        cik, accession, primary_document = _request_identity(request)
        filing_date, form, acceptance_text = _filing_header(payload, cik, accession)
        instance_name, instance = _discover_instance(payload)
        facts = _parse_instance(instance, cik, form)
        retrieved = self.retrieval_timestamp(self.now)
        availability = datetime.combine(filing_date, time.max, tzinfo=UTC)
        issuer_id = IssuerId.from_cik(cik).value
        checksum = hashlib.sha256(instance).hexdigest()
        return tuple(
            {
                "issuer_id": issuer_id,
                "cik": cik,
                "accession_number": accession,
                "filing_date": filing_date,
                "acceptance_datetime_text": acceptance_text,
                "form": form,
                "primary_document": primary_document,
                "instance_document": instance_name,
                "instance_sha256": checksum,
                "fact_ordinal": ordinal,
                "concept": fact["concept"],
                "context_ref": fact["context_ref"],
                "context_period_start": fact["period_start"],
                "context_period_end": fact["period_end"],
                "context_instant": fact["instant"],
                "dimensions_json": fact["dimensions_json"],
                "value": fact["value"],
                "unit_ref": fact["unit_ref"],
                "unit_measure": fact["unit_measure"],
                "decimals": fact["decimals"],
                "source": self.source.value,
                "retrieval_timestamp": retrieved,
                "availability_timestamp": availability,
                "availability_quality": "INFERRED_DATE_LEVEL",
                "parser_version": PARSER_VERSION,
                "schema_version": "1.0.0",
            }
            for ordinal, fact in enumerate(facts, start=1)
        )


def _discover_instance(payload: bytes) -> tuple[str, bytes]:
    instances: list[tuple[str, bytes]] = []
    for match in re.finditer(rb"(?is)<DOCUMENT>(.*?)</DOCUMENT>", payload):
        block = match.group(1)
        document_type = _block_value(block, b"TYPE")
        if document_type.upper() != "EX-101.INS":
            continue
        filename = _block_value(block, b"FILENAME")
        if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]{0,254}", filename):
            raise RetrievalError("SEC legacy XBRL instance filename is unsafe.")
        text = re.search(rb"(?is)<TEXT>(.*?)(?:</TEXT>|$)", block)
        if text is None or not text.group(1).strip():
            raise RetrievalError("SEC legacy XBRL instance attachment is empty.")
        instances.append((filename, _unwrap_sgml_xbrl(text.group(1).strip())))
    if not instances:
        raise RetrievalError("SEC complete submission contains no legacy XBRL instance.")
    if len(instances) != 1:
        raise RetrievalError("SEC complete submission contains ambiguous legacy XBRL instances.")
    return instances[0]


def _unwrap_sgml_xbrl(payload: bytes) -> bytes:
    """Remove the legacy SEC `<XBRL>` SGML envelope around the actual XML instance."""
    match = re.fullmatch(rb"(?is)<XBRL>\s*(.*?)\s*</XBRL>", payload)
    return match.group(1).strip() if match is not None else payload


def _block_value(block: bytes, label: bytes) -> str:
    match = re.search(rb"(?im)^\s*<" + label + rb">\s*([^\r\n<]+)", block)
    if match is None:
        raise RetrievalError(f"SEC legacy XBRL attachment lacks {label.decode()}.")
    try:
        return match.group(1).decode("ascii", errors="strict").strip()
    except UnicodeDecodeError as exc:
        raise RetrievalError("SEC legacy XBRL attachment identity is not ASCII.") from exc


def _parse_instance(payload: bytes, cik: str, form: str) -> list[dict[str, object]]:
    upper = payload.upper()
    if b"<!DOCTYPE" in upper or b"<!ENTITY" in upper:
        raise RetrievalError("SEC legacy XBRL instance contains prohibited XML declarations.")
    try:
        root = ET.fromstring(payload)
    except ET.ParseError as exc:
        raise RetrievalError(f"SEC legacy XBRL instance is malformed: {exc}") from exc
    if _local(root.tag).lower() != "xbrl":
        raise RetrievalError("SEC legacy XBRL attachment root is not xbrl.")

    contexts = _contexts(root, cik)
    units = _units(root)
    records: list[dict[str, object]] = []
    identities: dict[tuple[str, str, str | None], str] = {}
    for element in root:
        concept = _local(element.tag)
        if concept not in _APPROVED or not _is_dei(element.tag):
            continue
        context_ref = element.attrib.get("contextRef", "").strip()
        if context_ref not in contexts:
            raise RetrievalError("SEC legacy DEI fact references a missing context.")
        value = " ".join("".join(element.itertext()).split())
        if not value:
            raise RetrievalError("SEC legacy DEI fact has an empty value.")
        unit_ref = element.attrib.get("unitRef")
        unit_measure = None
        decimals = element.attrib.get("decimals")
        if concept in _NUMERIC:
            if not unit_ref or unit_ref not in units:
                raise RetrievalError("SEC legacy numeric DEI fact has an unresolved unit.")
            unit_measure = units[unit_ref]
            try:
                if not Decimal(value).is_finite():
                    raise InvalidOperation
            except InvalidOperation as exc:
                raise RetrievalError("SEC legacy numeric DEI fact is invalid.") from exc
        key = (concept, context_ref, unit_ref)
        if key in identities:
            if identities[key] != value:
                raise RetrievalError("SEC legacy XBRL contains conflicting duplicate facts.")
            continue
        identities[key] = value
        context = contexts[context_ref]
        records.append(
            {
                "concept": concept,
                "context_ref": context_ref,
                "period_start": context["period_start"],
                "period_end": context["period_end"],
                "instant": context["instant"],
                "dimensions_json": context["dimensions_json"],
                "value": value,
                "unit_ref": unit_ref,
                "unit_measure": unit_measure,
                "decimals": decimals,
            }
        )
    if not records:
        raise RetrievalError("SEC legacy XBRL instance contains no approved DEI facts.")
    document_types = {row["value"] for row in records if row["concept"] == "DocumentType"}
    if document_types != {form}:
        raise RetrievalError("SEC legacy DocumentType does not match the filing header.")
    reported_ciks = {
        str(row["value"]).zfill(10)
        for row in records
        if row["concept"] == "EntityCentralIndexKey" and row["dimensions_json"] == "{}"
    }
    if reported_ciks and reported_ciks != {cik}:
        raise RetrievalError("SEC legacy registrant CIK does not match the filing header.")
    return records


def _contexts(root: ET.Element, cik: str) -> dict[str, dict[str, object]]:
    result: dict[str, dict[str, object]] = {}
    for element in root:
        if _local(element.tag) != "context":
            continue
        context_id = element.attrib.get("id", "").strip()
        if not context_id or context_id in result:
            raise RetrievalError("SEC legacy XBRL context identity is invalid.")
        identifiers = [
            "".join(item.itertext()).strip()
            for item in element.iter()
            if _local(item.tag) == "identifier"
        ]
        if len(identifiers) != 1 or identifiers[0].lstrip("0") != cik.lstrip("0"):
            raise RetrievalError("SEC legacy XBRL context registrant is mismatched.")
        dimensions: dict[str, str] = {}
        for item in element.iter():
            local = _local(item.tag)
            if local not in {"explicitMember", "typedMember"}:
                continue
            dimension = item.attrib.get("dimension", "").strip()
            value = " ".join("".join(item.itertext()).split())
            if not dimension or not value or dimension in dimensions:
                raise RetrievalError("SEC legacy XBRL context dimensions are invalid.")
            dimensions[dimension] = value
        result[context_id] = {
            "period_start": _child_date(element, "startDate"),
            "period_end": _child_date(element, "endDate"),
            "instant": _child_date(element, "instant"),
            "dimensions_json": _json_dimensions(dimensions),
        }
    return result


def _units(root: ET.Element) -> dict[str, str]:
    result: dict[str, str] = {}
    for element in root:
        if _local(element.tag) != "unit":
            continue
        unit_id = element.attrib.get("id", "").strip()
        measures = [
            " ".join("".join(item.itertext()).split())
            for item in element.iter()
            if _local(item.tag) == "measure"
        ]
        if not unit_id or not measures or unit_id in result:
            raise RetrievalError("SEC legacy XBRL unit identity is invalid.")
        result[unit_id] = "*".join(measures)
    return result


def _child_date(element: ET.Element, name: str) -> date | None:
    values = [item.text for item in element.iter() if _local(item.tag) == name]
    if not values:
        return None
    if len(values) != 1 or values[0] is None:
        raise RetrievalError("SEC legacy XBRL context period is invalid.")
    try:
        return date.fromisoformat(values[0].strip())
    except ValueError as exc:
        raise RetrievalError("SEC legacy XBRL context date is invalid.") from exc


def _local(tag: str) -> str:
    return tag.rsplit("}", 1)[-1].rsplit(":", 1)[-1]


def _is_dei(tag: str) -> bool:
    namespace = tag[1:].split("}", 1)[0].lower() if tag.startswith("{") else ""
    return "xbrl.sec.gov/dei" in namespace or "xbrl.us/dei" in namespace


def _json_dimensions(dimensions: dict[str, str]) -> str:
    import json

    return json.dumps(dimensions, sort_keys=True, separators=(",", ":"))
