# Signatures et historique

## Principe

CoproScope ne modifie pas destructivement l'etat collaboratif. Chaque changement
produit un evenement signe, horodate, attribue a un auteur et a un appareil.
L'historique verifiable est la source de verite; les bases locales, caches,
snapshots et indexes ne sont que des projections reconstruisibles.

## Identites V1

Identites separees:

- `author_key_id`: cle publique Ed25519 autorisee a signer des evenements;
- `device_id`: appareil local qui produit une sequence append-only;
- `vault_id`: espace collaboratif cible;
- cle de vault symetrique: secret de chiffrement partage, jamais stocke en
  clair dans le vault.

Une cle de signature peut representer un membre ou un appareil selon la
politique du vault, mais V1 impose une relation explicite dans les payloads
`member_invited` et `member_revoked`. Les cles privees restent locales. Les
cles publiques peuvent etre stockees dans `keys/public/` et referencees par les
evenements d'identite.

`author_key_id` est derive de la cle publique canonique comme defini dans
`vault_format.md`; il ne doit pas contenir de nom de personne.

## Signature V1

Algorithme: Ed25519.

Entree signee:

- l'evenement JSON canonique;
- sans le champ `signature`;
- incluant `encrypted_payload`, `encrypted_payload_hash`, `payload_nonce` et
  tous les champs de l'enveloppe claire;
- encodage UTF-8 exact des octets canoniques.

La verification doit recalculer ces octets, verifier la signature avec la cle
publique `author_key_id`, puis verifier que le SHA-256 de ces memes octets
correspond au `event_hash` porte par le nom de fichier.

Statuts minimaux exposes par la verification:

| Statut | Signification |
| --- | --- |
| `valid` | signature, hash, chaine et schema valides |
| `invalid_signature` | signature Ed25519 invalide |
| `event_hash_mismatch` | nom de fichier incoherent avec le contenu |
| `payload_hash_mismatch` | hash du payload chiffre incoherent |
| `unknown_author` | cle publique absente ou non invitee |
| `revoked_author` | cle revoquee pour cet evenement |
| `broken_device_chain` | sequence ou precedent manquant/incoherent |
| `device_fork` | deux evenements concurrents pour le meme couple appareil/sequence |
| `missing_blob` | blob reference absent ou hash invalide |
| `unsupported_schema` | version non supportee |

## Invitation et revocation

`member_invited` autorise une cle publique a signer pour un vault. Son payload
chiffre contient au minimum:

- `invited_author_key_id`;
- `public_key_algorithm`;
- `public_key`;
- `role`;
- `invited_by_event_id`;
- `valid_from_event_hash`.

`member_revoked` retire cette autorisation pour les evenements futurs. Son
payload chiffre contient au minimum:

- `revoked_author_key_id`;
- `reason`;
- `effective_after`: carte `{device_id: event_hash}` des heads connus par le
  signataire au moment de la revocation.

Regle V1 de revocation: un evenement signe par une cle revoquee reste applicable
seulement s'il appartient a une chaine d'appareil deja couverte par
`effective_after`. Les evenements ulterieurs ou inconnus au moment de la
revocation sont conserves pour audit mais non appliques. Cette regle est
conservative et deterministe; elle ne promet pas d'effacer ce qui a deja ete
dechiffre sur un appareil.

## Historique par appareil

Chaque `device_id` maintient sa propre chaine:

- `sequence = 1` commence avec `prev_device_event_hash = null`;
- `sequence > 1` pointe vers le hash exact de l'evenement precedent du meme
  appareil;
- aucun trou de sequence n'est acceptable pour appliquer les evenements suivants
  du meme appareil;
- un fork de sequence est un conflit d'integrite, pas un choix automatique.

Un appareil peut emettre des evenements pour plusieurs objets. Le chainage par
appareil garantit l'ordre local de production; il ne definit pas seul l'ordre
global metier.

## Reconstruction

La reconstruction s'effectue en trois phases:

1. charger `vault.json`, cles publiques et evenements;
2. verifier schema, hash, signature, chainage, revocation et references blobs;
3. appliquer uniquement les evenements valides selon l'ordre deterministe V1.

Ordre deterministe V1:

1. respecter les dependances de chaine par appareil;
2. appliquer d'abord les evenements d'identite necessaires a la validation;
3. pour les evenements independants, trier par `created_at`, puis
   `device_id`, puis `sequence`, puis `event_hash`.

`created_at` sert a l'ergonomie et au tri stable, mais ne remplace jamais les
preuves cryptographiques. En cas d'horloge incoherente, l'evenement reste
verifiable; le diagnostic doit signaler l'anomalie sans inventer une nouvelle
date.

La projection locale doit conserver, pour chaque champ reconstruit, le ou les
`event_hash` sources. Une base SQLite locale sert de cache de lecture, pas de
source de verite.

## Corrections et conflits

Regles V1:

- pas de last-write-wins silencieux;
- une correction est un nouvel evenement signe qui reference l'evenement ou
  l'objet corrige;
- les statuts concurrents restent visibles tant qu'une resolution explicite
  n'est pas signee;
- une resolution de conflit est elle-meme un evenement signe;
- les suppressions metier sont representees par des statuts (`archived`,
  `superseded`, `cancelled`, `dismissed`) plutot que par suppression physique
  de l'historique.
- une recuperation de cle, un changement de quorum ou un export d'archive
  complete sont eux-memes des evenements signes.

Conflits a exposer:

- deux statuts actifs incompatibles pour le meme objet;
- deux classifications concurrentes de meme priorite;
- action cloturee puis modifiee par une autre chaine;
- plugin produisant un resultat avec entrees ou version incompatibles;
- evenement valide cryptographiquement mais non applicable a cause d'une
  dependance absente.

## UI et audit

L'interface doit afficher:

- historique d'un document, d'un point, d'une action et d'un export;
- validite des signatures et statut de la cle;
- auteur logique, appareil et date UTC de chaque evenement;
- source d'un point ou d'une action;
- traitement plugin applique, version, entrees et hash de sortie;
- export ou biffage produit;
- conflit, evenement invalide ou evenement ignore.
- etat de survivabilite: replicas connus, dernier snapshot, capacite de
  reconstruction coproprietaire, quorum de recuperation des cles critiques.

L'UI ne doit jamais masquer un probleme d'integrite derriere un etat courant
apparemment propre. Un utilisateur peut choisir de masquer les warnings, mais
pas les erreurs qui affectent l'etat applique.
