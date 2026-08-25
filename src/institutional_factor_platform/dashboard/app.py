"""Streamlit entry point for non-advisory authenticated research review."""

from typing import Any

import streamlit as st

from institutional_factor_platform import __version__
from institutional_factor_platform.dashboard.client import DashboardClient
from institutional_factor_platform.dashboard.presentation import (
    EMPTY_STATE,
    PAGES,
    provenance_panel,
    publication_options,
)
from institutional_factor_platform.delivery.config import load_delivery_config
from institutional_factor_platform.ml.config import load_ml_config


def main() -> None:
    config = load_delivery_config()
    client = DashboardClient(config)
    st.set_page_config(page_title="Institutional Research Platform", page_icon="📊", layout="wide")
    st.title("Institutional Multi-Factor Research Platform")
    st.caption(f"Version {__version__} · non-advisory research delivery")
    selected = st.sidebar.radio("Workspace", PAGES, format_func=lambda page: page.title)
    st.header(selected.title)
    st.write(selected.description)
    try:
        if selected.key == "overview":
            _overview(client)
        elif selected.key == "reports":
            _reports(client)
        else:
            _research_page(client, selected.key)
    except Exception as exc:
        st.error(client.safe_error(exc))
    st.divider()
    st.caption("Research outputs are not financial advice or investment recommendations.")


def _overview(client: DashboardClient) -> None:
    ready = client.get("ready")
    governance = client.get("governance")
    limitations = client.get("limitations")
    columns = st.columns(3)
    columns[0].metric("Platform", ready["status"])
    columns[1].metric("Authenticated publications", ready["authenticated_publications"])
    columns[2].metric("Research status", governance["advisory_status"])
    if ready["empty_state"]:
        st.info(EMPTY_STATE)
    st.subheader("Phase status")
    st.write("Phases 1-6 complete; live empirical validation remains evidence-dependent.")
    st.subheader("Limitations")
    for item in limitations["limitations"]:
        st.write(f"- {item}")


def _research_page(client: DashboardClient, key: str) -> None:
    family = {
        "lineage": "publications",
        "factors": "factors/publications",
        "asset_pricing": "asset-pricing/publications",
        "portfolio": "portfolios/publications",
        "risk": "portfolios/publications",
        "ml": "ml/publications",
        "validation": "publications",
    }[key]
    page = client.get(family)
    items = publication_options(page["items"], _preferred_publication_id(key))
    if not items:
        st.info(EMPTY_STATE)
        if key == "ml":
            st.warning("SHAP and feature importance are not causal.")
        return
    labels = [item["publication_id"] for item in items]
    publication_id = st.selectbox("Authenticated publication", labels)
    selected = next(item for item in items if item["publication_id"] == publication_id)
    st.subheader("Provenance")
    st.json(provenance_panel(selected), expanded=True)
    st.warning("Display values retain authenticated source identity and configured units.")
    detail_family = {
        "lineage": "publications",
        "factors": "factors/publications",
        "asset_pricing": "asset-pricing/publications",
        "portfolio": "portfolios/publications",
        "risk": "portfolios/publications",
        "ml": "ml/publications",
        "validation": "publications",
    }[key]
    detail = client.get(f"{detail_family}/{publication_id}")
    st.subheader("Authenticated evidence")
    st.json(detail, expanded=False)
    for title, suffix in _detail_sections(key):
        st.subheader(title)
        st.json(client.get(f"{detail_family}/{publication_id}/{suffix}"), expanded=False)
    if key == "ml":
        st.warning("SHAP and feature importance are not causal.")


def _reports(client: DashboardClient) -> None:
    page = client.get("publications")
    items = page["items"]
    if not items:
        st.info(EMPTY_STATE)
        return
    options = {f"{item['kind']}: {item['publication_id']}": item for item in items}
    selected = st.multiselect("Authenticated publications", sorted(options))
    format_name = st.selectbox("Format", ("markdown", "html", "json", "csv"))
    if st.button("Generate deterministic report", disabled=not selected):
        references = [
            {"kind": options[label]["kind"], "publication_id": options[label]["publication_id"]}
            for label in selected
        ]
        result: Any = client.post_report({"publications": references, "format": format_name})
        st.success(f"Authenticated report created: {result['report_id']}")


def _detail_sections(key: str) -> tuple[tuple[str, str], ...]:
    return {
        "lineage": (("Connected lineage", "lineage"),),
        "factors": (
            ("Definitions and rationale", "definitions"),
            ("Diagnostics", "diagnostics"),
            ("Observations", "observations?limit=250"),
        ),
        "asset_pricing": (
            ("Coefficients and inference", "coefficients?limit=250"),
            ("Model comparison", "comparisons?limit=250"),
            ("Diagnostics", "diagnostics"),
        ),
        "portfolio": (
            ("Weights", "weights?limit=250"),
            ("Performance", "performance"),
            ("Transaction costs", "costs?limit=250"),
        ),
        "risk": (
            ("Risk measures", "risk"),
            ("Scenario analysis", "scenarios"),
        ),
        "ml": (
            ("Model card", "model-card"),
            ("Evaluation", "evaluation"),
            ("Explanations", "explanations?limit=250"),
            ("Drift", "drift?limit=250"),
            ("Economic evaluation", "economic-evaluation"),
        ),
        "validation": (("Verification", "verify"),),
    }[key]


def _preferred_publication_id(key: str) -> str | None:
    inputs = load_ml_config().inputs
    return {
        "factors": inputs.phase2_publication_id,
        "asset_pricing": inputs.phase3_publication_id,
        "portfolio": inputs.phase4_publication_id,
        "risk": inputs.phase4_publication_id,
    }.get(key)


if __name__ == "__main__":
    main()
