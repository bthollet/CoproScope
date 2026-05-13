# CoproScope Server

Paquet backend du produit CoproScope.

Ce paquet expose:

- la CLI `coprocs` ;
- un serveur MCP minimal compatible stdio ;
- le socle de schemas, configurations, prompts et templates.

## Aides utiles pour publier proprement

- `coprocs share-audit --repo-root .. --config src/coproscope/configs/github_sharing.default.yml`
- `coprocs share-export --repo-root .. --config src/coproscope/configs/github_sharing.default.yml --output-dir ..\\public-export --clean`
