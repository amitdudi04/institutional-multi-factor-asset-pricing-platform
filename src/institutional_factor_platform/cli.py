"""Minimal explicit Phase 1 command-line workflow."""

import argparse
import json
import sys
from datetime import UTC, date, datetime
from pathlib import Path

from institutional_factor_platform.asset_pricing.config import load_asset_pricing_config
from institutional_factor_platform.asset_pricing.service import AssetPricingResearchService
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
from institutional_factor_platform.ml.config import load_ml_config
from institutional_factor_platform.ml.publication import MLRepository
from institutional_factor_platform.ml.service import MLResearchService
from institutional_factor_platform.portfolio.config import load_portfolio_config
from institutional_factor_platform.portfolio.service import PortfolioResearchService
from institutional_factor_platform.research_outputs.portfolio_storage import (
    PortfolioRepository,
    authenticate_portfolio_publication,
)
from institutional_factor_platform.research_outputs.storage import (
    AssetPricingRepository,
    authenticate_asset_pricing_publication,
)


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
    commands.add_parser("validate-asset-pricing-config", help="Validate Phase 3 configuration")
    commands.add_parser(
        "list-asset-pricing-publications", help="List authenticated Phase 3 publications"
    )
    verify_asset_pricing = commands.add_parser(
        "verify-asset-pricing-publication", help="Authenticate one Phase 3 publication"
    )
    verify_asset_pricing.add_argument("path", type=Path)
    compute_asset_pricing = commands.add_parser(
        "compute-asset-pricing",
        help="Build Phase 3 research from one authenticated Phase 2 publication",
    )
    compute_asset_pricing.add_argument("factor_publication_id")
    compute_asset_pricing.add_argument("--model", action="append", default=None)
    compute_asset_pricing.add_argument("--asset-pricing-config", type=Path, default=None)
    commands.add_parser(
        "validate-portfolio-config", help="Validate Phase 4 portfolio configuration"
    )
    commands.add_parser(
        "list-portfolio-publications", help="List authenticated Phase 4 publications"
    )
    verify_portfolio = commands.add_parser(
        "verify-portfolio-publication", help="Authenticate one Phase 4 publication"
    )
    verify_portfolio.add_argument("path", type=Path)
    compute_portfolio = commands.add_parser(
        "compute-portfolio", help="Run Phase 4 from connected authenticated Phase 2/3 evidence"
    )
    compute_portfolio.add_argument("asset_pricing_publication_id")
    compute_portfolio.add_argument(
        "method",
        choices=[
            "equal_weight",
            "minimum_variance",
            "mean_variance",
            "maximum_sharpe",
            "maximum_diversification",
            "risk_parity",
            "hrp",
            "cvar",
        ],
    )
    compute_portfolio.add_argument("--portfolio-config", type=Path, default=None)
    validate_ml = commands.add_parser(
        "validate-ml-config", help="Validate Phase 5 ML configuration"
    )
    validate_ml.add_argument("--ml-config", type=Path, default=None)
    build_ml = commands.add_parser(
        "build-ml-dataset", help="Validate an authenticated Phase 5 feature/target assembly"
    )
    build_ml.add_argument("asset_pricing_publication_id")
    build_ml.add_argument("--ml-config", type=Path, default=None)
    train_ml = commands.add_parser(
        "train-ml-model", help="Train and publish one authenticated Phase 5 research model"
    )
    train_ml.add_argument("asset_pricing_publication_id")
    train_ml.add_argument("family")
    train_ml.add_argument("--ml-config", type=Path, default=None)
    commands.add_parser("list-ml-publications", help="List authenticated Phase 5 publications")
    verify_ml = commands.add_parser(
        "verify-ml-publication", help="Authenticate one immutable Phase 5 publication"
    )
    verify_ml.add_argument("publication_id")
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
        elif args.command == "validate-asset-pricing-config":
            print(load_asset_pricing_config().canonical_hash())
        elif args.command == "list-asset-pricing-publications":
            pricing_config = load_asset_pricing_config()
            pricing_repository = AssetPricingRepository(
                service.root, service.root / pricing_config.publication.manifest_root
            )
            for publication_id in pricing_repository.list_authenticated():
                print(publication_id)
        elif args.command == "verify-asset-pricing-publication":
            manifest = authenticate_asset_pricing_publication(args.path, service.root)
            print(manifest.publication_id)
        elif args.command == "compute-asset-pricing":
            factor_config = load_factor_config()
            factor_repository = FactorRepository(
                service.root, service.root / factor_config.publication.manifest_root
            )
            pricing_service = AssetPricingResearchService(
                load_asset_pricing_config(args.asset_pricing_config),
                service.root,
                factor_repository,
            )
            manifest = pricing_service.compute_and_publish(
                args.factor_publication_id,
                tuple(args.model) if args.model else None,
            )
            print(manifest.publication_id)
        elif args.command == "validate-portfolio-config":
            print(load_portfolio_config().canonical_hash())
        elif args.command == "list-portfolio-publications":
            portfolio_config = load_portfolio_config()
            portfolio_repository = PortfolioRepository(
                service.root, service.root / portfolio_config.publication.manifest_root
            )
            for publication_id in portfolio_repository.list_authenticated():
                print(publication_id)
        elif args.command == "verify-portfolio-publication":
            portfolio_manifest = authenticate_portfolio_publication(args.path, service.root)
            print(portfolio_manifest.publication_id)
        elif args.command == "compute-portfolio":
            factor_config = load_factor_config()
            pricing_config = load_asset_pricing_config()
            portfolio_config = load_portfolio_config(args.portfolio_config)
            portfolio_service = PortfolioResearchService(
                portfolio_config,
                service.root,
                FactorRepository(
                    service.root, service.root / factor_config.publication.manifest_root
                ),
                AssetPricingRepository(
                    service.root, service.root / pricing_config.publication.manifest_root
                ),
            )
            portfolio_result = portfolio_service.compute_and_publish(
                args.asset_pricing_publication_id, args.method
            )
            print(portfolio_result.publication_id)
        elif args.command == "validate-ml-config":
            print(load_ml_config(args.ml_config).canonical_hash())
        elif args.command in {
            "build-ml-dataset",
            "train-ml-model",
            "list-ml-publications",
            "verify-ml-publication",
        }:
            ml_config = load_ml_config(getattr(args, "ml_config", None))
            factor_config = load_factor_config()
            pricing_config = load_asset_pricing_config()
            factor_repository = FactorRepository(
                service.root, service.root / factor_config.publication.manifest_root
            )
            pricing_repository = AssetPricingRepository(
                service.root, service.root / pricing_config.publication.manifest_root
            )
            ml_repository = MLRepository(
                service.root, service.root / ml_config.publication.manifest_root
            )
            if args.command == "list-ml-publications":
                for publication_id in ml_repository.list_authenticated():
                    print(publication_id)
            elif args.command == "verify-ml-publication":
                print(ml_repository.authenticate(args.publication_id).publication_id)
            elif args.command == "build-ml-dataset":
                dataset, metadata = MLResearchService(
                    ml_config, service.root, factor_repository, pricing_repository
                ).build_authenticated_dataset(args.asset_pricing_publication_id)
                print(json.dumps({**metadata, "rows": len(dataset)}, sort_keys=True))
            else:
                ml_manifest = MLResearchService(
                    ml_config, service.root, factor_repository, pricing_repository
                ).train_evaluate_publish(args.asset_pricing_publication_id, args.family)
                print(ml_manifest.publication_id)
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
