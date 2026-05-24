# Integration route pilotage

## Perimetre

La page `/pilotage` est branchee dans l'application FastAPI locale sans modifier le calcul metier ni le viewmodel global.

- Route: `server/src/coproscope/web/app.py`
- Template rendu: `server/src/coproscope/web/templates/pilotage.html`
- Modele fourni au template: `coproscope.web.pilotage_view.build_pilotage_view`
- Lien de navigation: libelle novice `A surveiller`

## Securite locale

La route utilise le garde-fou de token existant:

- sans token configure, elle reste accessible comme les routes UI de demonstration;
- avec `access_token` configure dans `create_app`, `/pilotage` repond `403` sans token;
- avec `?token=...`, le rendu passe en `200` et la navigation conserve le token via `ui_token_query`.

## Limites

Cette integration ne branche pas encore de donnees indicateurs persistantes. La page affiche donc l'etat vide du modele `pilotage_view` tant qu'aucune carte issue de `pilotageops` n'est injectee.
