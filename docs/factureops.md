# FactureOps

FactureOps est la couche d'extraction et d'analyse des factures. Elle se place entre DocOps et ComptaScope.

DocOps produit la preuve documentaire brute: inventaire, hash, texte natif, OCR et artefacts DocAI locaux. FactureOps transforme cette preuve en factures candidates. ComptaScope consomme ensuite ces factures pour reconstruire des ecritures candidates, rapprocher l'etat des depenses et produire les controles comptables.

## Sorties

- `invoice_evidence_<annee>.csv`: registre des factures candidates.
- `invoice_anomalies_<annee>.csv`: anomalies facture, separees des controles comptables.

Ces fichiers restent temporairement dans `accounting_dir/<annee>` pour conserver la compatibilite avec Grist, Evidence et les rapports existants.

## Intensite des outils

Les niveaux `L0` a `L4` decrivent l'intensite des outils mobilises. Ils ne sont pas des priorites d'anomalie.

| Niveau | Role |
| --- | --- |
| `L0_STRUCTURED_SOURCE` | CSV precharge, Factur-X/XML/UBL/CII ou source structuree declaree. |
| `L1_NATIVE_TEXT` | Texte natif et parseurs deterministes. |
| `L2_LOCAL_OCR` | OCR local ou sidecar OCR. |
| `L3_LOCAL_STRUCTURE_OR_VISUAL` | Docling, tables/layout locaux ou revue visuelle locale. |
| `L4_AI_OR_ONLINE_REVIEW` | IA ou vision externe; confirmation explicite requise; jamais validation comptable finale. |

Les priorites `P0`, `P1` et `P2` restent reservees aux anomalies, controles et rapprochements.

## Anomalies facture

FactureOps signale les anomalies de piece, par exemple fournisseur absent, numero de facture absent, date absente, TTC absent, SIREN/SIRET absent, incoherence HT/TVA/TTC, doublon potentiel ou facture hors exercice.

Ces anomalies ne disent pas encore que la comptabilite est fausse. Elles disent que le registre facture doit etre complete ou controle avant de servir de preuve comptable forte.

## Commande

```powershell
.\server\.venv\Scripts\python.exe -m coproscope.cli invoices extract --instance-root .\examples\synthetic_copro --year 2025
.\server\.venv\Scripts\python.exe -m coproscope.cli factures extraire --instance-root .\examples\synthetic_copro --annee 2025
```

## Limites

- FactureOps ne valide pas l'imputation comptable.
- FactureOps ne rapproche pas l'etat des depenses.
- FactureOps ne transforme pas une extraction IA en preuve finale.
- Les sources privees et artefacts reels restent hors GitHub.
