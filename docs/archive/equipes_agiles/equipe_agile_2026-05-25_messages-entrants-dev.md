# Equipe agile - Messages entrants

Rattachement: `RM-2026-0031` / `RM-2026-0006` / `ORD-P1-040`.
Chantier: `CH-20260525-233500-RM-2026-0031-messages-entrants-dev`.
Conversation: `CONV-2026-1782`.

## BOT-START - Owner messages entrants - 2026-05-25 23:35 +02:00

Mission: livrer une premiere page `Messages entrants` pour qualifier une
sollicitation recue, decider si elle peut etre diffusee, la rattacher a une
preuve ou creer une demande. V1 sans connecteur, sans reponse automatique et
sans publication.

Ownership modifiable:

- `server/src/coproscope/web/messages_entrants_view.py`
- `server/src/coproscope/web/templates/messages_entrants.html`
- `server/src/coproscope/web/templates/base.html`
- `server/src/coproscope/web/feature_routes.py`
- `server/src/coproscope/web/static/styles.css`
- `server/src/coproscope/web/static/styles_part_19.css`
- `server/tests/test_ui_messages_entrants.py`
- tests smoke/security cibles
- registres de presence et gouvernail

Fichiers evites: instances privees, documents bruts, OCR/logs, exports bruts,
secrets, serveurs, connecteurs externes, reponse ou publication reelle,
`RM-2026-0017` et `ORD-P0-990`.

Commande dev:

- route tokenisee `/messages/entrants`;
- modele synthetique marque `FICTIF`;
- premier viewport: pourquoi la file existe, combien de messages a qualifier,
  quelle action humaine faire;
- chaque message affiche source rolee, sujet, urgence, statut de moderation,
  diffusion et preuve attendue;
- actions sensibles bloquees par defaut.

## BOT-END - Owner messages entrants - 2026-05-25 23:42 +02:00

Roadmap: `RM-2026-0031` / `RM-2026-0006`.
Chantier: `CH-20260525-233500-RM-2026-0031-messages-entrants-dev`.
Conversation: `CONV-2026-1782`.
Statut: `INTEGRE`.

Fichiers modifies:

- `server/src/coproscope/web/messages_entrants_view.py`;
- `server/src/coproscope/web/templates/messages_entrants.html`;
- `server/src/coproscope/web/templates/base.html`;
- `server/src/coproscope/web/feature_routes.py`;
- `server/src/coproscope/web/static/styles.css`;
- `server/src/coproscope/web/static/styles_part_19.css`;
- `server/tests/test_ui_messages_entrants.py`;
- `server/tests/test_ui_smoke_routes_expanded.py`;
- `server/tests/test_ui_security_routes.py`;
- `server/tests/test_security_no_private_sync_leaks.py`;
- `docs/equipe_agile_2026-05-25_messages-entrants-dev.md`;
- `docs/presence_agents.md`;
- `docs/roadmap_backlog_central.md`.

Fichiers volontairement evites: instances privees, documents bruts, OCR/logs,
exports bruts, secrets, serveurs, connecteurs externes, reponse automatique,
publication coproprietaires, message reel, `RM-2026-0017` et `ORD-P0-990`.

Livraison:

- route `/messages/entrants` tokenisee;
- file de qualification fictive avec sources rolees, urgence, diffusion,
  preuve et suite humaine;
- libelles novice `Message recu`, `Comprendre et classer`, `Moderation`,
  `Preuve`, `Diffusion`, `Decisions avant action`;
- actions de reponse automatique, publication et connecteur bloquees.

Tests/preuves:

```powershell
$env:PYTHONPATH='src'; .\.venv\Scripts\python.exe -m unittest tests.test_ui_messages_entrants tests.test_ui_smoke_routes_expanded tests.test_ui_security_routes tests.test_security_no_private_sync_leaks -v
$env:PYTHONPATH='src'; .\.venv\Scripts\python.exe -m unittest tests.test_ui_accessibility_language tests.test_ui_no_jargon_primary tests.test_ui_novice_language_static -v
.\server\.venv\Scripts\python.exe .\tools\check_code_line_limit.py
git diff --check
```

Resultat: panier messages/smoke/security/no-private `21 OK`, puis
langue/accessibilite `15 OK`, line-limit OK, diff-check OK. Le diff-check
signale seulement des warnings CRLF preexistants sur des fichiers deja sales.

Limites: pas de GO produit navigateur; aucune capture desktop/tablette/mobile
ni serveur visible reserve. La page reste informative et synthetique, sans
connecteur, reponse automatique, publication ou message reel.

Prochain mouvement propose: laisser la heartbeat choisir le prochain backlog
actionnable sans reouvrir ce lot; recette navigateur ulterieure seulement avec
port reserve, token, instance de test et captures.

AGILE-DONE - equipe agile a fini son job.
