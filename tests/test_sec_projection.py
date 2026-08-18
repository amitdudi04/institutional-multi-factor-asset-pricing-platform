from datetime import UTC, date, datetime
from pathlib import Path

import pytest

from institutional_factor_platform.data.domain import (
    IssuerId,
    IssuerListingMapping,
    MappingEvidence,
    MappingStatus,
    SecurityId,
)
from institutional_factor_platform.data.sec_projection import project_annual_sec_fundamentals
from institutional_factor_platform.data.security_master import IssuerListingMappingStore
from institutional_factor_platform.exceptions import DataQualityError


def _mapping(tmp_path: Path) -> tuple[IssuerListingMappingStore, IssuerId, tuple[SecurityId, ...]]:
    issuer = IssuerId.from_cik("1")
    securities = (SecurityId.assign(), SecurityId.assign())
    store = IssuerListingMappingStore(tmp_path / "issuer-listings.json")
    store.persist(
        tuple(
            IssuerListingMapping(
                issuer,
                security,
                date(2020, 1, 1),
                None,
                MappingStatus.RESOLVED,
                MappingEvidence.OWNER_CONFIRMED,
                "synthetic filing-cover and listing evidence",
                datetime(2024, 1, 1, tzinfo=UTC),
            )
            for security in securities
        )
    )
    return store, issuer, securities


def _fact(
    issuer: IssuerId,
    *,
    concept: str,
    value: float,
    year: int,
    instant: bool,
) -> dict[str, object]:
    return {
        "issuer_id": issuer.value,
        "taxonomy": "us-gaap",
        "concept": concept,
        "unit": "USD",
        "value": value,
        "fiscal_period": "FY",
        "period_start": None if instant else date(year, 1, 1),
        "period_end": date(year, 12, 31),
        "filing_date": date(year + 1, 2, 1),
        "form": "10-K",
        "accession_number": f"accession-{year}",
        "availability_timestamp": datetime(year + 1, 2, 1, 23, 59, tzinfo=UTC),
    }


def test_annual_projection_preserves_share_classes_and_derives_without_lookahead(
    tmp_path: Path,
) -> None:
    store, issuer, securities = _mapping(tmp_path)
    records: list[dict[str, object]] = []
    for year, scale in ((2022, 1.0), (2023, 2.0)):
        records.extend(
            [
                _fact(issuer, concept="Assets", value=100.0 * scale, year=year, instant=True),
                _fact(
                    issuer,
                    concept="StockholdersEquity",
                    value=40.0 * scale,
                    year=year,
                    instant=True,
                ),
                _fact(issuer, concept="AssetsCurrent", value=50.0 * scale, year=year, instant=True),
                _fact(
                    issuer,
                    concept="LiabilitiesCurrent",
                    value=20.0 * scale,
                    year=year,
                    instant=True,
                ),
                _fact(
                    issuer, concept="NetIncomeLoss", value=10.0 * scale, year=year, instant=False
                ),
                _fact(
                    issuer,
                    concept="NetCashProvidedByUsedInOperatingActivities",
                    value=8.0 * scale,
                    year=year,
                    instant=False,
                ),
                _fact(
                    issuer,
                    concept="PaymentsToAcquirePropertyPlantAndEquipment",
                    value=5.0 * scale,
                    year=year,
                    instant=False,
                ),
            ]
        )
    projected = project_annual_sec_fundamentals(tuple(records), store)
    assert {row["security_id"] for row in projected} == {item.value for item in securities}
    latest = [row for row in projected if row["period_end"] == date(2023, 12, 31)]
    by_security = {
        security.value: {
            row["field"]: row["value"] for row in latest if row["security_id"] == security.value
        }
        for security in securities
    }
    for values in by_security.values():
        assert values["working_capital"] == 60.0
        assert values["total_accruals"] == 4.0
        assert values["prior_total_assets"] == 100.0
        assert values["average_assets"] == 150.0
        assert values["prior_capex"] == 5.0
        assert "net_equity_issuance" not in values


def test_annual_projection_rejects_conflicting_standard_facts(tmp_path: Path) -> None:
    store, issuer, _ = _mapping(tmp_path)
    first = _fact(issuer, concept="Assets", value=100.0, year=2023, instant=True)
    second = {**first, "value": 101.0}
    with pytest.raises(DataQualityError, match="Conflicting SEC values"):
        project_annual_sec_fundamentals((first, second), store)
