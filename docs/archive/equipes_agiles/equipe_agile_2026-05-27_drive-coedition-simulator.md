# Equipe agile Drive - simulateur deux appareils

BOT-START - Coordinateur-scribe Drive - 2026-05-27 23:14 +02:00

Roadmap: `RM-2026-0014` / `RM-2026-0007` / `RM-2026-0033`

Chantier: `CH-20260527-231424-RM-2026-0014-drive-coedition-simulator`

Conversation coordinatrice: `CONV-2026-1803`

Objectif: prolonger `ORD-P0-901` apres le contrat paquet de changement chiffre
en livrant un simulateur local deux appareils. Le resultat attendu est un
artefact JSON testable: deux appareils autorises publient des changements
chiffres, puis CoproScope annonce soit une fusion locale deterministe, soit un
conflit humain explicite.

## Perimetre

UI ou artefact reel cible: artefact local `simulate_two_device_coedition` dans
le module Drive coedition, verifie par tests unitaires. Aucune UI navigateur et
aucun serveur ne sont requis pour ce lot.

Owner code unique: `CONV-2026-1806`.

Ownership modifiable code:

- `server/src/coproscope/modules/gdrive_coedit.py`
- `server/tests/test_gdrive_coedit.py`

Ownership coordination:

- `docs/equipe_agile_2026-05-27_drive-coedition-simulator.md`
- `docs/presence_agents.md`
- `docs/roadmap_backlog_central.md`

Fichiers et actions evites: instances privees, documents bruts, OCR/logs,
exports bruts, secrets OAuth/tokens, chemins OAuth reels, identites reelles,
IDs Drive bruts, reseau Drive reel, upload Drive reel, serveurs, scans/kills,
push GitHub, `RM-2026-0017`, `ORD-P0-990`.

Dernier point lu: `docs/presence_agents.md`,
`docs/roadmap_backlog_central.md`, `docs/protocole_equipe_agile_agents.md`,
et lot integre `docs/equipe_agile_2026-05-27_drive-coedition-protocol.md`.

Tests/preuves attendus:

- `.\.venv\Scripts\python.exe -B -m unittest tests.test_gdrive_coedit tests.test_gdriveops tests.test_security_no_private_sync_leaks -v`
  depuis `server/`;
- `.\server\.venv\Scripts\python.exe .\tools\check_code_line_limit.py`
  depuis la racine;
- `git diff --check` sur les fichiers touches.

## Roles ouverts

| Conversation | Role | Statut | Mission | Ecrit dans |
|---|---|---|---|---|
| `CONV-2026-1803` | Coordinateur-scribe Drive | `EN_COURS` | Tenir presence/gouvernail, lancer roles, integrer le lot apres preuves. | Docs de coordination uniquement. |
| `CONV-2026-1804` | Architecte protocole coedition | `EN_COURS` | Challenger causalite, parents, reprise et frontiere merge/conflit sans lire de clair. | Lecture seule. |
| `CONV-2026-1805` | Utilisateur novice / collaboration | `EN_COURS` | Verifier que la sortie explique clairement fusion, conflit, appareil et action suivante. | Lecture seule. |
| `CONV-2026-1806` | Dev back owner Drive coedition | `EN_COURS` | Implementer le simulateur local deux appareils et ses tests. | `gdrive_coedit.py`, `test_gdrive_coedit.py`. |
| `CONV-2026-1807` | QA securite / anti-fuite | `EN_COURS` | Verifier absence de secret, chemin, identite, ID Drive brut et overwrite silencieux. | Lecture seule. |

## Commande dev initiale

Ajouter au contrat local de coedition un simulateur deux appareils qui accepte
des paquets prepares par `prepare_encrypted_change_packet` et des intentions de
changement synthetiques, sans clair documentaire. Le simulateur doit:

- refuser les paquets bloques ou appartenant a des objets differents;
- garder seulement des hashes, sequences, parents et empreintes pseudonymes;
- detecter deux branches concurrentes sur le meme objet;
- retourner `merged` quand les intentions synthetiques sont disjointes;
- retourner `conflict` quand elles touchent le meme composant logique ou quand
  le merge ne peut pas etre prouve sans clair;
- toujours exposer `silent_overwrite: forbidden`;
- ne jamais tenter d'appel Drive, upload, lecture de token ou resolution
  d'identite reelle.

## Point de coordination

- A tester maintenant: contrat local `prepare_encrypted_change_packet` deja
  integre, puis futur `simulate_two_device_coedition`.
- En dev maintenant: simulateur causal deux appareils, owner `CONV-2026-1806`.
- En enquete maintenant: lisibilite novice de la sortie `merged` / `conflict`.
- Commande prete: oui, sans UI navigateur.
- Comparaison visuels enquete: non pertinente pour ce lot backend local; la
  comparaison utilisateur porte sur le vocabulaire de confiance issu de
  `Coffre et partage`.
