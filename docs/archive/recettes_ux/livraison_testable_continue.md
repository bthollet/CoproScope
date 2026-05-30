# Livraison testable continue

Date de reference: 2026-05-20.

Note 2026-05-21: cette note reste une trace historique Platanes. Pour les
recettes live locales actuelles, l'environnement de test par defaut est
`C:\Users\brice\CoproScope\instances\beauvallon_test`.

Cette note fige un lot QA de livraison testable continue. Elle decrit ce qui peut etre demarre, visite et verifie sur l'environnement local de test, sans revendiquer une recette navigateur deja faite ni une validation de diffusion publique.

## Contrat de lancement visible

Commande serveur autorisee pour une demo ou une recette locale:

```powershell
cd C:\Users\brice\CoproScope\coproscope
.\server\.venv\Scripts\python.exe -m coproscope.cli ui open-test --instance-root C:\Users\brice\CoproScope\instances\beauvallon_test --year 2025 --host 127.0.0.1 --port 8766 --token beauvallon-test-local
```

Commande publique/CI equivalente, sans donnee locale privee:

```powershell
cd C:\Users\brice\CoproScope\coproscope
.\server\.venv\Scripts\python.exe -m coproscope.cli ui open-test --instance-root .\examples\synthetic_copro --year 2025 --host 127.0.0.1 --port 8769 --token qa-livraison-continue-local
```

Comportement attendu:

- serveur visible au premier plan dans le terminal;
- arret manuel par `Ctrl+C`;
- URL tokenisee affichee dans la sortie standard;
- ouverture manuelle de l'URL par la personne qui teste;
- aucun process cache, aucune ouverture navigateur automatique, aucun scan de ports, aucun `taskkill`, aucun `Start-Process` cache.

Le port `8769` est propose pour eviter les ports courants. S'il est occupe, choisir explicitement un autre port dans la commande visible; ne pas automatiser une recherche de port libre pendant la recette.

## Donnees synthetiques

La cible de recette live locale par defaut est `C:\Users\brice\CoproScope\instances\beauvallon_test`. `examples/synthetic_copro` reste la cible publique/CI.

Ces donnees servent a verifier les parcours, les libelles, les garde-fous et les exports derives. Elles ne prouvent pas que des donnees reelles, des pieces privees, des chemins utilisateur ou une synchronisation cloud fonctionneront sans revue separee.

## Routes a tester manuellement

Pages principales:

- `/`: cockpit local et priorites.
- `/actions`: registre actions, filtres et exports.
- `/documents`: liste des documents.
- `/documents/{doc_id}`: detail document quand l'identifiant existe dans l'instance synthetique.
- `/pieces`: atelier pieces/preuves.
- `/demandes`: demandes coproprietaires, protegee par token.
- `/ag-contentieux`: AG, contentieux et passation, protegee par token.
- `/gouvernance`: roles, commissions et acces.
- `/pilotage`: indicateurs, protegee par token.
- `/depot`: depot guide et pipelines locaux non lourds, protegee par token.
- `/confidentialite`: rappels de diffusion.
- `/chantiers`: prochaines etapes.
- `/health`: statut technique minimal.

Exports et API:

- `/api/model`: modele dashboard, protegee par token.
- `/exports/actions.csv`: export actions CSV, protege par token.
- `/exports/actions.md`: export actions Markdown, protege par token.
- `/exports/local.zip`: pack local derive, protege par token.
- `/exports/passation.json`: export passation derive, protege par token.
- `/exports/passation.txt`: export passation derive texte, protege par token.
- `/exports/{export_path:path}`: doit refuser les chemins interdits ou inconnus.
- `/{root_name}/{path:path}`: doit refuser les racines privees comme `raw`, `restricted`, `logs` ou `private`.

## Etat UI

Testable maintenant:

- cockpit, actions, documents, pieces, depot, confidentialite et chantiers;
- pages demandes, AG/contentieux/passation, gouvernance et pilotage;
- bandeau de contexte sur les surfaces principales;
- token local par query string, en-tete `x-coproscope-token` ou cookie apres premiere requete autorisee;
- exports actions, pack local derive et exports passation derives;
- garde-fous contre chemins prives et racines non servies.

Limites UI a garder visibles:

- pas de validation navigateur manuelle revendiquee dans cette note;
- pas de lancement navigateur automatique;
- pas de promesse sur une ergonomie finale pour toutes tailles d'ecran;
- pas de promesse sur l'import de fichiers reels hors instance synthetique;
- les suggestions et resultats derives restent soumis a revue humaine avant action.

## Etat coffre et vault

Le vocabulaire utilisateur doit privilegier `coffre`; le terme `vault` reste acceptable pour les modules et tests techniques.

Testable maintenant:

- commandes techniques `vault init`, `vault import`, `vault status`, `vault verify` et `vault snapshot`;
- profils de transport documentes comme transport, pas moteur de synchronisation;
- exclusions obligatoires des zones sensibles, temporaires ou dechiffrees;
- alertes de sync et resilience exposees comme signaux locaux;
- archive de reconstruction et notifications internes derivees.

Limites coffre/vault:

- la sync externe n'est pas garantie;
- aucun moteur cache de sync ne doit etre lance par cette livraison;
- pas de scan de processus, de ports ou de clients cloud;
- les signatures collaboratives finales restent a traiter comme futures ou prototypes si elles ne sont pas presentes;
- les exports de passation sont derives et ne deviennent pas source de verite.

## Tests a lancer

Depuis `C:\Users\brice\CoproScope\coproscope\server`:

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -p test_docs_livraison_testable_continue.py -v
.\.venv\Scripts\python.exe -m unittest discover -s tests -p test_ui_smoke_routes_expanded.py -v
.\.venv\Scripts\python.exe -m unittest discover -s tests -p test_ui_security_routes.py -v
```

Suite large possible quand le poste est pret:

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

## Criteres de sortie QA

- la note de livraison existe et mentionne la commande visible autorisee;
- les interdits sont explicites: process cache, scan de ports, ouverture navigateur automatique;
- les routes pages, exports et garde-fous sont listés;
- les donnees synthetiques sont identifiees comme seule base de recette;
- les tests statiques de documentation passent;
- les smoke tests UI et securite routes passent sur l'instance synthetique;
- l'etat UI et l'etat coffre/vault ne promettent pas plus que ce qui est testable.
