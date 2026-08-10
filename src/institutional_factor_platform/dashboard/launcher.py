"""Streamlit launcher kept outside CLI dispatch logic."""

import os
import sys
from pathlib import Path

from streamlit.web import cli as streamlit_cli

from institutional_factor_platform.delivery.config import load_delivery_config
from institutional_factor_platform.project import find_project_root


def run_dashboard(config_path: Path | None = None) -> None:
    root = find_project_root()
    if config_path:
        os.environ["IFP_DELIVERY_CONFIG"] = str(config_path.resolve())
    config = load_delivery_config(config_path)
    entry = root / "src" / "institutional_factor_platform" / "dashboard" / "app.py"
    original = sys.argv
    try:
        sys.argv = ["streamlit", "run", str(entry), "--server.address", config.api.host]
        streamlit_cli.main()
    finally:
        sys.argv = original
