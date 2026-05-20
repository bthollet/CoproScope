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

## Preparation avant lancement

1. Stabiliser le depot principal : commit ou stash explicite des changements en cours.
2. Verifier la branche de base : `codex/bootstrap-coproscope-server` ou autre branche decidee.
3. Creer un worktree par agent.
4. Donner a chaque agent un contrat avec ownership fichiers.
5. Reserver un port local par agent si une interface est lancee.
6. Noter les agents actifs dans le registre de suivi.

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
Branche: codex/<sprint>-<scope>
Worktree: <chemin absolu ou relatif>

Tu n'es pas seul dans le codebase. Ne revert jamais les changements des autres.

Ownership modifiable:
- <dossier/fichier 1>
- <dossier/fichier 2>

Hors perimetre:
- <dossier/fichier a ne pas toucher>

Donnees:
- Ne jamais ajouter de donnees reelles dans Git.
- Utiliser `examples/synthetic_copro` pour les tests publics.
- Utiliser l'instance privee seulement en lecture locale si explicitement demande.
- La copro demo publiable reste hors Drive, dans `Documents/CoproScope/instances/...`.

Verification:
- <commande test 1>
- <commande test 2>
- checks UI attendus si pertinent.

Livrable final:
- fichiers modifies ;
- tests lances ;
- limites connues ;
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
.\server\.venv\Scripts\python.exe -m coproscope.cli ui serve --instance-root ..\coproscope-instances\beauvallon --year 2025 --port 8766
```

## Registre de suivi multi-agents

Ajouter une section dans le registre courant quand plusieurs agents tournent :

| Agent | Branche | Worktree | Ownership | Statut | Tests | Notes integration |
|---|---|---|---|---|---|---|
| UI/actions | `codex/sprint2-actions` | `..\coproscope-agent-sprint2-actions` | web UI/actions | EN_COURS | a venir | Ne touche pas privacy. |
| Compta | `codex/sprint3-compta` | `..\coproscope-agent-sprint3-compta` | vue comptes | EN_COURS | a venir | Ne touche pas CLI. |

Statuts conseilles : `A_LANCER`, `EN_COURS`, `PRET_A_INTEGRER`, `INTEGRE`, `BLOQUE`.

## Verification minimale d'integration

Depuis `server/` :

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

Checks UI depuis la racine :

```powershell
Invoke-WebRequest -Uri http://127.0.0.1:8765/health -UseBasicParsing
Invoke-WebRequest -Uri http://127.0.0.1:8765/ -UseBasicParsing
Invoke-WebRequest -Uri http://127.0.0.1:8765/comptes -UseBasicParsing
Invoke-WebRequest -Uri http://127.0.0.1:8765/confidentialite -UseBasicParsing
```

## Garde-fous donnees

- Ne jamais commiter `coproscope-instances/`, `raw`, `restricted`, `.env.local`, tables de correspondance ou exports prives.
- Ne pas publier une instance seulement pseudonymisee.
- Ne pas melanger copro demo et instance privee dans le cockpit.
- Les tests publics doivent passer sur `examples/synthetic_copro` ou sur une demo fictive.
- Toute sortie diffusable doit passer par PrivacyOps/BiffageOps ou par une transformation fictive robuste.
