# Objets metier et evenements V1

## Portee

Ce document definit le vocabulaire metier porte par les payloads chiffres des
evenements V1. Il complete `vault_format.md`, qui definit l'enveloppe, et
`signatures_historique.md`, qui definit la validation et l'application.

Les champs metier sensibles restent dans `encrypted_payload`. Les noms
d'objets, noms de documents, commentaires, chemins locaux, textes OCR et
resultats plugin ne doivent jamais apparaitre dans les noms de fichiers ou dans
`vault.json`.

## Convention de payload

Tout payload chiffre V1 est un JSON canonique avec les champs communs suivants:

| Champ | Type | Regle |
| --- | --- | --- |
| `payload_schema_version` | entier | valeur `1` |
| `object_kind` | chaine | kind de l'objet principal |
| `operation` | chaine | intention stable, proche du type d'evenement |
| `data` | objet | champs metier du type d'evenement |
| `links` | objet | references optionnelles vers objets, evenements, blobs |

`object_id` dans l'enveloppe claire doit designer l'objet principal du payload.
Les references secondaires restent dans `links`.

References standard:

- `event_hash`: hash d'un evenement valide;
- `blob_id`: hash d'un blob chiffre;
- `object_id`: identifiant stable d'objet;
- `version_id`: identifiant stable d'une version de document;
- `plugin_run_id`: identifiant stable d'un traitement plugin.

Une reference absente au moment de l'import ne rend pas le vault illisible. Elle
cree un diagnostic `dangling_reference` et l'evenement reste en attente
d'application metier tant que la dependance manque.

## Objets noyau

| Objet | `object_kind` | Role |
| --- | --- | --- |
| `DocumentRecord` | `document` | document importe, versions, hash, classification, confidentialite |
| `Proof` | `proof` | piece ou extrait relie a un point, une action ou une decision |
| `Point` | `point` | fait concret, anomalie, question, risque ou opportunite |
| `Action` | `action` | demande, relance, verification, decision ou tache suivie |
| `DecisionFollowUp` | `decision` | resolution ou decision suivie avec actions et preuves |
| `PrivacyReview` | `privacy_review` | statut de confidentialite et diffusion possible |
| `ProofCapsule` | `proof_capsule` | preuve biffee, exportee ou partageable |
| `PluginRun` | `plugin_run` | traitement officiel signe avec version, entrees, parametres et resultat |
| `Member` | `member` | cle publique, role et revocation |
| `Migration` | `migration` | changement de format ou import historique |
| `Vault` | `vault` | politique initiale et parametres non sensibles du vault |

## Champs minimaux par objet

`DocumentRecord`:

- `document_id`;
- `current_version_id`;
- `versions`;
- `classification_status`;
- `privacy_status`;
- `created_from_event_hash`.

`Proof`:

- `proof_id`;
- `source_document_id`;
- `source_version_id`;
- `locator`;
- `summary`;
- `confidence`;
- `created_from_event_hash`.

`Point`:

- `point_id`;
- `title`;
- `category`;
- `severity`;
- `status`;
- `proof_ids`;
- `created_from_event_hash`.

`Action`:

- `action_id`;
- `title`;
- `status`;
- `owner_ref`;
- `due_at`;
- `related_point_ids`;
- `proof_ids`;
- `created_from_event_hash`.

`DecisionFollowUp`:

- `decision_id`;
- `title`;
- `status`;
- `decided_at`;
- `action_ids`;
- `proof_ids`;
- `created_from_event_hash`.

`PrivacyReview`:

- `privacy_review_id`;
- `target_object_id`;
- `diffusion_status`;
- `redaction_required`;
- `reason`;
- `created_from_event_hash`.

`ProofCapsule`:

- `proof_capsule_id`;
- `source_proof_ids`;
- `redacted_blob_id`;
- `export_blob_id`;
- `diffusion_status`;
- `created_from_event_hash`.

`PluginRun`:

- `plugin_run_id`;
- `plugin_id`;
- `plugin_version`;
- `manifest_hash`;
- `status`;
- `input_hashes`;
- `parameter_hash`;
- `output_hashes`;
- `created_from_event_hash`.

## Vocabulaires de statut

Statuts communs:

- `draft`;
- `active`;
- `superseded`;
- `archived`;
- `invalidated`.

Statuts de point:

- `open`;
- `confirmed`;
- `dismissed`;
- `converted_to_action`;
- `resolved`.

Statuts d'action:

- `open`;
- `waiting`;
- `done`;
- `cancelled`;
- `blocked`.

