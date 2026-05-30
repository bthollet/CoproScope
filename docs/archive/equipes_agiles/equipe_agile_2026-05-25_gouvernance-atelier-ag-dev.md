# Equipe agile - Gouvernance Atelier AG

BOT-START - Owner code unique front/back/viewmodel - 2026-05-25 23:57 +02:00

Roadmap: `RM-2026-0024`, appui `RM-2026-0008` et `RM-2026-0006`.
Ordre: `ORD-P1-011`.
Chantier: `CH-20260525-235642-RM-2026-0024-gouvernance-atelier-ag`.
Conversation: `CONV-2026-1784`.

Mission: livrer une route tokenisee `/gouvernance/atelier-ag` pour preparer
questions, resolutions de travail, preuves et revue de diffusion, sans action
officielle.

Ownership modifiable:

- `server/src/coproscope/web/governance_atelier_ag_view.py`
- `server/src/coproscope/web/templates/governance_atelier_ag.html`
- `server/src/coproscope/web/templates/base.html`
- `server/src/coproscope/web/feature_routes.py`
- `server/src/coproscope/web/static/styles.css`
- `server/src/coproscope/web/static/styles_part_21.css`
- `server/tests/test_ui_governance_atelier_ag.py`
- tests smoke/security anti-fuite lies a la route

Fichiers evites: instances privees, documents bruts, OCR/logs, exports bruts,
secrets, serveurs locaux, scans/kills, push GitHub, `RM-2026-0017`,
`ORD-P0-990`, convocation officielle, proces-verbal officiel, signature
qualifiee, vote AG et avis juridique.

## Produit livre

- Route `/gouvernance/atelier-ag` tokenisee.
- Navigation `Atelier AG`.
- Modele synthetique marque `FICTIF`.
- Bandeau `Projet CS - non officiel`.
- Questions et resolutions en brouillon, avec preuve attendue et prochaine
  action humaine.
- Revue de diffusion avant export.
- Actions officielles bloquees: convocation, publication officielle et vote.

## Preuves

- `python -m unittest tests.test_ui_governance_atelier_ag tests.test_ui_smoke_routes_expanded tests.test_ui_security_routes tests.test_security_no_private_sync_leaks -v`: 21 OK.
- `python -m unittest tests.test_ui_accessibility_language tests.test_ui_no_jargon_primary tests.test_ui_novice_language_static -v`: 15 OK.
- `tools/check_code_line_limit.py`: OK, aucun fichier code suivi ne depasse 600 lignes.
- `git diff --check` cible: OK, avec warning CRLF preexistant sur `styles.css`.

## Limites

Pas de serveur live ni capture navigateur. Le GO produit navigateur reste a faire
si ce parcours devient prioritaire en recette visuelle. La page reste un atelier
local de preparation, pas une sortie officielle.

BOT-END - Owner code unique front/back/viewmodel - 2026-05-26 00:01 +02:00

Statut: `INTEGRE`.
Prochain mouvement propose: continuer le backlog P1 par `ORD-P1-050`,
`ORD-P1-060`, `ORD-P1-070` ou `ORD-P1-080`, sauf reprise manuelle du serveur
visible `8788` pour le blocage live `CONV-2026-1772`.
