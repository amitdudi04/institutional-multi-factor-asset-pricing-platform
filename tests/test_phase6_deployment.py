from pathlib import Path

import yaml


def test_docker_security_foundation() -> None:
    dockerfile = Path("Dockerfile").read_text(encoding="utf-8")
    assert " AS builder" in dockerfile
    assert "USER platform" in dockerfile
    assert "HEALTHCHECK" in dockerfile
    assert "uv sync --frozen --no-dev" in dockerfile
    assert "COPY . " not in dockerfile
    assert "COPY data " not in dockerfile
    assert "latest" not in dockerfile

    ignored = Path(".dockerignore").read_text(encoding="utf-8")
    for value in (".git", ".env", "data/**", "*.parquet", "*.joblib", "tests"):
        assert value in ignored


def test_compose_services_and_boundaries() -> None:
    compose = yaml.safe_load(Path("docker-compose.yml").read_text(encoding="utf-8"))
    services = compose["services"]
    assert set(services) == {"api", "dashboard"}
    for service in services.values():
        assert service["read_only"] is True
        assert service["security_opt"] == ["no-new-privileges:true"]
        assert service["cap_drop"] == ["ALL"]
        assert "./data:/app/data:ro" in service["volumes"]
        assert "delivery-output:/app/data/delivery" in service["volumes"]
    assert services["api"]["ports"] == ["127.0.0.1:8000:8000"]
    assert services["dashboard"]["ports"] == ["127.0.0.1:8501:8501"]
    assert services["api"]["healthcheck"]


def test_ci_has_required_read_only_gates() -> None:
    workflow = yaml.safe_load(Path(".github/workflows/quality.yml").read_text(encoding="utf-8"))
    assert workflow["permissions"] == {"contents": "read"}
    assert set(workflow["jobs"]) == {"validate", "docker"}
    commands = "\n".join(
        step.get("run", "") for step in workflow["jobs"]["validate"]["steps"]
    )
    for gate in (
        "uv sync --frozen --all-groups",
        "uv lock --check",
        "pytest",
        "coverage report --fail-under=90",
        "ruff check",
        "ruff format --check",
        "mypy src",
        "validate-delivery-config",
        "verify-delivery-platform",
        "pip-audit --path",
    ):
        assert gate in commands
    docker_step = workflow["jobs"]["docker"]["steps"][-1]
    assert docker_step["with"]["push"] is False
