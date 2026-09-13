# Smoke routes UI locales

Ce smoke test couvre les routes principales de l'interface locale sur l'instance synthetique :

- `/`
- `/actions`
- `/documents`
- `/pieces`
- `/demandes`
- `/ag-contentieux`
- `/pilotage`
- `/gouvernance`
- `/depot`
- `/confidentialite`
- `/chantiers`

Le test `server/tests/test_ui_smoke_routes_expanded.py` construit une copie temporaire de `examples/synthetic_copro`, instancie l'application avec `FastAPI TestClient`, puis verifie :

- rendu HTTP 200 quand aucun token UI n'est configure ;
- presence d'un token fonctionnel propre a chaque page ;
- absence de fuite de contenu ou de noms de fichiers places dans `raw`, `restricted` et `logs` ;
- absence de chemins prives bruts vers le depot UI local dans le HTML rendu ;
- garde locale active quand `access_token` est configure : 403 sans token, 200 avec `?token=...`, en-tete `x-coproscope-token` ou cookie pose par la premiere requete autorisee.

Commande cible depuis `server/` :

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -p test_ui_smoke_routes_expanded.py -v
```

Le test reste volontairement externe a `app.py` : il valide le contrat public des routes sans modifier les routes ni les templates.
