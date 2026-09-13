# Equipe agile - Coffre et partage dev

Date: 2026-05-25 23:00 +02:00.
Rattachement: `ORD-P0-050`, `RM-2026-0033`, `RM-2026-0006`.
Chantier: `CH-20260525-230000-RM-2026-0033-coffre-partage-dev`.

## BOT-START

Voir la ligne active `CONV-2026-1777` dans `docs/presence_agents.md`.

Mission: livrer une route minimale `/coffre/partage` tokenisee, sur donnees
fictives, avec droits separes, partage/invitation/revocation/recuperation
bloques par defaut, navigation visible et tests anti-fuite.

Interdits maintenus: instance privee reelle, documents bruts, OCR/logs,
exports bruts, secrets, serveur non reserve, scan/kill, push GitHub,
`RM-2026-0017`, `ORD-P0-990`, action reelle d'invitation/export/revocation.

## BOT-END - Owner code unique - 2026-05-25 23:06 +02:00

Roadmap: `RM-2026-0033` / `RM-2026-0006`.
Chantier: `CH-20260525-230000-RM-2026-0033-coffre-partage-dev`.
Conversation: `CONV-2026-1777`.
Statut: `INTEGRE`.

Fichiers modifies:

- `server/src/coproscope/web/coffre_partage_view.py`;
- `server/src/coproscope/web/feature_routes.py`;
- `server/src/coproscope/web/templates/coffre_partage.html`;
- `server/src/coproscope/web/templates/base.html`;
- `server/src/coproscope/web/static/styles.css`;
- `server/src/coproscope/web/static/styles_part_15.css`;
- `server/src/coproscope/web/_app_fragments/part_003.pyfrag`;
- `server/tests/test_ui_coffre_partage.py`;
- `server/tests/test_ui_smoke_routes_expanded.py`;
- `docs/presence_agents.md`;
- `docs/roadmap_backlog_central.md`.

Fichiers volontairement evites: instances privees, documents bruts,
OCR/logs, exports bruts, secrets, routes d'action reelle, `viewmodel.py`,
`cli.py`, persistence de droits, connecteurs Drive/OAuth, `RM-2026-0017`,
`ORD-P0-990`.

Tests/preuves:

```powershell
.\.venv\Scripts\python.exe -m unittest tests.test_ui_coffre_partage -v
.\.venv\Scripts\python.exe -m unittest tests.test_ui_smoke_routes_expanded tests.test_ui_security_routes tests.test_security_no_private_sync_leaks -v
.\server\.venv\Scripts\python.exe .\tools\check_code_line_limit.py
git diff --check -- server/src/coproscope/web/coffre_partage_view.py server/src/coproscope/web/feature_routes.py server/src/coproscope/web/templates/coffre_partage.html server/src/coproscope/web/templates/base.html server/src/coproscope/web/static/styles.css server/src/coproscope/web/static/styles_part_15.css server/src/coproscope/web/_app_fragments/part_003.pyfrag server/tests/test_ui_coffre_partage.py server/tests/test_ui_smoke_routes_expanded.py docs/presence_agents.md docs/roadmap_backlog_central.md
```

Resultat: `4 OK`, puis `17 OK`, line-limit OK, diff-check OK.
Note: `feature_routes.py` extrait l'enregistrement des routes feature pour
conserver `part_003.pyfrag` sous le plafond local de 600 lignes.

Limites: pas de GO produit navigateur; aucune capture desktop/tablette/mobile
ni serveur visible reserve. Les actions sensibles restent informatives et
desactivees. La route utilise un modele synthetique, pas une persistence
multi-coffres.

Prochain mouvement propose: laisser la heartbeat choisir le prochain backlog
actionnable sans reouvrir ce lot; recette navigateur ulterieure seulement avec
port reserve, token, instance de test et captures.

AGILE-DONE - equipe agile a fini son job
