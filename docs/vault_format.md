# Format vault CoproScope V1

## But et invariants

Le vault CoproScope est un dossier synchronisable chiffre. Il transporte des
blobs immuables, des evenements signes et des accelerateurs reconstruisibles.
L'application reconstruit l'etat courant localement a partir de l'historique
valide; aucun fichier de cache local n'est source de verite.

Invariants V1:

- un fichier deja reference par hash est immuable;
- un evenement valide est append-only et ne peut pas etre reecrit;
- aucune donnee metier sensible n'apparait en clair dans le dossier sync;
- toute modification manuelle d'un evenement, d'un blob reference ou d'une cle
  publique referencee doit etre detectee par `vault verify`;
- les snapshots et indexes accelerent la lecture mais ne remplacent jamais les
  evenements.

## Arborescence sync

```text
vault.json
blobs/
  <prefix>/
    <blob_id>.blob
events/
  <device_id>/
    <sequence>_<event_hash>.json
snapshots/
  <snapshot_id>.json
keys/
  public/
    <author_key_id>.json
  wrapped/
    <recipient_key_id>.json
indexes/
  <index_id>.idx
```

Seules ces entrees sont autorisees a la racine du vault V1. Les repertoires
vides peuvent etre crees par `vault init`. Un client doit ignorer les fichiers
temporaires qu'il cree hors vault; il ne doit pas les synchroniser.

## Conventions communes

- Encodage texte: UTF-8 sans BOM, fins de ligne LF.
- JSON canonique pour tout contenu signe ou hashe: objets avec cles triees
  lexicographiquement, pas d'espace insignifiant, entiers en base 10, chaines
  JSON normalisees, pas de champs `null` sauf quand la spec le demande.
- Dates: chaines UTC au format `YYYY-MM-DDTHH:MM:SSZ`. Les fuseaux locaux et
  timestamps sans `Z` sont invalides.
- Hashs: SHA-256 en hex minuscule sur les octets exacts du contenu cible, sauf
  mention contraire.
- Base64: base64url sans padding pour les nonces et ciphertexts encodes dans
  JSON.
- Sequences: entiers positifs, demarrant a `1` par `device_id`, sans trou dans
  une chaine valide.
- Identifiants: ASCII minuscule, stables, sans signification metier.

Formats d'identifiants V1:

| Champ | Format |
| --- | --- |
| `vault_id` | `vlt_` + 32 octets aleatoires en hex |
| `event_id` | `evt_` + 32 octets aleatoires en hex |
| `device_id` | `dev_` + 16 octets aleatoires en hex |
| `author_key_id` | `key_` + 32 premiers caracteres du SHA-256 de la cle publique canonique |
| `object_id` | `<kind>_` + 16 octets aleatoires en hex |
| `blob_id` | SHA-256 hex du fichier `.blob` chiffre complet |

## `vault.json`

`vault.json` est non sensible et ne contient aucun nom de copropriete, document,
personne, chemin local ou commentaire.

Champs requis V1:

| Champ | Type | Regle |
| --- | --- | --- |
| `schema_version` | entier | valeur `1` |
| `vault_id` | chaine | format `vlt_*` defini ci-dessus |
| `created_at` | chaine | date UTC canonique |
| `crypto_profile` | chaine | valeur V1: `aes-256-gcm+ed25519+sha256` |
| `event_format_version` | entier | valeur `1` |
| `snapshot_format_version` | entier | valeur `1` |

Un client V1 doit refuser un `schema_version` superieur a `1`. Un champ
additionnel est autorise seulement s'il commence par `x_`; il ne doit pas
changer la verification cryptographique V1.

## Blobs

- Stockage: `blobs/<prefix>/<blob_id>.blob`, ou `prefix` correspond aux deux
  premiers caracteres de `blob_id`.
- `blob_id` est le SHA-256 du fichier `.blob` chiffre complet, jamais du nom ou
  du contenu clair source.
- Le contenu est chiffre en AES-256-GCM avec nonce unique de 96 bits.
- Le fichier `.blob` contient uniquement des octets chiffres et le tag
  d'authentification; aucune metadata lisible n'est incluse dans le fichier.
- Le nom original, le MIME type, la taille claire, les chemins locaux et les
  commentaires restent dans le payload evenement chiffre.
- Un blob n'est considere utilise que s'il est reference par un evenement
  valide. Un blob orphelin est signale par `vault verify` mais ne rend pas
  l'historique invalide.

## Evenements

Stockage: `events/<device_id>/<sequence>_<event_hash>.json`.

`event_hash` est le SHA-256 hex des octets canoniques de l'evenement sans le
champ `signature`. Le champ `signature` signe exactement ces memes octets
canoniques. Le hash n'est pas stocke dans le JSON V1 pour eviter une dependance
circulaire; il est derive et compare au nom de fichier.

Un evenement V1 doit respecter toutes les regles suivantes:

