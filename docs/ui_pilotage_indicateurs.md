# UI pilotage indicateurs

Date de reference: 2026-05-20

Cette note decrit la couche UI ajoutee apres `pilotageops`. Elle ne cree pas de route globale et ne modifie pas le calcul metier: elle prepare seulement un modele de vue et un template pour afficher des cartes indicateurs deja composees par `pilotageops`.

## Objectif

L'ecran doit aider un conseil syndical novice a lire une carte sans connaitre la formule. Chaque carte affiche:

- domaine;
- periode;
- preuve ou source;
- seuil;
- statut;
- prochaine action;
- diffusion;
- rattachement a un point ou a une action.

## Modele de vue

`coproscope.web.pilotage_view.build_pilotage_view` accepte des `PilotageCard` ou des dictionnaires issus de `pilotageops.card_to_dict`.

La couche UI ajoute uniquement:

- des libelles novices pour les statuts;
- des libelles de domaines et de diffusion;
- un champ `proof_source` lisible;
- un champ `attachment_label` pour point/action;
- des compteurs de synthese;
- un etat vide utile.

Elle ne recalcule pas le statut, le seuil ou la prochaine action.

## Template

`web/templates/pilotage.html` est pret a etre branche par une route future ou inclus par une page existante. Il attend une variable `pilotage`, ou `model.pilotage` si la route utilise deja un modele global.

L'etat vide explique que les indicateurs ne sont pas encore alimentes et indique la prochaine etape: produire une carte avec `build_pilotage_card`, puis la rattacher a un point ou a une action.

## Garde-fous

- Pas de route globale ajoutee dans cette livraison.
- Pas de modification de `pilotageops`.
- Pas de masquage silencieux: une preuve manquante reste affichee comme `preuve manquante`.
- Le vocabulaire reste stable: domaine, periode, preuve, source, seuil, statut, prochaine action, diffusion, rattachement.
- Le rattachement point/action reste visible pour eviter les cartes orphelines.

## Verification

Les tests statiques et modele couvrent:

- preparation des champs affiches;
- acceptation des dictionnaires issus de `pilotageops`;
- etat vide novice;
- rendu Jinja du template;
- absence de decorateur de route dans la couche UI.
