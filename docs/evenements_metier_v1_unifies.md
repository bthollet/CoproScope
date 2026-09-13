# Evenements metier V1 unifies

## Objectif

Les evenements metier V1 unifies servent de couche de liaison entre comptes,
demandes, actions, suggestions, resultats plugins et exports de passation.

Le module `coproscope.core.events_v1` produit uniquement des brouillons purs:
aucune ecriture dans le vault, aucun acces disque, aucune signature reelle. Le
hash du payload permet de preparer une future enveloppe signee sans exposer le
contenu metier brut.

## Modele

`BusinessEventDraft` contient les champs suivants:

| Champ | Role |
| --- | --- |
| `event_type` | Type metier stable en snake_case canonique, par exemple `request_created`. |
| `object_id` | Identifiant logique de l'objet principal. |
| `actor_ref` | Reference de compte ou role applicatif, jamais un nom/email. |
| `device_ref` | Reference logique du terminal ou runtime local. |
| `occurred_at` | Horodatage fourni par le producteur. |
| `payload_hash` | Hash `sha256:<hex>` du payload canonique filtre. |
| `previous_hash` | Hash optionnel de chainage logique. |
| `source_module` | Module producteur, par exemple `requestops`. |
| `visibility` | Diffusion normalisee: `conseil_syndical`, `copro`, `public_apres_expurgation` ou `non_diffusable`. |
| `future_signature_status` | Toujours `pending_future_signature` en V1. |

Un draft n'est pas une source de verite collaborative. Il est un contrat de
transition pour relier des objets deja normalises.

## Canonicalisation et hash

Le hash est calcule sur un JSON canonique:

- cles triees;
- separateurs compacts;
- encodage ASCII stable;
- dataclasses et mappings convertis en structures JSON;
- listes conservees dans leur ordre metier.

Deux payloads equivalents mais ordonnes differemment doivent produire le meme
`payload_hash`.

## Regles de minimisation

Les drafts ne transportent pas de payload brut. Les helpers construisent un
payload minimal, le valident, puis ne conservent que son hash.

Interdits dans les payloads et references:

- secrets, tokens, mots de passe, cles API;
- chemins locaux ou absolus;
- marqueurs `raw`;
- marqueurs `restricted`;
- emails et numeros de telephone;
- champs de type chemin (`path`, `local_path`, `absolute_path`, etc.).

Une visibilite restreinte venant d'un module amont est normalisee en
`non_diffusable` afin de ne pas propager le marqueur interdit.

## Helpers V1

Helpers requestops:

- `draft_from_requestops_request(...)` produit `request_created`;
- `draft_from_requestops_action(...)` produit `request_action_recorded`.

Helpers suggestionops:

- `draft_from_suggestionops_suggestion(...)` produit `suggestion_review_requested`;
- `draft_from_suggestionops_outcome(...)` produit `suggestion_outcome_prepared`.

Helper plugins:

- `draft_from_plugin_result(...)` produit `plugin_result_recorded` depuis un
  resultat deja prepare par `coproscope.plugins.results`.

Helper passation:

- `draft_from_passation_export_ref(...)` produit
  `passation_export_created` depuis les references diffusable d'un export
  derive.

Tous ces helpers demandent explicitement `actor_ref` et `device_ref`. Les dates
sont soit reprises de l'objet source, soit fournies par l'appelant lorsque
l'objet source n'en contient pas.

## Non-objectifs V1

La V1 ne fait pas:

- d'ecriture dans le vault reel;
- de signature cryptographique;
- de resolution de conflit;
- de stockage de payload brut;
- d'application metier automatique.

Ces responsabilites appartiennent aux couches vault, signature et application
future.
