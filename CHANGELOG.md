# Changelog

All notable changes to CoproScope will be documented in this file.

CoproScope follows a pragmatic pre-1.0 versioning approach while the public API, CLI and data schemas are still evolving.

## [0.1.0-alpha.1] - 2026-05-13

### Release status

This is the first public alpha release candidate for CoproScope.

It is intended for:

- curious conseil syndical members;
- early technical testers;
- open source contributors;
- syndics or property-management actors interested in structured CS-syndic workflows;
- people who want to test the synthetic corpus without exposing real copropriete data.

It is not yet intended as a turnkey tool for non-technical users.

### Added

- Public repository structure for CoproScope.
- Python package `coproscope` with CLI entry point `coprocs`.
- First local-first documentary pipeline.
- Initial DocOps workflow: inventory, text extraction, classification, completeness and KPI-oriented outputs.
- Initial SyndicOps foundations for demand tracking and evidence chains.
- Initial AGOps foundations for AG preparation signals.
- Minimal MCP server foundations.
- Versioned schemas, configs, prompts and templates.
- Public synthetic copro instance for tests and demonstrations.
- Public/private sharing boundary with `share-audit` and `share-export` tooling.
- Documentation in French describing concept, target functions, implementation plan, development state and GitHub sharing policy.
- MPL-2.0 license for code.

### Changed

- The public positioning now prioritizes conseil syndical users rather than developers only.
- The project vocabulary is being simplified around practical modules: DocuScope, BavardDoc, SyndicOps, AGScope, TravauxScope, PrestaScope and CoproLink.

### Security and privacy

- Real copropriete documents must never be committed to the public repository.
- Sensitive folders, private OCR outputs, generated local reports and real exports are out of scope for the public repository.
- The alpha should only be tested with the synthetic corpus or with local private data kept outside GitHub.

### Known limitations

- Installation and packaging remain early-stage.
- The user experience is still CLI-first.
- The synthetic demonstration corpus needs to become more pedagogical.
- DocOps heuristics need more real-world validation.
- SyndicOps, AGOps, TravauxScope, PrestaScope and CoproLink are not yet complete products.
- Automated tests and release checks need to be strengthened.
- The tool does not provide legal advice and must not be used as a substitute for professional review.

### Suggested tag

`v0.1.0-alpha.1`

### Suggested release title

`CoproScope v0.1.0-alpha.1 — First public alpha for conseil syndical workflows`
