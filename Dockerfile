FROM ghcr.io/astral-sh/uv:0.8.14-python3.13-bookworm-slim AS builder
WORKDIR /app
ENV UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy
COPY pyproject.toml uv.lock LICENSE README.md ./
COPY src ./src
RUN uv sync --frozen --no-dev

FROM python:3.13.7-slim-bookworm AS runtime
RUN groupadd --system platform && useradd --system --gid platform --home-dir /app platform
WORKDIR /app
COPY --from=builder --chown=platform:platform /app /app
COPY --chown=platform:platform config ./config
COPY --chown=platform:platform data/README.md ./data/README.md
ENV PATH="/app/.venv/bin:$PATH" PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1
USER platform
EXPOSE 8000 8501
HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/api/v1/health', timeout=3)"
CMD ["institutional-factor-platform", "serve-api"]
