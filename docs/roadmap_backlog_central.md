# Gouvernail roadmap CoproScope

Date de creation: 2026-05-21.
Source de verite unique de pilotage: oui.

Ce fichier est le gouvernail de CoproScope. Il remplace les feuilles de route,
backlogs, plans de cycles et journaux de coordination comme point de decision.
Les anciens documents restent consultables comme sources, traces, briefs ou
specifications derivees, mais ils ne pilotent plus le produit par eux-memes.

## Regle maitresse

Rien n'est "dans la roadmap" tant qu'une ligne `RM-*` n'existe pas ici.

Une demande n'est pilotable que si elle a:

- un identifiant stable `RM-YYYY-NNNN`;
- un statut explicite;
- une source;
- une prochaine action;
- une trace d'historique append-only;
- un rattachement `CH-*` dans `docs/presence_agents.md` si un chantier demarre.

Les lignes ne sont pas effacees silencieusement. Une erreur, une fusion, une
annulation ou un remplacement se note dans le journal et, si besoin, par un
statut `SUPERSEDE`, `ABANDONNE` ou `CLOTURE`.

## Statuts roadmap

| Statut | Sens |
|---|---|
| `A_QUALIFIER` | Capture officielle, pas encore arbitree. |
| `BACKLOG` | A suivre, mais non planifie. |
| `ROADMAP` | Retenu dans la trajectoire produit/gouvernance. |
| `ACTIF` | Un chantier ouvert travaille dessus. |
| `BLOQUE` | Impossible d'avancer sans decision, source ou arbitrage. |
| `PRET_A_INTEGRER` | Livrable termine, en attente de revue/integration. |
| `INTEGRE` | Integre dans la base de travail ou la doctrine active. |
| `CLOTURE` | Ferme proprement, sans suite attendue. |
| `ABANDONNE` | Abandon explicite, conserve pour memoire. |
| `SUPERSEDE` | Remplace par un autre identifiant. |

## Statuts des anciens plans

| Statut | Sens |
|---|---|
| `SOURCE_HISTORIQUE` | Document utile pour comprendre l'origine, non canonique. |
| `SPEC_DERIVEE` | Specification ou brief executable seulement si rattache a un `RM-*`. |
| `JOURNAL_TRACE` | Journal de coordination passe, non pilotable directement. |
| `REFERENCE_ACTIVE` | Doctrine ou protocole actif, subordonne a ce gouvernail. |

## Registre actif

