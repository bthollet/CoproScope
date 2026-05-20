# Fonctions cibles

## Vue d'ensemble

| Bloc | But | Entrees typiques | Sorties attendues | Statut |
|---|---|---|---|---|
| DocOps | Reconstituer un registre documentaire fiable | bruts Drive, extranet, dossiers locaux | inventaire, hash, doublons, texte, classement, completude | en cours, deja exploitable |
| SyndicOps | Structurer la relation documentaire avec le syndic | demandes, reponses, mails, pieces attendues | registre des demandes, relances, constats, diligences | en cours, socle present |
| FactureOps | Extraire et qualifier les factures | pieces detectees par DocOps, Factur-X/XML/CSV, OCR local | factures candidates, anomalies facture, niveau d'intensite L0-L4 | amorce v1 |
| ComptaScope | Reconstituer et controler les flux comptables | factures candidates FactureOps, annexes, etats de depenses, contrats | ecritures candidates, controles comptables, rapprochements, exports DuckDB/Grist/Evidence | amorce v1 |
| AGOps | Standardiser la preparation des AG | convocations, PV, annexes, resolutions | registre AG, rapport de preparation, points d'attention | en cours, premiere version presente |
| Audit360 | Transformer les signaux metier en controles relisibles | pieces, demandes, AG, sujets travaux ou contrats | constats normalises, repertoire de controles, syntheses, diligences | en cours d'extraction publique |
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

## FactureOps

FactureOps est la couche amont specialisee dans les factures. Elle ne fait pas de comptabilite: elle transforme des pieces documentaires en factures candidates exploitables.

Fonctions recherchees:

- detecter les factures et avoirs ;
- extraire fournisseur, numero, date, HT, TVA, TTC ;
- proposer un compte et une famille de charge ;
- signaler les anomalies facture ;
- conserver la source, le hash, la methode d'extraction et le niveau d'intensite ;
- produire `invoice_evidence` et `invoice_anomalies`.

Signes de reussite:

- les anomalies de piece ne sont plus confondues avec les controles comptables ;
- chaque facture candidate renvoie a une preuve documentaire ;
- l'intensite des outils est lisible de `L0_STRUCTURED_SOURCE` a `L4_AI_OR_ONLINE_REVIEW`.

## ComptaScope

ComptaScope transforme les factures candidates FactureOps et les sources comptables en objets auditables sans pretendre tenir la comptabilite officielle.

Fonctions recherchees:

- produire une ecriture candidate ;
- rapprocher factures et etat des depenses ;
- signaler les controles comptables et les rapprochements a confirmer ;
- exporter vers CSV, DuckDB, Grist et Evidence.

Signes de reussite:

- chaque ligne comptable candidate renvoie a une facture candidate FactureOps ;
- les hypotheses restent marquees comme telles ;
- les ecarts et manques deviennent visibles avant discussion avec le syndic.

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

## Audit360

Audit360 sert a rendre les analyses comparables, relisibles et actionnables.

Fonctions recherchees:

- normaliser des constats issus de sources heterogenes ;
- consolider ces constats dans un repertoire de controles ;
- produire une synthese par point de controle ;
- expliciter les preuves attendues ;
- rattacher une action, une relance ou une diligence a chaque point utile.

Signes de reussite:

- les analyses ne restent pas dispersees dans des notes ;
- les points de controle reviennent d'un dossier a l'autre avec une forme stable ;
- un relecteur comprend vite le lien entre fait, risque, preuve et action ;
- les sorties sont assez propres pour etre discutees ou diffusees.

## Regle de priorisation

L'ordre de construction reste volontairement strict:

1. DocOps
2. SyndicOps
3. FactureOps
4. ComptaScope
5. AGOps
6. puis seulement ContractOps, WorksOps et CommsOps

Cette discipline evite d'empiler des couches "intelligentes" sur un socle documentaire encore flou.

## Ce qui reste hors perimetre court terme

- application web ;
- orchestration cloud lourde ;
- moteur multi-entites complet ;
- experience "grand public" ;
- promesses d'automatisation sans trace ni verification.
