# Documentation CoproScope

Cette documentation est ecrite pour etre lisible par trois publics :

- les membres de conseil syndical qui veulent comprendre la promesse ;
- les relecteurs UX/produit qui veulent challenger les priorites ;
- les contributeurs techniques qui veulent savoir ou agir sans exposer de donnees.

## Lire vite

| Temps | Lire | Pourquoi |
|---|---|---|
| 5 min | [Gouvernail roadmap](./roadmap_backlog_central.md) + [Etude utilisateurs](./etude_utilisateurs.md) + [Etat du developpement](./etat_du_developpement.md) | Comprendre la source de verite, le besoin, ce qui existe et ce qui manque. |
| 15 min | Ajouter [Concept et philosophie](./concept_et_philosophie.md), [Fonctions cibles](./fonctions_cibles.md), [Feuille de route](./feuille_de_route.md), [Plan directeur local + vault](./plan_directeur_coproscope_local_vault.md) | Comprendre le produit; les priorites actives restent dans le gouvernail. |
| 30 min | Ajouter [Architecture et flux](./architecture_et_flux.md), [Confidentialite et biffage](./confidentialite_et_biffage.md), [Audit360](./audit360.md) | Comprendre les choix structurants. |
| Contribution | Ajouter [Plan d'implementation](./implementation_plan.md), [Cycles refonte UX](./refonte_ux_cycles_image_dev_test.md), [Orchestration multi-agents](./orchestration_agents.md), [Politique de partage GitHub](./github_sharing.md), [Outillage](./outillage_open_source.md) | Contribuer seul ou a plusieurs sans casser les garde-fous. |

## Carte de la doc

| Document | Role |
|---|---|
| [Gouvernail roadmap](./roadmap_backlog_central.md) | Source de verite unique des priorites, du backlog officiel et des rattachements aux anciens plans. |
| [Etude utilisateurs](./etude_utilisateurs.md) | Synthese accessible de l'enquete UX/SHS et de ses conclusions produit. |
| [Concept et philosophie](./concept_et_philosophie.md) | Promesse, principes et limites de CoproScope. |
| [Fonctions cibles](./fonctions_cibles.md) | Tous les blocs fonctionnels, avec statut clair. |
| [Feuille de route](./feuille_de_route.md) | Source historique P0/P1/P2/P3 issue de l'etude; non canonique pour les priorites actives. |
| [Plan directeur local + vault](./plan_directeur_coproscope_local_vault.md) | Source historique d'architecture local + vault; ne pilote plus les sprints directement. |
| [Roadmap produit fini depuis les visuels](./roadmap_produit_fini_visuels_enquete.md) | Source historique de vision UX; les suites actives sont importees dans le gouvernail. |
| [Cycles refonte UX Image -> Dev -> Test](./refonte_ux_cycles_image_dev_test.md) | Cadence operationnelle pour enqueter sur les images, commander les devs, tester les routes livrees et garder les flux en parallele. |
| [Registre cycles refonte UX](./registre_cycles_refonte_ux.md) | Trace de flux et journal des points de coordination; les nouvelles vagues passent par le gouvernail. |
| [Prompts agents refonte UX](./prompts_agents_refonte_ux.md) | Prompts par role pour designer, utilisateur novice, front, back/viewmodel, QA et integrateur-scribe. |
| [Indicateurs centraux de pilotage copro](./indicateurs_pilotage_copro.md) | Themes de gestion, objets noyau, preuves, seuils et actions pour le cockpit. |
| [Accessibilite et registre de langage](./accessibilite_registre_langage.md) | Publics cibles, vocabulaire stable, infobulles et test novice 10 minutes. |
| [Veille open source et integration](./veille_open_source_integration.md) | Radar des briques OSS, gates d'adoption, noyau/plugin/export/transport. |
| [Strategie Obsidian-like depuis l'enquete](./strategie_obsidian_like_enquete_utilisateur.md) | Horizons produit, lecons Obsidian et strategie plugins/vault centree utilisateur. |
| [Resilience anti-accaparement](./resilience_anti_accaparement.md) | Archive complete coproprietaire, compartiments chiffres, quorum de secours et gouvernance des cles. |
| [Livraison test 20h](./livraison_test_2000.md) | Protocole de test novice, commandes Windows et criteres Go/No-go. |
| [Audit UX atelier pieces](./ux_review_atelier_piece.md) | Revue UX/UI de la bascule locale/vault et de l'atelier piece -> point -> action -> preuve. |
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
