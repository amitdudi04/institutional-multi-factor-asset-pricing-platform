"""Source-independent immutable Phase 1 domain types."""

import re
import uuid
from dataclasses import dataclass, field
from datetime import UTC, date, datetime
from enum import StrEnum
from pathlib import Path
from typing import Any

from institutional_factor_platform.exceptions import SecurityMappingError, TemporalIntegrityError


class DataSource(StrEnum):
    OWNER_SUPPLIED = "owner_supplied"
    YAHOO_FINANCE = "yahoo_finance"
    FRED = "fred"
    KENNETH_FRENCH = "kenneth_french"
    SEC_EDGAR = "sec_edgar"
    ALPHA_VANTAGE = "alpha_vantage"


class DataFrequency(StrEnum):
    DAILY = "daily"
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    ANNUAL = "annual"
    EVENT = "event"


class AssetType(StrEnum):
    COMMON_STOCK = "common_stock"


class ListingType(StrEnum):
    PRIMARY = "primary"
    ETF = "etf"
    ETN = "etn"
    CLOSED_END_FUND = "closed_end_fund"
    ADR = "adr"
    PREFERRED = "preferred"
    REIT = "reit"
    WARRANT = "warrant"
    RIGHT = "right"
    UNIT = "unit"
    SPAC_UNIT = "spac_unit"
    MUTUAL_FUND = "mutual_fund"
    MONEY_MARKET = "money_market"
    DEBT = "debt"
    OPTION = "option"
    FUTURE = "future"
    CRYPTO = "crypto"


class DatasetStatus(StrEnum):
    PASS = "PASS"
    PASS_WITH_WARNINGS = "PASS_WITH_WARNINGS"
    QUARANTINED = "QUARANTINED"
    FAIL = "FAIL"


class ValidationSeverity(StrEnum):
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class RetrievalStatus(StrEnum):
    SUCCESS = "SUCCESS"
    PARTIAL = "PARTIAL"
    FAILED = "FAILED"


class AvailabilityQuality(StrEnum):
    SOURCE_TIMESTAMP = "SOURCE_TIMESTAMP"
    SOURCE_DATE = "SOURCE_DATE"
    INFERRED_DATE_LEVEL = "INFERRED_DATE_LEVEL"
    UNKNOWN = "UNKNOWN"


class MappingStatus(StrEnum):
    RESOLVED = "RESOLVED"
    UNRESOLVED = "UNRESOLVED"
    AMBIGUOUS = "AMBIGUOUS"
    CONFLICT = "CONFLICT"
    EXPIRED = "EXPIRED"


class MappingEvidence(StrEnum):
    OWNER_CONFIRMED = "OWNER_CONFIRMED"
    LISTING_METADATA = "LISTING_METADATA"
    REGISTRANT_ONLY = "REGISTRANT_ONLY"


@dataclass(frozen=True, slots=True)
class SecurityId:
    value: str

    def __post_init__(self) -> None:
        if not re.fullmatch(r"sec_[a-f0-9]{32}", self.value):
            raise SecurityMappingError("Security ID must be a canonical 128-bit internal ID.")

    @classmethod
    def canonical(
        cls, stable_listing_key: str, exchange: str, mic: str | None = None
    ) -> "SecurityId":
        """Reject caller-derived identity; canonical IDs must be assigned and persisted."""
        del stable_listing_key, exchange, mic
        raise SecurityMappingError(
            "Direct canonical construction is prohibited; assign an ID and persist "
            "mapping authority."
        )

    @classmethod
    def assign(cls) -> "SecurityId":
        """Assign a permanent internal listing identifier for persisted reference data."""
        return cls(f"sec_{uuid.uuid4().hex}")


@dataclass(frozen=True, slots=True)
class IssuerId:
    value: str

    @classmethod
    def from_cik(cls, cik: str) -> "IssuerId":
        normalized = cik.zfill(10)
        if len(normalized) != 10 or not normalized.isdigit():
            raise SecurityMappingError("Issuer CIK must contain at most ten digits.")
        return cls(f"issuer_{uuid.uuid5(uuid.NAMESPACE_URL, 'sec-cik|' + normalized).hex}")


@dataclass(frozen=True, slots=True)
class SymbolHistoryRecord:
    security_id: SecurityId
    ticker: str
    exchange: str
    mic: str | None
    valid_from: date
    valid_to: date | None
    source: DataSource
    source_identifier: str
    retrieval_timestamp: datetime
    evidence_reference: str

    def __post_init__(self) -> None:
        if (
            not self.ticker.strip()
            or not self.exchange.strip()
            or not self.evidence_reference.strip()
        ):
            raise SecurityMappingError("Symbol history requires ticker, venue, and evidence.")
        if self.valid_to is not None and self.valid_to < self.valid_from:
            raise SecurityMappingError("Symbol history validity end precedes start.")
        if self.retrieval_timestamp.tzinfo is None:
            raise SecurityMappingError("Symbol history retrieval timestamp must be timezone-aware.")


