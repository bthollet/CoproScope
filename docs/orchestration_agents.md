# Orchestration multi-agents

Ce document permet de lancer plusieurs agents en meme temps sur CoproScope sans melanger les responsabilites, les branches, les donnees privees ou les ports locaux.

## Pourquoi paralleliser

Les prochains sprints peuvent avancer plus vite si on separe :

- le cockpit et les actions ;
- ComptaScope et les questions au syndic ;
- DocOps/PrivacyOps et la revue de diffusion ;
- la documentation, les registres et l'integration ;
- les nouveaux modules decision-action-preuve, WorksOps ou IncidentOps.

La parallelisation ne doit pas servir a faire travailler plusieurs agents sur les memes fichiers. Elle sert a avancer sur des tranches coherentes, puis a integrer proprement.

## Principe d'organisation

| Role | Responsabilite |
|---|---|
| Coordinateur | Decoupe les lots, cree les branches/worktrees, tient le registre, integre les resultats. |
| Agent de sprint | Travaille sur un perimetre borne, teste, documente ses limites. |
| Agent verification | Relit ou teste une tranche sans modifier le meme perimetre. |

Un agent ne doit pas supposer qu'il est seul. Il ne revert pas le travail des autres, ne deplace pas une responsabilite sans accord, et ne modifie pas les donnees privees.

## Routeur automatique d'equipes

Avant de lancer une equipe multi-agents, utiliser
[`strategie_equipes_multi_agents.md`](./strategie_equipes_multi_agents.md).
Le routeur choisit l'equipe-type et la strategie d'orchestration avant de
creer le `CH-*`:

- `INCIDENT_STATIONNEMENT`: arbitrage, doublon ou blocage; check-in seulement;
- `FANIN_CONSOLIDATION`: retours concurrents ou tardifs; dedoublonner avant
  tout nouveau dispatch;
- `RECHERCHE_METIER`: experts juridique/syndic/compta/travaux/CS sans dev;
- `UXUI_RECHERCHE`: recherche UX/UI visuelle sans dev;
- `AGILE_UI_PRODUIT`: delivery UI avec visuel IA, blueprint, novice, front,
  back et QA;
- `BACKEND_DOMAINE`: owner code unique sur DB/vault/read model/sync/extracteurs,
  experts en lecture;
- `RECETTE_LIVE_QA`: serveur reserve, captures et verdict navigateur;
- `INTEGRATION_RELEASE`: integration serie, une branche/worktree a la fois;
- `DOCTRINE_SIDEQUEST`: protocole ou cadrage transverse borne.

Le choix automatique ne saute jamais le preflight: `EN_ATTENTE_USER`, incident
de doublon ou `BLOQUE` non stationne gagnent sur toute priorite backlog. Si un
`CH-*` vivant existe deja, le routeur reprend seulement ses roles manquants,
idle, bloques ou expires.

Apres le choix d'un `ORD-*` et d'un `CH-*`, le coordinateur publie les slots de
role dans [`tableau_execution_courant.md`](./tableau_execution_courant.md).
Les conversations workers ne piochent pas dans `roadmap_backlog_central.md`;
elles prennent seulement un slot `A_PRENDRE` deja ouvert pour le chantier
courant.

## Chemin critique et side-quests

Dans une conversation orientee vers un but principal, par exemple un audit, une
recette ou une livraison, le coordinateur protege le chemin critique: il continue
a faire avancer le resultat attendu et ne se disperse pas dans les demandes
laterales.

Quand une orientation ponctuelle demande de generaliser une regle, clarifier une
doctrine, explorer un sujet transverse ou produire une note annexe, le travail
est confie a un sub-agent si le nombre de threads/conversations le permet. Le
lot delegue doit etre borne: objectif, fichiers autorises, fichiers evites,
trace attendue, verification et critere de fin.

