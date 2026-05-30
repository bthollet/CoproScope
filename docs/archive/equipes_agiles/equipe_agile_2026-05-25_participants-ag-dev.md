# Equipe agile - Participants AG dev - 2026-05-25

Date: 2026-05-25 23:16 +02:00.
Rattachement: `ORD-P1-020`, `RM-2026-0026`, `RM-2026-0006`.
Chantier: `CH-20260525-231600-RM-2026-0026-participants-ag-dev`.

## BOT-START

Voir la ligne active `CONV-2026-1779` dans `docs/presence_agents.md`.

Mission: livrer une route minimale `/gouvernance/participants-ag` tokenisee,
sur donnees fictives, avec droits et pouvoirs AG lisibles, actions officielles
bloquees et tests anti-fuite.

Interdits maintenus: instance privee reelle, documents bruts, OCR/logs,
exports bruts, secrets, serveur non reserve, scan/kill, push GitHub,
`RM-2026-0017`, `ORD-P0-990`, import reel coproprietaires, export officiel,
convocation ou vote AG.

## BOT-END - Owner code unique - 2026-05-25 23:23 +02:00

Roadmap: `RM-2026-0026` / `RM-2026-0006`.
Chantier: `CH-20260525-231600-RM-2026-0026-participants-ag-dev`.
Conversation: `CONV-2026-1779`.
Statut: `INTEGRE`.

Fichiers modifies:

- `server/src/coproscope/web/participants_ag_view.py`;
- `server/src/coproscope/web/templates/participants_ag.html`;
- `server/src/coproscope/web/templates/base.html`;
- `server/src/coproscope/web/feature_routes.py`;
- `server/src/coproscope/web/static/styles.css`;
- `server/src/coproscope/web/static/styles_part_17.css`;
- `server/tests/test_ui_participants_ag.py`;
- `server/tests/test_ui_smoke_routes_expanded.py`;
- `server/tests/test_ui_security_routes.py`;
- `server/tests/test_security_no_private_sync_leaks.py`;
- `docs/presence_agents.md`;
- `docs/roadmap_backlog_central.md`.

Fichiers volontairement evites: instances privees, documents bruts, OCR/logs,
exports bruts, secrets, persistence de participants, import CSV reel, export
officiel, convocation, vote AG, connecteurs externes, `RM-2026-0017`,
`ORD-P0-990`.

Tests/preuves:

```powershell
$env:PYTHONPATH='src'; .\.venv\Scripts\python.exe -m unittest tests.test_ui_participants_ag tests.test_ui_smoke_routes_expanded tests.test_ui_security_routes tests.test_security_no_private_sync_leaks -v
$env:PYTHONPATH='src'; .\.venv\Scripts\python.exe -m unittest tests.test_ui_accessibility_language tests.test_ui_no_jargon_primary tests.test_ui_novice_language_static -v
.\server\.venv\Scripts\python.exe .\tools\check_code_line_limit.py
git diff --check
```

Resultat: panier participants/smoke/security/no-private `21 OK`, puis
langue/accessibilite `15 OK`, line-limit OK, diff-check OK. Le diff-check
signale seulement des warnings CRLF preexistants sur des fichiers deja sales.

Libelles novice ajoutes: `Voix AG`, `Pouvoir`, `Mandataire`, `Feuille de
presence`, compteurs `Coproprietaires a verifier`, `Pouvoirs recus`,
`Votes incomplets`, et synthese derivee `source_of_truth=false`.

Limites: pas de GO produit navigateur; aucune capture desktop/tablette/mobile
ni serveur visible reserve. La page reste informative et synthetique, sans
import reel, export officiel, convocation, envoi ni vote AG.

Prochain mouvement propose: laisser la heartbeat choisir le prochain backlog
actionnable sans reouvrir ce lot; recette navigateur ulterieure seulement avec
port reserve, token, instance de test et captures.

AGILE-DONE - equipe agile a fini son job