@dataclass(frozen=True, slots=True)
class IssuerListingMapping:
    issuer_id: IssuerId
    security_id: SecurityId | None
    valid_from: date
    valid_to: date | None
    status: MappingStatus
    evidence: MappingEvidence
    provenance: str
    retrieval_timestamp: datetime

    def __post_init__(self) -> None:
        if self.valid_to is not None and self.valid_to < self.valid_from:
            raise SecurityMappingError("Issuer-listing validity end precedes start.")
        if self.status is MappingStatus.RESOLVED and self.security_id is None:
            raise SecurityMappingError("Resolved issuer-listing mapping requires a listing ID.")
        if self.status is not MappingStatus.RESOLVED and self.security_id is not None:
            raise SecurityMappingError(
                "Ambiguous issuer-listing mapping cannot carry a listing ID."
            )
        if not self.provenance.strip() or self.retrieval_timestamp.tzinfo is None:
            raise SecurityMappingError("Issuer-listing mapping requires provenance and aware time.")


@dataclass(frozen=True, slots=True)
class DateRange:
    start: date
    end: date

    def __post_init__(self) -> None:
        if self.end < self.start:
            raise TemporalIntegrityError("Date range end must not precede start.")


@dataclass(frozen=True, slots=True)
class TemporalMetadata:
    observation_date: date | None
    retrieval_timestamp: datetime
    availability_timestamp: datetime | None = None
    period_start: date | None = None
    period_end: date | None = None
    filing_date: date | None = None
    publication_date: date | None = None
    effective_date: date | None = None
    inferred_availability: bool = False

    def __post_init__(self) -> None:
        if self.retrieval_timestamp.tzinfo is None:
            raise TemporalIntegrityError("Retrieval timestamp must be timezone-aware.")
        if self.filing_date and self.period_end and self.filing_date < self.period_end:
            raise TemporalIntegrityError("Filing date must not precede period end.")
        if self.availability_timestamp and self.filing_date:
            filing = datetime.combine(self.filing_date, datetime.min.time(), tzinfo=UTC)
            if self.availability_timestamp < filing:
                raise TemporalIntegrityError("Availability timestamp must not precede filing date.")


@dataclass(frozen=True, slots=True)
class SecurityRecord:
    security_id: SecurityId
    ticker: str
    issuer_name: str
    exchange: str
    asset_type: AssetType
    listing_type: ListingType
    currency: str
    country: str
    primary_listing: bool
    active: bool
    source: DataSource
    source_identifier: str
    retrieval_timestamp: datetime
    availability_timestamp: datetime
    schema_version: str
    mic: str | None = None
    sector: str | None = None
    industry: str | None = None
    listing_start_date: date | None = None
    listing_end_date: date | None = None
    metadata_quality_status: DatasetStatus = DatasetStatus.PASS

    @property
    def normalized_ticker(self) -> str:
        return re.sub(r"[^A-Z0-9.-]", "", self.ticker.strip().upper())


@dataclass(frozen=True, slots=True)
class ValidationResult:
    rule: str
    severity: ValidationSeverity
    message: str
    field: str | None = None
    row: int | None = None
    rule_version: str = "1.0.0"
    dataset_id: str | None = None
    affected_count: int = 1
    representative_keys: tuple[str, ...] = ()
    remediation: str | None = None
    source: str | None = None
    timestamp: datetime | None = None


@dataclass(frozen=True, slots=True)
class SecurityMapping:
    source: DataSource
    source_identifier: str
    ticker: str | None
    exchange: str | None
    mic: str | None
    cik: str | None
    valid_from: date
    valid_to: date | None
    status: MappingStatus
    evidence: MappingEvidence
    provenance: str
    retrieval_timestamp: datetime
    security_id: SecurityId | None = None

    def __post_init__(self) -> None:
        if not self.source_identifier.strip() or not self.provenance.strip():
            raise SecurityMappingError("Mapping requires source identifier and provenance.")
        if self.valid_to is not None and self.valid_to < self.valid_from:
            raise SecurityMappingError("Mapping validity end precedes its start.")
        if self.retrieval_timestamp.tzinfo is None:
            raise SecurityMappingError("Mapping retrieval timestamp must be timezone-aware.")
        if self.status is MappingStatus.RESOLVED and self.security_id is None:
            raise SecurityMappingError("Resolved mapping requires a canonical security ID.")
        if self.status is not MappingStatus.RESOLVED and self.security_id is not None:
            raise SecurityMappingError("Unresolved mapping cannot carry a canonical security ID.")


@dataclass(frozen=True, slots=True)
class DataArtifact:
    path: Path
    checksum: str
    byte_size: int
    media_type: str
    source: DataSource
    retrieval_timestamp: datetime


@dataclass(frozen=True, slots=True)
class RetrievalRequest:
    source: DataSource
    dataset: str
    date_range: DateRange | None = None
    identifiers: tuple[str, ...] = ()
    parameters: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class RetrievalResult:
    request: RetrievalRequest
    status: RetrievalStatus
    artifact: DataArtifact | None
    records: tuple[dict[str, Any], ...] = ()
    failures: tuple[str, ...] = ()
