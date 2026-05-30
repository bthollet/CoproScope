# Reprise par agents paralleles

Ce document sert a lancer plusieurs conversations Codex sans collision.

## Preconditions

- Travailler depuis `<COPROSCOPE_HOME>\coproscope`.
- Ne jamais travailler dans un `coproscope-agent-*` dont `.git` pointe vers `<DRIVE_SYNCHRONISE>`.
- Creer les nouveaux worktrees sous `<COPROSCOPE_HOME>\_worktrees`.
- Donner a chaque agent une branche `codex/<sujet>` et un perimetre de fichiers exclusif.
- Relancer `tools\transition\00_audit_local_readonly.bat` avant integration.

## Lots paralleles possibles

### Agent A - Specs vault

Objectif: durcir les specifications sans modifier le code.

Fichiers autorises:

- `docs/vault_format.md`
- `docs/signatures_historique.md`
- `docs/objets_metier_evenements_v1.md`
- `docs/plugins_officiels.md`

Interdits:

- `server/src/coproscope/vault/**`
- `server/src/coproscope/cli.py`
- `tools/transition/**`

### Agent B - Tests vault

Objectif: enrichir les tests du prototype vault.

Fichiers autorises:

- `server/tests/test_vault.py`

Interdits:

- implementation vault;
- docs;
- scripts de transition.

### Agent C - Batchs transition

Objectif: renforcer les scripts Windows et leurs rapports.

Fichiers autorises:

- `tools/transition/**`
- `docs/archive/notes_integration/batchs_transition_locale.md`

Interdits:

- `server/src/coproscope/vault/**`
- `server/src/coproscope/cli.py`
- autres docs produit.

### Agent D - Reconstruction locale

Objectif: preparer Sprint 3, sans toucher a l'UI.

Fichiers autorises:

- nouveaux fichiers sous `server/src/coproscope/vault/`
- `server/tests/test_vault.py`

Interdits:

- `server/src/coproscope/web/**`
- scripts de transition;
- docs hors specs vault.

### Agent E - UI atelier piece

Objectif: preparer Sprint 4 seulement apres stabilisation de l'API vault.

Fichiers autorises a definir au moment du lancement:

- `server/src/coproscope/web/**`
- tests UI dedies.

Interdits:

- format vault;
- crypto/signatures;
- scripts de migration.

## Prompt de lancement type

```text
Travaille dans <COPROSCOPE_HOME>\coproscope. Ne touche qu'aux fichiers autorises du lot <X>. Ne modifie aucun fichier Drive, aucun .venv, aucun .git, aucun worktree existant pointant vers Drive. Commence par lire docs/reprise_agents_paralleles_vault.md et fais un git status. Termine avec les tests pertinents et la liste exacte des fichiers modifies.
```

## Moment recommande

Les agents paralleles peuvent commencer des que le socle `vault init/import/status/verify/snapshot`, les docs de transition et les batchs d'audit sont stabilises dans une branche locale. Si le socle n'est pas encore committe, chaque agent doit recevoir une copie claire du statut initial pour ne pas confondre changements existants et changements a produire.
