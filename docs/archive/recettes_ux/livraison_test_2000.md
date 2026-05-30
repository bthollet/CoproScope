# Checklist livraison testable 20h

Date : 2026-05-20

Note 2026-05-21: cette checklist est une trace du jalon Platanes/20h. Les
recettes live locales par defaut doivent maintenant utiliser
`C:\Users\brice\CoproScope\instances\beauvallon_test`.

Objectif : donner a un testeur novice un protocole court pour verifier la livraison CoproScope locale, sans importer de nouvelles donnees reelles et sans synchroniser de dossiers dangereux dans Drive ou dans le futur vault.

La livraison de 19h30 est annulee et remplacee par ce jalon 20h. Apres 20h, le developpement continue : le jalon sert a tester une version ouvrable, pas a figer la roadmap.

## Perimetre de test

Tester uniquement une instance de demonstration ou une instance locale deja preparee. Ne pas importer de documents reels pendant cette passe de 15 minutes.

Pages UI a couvrir :

- Cockpit : vue d'ensemble des priorites, KPI et etat des modules.
- Actions : liste de travail, filtres par domaine, exports CSV et Markdown.
- Comptes : controle guide ComptaScope, P1/P2/OK, questions syndic.
- Documents : pieces presentes, manquantes, obsoletes et artefacts.
- Atelier pieces : file des pieces a demander ou verifier.
- Depot & exports : depot local, historique, pipelines manuels, export zip local.
- Confidentialite : statuts de diffusion, revue humaine et file de biffage.
- Chantiers : DecisionOps, IncidentOps, WorksOps a lancer, passation.

Limites connues a annoncer au testeur :

- l'interface est locale et prioritairement en lecture ; certains boutons declenchent des pipelines locaux, pas des workflows collaboratifs complets ;
- WorksOps, ContractOps et CommsOps ne sont pas complets ;
- la revue confidentialite aide a decider, mais ne remplace pas une validation humaine ou juridique ;
- une pseudonymisation tracee reste une donnee personnelle ;
- les exports ne doivent pas etre consideres diffusables sans controle PrivacyOps/BiffageOps.

## Commandes Windows depuis `C:\Users\brice\CoproScope\coproscope`

Ouvrir PowerShell :

```powershell
cd C:\Users\brice\CoproScope\coproscope
git branch --show-current
git status --short
```

Installer ou verifier l'environnement UI, si necessaire :

```powershell
cd C:\Users\brice\CoproScope\coproscope\server
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e ".[ui]"
```

Revenir a la racine et preparer l'instance synthetique :

```powershell
cd C:\Users\brice\CoproScope\coproscope
.\server\.venv\Scripts\python.exe -m coproscope.cli doctor --instance-root .\examples\synthetic_copro
.\server\.venv\Scripts\python.exe -m coproscope.cli pipeline run --instance-root .\examples\synthetic_copro
.\server\.venv\Scripts\python.exe -m coproscope.cli privacy screen-existing --instance-root .\examples\synthetic_copro
.\server\.venv\Scripts\python.exe -m coproscope.cli privacy redaction-queue --instance-root .\examples\synthetic_copro
.\server\.venv\Scripts\python.exe -m coproscope.cli invoices extract --instance-root .\examples\synthetic_copro --year 2025
.\server\.venv\Scripts\python.exe -m coproscope.cli accounting reconstruct --instance-root .\examples\synthetic_copro --year 2025
.\server\.venv\Scripts\python.exe -m coproscope.cli accounting controls --instance-root .\examples\synthetic_copro --year 2025
.\server\.venv\Scripts\python.exe -m coproscope.cli decisions build --instance-root .\examples\synthetic_copro
.\server\.venv\Scripts\python.exe -m coproscope.cli incidents build --instance-root .\examples\synthetic_copro
```

Lancer l'UI locale :

```powershell
cd C:\Users\brice\CoproScope\coproscope
.\server\.venv\Scripts\python.exe -m coproscope.cli ui open-test --instance-root C:\Users\brice\CoproScope\instances\beauvallon_test --year 2025 --host 127.0.0.1 --port 8766 --token beauvallon-test-local
```

Ouvrir ensuite :

```text
http://127.0.0.1:8766/?token=beauvallon-test-local
```

En mode compatible antivirus, ne pas lancer de script de probing reseau, de boucle `Invoke-WebRequest`, de scan de ports ou d'arret automatique par PID pendant la demo. Verifier les pages depuis le navigateur et arreter le serveur avec `Ctrl+C` dans le terminal visible qui a lance `ui open-test`.

## Protocole utilisateur novice

