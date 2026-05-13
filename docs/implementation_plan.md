# CoproScope v1 Implementation Plan

This file anchors the implementation plan on disk so the product keeps a durable execution contract outside chat history.

## Summary

- Build CoproScope as a separate product with a local-first backend in `server/`.
- Keep real copropriete data outside the product repository as private instances.
- Deliver a first usable slice around DocOps, SyndicOps bootstrap, and AGOps.

## Architectural Decisions

- Product code, default configs, schemas, prompts, and templates live in `coproscope/server/`.
- Private instances live outside the product repository and provide `instance.yml` mappings.
- A private pilot instance validates the real workflow; `examples/synthetic_copro/` is the public validation instance.
- Generic improvements are prepared for the public repository `https://github.com/bthollet/CoproScope`.
- No destructive migration is allowed. RAW remains read-only. Writes are limited to staging, outputs, and registers.

## v1 Command Surface

- `coprocs doctor`
- `coprocs inventory`
- `coprocs extract-text`
- `coprocs classify`
- `coprocs missing-docs`
- `coprocs kpi`
- `coprocs ag analyze`
- `coprocs due-diligence summarize`
- `coprocs pipeline run`

## v1 Product Scope

- Generic copropriete-simple core with extension points for future multi-entity support.
- Instance-based path mapping and configuration.
- Stable CLI plus a minimal MCP server for safe automation.
- Structured schemas, default configs, prompts, templates, and write logs.

## Explicit Non-Goals For v1

- No web application.
- No SaaS or multi-tenant server deployment.
- No mandatory RAG stack.
- No native recursive multi-entity engine yet.

## Guardrails

- No secrets in Git.
- No real copropriete documents in the product repo.
- No writes in RAW roots.
- All writes to registers and outputs are logged.
