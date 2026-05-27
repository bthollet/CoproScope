# Equipe agile - IncidentOps signalements

Date: 2026-05-26.

## BOT-START - owner code IncidentOps - 2026-05-26 00:15 +02:00

Roadmap: `RM-2026-0034` / `RM-2026-0031` / `RM-2026-0006`.
Chantier: `CH-20260526-001500-RM-2026-0034-incidentops-signalements`.
Conversation: `CONV-2026-1787`.
Role: owner code unique front/back/viewmodel `ORD-P1-070`.
Mission: livrer `/incidents` pour signaler, qualifier et suivre un incident/sinistre jusqu'a preuve de cloture.
Ownership modifiable: route/viewmodel/template/CSS/tests IncidentOps declares, presence, roadmap et cette trace.
Fichiers evites: instances privees, documents bruts, OCR/logs, exports bruts, secrets, assurance reelle, photos originales, envoi/declaration automatique, serveurs non reserves, scans/kills, push GitHub, `RM-2026-0017`, `ORD-P0-990`.
Dernier point lu: `CONV-2026-1786` integre a 00:11 +02:00; `CONV-2026-1772` reste bloque par recharge manuelle `8788`.
Tests/preuves attendus: test UI dedie, smoke/security/no-private, langue/accessibilite si pertinent, line-limit, diff-check.
Risque de collision: moyen sur `base.html`, `feature_routes.py` et `styles.css`; owner unique declare dans la ligne de presence.
Lease ownership: 2026-05-26 02:15 +02:00.
Prochaine action: lire les patterns routes recentes, ajouter la route et ses tests sans serveur live.

## Livraison

La route `/incidents` est tokenisee et affiche une file IncidentOps lisible par un membre CS novice: incidents ouverts, qualification, assurance a verifier, preuve de cloture attendue, diffusion et prochaines actions. La vue utilise le registre local s'il existe et bascule sur des exemples `FICTIF` sinon. Les chemins locaux et references de sources brutes ne sont pas affiches.

Actions sensibles bloquees: declaration assurance, partage aux coproprietaires et cloture sans preuve. Aucun serveur live n'a ete lance.

## Preuves

- `.\.venv\Scripts\python.exe -m unittest tests.test_ui_incidentops tests.test_ui_smoke_routes_expanded tests.test_ui_security_routes tests.test_security_no_private_sync_leaks -v` depuis `server/`: 22 tests OK.
- `.\.venv\Scripts\python.exe -m unittest tests.test_ui_accessibility_language tests.test_ui_no_jargon_primary tests.test_ui_novice_language_static -v` depuis `server/`: 15 tests OK.
- `.\server\.venv\Scripts\python.exe .\tools\check_code_line_limit.py` depuis la racine: OK.
- `git diff --check -- ...` sur les fichiers du lot: OK avec avertissement CRLF preexistant sur `styles.css`.

## BOT-END - owner code IncidentOps - 2026-05-26 00:24 +02:00

Roadmap: `RM-2026-0034` / `RM-2026-0031` / `RM-2026-0006`.
Chantier: `CH-20260526-001500-RM-2026-0034-incidentops-signalements`.
Conversation: `CONV-2026-1787`.
Statut: `INTEGRE`.
Fichiers modifies: `server/src/coproscope/web/incidentops_view.py`, `server/src/coproscope/web/templates/incidents.html`, `server/src/coproscope/web/templates/base.html`, `server/src/coproscope/web/feature_routes.py`, `server/src/coproscope/web/static/styles.css`, `server/src/coproscope/web/static/styles_part_22.css`, `server/tests/test_ui_incidentops.py`, `server/tests/test_ui_smoke_routes_expanded.py`, `server/tests/test_ui_security_routes.py`, `server/tests/test_security_no_private_sync_leaks.py`, `docs/equipe_agile_2026-05-26_incidentops-signalements-dev.md`, `docs/presence_agents.md`, `docs/roadmap_backlog_central.md`.
Fichiers volontairement evites: instances privees, documents bruts, OCR/logs, exports bruts, secrets, assurance reelle, photos originales, envoi/declaration automatique, serveurs non reserves, scans/kills, push GitHub, `RM-2026-0017`, `ORD-P0-990`.
Tests/preuves: IncidentOps/smoke/security/no-private 22 OK; langue/accessibilite 15 OK; line-limit OK; diff-check OK avec avertissement CRLF preexistant sur `styles.css`.
Limites: pas de recette navigateur live/captures sans serveur reserve.
Questions ouvertes: raccorder plus tard des actions detaillees si ContractOps ou demandes avancees le necessitent.
Prochain mouvement propose: continuer le backlog autonome, hors blocage manuel `CONV-2026-1772` sur serveur visible `8788`.

