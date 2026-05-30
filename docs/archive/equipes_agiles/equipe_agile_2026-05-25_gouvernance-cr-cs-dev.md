# Equipe agile - Gouvernance compte rendu conseil syndical dev

Date: 2026-05-25 23:07 +02:00.
Rattachement: `ORD-P1-010`, `RM-2026-0024`, `RM-2026-0006`.
Chantier: `CH-20260525-230700-RM-2026-0024-gouvernance-cr-cs-dev`.

## BOT-START

Voir la ligne active `CONV-2026-1778` dans `docs/presence_agents.md`.

Mission: livrer une route minimale `/gouvernance/compte-rendu-cs` tokenisee,
sur donnees fictives, avec validation interne prudente, preuves et diffusion
visibles, version locale, actions officielles bloquees et tests anti-fuite.

Interdits maintenus: instance privee reelle, documents bruts, OCR/logs,
exports bruts, secrets, serveur non reserve, scan/kill, push GitHub,
`RM-2026-0017`, `ORD-P0-990`, PV AG complet, signature qualifiee, publication
ou envoi officiel.

## BOT-END - Owner code unique - 2026-05-25 23:14 +02:00

Roadmap: `RM-2026-0024` / `RM-2026-0006`.
Chantier: `CH-20260525-230700-RM-2026-0024-gouvernance-cr-cs-dev`.
Conversation: `CONV-2026-1778`.
Statut: `INTEGRE`.

Fichiers modifies:

- `server/src/coproscope/web/governance_cr_cs_view.py`;
- `server/src/coproscope/web/templates/governance_cr_cs.html`;
- `server/src/coproscope/web/templates/base.html`;
- `server/src/coproscope/web/feature_routes.py`;
- `server/src/coproscope/web/static/styles.css`;
- `server/src/coproscope/web/static/styles_part_16.css`;
- `server/tests/test_ui_governance_cr_cs.py`;
- `server/tests/test_ui_smoke_routes_expanded.py`;
- `server/tests/test_ui_security_routes.py`;
- `server/tests/test_security_no_private_sync_leaks.py`;
- `docs/presence_agents.md`;
- `docs/roadmap_backlog_central.md`.

Fichiers volontairement evites: instances privees, documents bruts, OCR/logs,
exports bruts, secrets, `viewmodel.py`, persistence de signatures, connecteurs
mail/Drive/LRAR, actions d'envoi, `RM-2026-0017`, `ORD-P0-990`.

Tests/preuves:

```powershell
.\.venv\Scripts\python.exe -m unittest tests.test_ui_governance_cr_cs tests.test_ui_smoke_routes_expanded tests.test_ui_security_routes tests.test_security_no_private_sync_leaks -v
.\server\.venv\Scripts\python.exe .\tools\check_code_line_limit.py
git diff --check
.\.venv\Scripts\python.exe -m unittest tests.test_ui_accessibility_language tests.test_ui_no_jargon_primary tests.test_ui_novice_language_static -v
```

Resultat: `21 OK`, line-limit OK, diff-check OK avec warnings CRLF
preexistants, puis `15 OK`.

Limites: pas de GO produit navigateur; aucune capture desktop/tablette/mobile
ni serveur visible reserve. La route utilise un modele synthetique et ne cree
aucun compte rendu persistant. La validation interne reste informative et les
actions de publication/envoi restent absentes.

Prochain mouvement propose: laisser la heartbeat choisir le prochain backlog
actionnable sans reouvrir ce lot; recette navigateur ulterieure seulement avec
port reserve, token, instance de test et captures.

AGILE-DONE - equipe agile a fini son job
