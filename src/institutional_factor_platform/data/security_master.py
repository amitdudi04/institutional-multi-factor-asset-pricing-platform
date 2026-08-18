"""Versioned security-master eligibility and persisted cross-source mappings."""

import json
from collections import Counter
from datetime import date
from pathlib import Path

from institutional_factor_platform.data.config import UniverseSettings
from institutional_factor_platform.data.domain import (
    AssetType,
    DatasetStatus,
    DataSource,
    IssuerId,
    IssuerListingMapping,
    ListingType,
    MappingEvidence,
    MappingStatus,
    SecurityId,
    SecurityMapping,
    SecurityRecord,
    SymbolHistoryRecord,
    ValidationResult,
    ValidationSeverity,
)
from institutional_factor_platform.data.evidence import atomic_write_json
from institutional_factor_platform.exceptions import SecurityMappingError


def validate_security_master(
    records: tuple[SecurityRecord, ...], settings: UniverseSettings
) -> tuple[ValidationResult, ...]:
    results: list[ValidationResult] = []
    ids = Counter(record.security_id.value for record in records)
    sources = Counter((record.source.value, record.source_identifier) for record in records)
    primary = Counter(
        (record.normalized_ticker, record.exchange) for record in records if record.primary_listing
    )
    for label, counter in (
        ("security_id", ids),
        ("source_identifier", sources),
        ("primary_listing", primary),
    ):
        duplicates = sum(count > 1 for count in counter.values())
        if duplicates:
            results.append(
                ValidationResult(
                    f"unique_{label}", ValidationSeverity.CRITICAL, f"{duplicates} duplicates"
                )
            )
    for index, record in enumerate(records):
        if not record.normalized_ticker:
            results.append(
                ValidationResult("ticker", ValidationSeverity.CRITICAL, "Missing ticker", row=index)
            )
        if record.asset_type is not AssetType.COMMON_STOCK:
            results.append(
                ValidationResult(
                    "asset_type", ValidationSeverity.CRITICAL, "Unsupported asset type", row=index
                )
            )
        if record.listing_type is not ListingType.PRIMARY or not record.primary_listing:
            results.append(
                ValidationResult(
                    "listing_type", ValidationSeverity.CRITICAL, "Non-primary listing", row=index
                )
            )
        if record.currency != settings.currency or record.country != settings.country:
            results.append(
                ValidationResult(
                    "market", ValidationSeverity.CRITICAL, "Unsupported country/currency", row=index
                )
            )
        if (
            record.listing_start_date
            and record.listing_end_date
            and record.listing_end_date < record.listing_start_date
        ):
            results.append(
                ValidationResult(
                    "listing_dates", ValidationSeverity.CRITICAL, "Invalid listing dates", row=index
                )
            )
        if record.active and record.listing_end_date is not None:
            results.append(
                ValidationResult(
                    "active_status",
                    ValidationSeverity.ERROR,
                    "Active listing has end date",
                    row=index,
                )
            )
        if record.metadata_quality_status in {DatasetStatus.FAIL, DatasetStatus.QUARANTINED}:
            results.append(
                ValidationResult(
                    "metadata_quality",
                    ValidationSeverity.ERROR,
                    "Record quality is not usable",
                    row=index,
                )
            )
    return tuple(results)


