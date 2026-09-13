# Strategie CoproScope gestion copro

## Cap produit

CoproScope evolue vers un cockpit local-first pour conseil syndical. L'audit documentaire reste present, mais comme couche transverse : le produit principal devient l'aide au travail reel du CS.

Le cap tient en quatre mots :

**preuve, action, memoire, diffusion sure.**

## Couches fonctionnelles

| Couche | Role | Sorties |
|---|---|---|
| DocOps | Inventaire, hash, extraction, preuve documentaire | registre documents, textes, completude |
| PrivacyOps | Politique d'acces et risques de diffusion | screening confidentialite, colleges, transformations |
| BiffageOps | Versions biffees ou pseudonymisees | file de biffage, registre biffages, versions diffusables |
| SyndicOps | Demandes, relances, reponses, delais | registre demandes, preuves, relances |
| FactureOps | Extraction et qualification des factures | factures candidates, anomalies facture, intensite L0-L4 |
| ComptaScope | Reconstruction et rapprochement comptable | controles comptables, rapprochements, rapport |
| AGOps | Convocations, resolutions, suites | registre AG, points d'attention |
| WorksOps | Devis, travaux, receptions, garanties | suivi operations, ecarts, preuves |
| IncidentOps | Signalements, sinistres, interventions | tickets, statuts, photos, preuves de cloture |
| ContractOps | Contrats et obligations | registre contrats, alertes, clauses |
| Audit360 | Controles transverses et diligences | constats, risques, preuves attendues, actions |
| CommsOps | Communications diffusables | notes, syntheses, PDF, messages |
| GristOps | Tableaux collaboratifs locaux | tables exportees ou synchronisees |
| EvidenceOps | Rapports reproductibles | pages SQL/Markdown |

## Principe de conception

Chaque ligne structuree doit rester reliee a une source : fichier, hash, page, ligne, registre, decision ou biffage.

Les aides IA peuvent proposer, mais les controles deterministes, la trace documentaire et la validation humaine gardent la priorite.

## Workflows cibles

1. Ingestion : inventaire, hash, extraction texte.
2. Qualification : type documentaire, fournisseur, exercice, sensibilite.
3. Protection : college d'acces, biffage ou aggregation si necessaire.
4. Extraction metier : factures, contrats, demandes syndic, AG, travaux.
5. Controle : anomalies, rapprochements, preuves manquantes, risques.
6. Pilotage : vues locales pour agir.
7. Restitution : syntheses diffusables, biffees ou agregees.
8. Publication : uniquement code, docs, schemas, tests et exemples synthetiques.

## Interfaces a construire

- Cockpit conseil syndical.
- Vue confidentialite / diffusion.
- Controle des comptes guide.
- Registre decisions-actions-preuves.
- Dossier travaux.
- Dossier incidents/sinistres.
- Memoire et passation CS.
- Fabrique de syntheses diffusables.

## Decision strategique

CoproScope ne doit pas courir apres les extranets ou les neosyndics. Sa position la plus forte est differente :

> Un outil independant du syndic, local-first, probatoire, capable de relier documents, demandes, decisions, comptes et restitutions.

