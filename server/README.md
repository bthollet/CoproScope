# CoproScope Server

`server/` contient le produit executable: CLI, modules metier, interface locale, configs, templates et tests.

## Prerequis

- Windows PowerShell recommande pour les commandes ci-dessous.
- Python 3.11 ou plus recent.
- Aucune donnee reelle ni secret pour lancer l'instance synthetique.

## Installation Locale

Depuis `server/`:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e ".[ui]"
```

Pour les controles securite locaux:

```powershell
.\.venv\Scripts\python.exe -m pip install -e ".[security]"
```

## Tester Maintenant

Depuis la racine du depot, le check court recommande pour une reprise agent est:

```powershell
.\tools\agent-check.cmd
```

Il verifie le statut Git, le garde-fou 600 lignes et un noyau de tests rapides.

Pour ajouter les tests UI transverses:

```powershell
.\tools\agent-check.cmd -Ui
```

Pour la suite complete depuis `server/`:

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

Les tests publics utilisent l'instance fictive `examples/synthetic_copro`.

## Commandes Par Usage

Les commandes suivantes se lancent depuis la racine du depot avec l'interpreteur de `server/.venv`.

| Usage | Commande |
|---|---|
| Diagnostic | `.\server\.venv\Scripts\python.exe -m coproscope.cli doctor --instance-root .\examples\synthetic_copro` |
| Pipeline documentaire | `.\server\.venv\Scripts\python.exe -m coproscope.cli pipeline run --instance-root .\examples\synthetic_copro` |
| Confidentialite | `.\server\.venv\Scripts\python.exe -m coproscope.cli privacy screen-existing --instance-root .\examples\synthetic_copro` |
| File de biffage | `.\server\.venv\Scripts\python.exe -m coproscope.cli privacy redaction-queue --instance-root .\examples\synthetic_copro` |
| Factures | `.\server\.venv\Scripts\python.exe -m coproscope.cli invoices extract --instance-root .\examples\synthetic_copro --year 2025` |
| Comptes | `.\server\.venv\Scripts\python.exe -m coproscope.cli accounting reconstruct --instance-root .\examples\synthetic_copro --year 2025` |
| Controles comptables | `.\server\.venv\Scripts\python.exe -m coproscope.cli accounting controls --instance-root .\examples\synthetic_copro --year 2025` |
| Demo fictive | `.\server\.venv\Scripts\python.exe -m coproscope.cli demo build --source-instance-root .\examples\synthetic_copro --output-instance "$env:USERPROFILE\CoproScope\instances\demo_fictive_tilleuls" --mode fictive --year 2025` |
| UI locale | `.\server\.venv\Scripts\python.exe -m coproscope.cli ui open-test --instance-root "$env:USERPROFILE\CoproScope\instances\demo_fictive_tilleuls" --year 2025 --port 8765` |
| Audit publication | `.\server\.venv\Scripts\python.exe -m coproscope.cli share-audit --repo-root . --config .\server\src\coproscope\configs\github_sharing.default.yml` |
| Export public | `.\server\.venv\Scripts\python.exe -m coproscope.cli share-export --repo-root . --config .\server\src\coproscope\configs\github_sharing.default.yml --output-dir ..\public-export --clean` |

`ui open-test` lance le serveur au premier plan, affiche l'URL locale tokenisee et s'arrete avec `Ctrl+C`.

## Organisation

- `src/coproscope/cli.py`: point d'entree CLI.
- `src/coproscope/core/`: logique transverse.
- `src/coproscope/modules/`: modules fonctionnels.
- `src/coproscope/vault/`: evenements, reconstruction, sync, resilience.
- `src/coproscope/web/`: application locale, routes, templates, styles.
- `src/coproscope/configs/`: configurations par defaut.
- `src/coproscope/templates/`: gabarits CSV et sorties bootstrap.
- `tests/`: verification du socle public.

## Frontiere Public / Prive

Le depot public expose le code, les schemas, les tests, la documentation et les exemples fictifs. Les instances reelles, OCR prives, sorties brutes, secrets, chemins locaux et cartes de biffage restent hors Git.

Avant de publier:

```powershell
.\server\.venv\Scripts\python.exe -m coproscope.cli share-audit --repo-root . --config .\server\src\coproscope\configs\github_sharing.default.yml
```

## CI Publique

Le workflow GitHub Actions `.github/workflows/ci.yml` installe le paquet serveur avec les extras publics, puis lance:

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
.\.venv\Scripts\python.exe -m pip_audit . --skip-editable --progress-spinner off
.\.venv\Scripts\python.exe -m bandit -r src -q --severity-level high
```

Les signaux Bandit bas/moyens restent a traiter en durcissement progressif; la CI bloque d'abord les alertes haute severite.
