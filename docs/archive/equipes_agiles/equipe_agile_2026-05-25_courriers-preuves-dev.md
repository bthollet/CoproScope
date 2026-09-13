# Equipe agile - Courriers et preuves dev - 2026-05-25

Date: 2026-05-25 23:23 +02:00.
Rattachement: `ORD-P1-030`, `RM-2026-0028`, `RM-2026-0006`.
Chantier: `CH-20260525-232300-RM-2026-0028-courriers-preuves-dev`.

## BOT-START

Voir la ligne active `CONV-2026-1780` dans `docs/presence_agents.md`.

Mission: livrer une route minimale `/courriers/preuves` tokenisee, sur donnees
fictives, avec brouillons, mandat, validation humaine, preuves et rattachements
lisibles, sans transmission depuis CoproScope.

Interdits maintenus: instance privee reelle, documents bruts, OCR/logs,
exports bruts, secrets, serveur non reserve, scan/kill, push GitHub,
`RM-2026-0017`, `ORD-P0-990`, OAuth, IMAP, SMTP, LRAR, envoi automatique,
export officiel ou courrier reel.

## BOT-END - Owner code unique - 2026-05-25 23:28 +02:00

Roadmap: `RM-2026-0028` / `RM-2026-0006`.
Chantier: `CH-20260525-232300-RM-2026-0028-courriers-preuves-dev`.
Conversation: `CONV-2026-1780`.
Statut: `INTEGRE`.

Fichiers modifies:

- `server/src/coproscope/web/courriers_preuves_view.py`;
- `server/src/coproscope/web/templates/courriers_preuves.html`;
- `server/src/coproscope/web/templates/base.html`;
- `server/src/coproscope/web/feature_routes.py`;
- `server/src/coproscope/web/static/styles.css`;
- `server/src/coproscope/web/static/styles_part_18.css`;
- `server/tests/test_ui_courriers_preuves.py`;
- `server/tests/test_ui_smoke_routes_expanded.py`;
- `server/tests/test_security_no_private_sync_leaks.py`;
- `docs/equipe_agile_2026-05-25_courriers-preuves-dev.md`;
- `docs/presence_agents.md`;
- `docs/roadmap_backlog_central.md`.

Fichiers volontairement evites: instances privees, documents bruts, OCR/logs,
exports bruts, secrets, connecteurs externes, compte mail, prestataire courrier,
envoi automatique, export officiel, courrier reel, `RM-2026-0017`,
`ORD-P0-990`.

Tests/preuves:

```powershell
$env:PYTHONPATH='src'; .\.venv\Scripts\python.exe -m unittest tests.test_ui_courriers_preuves tests.test_ui_smoke_routes_expanded tests.test_ui_security_routes tests.test_security_no_private_sync_leaks -v
$env:PYTHONPATH='src'; .\.venv\Scripts\python.exe -m unittest tests.test_ui_accessibility_language tests.test_ui_no_jargon_primary tests.test_ui_novice_language_static -v
.\server\.venv\Scripts\python.exe .\tools\check_code_line_limit.py
git diff --check
```

Resultat: panier courriers/smoke/security/no-private `21 OK`, puis
langue/accessibilite `15 OK`, line-limit OK, diff-check OK. Le diff-check
signale seulement des warnings CRLF preexistants sur des fichiers deja sales.

Libelles novice livres: `Brouillon`, `Mandat`, `Preuve de depot`, `Preuve de
reception`, `Verifier avant envoi`, `Copier le brouillon`, `Rattacher une
preuve`, et `source_of_truth=false` pour rappeler que les sorties restent des
syntheses derivees.

Limites: pas de GO produit navigateur; aucune capture desktop/tablette/mobile
ni serveur visible reserve. La page reste informative et synthetique, sans
transmission, connecteur, secret, export officiel ni courrier reel.

Prochain mouvement propose: laisser la heartbeat choisir le prochain backlog
actionnable sans reouvrir ce lot; recette navigateur ulterieure seulement avec
port reserve, token, instance de test et captures.

AGILE-DONE - equipe agile a fini son job
