"""Subprocess helper for abrupt Phase 1 publication termination tests."""

import os
import sys
from pathlib import Path

from test_service_cli_calendar import SyntheticMacroAdapter, _temp_config

from institutional_factor_platform.data.contracts import MACRO_OBSERVATIONS
from institutional_factor_platform.data.domain import DataSource, RetrievalRequest
from institutional_factor_platform.data.services import DataIngestionService


def main() -> None:
    root = Path(sys.argv[1])
    boundary = sys.argv[2]

    def terminate(name: str) -> None:
        if name == boundary:
            os._exit(91)

    service = DataIngestionService(_temp_config(root), root=root, failure_hook=terminate)
    service.ingest(
        SyntheticMacroAdapter(),
        RetrievalRequest(DataSource.OWNER_SUPPLIED, "synthetic_macro"),
        MACRO_OBSERVATIONS,
        "txt",
        "text/plain",
    )


if __name__ == "__main__":
    main()
