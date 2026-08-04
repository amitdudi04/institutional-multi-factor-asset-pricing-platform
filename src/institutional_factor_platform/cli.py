"""Minimal explicit Phase 1 command-line workflow."""

import argparse
import json
import sys
from datetime import UTC, date, datetime
from pathlib import Path

from institutional_factor_platform.data.config import load_phase1_config
from institutional_factor_platform.data.contracts import (
    CONTRACTS,
    FRENCH_FACTORS,
    MACRO_OBSERVATIONS,
    SEC_FACTS,
)
from institutional_factor_platform.data.domain import (
    DataArtifact,
    DataSource,
    DateRange,
    RetrievalRequest,
)
from institutional_factor_platform.data.lineage import LifecycleState, LineageStore
from institutional_factor_platform.data.manifests import DatasetManifest
from institutional_factor_platform.data.services import DataIngestionService
from institutional_factor_platform.data.sources.base import HttpTransport
from institutional_factor_platform.data.sources.fred import FredAdapter
from institutional_factor_platform.data.sources.french import KennethFrenchAdapter
from institutional_factor_platform.data.sources.owner_supplied import OwnerSuppliedAdapter
from institutional_factor_platform.data.sources.sec_edgar import SecEdgarAdapter
from institutional_factor_platform.data.storage import (
    RawStorage,
    authenticate_dataset_evidence,
    sha256_file,
)
from institutional_factor_platform.exceptions import ChecksumMismatchError, PlatformError
from institutional_factor_platform.factors.config import load_factor_config
from institutional_factor_platform.factors.service import FactorResearchService
from institutional_factor_platform.factors.storage import (
    FactorRepository,
    authenticate_factor_publication,
)
from institutional_factor_platform.logging import configure_logging


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="institutional-factor-platform")
    parser.add_argument("--config", type=Path, default=None, help="Phase 1 YAML configuration path")
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("validate-config", help="Validate configuration and print its hash")
    commands.add_parser("init-storage", help="Create approved local Phase 1 storage directories")
    inspect = commands.add_parser(
        "inspect-manifest", help="Validate and print a local JSON manifest"
    )
    inspect.add_argument("path", type=Path)
    listing = commands.add_parser("list-datasets", help="List registered DuckDB datasets")
    listing.add_argument("--research-ready", action="store_true")
    commands.add_parser("validate-catalog", help="Verify all promoted catalog evidence")
    commands.add_parser("reconcile", help="Reconcile publication lifecycle and catalog state")
    commands.add_parser("rebuild-catalog", help="Atomically rebuild the authenticated catalog")
    commands.add_parser("validate-factor-config", help="Validate Phase 2 factor configuration")
    commands.add_parser("list-factor-publications", help="List authenticated factor publications")
    verify_factor = commands.add_parser(
        "verify-factor-publication", help="Authenticate one Phase 2 factor publication"
    )
    verify_factor.add_argument("path", type=Path)
    compute_factors = commands.add_parser(
        "compute-factors", help="Build an immutable Phase 2 publication from authenticated parents"
    )
    compute_factors.add_argument("--parent", action="append", required=True)
    compute_factors.add_argument("--market-dataset", required=True)
    compute_factors.add_argument("--fundamental-dataset", required=True)
    compute_factors.add_argument("--factor-config", type=Path, default=None)
    publication = commands.add_parser(
        "verify-publication", help="Authenticate one persisted publication evidence bundle"
    )
    publication.add_argument("dataset_id")
    publication.add_argument("manifest", type=Path)
    lineage = commands.add_parser("inspect-lineage", help="Validate and print persisted lineage")
    lineage.add_argument("path", type=Path)
    dataset_manifest = commands.add_parser(
        "inspect-dataset-manifest", help="Validate and print a v5 dataset manifest"
    )
    dataset_manifest.add_argument("path", type=Path)
    verify = commands.add_parser("verify-raw", help="Verify a raw file against a SHA-256 checksum")
    verify.add_argument("path", type=Path)
    verify.add_argument("checksum")
    standardized = commands.add_parser(
        "verify-standardized", help="Verify a standardized file against SHA-256"
    )
    standardized.add_argument("path", type=Path)
    standardized.add_argument("checksum")
    reprocess = commands.add_parser(
        "reprocess-raw", help="Reprocess a verified existing raw artifact without retrieval"
    )
    reprocess.add_argument(
        "source", choices=["fred", "kenneth_french", "sec_edgar", "owner_supplied"]
    )
    reprocess.add_argument("dataset")
    reprocess.add_argument("contract", choices=sorted(CONTRACTS))
    reprocess.add_argument("path", type=Path)
    reprocess.add_argument("checksum")
    reprocess.add_argument("--media-type", required=True)
    reprocess.add_argument("--parameters-json", default="{}")
    fred = commands.add_parser("ingest-fred", help="Retrieve an approved FRED series")
    fred.add_argument("series", choices=["DGS3MO", "TB3MS"])
    _dates(fred)
    french = commands.add_parser(
        "ingest-french", help="Retrieve an approved Kenneth French dataset"
    )
    french.add_argument("dataset", choices=sorted(KennethFrenchAdapter.approved))
    sec = commands.add_parser("ingest-sec", help="Retrieve SEC company facts for one explicit CIK")
    sec.add_argument("cik")
    owner = commands.add_parser(
        "ingest-owner-factor-input", help="Ingest an owner Phase 2 input under a strict contract"
    )
    owner.add_argument("dataset")
    owner.add_argument("contract", choices=["factor_market_input", "factor_fundamental_input"])
    owner.add_argument("path", type=Path)
    owner.add_argument("--metadata-json", type=Path, required=True)
    return parser


