# Strategie CoproScope gestion copro

## Cap produit

CoproScope passe d'un lecteur critique de documents vers un cockpit local-first pour conseil syndical. L'audit reste present, mais comme couche de controle transverse: le produit principal devient la gestion operable de la copropriete et du suivi syndic.

## Couches fonctionnelles

| Couche | Role | Sorties |
|---|---|---|
| DocOps | Inventaire, hash, extraction, preuve documentaire | registre documents, textes, completude |
| SyndicOps | Demandes, relances, reponses, delais | registre demandes, preuves, relances |
| ComptaScope | Factures, ecritures candidates, controles | factures, grand livre candidat, anomalies |
| AGOps | Convocations, resolutions, suites | registre AG, points d'attention |
| WorksOps | Devis, travaux, receptions, garanties | suivi operations, ecarts, preuves |
| Audit360 | Controles transverses et diligences | constats, risques, actions |
| GristOps | Tableaux collaboratifs locaux | tables exportees ou synchronisees |
| EvidenceOps | Rapports reproductibles | pages SQL/Markdown |

## Principe de conception

Chaque ligne structuree doit rester reliee a une source: fichier, hash, page, ligne, registre ou decision. Les aides IA peuvent proposer, mais les controles deterministes et la trace documentaire gardent la priorite.

## Workflows cibles

1. Ingestion: inventaire, hash, extraction texte.
2. Qualification: type documentaire, fournisseur, exercice, sensibilite.
3. Exploitation: factures, contrats, demandes syndic, AG, travaux.
4. Controle: anomalies, preuves manquantes, rapprochements.
5. Pilotage: Grist local pour agir, Evidence pour expliquer.
6. Publication: uniquement code, docs, schemas, tests et exemples synthetiques.

## Interfaces a construire

- CLI stable pour automatiser les workflows.
- Exports CSV/DuckDB pour analyses locales.
- Tables Grist pour pilotage par conseil syndical.
- Rapports Evidence pour restitution.
- Plus tard: interface web locale, seulement lorsque les objets metier sont stabilises.
