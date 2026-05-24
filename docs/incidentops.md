# IncidentOps

IncidentOps structure les signalements et sinistres du quotidien sans ajouter de donnees reelles au depot. Le module travaille sur l'instance locale, derive des candidats depuis le registre documentaire et produit des sorties exploitables par le conseil syndical.

## Registre

Le registre par defaut est `registers/registre_incidents.csv`, sauf si l'instance expose un registre `incidents`.

Champs principaux :

- `date_signalement` ;
- `lieu` ;
- `description` ;
- `piece_ref`, `doc_ids`, `photo_or_piece` ;
- `syndic_or_provider` ;
- `status` ;
- `priority` ;
- `next_action` ;
- `action_due_date` ;
- `expected_closure_proof` ;
- `closure_proof_ref` ;
- `contract_or_insurance_ref`.

## Statuts

Statuts ouverts :

- `NOUVEAU` ;
- `A_QUALIFIER` ;
- `EN_COURS` ;
- `EN_RELANCE` ;
- `EN_ATTENTE_PREUVE` ;
- `A_CLOTURER`.

Statuts fermes :

- `CLOTURE` ;
- `SANS_SUITE`.

Un incident ouvert doit toujours porter une `next_action` et une `expected_closure_proof`. Le module les complete prudemment quand elles manquent.

## Sorties

`build_incident_register(instance, run)` produit :

- le registre incidents ;
- `outputs/reports/incidentops/incidents_ouverts.csv` ;
- `outputs/reports/incidentops/rapport_incidentops.md`.

L'export ouvert sert de liste de relance : statut, priorite, prochaine action et preuve attendue. La cloture n'est pas consideree probante sans `closure_proof_ref`.

## Confidentialite

IncidentOps ne fournit pas de donnees de demonstration reelles. Les tests utilisent l'instance synthetique et les traitements d'instance privee restent locaux. Toute diffusion externe doit passer par les garde-fous PrivacyOps/BiffageOps.
