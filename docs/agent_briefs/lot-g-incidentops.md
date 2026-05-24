# Brief agent - Lot G IncidentOps signalements

Mission : outiller les incidents et sinistres du quotidien.

Branche conseillee : `codex/lot-g-incidentops`  
Port conseille : `8774`

## Objectif

Creer un registre incidents avec :

- date ;
- lieu ;
- description ;
- photo ou piece ;
- syndic/prestataire ;
- statut ;
- preuve de cloture ;
- lien contrat ou assurance si disponible.

## Ownership

Modifiable :

- nouveau module IncidentOps ;
- tests incidents ;
- vue incident ou extension chantiers ;
- docs incidents.

A eviter sans coordination :

- WorksOps si un autre agent le possede ;
- ContractOps non defini ;
- donnees reelles.

## Livrables

- registre incidents ;
- statuts simples ;
- actions de relance ;
- liens vers preuves ;
- export liste incidents ouverts.

## Verification

Depuis `server/` :

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

Critere UX : un incident ouvert doit avoir une prochaine action et une preuve attendue.

