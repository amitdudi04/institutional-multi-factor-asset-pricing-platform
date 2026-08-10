"""FastAPI application exposing authenticated Phase 1-5 research evidence."""

from datetime import UTC, datetime
from typing import Annotated, Any

from fastapi import FastAPI, Path, Query, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, Response
from pydantic import ValidationError
from starlette.middleware.trustedhost import TrustedHostMiddleware

from institutional_factor_platform import __version__
from institutional_factor_platform.delivery.config import DeliveryConfig, load_delivery_config
from institutional_factor_platform.delivery.schemas import PublicationKind, ReportRequest
from institutional_factor_platform.delivery.service import DeliveryService
from institutional_factor_platform.exceptions import PlatformError
from institutional_factor_platform.observability.metrics import OperationalMetrics

from .middleware import RequestPolicy

Identifier = Annotated[str, Path(pattern=r"^[A-Za-z0-9][A-Za-z0-9._-]{2,127}$")]

LIMITATIONS = (
    "Research outputs are not financial advice or investment recommendations.",
    "Live empirical validation may remain pending.",
    "SHAP and feature importance are not causal.",
    "Local bearer protection is not multi-tenant enterprise identity management.",
    "No brokerage, live execution, or automatic model retraining exists.",
)


def create_app(
    config: DeliveryConfig | None = None, service: DeliveryService | None = None
) -> FastAPI:
    settings = config or load_delivery_config()
    settings.api.validate_binding()
    if settings.api.authentication == "required" and settings.api.token() is None:
        raise ValueError("Required bearer authentication has no configured token")
    delivery = service or DeliveryService(settings)
    metrics = OperationalMetrics()
    app = FastAPI(
        title="Institutional Research Delivery API",
        version=__version__,
        docs_url=None,
        redoc_url=None,
        openapi_url=f"{settings.api.prefix}/openapi.json",
    )
    app.state.delivery = delivery
    app.state.settings = settings
    app.state.metrics = metrics
    app.add_middleware(TrustedHostMiddleware, allowed_hosts=list(settings.api.trusted_hosts))
    app.add_middleware(
        CORSMiddleware,
        allow_origins=list(settings.api.allowed_origins),
        allow_credentials=False,
        allow_methods=["GET", "POST"],
        allow_headers=["authorization", "content-type", "x-correlation-id"],
    )
    policy = RequestPolicy(settings.api, metrics)
    app.middleware("http")(policy)

    @app.exception_handler(PlatformError)
    async def platform_error(request: Request, exc: PlatformError) -> JSONResponse:
        del exc
        return _error(request, 422, "evidence_unavailable", "Authenticated evidence is unavailable")

    @app.exception_handler(ValidationError)
    async def validation_error(request: Request, exc: ValidationError) -> JSONResponse:
        del exc
        return _error(request, 422, "invalid_request", "Request validation failed")

    @app.exception_handler(RequestValidationError)
    async def request_validation_error(
        request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        del exc
        return _error(request, 422, "invalid_request", "Request validation failed")

    prefix = settings.api.prefix

    @app.get(f"{prefix}/health")
    def health() -> dict[str, Any]:
        return {"status": "healthy", "version": __version__, "timestamp": _now()}

    @app.get(f"{prefix}/ready")
    def ready() -> dict[str, Any]:
        settings.api.validate_binding()
        delivery.root.stat()
        publications = delivery.catalog.list()
        return {
            "status": "ready",
            "authenticated_publications": len(publications),
            "empty_state": not publications,
            "timestamp": _now(),
        }

    @app.get(f"{prefix}/version")
    def version() -> dict[str, Any]:
        return {"version": __version__, "api_version": "v1", "timestamp": _now()}

    @app.get(f"{prefix}/governance")
    def governance() -> dict[str, Any]:
        return {
            "purpose": "Authenticated institutional quantitative research delivery",
            "advisory_status": "NON_ADVISORY_RESEARCH_ONLY",
            "phases": (1, 2, 3, 4, 5, 6),
            "timestamp": _now(),
        }

    @app.get(f"{prefix}/limitations")
    def limitations() -> dict[str, Any]:
        return {"limitations": LIMITATIONS, "timestamp": _now()}

    def paged(kind: PublicationKind | None, offset: int, limit: int) -> dict[str, Any]:
        return delivery.publications(kind, offset, limit).model_dump(mode="json")

    @app.get(f"{prefix}/publications")
    def publications(
        kind: PublicationKind | None = None,
        offset: int = Query(0, ge=0),
        limit: int = Query(settings.api.default_page_size, ge=1, le=settings.api.maximum_page_size),
    ) -> dict[str, Any]:
        return paged(kind, offset, limit)

    @app.get(f"{prefix}/publications/{{publication_id}}")
    def publication(publication_id: Identifier) -> dict[str, Any]:
        return delivery.find_publication(publication_id)

    @app.get(f"{prefix}/publications/{{publication_id}}/verify")
    def verify_publication(publication_id: Identifier) -> dict[str, Any]:
        value = delivery.find_publication(publication_id)
        return {"publication_id": publication_id, "authenticated": True, "kind": value["kind"]}

    @app.get(f"{prefix}/publications/{{publication_id}}/lineage")
    def publication_lineage(publication_id: Identifier) -> Any:
        kind, _ = delivery.catalog.find(publication_id)
        return delivery.catalog.lineage(kind, publication_id)

    @app.get(f"{prefix}/publications/{{publication_id}}/artifacts")
    def publication_artifacts(publication_id: Identifier) -> Any:
        kind, _ = delivery.catalog.find(publication_id)
        return delivery.catalog.artifact_inventory(kind, publication_id)

    family_paths: dict[str, PublicationKind] = {
        "data": "data",
        "factors": "factors",
        "asset-pricing": "asset_pricing",
        "portfolios": "portfolio",
        "ml": "ml",
    }
    for family, kind in family_paths.items():
        _add_family_routes(app, prefix, family, kind, delivery, settings.api)

    @app.post(f"{prefix}/reports", status_code=201)
    def create_report(request: ReportRequest) -> dict[str, Any]:
        if not settings.features.reports:
            return {"status": "disabled"}
        metrics.increment("reports")
        return delivery.create_report(request).model_dump(mode="json")

    @app.get(f"{prefix}/reports/{{report_id}}")
    def get_report(report_id: Identifier) -> Response:
        record = delivery.reports.verify(report_id)
        media = {
            "markdown": "text/markdown",
            "html": "text/html",
            "json": "application/json",
            "csv": "text/csv",
        }[record.format]
        return Response(delivery.reports.read(report_id), media_type=media)

    @app.get(f"{prefix}/reports/{{report_id}}/manifest")
    def get_report_manifest(report_id: Identifier) -> dict[str, Any]:
        return delivery.reports.manifest(report_id)

    return app


def _add_family_routes(
    app: FastAPI,
    prefix: str,
    family: str,
    kind: PublicationKind,
    delivery: DeliveryService,
    api: Any,
) -> None:
    base = f"{prefix}/{family}/publications"

    async def listing(
        offset: int = Query(0, ge=0),
        limit: int = Query(api.default_page_size, ge=1, le=api.maximum_page_size),
    ) -> dict[str, Any]:
        return delivery.publications(kind, offset, limit).model_dump(mode="json")

    async def detail(publication_id: Identifier) -> dict[str, Any]:
        return delivery.publication(kind, publication_id)

    app.add_api_route(base, listing, methods=["GET"], name=f"list_{family}")
    app.add_api_route(f"{base}/{{publication_id}}", detail, methods=["GET"], name=f"get_{family}")

    artifact_routes = {
        "factors": {
            "definitions": ("document", "manifest"),
            "diagnostics": ("document", "diagnostics"),
            "observations": ("table", "observations"),
        },
        "asset-pricing": {
            "models": ("table", "model_comparison"),
            "coefficients": ("table", "coefficients"),
            "diagnostics": ("document", "diagnostics"),
            "comparisons": ("table", "model_comparison"),
        },
        "portfolios": {
            "weights": ("table", "allocations"),
            "performance": ("document", "performance_summary"),
            "risk": ("document", "risk_summary"),
            "scenarios": ("document", "scenario_report"),
            "costs": ("table", "transactions"),
        },
        "ml": {
            "model-card": ("document", "model_card"),
            "predictions": ("table", "predictions"),
            "evaluation": ("document", "evaluation"),
            "explanations": ("table", "explanations"),
            "drift": ("table", "drift"),
            "economic-evaluation": ("document", "economic_evaluation"),
        },
    }
    for suffix, (mode, artifact) in artifact_routes.get(family, {}).items():
        route = _artifact_endpoint(delivery, kind, mode, artifact, api)
        app.add_api_route(
            f"{base}/{{publication_id}}/{suffix}",
            route,
            methods=["GET"],
            name=f"{family}_{suffix}",
        )


def _artifact_endpoint(
    delivery: DeliveryService,
    kind: PublicationKind,
    mode: str,
    artifact: str,
    api: Any,
) -> Any:
    async def endpoint(
        publication_id: Identifier,
        offset: int = Query(0, ge=0),
        limit: int = Query(api.default_page_size, ge=1, le=api.maximum_page_size),
    ) -> Any:
        if mode == "table":
            return delivery.table_page(kind, publication_id, artifact, offset, limit).model_dump(
                mode="json"
            )
        if artifact == "manifest" and kind == "factors":
            return delivery.publication(kind, publication_id)["metadata"]
        return delivery.catalog.document(kind, publication_id, artifact)

    return endpoint


def _error(request: Request, status: int, code: str, message: str) -> JSONResponse:
    return JSONResponse(
        status_code=status,
        content={
            "error": {"code": code, "message": message},
            "correlation_id": request.headers.get("x-correlation-id"),
        },
    )


def _now() -> str:
    return datetime.now(UTC).isoformat()


app = create_app()
