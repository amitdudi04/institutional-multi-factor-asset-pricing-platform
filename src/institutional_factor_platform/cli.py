"""Minimal explicit Phase 1 command-line workflow."""

import argparse
import json
import sys
from datetime import UTC, date, datetime
from pathlib import Path

from institutional_factor_platform.data.config import load_phase1_config
from institutional_factor_platform.data.contracts import (
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
from institutional_factor_platform.data.services import DataIngestionService
from institutional_factor_platform.data.sources.base import HttpTransport
from institutional_factor_platform.data.sources.fred import FredAdapter
from institutional_factor_platform.data.sources.french import KennethFrenchAdapter
from institutional_factor_platform.data.sources.sec_edgar import SecEdgarAdapter
from institutional_factor_platform.data.storage import RawStorage
from institutional_factor_platform.exceptions import PlatformError
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
    commands.add_parser("list-datasets", help="List registered DuckDB datasets")
    verify = commands.add_parser("verify-raw", help="Verify a raw file against a SHA-256 checksum")
    verify.add_argument("path", type=Path)
    verify.add_argument("checksum")
    fred = commands.add_parser("ingest-fred", help="Retrieve an approved FRED series")
    fred.add_argument("series", choices=["DGS3MO", "TB3MS"])
    _dates(fred)
    french = commands.add_parser(
        "ingest-french", help="Retrieve an approved Kenneth French dataset"
    )
    french.add_argument("dataset", choices=sorted(KennethFrenchAdapter.approved))
    sec = commands.add_parser("ingest-sec", help="Retrieve SEC company facts for one explicit CIK")
    sec.add_argument("cik")
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
            for row in service.catalog.list_datasets():
                print("\t".join(row))
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
        else:  # pragma: no cover - argparse enforces command choices
            raise AssertionError(args.command)
        return 0
    except (PlatformError, OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
