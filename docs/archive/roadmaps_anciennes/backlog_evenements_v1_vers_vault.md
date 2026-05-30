# Backlog technique - evenements V1 vers vault reel

> Statut gouvernail: `SOURCE_HISTORIQUE`.
> La source de verite roadmap est `docs/roadmap_backlog_central.md`
> (`RM-2026-0004`). Ce backlog ne lance plus de dev directement.

Date: 2026-05-20
Perimetre: plan de raccordement, sans implementation.

## Objectif

Raccorder les brouillons `BusinessEventDraft` produits par
`coproscope.core.events_v1` a un vault reel: enveloppe signee, chainage par
appareil, payload chiffre, reconstruction SQLite, actions UI
commentaire/point/action, resultats plugins, demandes et export de passation.

Le changement vise une bascule claire:

- les brouillons V1 restent un contrat de transition;
- le vault signe devient la source collaborative;
- SQLite, templates, exports et indexes restent des projections
  reconstruisibles.

## Etat de depart

- `BusinessEventDraft` calcule un `payload_hash`, impose les types V1
  canoniques en snake_case, mais ne conserve pas le payload metier et ne signe
  rien.
- Les anciens libelles a points (`plugin.result_recorded`,
  `request.normalized`, etc.) sont des alias de migration explicites; les
  nouveaux brouillons produisent `plugin_result_recorded`, `request_created`,
  `request_action_recorded`, `suggestion_review_requested` et
  `suggestion_outcome_prepared`.
- `vault.core` sait deja initialiser/importer/verifier/snapshotter un vault,
  avec etat local, cle auteur, `device_id` et events append-only.
- `vault.reconstruction` reconstruit deja `event_log`, `identities`,
  `documents`, `status_observations` et `conflicts`, mais pas encore points,
  actions, commentaires, demandes, plugins ni exports.
- Les UI demandes, AG/contentieux/passation et atelier piece sont pretes ou
  partiellement visibles, mais les actions restent locales/derivees.

## Invariants a conserver

- Aucun chemin local, email, telephone, secret, nom de fichier sensible ou
  payload brut non chiffre dans le dossier sync.
- Aucun last-write-wins silencieux: correction et resolution de conflit sont
  de nouveaux evenements signes.
- Le payload chiffre porte les champs metier; l'enveloppe claire porte
  seulement les champs non sensibles du format vault.
- La sequence est locale au `device_id`, contigue et verifiee.
- Un export de passation reste derive, avec `source_of_truth: false`; il peut
  etre reference par evenement, pas devenir registre source.

## P0 - Socle signature et ecriture vault

### P0.1 - Aligner le contrat `BusinessEventDraft` avec les events vault

Livrables:

- Definir un objet d'entree d'ecriture vault, par exemple
  `VaultEventWriteRequest`, qui contient:
  `event_type`, `object_id`, `object_kind`, `operation`, `data`, `links`,
  `visibility`, `source_module`, `draft_hash`.
- Ajouter une couche d'adaptation depuis `BusinessEventDraft`, sans modifier
  les producteurs metier dans le meme lot.
- Maintenir le nommage canonique:
  `plugin_result_recorded`, `request_created`, `request_action_recorded`,
  `suggestion_review_requested`, `suggestion_outcome_prepared`.
- Decider si `request_created` et `request_action_recorded` deviennent des
  events vault natifs, ou s'ils sont projetes en `action_created`,
  `status_changed` et `comment_added`.

Criteres d'acceptation:

- Un brouillon ne peut pas etre ecrit si son `payload_hash` ne correspond pas
  au payload fourni a l'ecrivain vault.
- Les types inconnus sont conservables pour audit mais non applicables par la
  reconstruction V1.
- Les tests couvrent canonicalisation, refus des champs dangereux et compat
  des anciens alias a points vers les types snake_case.

Fichiers probables:

- `server/src/coproscope/core/events_v1.py`
- `server/src/coproscope/vault/core.py`
- `server/tests/test_events_v1.py`
- `server/tests/test_vault.py`

### P0.2 - Ecrire une enveloppe signee depuis `vault.core`

Livrables:

- Centraliser une fonction d'ecriture append-only:
  `append_signed_event(local_root, sync_root, request)`.
- Construire le payload chiffre canonique:
  `payload_schema_version`, `object_kind`, `operation`, `data`, `links`.
- Construire l'enveloppe claire:
  `event_id`, `vault_id`, `schema_version`, `event_type`, `author_key_id`,
  `device_id`, `sequence`, `created_at`, `object_id`,
  `prev_device_event_hash`, `encrypted_payload_hash`, `payload_nonce`,
  `encrypted_payload`.
- Signer l'enveloppe sans `signature`, puis ecrire
  `events/<device_id>/<sequence>_<event_hash>.json`.
