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
    ListingType,
    SecurityId,
    SecurityRecord,
    TemporalMetadata,
)
from institutional_factor_platform.data.security_master import validate_security_master
from institutional_factor_platform.exceptions import ConfigurationError, TemporalIntegrityError


def test_phase1_configuration_is_strict_hashable_and_redacted(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("IFP_SEC_CONTACT_EMAIL", "owner@example.invalid")
    monkeypatch.setenv("IFP_FRED_API_KEY", "test-secret-not-a-live-key")
    config = load_phase1_config()
    assert len(config.configuration_hash()) == 64
    assert config.configuration_hash() == config.configuration_hash()
    redacted = config.redacted_dict()
    assert redacted["sources"]["sec"]["contact_email"] == "[REDACTED]"  # type: ignore[index]
    assert redacted["sources"]["fred"]["api_key"] == "**********"  # type: ignore[index]
    snapshot = tmp_path / "snapshot.json"
    first = config.write_snapshot(snapshot)
    assert config.write_snapshot(snapshot) == first
    assert "owner@example.invalid" not in snapshot.read_text(encoding="utf-8")


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
    first = SecurityId.create(DataSource.OWNER_SUPPLIED, "TEST", "XNYS", "owner-1")
    assert first == SecurityId.create(DataSource.OWNER_SUPPLIED, "test", "xnys", "owner-1")
    assert first != SecurityId.create(DataSource.OWNER_SUPPLIED, "TEST", "XNAS", "owner-1")
    with pytest.raises(Exception, match="requires"):
        SecurityId.create(DataSource.OWNER_SUPPLIED, "", "XNYS", "owner-1")


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
        SecurityId.create(DataSource.OWNER_SUPPLIED, "SYNTH", "XNYS", source_id),
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