| ID | Titre | Type | Statut | Priorite | Owner | Source | Prochaine action | Chantiers lies | Preuve/livrable | MAJ |
|---|---|---|---|---|---|---|---|---|---|---|
| `RM-2026-0001` | Unifier roadmap, backlog, presence agents et conversations actives | Gouvernance multi-agents | `INTEGRE` | P0 | Coordinateur docs | Conversation Codex du 2026-05-21 | Appliquer le gouvernail pour toute nouvelle demande | `CH-2026-0001` | `docs/presence_agents.md`, `docs/protocole_roadmap_presence_agents.md`, `AGENTS.md` | 2026-05-21 21:48 +02:00 |
| `RM-2026-0002` | Faire de ce fichier le gouvernail et la roadmap unique | Gouvernance produit | `INTEGRE` | P0 | Coordinateur docs | Conversation Codex du 2026-05-21 22:05 | Utiliser ce gouvernail comme source unique pour toute priorite et tout ajout roadmap | `CH-2026-0002` | Ce fichier, README, AGENTS, protocole, bandeaux legacy | 2026-05-21 22:18 +02:00 |
| `RM-2026-0003` | Produit fini UX conseil syndical | Produit / UX | `ACTIF` | P0 | Coordinateur-scribe UX | `docs/roadmap_produit_fini_visuels_enquete.md`, `docs/backlog_produit_fini_refonte_ux.md`, cycles UX, `docs/audit_adequation_ux_ui_enquete_2026-05-22.md` | Classer explicitement `/exports/passation`: ecran critique novice a passer sous 5s ou lot perf separe repris par `RM-2026-0016` read models | `CH-2026-0003`, `CH-2026-0006`, `CH-2026-0007`, `CH-2026-0008` | Ecrans conseil syndical, actions, preuves, memoire, passation; pieces manquantes et relance contextualisee actionnables; recette `8784` synthetique OK; gate id reel auto; perf Beauvallon amelioree ~38/36/34s -> ~16/18/17s -> couloir ~4.2-6.4s; gate cible `8787` timeout 8s OK; hors-couloir `/demandes`, `/ag-contentieux`, `/demandes/relance` passe en shell leger; live contract Beauvallon temporaire `6 OK` avec timeout 8s; routes principales mesurees sous `0.5s` apres chauffe sur `8791`; `/exports/passation` reste hors seuil a ~18s | 2026-05-22 17:58 +02:00 |
| `RM-2026-0004` | Vault local verifiable et evenements signes | Architecture / confiance | `ACTIF` | P0 | Coordinateur architecture | `docs/plan_directeur_coproscope_local_vault.md`, `docs/backlog_evenements_v1_vers_vault.md`, `docs/vault_format.md`, demande Brice du 2026-05-22 | Recette navigateur interactive sur `beauvallon_test` avec serveur recharge sur le patch perf; profiler `build_dashboard_model` si 17s reste trop long; decisions/incidents restent differes jusqu'a besoin metier explicite | `CH-2026-0010`, `CH-2026-0011` | `docs/runbook_reconstruction_base_projections.md`, backups verifies, pipeline documentaire, ComptaScope 2025, matrices de completude restaurees, `missing-docs` et KPI recalcules, tests cibles `94 OK`; patch perf route passation/actions `28 OK`, mesures Beauvallon TestClient `/actions` `17.2s`, `/exports/passation` `22.4s` | 2026-05-22 13:17 +02:00 |
| `RM-2026-0005` | Orchestration agents, conversations et worktrees | Gouvernance multi-agents | `INTEGRE` | P0 | Coordinateur agents | `docs/orchestration_agents.md`, `docs/registre_cycles_refonte_ux.md`, retours terrain equipe agile | Appliquer `docs/protocole_equipe_agile_agents.md` a toute prochaine demande "equipe agile" | `CH-2026-0004` | `docs/protocole_equipe_agile_agents.md`, `AGENTS.md`, `docs/orchestration_agents.md`, presence et gouvernail mis a jour | 2026-05-21 22:21 +02:00 |
| `RM-2026-0006` | Qualite live, tests novice et regression UI | Qualite produit | `ACTIF` | P0 | Coordinateur QA | `docs/qa_cycle_n_exports_passation_apercu_2026-05-21.md`, `docs/test_novice_live_8766_2026-05-21.md`, `docs/journal_cycles_ux_2026-05-21.md`, `docs/audit_adequation_ux_ui_enquete_2026-05-22.md` | Garder le panier live complet comme regression, puis traiter le NO-GO perf `/exports/passation` avec `RM-2026-0016` si route critique novice | `CH-2026-0005`, `CH-2026-0008` | Tests routes, captures, go/no-go novice, preuve navigateur, absence de CTA trompeur, H1/nav coherents; tests cibles viewmodel/couloir/security/passation `79 OK`; gate live Beauvallon piece -> relance -> depot OK a 8s; hors-couloir demandes/agcontentieux `12 OK`, smoke/security `9 OK`; full live contract Beauvallon temporaire `6 OK`; verification locale complementaire `8791` verte, routes principales sous `0.5s` apres chauffe, `/exports/passation` a ~18s donc NO-GO si ecran critique | 2026-05-22 17:58 +02:00 |
| `RM-2026-0007` | Produit installe, packaging et distribution | Produit / delivery | `ACTIF` | P0 | Coordinateur delivery | `docs/roadmap_produit_fini_visuels_enquete.md`, `docs/feuille_de_route.md`, pivot Brice du 2026-05-22 | Se subordonner a `RM-2026-0014`: livrer d'abord un installable noob qui configure un coffre local et partage uniquement des octets deja chiffres via Drive | `CH-2026-0014` | A produire: installateur Windows, assistant premiere ouverture, diagnostic local, demarrage sans terminal; bootstrap OAuth Drive CLI pret | 2026-05-22 15:34 +02:00 |
| `RM-2026-0008` | Module audit et boite de reprise probatoire | Produit / audit | `ACTIF` | P1 | Coordinateur produit | `docs/commande_cycle9_module_audit_boite_reprise_probatoire.md`, `docs/audit360.md`, convocation AG externe `DOC-14F51C8E5607`, demandes de resolution Drive 021, Gmail `audit pinede` | Exploiter le rapport actualise pour demander corrections/pieces avant AG, puis rattacher les reponses du syndic comme preuves; garder tout audit cloud sur derives anonymises ou syntheses agregees | `CH-2026-0009` | Commande Cycle 9 restauree; frontiere anonymisee `audit_sources_anonymized`; import demandes Thollet/Abour/Roche et mails Gmail; biffage PDF sans couche texte via derive texte; derive audit pour pieces sans identifiants; registre decisions 176 lignes; rapport canonique `rapport_juridique_precontentieux_ag_DOC-14F51C8E5607.md`; copie versionnee `rapport_audit_ag_integrant_demandes_resolution_pieces_DOC-14F51C8E5607_2026-05-22.md`; expertise contradictoire `expertise_juridique_contradictoire_gouvernance_AG_DOC-14F51C8E5607_2026-05-22.md` enrichie noms clairs, malveillance/refere et comptabilite; tests cibles privacy/audit360 OK | 2026-05-22 14:02 +02:00 |
| `RM-2026-0009` | Strategie onboarding et premier succes novice | Produit / UX onboarding | `ROADMAP` | P0 | Coordinateur produit UX | `docs/strategie_onboarding.md`, `docs/test_novice_live_8766_2026-05-21.md`, `docs/ux_novice_p0.md`, `docs/audit_adequation_ux_ui_enquete_2026-05-22.md` | Servir de cadre novice aux 0-30 jours: savoir ou l'on est, trouver une action en moins d'une minute, comprendre preuve et limite de diffusion, sans jargon moteur au premier niveau | `CH-2026-0008` | Parcours premier repere, intention, premiere action, preuve/trace, reprise; gate novice rattachee a `RM-2026-0003` et `RM-2026-0006` | 2026-05-22 01:16 +02:00 |
| `RM-2026-0010` | DocOps: traces mail/email locales comme pieces Communication | Produit / DocOps | `INTEGRE` | P1 | Coordinateur DocOps | Demande Brice du 2026-05-22; agent Chandrasekhar | Utiliser DocOps pour classer les traces locales mail/email/e-mail/courriel; garder tout connecteur boite mail ou envoi automatique comme plugin futur separe | `CH-2026-0012` | `taxonomy.default.yml`, `test_docops_completeness.py`, `docs/docops_actionnable.md`; tests DocOps + pipeline `7 OK` | 2026-05-22 14:02 +02:00 |
| `RM-2026-0011` | Deleguer generalisations et side-quests hors chemin critique | Gouvernance multi-agents | `INTEGRE` | P0 | Coordinateur agents | Demande Brice du 2026-05-22; agent Schrodinger | Appliquer a toute conversation orientee but: le coordinateur garde la piste critique et delegue les generalisations/side-quests bornees a des sub-agents si des threads sont disponibles | `CH-2026-0013` | `AGENTS.md`, `docs/orchestration_agents.md`, `docs/protocole_equipe_agile_agents.md`; verification `git diff --check` OK | 2026-05-22 14:02 +02:00 |
| `RM-2026-0012` | Rendre le travail en background visible | Produit / observabilite | `A_QUALIFIER` | P2 | Coordinateur produit/agents | Demande Brice du 2026-05-22 | Concevoir une vue ou un bandeau qui montre les taches en arriere-plan: dernier passage, prochaine relance, statut, progression, blocages, erreurs et trace consultable, sans exposer secrets ni chemins prives | Aucun | A definir: maquette UX, contrat de donnees jobs/heartbeats, journal utilisateur lisible et gate anti-fuite | 2026-05-22 14:45 +02:00 |
| `RM-2026-0013` | Confidentialite conversationnelle des audits | Privacy / gouvernance IA | `ROADMAP` | P0 | Coordinateur privacy | Demande Brice du 2026-05-22 | Definir et appliquer une garde conversationnelle: pendant les audits, travailler sur derives anonymises, eviter les noms de personnes en clair dans le fil, limiter les noms de fichiers en clair aux pieces strictement necessaires, et fournir des rapports rediges avec numeros de pieces/alias plutot que donnees personnelles | Aucun | Spec a produire: regle de redaction assistant, gabarit de rapport anonymise, checklist avant envoi final, tests/docs anti-fuite conversationnelle | 2026-05-22 15:10 +02:00 |
| `RM-2026-0014` | Installable noob avec partage Drive chiffre | Produit / delivery securise | `ACTIF` | P0 | Coordinateur delivery/securite | Pivot Brice du 2026-05-22: priorite absolue | Brice doit creer le client OAuth Desktop app et placer le JSON hors Git; ensuite activer le vrai upload Drive puis l'assistant installable noob | `CH-2026-0014` | Runbooks OAuth/packaging/checklist noob; `.gitignore` anti-secrets; option `[drive]`; `coprocs drive status/auth/smoke`; gate anti-fuite smoke sans upload; tests `test_gdriveops 8 OK` | 2026-05-22 15:45 +02:00 |
| `RM-2026-0015` | Hygiene Git local et lien GitHub serre | Gouvernance delivery | `INTEGRE` | P1 | Coordinateur Git | Demande Brice du 2026-05-22 | Trier le working tree charge par lots publics avant tout push; utiliser `tools\git\sync.cmd` au debut et avant publication | `CH-2026-0015` | `docs/git_local_github_hygiene.md`, `tools/git/sync.cmd`, `tools/git/install-local-guardrails.cmd`, `.githooks/pre-push`; config locale installee; sync/fetch verifie `ahead=0`, `behind=0` | 2026-05-22 17:02 +02:00 |
| `RM-2026-0016` | Socle DB performant: projections incrementales et read models UI | Architecture / performance local-first | `ACTIF` | P0 | Coordinateur architecture DB | Demande Brice du 2026-05-22: comparaison Obsidian/Logseq, challenge structure DB et methode d'execution | Lot 3: preparer `/actions` en read model public versionne, sans DDL au GET, avec controle `projection_meta`/schema et tests ancienne projection incompatible/read-only | `CH-2026-0016` | Lot 1 integre: `projection_meta`, `event_applied`, `mark_event_applied`, `apply_event_once`, `apply_incremental_events`; lot 2 integre: `/pieces?proof=missing` branche sur read model public allowliste, sans `SELECT *`, sans FTS/MATCH, sans creation de vue persistante au GET, fallback vide prudent si projection configuree absente/cassee, diffusion/candidates normalises, sentinelles `source_file`/`chemin`; tests read model `5 OK`, UI/securite `37 OK`, vault `18 OK` | 2026-05-23 18:43 +02:00 |
| `RM-2026-0017` | Sidequest prioritaire: reconstruction progressive Beauvallon depuis pieces primaires | Simulation / qualite base de connaissance | `ACTIF` | P0 | Coordinateur reconstruction | Demande Brice du 2026-05-23: instance specifique vide, copie du dossier Beauvallon, integration complete des pieces primaires, comparaison obligatoire reel/test, equipe agile et relance 30 min | Arbitrer les categories candidates (`290`, quarantaine, registres humains, restreint, fichiers racine), puis copier le premier lot primaire avec verification hash avant pipeline | `CH-2026-0017` | Commande sidequest creee; instance vide `beauvallon_reconstruction_sim_20260523` preparee hors Git; `doctor` OK et `inventory` OK; manifeste reel candidat hors Git: 772 fichiers, environ 713 Mio; aucune copie primaire encore; rapport final reel/test reste obligatoire | 2026-05-23 18:58 +02:00 |
| `RM-2026-0018` | Dette structurelle: aucun fichier de code au-dessus de 600 lignes | Architecture / maintenabilite | `INTEGRE` | P0 | Coordinateur refactor | Demande Brice du 2026-05-23 22:19: "P absolue: refactor code: pas de fichier de plus de 600 lignes" | Maintenir le garde-fou dans toute livraison code; refactorer avant ajout si un fichier approche ou depasse 600 lignes | `CH-2026-0018` | Regle inscrite dans `AGENTS.md`; garde-fou `tools/check_code_line_limit.py` + `test_code_line_limit`; refactor par facades/modules/includes/fragments; check 0 fichier code >600 lignes; suite `505 OK`, `3 skipped` | 2026-05-23 22:47 +02:00 |
| `RM-2026-0019` | Boucler les fonctionnalites proches sans IA cloud | Produit / local-first | `ACTIF` | P0 | Coordinateur local-first | Demande Brice du 2026-05-23: "Lance des equipes agiles pour les boucler"; audit `docs/audit_gouvernail_maturite_equipes_agiles_2026-05-23.md` | Brancher la route `/actions` sur le read model public versionne, puis faire une passe navigateur live/multi-viewport du couloir piece -> relance -> depot | `CH-2026-0019` | Lots A/B/C integres: lecteur `public_actions_v1` local allowliste; couloir novice clarifie sans vocabulaire demo/fictif/DocAI; passation/share renforces contre secrets OAuth/OpenAI/Bearer et elargissement `scope=event`. Verification commune `117 OK`, `1 skipped` live serveur absent. B/C GO technique local-first; A GO technique lecteur, GO produit reporte au branchement `/actions` | 2026-05-23 23:05 +02:00 |