Si aucun thread n'est disponible, le coordinateur enregistre la side-quest comme
reprise ulterieure ou demande d'arbitrage et garde la piste principale. Il ne la
traite lui-meme que si elle bloque directement le but en cours. Un sub-agent de
generalisation ne modifie pas le code applicatif sans ownership explicite; par
defaut, il produit une doctrine, une note ou une proposition d'integration.

## Methode equipe agile

Quand Brice demande une "equipe agile", une equipe multi-agents, ou un
fonctionnement UX/dev/QA par iterations rapides, utiliser
[`protocole_equipe_agile_agents.md`](./protocole_equipe_agile_agents.md).
Quand la demande est seulement "equipe multi-agents" ou quand le prochain lot
vient du gouvernail, appliquer d'abord le routeur automatique; l'equipe agile
UI produit n'est lancee que si le routeur choisit `AGILE_UI_PRODUIT`.

Au lancement effectif, le coordinateur met a jour la heartbeat canonique
`relance-equipe-agile-gouvernail-autonome` toutes les 5 minutes sur le fil
courant. Il ne cree pas de heartbeat concurrente sans demande explicite de
Brice; tout doublon actif est mis en pause. La relance laisse un check-in
persistant dans `docs/presence_agents.md`, meme en `DONT_NOTIFY`, reprend les
roles manquants, idle, bloques ou expires, ne duplique pas un role vivant, et
traite `AGILE-DONE - equipe agile a fini son job` comme une fin de lot, pas
comme une fin d'orchestration. Si tous les roles du lot sont clos, la heartbeat
reprend le gouvernail, choisit le prochain `ORD-*` actionnable et ouvre une
nouvelle equipe avec un nouveau `CH-*`, puis met a jour le tableau d'execution
courant avec les slots workers. Elle n'est supprimee que sur demande explicite
de Brice ou absence verifiee de tout `ORD-*` actionnable.

Le noyau d'equipe est:

- coordinateur-scribe;
- designer service / facilitateur;
- utilisateur novice ou representant metier;
- dev front;
- dev back / viewmodel;
- QA securite / regression.

Si le budget de threads le permet, le coordinateur ajoute aussi un testeur
expert metier juridique/compta/process chantier/syndic. Ce role reste en
lecture seule, contre-teste les risques de procedure et de diffusion, et rend
ses constats en `fait -> preuve attendue -> regle/process -> action`. Si aucun
thread n'est disponible, QA et coordinateur reprennent sa checklist dans le
verdict du lot.

Le coordinateur garde les roles en flux decale:

- `N-1`: QA et utilisateur novice testent une route ou un artefact livre;
- `N`: front/back developpent une commande validee;
- `N+1`: designer et utilisateur preparent l'image, le blueprint et la
  commande suivante.

Chaque cycle part d'une UI reelle ou en produit une: route locale, ecran,
modale, artefact HTML ou parcours testable. Quand le sujet est visuel, nouveau,
ambigu ou sensible pour un novice, le designer genere une image IA bitmap de
l'ecran complet et un blueprint avant le dev; le membre novice les qualifie en
GO/NO-GO, puis seulement le coordinateur ouvre l'ownership front/back. L'un
et/ou l'autre peuvent etre annules seulement avec justification tracee
`VISUEL_IA_WAIVED` et/ou `BLUEPRINT_WAIVED`.

La comparaison aux visuels d'enquete utilisateur est une activite recurrente:
designer, novice et QA rapprochent l'UI reelle des captures source ou du visuel
designer derive avant commande dev, apres livraison, puis avant tout GO. Les
ecarts de structure, hierarchie, densite, vocabulaire et affordances sont traces
comme acceptes, refuses ou reportes.

Un agent idle est relance sur QA, preparation, documentation, coherence ou
integration, selon son ownership declare. Les devs ne codent pas tant qu'il n'y
a pas UI cible reelle, commande dev validee, qualification novice requise et
owner unique sur les fichiers sensibles.

## Methode equipe UX/UI recherche sans dev

