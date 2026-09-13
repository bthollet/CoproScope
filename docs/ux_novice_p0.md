# UX novice P0

Date de reference: 2026-05-20

Lot L1: formaliser une grille de langage pour publics neophytes copro et la bloquer par tests statiques, sans modifier les templates.

## Objectif

Un utilisateur novice doit comprendre en moins de quelques secondes:

- ou il se trouve: coffre local, role ou contexte actif;
- ce qui demande attention: preuve, source ou piece a regarder;
- ce qu'il faut faire: prochaine action concrete;
- ce qui peut etre partage: diffusion, restriction ou masquage;
- ce qui reste local: depot, export prepare, sync non automatique.

## Garde-fous P0

| Axe | Regle de premier niveau | No-go |
|---|---|---|
| Coffre | Dire `coffre`, `coffre local` ou `coffre chiffre`. | Dire seulement `vault`. |
| Sync | Dire `synchronisation`, `sync externe`, `a verifier`, `ne synchronise rien`. | Laisser croire a une publication cloud automatique. |
| Role | Dire `role`, `mandat`, `qui agit`, avec droits ou public. | Utiliser ACL/RBAC sans explication. |
| Preuve | Dire `preuve de quoi`, `source`, `justificatif`. | Clore un sujet sans preuve rattachee. |
| Action | Dire `prochaine action`, `action attendue`, responsable ou suite. | Bouton vague: `OK`, `Executer`, `Valider` sans consequence. |
| Infobulle | Expliquer en une phrase, accessible clavier/tactile. | Mettre une definition indispensable uniquement au survol souris. |
| Registre | Novice d'abord, CS ensuite, technique replie. | Faire porter la comprehension par des noms de modules. |

## Perimetre L1

Ecritures autorisees:

- `docs/ux_novice_p0.md`;
- `docs/registre_langage_ui.md`;
- `server/tests/test_ui_novice_language_static.py`.

Les templates existants sont lus pour verification statique seulement. Ce lot ne modifie pas `document_intake.html`, ne touche pas `annotationops`, et ne modifie pas les tests QA reserves a Sagan.

## Templates cibles en lecture

- `server/src/coproscope/web/templates/base.html`
- `server/src/coproscope/web/templates/_context_banner.html`
- `server/src/coproscope/web/templates/overview.html`
- `server/src/coproscope/web/templates/governance.html`
- `server/src/coproscope/web/templates/depot.html`
- `server/src/coproscope/web/templates/actions.html`
- `server/src/coproscope/web/templates/pieces.html`
- `server/src/coproscope/web/templates/requests.html`
- `server/src/coproscope/web/templates/agcontentieux.html`

Ces templates portent deja des ancres utiles: contexte du coffre local, role et synchronisation, prochaine action, preuve/source, prudence de diffusion, depot local et absence de sync cloud automatique.

## Definition de texte primaire

Le test statique regarde le texte visible ou accessible le plus expose:

- titres `h1`, `h2`, `h3`;
- liens, boutons, libelles de cartes et badges;
- `aria-label`, `title`, `alt`, `placeholder`;
- textes de cartes de prochaine action;
- aides courtes dans les zones `hint`, `lead`, `small`, `caption`.

Le code Jinja, les noms de variables, les routes et les chemins techniques ne sont pas analyses comme texte primaire.

## Checklist de revue novice

- Le haut de page dit ce qu'on peut faire maintenant.
- Le coffre ou le contexte local est visible avant une action sensible.
- Un statut sync indique clairement local, externe, a verifier ou sans publication.
- Une fiche importante contient `Pourquoi`, `Preuve / source`, `Prochaine action` et `Prudence diffusion`.
- Les mots courts ou techniques ont une micro-definition proche.
- Les boutons nomment la consequence de l'action.
- Les exports et depots ne promettent pas de synchronisation cloud.
- Les restrictions disent qui peut voir quoi et pourquoi.
- Les priorites P1/P2 ne sont jamais le seul niveau de comprehension.
- Les details techniques peuvent rester, mais ne portent pas seuls la decision.

## Tests cibles

Commande depuis `server/`:

```powershell
.\.venv\Scripts\python.exe -m unittest tests.test_ui_novice_language_static -v
```

Le test est volontairement statique: il verrouille le contrat de langage sans forcer une refonte des templates pendant que d'autres agents travaillent dessus.
