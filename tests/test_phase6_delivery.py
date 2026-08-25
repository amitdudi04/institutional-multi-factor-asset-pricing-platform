from __future__ import annotations

import json
import logging
import os
import sys
import threading
import time
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from types import SimpleNamespace
from typing import Any
from unittest.mock import Mock

import httpx
import pyarrow as pa
import pyarrow.parquet as pq
import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from institutional_factor_platform.api.app import create_app
from institutional_factor_platform.dashboard import app as dashboard_app
from institutional_factor_platform.dashboard import launcher as dashboard_launcher
from institutional_factor_platform.dashboard.client import DashboardClient
from institutional_factor_platform.dashboard.presentation import (
    EMPTY_STATE,
    PAGES,
    chart_from_page,
    format_value,
    provenance_panel,
    publication_options,
)
from institutional_factor_platform.data.domain import DatasetStatus
from institutional_factor_platform.delivery.catalog import DeliveryCatalog
from institutional_factor_platform.delivery.config import DeliveryConfig, load_delivery_config
from institutional_factor_platform.delivery.provenance import (
    canonical_bytes,
    checksum,
    confined_path,
    validate_identifier,
)
from institutional_factor_platform.delivery.reporting import ReportService
from institutional_factor_platform.delivery.schemas import (
    Page,
    PublicationReference,
    PublicationSummary,
    ReportRecord,
    ReportRequest,
)
from institutional_factor_platform.delivery.service import DeliveryService
from institutional_factor_platform.exceptions import (
    ConfigurationError,
    EvidenceIntegrityError,
)
from institutional_factor_platform.observability.logging import operational_log, redact
from institutional_factor_platform.observability.metrics import OperationalMetrics


def delivery_config(tmp_path: Path, **api_overrides: Any) -> DeliveryConfig:
    api = {
        "host": "127.0.0.1",
        "port": 8000,
        "prefix": "/api/v1",
        "allow_non_loopback": False,
        "unsafe_development_anonymous_non_loopback": False,
        "authentication": "disabled",
        "token_environment_variable": "IFP_TEST_TOKEN",
        "allowed_origins": [],
        "trusted_hosts": ["testserver", "testclient", "localhost", "127.0.0.1"],
        "maximum_request_bytes": 1024,
        "default_page_size": 2,
        "maximum_page_size": 5,
        "timeout_seconds": 5,
        "requests_per_minute": 100,
        **api_overrides,
    }
    return DeliveryConfig.model_validate(
        {
            "schema_version": "1.0.0",
            "environment": "local",
            "api": api,
            "dashboard": {
                "api_url": "http://127.0.0.1:8000/api/v1",
                "maximum_chart_rows": 10,
            },
            "reports": {
                "output_directory": "delivery-reports",
                "maximum_rows": 100,
                "allowed_formats": ["markdown", "html", "json", "csv"],
            },
            "cache": {"enabled": True, "maximum_entries": 4},
            "logging": {"level": "INFO", "format": "json"},
            "features": {"reports": True, "exports": True},
        }
    )


class FakeCatalog:
    def __init__(self) -> None:
        self.changed = False
        self.summary = PublicationSummary(
            kind="factors",
            publication_id="factor-123",
            schema_version="1.0.0",
            validation_status=DatasetStatus.PASS,
            configuration_hash="a" * 64,
            git_commit="abc123",
            created_at=datetime(2026, 1, 1, tzinfo=UTC),
        )

    def list(self, kind: str | None = None) -> tuple[PublicationSummary, ...]:
        return () if kind == "ml" else (self.summary,)

    def manifest(self, kind: str, publication_id: str) -> dict[str, Any]:
        if publication_id != "factor-123":
            raise EvidenceIntegrityError("missing secret path C:/private")
        return {
            **self.summary.model_dump(mode="json"),
            "configuration_hash": "b" * 64 if self.changed else "a" * 64,
            "metadata": [{"factor_id": "value", "unit": "return"}],
        }

    def find(self, publication_id: str) -> tuple[str, dict[str, Any]]:
        return "factors", self.manifest("factors", publication_id)

    def lineage(self, kind: str, publication_id: str) -> dict[str, str]:
        self.manifest(kind, publication_id)
        return {"publication_id": publication_id, "parent": "data-123"}

    def artifact_inventory(self, kind: str, publication_id: str) -> tuple[dict[str, Any], ...]:
        self.manifest(kind, publication_id)
        return ({"name": "factors", "checksum": "c" * 64},)

    def document(self, kind: str, publication_id: str, name: str) -> dict[str, Any]:
        self.manifest(kind, publication_id)
        return {"publication_id": publication_id, "artifact": name}