Quand Brice dit `lance une equipe UX/UI`, avec ou sans accent sur `equipe`,
utiliser
[`protocole_equipe_ux_ui_recherche.md`](./protocole_equipe_ux_ui_recherche.md).

Ce mode est volontairement different de l'equipe agile:

- 6 roles maximum;
- aucun dev, aucun patch, aucun ticket technique detaille;
- deux testeurs obligatoires: Testeur metier expert et Testeur
  accessibilite/novice;
- generation d'images par le Designer UI / generateur visuel;
- images retenues archivees dans `docs/assets/...` et referencees dans la doc
  de mission avec prompt/intention, decision et retours testeurs;
- heartbeat automatique toutes les 10 minutes sur le fil courant jusqu'au
  marqueur `UXUI-DONE - equipe UX/UI a fini son job`.

Le coordinateur cree le `RM-*` si necessaire, le `CH-*` horodate, la ligne
`CONV-*`, la doc de mission `docs/recherche_ux_ui_<date>_<slug>.md` et le
dossier d'images `docs/assets/ux-ui-recherche-<date>-<slug>/`. Si les outils
de sous-agents sont disponibles, il lance les roles separement; sinon il execute
les roles dans le fil courant avec des sections nommees. Dans tous les cas, la
relance ne doit pas dupliquer un role vivant.

## Regle zero interconversations

Tout agent doit appliquer
[`consignes_bots_interconversations.md`](./consignes_bots_interconversations.md)
avant de travailler. S'il ne peut pas declarer son role, son ownership, sa
passerelle de trace et le dernier point lu, il reste en lecture seule.

Les passerelles sont separees:

- UX ecrit vers DB dans `passerelle_ux_vers_db_2026-05-21.md`;
- DB repond vers UX dans `passerelle_db_vers_ux_2026-05-21.md`;
- le coordinateur consolide dans `coordination_interconversations_2026-05-21.md`
  et le point live;
- QA/novice publient des go/no-go sur routes reelles dans le journal ou le
  registre de cycle.

Le coordinateur doit traiter comme risque de collision tout bot qui modifie un
fichier sensible sans owner declare.

Les demandes et chantiers vivants sont suivis dans deux registres transverses:

- `roadmap_backlog_central.md` comme gouvernail unique pour les intentions `RM-*`;
- `tableau_execution_courant.md` comme tableau court du chantier courant et
  seule surface ou un worker prend un slot;
- `presence_agents.md` pour les chantiers `CH-*`, conversations `CONV-*`,
  ownerships, worktrees, heartbeats et fins de mission.

Les nouveaux chantiers doivent etre nommes
`CH-YYYYMMDD-HHMMSS-RM-YYYY-NNNN-slug-court`; les anciens `CH-YYYY-NNNN`
restent des references legacy mais ne sont plus crees.

Les anciennes feuilles de route, backlogs et journaux de cycles sont des sources
rattachees. Un agent ne les utilise pour demarrer un chantier que si le
gouvernail pointe vers un `RM-*` correspondant.

## Flux refonte UX Canva

Pour la refonte UX depuis les visuels d'enquete, utiliser le protocole
[`refonte_ux_cycles_image_dev_test.md`](./refonte_ux_cycles_image_dev_test.md)
avant de lancer les devs. Le flux impose:

- enquete sur image ou visuel recree par le designer;
- commande dev validee;
- developpement front/back;
- test de la route livree;
- correction ou cloture.

Le registre de suivi est
[`registre_cycles_refonte_ux.md`](./registre_cycles_refonte_ux.md). Les prompts
par role sont dans [`prompts_agents_refonte_ux.md`](./prompts_agents_refonte_ux.md).

Regle specifique: aucun dev ne demarre une vue manquante sans blueprint
designer, aucun dev ne demarre une UI pertinente sans image IA bitmap plein
ecran et blueprint qualifies par le novice, et aucun testeur ne valide une
intention abstraite sans route ou artefact reel livre. Aucun GO UI n'est publie
sans comparaison aux visuels d'enquete ou justification explicite de
non-pertinence.

