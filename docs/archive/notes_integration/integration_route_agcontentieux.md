# Integration route AG/contentieux/passation

## Perimetre

La page `/ag-contentieux` branche l'UI AG/contentieux/passation deja portee par `agcontentieux.html` et `coproscope.web.agcontentieux_view`.

Le routage reste volontairement minimal:

- `server/src/coproscope/web/app.py` expose `GET /ag-contentieux`.
- La route reutilise le controle de jeton local existant (`access_token`, query `token`, cookie `coproscope_ui_token`, entete `x-coproscope-token`).
- Le contexte passe au template est `context(request, "agcontentieux", agcontentieux=build_agcontentieux_passation_view(instance, year))`.
- `server/src/coproscope/web/templates/base.html` ajoute un lien de navigation novice vers `/ag-contentieux`.

## Donnees

Le modele `agcontentieux_view` lit les registres deja disponibles pour composer:

- les questions AG;
- les pieces de convocation;
- les dossiers contentieux factuels;
- les preuves et sources;
- la checklist de passation.

Aucune logique n'est ajoutee dans `viewmodel.py` et aucun style dedie n'est requis pour cette integration.

## Verification ciblee

Le test `server/tests/test_ui_agcontentieux_route.py` couvre:

- rendu `200` sans jeton quand aucun jeton local n'est configure;
- refus `403` sans jeton quand un jeton local est configure;
- rendu `200` avec jeton en query;
- conservation du jeton dans le lien de navigation;
- libelle novice dans la navigation;
- rendu du contenu principal issu de `agcontentieux.html` et du modele `agcontentieux_view`;
- acces avec l'entete `x-coproscope-token`.