class FakeReports:
    def verify(self, report_id: str) -> ReportRecord:
        if report_id != "report-123":
            raise EvidenceIntegrityError("missing")
        return ReportRecord(
            report_id=report_id,
            generated_at=datetime(2026, 1, 1, tzinfo=UTC),
            format="markdown",
            output_checksum="d" * 64,
            manifest_checksum="e" * 64,
            publications=(PublicationReference(kind="factors", publication_id="factor-123"),),
        )

    def read(self, report_id: str) -> bytes:
        self.verify(report_id)
        return b"# Report"

    def manifest(self, report_id: str) -> dict[str, str]:
        self.verify(report_id)
        return {"report_id": report_id}


class FakeDelivery:
    def __init__(self) -> None:
        self.root = Path.cwd()
        self.catalog = FakeCatalog()
        self.reports = FakeReports()

    def publications(self, kind: str | None, offset: int, limit: int) -> Page:
        items = self.catalog.list(kind)
        return Page(
            items=tuple(x.model_dump(mode="json") for x in items[offset : offset + limit]),
            offset=offset,
            limit=limit,
            total=len(items),
        )

    def publication(self, kind: str, publication_id: str) -> dict[str, Any]:
        return self.catalog.manifest(kind, publication_id)

    def find_publication(self, publication_id: str) -> dict[str, Any]:
        kind, manifest = self.catalog.find(publication_id)
        return {"kind": kind, "manifest": manifest}

    def table_page(
        self, kind: str, publication_id: str, artifact: str, offset: int, limit: int
    ) -> Page:
        self.catalog.manifest(kind, publication_id)
        return Page(
            items=({"publication_id": publication_id, "artifact": artifact},),
            offset=offset,
            limit=limit,
            total=1,
        )

    def create_report(self, request: ReportRequest) -> ReportRecord:
        assert request.publications
        return self.reports.verify("report-123")


