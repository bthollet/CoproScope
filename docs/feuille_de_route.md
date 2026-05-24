# Feuille de route produit

> Statut gouvernail: `SOURCE_HISTORIQUE`.
> La source de verite roadmap est `docs/roadmap_backlog_central.md`
> (`RM-2026-0003`, `RM-2026-0007`). Ne pas ajouter de priorite active ici.

Cette feuille de route part de l'etude utilisateurs et de l'etat reel du depot.

## Cap

Faire passer CoproScope de **moteur documentaire probatoire local-first** a **cockpit de travail pour conseil syndical**.

La priorite n'est pas d'ajouter un maximum de modules. La priorite est de rendre visibles, actionnables et transmissibles les objets deja structurants : documents, demandes, decisions, preuves, comptes, risques, biffages.

## P0 - Rendre le noyau utilisable par un conseil syndical

| Chantier | Pourquoi | Livrable attendu |
|---|---|---|
| Cockpit conseil syndical | Les modules existent mais restent disperses. | Vue priorisee : a traiter, pieces manquantes, demandes syndic, AG, comptes, confidentialite. |
| DocOps actionnable | Le besoin documentaire est tres fort. | Vue "ce qu'on a / ce qui manque / ce qui est obsolete / ce qui est a demander". |
| SyndicOps complet | Les demandes au syndic sont une douleur centrale. | Statuts, echeances, relances, pieces attendues, preuves de reponse. |
| ComptaScope lisible | La brique est forte mais experte. | Controle comptes guide : `OK`, `P2`, `P1`, questions au syndic, rapport AG. |
| Confidentialite visible | Les dernieres briques PrivacyOps/BiffageOps changent la promesse. | Vue screening, file de biffage, documents diffusables, restrictions. |

## P1 - Construire les chaines d'action manquantes

| Chantier | Pourquoi | Livrable attendu |
|---|---|---|
| Registre decision -> action -> preuve | Angle mort majeur du marche. | Chaque resolution AG devient une action suivie avec preuves et historique. |
| Passation conseil syndical | Besoin fort mais silencieux. | Dossier nouveau CS : sujets ouverts, risques, calendrier, acces, memoire. |
| WorksOps | Travaux et renovation concentrent couts, conflits et preuves. | Dossier travaux : devis, lots, assurances, reception, garanties. |
| IncidentOps minimal | Les incidents structurent le quotidien. | Signalement, photo, statut, localisation, lien contrat/syndic/prestataire. |
| CommsOps v1 | Le CS doit expliquer sans exposer. | Notes diffusables, syntheses AG, exports PDF sobres. |

## P2 - Consolider les publics avances

| Chantier | Pourquoi | Livrable attendu |
|---|---|---|
| GristOps / EvidenceOps | Tres utile pour CS experts et audits. | Templates locaux mieux guides, exemples synthetiques. |
| Audit360 enrichi | Promesse differenciante fait -> preuve -> risque -> action. | Repertoires de controles par parcours : comptes, AG, contrats, travaux. |
| Extracteurs factures | Fiabiliser les corpus fournisseurs. | Manifestes, tests, limites explicites, exemples synthetiques. |
| Policy-as-data | La confidentialite doit rester configurable. | Regles privacy partageables, documentees, testees. |

## P3 - Non prioritaire maintenant

| Sujet | Decision |
|---|---|
| SaaS multi-tenant | Reporter. Trop de risques donnees et d'effort pour le cap actuel. |
| Application mobile native | Reporter. Utile plus tard, pas avant stabilisation des objets metier. |
| Reseau social de coproprietaires | Ne pas prioriser. Le besoin fort est action/preuve, pas conversation generale. |
| Vote electronique complet | Ne pas prioriser. Le marche est deja outille ; CoproScope doit suivre les suites d'AG. |
| Chatbot IA autonome | Ne pas livrer sans preuves citees, incertitudes et validation humaine. |
| Jumeau numerique 3D | Hors cap court terme. |

## Sequencement conseille

1. Stabiliser les registres et sorties existants.
2. Construire un prototype de cockpit sur donnees synthetiques.
3. Ajouter la vue confidentialite/biffage.
4. Ajouter le registre decisions-actions-preuves.
5. Relier ComptaScope au rapport AG.
6. Ouvrir WorksOps et IncidentOps en mode minimal.
7. Produire les premiers exports CommsOps.
8. Seulement ensuite, envisager une interface locale plus complete.

## Mesures de succes

| Objectif | Mesure |
|---|---|
| Le CS sait quoi traiter | Nombre de sujets priorises avec prochaine action claire. |
| Les demandes au syndic ne se perdent pas | Taux de demandes avec statut, echeance et preuve. |
| Le controle comptes devient lisible | Nombre de `P1` traites et questions generees avant AG. |
| Les decisions AG vivent apres le PV | Pourcentage de resolutions avec action et statut. |
| La diffusion est plus sure | Nombre de documents classes, biffes ou bloques avant partage. |
| La memoire se transmet | Pack passation genere et sujets ouverts identifies. |
