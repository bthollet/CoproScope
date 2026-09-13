# Brief agent - Lot C DocOps actionnable

Mission : passer de l'inventaire documentaire a une vue de travail "ce qu'on a / ce qui manque / ce qui est a demander".

Branche conseillee : `codex/lot-c-docops-actionnable`  
Port conseille : `8771`

## Objectif

Rendre le registre documentaire utile a un CS :

- typologies documentaires lisibles ;
- pieces presentes ;
- pieces manquantes ;
- pieces obsoletes ;
- pieces a demander au syndic ;
- liens vers preuves.

## Ownership

Modifiable :

- modules DocOps/Docuscope concernes ;
- vue documents ;
- tests documentaires ;
- documentation DocOps si necessaire.

A eviter sans coordination :

- PrivacyOps ;
- ComptaScope ;
- `cli.py` sauf commande strictement necessaire.

## Livrables

- matrice lisible de completude documentaire ;
- liste actionnable des pieces a demander ;
- distinction absence / obsolescence / doute de classement ;
- export CSV ou Markdown de la liste de pieces ;
- tests sur instance synthetique.

## Verification

Depuis `server/` :

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

Critere UX : un membre de CS doit comprendre en moins de deux minutes quelles pieces demander.

