# Equipe agile - indicateurs pilotage

Date: 2026-05-26.

## BOT-START - owner integration/tests pilotage - 2026-05-26 00:10 +02:00

Roadmap: `RM-2026-0036` / `RM-2026-0003` / `RM-2026-0006`.
Chantier: `CH-20260526-001000-RM-2026-0036-indicateurs-pilotage`.
Conversation: `CONV-2026-1786`.
Role: owner integration/tests pilotage actionnable `ORD-P1-060`.
Mission: fermer la route `/pilotage` en indicateurs actionnables: periode, source, preuve, seuil, confiance et prochaine action lisibles.
Ownership modifiable: tests pilotage/indicatorops/pilotageops, `pilotage_view.py`, `pilotage.html`, cette trace, presence et roadmap.
Fichiers evites: instances privees, documents bruts, OCR/logs, exports bruts, secrets, serveurs non reserves, scans/kills, push GitHub, `RM-2026-0017`, `ORD-P0-990`.
Dernier point lu: watchdog 2026-05-26 00:09 +02:00; `CONV-2026-1772` reste bloque par recharge manuelle `8788`.
Tests/preuves attendus: paniers pilotage et anti-fuite, line-limit, diff-check.
Risque de collision: faible, correction bornee sur test nav responsive observee rouge.
Lease ownership: 2026-05-26 02:10 +02:00.
Prochaine action: corriger le test stale, ajouter si besoin une assertion produit, relancer les preuves et cloturer.

## Livraison

La route `/pilotage` et son modele affichent des indicateurs actionnables avec periode, source, preuve, seuil, statut lisible, confiance, diffusion, rattachement et prochaine action. Chaque carte expose aussi un lien d'action token-safe: action rattachee si `action_ref` existe, sinon destination prudente par domaine (`/actions`, `/comptes`, `/travaux` ou AG/contentieux). Le lot durcit aussi le contrat: une carte UI sans `confidence` est refusee.

## Preuves

- `.\.venv\Scripts\python.exe -m unittest tests.test_ui_pilotage tests.test_ui_pilotage_data tests.test_ui_pilotage_route tests.test_indicatorops tests.test_pilotageops -v` depuis `server/`: 31 tests OK.
- `.\.venv\Scripts\python.exe -m unittest tests.test_ui_smoke_routes_expanded tests.test_ui_security_routes tests.test_security_no_private_sync_leaks tests.test_ui_accessibility_language tests.test_ui_no_jargon_primary tests.test_ui_novice_language_static -v` depuis `server/`: 32 tests OK.
- `.\server\.venv\Scripts\python.exe .\tools\check_code_line_limit.py` depuis la racine: OK.
- `git diff --check -- ...` sur les fichiers du lot: OK.

## BOT-END - owner integration/tests pilotage - 2026-05-26 00:11 +02:00

Roadmap: `RM-2026-0036` / `RM-2026-0003` / `RM-2026-0006`.
Chantier: `CH-20260526-001000-RM-2026-0036-indicateurs-pilotage`.
Conversation: `CONV-2026-1786`.
Statut: `INTEGRE`.
Fichiers modifies: `server/src/coproscope/web/pilotage_view.py`, `server/src/coproscope/web/templates/pilotage.html`, `server/tests/test_ui_pilotage.py`, `server/tests/test_ui_pilotage_data.py`, `server/tests/test_ui_pilotage_route.py`, `docs/equipe_agile_2026-05-26_indicateurs-pilotage-dev.md`, `docs/presence_agents.md`, `docs/roadmap_backlog_central.md`.
Fichiers volontairement evites: instances privees, documents bruts, OCR/logs, exports bruts, secrets, serveurs non reserves, scans/kills, push GitHub, `RM-2026-0017`, `ORD-P0-990`.
Tests/preuves: pilotage/indicatorops 31 OK; smoke/security/no-private/langue 32 OK; line-limit OK; diff-check OK.
Limites: pas de recette navigateur live/captures car aucun serveur visible reserve n'a ete ouvert.
Questions ouvertes: aucune pour le lot borne.
Prochain mouvement propose: continuer le backlog autonome, hors blocage manuel `CONV-2026-1772` sur serveur visible `8788`.

AGILE-DONE - equipe agile a fini son job
