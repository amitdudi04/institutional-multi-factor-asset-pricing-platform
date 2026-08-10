"""Application service used by API, dashboard, CLI, and reporting."""

from pathlib import Path
from typing import Any

import pyarrow as pa

from institutional_factor_platform.project import find_project_root

from .catalog import DeliveryCatalog
from .config import DeliveryConfig, load_delivery_config
from .reporting import ReportService
from .schemas import Page, PublicationKind, ReportRecord, ReportRequest


class DeliveryService:
    def __init__(self, config: DeliveryConfig | None = None, root: Path | None = None) -> None:
        self.root = (root or find_project_root()).resolve()
        self.config = config or load_delivery_config()
        self.catalog = DeliveryCatalog(self.root)
        self.reports = ReportService(self.root, self.config, self.catalog)

    def publications(self, kind: PublicationKind | None, offset: int, limit: int) -> Page:
        values = self.catalog.list(kind)
        return Page(
            items=tuple(item.model_dump(mode="json") for item in values[offset : offset + limit]),
            offset=offset,
            limit=limit,
            total=len(values),
        )

    def publication(self, kind: PublicationKind, publication_id: str) -> dict[str, Any]:
        return self.catalog.manifest(kind, publication_id)

    def find_publication(self, publication_id: str) -> dict[str, Any]:
        kind, manifest = self.catalog.find(publication_id)
        return {"kind": kind, "manifest": manifest}

    def table_page(
        self,
        kind: PublicationKind,
        publication_id: str,
        artifact: str,
        offset: int,
        limit: int,
    ) -> Page:
        table = self.catalog.table(kind, publication_id, artifact)
        return self._page(table, offset, limit)

    def create_report(self, request: ReportRequest) -> ReportRecord:
        return self.reports.generate(request)

    @staticmethod
    def _page(table: pa.Table, offset: int, limit: int) -> Page:
        rows = table.slice(offset, limit).to_pylist()
        return Page(items=tuple(rows), offset=offset, limit=limit, total=table.num_rows)