## Arbitrage 0-90j issu de l'audit UX/UI

Audit source: `docs/audit_adequation_ux_ui_enquete_2026-05-22.md`.

| Horizon | Priorite canonique | Gate de sortie |
|---|---|---|
| 0-30 jours | Lever les NO-GO novices et prouver les boucles courtes: cockpit/action inbox, navigation 3 intentions, ajout document, demande syndic, piece manquante, relance, preuve, export prudent. | GO test novice semi-autonome: l'utilisateur sait ou il est en moins d'une minute, trouve une prochaine action sans documentation externe, et ne peut pas exporter de brut sensible par erreur. |
| 30-60 jours | Transformer les signaux en chaines metier: demandes/SyndicOps, decision -> action -> preuve, ComptaScope guide AG, memoire/passation MVP, membres/droits minimaux. | GO test novice non accompagne sur les parcours cockpit, piece/preuve, comptes et memoire/passation. |
| 60-90 jours | Consolider confiance et collaboration: vault/sync lisibles, anti-confiscation traduite en produit, multi-coffres isoles, indicateurs limites aux cas avec preuve/seuil/action, packaging seulement si UI/vault sont stabilises. | GO confiance: archive verifiable, droits comprehensibles, sync presentee comme transport non fiable, aucun melange cache/cles/exports entre coffres. |

