# Projection evenements vault P0

## Objectif

Le module `coproscope.vault.projection_events` applique des enveloppes
`BusinessEventVaultEnvelope` hash-only a une projection memoire minimale. Il ne
lit ni n'ecrit SQLite, ne modifie pas `vault.core` et ne reconstruit aucun
payload metier clair.

## Entree acceptee

La projection attend l'enveloppe produite par
`prepare_business_event_envelope(...)` ou un mapping equivalent:

- `schema_version` vaut `coproscope.vault.business_event_envelope.v1`;
- `event_type` est un type V1 canonique connu;
- `canonical_hash` correspond au corps canonique;
- seuls `business_draft_hash` et `business_payload_hash` representent le
  contenu metier;
- les champs `payload`, `clear_payload`, `encrypted_payload` et
  `business_payload` sont refuses.

## Sortie memoire

`project_business_event_envelopes(...)` retourne un
`VaultBusinessProjection` contenant:

- `requests` pour `request_created`;
- `actions` pour `request_action_recorded` et `action_created`;
- `plugins` pour `plugin_activated` et `plugin_result_recorded`;
- `exports` pour `export_created` et `passation_export_created`;
- `annotations` pour `pdf_annotation_created`;
- `device_sequences` pour detecter un fork simple de sequence par appareil;
- `diagnostics` pour conflits, types inconnus ou enveloppes invalides.

Chaque objet projete conserve uniquement les identifiants, dates, type,
module source, visibilite, hashes metier et hashes d'evenements sources.

## Diagnostics

La couche ne leve pas pour un evenement applicatif invalide: elle conserve un
diagnostic et n'applique pas l'evenement.

- `invalid_event_type`: type non canonique, ancien libelle a points ou forme
  ambigue.
- `unknown_event_type`: type snake_case inconnu en V1, ou type V1 connu mais
  hors du perimetre P0 de cette projection.
- `conflict`: meme objet avec hash metier different, ou meme
  `(device_id, sequence)` avec hash d'evenement different.
- `payload_present`, `invalid_hash`, `invalid_schema`, `invalid_envelope`:
  enveloppe non hash-only ou incoherente.

En cas de conflit, la projection conserve le premier objet applique et garde
l'evenement concurrent dans les diagnostics. Il n'y a pas de last-write-wins.

## Non-objectifs

Cette P0 ne chiffre pas, ne signe pas, ne resout pas les conflits et ne remplace
pas la reconstruction SQLite future. Elle fournit seulement une couche pure,
deterministe et testable pour rejouer des enveloppes hash-only.