## Preparation avant lancement

1. Stabiliser le depot principal : commit ou stash explicite des changements en cours.
2. Verifier la branche de base : `codex/bootstrap-coproscope-server` ou autre branche decidee.
3. Creer un worktree par agent.
4. Donner a chaque agent un contrat avec ownership fichiers.
5. Reserver un port local par agent si une interface est lancee.
6. Noter ou creer l'item `RM-*` dans le gouvernail `roadmap_backlog_central.md`.
7. Noter les agents actifs dans `presence_agents.md` avec `CH-*`, `CONV-*`,
   lease et prochaine action.
8. Verifier que chaque agent a lu le dernier point de coordination et declare
   sa passerelle de trace.

Commandes types :

```powershell
git fetch origin
git switch codex/bootstrap-coproscope-server
git pull --ff-only

git worktree add ..\coproscope-agent-sprint2-actions -b codex/sprint2-actions
git worktree add ..\coproscope-agent-sprint3-compta -b codex/sprint3-compta
git worktree add ..\coproscope-agent-sprint4-privacy -b codex/sprint4-privacy
```

Si la branche existe deja :

```powershell
git worktree add ..\coproscope-agent-sprint2-actions codex/sprint2-actions
```

## Contrat de mission a copier-coller

```text
Mission: Sprint <numero> - <nom court>
Objectif: <resultat visible attendu>
Role/filiere: <UX | DB | QA | front | back | docs | coordinateur>
Roadmap: RM-YYYY-NNNN
Chantier: CH-YYYYMMDD-HHMMSS-RM-YYYY-NNNN-slug-court
Conversation: CONV-YYYY-NNNN
Branche: codex/<sprint>-<scope>
Worktree: <chemin absolu ou relatif>
Port local reserve: <port ou aucun serveur>

Tu n'es pas seul dans le codebase. Ne revert jamais les changements des autres.

Ownership modifiable:
- <dossier/fichier 1>
- <dossier/fichier 2>

Hors perimetre:
- <dossier/fichier a ne pas toucher>

Passerelle/registre de trace:
- <fichier markdown ou registre>

Dernier point coordination lu:
- <fichier + heure>

Lease ownership:
- <expiration + fuseau, par defaut 2h pour edition>

Donnees:
- Ne jamais ajouter de donnees reelles dans Git.
- Utiliser `C:\Users\brice\CoproScope\instances\beauvallon_test` comme environnement de test local par defaut.
- Utiliser `examples/synthetic_copro` seulement pour les tests publics/CI et les exemples partageables.
- Utiliser toute autre instance privee seulement en lecture locale si explicitement demande.
- La copro demo publiable reste hors Drive, dans `CoproScope/instances/...`.

Verification:
- <commande test 1>
- <commande test 2>
- checks UI attendus si pertinent.

Livrable final:
- fichiers modifies ;
- fichiers volontairement evites ;
- tests lances ;
- limites connues ;
- questions ouvertes ;
- proposition d'integration.
```

## Matrice des prochains sprints

| Sprint | Agent possible | Ownership conseille | Dependances | Livrable |
|---|---|---|---|---|
| Lot 0 - Base Sprint 2 | Coordinateur | `server/src/coproscope/web/`, `server/tests/test_ui_demo.py`, docs suivi | A faire avant forte parallelisation | Vue Actions, exports, docs multi-agents, tests OK. |
| Lot A - ComptaScope CS | Agent compta | templates comptes, helpers comptes, docs `comptascope.md` | Actions clarifiees | Questions syndic editables/copiables, detail facture, rapport court. |
| Lot B - SyndicOps | Agent demandes | module demandes, registres, tests dedies | Questions/actions | Demandes avec statut, echeance, relance, preuve. |
| Lot C - DocOps actionnable | Agent documents | modules DocOps, vue documents, tests documentaires | Baseline documents | Pieces presentes/manquantes/obsoletes/a demander. |
| Lot D - Privacy revue | Agent privacy | `privacyops.py`, templates confidentialite, tests privacy | Garde-fous existants | Revue humaine, statuts diffusion, file biffage lisible. |
| Lot E - Decision -> action -> preuve | Agent registre | nouveau module et tests dedies | AGOps minimal | Registre decisions, actions, preuves et premiere interface. |
| Lot F - WorksOps | Agent travaux | module travaux, tests dedies | Registre action/preuve souhaitable | Dossier travaux minimal probatoire. |
| Lot G - IncidentOps | Agent incidents | module incidents, tests dedies | Registre action/preuve souhaitable | Signalements, statuts, preuves de cloture. |
| Lot H - CommsOps/passation | Agent sorties | exports, templates rapports, docs confidentialite | Privacy revue | Syntheses diffusables et pack passation. |

