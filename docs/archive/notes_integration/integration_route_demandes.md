# Integration route demandes

## Perimetre

La page `/demandes` branche l'UI des demandes coproprietaires deja portee par `requests.html` et `coproscope.web.requests_view`.

Le routage reste volontairement minimal:

- `server/src/coproscope/web/app.py` expose `GET /demandes`.
- La route reutilise le controle de jeton local existant (`access_token`, query `token`, cookie `coproscope_ui_token`, entete `x-coproscope-token`).
- Le contexte passe au template est `context(request, "requests", **template_context(instance, year))`.
- `server/src/coproscope/web/templates/base.html` ajoute un lien de navigation novice vers `/demandes`.

## Donnees

Le modele `requests_view` lit les registres configures par `requestops`:

- registre des demandes;
- journal d'actions concret;
- statuts, canaux, preuves ou sources, rattachements et niveau de diffusion.

Aucune logique n'est ajoutee dans `viewmodel.py` et aucun style dedie n'est requis pour cette integration.

## Verification ciblee

Le test `server/tests/test_ui_requests_route.py` couvre:

- refus `403` sans jeton quand un jeton local est configure;
- rendu `200` avec jeton en query;
- conservation du jeton dans le lien de navigation;
- libelle novice dans la navigation;
- rendu du contenu principal issu de `requests.html` et du modele `requests_view`;
- acces avec l'entete `x-coproscope-token`.
