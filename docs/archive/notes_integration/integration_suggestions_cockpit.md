# Integration suggestions cockpit

Date de reference: 2026-05-20

Cette note prepare le raccordement futur des suggestions d'amelioration au
cockpit conseil syndical. Elle ne modifie pas le cockpit existant: elle decrit
le contrat produit par `coproscope.modules.suggestionview`.

## Objectif

Transformer des `ImprovementSuggestion` de `suggestionops` en cartes deja
lisibles par une interface:

- titre;
- pourquoi;
- preuve et source;
- prochaine action;
- diffusion;
- confiance;
- effort;
- destination cible: `action`, `demande`, `point`, `indicateur` ou `export`.

La couche `suggestionview` est un adaptateur de lecture. Elle ne persiste rien,
ne cree pas de `SuggestionOutcome`, ne modifie aucun registre et ne declenche
aucun effet automatique.

## Entrees

`build_suggestion_cards(suggestions, reviews)` accepte:

- des `ImprovementSuggestion` ou des mappings compatibles
  `normalize_suggestion`;
- des `SuggestionReview` ou des mappings compatibles `normalize_review`.

Les revues sont utilisees uniquement pour verifier qu'une suggestion a ete
acceptee par un humain et pour choisir la destination de la carte.

## Filtres appliques

Une carte est produite seulement si:

- la suggestion est encore au statut `a_revoir`;
- `title`, `why`, `proof`, `source`, `next_action`, `public`, `confidence` et
  `effort` sont renseignes;
- une revue correspondante est en decision `accepted`;
- la revue acceptee contient les informations exigees par `suggestionops`
  pour une transformation humaine;
- la destination selectionnee est autorisee par les transformations de la
  suggestion.

Les suggestions sans preuve, sans source, rejetees, en attente, a completer,
deja ecartees ou deja transformees ne remontent pas dans les cartes cockpit.

## Sortie

Chaque `SuggestionUICard` contient:

| Champ | Usage cockpit |
|---|---|
| `card_id` | Identifiant stable pour l'affichage |
| `suggestion_id` | Lien vers la suggestion source |
| `review_id` | Lien vers la revue humaine acceptee |
| `title` | Titre court de la carte |
| `why` | Raison d'attention |
| `proof` | Reference de preuve |
| `source` | Module ou registre producteur |
| `evidence` | Libelle compose `source - proof` |
| `next_action` | Prochaine action humaine proposee |
| `diffusion` | Public de diffusion issu de la revue ou de la suggestion |
| `confidence` | Niveau de confiance textuel |
| `effort` | Effort estime textuel |
| `destination` | Type cible technique |
| `destination_label` | Libelle affichable |
| `available_destinations` | Destinations acceptables |
| `automatic_effect` | Toujours `False` |

`suggestion_cards_to_dicts` permet une serialisation directe pour une future
vue ou API.

## Garde-fous

- Le cockpit futur devra traiter la carte comme une intention d'affichage, pas
  comme un ordre.
- Le bouton de transformation, s'il est ajoute plus tard, devra appeler une
  action explicite separee et reconstruire/verifier la revue.
- Les exports restent soumis a une revue de diffusion et, si necessaire, a un
  passage PrivacyOps/BiffageOps.
- Les cartes ne remplacent pas l'historique: la source de verite reste la
  suggestion, sa revue et les futurs evenements ou registres metier.

## Tests cibles

Les tests dedies vivent dans `server/tests/test_suggestionview.py` et couvrent:

- construction d'une carte complete;
- filtrage des suggestions non sourcees ou non acceptees;
- rejet des suggestions ecartees;
- refus d'une destination non autorisee;
- choix d'une destination par defaut quand la revue n'en selectionne pas;
- export dictionnaire sans `outcome_id` ni `payload` metier.