Voir les briefs detailles : [Lots paralleles approfondis](./lots_paralleles.md).

## Perimetres a ne pas faire modifier en parallele

| Fichier ou zone | Pourquoi | Regle |
|---|---|---|
| `server/src/coproscope/web/viewmodel.py` | Point de convergence de l'interface | Un seul owner a la fois. |
| `server/src/coproscope/cli.py` | Surface de commande partagee | Modifications groupees par coordinateur ou agent unique. |
| schemas/registres partages | Risque de casser plusieurs modules | Proposer le schema dans une note avant implementation concurrente. |
| docs de synthese (`README.md`, `archive/roadmaps_anciennes/feuille_de_route.md`) | Risque de conflits editoriaux | Owner documentation unique. |

## Ports et serveurs locaux

La reference canonique est la section `Ports locaux` de `AGENTS.md`. Un port
est un ownership temporaire: il doit etre reserve dans le contrat agent, visible
dans `presence_agents.md`, puis libere dans le `BOT-END`.

| Usage | Port |
|---|---:|
| Integration principale | 8765 |
| Agent UI/actions | 8766 |
| Agent compta | 8767 |
| Agent privacy | 8768 |
| Agent demo/docs | 8769 |
| Agent syndic | 8770 |
| Agent DocOps | 8771 |
| Agent decision/action/preuve | 8772 |
| Agent travaux | 8773 |
| Agent incidents | 8774 |
| Agent comms/passation | 8775 |

Exemple :

```powershell
.\server\.venv\Scripts\python.exe -m coproscope.cli ui open-test --instance-root C:\Users\brice\CoproScope\instances\beauvallon_test --year 2025 --host 127.0.0.1 --port 8766 --token beauvallon-test-local
```

Regle compatible antivirus : lancer le serveur dans un terminal PowerShell
visible, au premier plan ou minimise par l'utilisateur, puis l'arreter avec
`Ctrl+C`. Ne pas utiliser de fenetre cachee, de `Start-Process` cache, de scan
de ports/processus, de `taskkill`, ni d'ouverture navigateur automatique. Si une
page ne repond pas, lire le terminal serveur visible plutot que chercher et tuer
un PID.

La plage `8780` a `8799` sert uniquement aux recettes temporaires, gates live et
comparaisons. Avant de l'utiliser, annoncer le port, l'instance, le token et le
motif dans la trace `CONV-*`; apres usage, noter l'arret ou la conservation
volontaire du serveur.

## Registre de suivi multi-agents

Le registre courant des agents est `presence_agents.md`. Ajouter ou mettre a
jour une ligne quand plusieurs agents tournent :

| Conversation | Roadmap | Chantier | Branche/worktree | Ownership | Statut | Expire | Prochain geste |
|---|---|---|---|---|---|---|---|
| `CONV-YYYY-NNNN` | `RM-YYYY-NNNN` | `CH-YYYYMMDD-HHMMSS-RM-YYYY-NNNN-slug-court` | `codex/...` / `...\_worktrees\...` | fichiers reserves | EN_COURS | date + fuseau | action concrete |

