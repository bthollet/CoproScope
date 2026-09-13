# Brief agent - Lot A ComptaScope CS approfondi

Mission : rendre ComptaScope comprehensible et actionnable pour un conseil syndical non expert.

Branche conseillee : `codex/lot-a-comptascope-cs`  
Port conseille : `8767`

## Objectif

Transformer la vue comptes en parcours de controle guide :

- comprendre les `P1`, `P2`, `OK` ;
- voir pourquoi une facture n'est pas rapprochee ;
- copier une question claire au syndic ;
- produire un mini-rapport utilisable avant AG.

## Ownership

Modifiable :

- templates et helpers de la vue comptes ;
- tests UI/compta dedies ;
- documentation ComptaScope.

A eviter sans coordination :

- `server/src/coproscope/cli.py` ;
- schemas globaux ;
- modules PrivacyOps/DocOps ;
- donnees privees ou chemins prives.

## Livrables

- regroupement par fournisseur, anomalie et priorite ;
- detail facture : piece, ecriture candidate, motif, confiance, prochaine action ;
- questions syndic copiables ;
- export Markdown du mini-rapport comptes ;
- tests sur instance synthetique ou demo fictive.

## Verification

Depuis `server/` :

```powershell
.\.venv\Scripts\python.exe -m unittest tests.test_ui_demo -v
.\.venv\Scripts\python.exe -m unittest tests.test_comptascope -v
```

Checks UI : `/comptes` et, si ajoute, toute route comptes dediee.

