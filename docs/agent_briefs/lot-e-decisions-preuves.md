# Brief agent - Lot E Decision -> action -> preuve

Mission : construire le registre differenciant qui fait vivre les decisions d'AG apres le PV.

Branche conseillee : `codex/lot-e-decisions-preuves`  
Port conseille : `8772`

## Objectif

Creer un registre reliant :

- decision AG ;
- action attendue ;
- responsable ;
- echeance ;
- preuve attendue ;
- statut ;
- documents, demandes, factures ou travaux rattaches.

## Ownership

Modifiable :

- nouveau module dedie ;
- registres/tests dedies ;
- vue dediee ou enrichissement de la vue chantiers ;
- docs fonctions cibles.

A eviter sans coordination :

- refonte AGOps globale ;
- modification large de `viewmodel.py` sans coordination ;
- donnees privees.

## Livrables

- registre CSV initial ;
- extraction ou import depuis AGOps quand possible ;
- creation d'actions depuis resolutions ;
- liens vers preuves existantes ;
- tests sur instance synthetique.

## Verification

Depuis `server/` :

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

Critere UX : une resolution ne doit plus rester un texte archive ; elle doit devenir une action suivie.

