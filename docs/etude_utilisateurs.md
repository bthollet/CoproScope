# Etude utilisateurs

Date de reference : 2026-05-20

Cette page rend accessible l'etude UX/SHS menee avant l'audit de CoproScope. Le principe etait simple : comprendre les besoins des conseils syndicaux sans regarder d'abord le produit, pour eviter de justifier l'existant apres coup.

## Conclusion courte

Les conseils syndicaux n'ont pas seulement besoin d'un endroit ou stocker les documents. Ils ont besoin d'un outil qui aide a relier :

- une piece ;
- une demande au syndic ;
- une decision d'assemblee generale ;
- une depense ;
- une preuve ;
- une action a suivre ;
- une restitution diffusable.

Le besoin profond est donc : **preuve + action + memoire**, avec des garde-fous pour ne pas surcharger des benevoles.

## Ce que l'etude change pour CoproScope

Avant l'etude, CoproScope pouvait etre lu comme un tres bon moteur documentaire local-first.

Apres l'etude, la direction est plus nette : CoproScope doit devenir un **compagnon de travail du conseil syndical**, capable de rendre visibles les sujets qui demandent attention, sans faire croire que l'outil remplace le syndic, le droit ou la validation humaine.

## Besoins prioritaires

| Besoin | Intensite | Implication produit |
|---|---:|---|
| Documents utiles, complets, retrouvables | Tres forte | DocOps doit produire une vue "ce qu'on a / ce qui manque / ce qui est obsolete". |
| Suivi des demandes au syndic | Tres forte | SyndicOps doit devenir un vrai workflow avec statut, echeance, relance et preuve. |
| Controle des comptes | Tres forte | ComptaScope doit rester probatoire, mais devenir plus pedagogique. |
| Suivi post-AG | Forte | Chaque resolution doit devenir une action suivie. |
| Travaux, devis, reception | Forte | WorksOps est prioritaire. |
| Incidents et sinistres | Forte | Un IncidentOps minimal est pertinent. |
| Passation du conseil syndical | Forte, peu exprimee | La memoire de copropriete doit devenir un livrable produit. |
| Role et limites du CS | Forte | Ajouter aide contextuelle, formulations prudentes et garde-fous. |
| Restitutions diffusables | Forte | CommsOps doit aider a expliquer sans exposer. |

## Typologies d'usage

Une meme copropriete peut passer d'un type a l'autre selon le moment.

| Type | Ce qu'il fait | Besoin UX |
|---|---|---|
| CS vigie | Surveille comptes, pieces, contrats, anomalies. | Vues de controle, alertes, preuves. |
| CS pompier | Reagit aux urgences, sinistres, conflits. | Incidents, statuts, escalade, historique. |
| CS batisseur | Porte travaux et renovation. | Devis, calendrier, arguments, suivi AG. |
| CS expert | Travaille deja avec tableurs et preuves. | Exports, schemas, donnees, controles avances. |
| CS captif | Depend fortement du syndic. | Demandes formelles, droits, pieces attendues. |
| CS fatigue | Trop peu de benevoles, memoire fragile. | Priorisation, passation, simplification. |
| Copro sans relais | Peu ou pas de conseil actif. | Diagnostic minimal, mobilisation, mode simple. |
| Copro de crise | Impayes, bati degrade, contentieux. | Journal de crise, preuves, acteurs, seuils. |

## Parcours critiques

1. Controler les comptes avant AG.
2. Transformer un PV d'AG en plan d'action.
3. Gerer un sinistre ou un incident.
4. Preparer un gros chantier.
5. Transmettre la memoire a un nouveau conseil syndical.

Ces parcours justifient les futures interfaces : cockpit CS, controle comptes guide, registre decisions-actions-preuves, dossier travaux, memoire de copropriete.

## Benchmark : ce que font les autres outils

Le marche est dense, mais fragmente.

| Famille | Ce qu'elle couvre bien | Angle mort |
|---|---|---|
| Extranets de syndics | Documents, compte client, quelques demandes. | Peu de controle CS, peu de chainage des preuves. |
| Neosyndics | Transparence, relation, plateforme. | Reste souvent centre syndic. |
| Syndic benevole | Comptabilite, AG, appels de fonds. | Charge forte sur les benevoles. |
| Outils incidents | Signalements, photos, statuts. | Peu de lien avec contrats, budgets, AG. |
| Outils generalistes | Flexibilite, collaboration. | Pas de modele copro, pas de droits ni preuves metier. |

L'angle mort le plus clair : tres peu d'outils montrent une chaine complete **decision -> action -> document -> depense -> preuve -> restitution**.

## Concepts d'interface

### Cockpit conseil syndical

![Cockpit conseil syndical](./assets/etude-utilisateurs/cockpit-conseil-syndical.png)

### Registre decisions, actions, preuves

![Registre decisions actions preuves](./assets/etude-utilisateurs/registre-decisions-actions-preuves.png)

### Controle des comptes guide

![Controle des comptes guide](./assets/etude-utilisateurs/controle-comptes-guide.png)

### Memoire de copropriete

![Memoire de copropriete](./assets/etude-utilisateurs/memoire-copropriete.png)

## Ce que CoproScope couvre deja bien

- Reprendre la main sur le fonds documentaire.
- Tracer les sources, hash, registres et rapports.
- Controler les factures et comptes de maniere candidate, explicable et non definitive.
- Proteger la frontiere public/prive.
- Construire des exports locaux et des rapports.

## Ce que CoproScope doit encore construire

- Une interface lisible pour les non-techniciens.
- Le registre decision -> action -> preuve.
- WorksOps pour travaux, devis, reception et garanties.
- IncidentOps pour sinistres et signalements.
- ContractOps pour contrats et obligations.
- CommsOps pour produire des syntheses diffusables.
- Une vraie experience de passation du conseil syndical.

## Principe produit retenu

CoproScope doit aider un conseil syndical a agir mieux, pas a tout faire.

Un bon ecran CoproScope doit donc repondre a quatre questions :

1. Qu'est-ce qui demande attention ?
2. Quelle preuve avons-nous ?
3. Quelle action est legitime maintenant ?
4. Que peut-on partager, avec qui, et sous quelle forme ?