## Gates novice obligatoires

Aucun chantier UI ou UX ne peut etre considere GO produit seulement parce que
les routes repondent en 200 ou que les tests HTML trouvent des libelles.

La cloture doit fournir:

- route(s) reelles testees;
- scenario utilisateur court;
- preuve navigateur multi-viewport, ou justification explicite de non-applicabilite;
- controle mobile/desktop des CTA et du premier viewport;
- H1, titre de route et navigation active coherents;
- aide accessible autrement que par `title` seul;
- absence de jargon moteur au premier niveau;
- action reliee a preuve, diffusion et trace;
- verdict GO/NO-GO novice.

## Sources rattachees

| Document | Statut | Rattachement canonique | Regle d'usage |
|---|---|---|---|
| `docs/feuille_de_route.md` | `SOURCE_HISTORIQUE` | `RM-2026-0003`, `RM-2026-0007` | Lire pour contexte produit; ne pas y ajouter de priorite active. |
| `docs/implementation_plan.md` | `SOURCE_HISTORIQUE` | `RM-2026-0004` | Lire pour contrats v1; les chantiers techniques vivent ici en `RM-*`. |
| `docs/plan_directeur_coproscope_local_vault.md` | `SOURCE_HISTORIQUE` | `RM-2026-0004` | Source d'architecture; ne pilote plus les sprints directement. |
| `docs/roadmap_produit_fini_visuels_enquete.md` | `SOURCE_HISTORIQUE` | `RM-2026-0003`, `RM-2026-0007` | Source de vision UX; convertir toute suite en item `RM-*` ou `CH-*`. |
| `docs/agent_backlog_continu.md` | `SOURCE_HISTORIQUE` | `RM-2026-0005` | Reserve de lots; un agent ne prend un lot que via presence `CH-*`. |
| `docs/backlog_evenements_v1_vers_vault.md` | `SOURCE_HISTORIQUE` | `RM-2026-0004` | Reserve technique; pas de dev sans chantier cree ici. |
| `docs/backlog_produit_fini_refonte_ux.md` | `SOURCE_HISTORIQUE` | `RM-2026-0003` | Reserve UX; pas de dev direct. |
| `docs/audit_adequation_ux_ui_enquete_2026-05-22.md` | `REFERENCE_ACTIVE` | `RM-2026-0003`, `RM-2026-0006`, `RM-2026-0009` | Trace consolidee de l'equipe d'audit UX/UI; ses arbitrages 0-90j et gates novice sont repris dans ce gouvernail. |
| `docs/audit_gouvernail_maturite_equipes_agiles_2026-05-23.md` | `REFERENCE_ACTIVE` | `RM-2026-0019`, `RM-2026-0016`, `RM-2026-0003`, `RM-2026-0006` | Audit de maturite locale-first: classe les fonctionnalites proches, challenge les surpromesses et impose le filtre sans IA cloud. |
| `docs/strategie_onboarding.md` | `SPEC_DERIVEE` | `RM-2026-0009`, `RM-2026-0003`, `RM-2026-0006`, `RM-2026-0007` | Etude produit pour transformer la premiere ouverture en premier succes guide; implementation seulement apres chantier `CH-*`. |
| `docs/registre_cycles_refonte_ux.md` | `JOURNAL_TRACE` | `RM-2026-0003`, `RM-2026-0005`, `RM-2026-0006` | Trace de cycles; les prochaines vagues passent par ce gouvernail. |
| `docs/journal_cycles_ux_2026-05-21.md` | `JOURNAL_TRACE` | `RM-2026-0006` | Journal de livraison; ne remplace pas le statut roadmap. |
| `docs/point_coordination_live_8766_2026-05-21.md` | `JOURNAL_TRACE` | `RM-2026-0006` | Trace live; utile pour verification, non canonique pour prioriser. |
| `docs/commandes/*.md` et `../docs/commande_cycle*.md` | `SPEC_DERIVEE` | Selon l'item `RM-*` indique | Commande executable seulement apres creation d'un chantier `CH-*`. |
| `docs/protocole_roadmap_presence_agents.md` | `REFERENCE_ACTIVE` | `RM-2026-0001`, `RM-2026-0002`, `RM-2026-0005` | Regle de fonctionnement; subordonnee au present gouvernail. |
| `docs/presence_agents.md` | `REFERENCE_ACTIVE` | Tous les `RM-*` actifs | Registre des conversations et chantiers ouverts. |
| `docs/commandes/commande_sidequest_reconstruction_beauvallon_2026-05-23.md` | `SPEC_DERIVEE` | `RM-2026-0017` | Commande de lancement de la simulation prioritaire; execution uniquement via `CH-2026-0017` et instance test vide hors depot. |

