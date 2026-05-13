# CoproScope Server

Backend package for the CoproScope product.

This package exposes the `coprocs` CLI and a minimal MCP-compatible stdio server.

Useful publication helpers:

- `coprocs share-audit --repo-root .. --config src/coproscope/configs/github_sharing.default.yml`
- `coprocs share-export --repo-root .. --config src/coproscope/configs/github_sharing.default.yml --output-dir ..\\public-export --clean`