- Agents idle a relancer: aucun au demarrage.
- Decision requise: aucune tant que le lot reste sans reseau Drive reel.
- Prochain mouvement: recevoir le patch dev back, puis lancer QA anti-fuite et
  tests cibles.

## Retours agents

Architecture `CONV-2026-1804`: NO-GO si le simulateur pretend fusionner depuis
le chiffre ou depuis l'ordre `sequence`. GO seulement si la fusion est
conservative: meme objet, paquets prepares, parent commun connu, branches
concurrentes prouvees et composants synthetiques disjoints. Toute ambiguite
devient un conflit humain explicite.

QA/novice `CONV-2026-1805` / `CONV-2026-1807`: la sortie doit rester lisible en
termes `merged`, `conflict`, `noop`, `ordered` ou `blocked`, avec
`next_action` clair, appareils/auteurs pseudonymes et `silent_overwrite:
forbidden`. La sortie ne doit jamais contenir token, secret, chemin OAuth, ID
Drive brut, identite reelle, clair documentaire, chemin local ou marqueur
source sensible.

Dev back `CONV-2026-1806`: patch rendu dans `gdrive_coedit.py` et
`test_gdrive_coedit.py`. API ajoutee: `simulate_two_device_coedition(...)`.
Le simulateur accepte deux paquets prepares et deux intentions synthetiques par
hash de composant, puis retourne `merged`, `conflict`, `blocked`, `noop` ou
`ordered` sans reseau ni upload.

## Verification

- `.\.venv\Scripts\python.exe -B -m unittest tests.test_gdrive_coedit tests.test_gdriveops -v`
  depuis `server/`: 26 tests OK.
- `.\.venv\Scripts\python.exe -B -m unittest tests.test_gdrive_coedit tests.test_gdriveops tests.test_security_no_private_sync_leaks -v`
  depuis `server/`: 34 tests OK apres regularisation hors-lot du fragment
  vault manquant.
- `.\server\.venv\Scripts\python.exe .\tools\check_code_line_limit.py`
  depuis la racine: OK, aucun fichier code suivi au-dessus de 600 lignes.
- `git diff --check -- server/src/coproscope/modules/gdrive_coedit.py server/tests/test_gdrive_coedit.py docs/presence_agents.md docs/roadmap_backlog_central.md docs/equipe_agile_2026-05-27_drive-coedition-simulator.md`: OK.
- Blocage initial hors perimetre: le premier passage du gate large echouait
  avant le code Drive sur `server/src/coproscope/vault/_reconstruction_parts/07_followups.py`
  manquant. Le fragment a ete regularise par un autre chantier; le gate large
  repasse maintenant sans modification Drive supplementaire.

## Statut courant

INTEGRE: le simulateur local deux appareils est livre et verifie. Le lot reste
strictement local: aucun reseau Drive reel, aucune lecture de secret ou token,
aucun document brut, aucun serveur, aucun scan/kill et aucun push GitHub.

AGILE-DONE - equipe agile a fini son job

BOT-END - Coordinateur-scribe Drive - 2026-05-27 23:34 +02:00

Roadmap: `RM-2026-0014` / `RM-2026-0007` / `RM-2026-0033`

Chantier: `CH-20260527-231424-RM-2026-0014-drive-coedition-simulator`

Conversation: `CONV-2026-1803`..`CONV-2026-1807`

Statut: `INTEGRE`

Fichiers modifies: `server/src/coproscope/modules/gdrive_coedit.py`,
`server/tests/test_gdrive_coedit.py`, cette trace, `docs/presence_agents.md`,
`docs/roadmap_backlog_central.md`.

Fichiers volontairement evites: instances privees, documents bruts, OCR/logs,
exports bruts, secrets OAuth/tokens, chemins OAuth reels, identites reelles,
IDs Drive bruts, reseau Drive reel, upload Drive reel, serveurs, scans/kills,
push GitHub, `RM-2026-0017`, `ORD-P0-990`.

Tests/preuves: Drive/coedit/gdriveops/no-private 34 OK, line-limit OK,
diff-check OK.

Limites: ce n'est pas encore une coedition utilisateur temps reel; c'est le
simulateur local causal qui permet de tester la fusion ou le conflit avant de
brancher une couche collaborative plus riche.

Prochain mouvement propose: poursuivre `ORD-P0-901` par la couche de
collaboration locale/reprise, en s'appuyant sur les statuts `merged`,
`conflict`, `blocked`, `noop` et `ordered` sans promettre de coedition depuis
un simple snapshot.
