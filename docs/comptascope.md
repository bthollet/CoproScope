# ComptaScope

ComptaScope est la brique comptable de CoproScope. Elle ne remplace pas une comptabilite officielle: elle reconstruit des ecritures candidates a partir des factures candidates produites par FactureOps et des sources comptables disponibles, afin d'aider un conseil syndical a controler, rapprocher et expliquer.

Frontiere metier:

- DocOps produit la preuve documentaire brute.
- FactureOps extrait les factures et signale les anomalies de piece.
- ComptaScope reconstruit les ecritures candidates, rapproche l'etat des depenses et signale les controles comptables.

## Donnees produites

- `invoice_evidence_<annee>.csv`: factures candidates produites par FactureOps.
- `invoice_anomalies_<annee>.csv`: anomalies facture produites par FactureOps.
- `ledger_reconstruction_<annee>.csv`: ecritures candidates debit charge / credit fournisseur.
- `accounting_controls_<annee>.csv`: controles comptables et rapprochements a traiter.
- `expense_statement_lines_<annee>.csv`: lignes d'etat des depenses normalisees quand une source est configuree.
- `invoice_expense_matches_<annee>.csv`: rapprochements factures / etat des depenses, avec cause et prochaine action.
- `non_rapproches_prioritaires_<annee>.csv`: non-rapprochements et candidats ambigus classes par montant.
- `supplier_alias_suggestions_<annee>.csv`: alias fournisseurs deduits ou proposes a partir des montants et familles comptables.
- `rapport_comptascope_<annee>.md`: rapport explicatif local, avec synthese, priorites, causes, traitements locaux appliques et exemples a traiter.
- `coproscope_accounting_<annee>.duckdb`: base analytique locale si DuckDB est disponible.

Ces sorties sont un contrat de production: meme lorsqu'aucun etat des depenses n'est configure, ComptaScope cree les rapports et tables vides correspondantes. Les commandes `accounting controls`, `grist sync` et `evidence build` verifient que le rapport ComptaScope existe et relancent la reconstruction si une sortie de rapport manque.

## Commandes

```powershell
.\server\.venv\Scripts\python.exe -m coproscope.cli invoices extract --instance-root .\examples\synthetic_copro --year 2025
.\server\.venv\Scripts\python.exe -m coproscope.cli accounting reconstruct --instance-root .\examples\synthetic_copro --year 2025
.\server\.venv\Scripts\python.exe -m coproscope.cli accounting controls --instance-root .\examples\synthetic_copro --year 2025
.\server\.venv\Scripts\python.exe -m coproscope.cli grist sync --instance-root .\examples\synthetic_copro --dataset demo --year 2025
.\server\.venv\Scripts\python.exe -m coproscope.cli evidence build --instance-root .\examples\synthetic_copro --dataset demo --year 2025
```

Alias francais:

```powershell
.\server\.venv\Scripts\python.exe -m coproscope.cli factures extraire --instance-root .\examples\synthetic_copro --annee 2025
.\server\.venv\Scripts\python.exe -m coproscope.cli compta reconstituer --instance-root .\examples\synthetic_copro --annee 2025
.\server\.venv\Scripts\python.exe -m coproscope.cli compta controles --instance-root .\examples\synthetic_copro --annee 2025
```

## Statuts

- `PROBABLE`: extraction coherente mais non validee officiellement.
- `INCERTAIN`: extraction utile mais incomplete.
- `A_CONTROLER`: anomalie P0 ou information indispensable manquante.

## Rapprochement facture / etat des depenses

Les anomalies facture et les controles comptables sont volontairement separes. Une anomalie facture dit que la piece ou son extraction est incomplete. Un controle comptable dit qu'une ecriture, un rapprochement ou une preuve comptable doit etre traite.

ComptaScope ne considere plus `NON_RAPPROCHE` comme une conclusion comptable. C'est un signal d'explication: l'automate n'a pas encore trouve de preuve deterministe suffisante.

Le rapport utilise trois niveaux de lecture:

- `OK`: preuve locale suffisante pour rapprocher sans demander d'interpretation supplementaire.
- `P2`: candidat plausible trouve par traitement local; confirmation humaine attendue, mais ce n'est pas un blocage prioritaire.
- `P1`: aucun indice local suffisant; controle prioritaire du grand livre, de l'etat des depenses, de l'OCR ou de la piece.

Les statuts de rapprochement principaux sont:

- `MATCH_REFERENCE`: la reference de facture apparait dans une ligne de depense.
- `MATCH_AMOUNT_SUPPLIER`: montant TTC exact et fournisseur reconnu.
- `MATCH_AMOUNT_ALIAS`: montant TTC exact et alias fournisseur configure.
- `CANDIDAT_MONTANT_FAMILLE`: montant TTC exact et compte/famille compatible, fournisseur a confirmer (`P2`).
- `CANDIDAT_SOMME_MULTI_LIGNES`: plusieurs lignes compatibles totalisent exactement la facture (`P2`).
- `CANDIDAT_NOM_SIMILAIRE`: montant, famille et nom fournisseur tres proche concordent (`P2`).
- `CANDIDAT_DIVISION_EGALE`: le TTC d'une facture se divise exactement en lignes de meme montant (`P2`).
- `CANDIDAT_REGROUPEMENT_FACTURES`: plusieurs factures du meme fournisseur totalisent une ligne de depense (`P2`).
- `CANDIDAT_MONTANT_AMBIGU` ou `CANDIDAT_VENTILATION_AMBIGUE`: ComptaScope peut avancer, mais plusieurs choix restent possibles (`P2`).
- `CANDIDAT_MONTANT_SANS_NOM`, `CANDIDAT_FOURNISSEUR_SANS_MONTANT` ou `CANDIDAT_FAMILLE_SEULE`: un indice local existe, mais il ne suffit pas seul (`P2`).
- `NON_RAPPROCHE`: reference, montant, fournisseur, alias, similarite de nom et famille comptable ne suffisent pas (`P1`).

Les traitements locaux sont volontairement explicites et ordonnes:

1. reference de facture dans l'etat des depenses ;
2. montant TTC exact avec fournisseur reconnu ;
3. montant TTC exact avec alias fournisseur configure ou deduit ;
4. montant TTC exact avec nom fournisseur tres similaire ;
5. montant TTC exact avec famille comptable compatible ;
6. division d'une facture en lignes egales ;
7. somme de plusieurs lignes vers une facture ;
8. regroupement de plusieurs factures vers une ligne ;
9. classement des cas restants en candidats `P2` ou blocages `P1`.

Une similarite de nom evidente ne doit donc plus remonter comme blocage dur: elle devient un candidat `P2` a confirmer. L'outil ne valide pas le rapprochement a la place du conseil syndical, mais il produit une cause locale, une action attendue et une priorite.

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
