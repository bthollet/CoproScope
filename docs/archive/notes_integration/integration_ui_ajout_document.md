# UI ajout de document

Ce lot ajoute une surface UI testable pour le runtime `document_intake` et son
branchement novice sur le depot local.

## Pieces livrees

- `server/src/coproscope/web/document_intake_view.py` expose `build_document_intake_view` et `template_context`.
- `server/src/coproscope/web/templates/document_intake.html` affiche le modele pret a brancher.
- `server/src/coproscope/web/_app_fragments/part_003.pyfrag` expose `GET /documents/ajouter`.
- `server/src/coproscope/web/_app_fragments/part_004.pyfrag` renvoie vers cette page quand le depot vient du parcours ajout document.
- `server/tests/test_ui_document_intake.py` couvre le modele et le rendu Jinja.
- `server/tests/test_ui_document_intake_route.py` couvre la route et le retour apres upload.

## Parcours couvert

L'ecran guide un utilisateur novice dans l'ordre suivant:

1. Deposer localement avec une reference opaque et une empreinte locale.
2. Classer le document, ou garder `A_CLASSER` si le type reste incertain.
3. Controler la confidentialite: `DIFFUSABLE_BRUT`, `A_BIFFER`, `RESERVE_CS`, `BLOQUE` ou `A_ARBITRER`.
4. Rattacher la chaine `piece -> point -> action -> preuve`.
5. Afficher le statut runtime et la prochaine action issue de `build_runtime_checklist`.

## Iteration novice livree

Un coproprietaire novice peut maintenant:

1. ouvrir `Ajouter un document`;
2. choisir un ou plusieurs fichiers depuis ce poste;
3. declencher le depot local existant;
4. revenir automatiquement sur `Ajouter un document` avec les fichiers deposes;
5. voir que le type reste `A_CLASSER`, que la confidentialite est `A_ARBITRER`
   et que le rattachement `piece -> point -> action -> preuve` reste a faire.

## Iteration reconstruction inbox

Pour la simulation Beauvallon, la meme page peut afficher une file issue du
registre `documents` de l'instance de reconstruction avec:

- URL locale: `/documents/ajouter?source=inbox`;
- barre de progression de qualification;
- une ligne par document candidat;
- reference stable `inbox-reconstruction:<doc_id>`;
- libelles neutres `Fichier inbox 1`, `Fichier inbox 2`, etc.;
- absence de nom de fichier local, chemin prive ou dossier `200_INBOX` dans le rendu.

## Iteration qualification persistante

Chaque ligne peut maintenant enregistrer localement:

- le type documentaire choisi ou `A_CLASSER`;
- la confidentialite choisie ou `A_ARBITRER`;
- la progression calculee depuis les controles requis.

Le POST `/documents/ajouter/qualifier` persiste par `doc_id` dans le manifeste
du depot ou dans le registre `documents` de l'inbox reconstruction. Les valeurs
non allowlistees retombent sur les choix prudents.

## Iteration rattachement local

Chaque ligne qualifiee peut maintenant enregistrer le lien metier:

- point concerne: AG, decision, demande, facture, incident, chantier,
  contentieux ou preuve libre;
- action attendue: verifier, demander, relancer, biffer, transmettre ou classer;
- preuve attendue: presence, decision, reception, execution, paiement, refus ou
  cloture.

Le POST `/documents/ajouter/rattacher` persiste uniquement ces libelles metier
par `doc_id`, dans le manifeste du depot ou dans le registre `documents`. Les
libelles ressemblant a des chemins locaux ou URLs sont rejetes avant ecriture.

## Contrat confidentialite

- Aucun nom reel ou nom de fichier local ne doit etre affiche dans la page de
  retour novice.
- Aucun chemin prive ne doit etre affiche.
- Aucun raw dans cloud: un brut cible cloud bloque le parcours avant export ou partage.
- Les chemins locaux, URLs et indices personnels sont masques avant rendu.
- Le template montre seulement doc_id, reference opaque, statut, empreinte courte, checklist et rattachement metier.

## Branchement

La route appelle:

```python
from coproscope.web.document_intake_view import build_document_intake_view

document_intake = build_document_intake_view(rows)
```

Puis rend `document_intake.html` avec `document_intake=document_intake`.

## Tests cibles

Commande recommandee depuis la racine du depot:

```powershell
.\server\.venv\Scripts\python.exe -m unittest server.tests.test_ui_document_intake server.tests.test_ui_document_intake_route -v
```
