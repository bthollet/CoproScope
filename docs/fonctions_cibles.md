# Fonctions cibles

## Vue d'ensemble

| Bloc | But | Sorties attendues | Statut |
|---|---|---|---|
| DocOps | Reconstituer un registre documentaire fiable | inventaire, hash, doublons, texte, classement, completude | en cours, deja exploitable |
| SyndicOps | Structurer la relation documentaire avec le syndic | registre des demandes, pieces attendues, relances, constats | en cours, socle present |
| AGOps | Standardiser la preparation des AG | registre AG, rapport de preparation, points d'attention | en cours, premiere version presente |
| ContractOps | Mieux suivre contrats et obligations | registre des contrats, alertes, clauses clefs | cible ulterieure |
| WorksOps | Suivre devis, travaux, entreprises, diligences | chronologies, comparatifs, alertes, constats | cible ulterieure |
| CommsOps | Organiser les communications diffusables | notes, syntheses, suivi de diffusion | cible ulterieure |

## DocOps

DocOps est le premier socle, parce qu'il conditionne tout le reste.

Fonctions recherchees:

- inventaire des pieces brutes ;
- empreintes SHA-256 ;
- detection de doublons ;
- extraction de texte natif ;
- signalement OCR ;
- classement assiste ;
- rapport de completude documentaire ;
- index probatoire.

## SyndicOps

SyndicOps transforme les demandes eparses en suivi clair.

Fonctions recherchees:

- registre unique des demandes ;
- piece attendue rattachee a chaque demande ;
- suivi des reponses et des relances ;
- rattachement demande -> document -> constat -> diligence ;
- indicateurs de couverture et de reponse.

## AGOps

AGOps vise a rendre la preparation d'AG lisible et reproductible.

Fonctions recherchees:

- reperage des convocations, PV et annexes ;
- comptage indicatif des resolutions ;
- signalement d'annexes manquantes ;
- rappel des majorites detectees ;
- rapport d'aide a la preparation AG.

## Regle de priorisation

L'ordre de construction reste volontairement strict:

1. DocOps
2. SyndicOps
3. AGOps
4. puis seulement ContractOps, WorksOps et CommsOps

Cette discipline evite d'empiler des couches "intelligentes" sur un socle documentaire encore flou.