def test_configuration_security_and_identity(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    config = delivery_config(tmp_path)
    assert len(config.canonical_hash()) == 64
    config.api.validate_binding()
    assert config.api.token() is None

    with pytest.raises(ValidationError, match="wildcard"):
        delivery_config(tmp_path, allowed_origins=["*"])
    with pytest.raises(ValidationError, match="default page"):
        delivery_config(tmp_path, default_page_size=6)
    with pytest.raises(ValidationError, match="project-relative"):
        DeliveryConfig.model_validate(
            {
                **config.model_dump(mode="json"),
                "reports": {**config.reports.model_dump(mode="json"), "output_directory": "../x"},
            }
        )

    external = delivery_config(tmp_path, host="0.0.0.0")
    with pytest.raises(ConfigurationError, match="explicit authorization"):
        external.api.validate_binding()
    external = delivery_config(tmp_path, host="delivery.local", allow_non_loopback=True)
    with pytest.raises(ConfigurationError, match="Anonymous"):
        external.api.validate_binding()
    external = delivery_config(
        tmp_path,
        host="0.0.0.0",
        allow_non_loopback=True,
        unsafe_development_anonymous_non_loopback=True,
    )
    external.api.validate_binding()
    monkeypatch.setenv("IFP_TEST_TOKEN", " ")
    with pytest.raises(ConfigurationError, match="cannot be empty"):
        external.api.token()
    monkeypatch.setenv("IFP_TEST_TOKEN", "owner-secret")
    assert external.api.token() == "owner-secret"

    source = Path("config/delivery.yaml")
    loaded = load_delivery_config(source)
    assert loaded.schema_version == "1.0.0"
    custom = tmp_path / "delivery.yaml"
    custom.write_text(source.read_text("utf-8"), encoding="utf-8")
    monkeypatch.setenv("IFP_DELIVERY_CONFIG", str(custom))
    assert load_delivery_config().canonical_hash() == loaded.canonical_hash()
    custom.write_text("unknown: true", encoding="utf-8")
    with pytest.raises(ConfigurationError, match="Invalid delivery"):
        load_delivery_config(custom)


def test_provenance_controls(tmp_path: Path) -> None:
    assert validate_identifier("report-safe_1.0") == "report-safe_1.0"
    for unsafe in ("../secret", "a", "C:\\secret", "bad/name"):
        with pytest.raises(EvidenceIntegrityError):
            validate_identifier(unsafe)
    assert confined_path(tmp_path, "report-safe.json").parent == tmp_path.resolve()
    for unsafe in ("../escape.json", "sub/path.json", "bad name.json"):
        with pytest.raises(EvidenceIntegrityError):
            confined_path(tmp_path, unsafe)
    content = canonical_bytes({"b": 1, "a": 2})
    assert content == b'{"a":2,"b":1}'
    assert len(checksum(content)) == 64


def test_api_system_empty_state_and_security(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    config = delivery_config(tmp_path)
    service = FakeDelivery()
    client = TestClient(create_app(config, service))  # type: ignore[arg-type]

    for endpoint in ("health", "ready", "version", "governance", "limitations"):
        response = client.get(f"/api/v1/{endpoint}")
        assert response.status_code == 200
        assert response.headers["x-content-type-options"] == "nosniff"
        assert response.headers["x-frame-options"] == "DENY"
        assert response.headers["cache-control"] == "no-store"
        assert response.headers["x-correlation-id"]
    assert client.get("/api/v1/ready").json()["empty_state"] is False

    response = client.get("/api/v1/publications", params={"offset": 0, "limit": 1})
    assert response.json()["total"] == 1
    invalid_page = client.get("/api/v1/publications", params={"limit": 6})
    assert invalid_page.status_code == 422
    assert invalid_page.json()["error"]["code"] == "invalid_request"
    assert client.get("/api/v1/publications/../secret").status_code in {404, 422}
    response = client.get("/api/v1/publications/missing-123")
    assert response.status_code == 422
    assert "private" not in response.text
    assert "traceback" not in response.text.lower()
    assert client.get("/api/v1/health", headers={"host": "evil.example"}).status_code == 400
    assert (
        client.get("/api/v1/health", headers={"x-correlation-id": "x\ninvalid"}).status_code == 400
    )

    monkeypatch.setenv("IFP_TEST_TOKEN", "owner-secret")
    protected = delivery_config(tmp_path, authentication="required")
    secured = TestClient(create_app(protected, service))  # type: ignore[arg-type]
    assert secured.get("/api/v1/health").status_code == 200
    assert secured.get("/api/v1/ready").status_code == 401
    assert (
        secured.get("/api/v1/ready", headers={"authorization": "Bearer wrong"}).status_code == 401
    )
    assert (
        secured.get("/api/v1/ready", headers={"authorization": "Bearer owner-secret"}).status_code
        == 200
    )
    monkeypatch.delenv("IFP_TEST_TOKEN")
    with pytest.raises(ValueError, match="no configured token"):
        create_app(protected, service)  # type: ignore[arg-type]

    cors_config = delivery_config(tmp_path, allowed_origins=["http://127.0.0.1:8501"])
    cors = TestClient(create_app(cors_config, service))  # type: ignore[arg-type]
    allowed = cors.options(
        "/api/v1/health",
        headers={
            "origin": "http://127.0.0.1:8501",
            "access-control-request-method": "GET",
        },
    )
    assert allowed.headers["access-control-allow-origin"] == "http://127.0.0.1:8501"
    denied = cors.options(
        "/api/v1/health",
        headers={"origin": "https://evil.example", "access-control-request-method": "GET"},
    )
    assert "access-control-allow-origin" not in denied.headers


def test_api_publication_families_and_reports(tmp_path: Path) -> None:
    service = FakeDelivery()
    client = TestClient(create_app(delivery_config(tmp_path), service))  # type: ignore[arg-type]
    assert client.get("/api/v1/publications/factor-123").status_code == 200
    assert client.get("/api/v1/publications/factor-123/verify").json()["authenticated"]
    assert client.get("/api/v1/publications/factor-123/lineage").status_code == 200
    assert client.get("/api/v1/publications/factor-123/artifacts").status_code == 200

    families = {
        "data": (),
        "factors": ("definitions", "diagnostics", "observations"),
        "asset-pricing": ("models", "coefficients", "diagnostics", "comparisons"),
        "portfolios": ("weights", "performance", "risk", "scenarios", "costs"),
        "ml": (
            "model-card",
            "predictions",
            "evaluation",
            "explanations",
            "drift",
            "economic-evaluation",
        ),
    }
    for family, artifacts in families.items():
        assert client.get(f"/api/v1/{family}/publications").status_code == 200
        assert client.get(f"/api/v1/{family}/publications/factor-123").status_code == 200
        for artifact in artifacts:
            assert (
                client.get(f"/api/v1/{family}/publications/factor-123/{artifact}").status_code
                == 200
            )

    payload = {
        "publications": [{"kind": "factors", "publication_id": "factor-123"}],
        "format": "markdown",
    }
    created = client.post("/api/v1/reports", json=payload)
    assert created.status_code == 201
    assert client.get("/api/v1/reports/report-123").text == "# Report"
    assert client.get("/api/v1/reports/report-123/manifest").status_code == 200
    assert (
        client.post(
            "/api/v1/reports", content="x", headers={"content-type": "text/plain"}
        ).status_code
        == 415
    )
    assert (
        client.post(
            "/api/v1/reports",
            content=b"{" + b"x" * 2000,
            headers={"content-type": "application/json"},
        ).status_code
        == 413
    )
    assert (
        client.post(
            "/api/v1/reports",
            content="{}",
            headers={"content-type": "application/json", "content-length": "invalid"},
        ).status_code
        == 413
    )


def test_api_rate_limit_and_internal_error(tmp_path: Path) -> None:
    limited = delivery_config(tmp_path, requests_per_minute=1)
    client = TestClient(create_app(limited, FakeDelivery()))  # type: ignore[arg-type]
    assert client.get("/api/v1/health").status_code == 200
    assert client.get("/api/v1/health").status_code == 429

    service = FakeDelivery()
    service.catalog.list = Mock(side_effect=RuntimeError("C:/secret token=abc"))
    client = TestClient(create_app(delivery_config(tmp_path), service))  # type: ignore[arg-type]
    response = client.get("/api/v1/ready")
    assert response.status_code == 500
    assert "secret" not in response.text


def test_report_formats_restart_and_authentication(tmp_path: Path) -> None:
    config = delivery_config(tmp_path)
    catalog = FakeCatalog()
    service = ReportService(tmp_path, config, catalog)  # type: ignore[arg-type]
    reference = PublicationReference(kind="factors", publication_id="factor-123")
    for format_name in ("markdown", "html", "json", "csv"):
        request = ReportRequest(publications=(reference,), format=format_name)
        record = service.generate(request)
        assert record == service.generate(request)
        assert record == service.verify(record.report_id)
        content = service.read(record.report_id)
        assert b"factor-123" in content
        manifest = service.manifest(record.report_id)
        assert manifest["output_checksum"] == record.output_checksum
        assert "financial advice" in str(manifest["disclaimer"])
    html_record = service.generate(ReportRequest(publications=(reference,), format="html"))
    assert b"<script" not in service.read(html_record.report_id)

    target = service.output_root / f"{html_record.report_id}.html"
    target.write_bytes(b"changed")
    with pytest.raises(EvidenceIntegrityError, match="changed"):
        service.verify(html_record.report_id)
    target.unlink()

    json_record = service.generate(ReportRequest(publications=(reference,), format="json"))
    manifest_path = service.output_root / f"{json_record.report_id}.manifest.json"
    original_manifest = manifest_path.read_bytes()
    changed_manifest = json.loads(original_manifest)
    changed_manifest["limitations"] = ["altered disclosure"]
    manifest_path.write_text(json.dumps(changed_manifest), encoding="utf-8")
    with pytest.raises(EvidenceIntegrityError, match="manifest identity"):
        service.verify(json_record.report_id)
    manifest_path.write_bytes(original_manifest)
    catalog.changed = True
    with pytest.raises(EvidenceIntegrityError, match="source identity"):
        service.verify(json_record.report_id)
    with pytest.raises(EvidenceIntegrityError):
        service.verify("../escape")


def test_dashboard_presentation_and_client(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    assert len(PAGES) == 9
    assert "No authenticated" in EMPTY_STATE
    assert format_value(None) == "Unavailable"
    assert format_value(1234.56789, "USD") == "1,234.5679 USD"
    assert format_value(datetime(2026, 1, 1, tzinfo=UTC)).startswith("2026-01-01")
    assert format_value("PASS") == "PASS"
    panel = provenance_panel({"publication_id": "factor-123", "validation_status": "PASS"})
    assert panel["Publication"] == "factor-123"
    assert panel["Git commit"] == "Unavailable"
    options = publication_options(
        [
            {"publication_id": "asset-pricing-old", "created_at": "2026-01-01T00:00:00Z"},
            {"publication_id": "asset-pricing-final", "created_at": "2026-02-01T00:00:00Z"},
        ]
    )
    assert options[0]["publication_id"] == "asset-pricing-final"
    preferred = publication_options(options, "asset-pricing-old")
    assert preferred[0]["publication_id"] == "asset-pricing-old"
    assert chart_from_page([], "date", "value", 5) is None
    assert chart_from_page([{"other": 1}], "date", "value", 5) is None
    figure = chart_from_page([{"date": "2026-01-01", "value": 1.0}], "date", "value", 5, "return")
    assert figure is not None and figure.layout.template

    config = delivery_config(tmp_path)
    client = DashboardClient(config)
    for path in ("../secret", "/absolute", "file:C:/x", "unknown/path", "bad\\path"):
        with pytest.raises(EvidenceIntegrityError):
            client.get(path)

    class Response:
        def raise_for_status(self) -> None:
            return None

        def json(self) -> dict[str, bool]:
            return {"ok": True}

    fake = Mock()
    fake.__enter__ = Mock(return_value=fake)
    fake.__exit__ = Mock(return_value=False)
    fake.get.return_value = Response()
    fake.post.return_value = Response()
    monkeypatch.setattr(httpx, "Client", Mock(return_value=fake))
    assert client.get("ready") == {"ok": True}
    assert httpx.Client.call_args.kwargs["timeout"] == 600
    assert client.get("asset-pricing/publications") == {"ok": True}
    assert httpx.Client.call_args.kwargs["timeout"] == 600
    assert client.post_report({"publications": []}) == {"ok": True}
    monkeypatch.setenv("IFP_TEST_TOKEN", "owner-secret")
    assert client._headers() == {"authorization": "Bearer owner-secret"}
    timeout_request = httpx.Request("GET", "http://127.0.0.1:8000/api/v1/ready")
    assert "timed out" in client.safe_error(httpx.ReadTimeout("slow", request=timeout_request))
    response = httpx.Response(401, request=timeout_request)
    assert "authorization failed (401)" in client.safe_error(
        httpx.HTTPStatusError("unauthorized", request=timeout_request, response=response)
    )


def test_delivery_catalog_serializes_authenticated_discovery() -> None:
    catalog = DeliveryCatalog.__new__(DeliveryCatalog)
    catalog.root = Path.cwd()
    catalog._authentication_lock = threading.RLock()
    active = 0
    maximum_active = 0
    state_lock = threading.Lock()

    class DataRepository:
        def list_authenticated(self) -> tuple[tuple[str, str, str], ...]:
            nonlocal active, maximum_active
            with state_lock:
                active += 1
                maximum_active = max(maximum_active, active)
            time.sleep(0.05)
            with state_lock:
                active -= 1
            return ()

    catalog.data = DataRepository()
    catalog.repositories = {}
    workers = [threading.Thread(target=catalog.list, args=("data",)) for _ in range(2)]
    for worker in workers:
        worker.start()
    for worker in workers:
        worker.join()
    assert maximum_active == 1


def test_metrics_and_log_redaction(caplog: pytest.LogCaptureFixture) -> None:
    metrics = OperationalMetrics()
    metrics.increment("requests")
    metrics.increment("requests")
    assert metrics.snapshot() == {"requests": 2}
    metrics.clear()
    assert metrics.snapshot() == {}
    assert "owner-secret" not in redact("Bearer owner-secret")
    assert "abc" not in redact("token=abc")
    logger = logging.getLogger("phase6-test")
    with caplog.at_level(logging.INFO, logger="phase6-test"):
        operational_log(logger, logging.INFO, "request", authorization="Bearer top-secret")
    assert "top-secret" not in caplog.text


class Manifest:
    def __init__(self, publication_id: str, artifacts: tuple[Any, ...] = ()) -> None:
        self.publication_id = publication_id
        self.schema_version = "1.0.0"
        self.validation_status = "PASS"
        self.configuration_hash = "a" * 64
        self.git_commit = "abc123"
        self.created_at = datetime(2026, 1, 1, tzinfo=UTC)
        self.artifacts = artifacts

    def model_dump(self, mode: str) -> dict[str, Any]:
        del mode
        return {
            "publication_id": self.publication_id,
            "schema_version": self.schema_version,
            "validation_status": self.validation_status,
            "configuration_hash": self.configuration_hash,
            "git_commit": self.git_commit,
            "created_at": self.created_at.isoformat(),
            "artifacts": [vars(item) for item in self.artifacts],
        }


class Repository:
    def __init__(self, manifest: Manifest, table: pa.Table | None = None) -> None:
        self.value = manifest
        self.table_value = table or pa.table({"value": [1]})

    def list_authenticated(self) -> tuple[str, ...]:
        return (self.value.publication_id,)

    def authenticate(self, publication_id: str) -> Manifest:
        if publication_id != self.value.publication_id:
            raise EvidenceIntegrityError("missing")
        return self.value

    def read_table(self, publication_id: str, name: str | None = None) -> pa.Table:
        self.authenticate(publication_id)
        return self.table_value

    def read_portfolios(self, publication_id: str) -> pa.Table:
        return self.read_table(publication_id)


class DataRepository:
    def list_authenticated(self) -> list[tuple[str, str, str]]:
        return [("data-123", "1.0.0", "PASS")]

    def get(self, publication_id: str) -> Any:
        if publication_id != "data-123":
            raise EvidenceIntegrityError("missing")
        return DataHandle(
            dataset_id="data-123",
            checksum="f" * 64,
            schema_version="1.0.0",
            configuration_hash="a" * 64,
            git_commit="abc123",
            validation_status=DatasetStatus.PASS,
            lineage_id="lineage-123",
            run_id="run-123",
            promotion_id="promotion-123",
        )

    def read_table(self, publication_id: str) -> pa.Table:
        self.get(publication_id)
        return pa.table({"value": [1, 2]})


@dataclass(frozen=True)
class DataHandle:
    dataset_id: str
    checksum: str
    schema_version: str
    configuration_hash: str
    git_commit: str
    validation_status: DatasetStatus
    lineage_id: str
    run_id: str
    promotion_id: str


def test_catalog_all_repository_paths(tmp_path: Path) -> None:
    json_content = json.dumps({"publication_id": "portfolio-123", "value": 1}).encode()
    json_path = tmp_path / "artifact.json"
    json_path.write_bytes(json_content)
    table = pa.table({"date": ["2026-01-01"], "value": [1.0]})
    table_path = tmp_path / "artifact.parquet"
    pq.write_table(table, table_path)
    artifacts = (
        SimpleNamespace(
            name="summary",
            path="artifact.json",
            checksum=checksum(json_content),
            byte_size=len(json_content),
            media_type="application/json",
        ),
        SimpleNamespace(
            name="observations",
            path="artifact.parquet",
            checksum=checksum(table_path.read_bytes()),
            byte_size=table_path.stat().st_size,
            media_type="application/vnd.apache.parquet",
        ),
        SimpleNamespace(
            name="model",
            path="model.joblib",
            checksum="0" * 64,
            byte_size=1,
            media_type="application/x-joblib",
        ),
    )
    catalog = DeliveryCatalog.__new__(DeliveryCatalog)
    catalog.root = tmp_path
    catalog._authentication_lock = threading.RLock()
    catalog.data = DataRepository()
    catalog.repositories = {
        "factors": Repository(Manifest("factor-123"), table),
        "asset_pricing": Repository(Manifest("pricing-123"), table),
        "portfolio": Repository(Manifest("portfolio-123", artifacts), table),
        "ml": Repository(Manifest("ml-123", artifacts), table),
    }
    assert len(catalog.list()) == 5
    assert len(catalog.list("ml")) == 1
    assert catalog.manifest("data", "data-123")["dataset_id"] == "data-123"
    assert catalog.manifest("factors", "factor-123")["publication_id"] == "factor-123"
    assert catalog.find("factor-123")[0] == "factors"
    with pytest.raises(EvidenceIntegrityError, match="unavailable or ambiguous"):
        catalog.find("missing-123")
    assert catalog.artifact_inventory("data", "data-123")[0]["name"] == "standardized_data"

    factor_manifest = catalog.manifest("factors", "factor-123")
    factor_manifest.update(
        {
            "artifact_checksum": "1" * 64,
            "portfolio_artifact_checksum": "2" * 64,
            "validation_report_checksum": "3" * 64,
            "diagnostics_checksum": "4" * 64,
            "parents": [],
        }
    )
    factor_repo = catalog.repositories["factors"]
    factor_repo.value.model_dump = Mock(return_value=factor_manifest)  # type: ignore[method-assign]
    factor_document = json.dumps({"publication_id": "factor-123"}).encode()
    factor_path = tmp_path / "factor-lineage.json"
    factor_path.write_bytes(factor_document)
    factor_repo.value.lineage_path = "factor-lineage.json"
    factor_repo.value.lineage_checksum = checksum(factor_document)
    factor_repo.value.diagnostics_path = "factor-lineage.json"
    factor_repo.value.diagnostics_checksum = checksum(factor_document)
    assert len(catalog.artifact_inventory("factors", "factor-123")) == 4
    assert catalog.table("data", "data-123", "observations").num_rows == 2
    assert catalog.table("factors", "factor-123", "observations").num_rows == 1
    assert catalog.table("factors", "factor-123", "portfolios").num_rows == 1
    assert catalog.table("asset_pricing", "pricing-123", "coefficients").num_rows == 1
    assert catalog.table("portfolio", "portfolio-123", "observations").num_rows == 1
    assert catalog.document("portfolio", "portfolio-123", "summary")["value"] == 1
    assert catalog.lineage("data", "data-123")["lineage_id"] == "lineage-123"
    assert catalog.lineage("factors", "factor-123")["publication_id"] == "factor-123"
    assert (
        catalog.document("factors", "factor-123", "diagnostics")["publication_id"] == "factor-123"
    )
    assert catalog.artifact_inventory("portfolio", "portfolio-123")[0]["name"] == "summary"
    with pytest.raises(EvidenceIntegrityError, match="not a document"):
        catalog.document("portfolio", "portfolio-123", "observations")
    with pytest.raises(EvidenceIntegrityError, match="not tabular"):
        catalog.table("portfolio", "portfolio-123", "summary")
    with pytest.raises(EvidenceIntegrityError, match="unavailable"):
        catalog.document("ml", "ml-123", "model")
    with pytest.raises(EvidenceIntegrityError, match="Unsupported"):
        catalog.document("factors", "factor-123", "summary")
    json_path.write_text("changed", encoding="utf-8")
    with pytest.raises(EvidenceIntegrityError, match="changed"):
        catalog.document("portfolio", "portfolio-123", "summary")


def test_delivery_service_pagination_without_constructor() -> None:
    service = DeliveryService.__new__(DeliveryService)
    service.catalog = FakeCatalog()  # type: ignore[assignment]
    page = service.publications(None, 0, 1)
    assert page.total == 1
    assert service.publication("factors", "factor-123")["publication_id"] == "factor-123"
    assert service.find_publication("factor-123")["kind"] == "factors"
    table = pa.table({"value": [1, 2, 3]})
    assert service._page(table, 1, 1).items == ({"value": 2},)


class FakeStreamlit:
    def __init__(self) -> None:
        self.messages: list[str] = []
        self.sidebar = self
        self.selection = PAGES[0]
        self.button_value = False

    def __getattr__(self, name: str) -> Any:
        def call(*args: Any, **kwargs: Any) -> Any:
            del kwargs
            self.messages.append(f"{name}:{args[0] if args else ''}")
            if name == "columns":
                return [self, self, self]
            if name == "radio":
                return self.selection
            if name == "selectbox":
                return args[1][0]
            if name == "multiselect":
                return list(args[1])[:1]
            if name == "button":
                return self.button_value
            return None

        return call


class DashboardAPI:
    def __init__(self, items: list[dict[str, Any]] | None = None) -> None:
        self.items = items or []

    def get(self, path: str) -> dict[str, Any]:
        if path == "ready":
            return {
                "status": "ready",
                "authenticated_publications": len(self.items),
                "empty_state": not self.items,
            }
        if path == "governance":
            return {"advisory_status": "NON_ADVISORY_RESEARCH_ONLY"}
        if path == "limitations":
            return {"limitations": ["No live execution"]}
        return {"items": self.items}

    def post_report(self, payload: dict[str, Any]) -> dict[str, str]:
        assert payload["publications"]
        return {"report_id": "report-123"}


def test_dashboard_application_states(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    fake_st = FakeStreamlit()
    monkeypatch.setattr(dashboard_app, "st", fake_st)
    dashboard_app._overview(DashboardAPI())
    assert any("No authenticated" in value for value in fake_st.messages)

    dashboard_app._research_page(DashboardAPI(), "ml")
    assert any("SHAP" in value for value in fake_st.messages)
    item = {
        "kind": "ml",
        "publication_id": "ml-123",
        "schema_version": "1.0.0",
        "validation_status": "PASS",
        "configuration_hash": "a" * 64,
        "git_commit": "abc123",
    }
    dashboard_app._research_page(DashboardAPI([item]), "ml")
    dashboard_app._research_page(DashboardAPI([item]), "risk")
    dashboard_app._reports(DashboardAPI())
    fake_st.button_value = True
    dashboard_app._reports(DashboardAPI([item]))
    assert any("report-123" in value for value in fake_st.messages)

    monkeypatch.setattr(dashboard_app, "load_delivery_config", lambda: delivery_config(tmp_path))
    monkeypatch.setattr(dashboard_app, "DashboardClient", lambda config: DashboardAPI())
    dashboard_app.main()
    fake_st.selection = PAGES[-1]
    dashboard_app.main()


def test_dashboard_launcher(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    entry = tmp_path / "src/institutional_factor_platform/dashboard/app.py"
    entry.parent.mkdir(parents=True)
    entry.write_text("", encoding="utf-8")
    config = delivery_config(tmp_path)
    called = Mock()
    monkeypatch.setattr(dashboard_launcher, "find_project_root", lambda: tmp_path)
    monkeypatch.setattr(dashboard_launcher, "load_delivery_config", lambda path: config)
    monkeypatch.setattr(dashboard_launcher.streamlit_cli, "main", called)
    monkeypatch.delenv("IFP_DELIVERY_CONFIG", raising=False)
    original = list(sys.argv)
    dashboard_launcher.run_dashboard(tmp_path / "config.yaml")
    called.assert_called_once()
    assert sys.argv == original
    assert "IFP_DELIVERY_CONFIG" not in os.environ

    monkeypatch.setenv("IFP_DELIVERY_CONFIG", "existing.yaml")
    monkeypatch.setattr(
        dashboard_launcher,
        "load_delivery_config",
        Mock(side_effect=RuntimeError("invalid configuration")),
    )
    with pytest.raises(RuntimeError, match="invalid configuration"):
        dashboard_launcher.run_dashboard(tmp_path / "missing.yaml")
    assert os.environ["IFP_DELIVERY_CONFIG"] == "existing.yaml"