class SecurityMappingStore:
    """Small owner-governed mapping registry; it is not a commercial security master."""

    def __init__(self, path: Path) -> None:
        self.path = path

    def persist(self, mappings: tuple[SecurityMapping, ...]) -> None:
        _validate_mappings(mappings)
        atomic_write_json(self.path, [_mapping_dict(item) for item in mappings])

    def load(self) -> tuple[SecurityMapping, ...]:
        try:
            values = json.loads(self.path.read_text(encoding="utf-8"))
            return tuple(_mapping_from_dict(value) for value in values)
        except (OSError, ValueError, TypeError, KeyError) as exc:
            raise SecurityMappingError(
                f"Invalid security mapping store {self.path}: {exc}"
            ) from exc

    def resolve(self, source: str, identifier: str, as_of: date) -> SecurityId:
        active = [
            mapping
            for mapping in self.load()
            if mapping.source.value == source
            and mapping.source_identifier.strip().upper() == identifier.strip().upper()
            and mapping.valid_from <= as_of
            and (mapping.valid_to is None or as_of <= mapping.valid_to)
            and mapping.status is MappingStatus.RESOLVED
        ]
        ids = {mapping.security_id for mapping in active}
        if len(ids) != 1 or None in ids:
            raise SecurityMappingError(
                f"Security mapping is unresolved or ambiguous for {source}:{identifier} at {as_of}."
            )
        resolved = next(iter(ids))
        if resolved is None:  # Defensive narrowing; None was rejected above.
            raise SecurityMappingError("Resolved mapping unexpectedly lacks an ID.")
        return resolved


class SymbolHistoryStore:
    """Immutable effective-dated symbols for stable listing identities."""

    def __init__(self, path: Path) -> None:
        self.path = path

    def persist(self, records: tuple[SymbolHistoryRecord, ...]) -> None:
        _validate_symbol_history(records)
        atomic_write_json(self.path, [_symbol_dict(item) for item in records])

    def load(self) -> tuple[SymbolHistoryRecord, ...]:
        try:
            values = json.loads(self.path.read_text(encoding="utf-8"))
            return tuple(_symbol_from_dict(value) for value in values)
        except (OSError, ValueError, TypeError, KeyError) as exc:
            raise SecurityMappingError(f"Invalid symbol history {self.path}: {exc}") from exc

    def resolve(self, ticker: str, exchange: str, as_of: date) -> SecurityId:
        normalized = ticker.strip().upper()
        matches = {
            item.security_id
            for item in self.load()
            if item.ticker.strip().upper() == normalized
            and item.exchange.strip().upper() == exchange.strip().upper()
            and item.valid_from <= as_of
            and (item.valid_to is None or as_of <= item.valid_to)
        }
        if len(matches) != 1:
            raise SecurityMappingError("Symbol is unresolved or ambiguous for the requested date.")
        return next(iter(matches))


class IssuerListingMappingStore:
    """Persist explicit issuer-to-listing relationships; ambiguity never joins."""

    def __init__(self, path: Path) -> None:
        self.path = path

    def persist(self, mappings: tuple[IssuerListingMapping, ...]) -> None:
        _validate_issuer_listing_mappings(mappings)
        atomic_write_json(self.path, [_issuer_listing_dict(item) for item in mappings])

    def load(self) -> tuple[IssuerListingMapping, ...]:
        try:
            values = json.loads(self.path.read_text(encoding="utf-8"))
            return tuple(_issuer_listing_from_dict(item) for item in values)
        except (OSError, ValueError, TypeError, KeyError) as exc:
            raise SecurityMappingError(f"Invalid issuer-listing mapping store: {exc}") from exc

    def resolve(self, issuer_id: IssuerId, as_of: date) -> SecurityId:
        matches = self.resolve_all(issuer_id, as_of)
        if len(matches) != 1:
            raise SecurityMappingError(
                "Issuer has multiple resolved listings; a singular listing join is ambiguous."
            )
        return matches[0]

    def resolve_all(self, issuer_id: IssuerId, as_of: date) -> tuple[SecurityId, ...]:
        """Resolve every authenticated listing for an issuer without collapsing share classes."""
        active = [
            item
            for item in self.load()
            if item.issuer_id == issuer_id
            and item.valid_from <= as_of
            and (item.valid_to is None or as_of <= item.valid_to)
        ]
        if any(item.status is not MappingStatus.RESOLVED for item in active):
            raise SecurityMappingError(
                "Issuer-to-listing evidence is unresolved or ambiguous; conflict is preserved."
            )
        matches = {item.security_id for item in active}
        if not matches or None in matches:
            raise SecurityMappingError("Issuer-to-listing relationship is unresolved or ambiguous.")
        return tuple(
            sorted((item for item in matches if item is not None), key=lambda item: item.value)
        )


