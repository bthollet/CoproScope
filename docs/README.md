# Documentation CoproScope

Cette documentation est ecrite pour etre lisible par trois publics :

- les membres de conseil syndical qui veulent comprendre la promesse ;
- les relecteurs UX/produit qui veulent challenger les priorites ;
- les contributeurs techniques qui veulent savoir ou agir sans exposer de donnees.

## Lire vite

| Temps | Lire | Pourquoi |
|---|---|---|
| 5 min | [Etude utilisateurs](./etude_utilisateurs.md) + [Etat du developpement](./etat_du_developpement.md) | Comprendre le besoin, ce qui existe et ce qui manque. |
| 15 min | Ajouter [Concept et philosophie](./concept_et_philosophie.md), [Fonctions cibles](./fonctions_cibles.md), [Feuille de route](./feuille_de_route.md) | Comprendre le produit et les priorites. |
| 30 min | Ajouter [Architecture et flux](./architecture_et_flux.md), [Confidentialite et biffage](./confidentialite_et_biffage.md), [Audit360](./audit360.md) | Comprendre les choix structurants. |
| Contribution | Ajouter [Plan d'implementation](./implementation_plan.md), [Orchestration multi-agents](./orchestration_agents.md), [Politique de partage GitHub](./github_sharing.md), [Outillage](./outillage_open_source.md) | Contribuer seul ou a plusieurs sans casser les garde-fous. |

## Carte de la doc

| Document | Role |
|---|---|
| [Etude utilisateurs](./etude_utilisateurs.md) | Synthese accessible de l'enquete UX/SHS et de ses conclusions produit. |
| [Concept et philosophie](./concept_et_philosophie.md) | Promesse, principes et limites de CoproScope. |
| [Fonctions cibles](./fonctions_cibles.md) | Tous les blocs fonctionnels, avec statut clair. |
| [Feuille de route](./feuille_de_route.md) | Priorites P0/P1/P2/P3 en francais, issues de l'etude. |
| [Etat du developpement](./etat_du_developpement.md) | Ce qui est livre, en cours, prevu, pas prioritaire. |
| [Architecture et flux](./architecture_et_flux.md) | Separation depot public / instances privees / artefacts locaux. |
| [Documentation noyau vs instance](./documentation_noyau_vs_instance.md) | Frontiere entre docs produit genericisables et docs d'instance sensibles. |
| [Transition vault collaboratif](./transition_vault_collaboratif.md) | Strategie de passage vers un vault local signe et synchronisable. |
| [Migration Drive vers local](./migration_drive_vers_local.md) | Runbook de bascule locale, nettoyage et garde-fous. |
| [Format vault](./vault_format.md) | Format V1 du dossier sync chiffre, blobs et evenements. |
| [Signatures et historique](./signatures_historique.md) | Modele append-only, signatures et reconstruction locale. |
| [Objets metier et evenements V1](./objets_metier_evenements_v1.md) | Contrat des objets noyau et evenements collaboratifs. |
| [Plugins officiels](./plugins_officiels.md) | Strategie de plugins signes, compatibles et revocables. |
| [Batchs transition locale](./batchs_transition_locale.md) | Commandes Windows relancables depuis une autre conversation. |
| [Reprise agents paralleles vault](./reprise_agents_paralleles_vault.md) | Lots paralleles sans collision et prompts de lancement. |
| [Confidentialite et biffage](./confidentialite_et_biffage.md) | PrivacyOps, BiffageOps, colleges d'acces, versions diffusables. |
| [Audit360](./audit360.md) | Couche transverse faits -> preuves -> risques -> actions. |
| [FactureOps](./factureops.md) | Extraction et anomalies facture. |
| [ComptaScope](./comptascope.md) | Rapprochements comptables candidats et rapport explicatif. |
| [DocOps actionnable](./docops_actionnable.md) | Completude documentaire sous forme pieces presentes, manquantes, obsoletes et a demander. |
| [IncidentOps](./incidentops.md) | Registre incidents, statuts, prochaines actions et preuves de cloture. |
| [Strategie gestion copro](./strategie_coproscope_gestion_copro.md) | Passage de l'audit documentaire au cockpit de travail CS. |
| [Plan d'implementation](./implementation_plan.md) | Contrat technique v1 et non-objectifs. |
| [Orchestration multi-agents](./orchestration_agents.md) | Lancer plusieurs agents en parallele avec worktrees, ownership et garde-fous. |
| [Lots paralleles approfondis](./lots_paralleles.md) | Briefs de lots A-H pour conversations independantes approfondies. |
| [Registre de suivi livraison interface](./registre_suivi_livraison_interface.md) | Suivi operationnel du cockpit local et de la copro demo fictive. |
| [Politique de partage GitHub](./github_sharing.md) | Ce qui peut ou ne peut pas remonter dans le depot public. |
| [Outillage open source](./outillage_open_source.md) | Outils locaux installes, retenus ou reportes. |
| [Registre d'avancement](./registre_avancement.md) | Historique des etapes genericisables. |

## Images et concepts UX

Les images dans [`assets/etude-utilisateurs/`](./assets/etude-utilisateurs/) illustrent les directions d'interface issues de l'etude :

- cockpit conseil syndical ;
- registre decisions/actions/preuves ;
- controle des comptes guide ;
- memoire de copropriete et passation CS.

Elles servent a discuter le produit cible. L'interface locale v0 existe, mais ces images restent des concepts cibles.

## Ligne editoriale

La documentation doit rester :

- franche sur la maturite : livre, en cours, prevu, pas encore ;
- orientee conseil syndical, pas seulement technique ;
- prudente sur les donnees sensibles ;
- francaise dans ses termes quand cela aide la comprehension ;
- concrete : chaque promesse doit renvoyer a un module, un livrable ou une limite.
