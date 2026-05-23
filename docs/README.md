# Documentation CoproScope

Cette documentation doit servir l'UX avant l'outillage. Un coproprietaire novice n'a pas a lancer de commandes pour comprendre la valeur du produit. Les commandes existent, mais elles appartiennent au public averti: contributeurs, integrateurs, auditeurs techniques, demo runners.

## Publics

| Public | Ce que la doc doit lui donner |
|---|---|
| Coproprietaire novice | Une comprehension simple de ce qui se passe, de la preuve disponible et de l'action possible. |
| Institution ou acteur d'accompagnement | Une lecture claire de l'interet collectif, des garde-fous et des limites. |
| Conseil syndical | Un support pour relancer, controler, expliquer et transmettre sans tout porter seul. |
| Public averti | Commandes, tests, architecture et politique de publication. |

## Parcours De Lecture

### Pour Comprendre L'Usage

| Lire | Pourquoi |
|---|---|
| [README racine](../README.md) | Promesse, publics, UX cible et maturite reelle. |
| [Etude utilisateurs](./etude_utilisateurs.md) | Source des besoins: preuve, action, memoire, diffusion prudente. |
| [Concept et philosophie](./concept_et_philosophie.md) | Ce que CoproScope est, n'est pas, et pourquoi le local-first compte. |
| [Etat du developpement](./etat_du_developpement.md) | Ce qui est livre, en cours, cible ou pas prioritaire. |

### Pour Concevoir L'Experience

| Lire | Pourquoi |
|---|---|
| [UX novice P0](./ux_novice_p0.md) | Contrat de langage pour publics non experts. |
| [Registre langage UI](./registre_langage_ui.md) | Vocabulaire stable et formulations prudentes. |
| [Accessibilite et langage](./accessibilite_registre_langage.md) | Lisibilite, aide contextuelle, test novice. |
| [Fonctions cibles](./fonctions_cibles.md) | Blocs produit et maturite de chaque fonction. |
| [Suggestions d'amelioration](./suggestions_amelioration.md) | Pistes d'amelioration issues des cycles precedents. |

### Pour Comprendre La Preuve Et La Confidentialite

| Lire | Pourquoi |
|---|---|
| [Architecture et flux](./architecture_et_flux.md) | Separation depot public, instances privees, artefacts locaux. |
| [Documentation noyau vs instance](./documentation_noyau_vs_instance.md) | Frontiere entre produit genericisable et donnees sensibles. |
| [Confidentialite et biffage](./confidentialite_et_biffage.md) | Diffusion prudente, biffage, colleges d'acces. |
| [Politique de partage GitHub](./github_sharing.md) | Ce qui peut etre publie et ce qui doit rester local. |
| [Exports passation derives](./exports_passation_derives.md) | Pourquoi un export est un derive, pas une source de verite. |

### Pour Explorer Les Parcours Produit

| Parcours | Lire |
|---|---|
| Documents utiles et pieces manquantes | [DocOps actionnable](./docops_actionnable.md), [UX ajout document](./ux_workflow_ajout_document.md) |
| Demandes et relances | [UI demandes coproprietaires](./ui_demandes_coproprietaires.md) |
| Comptes et questions au syndic | [ComptaScope](./comptascope.md), [FactureOps](./factureops.md) |
| AG, decisions, contentieux prudent | [UI AG contentieux passation](./ui_ag_contentieux_passation.md) |
| Pilotage accessible | [UI pilotage indicateurs](./ui_pilotage_indicateurs.md) |
| Memoire, passation, anti-confiscation | [Resilience anti-accaparement](./resilience_anti_accaparement.md), [Archive reconstruction coproprietaire](./archive_reconstruction_coproprietaire.md) |

## Public Averti

Cette section est volontairement separee. Elle concerne les personnes qui installent, testent, integrent ou publient CoproScope.

| Besoin | Lire |
|---|---|
| Installer et lancer les tests | [server/README](../server/README.md) |
| Comprendre le contrat technique | [Implementation plan](./implementation_plan.md) |
| Comprendre le vault local | [Transition vault collaboratif](./transition_vault_collaboratif.md), [Format vault](./vault_format.md), [Signatures et historique](./signatures_historique.md) |
| Comprendre les evenements | [Objets metier et evenements V1](./objets_metier_evenements_v1.md) |
| Travailler avec des agents | [Equipe doc agents](./equipe_doc_agents.md), [Orchestration multi-agents](./orchestration_agents.md), [Lots paralleles approfondis](./lots_paralleles.md) |

## Atelier, Journal, Archive

Le workspace local peut contenir des captures, journaux live, commandes de cycle et notes de coordination. Ils sont utiles pour piloter le travail, mais ils ne doivent pas devenir le parcours principal d'un lecteur.

- **Guide**: ce qu'un lecteur doit comprendre ou faire.
- **Reference**: contrat stable, architecture, module, politique.
- **Journal**: trace datee d'un cycle, utile mais non obligatoire.
- **Archive**: source historique ou decision remplacee.

Quand une note de journal devient durable, elle doit etre transformee en guide ou en reference courte.

## Ligne Editoriale

Une bonne page CoproScope doit:

- partir d'une situation vecue, pas d'un module;
- montrer la preuve, l'action et la limite;
- dire clairement si le sujet est livre, en cours ou cible;
- parler d'abord a un coproprietaire novice;
- permettre a une institution de comprendre l'interet collectif;
- reserver les details techniques a une section public averti;
- rappeler la frontiere donnees fictives / donnees privees quand le risque existe.

La doc doit donner confiance sans vendre une magie qui n'existe pas.