- `device_id` du chemin identique au champ `device_id`;
- `sequence` du nom de fichier identique au champ `sequence`;
- `sequence = 1` implique `prev_device_event_hash = null`;
- `sequence > 1` implique `prev_device_event_hash` egal au `event_hash` de
  l'evenement precedent du meme appareil;
- un couple `(device_id, sequence)` ne peut avoir qu'un seul `event_hash`;
- `vault_id` identique a celui de `vault.json`;
- `schema_version = 1`.

## Enveloppe claire

Champs requis, dans le modele logique V1:

| Champ | Sensibilite | Regle |
| --- | --- | --- |
| `event_id` | non sensible | identifiant aleatoire de l'evenement |
| `vault_id` | non sensible | identifiant du vault |
| `schema_version` | non sensible | entier `1` |
| `event_type` | non sensible | type declare dans `objets_metier_evenements_v1.md` |
| `author_key_id` | non sensible | cle Ed25519 publique autorisee |
| `device_id` | non sensible | appareil emetteur |
| `sequence` | non sensible | sequence locale de l'appareil |
| `created_at` | non sensible | date UTC fournie par l'appareil |
| `object_id` | non sensible | objet principal vise, ou `vault_id` pour `vault_initialized` |
| `prev_device_event_hash` | non sensible | hash precedent du meme appareil, ou `null` |
| `encrypted_payload_hash` | non sensible | SHA-256 des octets chiffres avant encodage base64url |
| `payload_nonce` | non sensible | nonce AES-GCM base64url sans padding |
| `encrypted_payload` | chiffre | payload chiffre base64url sans padding |
| `signature` | non sensible | signature Ed25519 base64url sans padding |

Le payload AES-GCM utilise comme AAD les octets canoniques de l'enveloppe claire
sans `encrypted_payload`, `encrypted_payload_hash` et `signature`. La signature
couvre l'enveloppe complete sans `signature`, donc elle couvre aussi le payload
chiffre et son hash.

## Payload chiffre

Le payload chiffre est un objet JSON canonique avant chiffrement. Il contient:

- `payload_schema_version`: entier `1`;
- `object_kind`: famille d'objet metier;
- `operation`: intention metier stable;
- `data`: objet contenant les champs metier du type d'evenement;
- `links`: references optionnelles vers objets, evenements ou blobs.

Donnees qui doivent rester chiffrees:

- nom original de document;
- chemins locaux ou references de depot;
- commentaires et notes;
- points, actions, decisions et statuts metier;
- resultats de traitement plugin;
- metadata utiles a la reconstruction locale.

## Cles

`keys/public/` peut contenir les cles publiques de signature necessaires a la
verification hors ligne. `keys/wrapped/` peut contenir des cles de vault
chiffrees pour des destinataires autorises. Aucune cle privee, seed, phrase de
recuperation ou secret plugin ne doit etre stocke dans le vault.

Un fichier de cle publique est lui-meme non sensible mais doit etre canonique:
`author_key_id`, `algorithm`, `public_key`, `created_at`, `status`. Son contenu
doit correspondre aux evenements `member_invited` et `member_revoked`.

## Snapshots et indexes

Les snapshots sont des accelerateurs signes et chiffres. Ils peuvent contenir
un etat projete, les heads par appareil et un hash de projection. Leur absence
ou suppression ne doit pas empecher la reconstruction depuis `events/`.

Les indexes synchronises doivent etre chiffres ou opaques. Un index lisible
contenant noms, statuts, commentaires, texte OCR ou chemins locaux est interdit.
Un index invalide est supprime ou reconstruit; il ne rend pas l'historique
valide invalide.

## Verification

`vault verify` controle au minimum:

- presence et schema de `vault.json`;
- absence d'entrees interdites a la racine et dans les repertoires sync;
- encodage UTF-8 et JSON canonique des fichiers JSON verifies;
- coherence chemin/champs pour chaque evenement;
- hash du payload chiffre;
- hash d'evenement derive et nom de fichier;
- signature Ed25519 et statut de la cle;
- chainage par appareil, sequences contigues et absence de forks silencieux;
- presence, chemin et hash des blobs references par des evenements valides;
- compatibilite des versions de schema, payload, snapshot et plugin;
- absence de metadata metier en clair dans `vault.json`, les noms de fichiers
  et les indexes lisibles.

Les diagnostics doivent distinguer au moins `error` et `warning`. Une erreur
empeche l'application de l'evenement concerne; un warning signale une entree
orpheline, regenerable ou ignoree.

## Interdits

Le dossier sync ne contient jamais:

- `.git`;
- `.venv`;
- `__pycache__`;
- cache OCR;
- exports temporaires;
- blobs dechiffres;
- cle privee ou secret;
- nom reel de document en clair;
- index lisible.

`vault init` et `vault verify` doivent refuser ou signaler ces entrees si elles
apparaissent dans le vault. Le repo produit local peut conserver son `.git`, et
un environnement Python local peut exister hors vault, mais ces dossiers restent
strictement exclus du cloud synchronise.