- Retourner un resultat exploitable par l'UI et les tests:
  `event_id`, `event_hash`, `device_id`, `sequence`, `object_id`,
  `event_type`, `signature_status`.

Criteres d'acceptation:

- `vault verify` detecte modification du JSON, payload chiffre, signature,
  nom de fichier, sequence, fork et precedent manquant.
- Une erreur d'ecriture n'avance pas la sequence locale.
- Les dates ecrites sont en UTC canonique `YYYY-MM-DDTHH:MM:SSZ`.

### P0.3 - Verrouiller la chaine appareil

Livrables:

- Stocker dans `vault_local.json` le prochain numero de sequence ou les heads
  par appareil.
- Reserver la sequence de facon atomique cote local root.
- Lire le dernier event existant du `device_id` avant ecriture pour calculer
  `prev_device_event_hash`.
- Signaler clairement:
  `broken_device_chain`, `device_fork`, `missing_previous_event`,
  `local_state_out_of_sync`.

Criteres d'acceptation:

- Deux events successifs du meme appareil forment une chaine contigue.
- Une copie concurrente avec meme sequence et hash different est un incident,
  pas un choix automatique.
- Le diagnostic UI peut afficher appareil, sequence, dernier event et action
  conseillee.

## P0 - Reconstruction SQLite metier

### P0.4 - Etendre la projection locale

Livrables:

- Ajouter des tables reconstruites:
  `points`, `actions`, `comments`, `requests`, `plugin_runs`, `exports`,
  `object_links`, `object_event_sources`.
- Conserver pour chaque ligne:
  `object_id`, statut courant, champs utiles, `created_from_event_hash`,
  `updated_from_event_hash`, `source_event_ids_json`.
- Appliquer les events:
  `comment_added`, `point_created`, `action_created`, `status_changed`,
  `plugin_result_recorded`, `export_created`, `passation_export_created`
  si conserve en compat.
- Ne jamais reconstruire depuis un export derive ou un cache local si les
  events sources existent.

Criteres d'acceptation:

- Supprimer `vault_reconstruction.sqlite3` puis relancer la reconstruction
  redonne le meme etat.
- Les conflits de statut action/point restent visibles dans `conflicts`.
- Un event valide mais a dependance manquante est journalise, non applique.

### P0.5 - Adapter les vues de lecture au cache reconstruit

Livrables:

- Definir des fonctions de lecture stables pour l'UI:
  historique d'objet, statut signature, auteur logique, appareil, date UTC,
  sources et preuves.
- Prioriser les donnees vault reconstruites quand un vault est configure.
- Garder les registres CSV actuels comme fallback local tant que tous les
  producteurs ne sont pas branches.

Criteres d'acceptation:

- Une fiche document, point, action ou export peut afficher son historique
  event-sourced.
- L'UI distingue clairement `source vault signee`, `projection locale` et
  `registre historique non migre`.

## P1 - Actions UI commentaire, point, action

### P1.1 - Creer des actions UI atomiques

Livrables:

- Ajouter trois commandes applicatives:
  `add_comment(target_object_id, body, visibility, proof_ids)`;
  `create_point(title, category, severity, proof_ids, source_refs)`;
  `create_action(title, owner_ref, due_at, related_point_ids, proof_ids)`.
- Chaque commande fabrique un payload metier, demande signature/ecriture vault,
  puis declenche reconstruction ou invalidation du cache.
- Les formulaires UI n'envoient jamais de chemin local ni de contenu brut de
  document.

Criteres d'acceptation:

- Depuis l'atelier piece, une ligne peut produire un commentaire, un point ou
  une action rattachee a la preuve/source visible.
- La ligne affiche ensuite le dernier event, la validite de signature, auteur,
  appareil et date UTC.
- En cas de vault non configure ou invalide, l'action est bloquee avec une
  explication et une prochaine action.

### P1.2 - Historique et conflits visibles

Livrables:

- Ajouter un panneau d'historique pour document, point, action, demande et
  export.
- Afficher au minimum:
  event type, statut signature, auteur logique, appareil, sequence, date UTC,
  source module, liens de preuve.
- Remonter les conflits de reconstruction avant les actions ordinaires.

Criteres d'acceptation:

- Un utilisateur novice voit pourquoi une action est ouverte, bloquee, faite
  ou conflictuelle.
- Les erreurs d'integrite ne peuvent pas etre masquees par un etat courant
  apparemment propre.

## P1 - Demandes coproprietaires

### P1.3 - Raccorder RequestOps au vault

Livrables:

- Mapper une demande normalisee en objet vault `request` ou en `action`
  rattachee a un `point`; trancher le modele avant implementation.
- Ecrire les creations de demandes et actions de journal via events signes.
- Conserver les champs actuels:
  canal, statut, preuve/source, next action, rattachement point/action,
  visibility.
- Exclure ou chiffrer les notes selon la visibilite; jamais de coordonnees en
  clair.

