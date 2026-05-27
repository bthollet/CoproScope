# Runbook - reconstruction base et projections CoproScope

Rattachement: `RM-2026-0004` / `CH-2026-0010`.
Date: 2026-05-22.

Ce runbook transforme une intuition du type "il faut reconstruire la base" en
operation reproductible, verifiable et reversible. Dans CoproScope, il n'existe
pas une base unique: l'etat est partage entre sources, registres, projections,
outputs analytiques et vault local.

## Vocabulaire

- Source a preserver: `instance.yml`, documents locaux, matrices/configuration,
  registres de travail, vault local et sync.
- Registre: CSV local qui porte un etat de travail ou une trace humaine.
- Projection: sortie derivee reconstructible, par exemple rapports, staging,
  CSV analytiques, DuckDB ComptaScope, exports derives.
- Rebuild: regeneration controlee d'une projection depuis les sources.
- GO rebuild: decision explicite apres diagnostic, sauvegarde et postchecks
  definis.

## No-Go Immediats

Ne pas reconstruire si:

- la sauvegarde complete n'est pas verifiee;
- `vault verify` remonte une erreur;
- le perimetre de rebuild n'est pas nomme;
- un autre agent possede les memes fichiers ou la meme instance;
- la demande implique de supprimer `raw`, `restricted`, cles, events, blobs,
  mappings de biffage, `.env.local`, registres demandes/decisions/incidents ou
  logs non sauvegardes.

## Preflight

Exemple pour `beauvallon_test`:

```powershell
$InstanceRoot = "C:\Users\brice\CoproScope\instances\beauvallon_test"
$Runtime = Join-Path $InstanceRoot "900_Systeme_Audit\coproscope_runtime"
$Stamp = Get-Date -Format "yyyyMMdd-HHmmss"
$BackupRoot = "C:\Users\brice\CoproScope\dev\instance_support\sauvegardes\beauvallon_test\$Stamp"
New-Item -ItemType Directory -Force -Path $BackupRoot
```

Créer un manifeste avant toute commande qui écrit:

```powershell
Get-ChildItem -LiteralPath $InstanceRoot -Recurse -File -Force |
  ForEach-Object {
    [pscustomobject]@{
      Rel = $_.FullName.Substring($InstanceRoot.Length).TrimStart("\")
      Bytes = $_.Length
      LastWriteUtc = $_.LastWriteTimeUtc.ToString("o")
      Sha256 = (Get-FileHash -LiteralPath $_.FullName -Algorithm SHA256).Hash
    }
  } | Export-Csv "$BackupRoot\manifest_before.csv" -NoTypeInformation -Encoding UTF8
```

Verifier le vault:

```powershell
.\server\.venv\Scripts\python.exe -B -m coproscope.cli vault status --local-root "$Runtime\vault_local" --sync-root "$Runtime\vault_sync_chiffre_test_local"
.\server\.venv\Scripts\python.exe -B -m coproscope.cli vault verify --local-root "$Runtime\vault_local" --sync-root "$Runtime\vault_sync_chiffre_test_local"
```

## Sauvegarde

La sauvegarde complete est obligatoire avant tout rebuild:

```powershell
robocopy $InstanceRoot "$BackupRoot\instance" /E /COPY:DAT /DCOPY:DAT /R:1 /W:1 /XJ /MT:8
if ($LASTEXITCODE -gt 7) { throw "Robocopy failed: $LASTEXITCODE" }
```

Refaire un manifeste sur `$BackupRoot\instance` et comparer avec
`manifest_before.csv`. Le GO sauvegarde n'est donne que si les chemins, tailles
et hash attendus concordent.

## Rebuilds Cibles

Toujours preferer le plus petit rebuild utile.

### Diagnostic general

```powershell
.\server\.venv\Scripts\python.exe -B -m coproscope.cli doctor --instance-root $InstanceRoot
```

### Projections documentaires prudentes

```powershell
.\server\.venv\Scripts\python.exe -B -m coproscope.cli pipeline run --instance-root $InstanceRoot --no-copy --docai off
```

Cette commande regenere inventaire, textes, classification, screening,
biffage, completude, KPI, AG et diligence. Elle n'est pas un rebuild ComptaScope
et ne reconstruit pas le vault.

### ComptaScope

```powershell
.\server\.venv\Scripts\python.exe -B -m coproscope.cli accounting reconstruct --instance-root $InstanceRoot --year 2025
.\server\.venv\Scripts\python.exe -B -m coproscope.cli accounting controls --instance-root $InstanceRoot --year 2025
```

### Decisions et incidents

```powershell
.\server\.venv\Scripts\python.exe -B -m coproscope.cli decisions build --instance-root $InstanceRoot
.\server\.venv\Scripts\python.exe -B -m coproscope.cli incidents build --instance-root $InstanceRoot
```

Ces commandes peuvent reecrire des registres. Sauvegarde et comparaison avant /
apres obligatoires.

### Vault

```powershell
.\server\.venv\Scripts\python.exe -B -m coproscope.cli vault snapshot --local-root "$Runtime\vault_local" --sync-root "$Runtime\vault_sync_chiffre_test_local"
```

Un snapshot est un accelerateur de reconstruction. Ce n'est pas une commande de
rebuild des projections CSV/DB.

## Postchecks

Verifier au minimum:

- `vault verify` reste valide;
- les registres importants existent et ont des compteurs coherents;
- les projections attendues existent: rapports, completude, compta, decisions,
  incidents selon le scope;
- aucun export ne fuit chemins locaux, sources brutes, logs, mappings de
  biffage ou donnees personnelles;
- les routes locales restent protegees par token.

Paniers de tests conseilles depuis `server/`:

```powershell
.\.venv\Scripts\python.exe -B -m unittest tests.test_pipeline tests.test_comptascope tests.test_passation_exports tests.test_security_no_private_sync_leaks -v
.\.venv\Scripts\python.exe -B -m unittest tests.test_vault tests.test_vault_core_hardening tests.test_vault_reconstruction_local tests.test_vault_reconstruction_archive tests.test_vault_resilience tests.test_vault_sync_profiles tests.test_vault_sync_alerts -v
.\.venv\Scripts\python.exe -B -m unittest tests.test_ui_security_routes tests.test_ui_smoke_routes_expanded tests.test_ui_passation_export_route tests.test_ui_depot_flow tests.test_ui_atelier_piece tests.test_ui_requests_route tests.test_ui_pilotage_route tests.test_ui_live_ux_contract -v
```

Si un rebuild touche des modules partages ou les projections globales, lancer
ensuite la suite complete:

```powershell
.\.venv\Scripts\python.exe -B -m unittest discover -s tests -v
```

## Roles Agile

- Coordinateur-scribe: declare `RM-*`, `CH-*`, `CONV-*`, perimetre et GO/NO-GO.
- Architecture DB/projections: separe source, registre, projection et cache.
- QA sauvegarde/non-regression: bloque si backup ou postchecks sont incomplets.
- Process produit: tient le vocabulaire et transforme le cycle en procedure
  reusable.
- Testeur novice: requis si le rebuild sert une recette UI ou une passation.

## Decision Finale

Le `BOT-END` doit indiquer:

- scope de rebuild execute;
- sauvegarde et manifeste;
- commandes lancees;
- fichiers/projections modifies;
- tests et routes verifies;
- verdict `GO`, `NO-GO` ou `GO_TECHNIQUE_RECETTE_UI_RESTANTE`;
- rollback possible depuis `$BackupRoot`.
