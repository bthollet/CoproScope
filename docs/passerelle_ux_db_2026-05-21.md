# Passerelle UX <-> Base de donnees - 2026-05-21

## Pourquoi ce fichier existe

Ce fichier sert de point de rencontre entre le fil courant de refonte UX et le futur fil sur la structure de base de donnees.

Regle simple:
- le fil UX ecrit ses besoins dans `coproscope/docs/passerelle_ux_vers_db_2026-05-21.md`;
- le fil DB repond dans `coproscope/docs/passerelle_db_vers_ux_2026-05-21.md`;
- chaque fil evite de reecrire le fichier principal de l'autre sans raison;
- les decisions communes doivent citer le fichier source, la date locale, et le bloc UX concerne.

## Etat courant a transmettre

- Produit local: `http://127.0.0.1:8766/?token=local-secret`.
- Instance de test par defaut: `C:\Users\brice\Documents\CoproScope\instances\beauvallon_test` (`beauvallon-test`).
- Instance Platanes: `coproscope/examples/synthetic_copro`, reservee aux tests publics/CI et exemples partageables.
- Suite UI complete: `150 tests OK` au dernier passage TestClient.
- Contrat principal: l'interface consomme des projections `model.ux.*`; la DB doit aider a stabiliser ces projections, pas imposer un schema directement au template.
- Attention live: un ecart de reload est en cours sur `/actions/{id}` pour le cas action inconnue. Les tests source sont verts; ne pas prendre ce comportement live comme contrat DB tant que le point de coordination ne dit pas "live aligne".

## Convention d'echange

Format recommande pour une question UX vers DB:

```md
### Question UXDB-YYYYMMDD-NN - Titre court

- Bloc UX:
- Route/ecran:
- Besoin utilisateur:
- Projection attendue `model.ux.*`:
- Donnees minimales:
- Donnees privees a ne jamais exposer:
- Reponse attendue du fil DB:
```

Format recommande pour une reponse DB vers UX:

```md
### Reponse UXDB-YYYYMMDD-NN - Titre court

- Decision schema:
- Tables/collections concernees:
- Champs publics exposes au viewmodel:
- Champs prives conserves hors UI:
- Migration ou import fictif necessaire:
- Risques:
- Impact pour les tests UX:
```

## Priorites DB issues de l'UX

1. Tracabilite decision -> action -> preuve -> relance.
2. Pieces manquantes exploitables: detenteur, raison, ecran d'origine, relance possible, depot possible.
3. Comptes: anomalie -> question syndic -> piece attendue -> preuve recue.
4. Memoire copropriete: evenement -> documents -> sujets ouverts -> passation.
5. Export passation: seulement derive, filtrable, sans chemins raw/restricted/logs/private.

## Fichiers utiles pour l'autre fil

- `coproscope/docs/passerelle_ux_vers_db_2026-05-21.md`
- `coproscope/docs/passerelle_db_vers_ux_2026-05-21.md`
- `coproscope/docs/refonte_ux_cycles_image_dev_test.md`
- `coproscope/docs/coordination_cycle_n2_pieces_detail_2026-05-21.md`
- `coproscope/docs/point_coordination_live_8766_2026-05-21.md`
- `coproscope/docs/journal_cycles_ux_2026-05-21.md`
- `coproscope/server/src/coproscope/web/viewmodel.py`
- `coproscope/server/src/coproscope/web/app.py`
- `coproscope/server/tests/test_ui_action_detail_route.py`
- `coproscope/server/tests/test_ui_pieces_viewmodel.py`
- `coproscope/server/tests/test_ui_registre_actions.py`
