"""Pure, testable dashboard formatting and provenance preparation."""

from dataclasses import dataclass
from datetime import date, datetime
from typing import Any

import pandas as pd
import plotly.express as px
from plotly.graph_objects import Figure


@dataclass(frozen=True, slots=True)
class PageDefinition:
    key: str
    title: str
    description: str


PAGES = (
    PageDefinition("overview", "Platform Overview", "Validated platform status and capabilities."),
    PageDefinition("lineage", "Data and Lineage Explorer", "Authenticated evidence connections."),
    PageDefinition("factors", "Factor Research", "Definitions, coverage, and diagnostics."),
    PageDefinition("asset_pricing", "Asset-Pricing Research", "Models and statistical estimates."),
    PageDefinition("portfolio", "Portfolio Construction", "Constraints, weights, and accounting."),
    PageDefinition("risk", "Risk Analytics", "Risk measures and scenario evidence."),
    PageDefinition("ml", "Machine Learning", "Model cards, explanations, and drift."),
    PageDefinition("validation", "Validation and Audit", "Quality gates and assurance evidence."),
    PageDefinition("reports", "Report Builder", "Deterministic authenticated research reports."),
)

EMPTY_STATE = (
    "No authenticated empirical publication is currently available. "
    "Create and promote evidence through the governed Phase 1-5 workflows; no synthetic result "
    "is displayed by the live application."
)


def format_value(value: Any, unit: str | None = None) -> str:
    if value is None:
        return "Unavailable"
    if isinstance(value, float):
        rendered = f"{value:,.4f}"
    elif isinstance(value, (date, datetime)):
        rendered = value.isoformat()
    else:
        rendered = str(value)
    return f"{rendered} {unit}" if unit else rendered


def provenance_panel(manifest: dict[str, Any]) -> dict[str, str]:
    return {
        "Publication": str(manifest.get("publication_id", "Unavailable")),
        "Schema": str(manifest.get("schema_version", "Unavailable")),
        "Validation": str(manifest.get("validation_status", "Unavailable")),
        "Configuration": str(manifest.get("configuration_hash", "Unavailable")),
        "Git commit": str(manifest.get("git_commit", "Unavailable")),
    }


def chart_from_page(
    records: list[dict[str, Any]], x: str, y: str, maximum_rows: int, unit: str | None = None
) -> Figure | None:
    if not records:
        return None
    frame = pd.DataFrame(records[:maximum_rows])
    if x not in frame or y not in frame:
        return None
    figure = px.line(frame, x=x, y=y, labels={x: x.replace("_", " "), y: unit or y})
    figure.update_layout(template="plotly_white")
    return figure