1. Ouvrir l'URL locale avec le token.
2. Verifier que le bandeau affiche "CoproScope local", le nom de l'instance et l'exercice 2025.
3. Cliquer sur chaque onglet de navigation, dans l'ordre : Cockpit, Actions, Comptes, Documents, Atelier pieces, Confidentialite, Chantiers, Depot & exports.
4. Sur chaque page, verifier qu'il n'y a ni erreur serveur, ni page blanche, ni chemin de fichier prive inattendu dans un contenu diffusable.
5. Sur Actions, tester au moins deux filtres : `Comptes` et `Confidentialite`, puis telecharger CSV et Markdown.
6. Sur Comptes, verifier que les notions P1, P2 et OK sont expliquees et que les questions syndic sont lisibles.
7. Sur Documents et Atelier pieces, verifier que le testeur comprend ce qui est present, manquant, obsolete ou a demander.
8. Sur Confidentialite, verifier que les statuts `a arbitrer`, `bloque`, `apres biffage` ou `apres aggregation` sont visibles quand ils existent.
9. Sur Depot & exports, ne deposer aucun fichier reel ; tester uniquement l'affichage de la page, l'historique et les exports existants.
10. Sur Chantiers, confirmer que WorksOps est clairement marque comme chantier a lancer, pas comme fonction complete.

## Grille de validation manuelle en 15 minutes

| Minute | Zone | Action testeur | Attendu | OK/NOK | Notes |
|---:|---|---|---|---|---|
| 0-2 | Lancement UI | Lancer `ui open-test`, ouvrir l'URL avec token | Page Cockpit chargee, navigation visible |  |  |
| 2-4 | Cockpit | Lire KPI, priorites, apercu actions, modules | Le testeur sait quoi regarder en premier |  |  |
| 4-6 | Actions | Filtrer Comptes puis Confidentialite, exporter CSV/MD | Filtres actifs, exports telecharges sans erreur |  |  |
| 6-8 | Pieces | Ouvrir Documents puis Atelier pieces | Pieces presentes/manquantes/a demander lisibles |  |  |
| 8-10 | Depot | Ouvrir Depot & exports avec token ; ne pas uploader de reel | Page accessible avec token, zone depot claire, exports visibles |  |  |
| 10-12 | Comptes | Lire P1/P2/OK, controles, questions syndic | Priorites comptables comprehensibles par non expert |  |  |
| 12-14 | Confidentialite | Lire revue humaine et file de biffage | Risques de diffusion et blocages visibles |  |  |
| 14-15 | Chantiers | Lire DecisionOps, IncidentOps, WorksOps, passation | Chantiers incomplets explicitement nommes |  |  |

Decision de livraison :

| Critere | Go si... | No-go si... |
|---|---|---|
| Navigation | Les huit pages repondent en `200` avec token | Page blanche, 500 ou navigation cassee |
| Novice | Un testeur comprend les actions prioritaires sans aide technique | Le testeur ne distingue pas priorite, preuve, action ou risque |
| Donnees | Aucune donnee reelle n'est necessaire au test | Le test pousse a importer ou afficher du reel |
| Confidentialite | Les limites de diffusion sont visibles | L'UI donne une impression de partage sur sans arbitrage |
| Depot | Le token protege les actions sensibles | Depot/export local accessible sans token |

## Ne pas faire : Drive, vault et synchronisation

Ne pas travailler directement dans Drive pour cette livraison.

Ne jamais synchroniser dans Drive, dans un vault sync ou dans un dossier partage :

- `.git` ;
- `.venv` ou tout environnement Python ;
- `__pycache__`, `.pytest_cache`, caches OCR, caches d'IA ou caches navigateur ;
- `_worktrees` et worktrees Git ;
- exports temporaires, `public-export`, zips de travail, rapports provisoires ;
- blobs dechiffres, originaux sensibles, cartes de correspondance de pseudonymisation ;
- cles privees, tokens, secrets plugin ou fichiers `.env` ;
- index lisibles contenant noms de documents, chemins locaux, OCR, notes, statuts metier ou commentaires.

Pour le futur vault synchronisable, seules les entrees prevues par la specification V1 doivent apparaitre a la racine du dossier sync : `vault.json`, `blobs/`, `events/`, `snapshots/`, `keys/`, `indexes/`. Les caches locaux et exports restent reconstructibles et hors sync.

## Recommandations de livraison 20h

- Faire la recette locale par defaut sur `C:\Users\brice\CoproScope\instances\beauvallon_test`; garder `examples\synthetic_copro` pour les tests publics/CI et demonstrations partageables.
- Afficher explicitement l'URL tokenisee au testeur et rappeler que le serveur ecoute sur `127.0.0.1`.
- Presenter l'UI comme un cockpit local de preuve, action et memoire, pas comme un extranet de syndic.
- Commencer par Cockpit puis Actions : c'est le chemin le plus comprehensible pour un novice.
- Dire avant la page Confidentialite que CoproScope signale le risque, mais que la decision de diffusion reste humaine.
- Ne pas tester DocAI lourd ni imports reels a 20h ; garder le test sur navigation, lisibilite, exports simples et garde-fous.
- Apres 20h, reprendre le developpement en priorisant les lots issus de la recherche utilisateur : demandes coproprietaires multi-canaux, PDF annote, comptes utilisateurs/commissions, AG/contentieux, puis vault collaboratif signe.
