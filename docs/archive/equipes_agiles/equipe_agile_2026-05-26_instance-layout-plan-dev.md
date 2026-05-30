# Equipe agile - instance layout plan

Date: 2026-05-26.

## BOT-START - owner code CLI/layout dry-run - 2026-05-26 00:03 +02:00

Roadmap: `RM-2026-0022` / `RM-2026-0025` / `RM-2026-0006`.
Chantier: `CH-20260526-000300-RM-2026-0022-instance-layout-plan`.
Conversation: `CONV-2026-1785`.
Role: owner code unique CLI/layout dry-run `ORD-P1-050`.
Mission: livrer `coprocs instance layout plan`, un plan JSON non destructif pour une arborescence d'instance lisible par un novice.
Ownership modifiable: `server/src/coproscope/modules/instance_layout.py`, `server/src/coproscope/_cli_parts/01_imports_and_parser.py`, `server/src/coproscope/_cli_parts/02_dispatch.py`, `server/tests/test_instance_layout_plan.py`, cette trace, `docs/presence_agents.md`, `docs/roadmap_backlog_central.md`.
Fichiers evites: instances privees, documents bruts, OCR/logs, exports bruts, secrets, migrations appliquees, deplacements/suppressions, serveurs non reserves, scans/kills, push GitHub, `RM-2026-0017`, `ORD-P0-990`.
Dernier point lu: `docs/presence_agents.md` 2026-05-26 00:03 +02:00, `docs/roadmap_backlog_central.md` entree `START_AGILE_INSTANCE_LAYOUT_PLAN_DEV`.
Tests/preuves attendus: unittest dedie, garde-fou anti-fuite, line-limit, diff-check.
Risque de collision: faible, owner unique deja declare; repo principal tres sale par lots precedents, donc aucun revert.
Lease ownership: 2026-05-26 02:03 +02:00.
Prochaine action: completer le plan dry-run et fermer le lot si les preuves passent.

## Livraison

La commande `coprocs instance layout plan` affiche un JSON de planification seulement. Elle ne cree aucun dossier, ne deplace aucun fichier et ne lit pas les sources de l'instance. Les chemins affiches sont relatifs a la racine de l'instance.

Le plan expose:

- un statut `planned`, `dry_run: true`, `will_modify_files: false`;
- les dossiers visibles recommandes pour le depot novice, les documents classes, les rapports et les points a verifier;
- une zone technique resumee sous `.coproscope/`, sans lister de chemins `raw`, `restricted`, `logs` ou `private` dans la sortie publique;
- les reglages `settings.layout` recommandes;
- les garde-fous de migration: sauvegarde verifiee, manifeste `doc_id` plus `sha256`, rollback et confirmation humaine explicite.

## Preuves

- `.\.venv\Scripts\python.exe -m unittest tests.test_instance_layout_plan -v` depuis `server/`: 3 tests OK.
- `.\.venv\Scripts\python.exe -m unittest tests.test_instance_layout_plan tests.test_security_no_private_sync_leaks -v` depuis `server/`: 11 tests OK.
- `.\server\.venv\Scripts\python.exe .\tools\check_code_line_limit.py` depuis la racine: OK.
- `git diff --check -- ...` sur les fichiers du lot: OK, avec avertissements CRLF preexistants sur les fragments CLI.
- La suite dediee verifie que la commande CLI retourne du JSON, que les chemins sont relatifs, que la racine locale et les marqueurs sensibles ne sortent pas, et qu'aucun dossier planifie n'est cree.

## BOT-END - owner code CLI/layout dry-run - 2026-05-26 00:07 +02:00

Roadmap: `RM-2026-0022` / `RM-2026-0025` / `RM-2026-0006`.
Chantier: `CH-20260526-000300-RM-2026-0022-instance-layout-plan`.
Conversation: `CONV-2026-1785`.
Statut: `INTEGRE`.
Fichiers modifies: `server/src/coproscope/modules/instance_layout.py`, `server/src/coproscope/_cli_parts/01_imports_and_parser.py`, `server/src/coproscope/_cli_parts/02_dispatch.py`, `server/tests/test_instance_layout_plan.py`, `docs/equipe_agile_2026-05-26_instance-layout-plan-dev.md`, `docs/presence_agents.md`, `docs/roadmap_backlog_central.md`.
Fichiers volontairement evites: instances privees, documents bruts, OCR/logs, exports bruts, secrets, migrations appliquees, deplacements/suppressions, serveurs non reserves, scans/kills, push GitHub, `RM-2026-0017`, `ORD-P0-990`.
Tests/preuves: unittest dedie 3 OK; panier layout + no-private 11 OK; line-limit OK; diff-check OK avec avertissements CRLF preexistants sur les fragments CLI.
Limites: pas de commande appliquee; migration reelle volontairement hors lot et devra exiger sauvegarde, manifeste, rollback et confirmation humaine.
Questions ouvertes: definir plus tard une commande appliquee si Brice valide explicitement la migration d'une instance.
Prochain mouvement propose: continuer le backlog autonome, hors blocage manuel `CONV-2026-1772` sur serveur visible `8788`.

AGILE-DONE - equipe agile a fini son job
