# Executable CoproScope avec fenetre pywebview

Roadmap: `RM-2026-0007`, appui `RM-2026-0014`, ordre `ORD-P0-900`.
Chantier: `CH-20260530-215707-RM-2026-0007-pywebview-exe`.
Conversation: `CONV-2026-1908`.

## BOT-START - Coordinateur delivery - 2026-05-30 21:57 +02:00

Role: coordinateur delivery et owner lanceur desktop pywebview.
Mission: livrer un nouvel executable CoproScope qui ouvre sa propre fenetre,
en reprenant l'etat a date du POC executable existant.
Ownership modifiable: lanceur executable, packaging Windows, tests dedies,
dependances optionnelles et docs de livraison.
Fichiers a eviter: instances privees, secrets OAuth, Drive reel, routes web
metier, `viewmodel.py`, `server/src/coproscope/cli.py`.
Passerelle/registre de trace: ce document, `docs/presence_agents.md`,
`docs/roadmap_backlog_central.md`.
Dernier point lu: `AGENTS.md`, `docs/consignes_bots_interconversations.md`,
`docs/protocole_roadmap_presence_agents.md`, `docs/tableau_execution_courant.md`,
`docs/presence_agents.md`, `docs/roadmap_backlog_central.md`.
Tests/preuves attendus: tests unitaires lanceur, line-limit, diff-check, build
PyInstaller, smoke HTTP de l'executable sans laisser de processus ouvert.
Risque de collision: faible; reprise du worktree dedie non integre du POC.
Lease ownership: 2026-05-30 23:57 +02:00.
Prochaine action: ajouter la fenetre pywebview avec fallback navigateur.

## Bloc enquete

Etat de depart:

- `CONV-2026-1907` a livre `server/dist/CoproScope/CoproScope.exe`;
- le lanceur demarre deja l'UI locale sur loopback avec token;
- la limite annoncee etait une ouverture dans navigateur, pas une vraie fenetre
  CoproScope.

Decision de conception:

- conserver l'architecture existante: moteur Python local + UI web existante;
- ajouter pywebview comme couche de fenetre seulement;
- garder `--browser` comme mode de secours et `--no-browser` comme mode smoke;
- ne pas restructurer le depot.

## Bloc doc + dev

Changements livres:

- `coproscope.executable_app` ouvre par defaut une fenetre CoproScope via
  pywebview;
- `--browser` conserve l'ancien mode navigateur;
- `--no-browser` conserve le mode de test sans interface;
- `COPROSCOPE_UI_MODE=window|browser|none` permet le meme choix par variable;
- le serveur local est lance en arriere-plan pour la fenetre, puis l'URL locale
  tokenisee est chargee dans pywebview;
- le build PyInstaller embarque `webview` et les backends Windows utiles;
- le script de build accepte `-DistPath` pour produire dans un dossier frais si
  l'ancien `dist\CoproScope` est verrouille.
- `packaging\windows\smoke-executable.ps1` devient la recette standard pour
  verifier l'executable en mode HTTP ou fenetre.

Artefact livre:

```text
server\dist\CoproScope-pywebview-20260531\CoproScope.exe
```

Taille: `11 593 102` octets.
SHA-256: `ABC41106293A5BE30F0C1A2A63C6B57AE1A75C279864581E1912FC98A1044504`.

Recettes realisees:

- tests unitaires du lanceur: `6 OK`;
- build PyInstaller `--onedir`: OK;
- smoke HTTP de l'executable en mode `--no-browser`: HTTP 200;
- smoke fenetre de l'executable: pywebview atteint l'etape d'ouverture de
  fenetre, `/health` HTTP 200 et page CoproScope HTTP 200.
- `smoke-executable.ps1 -Mode http`: OK;
- `smoke-executable.ps1 -Mode window`: OK.

Note de recette:

- les ports temporaires `8798` et `8797` etaient deja occupes localement;
- la recette finale a donc utilise des ports libres fournis par Windows;
- les processus lances par la recette ont ete fermes a la fin du test.
- l'artefact final a ete range sous `server\dist\...` pour rester hors Git et
  hors garde-fou de ligne source.

## BOT-END - Coordinateur delivery - 2026-05-31 00:33 +02:00

Roadmap: `RM-2026-0007`, appui `RM-2026-0014`, ordre `ORD-P0-900`.
Chantier: `CH-20260530-215707-RM-2026-0007-pywebview-exe`.
Conversation: `CONV-2026-1908`.
Statut: `PRET_A_INTEGRER`.
Fichiers modifies: lanceur executable, packaging Windows, tests lanceur,
dependances optionnelles, runbook packaging, README serveur, consignes agents
et registres de presence/roadmap.
Fichiers volontairement evites: instances privees, secrets OAuth, Drive reel,
routes web metier, `viewmodel.py`, `server/src/coproscope/cli.py`.
Tests/preuves: tests unitaires lanceur `6 OK`, build PyInstaller OK,
`smoke-executable.ps1 -Mode http` OK, `smoke-executable.ps1 -Mode window` OK,
line-limit OK, `git diff --check` OK.
Limites: pas encore d'installateur signe, pas de raccourci menu Demarrer cree
par installeur, pas de mise a jour automatique. L'executable portable est pret.
Prochain mouvement propose: integration de branche, puis decision separee sur
installateur Windows/signature/raccourci.
