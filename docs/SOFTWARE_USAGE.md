# Software Usage

## Install

```shell
uv sync --all-groups
```

## Configuration Checks

```shell
uv run institutional-factor-platform validate-config
uv run institutional-factor-platform validate-delivery-config
```

Credentials required by a provider are supplied through environment variables. Live credential values should not be committed.

## Research Data and Factors

The command-line interface contains the ingestion, validation, factor, asset-pricing, portfolio, ML and delivery commands used by the project. Run:

```shell
uv run institutional-factor-platform --help
```

for the current command inventory and required arguments.

Empirical input files are expected to remain in the local ignored data paths described by the configuration.

## Verify the Delivery Layer

```shell
uv run institutional-factor-platform verify-delivery-platform
```

## API

Start the research API:

```shell
uv run institutional-factor-platform serve-api
```

By default it is served locally under `127.0.0.1:8000` with the `/api/v1` prefix.

The API provides research-result discovery, factor/model/portfolio/ML output access, lineage metadata and report generation. It does not provide brokerage or live trading endpoints.

## Dashboard

Start the Streamlit dashboard:

```shell
uv run institutional-factor-platform serve-dashboard
```

The dashboard is a presentation layer over the stored research results. It does not create substitute empirical results when no valid result is available.

## Reports

The project supports research reports in Markdown, HTML, JSON and CSV-metadata formats through the reporting service.

## Docker

The repository includes a Dockerfile and Compose configuration for local API/dashboard execution. Docker support is an operational convenience; it is not part of the empirical evidence.

## Tests

```shell
uv run pytest
uv run coverage report --fail-under=90
uv run ruff check .
uv run ruff format --check .
uv run mypy src
```

Tests cover finance calculations, temporal separation, data contracts, portfolio accounting, transaction costs, ML splits, API/dashboard behavior and recovery/integrity logic.
