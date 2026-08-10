# Phase 6 Local Deployment Guide

## Native

```shell
uv sync --all-groups
uv run institutional-factor-platform serve-api
uv run institutional-factor-platform serve-dashboard
```

Both services bind to loopback by default. Set `IFP_API_TOKEN` outside Git to enable bearer protection.

## Docker Compose

Create an untracked `.env` containing a strong `IFP_API_TOKEN`, then run:

```shell
docker compose up --build
```

The image uses a locked multi-stage build and non-root runtime. Compose exposes ports only on host loopback, drops capabilities, enables `no-new-privileges`, uses read-only containers and temporary filesystems, mounts authenticated data read-only, and gives reports a separate writable named volume. It performs no automatic deployment or package publication.

Docker was unavailable on the final audit host. Dockerfile, Compose, ignore rules, commands, users, mounts, security options, and health checks were statically validated, while an actual local image build remains an accurately disclosed external validation item. CI contains the required independent image-build gate.
