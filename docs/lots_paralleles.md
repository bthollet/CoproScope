# Lots paralleles approfondis

Ce document transforme la feuille de route en lots suffisamment ambitieux pour lancer plusieurs conversations ou agents independants. Chaque lot doit pouvoir avancer sans attendre les autres, a condition que le Lot 0 soit stabilise.

## Lot 0 - Base commune Sprint 2

Objectif : figer la base partagee avant parallelisation forte.

Livrables :

- vue Actions locale ;
- filtres par perimetre ;
- compteur total/aperçu coherent ;
- exports CSV et Markdown ;
- documentation multi-agents ;
- tests serveur OK.

Critere de fin : `/actions`, `/exports/actions.csv`, `/exports/actions.md` repondent, la suite serveur passe, et le registre de suivi signale que la base est prete.

## Lots prioritaires

| Lot | Conversation | Branche conseillee | Port | Ownership |
|---|---|---|---:|---|
| A | ComptaScope CS approfondi | `codex/lot-a-comptascope-cs` | 8767 | Vue comptes, docs ComptaScope, tests UI/compta. |
| B | SyndicOps demandes et relances | `codex/lot-b-syndicops` | 8770 | Nouveau module demandes, registres, tests dedies. |
| C | DocOps actionnable | `codex/lot-c-docops-actionnable` | 8771 | DocOps, vue documents, tests documentaires. |
| D | PrivacyOps revue humaine | `codex/lot-d-privacy-review` | 8768 | PrivacyOps, vue confidentialite, tests privacy. |
| E | Decision -> action -> preuve | `codex/lot-e-decisions-preuves` | 8772 | Nouveau registre/module, tests, vue dediee. |
| F | WorksOps travaux | `codex/lot-f-worksops` | 8773 | Nouveau module travaux, tests, vue dediee. |
| G | IncidentOps signalements | `codex/lot-g-incidentops` | 8774 | Nouveau module incidents, tests, vue dediee. |
| H | CommsOps et passation | `codex/lot-h-comms-passation` | 8775 | Exports, templates rapports, controles diffusion. |

## Briefs de mission

Les briefs prets a copier-coller sont dans [`agent_briefs/`](./agent_briefs/).

Chaque brief contient :

- l'objectif produit ;
- le perimetre modifiable ;
- les fichiers a eviter ;
- les donnees autorisees ;
- les criteres de fin ;
- les tests minimaux ;
- les questions a trancher en fin de lot.

## Regles d'integration

- Ne pas lancer deux lots qui possedent le meme fichier de convergence.
- `viewmodel.py` et `cli.py` restent sous coordination : un agent les modifie seulement si son brief l'indique.
- Les nouveaux modules peuvent ajouter leurs propres tests et registres sans attendre l'interface finale.
- Chaque lot livre une note finale exploitable par le coordinateur.
- Le coordinateur integre une branche a la fois et relance les tests complets.

