# ComptaScope

ComptaScope est la brique comptable de CoproScope. Elle ne remplace pas une comptabilite officielle: elle reconstruit des ecritures candidates a partir des pieces, afin d'aider un conseil syndical a controler, rapprocher et expliquer.

## Donnees produites

- `invoice_evidence_<annee>.csv`: factures candidates, montants, fournisseur, compte propose, anomalies.
- `ledger_reconstruction_<annee>.csv`: ecritures candidates debit charge / credit fournisseur.
- `accounting_controls_<annee>.csv`: controles P0/P1 a traiter.
- `coproscope_accounting_<annee>.duckdb`: base analytique locale si DuckDB est disponible.

## Commandes

```powershell
.\server\.venv\Scripts\python.exe -m coproscope.cli accounting reconstruct --instance-root .\examples\synthetic_copro --year 2025
.\server\.venv\Scripts\python.exe -m coproscope.cli accounting controls --instance-root .\examples\synthetic_copro --year 2025
.\server\.venv\Scripts\python.exe -m coproscope.cli grist sync --instance-root .\examples\synthetic_copro --dataset demo --year 2025
.\server\.venv\Scripts\python.exe -m coproscope.cli evidence build --instance-root .\examples\synthetic_copro --dataset demo --year 2025
```

Alias francais:

```powershell
.\server\.venv\Scripts\python.exe -m coproscope.cli compta reconstituer --instance-root .\examples\synthetic_copro --annee 2025
.\server\.venv\Scripts\python.exe -m coproscope.cli compta controles --instance-root .\examples\synthetic_copro --annee 2025
```

## Statuts

- `PROBABLE`: extraction coherente mais non validee officiellement.
- `INCERTAIN`: extraction utile mais incomplete.
- `A_CONTROLER`: anomalie P0 ou information indispensable manquante.

## Limites

- Pas de saisie comptable complete.
- Pas de validation humaine simulee.
- Pas d'export de donnees reelles vers GitHub.
- Les comptes proposes sont des hypotheses de controle, pas une imputation definitive.
