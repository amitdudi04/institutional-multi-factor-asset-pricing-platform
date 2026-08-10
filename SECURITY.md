# Security Policy

Report suspected vulnerabilities privately to the repository owner through an established private channel. Include the affected version, reproduction conditions, impact, and suggested mitigation; do not include live credentials, proprietary data, or destructive proof-of-concept material.

The supported baseline is the latest tagged release. The application is designed for local single-owner research use. Keep services on loopback unless explicitly configured, use a strong environment-supplied bearer token for container/non-loopback access, do not expose report/data volumes publicly, and never load untrusted Joblib/Pickle artifacts.

No credential belongs in an issue, commit, YAML configuration, Docker image, report, or log.
