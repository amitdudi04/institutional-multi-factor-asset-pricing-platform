"""Deterministic research reports bound to stored publication metadata."""

import csv
import html
import io
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, cast

from institutional_factor_platform import __version__
from institutional_factor_platform.data.evidence import atomic_write_bytes, atomic_write_json
from institutional_factor_platform.exceptions import (
    EvidenceIntegrityError,
    PublicationConflictError,
)

from .catalog import DeliveryCatalog
from .config import DeliveryConfig
from .provenance import canonical_bytes, checksum, confined_path
from .schemas import ReportRecord, ReportRequest

DISCLAIMER = "Research software output only; not financial advice or an investment recommendation."
LIMITATIONS = (
    "Exact empirical reproduction requires the source data and mappings "
    "used for the reported release.",
    "Model explanations are not causal.",
    "Model performance is not guaranteed.",
)
TEMPLATE_VERSION = "1.0.0"


class ReportService:
    def __init__(self, root: Path, config: DeliveryConfig, catalog: DeliveryCatalog) -> None:
        self.root = root.resolve()
        self.config = config
        self.catalog = catalog
        self.output_root = (self.root / config.reports.output_directory).resolve()
        try:
            self.output_root.relative_to(self.root)
        except ValueError as exc:
            raise EvidenceIntegrityError("Report root escapes project root") from exc

    def generate(self, request: ReportRequest) -> ReportRecord:
        if request.format not in self.config.reports.allowed_formats:
            raise EvidenceIntegrityError("Unsupported report format")
        sources = []
        for reference in request.publications:
            manifest = self.catalog.manifest(reference.kind, reference.publication_id)
            sources.append(
                {
                    "kind": reference.kind,
                    "publication_id": reference.publication_id,
                    "configuration_hash": manifest.get("configuration_hash"),
                    "git_commit": manifest.get("git_commit"),
                    "created_at": manifest.get("created_at"),
                    "artifacts": self.catalog.artifact_inventory(
                        reference.kind, reference.publication_id
                    ),
                }
            )
        identity = {
            "template_version": TEMPLATE_VERSION,
            "format": request.format,
            "sections": request.sections,
            "sources": sources,
            "software_version": __version__,
            "delivery_config_hash": self.config.canonical_hash(),
        }
        report_id = "report-" + checksum(canonical_bytes(identity))[:32]
        extension = {"markdown": "md", "html": "html", "json": "json", "csv": "csv"}[request.format]
        output_path = confined_path(self.output_root, f"{report_id}.{extension}")
        manifest_path = confined_path(self.output_root, f"{report_id}.manifest.json")
        if manifest_path.exists():
            return self.verify(report_id)
        generated_at = self._generation_time(sources)
        document = {
            "report_id": report_id,
            "generated_at": generated_at.isoformat(),
            **identity,
            "limitations": LIMITATIONS,
            "disclaimer": DISCLAIMER,
        }
        content = self._render(request.format, document)
        output_checksum = checksum(content)
        manifest = {
            **document,
            "output_file": output_path.name,
            "output_checksum": output_checksum,
        }
        self.output_root.mkdir(parents=True, exist_ok=True)
        atomic_write_bytes(output_path, content)
        atomic_write_json(manifest_path, manifest)
        return self.verify(report_id)

    def verify(self, report_id: str) -> ReportRecord:
        manifest_path = confined_path(self.output_root, f"{report_id}.manifest.json")
        try:
            content = manifest_path.read_bytes()
            manifest = json.loads(content)
            output_path = confined_path(self.output_root, manifest["output_file"])
            output = output_path.read_bytes()
        except (OSError, KeyError, ValueError, json.JSONDecodeError) as exc:
            raise EvidenceIntegrityError("Report evidence is unavailable or malformed") from exc
        expected_keys = {
            "report_id",
            "generated_at",
            "template_version",
            "format",
            "sections",
            "sources",
            "software_version",
            "delivery_config_hash",
            "limitations",
            "disclaimer",
            "output_file",
            "output_checksum",
        }
        if set(manifest) != expected_keys:
            raise EvidenceIntegrityError("Report manifest schema changed after publication")
        try:
            identity = {
                "template_version": manifest["template_version"],
                "format": manifest["format"],
                "sections": manifest["sections"],
                "sources": manifest["sources"],
                "software_version": manifest["software_version"],
                "delivery_config_hash": manifest["delivery_config_hash"],
            }
            expected_report_id = "report-" + checksum(canonical_bytes(identity))[:32]
            extension = {
                "markdown": "md",
                "html": "html",
                "json": "json",
                "csv": "csv",
            }.get(manifest["format"])
            limitations = tuple(manifest["limitations"])
            expected_generation_time = self._generation_time(manifest["sources"]).isoformat()
        except (KeyError, TypeError, ValueError) as exc:
            raise EvidenceIntegrityError("Report manifest identity is malformed") from exc
        if (
            report_id != expected_report_id
            or manifest["report_id"] != report_id
            or extension is None
            or manifest["output_file"] != f"{report_id}.{extension}"
            or manifest["template_version"] != TEMPLATE_VERSION
            or manifest["software_version"] != __version__
            or manifest["delivery_config_hash"] != self.config.canonical_hash()
            or limitations != LIMITATIONS
            or manifest["disclaimer"] != DISCLAIMER
            or manifest["generated_at"] != expected_generation_time
        ):
            raise EvidenceIntegrityError("Report manifest identity changed after publication")
        if checksum(output) != manifest.get("output_checksum"):
            raise EvidenceIntegrityError("Report output changed after publication")
        for source in manifest["sources"]:
            current = self.catalog.manifest(source["kind"], source["publication_id"])
            artifacts = self.catalog.artifact_inventory(source["kind"], source["publication_id"])
            if (
                current.get("configuration_hash") != source["configuration_hash"]
                or current.get("git_commit") != source["git_commit"]
                or tuple(artifacts) != tuple(source["artifacts"])
            ):
                raise EvidenceIntegrityError("Report source identity changed")
        references = tuple(
            {"kind": source["kind"], "publication_id": source["publication_id"]}
            for source in manifest["sources"]
        )
        return ReportRecord.model_validate(
            {
                "report_id": report_id,
                "generated_at": manifest["generated_at"],
                "format": manifest["format"],
                "output_checksum": manifest["output_checksum"],
                "manifest_checksum": checksum(content),
                "publications": references,
            }
        )

    def read(self, report_id: str) -> bytes:
        self.verify(report_id)
        manifest = json.loads(
            confined_path(self.output_root, f"{report_id}.manifest.json").read_text("utf-8")
        )
        return confined_path(self.output_root, manifest["output_file"]).read_bytes()

    def manifest(self, report_id: str) -> dict[str, Any]:
        self.verify(report_id)
        return cast(
            dict[str, Any],
            json.loads(
                confined_path(self.output_root, f"{report_id}.manifest.json").read_text("utf-8")
            ),
        )

    @staticmethod
    def _render(format_name: str, document: dict[str, Any]) -> bytes:
        if format_name == "json":
            return canonical_bytes(document)
        if format_name == "csv":
            target = io.StringIO(newline="")
            writer = csv.writer(target, lineterminator="\n")
            writer.writerow(
                (
                    "report_id",
                    "generated_at",
                    "software_version",
                    "template_version",
                    "kind",
                    "publication_id",
                    "configuration_hash",
                    "git_commit",
                    "artifact_checksums",
                    "disclaimer",
                )
            )
            for source in document["sources"]:
                writer.writerow(
                    (
                        document["report_id"],
                        document["generated_at"],
                        document["software_version"],
                        document["template_version"],
                        source["kind"],
                        source["publication_id"],
                        source["configuration_hash"],
                        source["git_commit"],
                        ";".join(item["checksum"] for item in source["artifacts"]),
                        DISCLAIMER,
                    )
                )
            return target.getvalue().encode()
        if format_name == "html":
            rows = "".join(
                "<li>"
                + html.escape(
                    f"{x['kind']}: {x['publication_id']} | config={x['configuration_hash']} "
                    f"| git={x['git_commit']} | checksums="
                    + ",".join(item["checksum"] for item in x["artifacts"])
                )
                + "</li>"
                for x in document["sources"]
            )
            return (
                "<!doctype html><html><body><h1>Quantitative Research Report</h1>"
                + "<p>"
                + html.escape(
                    f"Report {document['report_id']} generated {document['generated_at']} "
                    f"with software {document['software_version']} and template "
                    f"{document['template_version']}."
                )
                + "</p><ul>"
                + rows
                + "</ul><p>"
                + html.escape(DISCLAIMER)
                + "</p></body></html>"
            ).encode()
        if format_name == "markdown":
            rows = "\n".join(
                f"- `{x['kind']}` — `{x['publication_id']}`; config "
                f"`{x['configuration_hash']}`; Git `{x['git_commit']}`; artifact checksums "
                + ", ".join(f"`{item['checksum']}`" for item in x["artifacts"])
                for x in document["sources"]
            )
            return (
                f"# Quantitative Research Report\n\nReport ID: `{document['report_id']}`  \n"
                f"Generated: `{document['generated_at']}`  \n"
                f"Software: `{document['software_version']}`  \n"
                f"Template: `{document['template_version']}`\n\n"
                f"## Research publications\n\n{rows}\n\n## Limitations\n\n"
                + "\n".join(f"- {x}" for x in LIMITATIONS)
                + f"\n\n> {DISCLAIMER}\n"
            ).encode()
        raise PublicationConflictError("Unsupported report renderer")

    @staticmethod
    def _generation_time(sources: list[dict[str, Any]]) -> datetime:
        values = [
            datetime.fromisoformat(str(source["created_at"]))
            for source in sources
            if source.get("created_at")
        ]
        return max(values) if values else datetime(1970, 1, 1, tzinfo=UTC)
