# Integration evenements metier vers vault

## Objectif

Le lot `coproscope.vault.business_events` fournit une passerelle pure entre les
`BusinessEventDraft` de `coproscope.core.events_v1` et une future ecriture
append-only dans le vault.

Il ne modifie pas le coeur vault existant, n'ecrit aucun fichier, ne chiffre pas
et ne signe pas. Il prepare uniquement une enveloppe canonique, hashable et
testable.

## Entree

L'entree metier est un `BusinessEventDraft` deja safe:

- `event_type`, `object_id`, `actor_ref`, `device_ref`, `occurred_at`;
- `payload_hash`, jamais le payload clair;
- `previous_hash` optionnel pour le chainage logique metier;
- `source_module`, `visibility`, `future_signature_status`.

Le contexte vault est porte par `BusinessEventVaultContext`:

- `vault_id`;
- `device_id`;
- `author_key_id`;
- `sequence`;
- `created_at`;
- `prev_device_event_hash` optionnel, au format hash vault hex sans prefixe.

## Sortie

`prepare_business_event_envelope(draft, context)` retourne une
`BusinessEventVaultEnvelope` contenant:

- une `body` canonique avec identifiants vault, sequence, device, auteur et
  chainage precedent;
- `business_draft_hash`, hash canonique du draft;
- `business_payload_hash`, seule preuve du payload metier;
- `canonical_hash`, hash `sha256:<hex>` de l'enveloppe sans auto-reference;
- `vault_event_hash`, meme hash sans prefixe, pratique pour un futur nommage
  append-only compatible vault.

L'enveloppe n'inclut pas `payload`, `clear_payload` ni `encrypted_payload`.
Le payload metier reste hors de cette passerelle.

## Limites V1

Cette couche ne remplace pas `coproscope.vault.core.append_event`. Elle prepare
un contrat stable pour brancher plus tard l'ecriture append-only, la signature
cryptographique et la resolution de sequence sans toucher aux routes UI.
