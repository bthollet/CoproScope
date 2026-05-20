# Consignes agents CoproScope

Ce depot peut etre travaille par plusieurs agents en parallele, a condition de ne pas partager le meme arbre de travail pour des modifications concurrentes.

## Regle courte

- Un agent = une branche `codex/<sprint>-<scope>` = un worktree dedie.
- Un agent possede un perimetre de fichiers explicite.
- Les instances privees restent hors depot et ne sont jamais commitees.
- Les sorties publiables utilisent l'instance synthetique ou une copro demo fictive hors Drive.
- Le coordinateur integre les branches une par une et relance les tests.

## Demarrage recommande

Depuis la racine du depot principal, apres avoir stabilise ou commite les changements en cours :

```powershell
git fetch origin
git switch codex/bootstrap-coproscope-server
git pull --ff-only

git worktree add ..\coproscope-agent-sprint2-actions -b codex/sprint2-actions
git worktree add ..\coproscope-agent-sprint3-compta -b codex/sprint3-compta
git worktree add ..\coproscope-agent-sprint4-privacy -b codex/sprint4-privacy
```

Si une branche existe deja, retirer `-b <branche>` et indiquer la branche existante a la fin de la commande.

## Contrat a donner a chaque agent

Copier-coller un contrat court au lancement :

```text
Mission: Sprint <numero> - <objectif>
Branche/worktree: <branche> / <chemin>
Tu n'es pas seul dans le codebase. Ne revert jamais les changements des autres.
Ownership fichiers: <liste de dossiers/fichiers modifiables>
Fichiers a eviter: <liste>
Donnees: pas de donnees privees dans Git ; instance privee uniquement en lecture locale.
Verification attendue: <commandes de test ou checks UI>
Livrable final: resume, fichiers modifies, limites, tests lances.
```

## Ports locaux

Ne pas lancer deux interfaces sur le meme port.

| Agent | Port conseille |
|---|---:|
| Coordinateur | 8765 |
| UI/actions | 8766 |
| ComptaScope | 8767 |
| Privacy/DocOps | 8768 |
| Demo/docs | 8769 |

## Perimetres qui se parallelisent bien

| Agent | Ownership principal |
|---|---|
| UI/actions | `server/src/coproscope/web/`, `server/tests/test_ui_demo.py` |
| ComptaScope guide | `server/src/coproscope/web/viewmodel.py`, templates comptes, docs ComptaScope |
| Privacy/DocOps | `server/src/coproscope/modules/privacyops.py`, templates confidentialite/documents, tests privacy |
| Decision-action-preuve | nouveau module/registre dedie, tests dedies, docs fonctions cibles |
| Documentation/orchestration | `docs/`, `README.md`, registres de suivi |

Quand deux agents doivent toucher `viewmodel.py`, le coordinateur tranche avant lancement : un seul agent possede ce fichier, les autres produisent une note d'integration ou travaillent sur des templates/tests.

## Integration

Le coordinateur :

1. verifie `git status --short` dans chaque worktree ;
2. relit les diffs ;
3. integre une branche a la fois ;
4. resout les conflits sans supprimer le travail d'un autre agent ;
5. lance au minimum `.\server\.venv\Scripts\python.exe -m unittest discover -s tests -v` depuis `server/` ;
6. met a jour le registre de suivi ;
7. pousse seulement les changements genericisables.

Voir aussi : [`docs/orchestration_agents.md`](./docs/orchestration_agents.md).
