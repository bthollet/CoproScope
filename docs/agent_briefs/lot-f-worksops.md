# Brief agent - Lot F WorksOps travaux

Mission : creer un dossier travaux minimal mais probatoire.

Branche conseillee : `codex/lot-f-worksops`  
Port conseille : `8773`

## Objectif

Suivre une operation travaux avec :

- decision ;
- devis ;
- fournisseur ;
- assurance ;
- facture ;
- reception ;
- garantie ;
- ecarts et preuves.

## Ownership

Modifiable :

- nouveau module WorksOps ;
- tests travaux ;
- vue travaux ou extension chantiers ;
- docs travaux.

A eviter sans coordination :

- ComptaScope sauf lecture de factures/actions ;
- Decision-action-preuve sauf liens definis ;
- PrivacyOps.

## Livrables

- registre travaux ;
- chronologie par operation ;
- checklist preuves ;
- export synthese travaux ;
- tests sur corpus synthetique.

## Verification

Depuis `server/` :

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

Critere UX : le CS doit voir en une page ou en est chaque operation et quelle preuve manque.

