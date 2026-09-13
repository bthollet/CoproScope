# Equipe agile - Drive upload smoke chiffre

Rattachement: `RM-2026-0014` / `RM-2026-0007` / `ORD-P0-900`.
Chantier: `CH-20260525-232621-RM-2026-0014-drive-upload-smoke`.
Conversation: `CONV-2026-1781`.

## BOT-START - Coordinateur Drive - 2026-05-25 23:26 +02:00

Mission: reprendre le lot installable Drive maintenant que l'OAuth local est
pret, livrer le plus petit smoke upload Drive chiffre defendable, puis rendre
un chainage backlog exploitable.

Ownership modifiable:

- `server/src/coproscope/modules/gdriveops.py`
- `server/src/coproscope/_cli_parts/01_imports_and_parser.py`
- `server/src/coproscope/_cli_parts/02_dispatch.py`
- `server/tests/test_gdriveops.py`
- `docs/runbook_installable_drive_chiffre_oauth.md`
- `docs/equipe_agile_2026-05-25_drive-upload-smoke.md`
- `docs/presence_agents.md`
- `docs/roadmap_backlog_central.md`

Fichiers et zones evites: instances privees, documents bruts, OCR/logs,
exports bruts, secrets OAuth, tokens, chemins OAuth reels, serveurs locaux,
push GitHub, `RM-2026-0017` et `ORD-P0-990`.

Dernier point lu: `docs/presence_agents.md` et
`docs/roadmap_backlog_central.md` a 23:26 +02:00. `CONV-2026-1772` reste
bloque sur recharge manuelle du serveur visible `8788`; `CONV-2026-1780` est
integre et ne doit pas etre duplique.

Agents lances en lecture seule:

- cartographie technique Drive;
- QA/privacy Drive;
- coordination backlog.

Commande stabilisee:

- conserver le scope strict `drive.file`;
- refuser tout upload si le gate anti-fuite ne valide pas un blob ou snapshot
  chiffre dans la surface vault sync;
- ne jamais afficher le contenu du token, du refresh token, du client secret ou
  des chemins OAuth reels;
- tester le vrai code d'upload avec un faux service Google Drive, sans reseau;
- si une surface de test chiffree est disponible, executer un smoke reel
  explicite seulement sur fichier chiffre.

Tests/preuves attendus:

- `python -m unittest tests.test_gdriveops -v`;
- `python -m unittest tests.test_security_no_private_sync_leaks -v` si les
  sorties ou traces changent;
- `tools/check_code_line_limit.py` ou garde-fou equivalent;
- `git diff --check` sur les fichiers touches.

## BOT-END - Coordinateur Drive - 2026-05-25 23:31 +02:00

Roadmap: `RM-2026-0014` / `RM-2026-0007`.
Chantier: `CH-20260525-232621-RM-2026-0014-drive-upload-smoke`.
Conversation: `CONV-2026-1781`.
Statut: `INTEGRE`.

Fichiers modifies:

- `server/src/coproscope/modules/gdriveops.py`;
- `server/src/coproscope/_cli_parts/01_imports_and_parser.py`;
- `server/src/coproscope/_cli_parts/02_dispatch.py`;
- `server/tests/test_gdriveops.py`;
- `docs/runbook_installable_drive_chiffre_oauth.md`;
- `docs/equipe_agile_2026-05-25_drive-upload-smoke.md`;
- `docs/presence_agents.md`;
- `docs/roadmap_backlog_central.md`.

Fichiers volontairement evites: instances privees, documents bruts, OCR/logs,
exports bruts, secrets OAuth/tokens, chemins OAuth reels, serveurs locaux,
push GitHub, `RM-2026-0017` et `ORD-P0-990`.

Livraison:

- `drive smoke --upload` appelle Drive seulement apres gate anti-fuite vert,
  token present et scope strict `drive.file`;
- l'upload reel est teste via faux service Drive, sans reseau;
- les sorties redactionnelles ne publient ni token, ni secret, ni chemin OAuth
  reel, ni chemin local absolu;
- `_token_scopes` accepte les tokens JSON UTF-8 avec BOM, cas courant quand un
  fichier factice est produit par PowerShell.

Tests/preuves:

```powershell
$env:PYTHONPATH='src'; .\.venv\Scripts\python.exe -m unittest tests.test_gdriveops tests.test_security_no_private_sync_leaks -v
.\server\.venv\Scripts\python.exe .\tools\check_code_line_limit.py
git diff --check
.\.venv\Scripts\python.exe -m coproscope.cli drive status
.\.venv\Scripts\python.exe -m coproscope.cli drive smoke --sync-root <temp-sync> --encrypted-path <temp-blob> --token-path <temp-token>
```

Resultat: `test_gdriveops` + `test_security_no_private_sync_leaks` = `19 OK`;
line-limit OK; diff-check OK avec warnings CRLF preexistants. `drive status`
retourne `status=ready`, scope `drive.file`, chemins OAuth expurges. Le smoke
CLI prepare un blob fictif `blobs/aa/<sha>.blob`, retourne `status=prepared`,
`ready_for_upload=true`, `upload_attempted=false`, `scope_ok=true`, et n'affiche
que le chemin relatif au coffre chiffre.

Limites: aucun nouvel upload Drive reel execute pendant cette verification,
aucun secret OAuth affiche, aucun serveur local lance. Le smoke reel reste a
faire seulement sur surface chiffree de test explicitement designee.

Prochain mouvement propose: laisser la heartbeat choisir le prochain backlog
actionnable; ne relancer Drive que pour un smoke reel explicite sur blob ou
snapshot chiffre verifie.

AGILE-DONE - equipe agile a fini son job.

## Point 23:31 +02:00 - Smoke Drive chiffre reel

Retours agents lecture seule:

- increment minimal: upload explicite d'un seul blob/snapshot chiffre, pas de
  sync complete ni partage;
- QA/privacy: aucun `files.list`, aucune permission, aucun token/secret/chemin
  local dans la sortie;
- backlog: ne pas dupliquer `CONV-2026-1772`, `CONV-2026-1776` ou les lots
  integres `1777`..`1780`; apres Drive, continuer sur `ORD-P1-040` si aucun
  serveur live n'est lance.

Implementation livree:

- `drive smoke` conserve le mode preparation sans upload;
- `drive smoke --upload` execute l'upload Drive apres gate anti-fuite;
- le nom distant est opaque: `coproscope-encrypted-smoke-<sha12>.blob`;
- l'upload ne liste pas Drive et ne cree aucune permission de partage;
- la sortie CLI redige les chemins OAuth et ne renvoie que des booleens
  `folder_id_present` / `file_id_present`.

Preuve reelle executee sur blob synthetique hors depot produit:

```text
status=uploaded
command=drive smoke upload
scope_ok=true
gate.code=encrypted_vault_surface
relative_path=blobs/ee/<64hex>.blob
size_bytes=37
upload_attempted=true
drive.folder_id_present=true
drive.file_id_present=true
```

Contenu envoye: octets synthetiques `ciphertext-only`, pas de document brut.
La sortie n'a affiche ni token, ni secret OAuth, ni ID Drive brut, ni chemin
OAuth.
