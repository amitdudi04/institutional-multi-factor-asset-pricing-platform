"""Versioned security-master eligibility and identity validation."""

from collections import Counter

from institutional_factor_platform.data.config import UniverseSettings
from institutional_factor_platform.data.domain import (
    AssetType,
    DatasetStatus,
    ListingType,
    SecurityRecord,
    ValidationResult,
    ValidationSeverity,
)


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
