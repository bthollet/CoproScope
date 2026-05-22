# UI AG, contentieux, passation

Cette passe ajoute une surface UI prete a brancher pour preparer une assemblee generale, suivre un dossier contentieux factuel et transmettre un pack de passation. Elle ne modifie pas les routes globales: le branchement futur devra appeler `build_agcontentieux_passation_view(instance, year)` et rendre `agcontentieux.html` avec la cle de contexte `agcontentieux`.

## Objectif novice

La page explique le parcours en mots simples:

- une question AG transforme une convocation, une annexe ou une decision en point a traiter;
- une piece de convocation indique la source, la preuve, le statut et ce qui reste a verifier;
- un dossier contentieux reste factuel, restreint et separe;
- une note de risque non juridique liste des constats, signaux et pieces a verifier sans avis juridique automatique;
- chaque preuve ou source affiche sa restriction, sa diffusion, sa prochaine action, son echeance et son statut;
- le pack passation rassemble les points ouverts et conserve la restriction la plus forte.

## Modele de vue

Fichier: `server/src/coproscope/web/agcontentieux_view.py`

Entree:

- `InstanceConfig`;
- exercice UI;
- registres disponibles: documents, AG et registre decision-action-preuve si present.

Sortie principale:

- `summary`: compteurs questions, pieces, dossiers contentieux, notes de risque, preuves, echeances et etat vide;
- `ag`: dossiers, questions AG, pieces de convocation;
- `contentieux`: dossiers factuels et notes de risque non juridiques;
- `evidence`: preuves et sources derivees des documents;
- `passation`: pack passation et checklist;
- `labels`: traductions UI des statuts, restrictions et diffusions.

Le modele n'expose pas les chemins bruts locaux. Il privilegie `doc_id`, nom de fichier, type de document, date et empreinte courte.

## Template

Fichier: `server/src/coproscope/web/templates/agcontentieux.html`

Sections:

- bandeau et compteurs;
- etat vide explicite;
- cartes de parcours: question AG, piece de convocation, dossier contentieux, note de risque, pack passation;
- tableaux questions, pieces, contentieux, notes, preuves;
- panneau pack passation et checklist.

Le template reutilise les classes existantes (`band`, `kpi-grid`, `next-action-card`, `panel`, `badge`, `table-band`) afin de rester compatible avec l'interface actuelle sans toucher a `styles.css`.

## Branchements futurs

Quand l'ownership de `app.py` sera ouvert, ajouter une route du type:

```python
from .agcontentieux_view import build_agcontentieux_passation_view

@app.get("/ag-contentieux", response_class=HTMLResponse)
def agcontentieux_page(request: FastAPIRequest):
    return templates.TemplateResponse(
        request=request,
        name="agcontentieux.html",
        context=context(
            request,
            "agcontentieux",
            agcontentieux=build_agcontentieux_passation_view(instance, year),
        ),
    )
```

Un ajout de navigation pourra ensuite etre traite dans `base.html`, hors de cette passe.

## Garde-fous

- Pas d'avis juridique automatique.
- Pas de diffusion large par defaut pour le contentieux.
- Les dossiers sensibles restent au niveau `confidentiel` et `conseil syndical`.
- Le pack passation indique les points ouverts au lieu de remplacer les sources.
- L'etat vide dit quoi deposer ou rattacher avant de promettre une analyse.
