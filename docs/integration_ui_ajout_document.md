# UI ajout de document

Ce lot ajoute une surface UI testable pour le runtime `document_intake`.

Frontiere d'integration: sans modifier app.py et sans modifier base.html.

## Pieces livrees

- `server/src/coproscope/web/document_intake_view.py` expose `build_document_intake_view` et `template_context`.
- `server/src/coproscope/web/templates/document_intake.html` affiche le modele pret a brancher.
- `server/tests/test_ui_document_intake.py` couvre le modele, le rendu Jinja et la frontiere sans route.

## Parcours couvert

L'ecran guide un utilisateur novice dans l'ordre suivant:

1. Deposer localement avec une reference opaque et une empreinte locale.
2. Classer le document, ou garder `A_CLASSER` si le type reste incertain.
3. Controler la confidentialite: `DIFFUSABLE_BRUT`, `A_BIFFER`, `RESERVE_CS`, `BLOQUE` ou `A_ARBITRER`.
4. Rattacher la chaine `piece -> point -> action -> preuve`.
5. Afficher le statut runtime et la prochaine action issue de `build_runtime_checklist`.

## Contrat confidentialite

- Aucun nom reel ne doit etre affiche.
- Aucun chemin prive ne doit etre affiche.
- Aucun raw dans cloud: un brut cible cloud bloque le parcours avant export ou partage.
- Les chemins locaux, URLs et indices personnels sont masques avant rendu.
- Le template montre seulement doc_id, reference opaque, statut, empreinte courte, checklist et rattachement metier.

## Branchement futur

Une route future peut appeler:

```python
from coproscope.web.document_intake_view import build_document_intake_view

document_intake = build_document_intake_view(rows)
```

Puis rendre `document_intake.html` avec `document_intake=document_intake`.

La couche actuelle ne declare aucune route FastAPI et ne depend pas de l'application globale. Elle peut donc etre integree sans conflit dans `app.py` plus tard.

## Tests cibles

Commande recommandee depuis la racine du depot:

```powershell
python -m pytest server\tests\test_ui_document_intake.py
```
