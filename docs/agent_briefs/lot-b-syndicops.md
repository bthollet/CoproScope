# Brief agent - Lot B SyndicOps demandes et relances

Mission : transformer questions, pieces manquantes et relances en workflow de demandes au syndic.

Branche conseillee : `codex/lot-b-syndicops`  
Port conseille : `8770`

## Objectif

Creer un registre de demandes exploitable par le conseil syndical :

- demande ;
- origine ;
- piece attendue ;
- echeance ;
- statut ;
- relance ;
- preuve de reponse.

## Ownership

Modifiable :

- nouveau module SyndicOps ou extension dediee ;
- registre et tests demandes ;
- templates de demande/export message.

A eviter sans coordination :

- `viewmodel.py` sauf point d'integration convenu ;
- `cli.py` sauf ajout minimal de commande convenu ;
- vue comptes hors liens vers demandes.

## Livrables

- registre CSV stable des demandes ;
- generation depuis questions ComptaScope ou constats DocOps ;
- statuts `brouillon`, `envoyee`, `relancee`, `repondue`, `close` ;
- export Markdown/mail pret a envoyer ;
- tests sur instance synthetique.

## Verification

Depuis `server/` :

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

Critere UX : aucune demande ne doit etre une simple note informelle ; elle doit avoir une prochaine action et un statut.

