# Brief agent - Lot H CommsOps et passation

Mission : produire des syntheses diffusables et un pack de passation conseil syndical.

Branche conseillee : `codex/lot-h-comms-passation`  
Port conseille : `8775`

## Objectif

Composer des sorties utiles :

- synthese CS ;
- points ouverts ;
- risques ;
- demandes syndic ;
- decisions en cours ;
- documents a transmettre ;
- pack nouveau membre du conseil syndical.

## Ownership

Modifiable :

- templates d'exports ;
- module CommsOps ou sorties dediees ;
- tests d'exports ;
- docs confidentialite/passation.

A eviter sans coordination :

- publication de donnees reelles ;
- contournement PrivacyOps ;
- refonte globale du cockpit.

## Livrables

- export Markdown sobre ;
- export PDF si la pile locale le permet sans fragiliser ;
- pack passation ;
- controle de diffusion prealable ;
- tests sur instance synthetique ou demo fictive.

## Verification

Depuis `server/` :

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

Critere de securite : aucune synthese diffusable ne doit inclure une piece brute sensible sans controle.

