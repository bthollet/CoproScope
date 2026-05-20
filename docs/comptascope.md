# ComptaScope

ComptaScope est la brique comptable de CoproScope. Elle ne remplace pas une comptabilite officielle: elle reconstruit des ecritures candidates a partir des pieces, afin d'aider un conseil syndical a controler, rapprocher et expliquer.

## Donnees produites

- `invoice_evidence_<annee>.csv`: factures candidates, montants, fournisseur, compte propose, anomalies.
- `ledger_reconstruction_<annee>.csv`: ecritures candidates debit charge / credit fournisseur.
- `accounting_controls_<annee>.csv`: controles P0/P1 a traiter.
- `expense_statement_lines_<annee>.csv`: lignes d'etat des depenses normalisees quand une source est configuree.
- `invoice_expense_matches_<annee>.csv`: rapprochements factures / etat des depenses, avec cause et prochaine action.
- `non_rapproches_prioritaires_<annee>.csv`: non-rapprochements et candidats ambigus classes par montant.
- `supplier_alias_suggestions_<annee>.csv`: alias fournisseurs deduits ou proposes a partir des montants et familles comptables.
- `rapport_comptascope_<annee>.md`: rapport explicatif local, notamment sur les causes de non-rapprochement.
- `coproscope_accounting_<annee>.duckdb`: base analytique locale si DuckDB est disponible.

Ces sorties sont un contrat de production: meme lorsqu'aucun etat des depenses n'est configure, ComptaScope cree les rapports et tables vides correspondantes. Les commandes `accounting controls`, `grist sync` et `evidence build` verifient que le rapport ComptaScope existe et relancent la reconstruction si une sortie de rapport manque.

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

## Rapprochement facture / etat des depenses

ComptaScope ne considere plus `NON_RAPPROCHE` comme une conclusion comptable. C'est un signal d'explication: l'automate n'a pas encore trouve de preuve deterministe suffisante.

Les statuts de rapprochement principaux sont:

- `MATCH_REFERENCE`: la reference de facture apparait dans une ligne de depense.
- `MATCH_AMOUNT_SUPPLIER`: montant TTC exact et fournisseur reconnu.
- `MATCH_AMOUNT_ALIAS`: montant TTC exact et alias fournisseur configure.
- `MATCH_AMOUNT_ACCOUNT_FAMILY`: montant TTC exact et compte/famille compatible, fournisseur a confirmer.
- `MATCH_SPLIT_SUM`: plusieurs lignes compatibles totalisent exactement la facture.
- `CANDIDAT_MONTANT_AMBIGU` ou `CANDIDAT_VENTILATION_AMBIGUE`: ComptaScope peut avancer, mais plusieurs choix restent possibles.
- `NON_RAPPROCHE`: reference, montant, fournisseur, alias et famille comptable ne suffisent pas encore.

Les alias et sources de lignes se configurent dans `settings.comptascope`:

```json
{
  "comptascope": {
    "invoice_evidence_csv": "./system/accounting/invoice_evidence_2025.csv",
    "expense_statement_lines": "./system/accounting/expense_statement_lines_2025.csv",
    "auto_infer_supplier_aliases": true,
    "auto_alias_min_evidence": 2,
    "supplier_aliases": [
      {"supplier": "JARDINS EXEMPLE SERVICES", "aliases": ["JEX"]}
    ]
  }
}
```

Si `invoice_evidence_csv` est renseigne, ComptaScope repart de ce registre deja extrait au lieu de rescanner les bruts. C'est le mode adapte aux reprises d'audit: on peut enrichir les rapprochements, les alias et les rapports sans refaire toute l'extraction documentaire.

Le mecanisme d'alias automatique reste prudent: un alias n'est auto-applique que lorsqu'au moins deux factures du meme fournisseur ont un montant exact, une famille comptable compatible, et le meme indice fournisseur structure dans l'etat des depenses. Les alias deduits seulement d'un libelle libre ou d'un cas unitaire restent proposes en `A_CONTROLER`.

## Limites

- Pas de saisie comptable complete.
- Pas de validation humaine simulee.
- Pas d'export de donnees reelles vers GitHub.
- Les comptes proposes sont des hypotheses de controle, pas une imputation definitive.
- Un rapprochement automatique reste une preuve candidate: les statuts `PROBABLE` et `PROBABLE_FORT` ne remplacent pas le grand livre ni la validation du conseil syndical.