def _dates(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--start", type=date.fromisoformat, required=True)
    parser.add_argument("--end", type=date.fromisoformat, required=True)


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        config = load_phase1_config(args.config)
        configure_logging(config.logging.level, config.logging.format)
        service = DataIngestionService(config)
        if args.command == "validate-config":
            print(config.configuration_hash())
        elif args.command == "init-storage":
            for path in service.initialize_storage():
                print(path)
        elif args.command == "inspect-manifest":
            print(
                json.dumps(
                    json.loads(args.path.read_text(encoding="utf-8")), indent=2, sort_keys=True
                )
            )
        elif args.command == "list-datasets":
            rows = (
                service.research.list_authenticated()
                if args.research_ready
                else service.catalog.list_datasets()
            )
            for row in rows:
                print("\t".join(row))
        elif args.command == "validate-catalog":
            service.catalog.verify_integrity(service.root)
            print("catalog integrity verified")
        elif args.command == "reconcile":
            print(json.dumps(service.recovery.reconcile_startup(), sort_keys=True))
        elif args.command == "rebuild-catalog":
            rebuilt = service.recovery.rebuild_catalog()
            print(rebuilt.path)
        elif args.command == "validate-factor-config":
            print(load_factor_config().canonical_hash())
        elif args.command == "list-factor-publications":
            factor_config = load_factor_config()
            repository = FactorRepository(
                service.root,
                service.root / factor_config.publication.manifest_root,
            )
            for publication_id in repository.list_authenticated():
                print(publication_id)
        elif args.command == "verify-factor-publication":
            factor_manifest = authenticate_factor_publication(args.path, service.root)
            print(factor_manifest.publication_id)
        elif args.command == "compute-factors":
            factor_service = FactorResearchService(
                load_factor_config(args.factor_config), service.root
            )
            result = factor_service.compute_and_publish(
                tuple(service.research.get(dataset_id) for dataset_id in args.parent),
                market_dataset_id=args.market_dataset,
                fundamental_dataset_id=args.fundamental_dataset,
            )
            print(result.publication_id)
        elif args.command == "verify-publication":
            authenticate_dataset_evidence(
                args.dataset_id,
                args.manifest,
                service.root,
                required_state=LifecycleState.FINALIZED,
            )
            print("publication evidence verified")
        elif args.command == "inspect-lineage":
            document = LineageStore(args.path).load()
            print(json.dumps(document.model_dump(mode="json"), indent=2, sort_keys=True))
        elif args.command == "inspect-dataset-manifest":
            dataset_manifest = DatasetManifest.model_validate_json(
                args.path.read_text(encoding="utf-8")
            )
            print(json.dumps(dataset_manifest.model_dump(mode="json"), indent=2, sort_keys=True))
        elif args.command == "verify-raw":
            artifact = DataArtifact(
                args.path,
                args.checksum,
                args.path.stat().st_size,
                "application/octet-stream",
                DataSource.OWNER_SUPPLIED,
                datetime.now(UTC),
            )
            RawStorage.verify(artifact)
            print("checksum verified")
        elif args.command == "verify-standardized":
            if not args.path.is_file() or sha256_file(args.path) != args.checksum:
                raise ChecksumMismatchError(
                    f"Standardized artifact failed checksum validation: {args.path}"
                )
            print("standardized checksum verified")
        elif args.command == "reprocess-raw":
            source = DataSource(args.source)
            parameters = json.loads(args.parameters_json)
            if not isinstance(parameters, dict):
                raise ValueError("--parameters-json must decode to an object")
            request = RetrievalRequest(source, args.dataset, parameters=parameters)
            artifact = DataArtifact(
                args.path,
                args.checksum,
                args.path.stat().st_size,
                args.media_type,
                source,
                datetime.fromtimestamp(args.path.stat().st_mtime, tz=UTC),
            )
            adapters = {
                DataSource.FRED: FredAdapter(HttpTransport(config.runtime)),
                DataSource.KENNETH_FRENCH: KennethFrenchAdapter(HttpTransport(config.runtime)),
                DataSource.SEC_EDGAR: SecEdgarAdapter(
                    config.sources.sec, HttpTransport(config.runtime)
                ),
                DataSource.OWNER_SUPPLIED: OwnerSuppliedAdapter(),
            }
            reprocessed_manifest = service.reprocess(
                adapters[source], artifact, request, CONTRACTS[args.contract]
            )
            print(reprocessed_manifest.dataset_id)
        elif args.command == "ingest-fred":
            request = RetrievalRequest(
                DataSource.FRED, args.series, DateRange(args.start, args.end)
            )
            service.ingest(
                FredAdapter(HttpTransport(config.runtime)),
                request,
                MACRO_OBSERVATIONS,
                "csv",
                "text/csv",
            )
        elif args.command == "ingest-french":
            request = RetrievalRequest(DataSource.KENNETH_FRENCH, args.dataset)
            service.ingest(
                KennethFrenchAdapter(HttpTransport(config.runtime)),
                request,
                FRENCH_FACTORS,
                "zip",
                "application/zip",
            )
        elif args.command == "ingest-sec":
            request = RetrievalRequest(DataSource.SEC_EDGAR, args.cik)
            service.ingest(
                SecEdgarAdapter(config.sources.sec, HttpTransport(config.runtime)),
                request,
                SEC_FACTS,
                "json",
                "application/json",
            )
        elif args.command == "ingest-owner-factor-input":
            metadata = json.loads(args.metadata_json.read_text(encoding="utf-8"))
            if not isinstance(metadata, dict):
                raise ValueError("--metadata-json must contain an object")
            contract = CONTRACTS[args.contract]
            parameters = {
                **metadata,
                "path": str(args.path.resolve()),
                "schema": contract.name,
                "contract_version": contract.version,
            }
            media_types = {
                ".csv": ("csv", "text/csv"),
                ".json": ("json", "application/json"),
                ".parquet": ("parquet", "application/vnd.apache.parquet"),
            }
            if args.path.suffix.lower() not in media_types:
                raise ValueError("Owner factor input must be CSV, JSON, or Parquet")
            extension, media_type = media_types[args.path.suffix.lower()]
            service.ingest(
                OwnerSuppliedAdapter(),
                RetrievalRequest(DataSource.OWNER_SUPPLIED, args.dataset, parameters=parameters),
                contract,
                extension,
                media_type,
            )
        else:  # pragma: no cover - argparse enforces command choices
            raise AssertionError(args.command)
        return 0
    except (PlatformError, OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