def mapping_from_listing(
    *,
    source: DataSource,
    source_identifier: str,
    ticker: str,
    exchange: str,
    mic: str | None,
    valid_from: date,
    valid_to: date | None,
    provenance: str,
    retrieval_timestamp: object,
    cik: str | None = None,
    evidence: MappingEvidence = MappingEvidence.LISTING_METADATA,
    security_id: SecurityId,
) -> SecurityMapping:
    from datetime import datetime

    if not isinstance(retrieval_timestamp, datetime):
        raise SecurityMappingError("Mapping retrieval timestamp must be a datetime.")
    return SecurityMapping(
        source=source,
        source_identifier=source_identifier,
        ticker=ticker.strip().upper(),
        exchange=exchange.strip().upper(),
        mic=mic.strip().upper() if mic else None,
        cik=cik.zfill(10) if cik else None,
        valid_from=valid_from,
        valid_to=valid_to,
        status=MappingStatus.RESOLVED,
        evidence=evidence,
        provenance=provenance,
        retrieval_timestamp=retrieval_timestamp,
        security_id=security_id,
    )


def _validate_mappings(mappings: tuple[SecurityMapping, ...]) -> None:
    for index, left in enumerate(mappings):
        for right in mappings[index + 1 :]:
            same_source_key = (
                left.source is right.source
                and left.source_identifier.strip().upper()
                == right.source_identifier.strip().upper()
            )
            overlaps = left.valid_to is None or right.valid_from <= left.valid_to
            reverse_overlaps = right.valid_to is None or left.valid_from <= right.valid_to
            if (
                same_source_key
                and overlaps
                and reverse_overlaps
                and left.security_id != right.security_id
            ):
                raise SecurityMappingError("Conflicting active source mappings.")


def _mapping_dict(mapping: SecurityMapping) -> dict[str, object]:
    return {
        "source": mapping.source.value,
        "source_identifier": mapping.source_identifier,
        "ticker": mapping.ticker,
        "exchange": mapping.exchange,
        "mic": mapping.mic,
        "cik": mapping.cik,
        "valid_from": mapping.valid_from.isoformat(),
        "valid_to": mapping.valid_to.isoformat() if mapping.valid_to else None,
        "status": mapping.status.value,
        "evidence": mapping.evidence.value,
        "provenance": mapping.provenance,
        "retrieval_timestamp": mapping.retrieval_timestamp.isoformat(),
        "security_id": mapping.security_id.value if mapping.security_id else None,
    }


def _mapping_from_dict(value: dict[str, object]) -> SecurityMapping:
    from datetime import datetime

    return SecurityMapping(
        source=DataSource(str(value["source"])),
        source_identifier=str(value["source_identifier"]),
        ticker=str(value["ticker"]) if value.get("ticker") is not None else None,
        exchange=str(value["exchange"]) if value.get("exchange") is not None else None,
        mic=str(value["mic"]) if value.get("mic") is not None else None,
        cik=str(value["cik"]) if value.get("cik") is not None else None,
        valid_from=date.fromisoformat(str(value["valid_from"])),
        valid_to=date.fromisoformat(str(value["valid_to"])) if value.get("valid_to") else None,
        status=MappingStatus(str(value["status"])),
        evidence=MappingEvidence(str(value["evidence"])),
        provenance=str(value["provenance"]),
        retrieval_timestamp=datetime.fromisoformat(str(value["retrieval_timestamp"])),
        security_id=SecurityId(str(value["security_id"])) if value.get("security_id") else None,
    )


