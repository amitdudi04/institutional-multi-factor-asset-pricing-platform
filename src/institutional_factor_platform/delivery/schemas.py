"""Stable delivery contracts shared by API, reports, and dashboard."""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

PublicationKind = Literal["data", "factors", "asset_pricing", "portfolio", "ml"]


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class PublicationReference(StrictModel):
    kind: PublicationKind
    publication_id: str = Field(pattern=r"^[A-Za-z0-9][A-Za-z0-9._-]{2,127}$")


class PublicationSummary(StrictModel):
    kind: PublicationKind
    publication_id: str
    schema_version: str
    validation_status: str
    configuration_hash: str | None
    git_commit: str | None
    created_at: datetime | None


class Page(StrictModel):
    items: tuple[dict[str, object], ...]
    offset: int
    limit: int
    total: int


class ReportRequest(StrictModel):
    publications: tuple[PublicationReference, ...] = Field(min_length=1, max_length=20)
    sections: tuple[
        Literal["overview", "provenance", "results", "validation", "limitations"], ...
    ] = (
        "overview",
        "provenance",
        "validation",
        "limitations",
    )
    format: Literal["markdown", "html", "json", "csv"] = "markdown"


class ReportRecord(StrictModel):
    report_id: str
    generated_at: datetime
    format: str
    output_checksum: str
    manifest_checksum: str
    publications: tuple[PublicationReference, ...]
