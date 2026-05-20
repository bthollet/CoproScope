# Migration Drive vers local

Ce runbook decrit la bascule d'un workspace CoproScope stocke dans un dossier cloud vers une copie locale durable.

## Objectifs

- Ne plus travailler dans le dossier Drive historique.
- Verifier que la copie locale contient le repo et les dossiers utiles.
- Isoler la documentation d'instance du repo noyau.
- Inventorier les environnements et worktrees copies avant nettoyage.
- Preparer le futur vault chiffre synchronisable.

## Etapes

1. Verifier la copie locale avec `tools\transition\00_audit_local_readonly.bat`.
2. Ecrire les documents de transition avec `tools\transition\01_write_transition_docs.bat`.
3. Inventorier l'ancien `.venv` avec `tools\transition\02_inventory_venv.bat`.
4. Produire le patch de dependances avec `tools\transition\03_update_dependencies_plan.bat`.
5. Rebatir `server\.venv` avec `tools\transition\04_rebuild_server_venv.bat`.
6. Auditer les worktrees avec `tools\transition\05_worktree_audit.bat`.
7. Archiver les worktrees obsoletes seulement apres lecture du rapport.
8. Nettoyer l'ancien `.venv` seulement apres dry-run et validation.
9. Lancer les specs vault avec `tools\transition\09_vault_spec_scaffold.bat`.

## Garde-fous

- Ne jamais ecrire dans le dossier Drive historique.
- Ne jamais supprimer un `.venv` avant inventaire.
- Ne jamais supprimer un worktree avant audit Git.
- Ne jamais placer `server\.venv`, `.git`, caches ou exports temporaires dans le dossier sync.
- Ne jamais publier une documentation contenant une preuve ou decision d'instance dans le repo noyau.

## Sortie attendue

Apres migration, la racine locale contient:

- un repo noyau exploitable;
- des rapports de transition hors repo;
- une passation locale;
- un environnement serveur propre;
- aucun worktree actif pointant vers Drive;
- des specs vault prêtes pour implementation.
