# Equipe agile Drive - protocole coedition-first

BOT-START - Coordinateur-scribe / owner code Drive - 2026-05-27 22:50 +02:00

Roadmap: `RM-2026-0014` / `RM-2026-0007` / `RM-2026-0033`

Chantier: `CH-20260527-225000-RM-2026-0014-drive-coedition-protocol`

Conversation: `CONV-2026-1794`

Role: owner code unique Drive coedition-first.

Mission: ouvrir `ORD-P0-901` avec un premier contrat local testable pour de la
coedition: paquet de changement chiffre append-only, parents multiples,
empreintes pseudonymes appareil/auteur, merge local ou conflit explicite.

Ownership modifiable:

- `server/src/coproscope/modules/gdrive_coedit.py`
- `server/tests/test_gdrive_coedit.py`
- `docs/equipe_agile_2026-05-27_drive-coedition-protocol.md`
- `docs/presence_agents.md`
- `docs/roadmap_backlog_central.md`

Fichiers et actions evites: instances privees, documents bruts, OCR/logs,
exports bruts, secrets OAuth/tokens, vrais identifiants utilisateurs, chemins
OAuth reels, appels reseau Drive reels, serveurs, scans/kills, push GitHub,
`RM-2026-0017`, `ORD-P0-990`.

Dernier point lu: `docs/presence_agents.md` et
`docs/roadmap_backlog_central.md`, heartbeat 2026-05-27 22:50 +02:00.

Tests/preuves attendus: tests unitaires du contrat coedition, tests Drive
existants, tests anti-fuite, line-limit, diff-check cible.

## Decision

La vraie coedition ne doit pas etre fondee sur un snapshot mutable. La V1
coedition-first demarre donc avec un journal append-only de changements
chiffres:

- un paquet change immuable est nomme par son hash;
- les parents peuvent etre multiples pour representer deux edits concurrents;
- l'acteur et l'appareil sont seulement des empreintes de cles pseudonymes;
- Drive ne transporte que les octets chiffres et des noms opaques;
- le merge est local, sinon un conflit humain explicite remplace tout overwrite
  silencieux.

## Livrables

- Module local `gdrive_coedit.py`.
- Fonction `prepare_encrypted_change_packet(...)`.
- Gate de surface chiffree: `changes/<prefix>/<sha256>.change`.
- Rejet des emplacements non chiffrables, paquets vides, nom/hash incoherents
  et identites non pseudonymes.
- Manifeste expurge: protocole, paquet, parents, sequence, empreintes de cles,
  nom distant opaque, politique de merge/conflit.

## Limites

Ce lot ne fait pas encore de merge CRDT, de lecture Drive, d'upload ou
d'interface utilisateur. Il pose le contrat testable qui doit preceder ces
etapes.

## Tests

- `.\.venv\Scripts\python.exe -B -m unittest tests.test_gdrive_coedit tests.test_gdriveops tests.test_security_no_private_sync_leaks -v`
  depuis `server/`: 27 tests OK.
- `.\server\.venv\Scripts\python.exe .\tools\check_code_line_limit.py`
  depuis la racine: OK, aucun fichier code suivi ne depasse 600 lignes.

BOT-END - Coordinateur-scribe / owner code Drive - 2026-05-27 22:55 +02:00

Statut: `INTEGRE`

Fichiers modifies: ownership ci-dessus.

Fichiers volontairement evites: instances privees, documents bruts, OCR/logs,
exports bruts, secrets OAuth/tokens, vrais identifiants utilisateurs, appels
reseau Drive reels, serveurs, scans/kills, push GitHub, `RM-2026-0017`,
`ORD-P0-990`.

Prochain mouvement propose: brancher le contrat sur un merge local/CRDT minimal
ou un simulateur deux appareils qui produit soit une fusion locale, soit un
conflit humain explicite.

AGILE-DONE - equipe agile a fini son job.
