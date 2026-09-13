# Batchs de transition locale

Les batchs vivent dans `tools\transition`. Chaque `.bat` appelle le `.ps1` du meme nom avec PowerShell en mode non interactif. Les rapports sont ecrits hors repo dans `<COPROSCOPE_HOME>\_transition_reports`.

Les helpers communs sont dans `tools\transition\_transition_common.ps1`:

- horodatage ISO pour tous les rapports;
- capture homogene des commandes, avec commande, dossier de travail, code retour et sortie;
- detection explicite des commandes absentes;
- verification stricte des chemins avant les operations de deplacement.
- tests Python lances avec `PYTHONDONTWRITEBYTECODE=1` pour eviter les ecritures de bytecode hors perimetre.

## Ordre recommande

1. `00_audit_local_readonly.bat`
2. `01_write_transition_docs.bat`
3. `02_inventory_venv.bat`
4. `03_update_dependencies_plan.bat`
5. `04_rebuild_server_venv.bat`
6. `05_worktree_audit.bat`
7. `06_archive_stale_worktrees.bat`
8. `07_cleanup_root_venv_dryrun.bat`
9. `08_cleanup_root_venv_execute.bat`
10. `09_vault_spec_scaffold.bat`
11. `10_vault_prototype_tests.bat`

## Batchs sans effet destructif

Ces batchs peuvent etre lances pour audit local. Ils produisent des rapports, mais ne nettoient pas de fichier du repo.

| Batch | Rapport principal | Effet |
|---|---|---|
| `00_audit_local_readonly` | `00_audit_local_*.md` | Verifie structure locale, Git status et worktrees. |
| `02_inventory_venv` | `02_venv_inventory.md`, `02_venv_inventory.json`, `02_dependency_gap.md` | Inventorie l'ancien `.venv` sans suppression. |
| `03_update_dependencies_plan` | `03_pyproject_dependency_patch.diff` | Produit un plan de dependances, sans modifier `pyproject.toml`. |
| `05_worktree_audit` | `05_worktree_audit_*.md` | Detecte les worktrees et pointeurs Git vers Drive. |
| `06_archive_stale_worktrees` | `06_archive_stale_worktrees_*.md` | Dry-run par defaut; archive seulement avec `-Execute`. |
| `07_cleanup_root_venv_dryrun` | `07_cleanup_root_venv_dryrun_*.md` | Prepare le nettoyage de l'ancien `.venv`, sans supprimer; liste les `__pycache__` seulement pour revue manuelle. |
| `10_vault_prototype_tests` | `10_vault_tests_*.md` | Lance les tests du prototype vault. |

## Batchs avec effets d'ecriture

Ces batchs doivent etre lances seulement quand leur effet est voulu.

| Batch | Effet |
|---|---|
| `01_write_transition_docs` | Cree les docs de passation manquantes; avec `-ForceRewrite`, sauvegarde puis reecrit. |
| `04_rebuild_server_venv` | Cree ou reutilise `server\.venv`, installe les dependances et lance `tools status`. |
| `08_cleanup_root_venv_execute` | Archive puis retire l'ancien `.venv` racine apres dry-run recent et `tools status` valide. |
| `09_vault_spec_scaffold` | Cree les specs vault generiques si elles manquent. |

## Reprises pretes a dicter

- Lance `tools\transition\00_audit_local_readonly.bat` puis resume le rapport.
- Lance `tools\transition\02_inventory_venv.bat`, puis dis-moi quelles dependances manquent dans `pyproject.toml`.
- Lance `tools\transition\05_worktree_audit.bat` et prepare le nettoyage des worktrees Drive sans supprimer.
- Lance `tools\transition\06_archive_stale_worktrees.bat` pour obtenir le dry-run d'archivage.
- Lance `tools\transition\07_cleanup_root_venv_dryrun.bat` avant toute suppression de l'ancien `.venv`.
- Lance `tools\transition\10_vault_prototype_tests.bat` et resume les tests vault.

## Garde-fous

- Ne jamais lancer `06_archive_stale_worktrees.ps1 -Execute` sans relire le rapport dry-run.
- Ne jamais lancer `08_cleanup_root_venv_execute.bat` sans un rapport `07_cleanup_root_venv_dryrun` de moins de 24 heures.
- Le dry-run `07_cleanup_root_venv_dryrun` exclut les chemins sous `.git` et `.venv`.
- Ne jamais travailler dans un `coproscope-agent-*` dont `.git` pointe vers `<DRIVE_SYNCHRONISE>`.
- Les deplacements verifient que le chemin source reste sous `<COPROSCOPE_HOME>`.
- Aucun `.git` ni `.venv` ne doit entrer dans un vault, un dossier cloud sync, un export d'instance ou une documentation d'instance.
