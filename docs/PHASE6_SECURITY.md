# Phase 6 Security Model

The delivery platform is local single-owner research software. Controls include loopback binding, explicit non-loopback authorization, optional/required constant-time bearer verification, restrictive CORS, trusted hosts, body and pagination limits, throttling, JSON-only mutations, correlation IDs, security headers, no-store responses, error redaction, and secret-aware logs.

Publication IDs and artifact names use a strict grammar. All research reads pass through existing authentication repositories. The API accepts no filesystem path, SQL, shell command, Python expression, uploaded model, or deserialization request. Reports use internal renderers, escaped HTML, safe filenames, confined output roots, immutable writes, and exact source/output checksum verification.

Tokens are read only from the configured environment variable. Empty configured tokens fail. Tokens, secrets, private keys, model bytes, and raw confidential configuration are not logged or returned. Repository scans cover credentials, keys, private paths, data, models, generated artifacts, binaries, and large files.

This control set is not OAuth, enterprise SSO, a multi-tenant authorization database, a cloud security architecture, or a production SLA.
