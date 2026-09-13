# Nomenclature evenements V1

## Objectif

La V1 stable utilise uniquement des `event_type` en `snake_case` ASCII,
minuscules, sans point ni separateur ambigu. Cette nomenclature sert de
reference commune pour les futurs evenements signes et pour les projections
metier; elle ne branche aucune integration vault par elle-meme.

Le module de reference est `coproscope.core.event_types`.

## Regles de nommage

- Un type canonique est une chaine `snake_case` connue de `EVENT_TYPES_V1`.
- Les points, tirets, espaces, slashs, deux-points et backslashes sont refuses.
- Les variantes en majuscules, camelCase, PascalCase ou avec doubles `_` sont
  refusees.
- `normalize_event_type(...)` accepte seulement un type V1 canonique connu.
- `validate_event_type(...)` retourne `True` si le type est canonique, sinon
  leve `ValueError`.
- `migrate_legacy_event_type(...)` est le seul helper autorise a convertir une
  ancienne valeur connue avant validation.

## Types V1 canoniques

| Constante Python | Valeur `event_type` | Objet principal |
| --- | --- | --- |
| `VAULT_INITIALIZED` | `vault_initialized` | `vault` |
| `MEMBER_INVITED` | `member_invited` | `member` |
| `MEMBER_REVOKED` | `member_revoked` | `member` |
| `RECOVERY_KEY_REGISTERED` | `recovery_key_registered` | `key_recovery` |
| `KEY_RECOVERY_PERFORMED` | `key_recovery_performed` | `key_recovery` |
| `ARCHIVE_DOWNLOADED` | `archive_downloaded` | `replica` |
| `ARCHIVE_INTEGRITY_VERIFIED` | `archive_integrity_verified` | `replica` |
| `REPLICA_REGISTERED` | `replica_registered` | `replica` |
| `REPLICA_CHECKED` | `replica_checked` | `replica` |
| `DOCUMENT_ADDED` | `document_added` | `document` |
| `DOCUMENT_VERSION_ADDED` | `document_version_added` | `document` |
| `OCR_COMPLETED` | `ocr_completed` | `plugin_run` |
| `CLASSIFICATION_COMPLETED` | `classification_completed` | `document` |
| `COMMENT_ADDED` | `comment_added` | `proof` |
| `POINT_CREATED` | `point_created` | `point` |
| `ACTION_CREATED` | `action_created` | `action` |
| `REQUEST_CREATED` | `request_created` | `request` |
| `REQUEST_ACTION_RECORDED` | `request_action_recorded` | `request_action` |
| `STATUS_CHANGED` | `status_changed` | objet cible |
| `DIFFUSION_DECIDED` | `diffusion_decided` | `privacy_review` |
| `REDACTION_COMPLETED` | `redaction_completed` | `proof_capsule` |
| `EXPORT_CREATED` | `export_created` | `proof_capsule` |
| `PASSATION_EXPORT_CREATED` | `passation_export_created` | `passation_export` |
| `SUGGESTION_REVIEW_REQUESTED` | `suggestion_review_requested` | `suggestion` |
| `SUGGESTION_OUTCOME_PREPARED` | `suggestion_outcome_prepared` | `suggestion` |
| `PDF_ANNOTATION_CREATED` | `pdf_annotation_created` | `annotation` |
| `PLUGIN_ACTIVATED` | `plugin_activated` | `plugin_run` |
| `PLUGIN_RESULT_RECORDED` | `plugin_result_recorded` | `plugin_run` |
| `MIGRATION_RECORDED` | `migration_recorded` | `migration` |

## Compatibilite migration

Les anciens brouillons peuvent contenir `plugin.result_recorded`. Cette valeur
n'est pas un type V1 stable et doit etre rejetee par `normalize_event_type(...)`
et `validate_event_type(...)`.

Lors d'une migration explicite, convertir avant validation:

| Ancien type | Type V1 |
| --- | --- |
| `plugin.result_recorded` | `plugin_result_recorded` |
| `passation.export_ref_created` | `passation_export_created` |
| `request.normalized` | `request_created` |
| `request.action` | `request_action_recorded` |
| `request.action_recorded` | `request_action_recorded` |
| `suggestion.review_requested` | `suggestion_review_requested` |
| `suggestion.outcome_prepared` | `suggestion_outcome_prepared` |

La compatibilite doit rester visible et bornee: un import historique peut
appeler `migrate_legacy_event_type(...)`, mais le stockage V1 ne doit persister
que les valeurs canoniques en `snake_case`.

## Hors scope

Cette nomenclature ne modifie pas les producteurs existants, ne cree pas
d'evenement signe et ne change pas les projections UI. Toute integration future
doit d'abord passer par les helpers de validation puis ajouter ses propres
tests de flux.