def _validate_symbol_history(records: tuple[SymbolHistoryRecord, ...]) -> None:
    for index, left in enumerate(records):
        for right in records[index + 1 :]:
            same_listing_venue = (
                left.security_id == right.security_id
                and left.exchange.strip().upper() == right.exchange.strip().upper()
            )
            same_symbol_venue = (
                left.ticker.strip().upper() == right.ticker.strip().upper()
                and left.exchange.strip().upper() == right.exchange.strip().upper()
            )
            overlaps = (left.valid_to is None or right.valid_from <= left.valid_to) and (
                right.valid_to is None or left.valid_from <= right.valid_to
            )
            if overlaps and same_listing_venue:
                raise SecurityMappingError("Overlapping symbol periods for one listing.")
            if overlaps and same_symbol_venue and left.security_id != right.security_id:
                raise SecurityMappingError("Active ticker conflicts across listings.")


def _validate_issuer_listing_mappings(mappings: tuple[IssuerListingMapping, ...]) -> None:
    for index, left in enumerate(mappings):
        for right in mappings[index + 1 :]:
            if left.issuer_id != right.issuer_id:
                continue
            overlaps = (left.valid_to is None or right.valid_from <= left.valid_to) and (
                right.valid_to is None or left.valid_from <= right.valid_to
            )
            if overlaps and left.security_id == right.security_id and left.status == right.status:
                raise SecurityMappingError("Duplicate overlapping issuer-to-listing mapping.")


def _symbol_dict(value: SymbolHistoryRecord) -> dict[str, object]:
    return {
        "security_id": value.security_id.value,
        "ticker": value.ticker.strip().upper(),
        "exchange": value.exchange.strip().upper(),
        "mic": value.mic.strip().upper() if value.mic else None,
        "valid_from": value.valid_from.isoformat(),
        "valid_to": value.valid_to.isoformat() if value.valid_to else None,
        "source": value.source.value,
        "source_identifier": value.source_identifier,
        "retrieval_timestamp": value.retrieval_timestamp.isoformat(),
        "evidence_reference": value.evidence_reference,
    }


def _symbol_from_dict(value: dict[str, object]) -> SymbolHistoryRecord:
    from datetime import datetime

    return SymbolHistoryRecord(
        security_id=SecurityId(str(value["security_id"])),
        ticker=str(value["ticker"]),
        exchange=str(value["exchange"]),
        mic=str(value["mic"]) if value.get("mic") else None,
        valid_from=date.fromisoformat(str(value["valid_from"])),
        valid_to=date.fromisoformat(str(value["valid_to"])) if value.get("valid_to") else None,
        source=DataSource(str(value["source"])),
        source_identifier=str(value["source_identifier"]),
        retrieval_timestamp=datetime.fromisoformat(str(value["retrieval_timestamp"])),
        evidence_reference=str(value["evidence_reference"]),
    )


def _issuer_listing_dict(value: IssuerListingMapping) -> dict[str, object]:
    return {
        "issuer_id": value.issuer_id.value,
        "security_id": value.security_id.value if value.security_id else None,
        "valid_from": value.valid_from.isoformat(),
        "valid_to": value.valid_to.isoformat() if value.valid_to else None,
        "status": value.status.value,
        "evidence": value.evidence.value,
        "provenance": value.provenance,
        "retrieval_timestamp": value.retrieval_timestamp.isoformat(),
    }


def _issuer_listing_from_dict(value: dict[str, object]) -> IssuerListingMapping:
    from datetime import datetime

    return IssuerListingMapping(
        issuer_id=IssuerId(str(value["issuer_id"])),
        security_id=SecurityId(str(value["security_id"])) if value.get("security_id") else None,
        valid_from=date.fromisoformat(str(value["valid_from"])),
        valid_to=date.fromisoformat(str(value["valid_to"])) if value.get("valid_to") else None,
        status=MappingStatus(str(value["status"])),
        evidence=MappingEvidence(str(value["evidence"])),
        provenance=str(value["provenance"]),
        retrieval_timestamp=datetime.fromisoformat(str(value["retrieval_timestamp"])),
    )
