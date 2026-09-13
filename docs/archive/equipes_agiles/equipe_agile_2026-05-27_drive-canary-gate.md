# Equipe agile Drive - canari et sync collaborative

BOT-START - Coordinateur-scribe / owner code Drive - 2026-05-27 22:32 +02:00

Roadmap: `RM-2026-0014` / `RM-2026-0007`

Chantier: `CH-20260527-223200-RM-2026-0014-drive-canary-gate`

Conversation: `CONV-2026-1793`

Role: owner code unique Drive CLI/gate anti-fuite.

Mission: durcir `coprocs drive smoke` pour verifier qu'un blob/snapshot chiffre
ne contient plus un canari clair et pour poser un contrat de synchronisation
compatible collaboration directe.

Ownership modifiable:

- `server/src/coproscope/modules/gdriveops.py`
- `server/src/coproscope/_cli_parts/01_imports_and_parser.py`
- `server/src/coproscope/_cli_parts/02_dispatch.py`
- `server/tests/test_gdriveops.py`
- `docs/runbook_installable_drive_chiffre_oauth.md`
- `docs/presence_agents.md`
- `docs/roadmap_backlog_central.md`
- cette trace

Fichiers et actions evites: instances privees, documents bruts, OCR/logs,
exports bruts, secrets OAuth/tokens, chemins OAuth reels, appels reseau Drive
reels, serveurs, scans/kills, push GitHub, `RM-2026-0017`, `ORD-P0-990`.

Dernier point lu: `docs/presence_agents.md` et
`docs/roadmap_backlog_central.md`, passage heartbeat 2026-05-27 22:32 +02:00.

Tests/preuves attendus: tests Drive, tests anti-fuite, garde-fou 600 lignes,
diff-check cible.

## Roles

- Coordinateur-scribe: cadrage, presence, gouvernail, trace.
- Dev Drive: implementation locale dans `gdriveops` et CLI.
- QA securite: non-fuite canari, token, chemin local, Drive ID brut.
- Testeur expert metier: lecture seule via sub-agent, recommandation retenue
  = paquet chiffre + manifeste expurge, pas de sync brute.

## Decision produit

Brice a precise que la synchro doit permettre la collaboration directe. Le lot
ne doit donc pas rester un simple smoke d'upload. La V1 retenue est une sync de
paquets chiffres immuables avec generation, parent attendu, hash, nom distant
opaque et politique de conflit explicite.

Apres arbitrage complementaire, Brice confirme que la vraie collaboration doit
etre l'etape suivante du backlog. Le gouvernail ajoute donc `ORD-P0-901`:
protocole coedition-first avec journal append-only de changements chiffres,
causalite/parents, merge local ou conflit humain explicite. Ce lot reste le
socle anti-fuite/transport, pas la promesse de coedition finale.

Approches concurrentes notees:

- snapshot chiffre mutable unique: plus simple, mais risque d'ecrasement
  silencieux, non retenu;
- journal d'evenements/CRDT: meilleur pour coedition simultanee, mais tranche
  architecture separee;
- Drive Desktop: fallback possible, moins controlable, non retenu comme socle
  principal.

## Livrables

- `drive smoke` accepte `--cleartext-canary` et bloque avant Drive si le
  marqueur clair est encore present dans le candidat chiffre, sans afficher ce
  marqueur.
- `drive smoke` accepte `--generation` et `--parent-sha256`.
- Le manifeste `encrypted_candidate.sync_contract` contient le protocole
  `coproscope-drive-sync-v1`, type de paquet, generation, parent, hash, nom
  distant opaque, politique de conflit et mode `direct-sync-compatible`.
- L'upload de smoke ajoute des `appProperties` expurgees: protocole,
  generation, hash et parent attendu quand il existe.
- Le faux service Drive de test interdit le listing Drive et prouve que l'appel
  reseau n'est fait qu'apres gate local.
- Le runbook Drive dit explicitement que le MVP n'est pas un export ponctuel:
  il doit rester compatible reprise, conflit et collaboration directe.

## Tests

- `.\.venv\Scripts\python.exe -B -m unittest tests.test_gdriveops tests.test_security_no_private_sync_leaks -v`
  depuis `server/`: 23 tests OK.
- `.\server\.venv\Scripts\python.exe .\tools\check_code_line_limit.py`
  depuis la racine: OK, aucun fichier code suivi ne depasse 600 lignes.

BOT-END - Coordinateur-scribe / owner code Drive - 2026-05-27 22:44 +02:00

Statut: `INTEGRE`

Fichiers modifies: ownership ci-dessus.

Limites: pas de vrai appel Drive, pas de verification retelechargement, pas
d'invitation multi-personnes ni de CRDT dans ce lot. La coedition simultanee
reste une decision d'architecture separee.

Prochain mouvement propose: ouvrir `ORD-P0-901` coedition-first comme prochain
lot Drive, avant toute promesse utilisateur de vraie collaboration.

AGILE-DONE - equipe agile a fini son job.
