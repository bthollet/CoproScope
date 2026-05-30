# QA UX, accessibilite et securite locale

Date de revue: 2026-05-20

## Axes verifies

- Parcours novice-friendly: les vues principales doivent expliquer quoi faire, pourquoi, quelle preuve regarder et quelle prudence de diffusion appliquer.
- Langage visible: utiliser `coffre` dans les textes utilisateur; reserver `vault` aux clefs, fichiers et docs techniques.
- Accessibilite: conserver lien d'evitement, landmarks, focus visible, aides clavier/tactile, labels accessibles, infobulles ou textes explicatifs proches.
- Routes gardees par token: quand un jeton local est configure, les vues principales, API et exports doivent refuser l'acces sans token.
- Exports passation derives: servir seulement des objets abstraits et expurges, jamais les bruts, dossiers restreints, logs, chemins prives ou mappings sensibles.
- Pack local: exclure `raw/`, `restricted/`, `logs/`, `private/`, secrets et cartes de correspondance.
- Strategie sync: exclure `.git/.venv/caches`, fichiers temporaires, logs, dossiers moteur et placeholders de fournisseur avant toute synchronisation.

## Tests automatises

- `server/tests/test_ui_accessibility_language.py`: contrat statique des textes visibles, aides, focus, registre de langage et absence de jargon primaire.
- `server/tests/test_security_no_private_sync_leaks.py`: contrat dynamique FastAPI pour token, routes privees, exports locaux/passation et profils sync.

Commande cible:

```powershell
$env:PYTHONPATH='server/src'
server\.venv\Scripts\python.exe -m unittest server.tests.test_ui_accessibility_language server.tests.test_security_no_private_sync_leaks
```

## Resultat cible du 2026-05-20

- Securite routes/exports/sync: OK sur le contrat ajoute.
- Accessibilite/aides novice: OK sur le contrat ajoute.
- Langage visible: echec attendu tant que le Cockpit contient encore `vault` en texte primaire dans `server/src/coproscope/web/templates/overview.html`.
- Correction produit attendue hors perimetre de cette passe: remplacer les libelles visibles `Vault`/`vault` par `Coffre`/`coffre`, en gardant `vault` seulement dans les references techniques.

## Points de revue manuelle

- Lire les ecrans Cockpit, Actions, Depot, Demandes, AG/contentieux, Pilotage et Gouvernance comme un membre novice du conseil syndical.
- Verifier que chaque table a un titre, une introduction ou une legende utile.
- Controler que les boutons d'export annoncent clairement le perimetre exporte et ne suggerent pas une publication externe.
- Tester la navigation clavier: Tab, Entree, focus visible et retour au contenu principal.
