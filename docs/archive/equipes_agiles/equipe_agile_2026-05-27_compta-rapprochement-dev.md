# Equipe agile - Compta rapprochement dev

Date: 2026-05-27 23:04 +02:00.

## BOT-START

- Conversation: `CONV-2026-1796`.
- Roadmap: `RM-2026-0030`.
- Chantier: `CH-20260527-230409-RM-2026-0030-compta-rapprochement`.
- Ordonnancement: `ORD-P0-021` / `COMPTA-RAPPROCHEMENT`.
- Declencheur: Brice valide "Go compta rapprochement".

## Mission

Livrer la premiere tranche utilisable du rapprochement comptable:

- route tokenisee `/comptes/rapprochement`;
- read model public `compta_reconciliation_queue_v1`;
- file de validation humaine ligne par ligne;
- trace append-only des validations/reserves/questions;
- actions sensibles bloquees ou externes: aucun envoi syndic, aucune ecriture comptable officielle, aucun export AG automatique.

## Ownership

Fichiers cibles:

- `server/src/coproscope/web/compta_rapprochement_view.py`;
- `server/src/coproscope/web/templates/compta_rapprochement.html`;
- `server/src/coproscope/web/templates/accounting.html`;
- `server/src/coproscope/web/feature_routes.py`;
- `server/tests/test_ui_comptes_rapprochement.py`;
- `server/tests/test_ui_smoke_routes_expanded.py`;
- `docs/equipe_agile_2026-05-27_compta-rapprochement-dev.md`;
- `docs/presence_agents.md`;
- `docs/roadmap_backlog_central.md`.

## Evites

Instances privees, documents bruts, OCR/logs, exports bruts, secrets, donnees
comptables reelles, mouvements bancaires reels, envoi syndic, export AG
automatique, serveur live, scans/kills, push GitHub, `RM-2026-0017` et
`ORD-P0-990`.

## Tests attendus

- `python -m unittest tests.test_ui_comptes_rapprochement -v`;
- smoke/security/no-private si la route rejoint le panier global;
- controle plafond 600 lignes.

## BOT-END

Date: 2026-05-27 23:16 +02:00.

Livraison:

- route `/comptes/rapprochement` tokenisee;
- read model `compta_reconciliation_queue_v1` depuis `controle_comptes_guide_YYYY.csv`;
- cellules comptabilite, banque, facture et decision/devis;
- journal humain append-only `compta_human_validations_YYYY.csv`;
- lien depuis `/comptes` et panier routes principales;
- instance courante exposee dans `app.state.instance` pour les routes feature derivees.

Preuves:

- `python -m unittest tests.test_ui_comptes_rapprochement -v`: 4 OK;
- `python -m unittest tests.test_ui_comptes_guide -v`: 10 OK;
- `python -m unittest tests.test_ui_smoke_routes_expanded -v`: 5 OK;
- `python -m unittest tests.test_ui_security_routes -v`: 4 OK;
- `python -m unittest tests.test_security_no_private_sync_leaks -v`: 8 OK;
- `server\.venv\Scripts\python.exe tools\check_code_line_limit.py`: OK;
- `git diff --check`: OK, avec warnings CRLF preexistants.

Limites:

- pas de serveur live ni capture navigateur;
- source bancaire directe encore representee comme cellule candidate/manquante si le read model ne l'alimente pas;
- aucun envoi syndic, export AG officiel ou modification comptable automatique.