Criteres d'acceptation:

- La page demandes peut etre reconstruite depuis le vault sans CSV.
- Les CSV restent importables comme historique de migration, avec events
  `migration_recorded` ou provenance explicite.
- Une demande restreinte n'apparait pas dans les exports coproprietaires sans
  decision de diffusion compatible.

## P1 - Resultats plugins

### P1.4 - Brancher `plugin_result_recorded`

Livrables:

- Faire de `PluginResultRecorded.signature_payload` le payload source de
  l'event vault `plugin_result_recorded`.
- Stocker `plugin_run_id`, `plugin_id`, version, `manifest_hash`,
  `input_hashes`, `parameters_hash`, `result_hash`, `output_hashes`,
  `produced_event_ids`, statut et erreurs generiques.
- Verifier que le plugin a declare le `result_event_type` et ses contrats de
  sortie.
- Relier les objets produits via `object_links`, sans jamais stocker les
  chemins d'outputs.

Criteres d'acceptation:

- Un resultat plugin peut etre rejoue en audit: version, entrees, parametres
  hashes et sorties sont identifiables.
- Un plugin fonde sur une entree absente, obsolete ou incompatible produit un
  diagnostic, pas une projection silencieuse.
- Les plugins restent du code local hors vault.

## P1 - Export passation

### P1.5 - Historiser les exports derives

Livrables:

- Garder `build_passation_derived_export(...)` comme constructeur derive.
- A l'export, ecrire un event vault de reference:
  `export_created` pour un artefact produit, ou
  `passation_export_created` comme type canonique.
- Le payload d'event contient:
  `export_id`, format, profil, hash du contenu exporte, sources, preuves,
  omissions, restriction maximale, `source_of_truth: false`.
- Si un fichier export est conserve dans le vault, le stocker comme blob
  chiffre et reference par `export_blob_id`.

Criteres d'acceptation:

- Reproduire l'export depuis events + blobs donne le meme hash ou explique les
  differences.
- Le watermark "export derive, non source collaborative" reste obligatoire.
- Un export bloque par confidentialite n'ecrit pas de blob diffusable; il ecrit
  seulement un diagnostic ou une omission signee.

## P2 - Migration et compatibilite

### P2.1 - Importer l'historique local existant

Livrables:

- Fournir une migration depuis registres CSV/modules locaux vers events vault.
- Produire des events `migration_recorded` avec versions outil, nombre
  d'objets, hash resultat et omissions.
- Garder un mode dry-run listant les donnees non migrables:
  chemin prive, contact personnel, statut inconnu, reference orpheline.

Criteres d'acceptation:

- Une instance synthetique peut etre migree, verifiee, reconstruite, puis lue
  par l'UI sans dependance aux CSV sources.
- Les omissions sont visibles dans le cockpit et dans le rapport de migration.

### P2.2 - Snapshots et performances

Livrables:

- Creer un snapshot chiffre apres reconstruction valide.
- Inclure heads par appareil, hash de projection et versions de schema.
- Verifier que supprimer le snapshot force une reconstruction complete sans
  perte d'etat.

Criteres d'acceptation:

- Les snapshots accelerent la lecture mais ne sont jamais source de verite.
- Un snapshot invalide est ignore ou reconstruit apres diagnostic.

## Ordre conseille

1. Corriger le contrat et le nommage des events (`BusinessEventDraft`,
   `plugin_result_recorded`, demandes).
2. Ajouter l'ecrivain vault signe append-only avec chainage appareil.
3. Etendre la reconstruction SQLite aux objets metier: points, actions,
   commentaires, demandes, plugins, exports.
4. Brancher les actions UI commentaire/point/action sur l'ecrivain vault.
5. Brancher RequestOps, plugins et passation export.
6. Ajouter migration, snapshots et lectures UI avancees.

## Tests de reference a preparer

- `test_business_event_draft_requires_matching_payload_before_vault_write`
- `test_append_signed_event_links_previous_device_event`
- `test_verify_rejects_device_fork`
- `test_reconstruction_rebuilds_points_actions_comments_from_events`
- `test_requestops_can_rebuild_requests_page_from_vault_cache`
- `test_plugin_result_recorded_uses_manifest_contracts_without_paths`
- `test_passation_export_reference_is_derived_not_source_of_truth`
- `test_ui_action_is_blocked_when_vault_verify_fails`

## No-go avant implementation

- Ne pas brancher une action UI qui ecrit seulement dans SQLite.
- Ne pas faire de SQLite la source de verite.
- Ne pas signer le hash d'un payload dont le contenu fourni a l'ecrivain n'est
  pas disponible et reverifiable.
- Ne pas exporter une demande restreinte sans event de diffusion compatible.
- Ne pas laisser produire de nouveaux evenements a points; les alias ne servent
  qu'a migrer ou lire l'ancien historique documente.
