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
    ListingType,
    MappingEvidence,
    MappingStatus,
    SecurityId,
    SecurityMapping,
    SecurityRecord,
    ValidationResult,
    ValidationSeverity,
)
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
        content = json.dumps([_mapping_dict(item) for item in mappings], sort_keys=True, indent=2)
        if self.path.exists() and self.path.read_text(encoding="utf-8") != content:
            raise SecurityMappingError(f"Refusing to overwrite mapping evidence: {self.path}")
        self.path.parent.mkdir(parents=True, exist_ok=True)
        if not self.path.exists():
            self.path.write_text(content, encoding="utf-8")

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
        security_id=SecurityId.canonical(ticker, exchange, mic),
    )


def registrant_mapping(
    *,
    cik: str,
    eligible_security_ids: tuple[SecurityId, ...],
    valid_from: date,
    provenance: str,
    retrieval_timestamp: object,
) -> SecurityMapping:
    from datetime import datetime

    if not isinstance(retrieval_timestamp, datetime):
        raise SecurityMappingError("Mapping retrieval timestamp must be a datetime.")
    unique = tuple(dict.fromkeys(eligible_security_ids))
    status = MappingStatus.RESOLVED if len(unique) == 1 else MappingStatus.AMBIGUOUS
    return SecurityMapping(
        source=DataSource.SEC_EDGAR,
        source_identifier=cik.zfill(10),
        ticker=None,
        exchange=None,
        mic=None,
        cik=cik.zfill(10),
        valid_from=valid_from,
        valid_to=None,
        status=status,
        evidence=MappingEvidence.REGISTRANT_ONLY,
        provenance=provenance,
        retrieval_timestamp=retrieval_timestamp,
        security_id=unique[0] if status is MappingStatus.RESOLVED else None,
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
