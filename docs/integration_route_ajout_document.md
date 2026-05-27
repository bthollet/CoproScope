# Integration route ajout de document

## Perimetre

La page `/documents/ajouter` est l'entree novice pour ajouter des documents au
coffre local. Elle branche l'ecran porte par `document_intake.html` et
`coproscope.web.document_intake_view`, puis reutilise le depot UI existant pour
recevoir les fichiers.

Le routage reste volontairement minimal:

- `server/src/coproscope/web/app.py` expose `GET /documents/ajouter`.
- `POST /depot` reste le seul point d'ecriture fichier; quand le formulaire
  envoie `return=document_intake`, il redirige vers
  `/documents/ajouter?depot=<id>&status=uploaded`.
- `POST /documents/ajouter/qualifier` enregistre uniquement des metadonnees
  locales par `doc_id`: type documentaire et confidentialite. Il n'accepte pas
  les noms de fichiers ni les chemins comme source d'autorite.
- `POST /documents/ajouter/rattacher` enregistre uniquement des libelles metier
  locaux par `doc_id`: point, action et preuve attendue. Il refuse les libelles
  qui ressemblent a un chemin local ou une URL.
- La route reutilise le controle de jeton local existant (`access_token`, query `token`, cookie `coproscope_ui_token`, entete `x-coproscope-token`).
- Le contexte passe au template est `context(request, "document_intake", **template_context(rows))`.
- `server/src/coproscope/web/templates/base.html` ajoute un lien novice clair: `Ajouter un document`.

## Donnees affichees

Sans depot selectionne, la page montre un etat vide actionnable: choisir un ou
plusieurs fichiers depuis ce poste. Avec `source=inbox`, elle lit le registre
documents local pour afficher une file de reconstruction deja deposee dans
l'inbox. Apres depot, elle affiche une ligne par fichier depose:

- libelle neutre `Fichier 1`, `Fichier 2`, etc. sans reprendre le nom local;
- `doc_id` opaque derive de l'empreinte si le pipeline n'a pas encore produit de
  doc_id;
- reference opaque `depot-local/<id>/fichier-<n>`;
- format, taille, empreinte courte;
- classification `A_CLASSER`;
- confidentialite `A_ARBITRER`;
- prochaine action lisible pour choisir le type, la diffusion et le rattachement
  `piece -> point -> action -> preuve`.

## Limites

Cette iteration reste volontairement locale: elle ne cree pas encore d'action
metier signee, ne modifie aucun fichier brut et ne compare pas encore le dossier
reconstruit au dossier reel. Elle prouve le couloir novice: depot, type,
confidentialite, rattachement `piece -> point -> action -> preuve`.

## Verification ciblee

Le test `server/tests/test_ui_document_intake_route.py` couvre:

- rendu `200` sans jeton quand aucun jeton local n'est configure;
- refus `403` sans jeton quand un jeton local est configure;
- rendu `200` avec jeton en query;
- conservation du jeton dans le lien de navigation;
- acces avec l'entete `x-coproscope-token`;
- rendu du template `document_intake.html` en etat vide novice;
- formulaire d'upload local vers `/depot`;
- redirection apres upload vers `/documents/ajouter?depot=<id>&status=uploaded`;
- affichage des fichiers deposes sans nom local ni chemin prive;
- absence de collision avec `/documents/{doc_id}`.
- rendu `/documents/ajouter?source=inbox` depuis le registre documents local;
- barre de progression et ligne par document candidat;
- absence de nom local, chemin prive et dossier `200_INBOX` dans la file inbox.
- persistance des choix type/confidentialite depuis depot et inbox;
- retour prudent `A_CLASSER` / `A_ARBITRER` pour les valeurs invalides.
- persistance du rattachement point/action/preuve depuis l'inbox;
- refus des libelles de rattachement qui ressemblent a des chemins prives.