## Journal append-only

| Horodatage | ID | Evenement | Trace |
|---|---|---|---|
| 2026-05-21 21:45 +02:00 | `RM-2026-0001` | `CREATE` | Creation du premier item officiel pour rendre la roadmap opposable et relier les conversations actives aux chantiers. |
| 2026-05-21 21:48 +02:00 | `RM-2026-0001` | `INTEGRATE` | Registres crees et references dans `AGENTS.md`, `docs/consignes_bots_interconversations.md` et `docs/orchestration_agents.md`. |
| 2026-05-21 22:05 +02:00 | `RM-2026-0002` | `CREATE` | Decision Brice: repartir sur une base propre gouvernail/roadmap comme source de verite unique. |
| 2026-05-21 22:05 +02:00 | `RM-2026-0003` a `RM-2026-0008` | `IMPORT_LEGACY` | Import des anciennes roadmaps/backlogs comme sources rattachees, sans leur laisser le pilotage actif. |
| 2026-05-21 22:12 +02:00 | `RM-2026-0003` | `ACTIVATE` | Reprise UX demandee par Brice: le chantier actif devient `CH-2026-0003`; `RM-2026-0002` reste reserve au gouvernail roadmap. |
| 2026-05-21 22:18 +02:00 | `RM-2026-0002` | `INTEGRATE` | Gouvernail stabilise: anciennes roadmaps marquees non canoniques, README/AGENTS/protocole branches sur la source unique, presence mise a jour. |
| 2026-05-21 22:18 +02:00 | `RM-2026-0005` | `ACTIVATE` | Demande Brice: rendre la methode equipe agile multi-agents reutilisable par les autres conversations via `AGENTS.md` et un protocole dedie. |
| 2026-05-21 22:21 +02:00 | `RM-2026-0005` | `INTEGRATE` | Methode equipe agile integree: protocole dedie cree, `AGENTS.md` et `docs/orchestration_agents.md` pointent dessus, presence mise a jour. |
| 2026-05-21 22:27 +02:00 | `RM-2026-0003` | `ACTIVATE_WAVE` | Demande Brice "lance une equipe agile": ouverture de `CH-2026-0006` pour continuer l'amelioration produit avec coordinateur, QA, novice/produit et cartographie dev. |
| 2026-05-21 22:51 +02:00 | `RM-2026-0009` | `CREATE` | Demande Brice: etudier la strategie d'onboarding et l'inscrire a la roadmap; creation de `docs/strategie_onboarding.md` comme source de cadrage. |
| 2026-05-21 23:11 +02:00 | `RM-2026-0003` | `ACTIVATE_WAVE` | Demande Brice "relance une nouvelle equipe agile": ouverture de `CH-2026-0007` pour continuer le flux produit apres CI minimale, detail blocage export et detail memoire integres. |
| 2026-05-21 23:20 +02:00 | `RM-2026-0003` | `INTEGRATE_WAVE` | `CH-2026-0007` livre: `/pieces?proof=missing` aligne novice avec demandes syndic, pieces privees, reponse recue, question, etat vide et liens token-safe; tests cibles `21 OK`, suite complete `451 OK`. |
| 2026-05-22 01:16 +02:00 | `RM-2026-0003`, `RM-2026-0006`, `RM-2026-0009` | `AUDIT_UX_UI` | Equipe de 6 agents consolidee dans `docs/audit_adequation_ux_ui_enquete_2026-05-22.md`; arbitrage 0-90j ajoute au gouvernail. |
| 2026-05-22 09:42 +02:00 | `RM-2026-0008` | `ACTIVATION_CHANTIER` | Module audit active via `CH-2026-0009`: commande Cycle 9 restauree, premier lot CLI Audit360 livre; prochaine garde: scan contenu `share-audit`/`share-export` avant publication large. |
| 2026-05-22 10:50 +02:00 | `RM-2026-0008` | `QUALITY_GATE` | Frontiere publication durcie: `share-audit`/`share-export` scannent les contenus texte publiables, bloquent chemins locaux, `file://`, tokens locaux et affectations de cles, bornent le manifeste sans valeur secrete et font echouer `share-audit` en cas de violation. |
| 2026-05-22 11:35 +02:00 | `RM-2026-0008` | `DOCTRINE_AUDIT_AG_ANONYMISE` | Demande Brice: une convocation AG non preparee dans CoproScope devient aussi une source d'audit. Le traitement audit cloud passe obligatoirement par pieces anonymisees: manifeste `audit_sources_anonymized`, texte derive anonymise et PDF brut conserve local. |
| 2026-05-22 11:58 +02:00 | `RM-2026-0008` | `ANALYSE_JURIDIQUE_PRECONTENTIEUSE` | Equipe juridique lancee sur les derives anonymises de `DOC-14F51C8E5607`; conclusion integree: pas d'action judiciaire generale immediate, phase precontentieuse ferme avant AG, puis decision ciblee apres PV signe. |
| 2026-05-22 12:25 +02:00 | `RM-2026-0008` | `PLAN_PRECONTENTIEUX` | Plan de reprise avant AG integre dans `agcontentieux`: couloirs demandes P1, reserves PV, pouvoirs/votes a tracer et corrections; validation anti-avis juridique, donnees privees et marqueurs locaux; tests cibles `10 OK`. |
| 2026-05-22 12:27 +02:00 | `RM-2026-0008` | `RAPPORT_JURIDIQUE_SOURCE` | Suite retour Brice: derive texte anonymise long regenere, equipe juridique relancee, rapport juridique remplace par une version expliquant procedure IA, urgence convocation recue le 2026-05-22, anomalies `AG-AUD-*`, sources `TXT l.xxx`, actions 24-48h et seuils contentieux. |
| 2026-05-22 13:42 +02:00 | `RM-2026-0008` | `AUDIT_AG_DEMANDES_PIECES` | Demande Brice: integrer demandes de resolution Drive 021, courrier LETRECO et Gmail `audit pinede`; biffage local relance, frontiere Audit360 regeneree, registre decisions reconstruit, equipe juridique relancee, rapport canonique remplace par `rapport_juridique_precontentieux_ag_DOC-14F51C8E5607.md` et version horodatee creee; tests privacy/audit360 OK. |
| 2026-05-22 13:53 +02:00 | `RM-2026-0008` | `EXPERTISE_JURIDIQUE_CONTRADICTOIRE` | Demande Brice: refaire l'expertise juridique avec composition d'equipe, charge/decharge, interet a agir ou non, et responsabilites dans la chaine de gouvernance; livrable `expertise_juridique_contradictoire_gouvernance_AG_DOC-14F51C8E5607_2026-05-22.md`, sur sources anonymisees et textes Legifrance verifies. |
| 2026-05-22 14:02 +02:00 | `RM-2026-0008` | `EXPERTISE_REFERE_COMPTABLE` | Demande Brice: ajouter indices de malveillance, necessite potentielle d'agir en refere, noms clairs des documents et elements comptables dans l'evaluation juridique; rapport contradictoire enrichi avec addenda dedies et sources Legifrance CPC/comptabilite copropriete. |
| 2026-05-22 14:02 +02:00 | `RM-2026-0010` | `CREATE_INTEGRATE` | Demande Brice: verifier si le cas mail est prevu dans DocOps et l'ajouter le cas echeant; support `email/e-mail` ajoute a la classification Communication, test dedie et documentation locale sans connecteur ni envoi automatique. |
| 2026-05-22 14:02 +02:00 | `RM-2026-0011` | `CREATE_INTEGRATE` | Demande Brice: generaliser la regle de delegation des generalisations et side-quests par sub-agents quand les threads le permettent; doctrine agents mise a jour. |
| 2026-05-22 14:45 +02:00 | `RM-2026-0012` | `CREATE` | Demande Brice pour plus tard: rendre le travail en background plus visible, avec statut/progression/dernier passage/prochaine relance/blocages et journal consultable sans fuite de donnees locales. |
| 2026-05-22 15:27 +02:00 | `RM-2026-0014` | `PRIORITY_SHIFT` | Pivot Brice: priorite absolue = livrer un installable utilisable par non-geek qui partage l'information via Drive chiffre; ouverture `CH-2026-0014`, `RM-2026-0007` remonte P0 actif, OAuth Google Drive doit etre debloque par Brice mais cache a l'utilisateur final. |
| 2026-05-22 15:34 +02:00 | `RM-2026-0014` | `OAUTH_BOOTSTRAP` | Runbook OAuth/noob cree; secrets OAuth ignores par Git; dependance optionnelle `[drive]`; commandes `coprocs drive status/auth` ajoutees; `drive status` pointe vers `%APPDATA%\CoproScope\oauth\client_secret_dev.json`; tests `test_gdriveops 3 OK`. |
| 2026-05-22 15:45 +02:00 | `RM-2026-0014` | `DRIVE_NOOB_TEAM` | Agents Drive, packaging et securite noob lances puis integres: checklist noob anti-fuite, runbook packaging Windows, gate Drive smoke sans upload, scope strict `drive.file`, chemins OAuth rediges dans status, CLI `drive smoke`, tests `test_gdriveops 8 OK`; pages Google Cloud ouvertes pour intervention Brice. |
| 2026-05-22 01:16 +02:00 | `RM-2026-0006` | `ACTIVATE` | La qualite novice devient P0 active: route 200 + libelles ne suffit plus; preuve navigateur, mobile, clavier, H1/nav et verdict novice requis pour GO UI. |
| 2026-05-22 09:32 +02:00 | `RM-2026-0004` | `ACTIVATE` | Demande Brice: reconstruire la base/projection locale et generaliser le process; ouverture de `CH-2026-0010` sans operation destructive avant diagnostic et sauvegarde. |
| 2026-05-22 09:36 +02:00 | `RM-2026-0004` | `RUNBOOK` | Process generalise cree: `docs/runbook_reconstruction_base_projections.md`; diagnostic initial `beauvallon_test` OK, vault valide, projections compta/completude a reconstruire apres sauvegarde. |
| 2026-05-22 12:16 +02:00 | `RM-2026-0004` | `GO_CONDITIONNEL` | Brice donne le GO sous reserve de l'avis technique; ouverture de `CH-2026-0011` pour executer le runbook sur `beauvallon_test` seulement si preflight, sauvegarde et no-go sont verts. |
| 2026-05-22 12:52 +02:00 | `RM-2026-0004` | `REBUILD_EXECUTE` | `CH-2026-0011` livre un rebuild cible de `beauvallon_test`: sauvegardes verifiees, pipeline documentaire, ComptaScope 2025, matrices de completude restaurees depuis l'instance, `missing-docs` et KPI recalcules; `vault verify` OK, aucune suppression, tests cibles `94 OK`, verdict technique OK avec recette navigateur/passation restante. |
| 2026-05-22 13:17 +02:00 | `RM-2026-0004` | `PERF_PASSATION` | `CONV-2026-0076` supprime les doubles/triples constructions du dashboard dans `/actions`, `/exports/passation` et detail blocage; tests cibles `28 OK`; mesures Beauvallon TestClient: `/actions` 200 en `17.2s`, `/exports/passation` 200 en `22.4s`; live `8772` a recharger si son processus precede le patch. |
| 2026-05-22 01:16 +02:00 | `RM-2026-0009` | `QUALIFY_TO_ROADMAP` | L'onboarding passe de `A_QUALIFIER` a `ROADMAP` comme cadre novice des 0-30 jours, rattache a `RM-2026-0003` et `RM-2026-0006`. |
| 2026-05-22 01:28 +02:00 | `RM-2026-0003`, `RM-2026-0006` | `INTEGRATE_WAVE` | `CH-2026-0008` poursuit le couloir piece/preuve: relance contextualisee clarifiee pour novice, tests couloir `30 OK`, live contract `5 OK`; GO produit complet reporte a la recette navigateur multi-viewport. |
| 2026-05-22 09:39 +02:00 | `RM-2026-0003`, `RM-2026-0006` | `QUALITY_GATE` | Gate substitut ajoute pour `CH-2026-0008`: parcours live piece -> relance -> depot, marqueurs novice en bande premier viewport, hrefs `piece_detail` chaines, tests live `6 OK`, TestClient chainage `3 OK`; capture navigateur reportee car Browser Use iab indisponible. |
| 2026-05-22 13:15 +02:00 | `RM-2026-0003`, `RM-2026-0006` | `RECETTE_NAVIGATEUR_MULTI_VIEWPORT` | Recette couloir piece -> relance -> depot poursuivie sur serveur frais `8784` synthetique: Browser Use recharge l'onglet depot, captures desktop/mobile/tablette `final2`, tests live `6 OK`, chainage token/securite `3 OK`, correctif mobile premier viewport integre; limite: serveur 8766/Beauvallon a rejouer avec un id piece existant. |
| 2026-05-22 13:59 +02:00 | `RM-2026-0003`, `RM-2026-0006` | `QUALITY_GATE_ID_REEL` | Gate live enrichi: `COPROSCOPE_LIVE_PIECE_ID=auto` decouvre un vrai lien detail depuis `/pieces?proof=missing`, masque les sous-tests et rend le timeout configurable; synthetique `8784` `6 OK`, TestClient `16 OK`; Beauvallon frais `8785` NO-GO par timeout/lenteur sur piece/relance/depot. |
| 2026-05-22 14:44 +02:00 | `RM-2026-0003`, `RM-2026-0006` | `PERF_PIECE_RELANCE_DEPOT` | Routes piece/relance/depot contextualisees reutilisent le dashboard deja construit au lieu de le reconstruire; TestClient Beauvallon ~38/36/34s -> ~16/18/17s; gate live `8786` auto OK avec `COPROSCOPE_LIVE_TIMEOUT=35`, echec attendu a `8s`, donc GO utilisateur encore refuse. |
| 2026-05-22 14:49 +02:00 | `RM-2026-0008` | `AUDIT360_CHAIN_RERUN` | Chaine Audit360 relancee apres collecte des derniers mails `audit pinede` et methode renforcee: nouveaux mails Simon/SignalConso et `REDDITION_2024010120241231_3 Annexe1.pdf` dans l'inbox; `pipeline run` OK; `privacy redact-required` OK apres correction de degradation `.xlsx` en revue manuelle; `audit360 prepare-anonymized --all` regenere `audit_sources_anonymized.csv` avec 1169 sources, 964 pretes cloud anonymisees et 205 bloquees pour revue/agregation/biffage manuel. |
| 2026-05-22 15:10 +02:00 | `RM-2026-0013` | `CREATE` | Demande Brice: trop de noms circulent encore en clair dans le fil alors que les audits doivent s'appuyer sur donnees anonymisees; ajout d'un item P0 pour une garde de confidentialite conversationnelle et des gabarits de sortie limites aux pieces/alias necessaires. |
| 2026-05-22 15:42 +02:00 | `RM-2026-0003`, `RM-2026-0006` | `PERF_VIEWMODEL_SANITIZE` | `build_dashboard_model` accelere par fast-path/cache dans la sanitisation anti-fuite UX; mesures Beauvallon isolees modele ~3.8-6.2s et routes couloir ~4.2-6.4s; tests cibles `79 OK`; gate live cible `8787` piece -> relance -> depot OK avec timeout 8s; suite live complete encore NO-GO hors-couloir. |
| 2026-05-22 16:57 +02:00 | `RM-2026-0015` | `CREATE_ACTIVATE` | Demande Brice: mettre en place les meilleures pratiques pour garder le Git local CoproScope plus serre avec le depot GitHub; ouverture de `CH-2026-0015` avec ownership limite a la documentation et aux outils Git locaux. |
| 2026-05-22 17:02 +02:00 | `RM-2026-0015` | `INTEGRATE` | Garde-fous locaux installes: config Git locale prudente, hook `pre-push`, scripts `.cmd` compatibles execution policy Windows, doc hygiene; verification sync OK avec branche alignee et working tree volontairement non publie car charge. |
| 2026-05-22 16:55 +02:00 | `RM-2026-0003`, `RM-2026-0006` | `PERF_HORS_COULOIR_DEMANDES_AG` | Equipe agile relancee par heartbeat: `/demandes`, `/ag-contentieux` et `/demandes/relance` utilisent un shell model leger hors contexte piece au lieu de reconstruire tout le dashboard; nav novice `AG / contentieux`, relance locale sans libelle demo/fictif/test; tests demandes/agcontentieux `12 OK`, smoke/security `9 OK`; mesures Beauvallon TestClient `0.278s/0.256s/0.094s`; prochaine etape: live complet sur serveur frais. |
| 2026-05-22 17:45 +02:00 | `RM-2026-0016` | `CREATE_ROADMAP_P0` | Demande Brice: inscrire en P0 la bascule DB/performance issue du challenge Obsidian/Logseq et de la structure de base. Methode retenue: un proprietaire DB unique pour le noyau critique, une equipe agile autour pour QA perf, privacy, UX novice et integration; livrables cibles: projections incrementales, liens normalises, read models UI, FTS public sanitise et gates rebuild/anti-fuite/perf. |
| 2026-05-22 17:47 +02:00 | `RM-2026-0016` | `ACTIVATE_WAVE` | Demande Brice: lancer une equipe agile guidee par le gouvernail avec verification toutes les 30 minutes. `RM-2026-0014` reste bloque cote JSON OAuth; `RM-2026-0016` devient le P0 actionnable via `CH-2026-0016`, avec proprietaire DB unique sur le noyau et agents QA/privacy/UX en lecture ou contrats. |
| 2026-05-22 18:02 +02:00 | `RM-2026-0016` | `INTEGRATE_LOT1` | Lot 1 socle DB integre: tracking projection SQLite `projection_meta`/`event_applied`, API idempotentes `mark_event_applied`, `apply_event_once`, `apply_incremental_events`; QA GO technique avec reserve routes non branchees; privacy impose read models publics allowlistes; UX choisit `/actions` comme premier branchement; tests `66 OK` et `26 OK`. |
| 2026-05-22 18:32 +02:00 | `RM-2026-0016` | `ARBITRAGE_LOT2` | Heartbeat: lot 1 termine, equipe relancee en cadrage lecture seule avant dev car deux pistes restent en tension: `/actions` comme pivot action/preuve/diffusion et `/pieces?proof=missing` comme premiere route novice deja bornee. Aucun branchement route avant contrat stable et gate privacy. |
| 2026-05-22 19:10 +02:00 | `RM-2026-0016` | `DECISION_LOT2` | Arbitrage apres retours UX, cartographie et QA: `/actions` reste le pivot produit, mais le premier branchement DB public sera `/pieces?proof=missing`, plus borne et mieux adapte pour prouver allowlist, anti-fuite, absence de fallback dashboard global et performance sous 5s. |
| 2026-05-23 18:43 +02:00 | `RM-2026-0016` | `INTEGRATE_LOT2` | Reprise equipe agile: anciens agents lot 2 expires, nouvelle vague coordinateur + QA privacy/perf + UX novice + cartographie DB. `/pieces?proof=missing` integre avec allowlist publique, fallback vide prudent quand une projection configuree est absente/cassee, pas de `SELECT *`, pas de FTS/MATCH, pas de DDL persistant au GET, libelles novice corriges; tests read model `5 OK`, UI/securite `37 OK`, vault `18 OK`. Prochain lot: `/actions` read model public versionne. |
| 2026-05-23 18:51 +02:00 | `RM-2026-0017` | `CREATE_ACTIVATE` | Demande Brice: sidequest prioritaire de simulation dans une instance specifique vide, reconstruisant progressivement la base de connaissance depuis une copie des pieces primaires Beauvallon jusqu'a integration complete. La comparaison finale reel actuel vs dossier test est obligatoire avant tout verdict. |
| 2026-05-23 18:58 +02:00 | `RM-2026-0017` | `PREPARE_LOT0` | Instance vide preparee hors Git, journal novice et gabarits de comparaison crees; `doctor` et `inventory` OK sur instance vide. Manifeste reel candidat produit hors Git: 772 fichiers, environ 713 Mio, aucune copie primaire. Prochain geste: arbitrage des categories candidates avant copie verifiee. |
| 2026-05-23 22:19 +02:00 | `RM-2026-0018` | `CREATE_ACTIVATE` | Demande Brice: priorite absolue de refactor code avec plafond 600 lignes par fichier. Ouverture `CH-2026-0018`; scope code uniquement, docs longues et assets binaires exclus du refactor; equipe de sous-agents lancee sur lots disjoints. |
| 2026-05-23 22:47 +02:00 | `RM-2026-0018` | `INTEGRATE` | Refactor structurel integre: `AGENTS.md` impose le plafond 600 lignes, garde-fou automatise ajoute, fichiers code decoupes en modules/includes/fragments, package-data ajuste. Verification finale: `python tools\check_code_line_limit.py` OK; `python -m unittest discover -s server\tests -v` = 505 tests OK, 3 skips. |
| 2026-05-23 22:55 +02:00 | `RM-2026-0019` | `CREATE_ACTIVATE` | Demande Brice: lancer des equipes agiles pour boucler les fonctionnalites proches au regard du filtre sans IA cloud. Ouverture `CH-2026-0019`; lots disjoints lances sur read model `/actions`, couloir piece-relance-depot, et anti-cloud/passation/share. |
| 2026-05-23 23:05 +02:00 | `RM-2026-0019` | `INTEGRATE_LOTS_A_B_C` | Lots agents integres et testes ensemble: `117 OK`, `1 skipped` live serveur absent. Resultat: B couloir novice et C anti-cloud/passation/share passent en GO technique local-first; A ajoute le lecteur public `/actions` mais le GO produit reste conditionne au branchement effectif de la route `/actions` sur ce read model. |

## Commande naturelle

Quand Brice dit "ajoute ceci a la roadmap":

1. creer un nouvel identifiant `RM-YYYY-NNNN` ici;
2. inscrire la demande dans le registre actif avec le statut `A_QUALIFIER`, sauf priorite explicite;
3. ajouter une ligne dans le journal append-only;
4. si un travail commence tout de suite, creer aussi un chantier dans `docs/presence_agents.md`;
5. ne pas deplacer l'item en `ACTIF` tant qu'une conversation ou un agent n'a pas declare son ownership.

Quand un ancien plan contient une nouvelle idee utile, ne pas le modifier comme
roadmap. Copier l'intention dans une ligne `RM-*`, citer l'ancien plan comme
source, puis travailler depuis le `RM-*`.
