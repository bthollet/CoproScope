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

Le noyau d'equipe est:

- coordinateur-scribe;
- designer service / facilitateur;
- utilisateur novice ou representant metier;
- dev front;
- dev back / viewmodel;
- QA securite / regression.

Le coordinateur garde les roles en flux decale:

- `N-1`: QA et utilisateur novice testent une route ou un artefact livre;
- `N`: front/back developpent une commande validee;
- `N+1`: designer et utilisateur preparent l'image, le blueprint et la
  commande suivante.

Un agent idle est relance sur QA, preparation, documentation, coherence ou
integration, selon son ownership declare. Les devs ne codent pas tant qu'il n'y
a pas commande dev validee et owner unique sur les fichiers sensibles.

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
- `presence_agents.md` pour les chantiers `CH-*`, conversations `CONV-*`,
  ownerships, worktrees, heartbeats et fins de mission.

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
designer, et aucun testeur ne valide une intention abstraite sans route livree.

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
Chantier: CH-YYYY-NNNN
Conversation: CONV-YYYY-NNNN
Branche: codex/<sprint>-<scope>
Worktree: <chemin absolu ou relatif>

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
- Utiliser `C:\Users\brice\Documents\CoproScope\instances\beauvallon_test` comme environnement de test local par defaut.
- Utiliser `examples/synthetic_copro` seulement pour les tests publics/CI et les exemples partageables.
- Utiliser toute autre instance privee seulement en lecture locale si explicitement demande.
- La copro demo publiable reste hors Drive, dans `Documents/CoproScope/instances/...`.

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
| docs de synthese (`README.md`, `feuille_de_route.md`) | Risque de conflits editoriaux | Owner documentation unique. |

## Ports et serveurs locaux

| Usage | Port |
|---|---:|
| Integration principale | 8765 |
| Agent UI/actions | 8766 |
| Agent compta | 8767 |
| Agent privacy | 8768 |
| Agent demo/docs | 8769 |

Exemple :

```powershell
.\server\.venv\Scripts\python.exe -m coproscope.cli ui open-test --instance-root C:\Users\brice\Documents\CoproScope\instances\beauvallon_test --year 2025 --host 127.0.0.1 --port 8766 --token beauvallon-test-local
```

Regle compatible antivirus : lancer le serveur dans un terminal PowerShell visible, au premier plan ou minimise par l'utilisateur, puis l'arreter avec `Ctrl+C`. Ne pas utiliser de fenetre cachee, de `Start-Process` cache, de scan de ports/processus, de `taskkill`, ni d'ouverture navigateur automatique. Si une page ne repond pas, lire le terminal serveur visible plutot que chercher et tuer un PID.

## Registre de suivi multi-agents

Le registre courant des agents est `presence_agents.md`. Ajouter ou mettre a
jour une ligne quand plusieurs agents tournent :

| Conversation | Roadmap | Chantier | Branche/worktree | Ownership | Statut | Expire | Prochain geste |
|---|---|---|---|---|---|---|---|
| `CONV-YYYY-NNNN` | `RM-YYYY-NNNN` | `CH-YYYY-NNNN` | `codex/...` / `...\_worktrees\...` | fichiers reserves | EN_COURS | date + fuseau | action concrete |

Statuts conseilles : `A_LANCER`, `EN_COURS`, `EN_ATTENTE_USER`, `BLOQUE`,
`PRET_A_INTEGRER`, `INTEGRE`, `EXPIRE`, `ABANDONNE`, `CLOTURE`.

## Vague active 21h15

La coordination exploitable pour le jalon du 2026-05-20 a 21h15 est tenue dans
[`orchestration_2115.md`](./orchestration_2115.md). Elle couvre:

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

## Garde-fous donnees

- Ne jamais commiter `coproscope-instances/`, `raw`, `restricted`, `.env.local`, tables de correspondance ou exports prives.
- Ne pas publier une instance seulement pseudonymisee.
- Ne pas melanger copro demo et instance privee dans le cockpit.
- La recette live locale par defaut se fait sur `C:\Users\brice\Documents\CoproScope\instances\beauvallon_test`.
- Les tests publics doivent passer sur `examples/synthetic_copro` ou sur une demo fictive.
- Toute sortie diffusable doit passer par PrivacyOps/BiffageOps ou par une transformation fictive robuste.
