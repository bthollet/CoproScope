# Plugins officiels CoproScope

## Principe

Le noyau reste petit et responsable de la confiance: vault, chiffrement,
signature, identite, sync dossier, objets metier et UI de base. Les traitements
lourds deviennent des plugins officiels signes, installes localement et
historises par evenements.

Un plugin V1 ne fait jamais partie du vault. Le vault ne stocke que des
references verifiables: manifeste signe, version, permissions accordees, hash
des entrees, hash des sorties et evenements produits.

## Manifeste V1

Le manifeste est un JSON canonique UTF-8. Sa signature couvre le manifeste sans
le champ `signature`.

Champs requis:

| Champ | Type | Regle |
| --- | --- | --- |
| `id` | chaine | identifiant stable, ex. `coproscope.docops` |
| `name` | chaine | nom affichable non sensible |
| `version` | chaine | SemVer `MAJOR.MINOR.PATCH` |
| `publisher` | chaine | editeur officiel |
| `manifest_schema_version` | entier | valeur `1` |
| `min_core_version` | chaine | version minimale du noyau |
| `max_core_version` | chaine ou null | version maximale testee ou `null` |
| `entrypoint` | objet | commande/module local, jamais un chemin vault |
| `permissions` | liste | permissions demandees |
| `event_types_produced` | liste | types V1 que le plugin peut emettre |
| `input_contracts` | liste | schemas d'entree acceptes |
| `output_contracts` | liste | schemas de sortie produits |
| `determinism` | chaine | `deterministic`, `bounded` ou `external` |
| `signature_key_id` | chaine | cle officielle de signature manifeste |
| `signature` | chaine | signature Ed25519 base64url sans padding |
| `revocation_status` | chaine | `valid`, `revoked` ou `unknown` |

`manifest_hash` est le SHA-256 hex du manifeste canonique sans `signature`. Il
est stocke dans les evenements `plugin_activated` et `plugin_result_recorded`.

## Permissions V1

Permissions reconnues:

- `read_event_history`;
- `read_decrypted_payload:<object_kind>`;
- `read_blob_plaintext:<purpose>`;
- `create_blob_ciphertext`;
- `emit_event:<event_type>`;
- `read_local_cache`;
- `write_local_cache`;
- `network:none`;
- `network:declared_hosts`.

Un plugin n'obtient aucune permission par defaut. L'activation enregistre les
permissions accordees, qui peuvent etre un sous-ensemble des permissions
demandees. Une permission inconnue rend l'activation invalide en V1.

Les secrets externes, tokens et chemins locaux restent dans la configuration
locale de l'utilisateur. Le vault ne stocke que `config_hash` et, si necessaire,
des labels non sensibles.

## Contrats d'entree et sortie

Un `input_contract` declare:

- `name`;
- `contract_version`;
- `object_kinds`;
- `event_types`;
- `required_fields`;
- `blob_requirements`;
- `schema_hash`.

Un `output_contract` declare:

- `name`;
- `contract_version`;
- `event_types`;
- `object_kinds`;
- `produced_blobs`;
- `schema_hash`.

Le noyau doit verifier qu'un resultat plugin respecte les types declares avant
d'accepter les evenements produits. Les sorties non conformes sont conservees en
diagnostic local mais ne sont pas appliquees au vault.

## Activation

- Le plugin est installe localement, jamais dans le vault.
- Le vault peut declarer un plugin requis ou recommande par evenement, pas par
  fichier executable synchronise.
- L'activation produit un evenement `plugin_activated`.
- Chaque execution produit un evenement `plugin_result_recorded`.

Payload minimal de `plugin_activated`:

- `plugin_id`;
- `plugin_version`;
- `manifest_hash`;
- `permissions_granted`;
- `config_hash`;
- `activated_by_policy`;
- `activated_at`.

Un client doit refuser l'activation si:

- le manifeste n'est pas signe par une cle officielle valide;
- la version noyau est hors bornes;
- `revocation_status` vaut `revoked` ou ne peut pas etre etabli;
- une permission demandee ou accordee est inconnue;
- le plugin declare produire un type d'evenement non autorise.

## Resultats historises

Payload minimal de `plugin_result_recorded`:

- `plugin_run_id`;
- `plugin_id`;
- `plugin_version`;
- `manifest_hash`;
- `status`;
- `started_at`;
- `completed_at`;
- `input_hashes`;
- `parameter_hash`;
- `output_hashes`;
- `produced_event_ids`;
- `diagnostics`;
- `reproducibility_note`.

`input_hashes` reference les evenements, blobs ou projections lus. Les
parametres sensibles ne sont pas stockes; seul `parameter_hash` est historise.
`output_hashes` reference les blobs ou evenements produits. Un plugin qui
utilise un moteur externe, un modele IA ou un service reseau doit declarer la
version du moteur et la raison de non-determinisme dans `reproducibility_note`.

## Garde-fous

- Pas d'auto-update silencieux.
- Pas de plugin communautaire en V1.
- Desactivation si version incompatible, signature inconnue ou manifeste
  revoque.
- Parametres, version, hash des entrees et hash des sorties sont historises.
- Un plugin ne peut pas modifier un evenement existant.
- Un plugin ne peut pas ecrire de blob dechiffre dans le vault.
- Un plugin ne peut pas emettre un type d'evenement absent de son manifeste.
- Les traitements reseau sont interdits sauf permission explicite
  `network:declared_hosts` et liste d'hotes dans la configuration locale.

## Revocation et compatibilite

La revocation d'un manifeste bloque les activations et executions futures. Les
resultats deja signes restent dans l'historique avec un diagnostic indiquant
que le plugin est desormais revoque. Un client V1 ne doit pas supprimer
automatiquement ces resultats; une correction metier passe par de nouveaux
evenements.

Une mise a jour de plugin est une nouvelle version avec nouveau
`manifest_hash`. Elle doit etre activee explicitement et ne remplace pas
retroactivement les `plugin_run_id` precedents.

## Plugins initiaux

| Plugin | `id` propose | Sorties principales autorisees |
| --- | --- | --- |
| DocOps | `coproscope.docops` | `document_added`, `document_version_added`, `classification_completed`, `plugin_result_recorded` |
| ComptaScope | `coproscope.comptascope` | `point_created`, `action_created`, `status_changed`, `plugin_result_recorded` |
| PrivacyOps | `coproscope.privacyops` | `diffusion_decided`, `status_changed`, `plugin_result_recorded` |
| BiffageOps | `coproscope.biffageops` | `redaction_completed`, `export_created`, `plugin_result_recorded` |
| DocAI/OCR | `coproscope.docai_ocr` | `ocr_completed`, `plugin_result_recorded` |
| Evidence/Exports | `coproscope.evidence_exports` | `export_created`, `plugin_result_recorded` |

Ces identifiants sont reserves. Tout renommage futur doit passer par un
evenement de migration et conserver la correspondance avec les anciens
`plugin_run_id`.
