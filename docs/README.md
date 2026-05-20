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
| Contribution | Ajouter [Plan d'implementation](./implementation_plan.md), [Politique de partage GitHub](./github_sharing.md), [Outillage](./outillage_open_source.md) | Contribuer sans casser les garde-fous. |

## Carte de la doc

| Document | Role |
|---|---|
| [Etude utilisateurs](./etude_utilisateurs.md) | Synthese accessible de l'enquete UX/SHS et de ses conclusions produit. |
| [Concept et philosophie](./concept_et_philosophie.md) | Promesse, principes et limites de CoproScope. |
| [Fonctions cibles](./fonctions_cibles.md) | Tous les blocs fonctionnels, avec statut clair. |
| [Feuille de route](./feuille_de_route.md) | Priorites P0/P1/P2/P3 en francais, issues de l'etude. |
| [Etat du developpement](./etat_du_developpement.md) | Ce qui est livre, en cours, prevu, pas prioritaire. |
| [Architecture et flux](./architecture_et_flux.md) | Separation depot public / instances privees / artefacts locaux. |
| [Confidentialite et biffage](./confidentialite_et_biffage.md) | PrivacyOps, BiffageOps, colleges d'acces, versions diffusables. |
| [Audit360](./audit360.md) | Couche transverse faits -> preuves -> risques -> actions. |
| [FactureOps](./factureops.md) | Extraction et anomalies facture. |
| [ComptaScope](./comptascope.md) | Rapprochements comptables candidats et rapport explicatif. |
| [Strategie gestion copro](./strategie_coproscope_gestion_copro.md) | Passage de l'audit documentaire au cockpit de travail CS. |
| [Plan d'implementation](./implementation_plan.md) | Contrat technique v1 et non-objectifs. |
| [Politique de partage GitHub](./github_sharing.md) | Ce qui peut ou ne peut pas remonter dans le depot public. |
| [Outillage open source](./outillage_open_source.md) | Outils locaux installes, retenus ou reportes. |
| [Registre d'avancement](./registre_avancement.md) | Historique des etapes genericisables. |

## Images et concepts UX

Les images dans [`assets/etude-utilisateurs/`](./assets/etude-utilisateurs/) illustrent les directions d'interface issues de l'etude :

- cockpit conseil syndical ;
- registre decisions/actions/preuves ;
- controle des comptes guide ;
- memoire de copropriete et passation CS.

Elles servent a discuter le produit cible. Elles ne sont pas encore une interface livree.

## Ligne editoriale

La documentation doit rester :

- franche sur la maturite : livre, en cours, prevu, pas encore ;
- orientee conseil syndical, pas seulement technique ;
- prudente sur les donnees sensibles ;
- francaise dans ses termes quand cela aide la comprehension ;
- concrete : chaque promesse doit renvoyer a un module, un livrable ou une limite.

