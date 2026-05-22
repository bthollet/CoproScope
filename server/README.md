# CoproScope Server

Paquet backend du produit CoproScope.

## Ce que contient `server/`

- la CLI `coprocs` ;
- un serveur MCP minimal compatible stdio ;
- le socle de schemas, configurations, prompts et templates ;
- les tests du noyau public.

## Organisation

- `src/coproscope/cli.py` : point d'entree CLI ;
- `src/coproscope/core/` : logique transverse ;
- `src/coproscope/modules/` : modules fonctionnels ;
- `src/coproscope/configs/` : configurations par defaut ;
- `src/coproscope/schemas/` : contrats de donnees ;
- `src/coproscope/templates/` : gabarits CSV et sorties bootstrap, y compris pour la couche Audit360 ;
- `tests/` : verification du socle public.

## Extraction publique Audit360

Le depot public expose maintenant une premiere extraction generique de la couche `Audit360`:

- gabarits `constats_normalises.csv`, `repertoire_controles.csv` et `synthese_controles.csv` ;
- schemas associes pour decrire ces sorties sans publier de donnees reelles.

L'objectif est de partager la forme reutilisable des controles et diligences, pas les contenus sensibles d'une copropriete reelle.

## Commandes utiles

```powershell
.\.venv\Scripts\python.exe -m coproscope.cli doctor --instance-root ..\examples\synthetic_copro
.\.venv\Scripts\python.exe -m coproscope.cli pipeline run --instance-root ..\examples\synthetic_copro
.\.venv\Scripts\python.exe -m coproscope.cli invoices extract --instance-root ..\examples\synthetic_copro --year 2025
.\.venv\Scripts\python.exe -m coproscope.cli accounting reconstruct --instance-root ..\examples\synthetic_copro --year 2025
.\.venv\Scripts\python.exe -m coproscope.cli share-audit --repo-root .. --config .\src\coproscope\configs\github_sharing.default.yml
.\.venv\Scripts\python.exe -m coproscope.cli share-export --repo-root .. --config .\src\coproscope\configs\github_sharing.default.yml --output-dir ..\public-export --clean
```

## Controles securite

```powershell
.\.venv\Scripts\python.exe -m pip install -e ".[security]"
.\.venv\Scripts\python.exe -m pip_audit
.\.venv\Scripts\bandit.exe -r src -q
pre-commit run gitleaks --all-files
```

## CI publique

Le workflow GitHub Actions `.github/workflows/ci.yml` installe le paquet serveur
avec les extras publics necessaires, puis lance:

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
.\.venv\Scripts\python.exe -m pip_audit . --skip-editable --progress-spinner off
.\.venv\Scripts\python.exe -m bandit -r src -q --severity-level high
```

La CI utilise `examples/synthetic_copro` via les tests publics. Les recettes
locales privees, comme `instance_privee_test`, restent hors GitHub Actions. Les
signaux Bandit bas/moyens restent a traiter en durcissement progressif, sans
bloquer la premiere CI.
