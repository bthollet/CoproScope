# Integration route ajout de document

## Perimetre

La page `/documents/ajouter` branche l'ecran de preparation deja porte par `document_intake.html` et `coproscope.web.document_intake_view`.

Le routage reste volontairement minimal:

- `server/src/coproscope/web/app.py` expose `GET /documents/ajouter`.
- La route reutilise le controle de jeton local existant (`access_token`, query `token`, cookie `coproscope_ui_token`, entete `x-coproscope-token`).
- Le contexte passe au template est `context(request, "document_intake", **template_context(rows))`.
- `server/src/coproscope/web/templates/base.html` ajoute un lien novice clair: `Ajouter un document`.

## Donnees affichees

La route fournit des lignes synthetiques de preparation, sans lecture de fichier et sans upload reel:

- un PV d'AG pret a relier a un point;
- une facture encore a arbitrer cote confidentialite;
- un devis qui exige une version biffee avant diffusion.

Ces donnees servent de fallback pour montrer le contrat de branchement: reference opaque locale, empreinte, classification, confidentialite, puis rattachement `piece -> point -> action -> preuve`.

## Limites

Cette integration ne cree pas de workflow d'upload.

Elle ne declare aucun `POST`, ne lit aucun fichier utilisateur, ne stocke aucun brut, et ne synchronise aucun raw vers un cloud. Le branchement futur devra remplacer les lignes synthetiques par les sorties du depot local ou d'un formulaire explicite, en gardant le meme contrat de confidentialite.

## Verification ciblee

Le test `server/tests/test_ui_document_intake_route.py` couvre:

- rendu `200` sans jeton quand aucun jeton local n'est configure;
- refus `403` sans jeton quand un jeton local est configure;
- rendu `200` avec jeton en query;
- conservation du jeton dans le lien de navigation;
- acces avec l'entete `x-coproscope-token`;
- rendu du template `document_intake.html` avec donnees synthetiques;
- absence de formulaire d'upload reel;
- absence de collision avec `/documents/{doc_id}`.