Statuts conseilles : `A_LANCER`, `EN_COURS`, `EN_ATTENTE_USER`, `BLOQUE`,
`PRET_A_INTEGRER`, `INTEGRE`, `EXPIRE`, `ABANDONNE`, `CLOTURE`.

## Watchdog orchestration

Avant de relancer une equipe ou de conclure que l'orchestrateur tourne encore,
lancer:

```powershell
.\tools\orchestration-watch.cmd
```

Pour obtenir un prompt de relance sans inventer de roles:

```powershell
.\tools\orchestration-watch.cmd --emit-prompt
```

Le watchdog signale les conversations `EN_COURS` stale ou expirees, les
`EN_ATTENTE_USER`, les `BLOQUE`, les lots `PRET_A_INTEGRER` et la derniere
trace de `relance-equipe-agile-gouvernail-autonome`. En mode strict:

```powershell
.\tools\agent-check.cmd -Orchestration
```

Un resultat rouge ne lance pas automatiquement une equipe. Il force le
coordinateur a remonter l'arbitrage, regulariser une expiration ou ouvrir un
nouveau `CH-*` avec ownership explicite.

## Vague active 21h15

La coordination exploitable pour le jalon du 2026-05-20 a 21h15 est tenue dans
[`orchestration_2115.md`](./archive/recettes_ux/orchestration_2115.md). Elle couvre:

- l'etat des chantiers comptes, sync alertes, atelier piece, cockpit et UX tester;
- les dependances entre lots;
- les criteres d'integration et de passage 21h15;
- la prochaine vague d'agents a lancer avec ownerships separes;
- les risques Git/worktree observes.

Regle de cette vague: si un agent doit toucher `server/src/coproscope/web/viewmodel.py`, il doit etre declare owner unique de ce fichier avant lancement. Les autres agents UI travaillent sur templates/tests ou rendent une note d'integration.

Les nouveaux worktrees doivent etre crees sous `C:\Users\brice\CoproScope\_worktrees`. Ne pas lancer de nouveau travail dans les anciens worktrees situes sous `G:/Mon Drive/...`; certains sont marques `prunable` et tous sont contraires au garde-fou actuel sur les dossiers synchronises.

## Verification minimale d'integration

Avant de rendre un lot court, depuis la racine du depot :

```powershell
.\tools\agent-check.cmd
```

Si le lot touche l'interface :

```powershell
.\tools\agent-check.cmd -Ui
```

Pour une integration coordinateur, depuis `server/` :

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

Checks UI depuis la racine :

Ouvrir manuellement l'URL tokenisee affichee par `ui open-test`, puis verifier les onglets `Cockpit`, `Actions`, `Comptes`, `Documents`, `Atelier pieces`, `Confidentialite`, `Chantiers` et `Depot`. Pour les agents, preferer les tests unitaires et les clients FastAPI internes plutot que des boucles `Invoke-WebRequest`.

Pour un lot desktop, packaging, installable ou recette utilisateur generale,
remplacer autant que possible la recette serveur PowerShell par la recette de
l'executable depuis `server/`:

```powershell
.\packaging\windows\smoke-executable.ps1 -Mode http
.\packaging\windows\smoke-executable.ps1 -Mode window
```

Le serveur PowerShell visible reste adapte au developpement d'une route web,
mais la preuve finale d'un executable doit citer le smoke executable, son mode
et l'artefact teste.

## Garde-fous donnees

- Ne jamais commiter `coproscope-instances/`, `raw`, `restricted`, `.env.local`, tables de correspondance ou exports prives.
- Ne pas publier une instance seulement pseudonymisee.
- Ne pas melanger copro demo et instance privee dans le cockpit.
- La recette live locale par defaut se fait sur `C:\Users\brice\CoproScope\instances\beauvallon_test`.
- Les tests publics doivent passer sur `examples/synthetic_copro` ou sur une demo fictive.
- Toute sortie diffusable doit passer par PrivacyOps/BiffageOps ou par une transformation fictive robuste.
