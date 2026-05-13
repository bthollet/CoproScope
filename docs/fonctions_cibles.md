# Fonctions cibles

## Vue d'ensemble

| Bloc | But | Entrees typiques | Sorties attendues | Statut |
|---|---|---|---|---|
| DocOps | Reconstituer un registre documentaire fiable | bruts Drive, extranet, dossiers locaux | inventaire, hash, doublons, texte, classement, completude | en cours, deja exploitable |
| SyndicOps | Structurer la relation documentaire avec le syndic | demandes, reponses, mails, pieces attendues | registre des demandes, relances, constats, diligences | en cours, socle present |
| AGOps | Standardiser la preparation des AG | convocations, PV, annexes, resolutions | registre AG, rapport de preparation, points d'attention | en cours, premiere version presente |
| ContractOps | Mieux suivre contrats et obligations | contrats, avenants, attestations | registre contrats, alertes, clauses clefs | cible ulterieure |
| WorksOps | Suivre devis, travaux et entreprises | devis, factures, assurance, diligence publique | chronologies, comparatifs, alertes, constats | cible ulterieure |
| CommsOps | Organiser les communications diffusables | notes, syntheses, courriels, comptes rendus | sorties partageables, suivis de diffusion | cible ulterieure |

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

Signes de reussite:

- on sait ce qu'on a ;
- on sait ce qui manque ;
- on peut citer une piece par identifiant ;
- on ne travaille plus a l'aveugle.

## SyndicOps

SyndicOps transforme les demandes eparses en suivi clair.

Fonctions recherchees:

- registre unique des demandes ;
- piece attendue rattachee a chaque demande ;
- suivi des reponses et des relances ;
- rattachement demande -> document -> constat -> diligence ;
- indicateurs de couverture et de reponse.

Signes de reussite:

- les relances ne repartent pas de zero ;
- les demandes ont une preuve d'origine ;
- les reponses partielles sont visibles ;
- les trous documentaires deviennent actionnables.

## AGOps

AGOps vise a rendre la preparation d'AG lisible et reproductible.

Fonctions recherchees:

- reperage des convocations, PV et annexes ;
- comptage indicatif des resolutions ;
- signalement d'annexes manquantes ;
- rappel des majorites detectees ;
- rapport d'aide a la preparation AG.

Signes de reussite:

- les pieces utiles a l'AG sont visibles en amont ;
- les annexes manquantes remontent avant la reunion ;
- le conseil syndical dispose d'une base de lecture partageable.

## Regle de priorisation

L'ordre de construction reste volontairement strict:

1. DocOps
2. SyndicOps
3. AGOps
4. puis seulement ContractOps, WorksOps et CommsOps

Cette discipline evite d'empiler des couches "intelligentes" sur un socle documentaire encore flou.

## Ce qui reste hors perimetre court terme

- application web ;
- orchestration cloud lourde ;
- moteur multi-entites complet ;
- experience "grand public" ;
- promesses d'automatisation sans trace ni verification.
