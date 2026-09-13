# Brief agent - Lot D PrivacyOps revue humaine

Mission : transformer le screening confidentialite en file de decision humaine.

Branche conseillee : `codex/lot-d-privacy-review`  
Port conseille : `8768`

## Objectif

Permettre au CS de decider clairement :

- diffusable brut ;
- diffusable apres biffage ;
- diffusable apres aggregation ;
- bloque ;
- a arbitrer.

## Ownership

Modifiable :

- `privacyops.py` ;
- vue confidentialite ;
- tests privacy ;
- documentation confidentialite.

A eviter sans coordination :

- ComptaScope ;
- modules travaux/incidents ;
- publication de documents reels ou cartes de correspondance.

## Livrables

- statuts de revue humaine ;
- justification obligatoire pour diffusion large ;
- file de biffage plus lisible ;
- blocages explicites ;
- tests qui garantissent que bruts/restreints/tables de correspondance ne sont pas servis.

## Verification

Depuis `server/` :

```powershell
.\.venv\Scripts\python.exe -m unittest tests.test_privacy -v
.\.venv\Scripts\python.exe -m unittest tests.test_ui_demo -v
```

Critere de securite : aucune sortie diffusable ne doit contourner PrivacyOps/BiffageOps.

