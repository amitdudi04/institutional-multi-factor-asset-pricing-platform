"""Unified authenticated discovery over existing Phase 1-5 repositories."""

import hashlib
import json
from dataclasses import asdict
from pathlib import Path
from typing import Any, cast

import pyarrow as pa
import pyarrow.parquet as pq

from institutional_factor_platform.asset_pricing.config import load_asset_pricing_config
from institutional_factor_platform.data.config import load_phase1_config
from institutional_factor_platform.data.evidence import resolve_project_path
from institutional_factor_platform.data.services import DataIngestionService
from institutional_factor_platform.exceptions import EvidenceIntegrityError
from institutional_factor_platform.factors.config import load_factor_config
from institutional_factor_platform.factors.storage import FactorRepository
from institutional_factor_platform.ml.config import load_ml_config
from institutional_factor_platform.ml.publication import MLRepository
from institutional_factor_platform.portfolio.config import load_portfolio_config
from institutional_factor_platform.research_outputs.portfolio_storage import PortfolioRepository
from institutional_factor_platform.research_outputs.storage import AssetPricingRepository

from .provenance import validate_identifier
from .schemas import PublicationKind, PublicationSummary


class DeliveryCatalog:
    """Read-only façade; every read reuses a Phase 1-5 authenticator."""

    def __init__(self, root: Path) -> None:
        self.root = root.resolve()
        phase1 = DataIngestionService(load_phase1_config(), root=self.root)
        factors = load_factor_config()
        pricing = load_asset_pricing_config()
        portfolio = load_portfolio_config()
        ml = load_ml_config()
        self.data = phase1.research
        self.repositories: dict[PublicationKind, Any] = {
            "factors": FactorRepository(self.root, self.root / factors.publication.manifest_root),
            "asset_pricing": AssetPricingRepository(
                self.root, self.root / pricing.publication.manifest_root
            ),
            "portfolio": PortfolioRepository(
                self.root, self.root / portfolio.publication.manifest_root
            ),
            "ml": MLRepository(self.root, self.root / ml.publication.manifest_root),
        }

    def list(self, kind: PublicationKind | None = None) -> tuple[PublicationSummary, ...]:
        kinds: tuple[PublicationKind, ...] = (
            (kind,) if kind else ("data", "factors", "asset_pricing", "portfolio", "ml")
        )
        records: list[PublicationSummary] = []
        for current in kinds:
            if current == "data":
                for dataset_id, _dataset_type, _status in self.data.list_authenticated():
                    handle = self.data.get(dataset_id)
                    records.append(
                        PublicationSummary(
                            kind="data",
                            publication_id=dataset_id,
                            schema_version=handle.schema_version,
                            validation_status=handle.validation_status.value,
                            configuration_hash=handle.configuration_hash,
                            git_commit=handle.git_commit,
                            created_at=None,
                        )
                    )
                continue
            repository = self.repositories[current]
            for publication_id in repository.list_authenticated():
                records.append(self._summary(current, repository.authenticate(publication_id)))
        return tuple(sorted(records, key=lambda item: (item.kind, item.publication_id)))

    def manifest(self, kind: PublicationKind, publication_id: str) -> dict[str, Any]:
        validate_identifier(publication_id)
        if kind == "data":
            return asdict(self.data.get(publication_id))
        return cast(
            dict[str, Any],
            self.repositories[kind].authenticate(publication_id).model_dump(mode="json"),
        )

    def find(self, publication_id: str) -> tuple[PublicationKind, dict[str, Any]]:
        validate_identifier(publication_id)
        matches: list[tuple[PublicationKind, dict[str, Any]]] = []
        for kind in ("data", "factors", "asset_pricing", "portfolio", "ml"):
            try:
                matches.append((kind, self.manifest(kind, publication_id)))
            except (EvidenceIntegrityError, OSError, ValueError):
                continue
        if len(matches) != 1:
            raise EvidenceIntegrityError("Publication identity is unavailable or ambiguous")
        return matches[0]

    def artifact_inventory(
        self, kind: PublicationKind, publication_id: str
    ) -> tuple[dict[str, Any], ...]:
        manifest = self.manifest(kind, publication_id)
        if kind == "data":
            return (
                {
                    "name": "standardized_data",
                    "checksum": manifest["checksum"],
                    "schema_version": manifest["schema_version"],
                },
            )
        if kind == "factors":
            return tuple(
                {
                    "name": name,
                    "checksum": manifest[f"{name}_checksum"]
                    if name != "factors"
                    else manifest["artifact_checksum"],
                }
                for name in ("factors", "portfolio_artifact", "validation_report", "diagnostics")
            )
        return tuple(
            {
                "name": item["name"],
                "checksum": item["checksum"],
                "byte_size": item["byte_size"],
                "media_type": item["media_type"],
            }
            for item in manifest["artifacts"]
        )

    def table(self, kind: PublicationKind, publication_id: str, name: str) -> pa.Table:
        validate_identifier(name)
        if kind == "data":
            return self.data.read_table(publication_id)
        if kind == "factors":
            repository = self.repositories[kind]
            if name == "observations":
                return repository.read_table(publication_id)
            if name == "portfolios":
                return repository.read_portfolios(publication_id)
            raise EvidenceIntegrityError("Unsupported authenticated factor table")
        if kind == "asset_pricing":
            return self.repositories[kind].read_table(publication_id, name)
        value = self._read_bound(kind, publication_id, name)
        if not isinstance(value, pa.Table):
            raise EvidenceIntegrityError("Requested authenticated artifact is not tabular")
        return value

    def document(self, kind: PublicationKind, publication_id: str, name: str) -> Any:
        validate_identifier(name)
        if kind == "factors":
            return self._read_factor_document(publication_id, name)
        value = self._read_bound(kind, publication_id, name)
        if isinstance(value, pa.Table):
            raise EvidenceIntegrityError("Requested authenticated artifact is not a document")
        return value

    def lineage(self, kind: PublicationKind, publication_id: str) -> Any:
        manifest = self.manifest(kind, publication_id)
        if kind == "data":
            return {
                "dataset_id": publication_id,
                "lineage_id": manifest["lineage_id"],
                "run_id": manifest["run_id"],
                "promotion_id": manifest["promotion_id"],
            }
        if kind == "factors":
            return self._read_factor_document(publication_id, "lineage")
        return self.document(kind, publication_id, "lineage")

    def _read_factor_document(self, publication_id: str, name: str) -> Any:
        fields = {
            "diagnostics": ("diagnostics_path", "diagnostics_checksum"),
            "validation": ("validation_report_path", "validation_report_checksum"),
            "lineage": ("lineage_path", "lineage_checksum"),
            "configuration": ("configuration_snapshot_path", "configuration_snapshot_checksum"),
        }
        if name not in fields:
            raise EvidenceIntegrityError("Unsupported authenticated factor document")
        manifest = self.repositories["factors"].authenticate(publication_id)
        path_field, checksum_field = fields[name]
        content = resolve_project_path(getattr(manifest, path_field), self.root).read_bytes()
        if hashlib.sha256(content).hexdigest() != getattr(manifest, checksum_field):
            raise EvidenceIntegrityError("Factor document changed during authenticated read")
        return json.loads(content)

    def _read_bound(self, kind: PublicationKind, publication_id: str, name: str) -> Any:
        if kind not in {"portfolio", "ml", "asset_pricing"}:
            raise EvidenceIntegrityError("Document artifact is unsupported for publication kind")
        repository = self.repositories[kind]
        manifest = repository.authenticate(publication_id)
        artifact = next((item for item in manifest.artifacts if item.name == name), None)
        if artifact is None or artifact.media_type == "application/x-joblib":
            raise EvidenceIntegrityError("Authenticated display artifact is unavailable")
        content = resolve_project_path(artifact.path, self.root).read_bytes()
        if (
            len(content) != artifact.byte_size
            or hashlib.sha256(content).hexdigest() != artifact.checksum
        ):
            raise EvidenceIntegrityError("Artifact changed during authenticated delivery read")
        if artifact.media_type == "application/json":
            return json.loads(content)
        return pq.read_table(pa.BufferReader(content))

    @staticmethod
    def _summary(kind: PublicationKind, manifest: Any) -> PublicationSummary:
        return PublicationSummary(
            kind=kind,
            publication_id=manifest.publication_id,
            schema_version=manifest.schema_version,
            validation_status=manifest.validation_status,
            configuration_hash=manifest.configuration_hash,
            git_commit=manifest.git_commit,
            created_at=manifest.created_at,
        )