Statuts de diffusion:

- `needs_review`;
- `diffusable`;
- `restricted`;
- `blocked`;
- `redacted`.

Un statut inconnu dans un payload V1 doit produire `unsupported_value` et ne
doit pas etre applique silencieusement.

## Evenements V1

| Evenement | Objet principal | Payload `data` minimal |
| --- | --- | --- |
| `vault_initialized` | `vault` | `initial_policy`, `created_by_device_id` |
| `member_invited` | `member` | `invited_author_key_id`, `public_key_algorithm`, `public_key`, `role`, `invited_by_event_id`, `valid_from_event_hash` |
| `member_revoked` | `member` | `revoked_author_key_id`, `reason`, `effective_after` |
| `document_added` | `document` | `document_id`, `version_id`, `blob_id`, `original_name`, `mime_type`, `ciphertext_sha256` |
| `document_version_added` | `document` | `document_id`, `version_id`, `supersedes_version_id`, `blob_id`, `reason` |
| `ocr_completed` | `plugin_run` | `plugin_run_id`, `document_id`, `version_id`, `text_blob_id`, `confidence`, `engine` |
| `classification_completed` | `document` | `document_id`, `version_id`, `classification`, `confidence`, `method` |
| `comment_added` | `proof` | `target_object_id`, `body`, `visibility`, `proof_ids` |
| `point_created` | `point` | `point_id`, `title`, `category`, `severity`, `proof_ids` |
| `action_created` | `action` | `action_id`, `title`, `owner_ref`, `due_at`, `related_point_ids`, `proof_ids` |
| `status_changed` | objet cible | `target_object_id`, `target_kind`, `previous_status`, `new_status`, `reason` |
| `diffusion_decided` | `privacy_review` | `target_object_id`, `diffusion_status`, `redaction_required`, `reason` |
| `redaction_completed` | `proof_capsule` | `proof_capsule_id`, `source_proof_ids`, `redacted_blob_id`, `method` |
| `export_created` | `proof_capsule` | `export_id`, `format`, `export_blob_id`, `source_object_ids`, `profile` |
| `plugin_activated` | `plugin_run` | `plugin_id`, `plugin_version`, `manifest_hash`, `permissions_granted`, `config_hash` |
| `plugin_result_recorded` | `plugin_run` | `plugin_run_id`, `plugin_id`, `status`, `input_hashes`, `output_hashes`, `produced_event_ids` |
| `migration_recorded` | `migration` | `migration_id`, `from_version`, `to_version`, `tool_version`, `result_hash` |

Un type d'evenement inconnu doit etre conserve pour audit mais non applique par
un client V1. Un plugin officiel ne peut produire que les types declares dans
son manifeste et autorises par `plugins_officiels.md`.

## Regles d'application

Chaque evenement ajoute une information. Aucune suppression destructive n'est
necessaire pour obtenir l'etat courant. Une correction est un nouvel evenement.

Regles V1:

- un objet est cree par son premier evenement create/add/initialize valide;
- les evenements ulterieurs reference l'objet par `object_id`;
- un champ metier ne peut changer que par un evenement dedie;
- `status_changed.previous_status` doit correspondre a un statut actif connu,
  sinon un conflit est expose;
- une nouvelle version de document ne supprime jamais les anciennes versions;
- un resultat plugin doit reference le hash des entrees qui ont ete traitees;
- un export est toujours derive et reference ses sources;
- une migration doit etre reversible par audit: elle declare versions, outil,
  entrees et hash de resultat.

## Conflits metier

Les conflits ne sont pas resolus implicitement. Sont notamment conflictuels:

- plusieurs statuts actifs incompatibles pour le meme objet;
- deux versions marquees comme courantes sans lien `supersedes_version_id`;
- action `done` puis modifiee sans evenement de reouverture;
- diffusion `blocked` suivie d'un export sans `diffusion_decided` compatible;
- resultat plugin fonde sur une version de document qui n'est plus courante,
  sauf si le payload declare explicitement une analyse historique.

La resolution utilise un nouvel evenement, le plus souvent `status_changed`,
`diffusion_decided`, `document_version_added` ou `plugin_result_recorded`, avec
references vers les evenements conflictuels dans `links`.

## Exports derives

Les CSV, Markdown, PDF, capsules biffees et exports de restitution sont derives
de l'historique. Ils peuvent etre references par `export_created`, mais ils ne
sont pas source collaborative. Reproduire un export doit etre possible a partir
des evenements valides, des blobs references et des versions plugin declarees.
