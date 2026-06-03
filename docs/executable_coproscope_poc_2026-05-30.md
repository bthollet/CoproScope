# POC executable CoproScope

Roadmap: `RM-2026-0007`, appui `RM-2026-0014`, ordre `ORD-P0-900`.
Chantier: `CH-20260530-131827-RM-2026-0007-executable-poc`.
Conversation: `CONV-2026-1907`.

## BOT-START

Role: coordinateur delivery et owner POC executable Windows.
Mission: livrer un premier executable CoproScope testable sans demander une
commande Python a l'utilisateur.
Ownership modifiable: lanceur executable, packaging Windows, tests dedies,
documentation packaging et traces presence/roadmap.
Fichiers evites: routes UI, templates, CSS, Drive/OAuth reel, instances
privees, documents bruts, OCR/logs, exports bruts, secrets, serveurs live,
scan/kill et push GitHub.
Dernier point lu: consignes agents, protocole presence, gouvernail
`RM-2026-0007` / `RM-2026-0014`, runbooks packaging et OAuth.
Tests/preuves attendus: tests unitaires du lanceur, garde 600 lignes,
`git diff --check`, build PyInstaller si la dependance est disponible.
Lease: 2026-05-30 15:18 +02:00.

## Bloc enquete

Probleme: CoproScope se lance aujourd'hui surtout comme commande Python. Pour
un utilisateur non technique, le premier pas doit devenir un double-clic.

Sources lues: `AGENTS.md`, `docs/consignes_bots_interconversations.md`,
`docs/protocole_roadmap_presence_agents.md`, `docs/roadmap_backlog_central.md`,
`docs/presence_agents.md`, `docs/runbook_packaging_noob_windows.md`,
`docs/checklist_installable_drive_chiffre_noob.md`, `server/README.md`,
`server/pyproject.toml` et le CLI `coproscope.cli`.

Donnees reelles disponibles: aucune donnee reelle utile ou autorisee pour ce
POC. Le POC doit s'ouvrir sur l'instance synthetique `examples/synthetic_copro`
ou sur une instance passee explicitement par variable locale.

Sources absentes: pas encore d'installateur signe, pas encore de profil
premiere ouverture complet, pas encore de choix de coffre local noob.

Etat actuel: le CLI sait deja servir l'interface locale avec un jeton. Le
runbook packaging cible PyInstaller `--onedir`, un raccourci Windows et un
lanceur qui ouvre le navigateur.

Ecarts: il manque un point d'entree dedie a l'executable et une recette de
build versionnee. Sans cela, PyInstaller emballerait la CLI brute, trop
technique pour un premier test novice.

No-go: ne pas embarquer d'instance privee, ne pas toucher aux secrets OAuth, ne
pas ouvrir un vrai Drive, ne pas ajouter de service Windows, ne pas modifier les
routes produit en cours.

Decision: `PRET_PLAN_DEV`. Livrer un POC borne: `CoproScope.exe` ouvre l'UI
locale sur `127.0.0.1`, avec token de session, navigateur ouvert
automatiquement et instance demo embarquable.

## Bloc doc + dev

Objectif produit: double-cliquer sur CoproScope et obtenir l'interface locale.

Artefact cible: dossier PyInstaller `server/dist/CoproScope/CoproScope.exe`.

Contrat de donnees: uniquement instance synthetique ou instance choisie par
`--instance-root` / `COPROSCOPE_INSTANCE_ROOT`; aucun document brut ni secret.

Plan:

- ajouter un lanceur `coproscope.executable_app`;
- ajouter un script d'entree PyInstaller;
- ajouter une spec PyInstaller qui embarque le paquet et l'instance demo;
- ajouter un script de build PowerShell;
- tester le choix d'instance, le jeton, le mode CLI de secours et l'appel
  serveur sans lancer de serveur live.

Definition de fini POC:

- tests unitaires verts;
- garde 600 lignes vert;
- diff-check vert;
- build PyInstaller tente si la dependance est disponible;
- limites noob restantes explicites.

## BOT-END

Statut: `PRET_A_INTEGRER`.

Livraison:

- executable construit: `server/dist/CoproScope/CoproScope.exe`;
- lanceur local `coproscope.executable_app`;
- recette PyInstaller Windows reproductible;
- instance demo synthetique embarquee dans le dossier PyInstaller;
- mode sans console, avec ouverture navigateur par defaut;
- trace diagnostic optionnelle via `COPROSCOPE_LAUNCHER_LOG`.

Preuves du 2026-05-30:

- `python -m unittest tests.test_executable_app -v`: 4 tests OK;
- `python tools/check_code_line_limit.py`: OK;
- `git diff --check`: OK;
- build PyInstaller OK avec `PyInstaller 6.20.0` et Python `3.14.5`;
- smoke reel du `.exe`: HTTP 200 sur `127.0.0.1` avec jeton local;
- controle apres smoke: aucun processus `CoproScope.exe` ni port du worktree
  laisse ouvert.

Limites restantes:

- ce n'est pas encore un installateur signe;
- le premier parcours de creation de coffre noob reste a livrer;
- les fonctions lourdes optionnelles non installees dans l'environnement de
  build, comme OCR avance ou compta avancee, ne font pas partie du smoke POC;
- aucun vrai Drive, secret OAuth, document brut ou donnee d'instance privee n'a
  ete utilise.
