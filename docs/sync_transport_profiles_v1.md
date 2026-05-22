# Sync transport profiles v1

Ce document decrit les profils de synchronisation acceptables pour un vault
CoproScope local. Le principe non negociable: sync = transport, pas moteur.
Le moteur du vault reste local, signe, verifie et append-only; le fournisseur de
synchronisation transporte seulement des octets deja produits par le vault.

La detection reste volontairement statique et testable. Elle inspecte l'arbre
de fichiers synchronise, les noms, les marqueurs de conflit et les artefacts de
transport. Elle ne scanne ni processus ni ports, et ne deduit pas l'etat de
sync depuis une application residente.

## Profils couverts

| id | transport | type | usage attendu | reaction aux conflits |
| --- | --- | --- | --- | --- |
| `google_drive_desktop` | Google Drive Desktop | `folder_transport` | Dossier local replique par Drive Desktop, avec fichiers hydrates localement. | Revue humaine des copies conflictuelles, rejet des pointeurs `.gdoc`, `.gsheet`, `.gslides` comme preuves. |
| `onedrive` | OneDrive | `folder_transport` | Dossier local replique par OneDrive, sans supposer que Files On-Demand fournit des octets stables. | Revue humaine des conflits Office et des fichiers partiels avant toute confiance. |
| `dropbox` | Dropbox | `folder_transport` | Dossier local replique par Dropbox Desktop, Smart Sync traite comme transport uniquement. | Revue humaine des conflicted copies et metadata Dropbox hors surface vault. |
| `nextcloud` | Nextcloud | `folder_transport` | Dossier local replique par Nextcloud Desktop, avec regles serveur variables. | Revue humaine des copies en conflit et metadata Nextcloud hors preuve. |
| `syncthing_p2p` | Syncthing P2P | `peer_to_peer` | Replique pair-a-pair entre appareils explicitement approuves. | Revue humaine des conflits P2P; les fichiers `.stfolder`, `.stignore`, `.stversions` restent de l'etat transport. |
| `cold_encrypted_backup` | Backup froid chiffre | `offline_backup` | Copie manuelle chiffree, deconnectee, verifiee par restauration periodique. | Pas de merge automatique; si deux copies divergent, verifier signatures, hashes et fraicheur avant restauration. |
| `local_folder` | Dossier local | `folder_transport` | Dossier local sans fournisseur distant, utile pour dev, demo ou export controle. | Meme discipline de surface: pas de conflit masque ni artefact temporaire dans le vault. |

## Exclusions obligatoires

Ces entrees ne doivent jamais etre placees dans le dossier synchronise du vault:

- `.git`
- `.venv`
- `__pycache__`
- `.pytest_cache`
- `.mypy_cache`
- `.ruff_cache`
- `.cache`
- `node_modules`
- `*.log`
- `logs`
- `decrypted_blobs`
- `blobs_dechiffres`
- `tmp_exports`
- `exports_tmp`
- `temporary_exports`

La regle couvre les racines et les sous-dossiers. Les caches, logs, virtualenvs,
exports temporaires et blobs dechiffres ne sont pas des preuves de vault; ils
sont regenerables, sensibles ou instables.

## Marqueurs de conflit

Les marqueurs fournisseur connus sont traites comme un signal `attention`, pas
comme une preuve de corruption du vault:

- `conflicted copy`
- `conflict copy`
- `selective sync conflict`
- `sync conflict`
- `sync-conflict`
- `computer's conflicted copy`
- `copie en conflit`
- `edit conflict`
- `fichier en conflit`
- `conflit`
- `.gdoc`
- `.gsheet`
- `.gslides`
- `.tmp`
- `.partial`

Reaction attendue:

- isoler le fichier conflictuel hors publication externe;
- demander une revue humaine;
- comparer les hashes, signatures et evenements sources;
- conserver la version valide comme nouvel evenement signe si une reprise est
  necessaire;
- ne jamais choisir une version par horodatage fournisseur seul;
- ne pas verrouiller tout le vault pour un simple conflit fournisseur;
- suspendre la publication si des octets instables, placeholders, caches,
  logs, exports temporaires, `.git` ou `.venv` sont exposes;
- passer en lecture seule uniquement si l'integrite vault est en incident
  (signature, hash, cle publique, manifeste ou blob manquant/invalide).

## Risques par transport

### Google Drive Desktop

Drive Desktop est accepte comme transport de dossier local, pas comme source
de verite. Les fichiers Google natifs `.gdoc`, `.gsheet` et `.gslides` sont des
pointeurs fournisseur et ne remplacent jamais des blobs hydrates, hashes et
signes. Les copies conflictuelles demandent une revue humaine.

### OneDrive

OneDrive est accepte comme transport si le dossier expose des octets locaux
stables. Files On-Demand, AutoSave Office, fichiers `~$`, `.tmp`, `.partial` ou
renommages de politique tenant sont des signaux a traiter avant publication.

### Dropbox

Dropbox est accepte comme transport de dossier. Smart Sync et LAN sync peuvent
laisser des placeholders, metadata ou conflicted copies; ces artefacts restent
hors preuve et doivent etre nettoyes ou justifies.

### Nextcloud

Nextcloud est accepte comme transport de dossier local. Les limites serveur,
regles d'ignore et journaux de sync peuvent varier par instance; les metadata
`.sync_journal.db` et `.sync-exclude.lst` ne sont pas des donnees vault.

### Syncthing P2P

Syncthing P2P est un transport pair-a-pair. Il n'y a pas d'autorite cloud qui
tranche une version canonique: les pairs peuvent propager suppressions, mauvais
octets ou conflits. L'ajout d'un appareil et la gestion des suppressions doivent
etre explicites.

### Backup froid chiffre

Le backup froid chiffre est une copie de reprise, pas une sync active. La
fraicheur depend de la cadence manuelle, les cles doivent etre testees, et la
restauration doit verifier signatures, hashes et blobs avant remise en service.

## Contrat d'audit

L'audit de transport ne fait que classer des signaux observables dans le dossier:

- `information`: dossier propre, sync active supposee, aucune entree interdite;
- `attention`: conflit fournisseur ou metadata de transport a revoir;
- `protection`: cache, log, export temporaire, `.git`, `.venv`, placeholder ou
  ecriture partielle dans la surface synchronisee;
- `incident`: integrite vault atteinte ou non verifiable.

Ce contrat se limite au transport. Il ne remplace pas la verification cryptographique du vault et ne doit pas devenir un moteur de sync cache.