AGILE-DONE - equipe agile a fini son job

## Livraison

La route `/incidents` est livree avec un viewmodel dedie IncidentOps, un template et un CSS responsive. La page affiche des signalements/sinistres sur exemples FICTIFS si aucun registre local n'existe, et sait aussi transformer un registre local en synthese derivee sans afficher chemins, sources brutes ou photos originales. Les cartes gardent date, lieu, statut, urgence, assurance a verifier, preuve de cloture attendue, prochaine action, echeance et diffusion `CS seulement`.

Actions disponibles: ouvrir les actions incidents, ajouter une preuve locale, voir les pieces sinistres. Actions bloquees: declaration assurance, partage coproprietaires, cloture sans preuve. Aucun envoi, declaration, serveur live ou lecture d'instance privee.

## Preuves

- `.\.venv\Scripts\python.exe -m unittest tests.test_incidentops tests.test_ui_incidentops -v` depuis `server/`: 9 tests OK.
- `.\.venv\Scripts\python.exe -m unittest tests.test_ui_smoke_routes_expanded tests.test_ui_security_routes tests.test_security_no_private_sync_leaks tests.test_ui_accessibility_language tests.test_ui_no_jargon_primary tests.test_ui_novice_language_static -v` depuis `server/`: 32 tests OK.
- `.\server\.venv\Scripts\python.exe .\tools\check_code_line_limit.py` depuis la racine: OK.
- `git diff --check -- ...` sur les fichiers du lot: OK, avec warning CRLF preexistant sur `server/src/coproscope/web/static/styles.css`.

## BOT-END - owner code IncidentOps - 2026-05-26 00:24 +02:00

Roadmap: `RM-2026-0034` / `RM-2026-0031` / `RM-2026-0006`.
Chantier: `CH-20260526-001500-RM-2026-0034-incidentops-signalements`.
Conversation: `CONV-2026-1787`.
Statut: `INTEGRE`.
Fichiers modifies: `server/src/coproscope/web/incidentops_view.py`, `server/src/coproscope/web/templates/incidents.html`, `server/src/coproscope/web/templates/base.html`, `server/src/coproscope/web/feature_routes.py`, `server/src/coproscope/web/static/styles.css`, `server/src/coproscope/web/static/styles_part_22.css`, `server/tests/test_ui_incidentops.py`, `server/tests/test_ui_smoke_routes_expanded.py`, `server/tests/test_ui_security_routes.py`, `server/tests/test_security_no_private_sync_leaks.py`, `docs/equipe_agile_2026-05-26_incidentops-signalements-dev.md`, `docs/presence_agents.md`, `docs/roadmap_backlog_central.md`.
Fichiers volontairement evites: instances privees, documents bruts, OCR/logs, exports bruts, secrets, assurance reelle, photos originales, envoi/declaration automatique, serveurs non reserves, scans/kills, push GitHub, `RM-2026-0017`, `ORD-P0-990`.
Tests/preuves: IncidentOps 5 OK; smoke/security/no-private 17 OK; langue/accessibilite 15 OK; line-limit OK; diff-check OK avec warning CRLF `styles.css`.
Limites: pas de recette navigateur live/captures car aucun serveur visible reserve n'a ete ouvert; la route affiche une synthese derivee et ne declare rien a l'assurance.
Questions ouvertes: aucune pour ce lot borne.
Prochain mouvement propose: continuer le backlog autonome sur `ORD-P1-080` ContractOps si aucun owner vivant plus recent n'est declare.

AGILE-DONE - equipe agile a fini son job
