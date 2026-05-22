# UI demandes coproprietaires

## Objectif

Cette page prepare l'interface des demandes coproprietaires multi-canaux apres `requestops`.
Elle ne branche pas encore de route dans `app.py`: le perimetre livre ici est un modele de vue,
un template et des tests statiques/modele, prets a raccorder plus tard.

La vue doit aider une personne novice a repondre a quatre questions simples:

- d'ou vient la demande, via le champ `canal`: email, oral, courrier, assemblee generale, portail syndic, document ou incident;
- de quoi parle la demande, avec quelle preuve/source locale;
- ou en est le statut et quelle est la prochaine action concrete;
- qui peut voir la synthese et a quel point/action elle est rattachee.

## Modele de vue

`server/src/coproscope/web/requests_view.py` lit:

- le registre `requestops.request_register_path(instance)`;
- le journal `requestops.request_action_log_path(instance)`.

Il retourne un dictionnaire centre sur `requests`, avec:

- `summary`: total, demandes ouvertes, preuves a rattacher, demandes non rattachees, actions journalisees;
- `status_counts`, `channel_counts`, `visibility_counts`: compteurs deja traduits pour l'UI;
- `rows`: demandes affichees, triees pour remonter relances et nouvelles demandes;
- `open_rows`: cartes de prochaines actions;
- `unlinked_rows`: demandes sans rattachement point/action;
- `empty_state`: etat vide utile quand aucun registre n'est encore charge;
- `novice_steps`: trois reperes courts pour comprendre le flux.

Les codes techniques de `requestops` sont traduits en texte novice: `a_qualifier` devient
`a qualifier`, `portail_syndic` devient `portail syndic`, `conseil_syndical` devient
`conseil syndical`.

## Template

`server/src/coproscope/web/templates/requests.html` attend une variable `requests`.
Il affiche:

- une bande KPI;
- un mode d'emploi court;
- les canaux d'arrivee;
- les statuts et niveaux de diffusion;
- les demandes ouvertes avec preuve/source, prochaine action, diffusion et rattachement;
- le registre complet des demandes;
- le journal d'actions concret;
- la liste des demandes a rattacher.

Le template reste volontairement compatible avec `base.html` et `styles.css` existants, sans
modification de ces fichiers. Il reutilise les classes deja presentes: `band`, `panel`,
`novice-card`, `next-action-card`, `timeline`, `badge`, `pill`, `empty`.

## Raccordement futur

Quand le perimetre de routage sera ouvert, la route pourra ressembler a ceci:

```python
@app.get("/demandes", response_class=HTMLResponse)
def requests_page(request: FastAPIRequest):
    from .requests_view import build_requests_view

    return templates.TemplateResponse(
        request=request,
        name="requests.html",
        context=context(
            request,
            "requests",
            requests=build_requests_view(instance, year),
        ),
    )
```

Il faudra aussi ajouter le lien de navigation dans `base.html` a ce moment-la, mais ce n'est
pas fait ici pour respecter le perimetre strict.

## Limites

- Aucun connecteur email, portail syndic ou messagerie.
- Aucun changement de `app.py`, `base.html`, `styles.css` ou `viewmodel.py`.
- Aucun export specifique demandes.
- Le modele accepte un registre vide et affiche un etat vide utile au lieu de masquer la page.
- Le journal d'actions concret depend du fichier local `journal_demandes_coproprietaires.csv`.
