from dataclasses import replace
from datetime import UTC, date, datetime
from pathlib import Path

import pytest
from pydantic import ValidationError

from institutional_factor_platform.data.config import (
    PathSettings,
    Phase1Config,
    load_phase1_config,
    write_config_example,
)
from institutional_factor_platform.data.domain import (
    AssetType,
    DatasetStatus,
    DataSource,
    DateRange,
    IssuerId,
    IssuerListingMapping,
    ListingType,
    MappingEvidence,
    MappingStatus,
    SecurityId,
    SecurityRecord,
    SymbolHistoryRecord,
    TemporalMetadata,
)
from institutional_factor_platform.data.security_master import (
    IssuerListingMappingStore,
    SecurityMappingStore,
    SymbolHistoryStore,
    mapping_from_listing,
    validate_security_master,
)
from institutional_factor_platform.exceptions import (
    ConfigurationError,
    SecurityMappingError,
    TemporalIntegrityError,
)


def test_phase1_configuration_is_strict_hashable_and_redacted(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("IFP_SEC_CONTACT_EMAIL", "owner@example.invalid")
    monkeypatch.setenv("IFP_FRED_API_KEY", "test-secret-not-a-live-key")
    monkeypatch.setenv("IFP_ALPHA_VANTAGE_API_KEY", "test-alpha-secret")
    config = load_phase1_config()
    assert len(config.configuration_hash()) == 64
    assert config.configuration_hash() == config.configuration_hash()
    redacted = config.redacted_dict()
    assert redacted["sources"]["sec"]["contact_email"] == "[REDACTED]"  # type: ignore[index]
    assert redacted["sources"]["fred"]["api_key"] == "**********"  # type: ignore[index]
    assert redacted["sources"]["alpha_vantage"]["api_key"] == "**********"  # type: ignore[index]
    snapshot = tmp_path / "snapshot.json"
    first = config.write_snapshot(snapshot)
    assert config.write_snapshot(snapshot) == first
    assert "owner@example.invalid" not in snapshot.read_text(encoding="utf-8")
    assert "test-alpha-secret" not in snapshot.read_text(encoding="utf-8")


def test_configuration_date_unknown_field_and_paths_fail(tmp_path: Path) -> None:
    config = load_phase1_config()
    data = config.model_dump()
    data["project"]["end_date"] = date(2009, 1, 1)
    with pytest.raises(ValidationError, match="end_date"):
        Phase1Config.model_validate(data)
    data = config.model_dump()
    data["unexpected"] = True
    with pytest.raises(ValidationError, match="Extra inputs"):
        Phase1Config.model_validate(data)
    data = config.model_dump()
    data["manifests"]["schema_version"] = "2.0.0"
    with pytest.raises(ValidationError, match=r"manifests\.schema_version"):
        Phase1Config.model_validate(data)
    data = config.model_dump()
    data["validation"]["schema_version"] = "3.0.0"
    with pytest.raises(ValidationError, match=r"validation\.schema_version"):
        Phase1Config.model_validate(data)
    paths = PathSettings(**{**config.paths.model_dump(), "raw": Path("../escape")})
    with pytest.raises(ConfigurationError, match="escapes"):
        paths.resolved(tmp_path)


def test_sec_contact_is_required_only_for_live_retrieval() -> None:
    config = load_phase1_config()
    with pytest.raises(ConfigurationError, match="IFP_SEC_CONTACT_EMAIL"):
        config.sources.sec.require_live_user_agent()


def test_config_example_refuses_overwrite(tmp_path: Path) -> None:
    path = tmp_path / "example.yaml"
    write_config_example(path)
    assert "base_currency: USD" in path.read_text(encoding="utf-8")
    with pytest.raises(ConfigurationError, match="overwrite"):
        write_config_example(path)


def test_security_id_is_stable_and_not_ticker_only() -> None:
    assert not hasattr(SecurityId, "create")
    with pytest.raises(SecurityMappingError, match="Direct canonical construction"):
        SecurityId.canonical("AAPL", "XNYS", "XNYS")
    assigned = SecurityId.assign()
    assert assigned.value.startswith("sec_")
    with pytest.raises(SecurityMappingError, match="canonical 128-bit"):
        SecurityId("sec_caller_injected")


def test_temporal_and_date_range_invariants() -> None:
    with pytest.raises(TemporalIntegrityError):
        DateRange(date(2020, 2, 1), date(2020, 1, 1))
    with pytest.raises(TemporalIntegrityError, match="timezone-aware"):
        TemporalMetadata(date.today(), datetime.now())
    with pytest.raises(TemporalIntegrityError, match="period end"):
        TemporalMetadata(
            date(2020, 1, 1),
            datetime.now(UTC),
            period_end=date(2020, 2, 1),
            filing_date=date(2020, 1, 1),
        )


def _security(
    source_id: str = "one", *, listing: ListingType = ListingType.PRIMARY
) -> SecurityRecord:
    now = datetime(2024, 1, 2, tzinfo=UTC)
    return SecurityRecord(
        SecurityId.assign(),
        " synth ",
        "Synthetic Test Issuer",
        "XNYS",
        AssetType.COMMON_STOCK,
        listing,
        "USD",
        "US",
        listing is ListingType.PRIMARY,
        True,
        DataSource.OWNER_SUPPLIED,
        source_id,
        now,
        now,
        "1.0.0",
    )


def test_security_master_accepts_valid_and_rejects_duplicate() -> None:
    config = load_phase1_config()
    record = _security()
    assert record.normalized_ticker == "SYNTH"
    assert validate_security_master((record,), config.universe) == ()
    findings = validate_security_master((record, record), config.universe)
    assert any(item.severity.value == "CRITICAL" for item in findings)


def test_security_master_rejects_non_primary() -> None:
    findings = validate_security_master(
        (_security(listing=ListingType.ADR),), load_phase1_config().universe
    )
    assert any(item.rule == "listing_type" for item in findings)
    assert DatasetStatus.PASS.value == "PASS"


def test_security_master_detects_market_dates_status_and_quality() -> None:
    record = _security()
    broken = SecurityRecord(
        record.security_id,
        "???",
        record.issuer_name,
        record.exchange,
        record.asset_type,
        record.listing_type,
        "CAD",
        "CA",
        True,
        True,
        record.source,
        "different",
        record.retrieval_timestamp,
        record.availability_timestamp,
        record.schema_version,
        listing_start_date=date(2024, 2, 1),
        listing_end_date=date(2024, 1, 1),
        metadata_quality_status=DatasetStatus.FAIL,
    )
    rules = {
        item.rule for item in validate_security_master((broken,), load_phase1_config().universe)
    }
    assert rules >= {"ticker", "market", "listing_dates", "active_status", "metadata_quality"}


def test_cross_source_mapping_is_persisted_and_ambiguous_cik_is_blocked(
    tmp_path: Path,
) -> None:
    now = datetime(2024, 1, 2, tzinfo=UTC)
    listing_id = SecurityId.assign()
    yahoo = mapping_from_listing(
        source=DataSource.YAHOO_FINANCE,
        source_identifier=" SYNTH ",
        ticker=" synth ",
        exchange=" xnys ",
        mic="xnys",
        valid_from=date(2020, 1, 1),
        valid_to=None,
        provenance="owner-confirmed synthetic test evidence",
        retrieval_timestamp=now,
        security_id=listing_id,
    )
    owner = mapping_from_listing(
        source=DataSource.OWNER_SUPPLIED,
        source_identifier="owner-1",
        ticker="SYNTH",
        exchange="XNYS",
        mic="XNYS",
        valid_from=date(2020, 1, 1),
        valid_to=None,
        provenance="owner-confirmed synthetic test evidence",
        retrieval_timestamp=now,
        security_id=listing_id,
    )
    assert yahoo.security_id == owner.security_id
    store = SecurityMappingStore(tmp_path / "mappings.json")
    store.persist((yahoo, owner))
    restarted = SecurityMappingStore(store.path)
    assert restarted.resolve("yahoo_finance", "synth", date(2024, 1, 1)) == yahoo.security_id


def test_mapping_conflict_and_ticker_reuse_are_explicit(tmp_path: Path) -> None:
    now = datetime(2024, 1, 2, tzinfo=UTC)
    first = mapping_from_listing(
        source=DataSource.OWNER_SUPPLIED,
        source_identifier="reused",
        ticker="OLD",
        exchange="XNYS",
        mic=None,
        valid_from=date(2010, 1, 1),
        valid_to=date(2019, 12, 31),
        provenance="synthetic historical mapping",
        retrieval_timestamp=now,
        security_id=SecurityId.assign(),
    )
    second = mapping_from_listing(
        source=DataSource.OWNER_SUPPLIED,
        source_identifier="reused",
        ticker="NEW",
        exchange="XNYS",
        mic=None,
        valid_from=date(2020, 1, 1),
        valid_to=None,
        provenance="synthetic historical mapping",
        retrieval_timestamp=now,
        security_id=SecurityId.assign(),
    )
    store = SecurityMappingStore(tmp_path / "reuse.json")
    store.persist((first, second))
    assert store.resolve("owner_supplied", "reused", date(2015, 1, 1)) == first.security_id
    conflicting = replace(second, valid_from=date(2019, 1, 1), security_id=SecurityId.assign())
    with pytest.raises(SecurityMappingError, match="Conflicting"):
        SecurityMappingStore(tmp_path / "conflict.json").persist((first, conflicting))


def test_symbol_history_preserves_listing_identity_across_ticker_change(tmp_path: Path) -> None:
    now = datetime(2024, 1, 2, tzinfo=UTC)
    listing = SecurityId.assign()
    old = SymbolHistoryRecord(
        listing,
        "OLD",
        "XNYS",
        "XNYS",
        date(2010, 1, 1),
        date(2019, 12, 31),
        DataSource.OWNER_SUPPLIED,
        "listing-1",
        now,
        "owner-approved-test-evidence",
    )
    new = replace(old, ticker="NEW", valid_from=date(2020, 1, 1), valid_to=None)
    store = SymbolHistoryStore(tmp_path / "symbols.json")
    store.persist((old, new))
    restarted = SymbolHistoryStore(store.path)
    assert restarted.resolve("old", "xnys", date(2015, 1, 1)) == listing
    assert restarted.resolve("NEW", "XNYS", date(2024, 1, 1)) == listing
    reused = replace(
        new,
        security_id=SecurityId.assign(),
        ticker="OLD",
        valid_from=date(2020, 1, 1),
    )
    SymbolHistoryStore(tmp_path / "reuse-symbol.json").persist((old, new, reused))
    with pytest.raises(SecurityMappingError, match="Overlapping"):
        SymbolHistoryStore(tmp_path / "overlap.json").persist(
            (old, replace(new, valid_from=date(2019, 1, 1)))
        )
    with pytest.raises(SecurityMappingError, match="requires ticker"):
        replace(old, ticker="")
    with pytest.raises(SecurityMappingError, match="precedes"):
        replace(old, valid_from=date(2020, 1, 1), valid_to=date(2019, 1, 1))
    with pytest.raises(SecurityMappingError, match="timezone-aware"):
        replace(old, retrieval_timestamp=datetime(2024, 1, 1))


def test_issuer_identity_is_distinct_and_ambiguous_listing_join_blocks(tmp_path: Path) -> None:
    now = datetime(2024, 1, 2, tzinfo=UTC)
    issuer = IssuerId.from_cik("1")
    first, second = SecurityId.assign(), SecurityId.assign()
    resolved = IssuerListingMapping(
        issuer,
        first,
        date(2020, 1, 1),
        None,
        MappingStatus.RESOLVED,
        MappingEvidence.OWNER_CONFIRMED,
        "owner-approved synthetic mapping evidence",
        now,
    )
    store = IssuerListingMappingStore(tmp_path / "issuer-listing.json")
    store.persist((resolved,))
    assert IssuerListingMappingStore(store.path).resolve(issuer, date(2024, 1, 1)) == first
    ambiguous = IssuerListingMapping(
        issuer,
        None,
        date(2020, 1, 1),
        None,
        MappingStatus.AMBIGUOUS,
        MappingEvidence.REGISTRANT_ONLY,
        f"multiple eligible listings: {first.value},{second.value}",
        now,
    )
    ambiguous_store = IssuerListingMappingStore(tmp_path / "ambiguous-issuer.json")
    ambiguous_store.persist((ambiguous,))
    with pytest.raises(SecurityMappingError, match="unresolved or ambiguous"):
        ambiguous_store.resolve(issuer, date(2024, 1, 1))
