# GitHub Sharing Policy

Public product repository: [bthollet/CoproScope](https://github.com/bthollet/CoproScope)

## Goal

Make it easy to upstream generic improvements from private copropriete work into the public CoproScope codebase without leaking data, secrets, or private documents.

## What can be shared

- product code under `server/`
- public docs under `docs/`
- schemas, configs, prompts, templates
- tests
- synthetic examples under `examples/synthetic_copro/`
- bug fixes, CLI improvements, MCP improvements, generic heuristics

## What must never be shared

- `coproscope-instances/`
- real copropriete files
- OCR/text exports from real private files
- raw manifests that expose private paths
- `.env.local`, tokens, API keys, secret file paths
- nominative, banking, litigation, or impayes data

## Upstream workflow

1. Implement or validate the improvement locally on a private instance.
2. Strip any private-instance-specific path, wording, identifier, or data dependency.
3. Move the reusable part into `coproscope/server/`, `coproscope/docs/`, or `coproscope/examples/synthetic_copro/`.
4. Add or update tests.
5. Check the share manifest and the public/private boundary.
6. Open an issue or PR on the public repository.

## Required review questions before sharing

- Is the change generic?
- Does it contain any real path, file name, person, lot, bank, or litigation detail?
- Can the behavior be demonstrated using the synthetic example only?
- Are secrets and environment expectations documented via `.env.example` only?

## Recommended PR shape

- one generic behavior change at a time
- include validation steps
- mention whether the change came from a private pilot instance
- describe the redaction/generalization work that was done before sharing
