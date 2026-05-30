# Challenge DB modele metier - 2026-05-27

Roadmap: `RM-2026-0040`
Chantier: `CH-20260527-225459-RM-2026-0040-modele-metier-db-challenge`
Conversation: `CONV-2026-1795`
Statut: conclusions consolidees apres revue par agents multidisciplinaires.

## BOT-START

- Heure: 2026-05-27 22:55 +02:00.
- Role: coordinateur DB + challenge metier, sans dev applicatif.
- Ownership: ce document, `docs/passerelle_db_vers_ux_2026-05-21.md`,
  `docs/roadmap_backlog_central.md`, `docs/presence_agents.md`.
- Lectures obligatoires effectuees: `AGENTS.md`,
  `docs/consignes_bots_interconversations.md`,
  `docs/protocole_roadmap_presence_agents.md`,
  `docs/orchestration_agents.md`,
  `docs/roadmap_backlog_central.md`, `docs/presence_agents.md`,
  `docs/point_coordination_live_8766_2026-05-21.md`,
  `docs/coordination_interconversations_2026-05-21.md`,
  `docs/passerelle_db_vers_ux_2026-05-21.md`.
- Garde-fous: aucune donnee d'instance, aucun serveur, aucune migration, aucun
  push, aucune lecture sous `instances/`.

## Methode

Une premiere passe locale avait produit un brouillon. Apres rappel de Brice, la
methode demandee a ete appliquee: lancement d'une equipe d'agents en lecture
seule, chacun avec un angle metier ou backend distinct.

| Agent | Role | Resultat principal |
| --- | --- | --- |
| Hume | Backend DB/vault/reconstruction | Socle sain, mais gaps P0 sur `proof`, update sparse, `status_changed`, events V1, conflits et taxonomie. |
| Copernicus | Syndic, juridique, gouvernance | `decision`, `request`, `request_action`, `proof`, `expected_piece`, `incident` ne doivent pas etre compresses en `action`. |
| Bacon | Comptabilite copropriete | Besoin d'un vrai graphe `accounting_line` / `bank_movement` / `invoice_evidence` / `candidate_bundle` / `human_validation`. |
| Archimedes | Incidents, travaux, assurance | `incident`, `works_project` et `milestone` ont des cycles propres; facture ou action close ne valent pas reception/preuve. |
| Bohr | Privacy, diffusion, UX | Read models publics allowlist a conserver, mais `public_requests_v1`, `public_exports_v1`, blockers et reviews doivent etre modelises. |

Les agents n'ont pas modifie de fichier, n'ont pas lance de serveur et n'ont pas
lu de donnees d'instance.

## Verdict

Le socle DB est bon comme projection locale reconstructible: `event_log`,
`projection_meta`, `event_applied`, `documents`, `document_versions`,
`points`, `actions`, `expected_pieces`, `requests`, `request_actions`,
`object_links`, `object_event_sources`, `source_import_map`, `exports` et les
read models publics a allowlist sont de bons choix.

Le modele n'est pas encore assez solide comme modele metier cible. Il couvre
bien le flux simple "point de vigilance -> action -> piece attendue -> demande",
mais plusieurs objets importants ont encore tendance a etre aplatis dans
`action` ou `expected_piece`. Ce serait une erreur de conception pour la suite:
on perdrait l'audit juridique, la preuve, les cycles incident/travaux, les
validations comptables humaines et les gates de diffusion.

Decision de challenge: `action` reste une tache humaine. Elle ne doit pas porter
la verite juridique, comptable, documentaire, incident, travaux ou privacy.

## Objets a conserver

- `event_log`, `projection_meta`, `event_applied`: noyau append/projection.
- `documents`, `document_versions`: versionnement documentaire prive.
- `points`: constats, anomalies, risques, controles a qualifier.
- `actions`: taches humaines et suites operationnelles.
- `expected_pieces`: pieces ou preuves attendues, pas encore acquises/validees.
- `requests`, `request_actions`: demandes et journal de relances/reponses.
- `privacy_reviews`, `proof_capsules`, `exports`: diffusion derivee et gates.
- `object_links`, `object_event_sources`, `source_import_map`: tracabilite et
  idempotence d'import.
- `public_actions_v1`, `public_missing_pieces_v1`: read models publics stricts,
  a renforcer mais a garder.

## Objets a promouvoir

| Objet | Pourquoi il doit etre premier rang |
| --- | --- |
| `proof` | La table existe, mais la frontiere preuve attendue / piece candidate / preuve validee est centrale. |
| `decision` | Une resolution AG/CS est une source juridique, pas une tache. Elle peut produire plusieurs actions. |
| `incident` | Sinistre ou signalement a cycle propre: criticite, lieu, assurance, tiers, statut, preuve de cloture. |
| `works_project` | Travaux: decision, devis, commande, reception, reserves, garanties, budget, preuves. |
| `milestone` | Jalon probatoire d'incident/travaux: declaration, expertise, OS, reception, reserve levee. |
| `alert` | Signal systeme/privacy/sync qui peut bloquer une diffusion sans etre une action ni un incident. |
| `suggestion` | Proposition machine non engageante; devient action seulement apres choix humain. |
| `accounting_line` | Ligne comptable a justifier avec identite stable et statut officiel/reconstruit. |
| `bank_movement` | Mouvement bancaire distinct d'un document ou d'une facture. |
| `invoice_evidence` / `invoice_line` | Preuve facture et details facture, sans chemin source public. |
| `decision_evidence` | Decision AG/CS liee au rapprochement comptable/travaux. |
| `contract_obligation` | Obligation contractuelle periodique ou conditionnelle. |
| `reconciliation_cell` | Etat par famille de source pour une ligne comptable. |
| `candidate_bundle` | Hypothese multi-source de rapprochement, pas une piece attendue. |
| `human_validation` | Decision humaine append-only, pas une action. |
| `syndic_question` | Question preparee, distincte d'une action envoyee ou d'une request reelle. |

## Frontieres conceptuelles

| Ne pas confondre | Regle |
| --- | --- |
| `decision` et `action` | Une decision cree des obligations; une action les execute. |
| `expected_piece`, `document`, `proof` | L'attente, le fichier et la preuve qualifiee sont trois etats differents. |
| `request`, `request_action`, `action` | Une demande a un journal; une relance n'est pas forcement une tache metier. |
| `incident` et `action` | L'action traite l'incident; elle ne le remplace pas. |
| `works_project` et `action` | Le chantier porte reception, reserves et garanties; une action ne suffit pas. |
| `candidate_bundle` et `expected_piece` | Un candidat comptable est une hypothese, pas une preuve manquante. |
| `human_validation` et `action` | La validation est une decision d'audit append-only. |
| `suggestion` et `validation` | La machine suggere; l'humain valide ou rejette. |
| `export` et source de verite | Un export est derive et doit rester `source_of_truth=false`. |
| `alert` et `incident` | Une alerte peut bloquer ou escalader; elle n'est pas toujours un objet metier. |

## Matrice signal vers objet cible

| Signal entrant | Objet primaire | Objets derives autorises | Remarque DB/UX |
| --- | --- | --- | --- |
| Ligne Audit360 vigilance | `point` | `action`, `expected_piece`, liens source | Modele actuel correct, a enrichir par domaine. |
| Ligne Audit360 preuve attendue | `expected_piece` | `request`, `action` | Ne pas creer `proof` sans revue. |
| Piece candidate detectee | `document` / candidat | `proof` apres validation | Pas de preuve automatique. |
| Preuve validee | `proof` | satisfaction piece, capsule, export | P0: ajouter event/recorder. |
| Demande syndic | `request` | `request_action`, action liee | `message_draft` reste prive. |
| Relance ou reponse | `request_action` | changement statut demande | Ne pas ranger comme action metier. |
| Resolution AG/CS | `decision` | actions, pieces, requests | Besoin d'une table/projection decisions. |
| Incident/sinistre | `incident` | action, request, piece de cloture | Cloture interdite sans preuve ou sans-suite motive. |
| Travaux votes | `works_project` | milestones, actions, pieces | Reception/reserves/garanties explicites. |
| Facture | `invoice_evidence` | candidate_bundle, proof apres revue | Facture seule ne prouve pas reception travaux. |
| Ligne comptable | `accounting_line` | cells, bundles, questions | Une ligne = une ligne de queue. |
| Mouvement bancaire | `bank_movement` | reconciliation cell/bundle | Supporter 1-n, n-1, n-n. |
| Validation comptable | `human_validation` | gate export, reserve | Append-only, pas action. |
| Question syndic compta | `syndic_question` | request/action apres validation | Pas d'envoi automatique. |
| Alerte sync/privacy | `alert` | blocker, action, incident si grave | Jamais de chemins publics. |
| Suggestion IA | `suggestion` | action seulement si acceptee | Non publique par defaut. |

## Corrections DB P0

| ID | Correction | Justification |
| --- | --- | --- |
| `DBCH-20260527-01` | Ajouter event + recorder `proof_recorded` / `proof_attached`. | `proofs` existe mais n'est pas alimente clairement; toute la chaine de preuve en depend. |
| `DBCH-20260527-02` | Corriger l'update sparse des recorders. | Des champs absents passes en chaine vide peuvent effacer titre, domaine, owner ou preuves liees. |
| `DBCH-20260527-03` | Formaliser `status_changed`: appliquer aux tables courantes ou le declarer observation-only. | Les read models lisent `actions.status` et `expected_pieces.status`; ils peuvent rester obsoletes. |
| `DBCH-20260527-04` | Aligner les events utilises avec `EVENT_TYPES_V1`. | `conflict_resolved`, `status_conflict_resolved`, `audit360_imported` sont utilises cote reconstruction mais pas coherents dans le contrat V1 inspecte. |
| `DBCH-20260527-05` | Restreindre la resolution de conflits aux event_ids resolus. | Une suppression globale par objet/champ peut masquer un conflit futur. |
| `DBCH-20260527-06` | Sortir `REQUEST_ACTION_RECORDED` du groupe hash-only `actions`. | Le journal de demande brouille la notion d'action metier. |
| `DBCH-20260527-07` | Ajouter unicite/detection fork `(device_id, sequence)` dans la reconstruction DB. | La projection memoire detecte ce fork; la DB doit etre alignee. |
| `DBCH-20260527-08` | Normaliser une taxonomie publique de domaines. | `assurance`, `travaux`, `contrats`, `compta` doivent etre coherents entre actions et pieces. |

## Corrections DB P1

| ID | Correction | Justification |
| --- | --- | --- |
| `DBCH-20260527-09` | Creer `decisions` + read model gouvernance. | Evite de reduire AG/CS a des actions. |
| `DBCH-20260527-10` | Creer `incidents`, events incident et `incident_followup_v1`. | Preserve criticite, assurance, preuve de cloture. |
| `DBCH-20260527-11` | Creer `works_projects`, `milestones`, read models travaux. | Preserve devis, ordre de service, reception, reserves, garanties. |
| `DBCH-20260527-12` | Creer `alerts` ou `diffusion_alerts`. | Les alertes sync/privacy doivent pouvoir bloquer sans fuite. |
| `DBCH-20260527-13` | Creer `compta_reconciliation_queue_v1`. | Le rapprochement multi-source ne rentre pas dans action/piece. |
| `DBCH-20260527-14` | Ajouter event append-only de validation comptable humaine. | La validation est une decision d'audit, pas une tache. |
| `DBCH-20260527-15` | Remplacer candidat facture aplati par cells + bundles. | Necessaire pour split/group et familles de source multiples. |
| `DBCH-20260527-16` | Ajouter `bank_movement` et sources orphelines. | Banque absente du modele actuel de rapprochement inspecte. |
| `DBCH-20260527-17` | Completer `privacy_reviews` et `exports` par items/sources/blockers. | Le schema actuel est trop court pour les gates de diffusion. |
| `DBCH-20260527-18` | Versionner `public_missing_pieces_v1` via `projection_meta`. | Symetrie avec `public_actions_v1`. |
| `DBCH-20260527-19` | Ajouter `public_requests_v1`, `public_exports_v1`, `public_export_blockers_v1`, `public_proof_capsules_v1`. | UX publique sans fallback vers donnees privees. |
| `DBCH-20260527-20` | Creer table/projection `annotations` ou recorder `pdf_annotation_created`. | La projection hash-only connait les annotations; la DB reconstruite ne les materialise pas. |

## Invariants de diffusion

1. Projection publique = allowlist stricte, jamais `SELECT *`, jamais vue SQL
   persistante exposee sans controle, jamais fallback dashboard prive.
2. Diffusion inconnue = `Conseil syndical uniquement` ou niveau conservateur.
3. Export = derive, `source_of_truth=false`, avec watermark et blockers.
4. Aucun read model public ne sort chemin local, `file://`, `raw`,
   `restricted`, `logs`, `private`, payload brut, OCR/log local, token, email,
   telephone, IBAN complet, blob id, locator interne, brouillon de message,
   table de correspondance de biffage ou identifiant source sensible.
5. `event_log.event_path`, `payload_json`, `payload_sha256`,
   `documents.original_name` non biffe, hashes, blob ids, `proofs.locator_json`,
   `source_import_map.source_file`, `requests.message_draft`,
   `privacy_reviews.reason` non biffe, `proof_capsules.redacted_blob_id` et
   `export_blob_id` sont interdits en projection publique.
6. Une preuve publique expose au maximum label, role, statut et lien public
   controle; extrait court seulement apres revue privacy explicite.
7. `/exports/actions.*` et futurs exports doivent consommer le read model public
   strict, pas un modele dashboard filtre a posteriori.

## Read models cibles

| Read model | Statut recommande |
| --- | --- |
| `public_actions_v1` | Conserver, enrichir taxonomie/domaines. |
| `public_missing_pieces_v1` | Conserver, versionner, renforcer anti-fuite. |
| `public_requests_v1` | Creer pour demandes et relances sans brouillons ni contacts. |
| `public_exports_v1` | Creer avec `source_of_truth=false`, watermark, blockers, profil. |
| `public_export_blockers_v1` / `public_diffusion_queue_v1` | Creer pour raisons bloquantes actionnables. |
| `public_proof_capsules_v1` | Creer apres recorder `proof` et gate privacy. |
| `audit360_points_to_verify_v1` | Creer pour separer constats et actions. |
| `incident_followup_v1` | Creer apres table `incidents`. |
| `works_project_portfolio_v1` / `works_project_detail_v1` | Creer apres tables travaux. |
| `compta_reconciliation_queue_v1` | Creer comme read model dedie multi-source. |

## Comptabilite: modele minimal cible

Le rapprochement comptable ne doit pas etre un ensemble d'actions. Le read model
`compta_reconciliation_queue_v1` doit porter:

- `context`: version, exercice, generation, profil privacy,
  `source_of_truth=false`.
- `summary`: total lignes, rouges, oranges, validees, validees avec reserve,
  bloquees export, questions ouvertes.
- `queue[]`: `line_id`, date, compte, libelle public, tiers, montant signe,
  statut global, severite, raison novice, prochain geste humain,
  `selected_bundle_id`, derniere validation.
- `cells[]`: famille `accounting`, `bank`, `invoice`, `decision_contract`,
  statut, severite, export gate, raison publique, refs publiques, nombre de
  candidats.
- `candidate_bundles[]`: rang, confiance, sources par famille, ecarts
  montant/date, familles manquantes, conflits.
- `latest_validation`: decision, reserve publique, role, horodatage,
  visibilite rapport AG.

Gates export AG:

- Rouge: facture absente significative, banque absente/contradictoire, ecart
  montant hors tolerance, decision/contrat obligatoire absent, candidat non revu
  pour inclusion AG, fuite de source privee. Bloque l'export.
- Orange: candidat plausible non valide, split/group a confirmer, OCR faible,
  decision en attente de PV, petit ecart, validation avec reserve. Export
  brouillon seulement avec reserve visible.
- Vert: cellules coherentes, preuve complete ou validation humaine sans reserve.

## Incidents et travaux: cycles cibles

Cycle incident recommande: `NOUVEAU` -> `A_QUALIFIER` ->
`ASSURANCE_A_QUALIFIER` ou `EN_COURS` -> `EN_ATTENTE_PREUVE` ->
`A_CLOTURER` -> `CLOTURE_AVEC_PREUVE` / `SANS_SUITE`.

Cycle travaux recommande: `A_QUALIFIER` -> `VOTE_A_RETROUVER` ->
`DEVIS_A_COMPARER` -> `DEVIS_RETENU` -> `COMMANDE_A_CONFIRMER` ->
`TRAVAUX_EN_COURS` -> `RECEPTION_A_PROUVER` -> `RESERVES_A_SUIVRE` ->
`GARANTIE_A_SURVEILLER` -> `CLOS_AVEC_PREUVES`.

Regle: une facture ne cloture pas un chantier, un devis retenu ne prouve pas les
travaux, une action faite ne cloture pas un sinistre. Il faut un objet metier et
une preuve de cloture ou un motif `SANS_SUITE`.

## Arbitrages a demander a Brice

1. Prioriser `proof` comme prochain chantier DB P0 avant extensions de
   diffusion/export. Recommandation: oui.
2. Valider la creation de `decisions` comme objet de gouvernance distinct de
   `actions`. Recommandation: oui.
3. Choisir l'ordre apres `proof`: `alerts/privacy gates`, puis
   `compta_reconciliation_queue_v1` si l'objectif court terme est AG/export, ou
   `incident_followup_v1` si l'objectif court terme est suivi terrain.
4. Definir les publics: conseil syndical, syndic, coproprietaires, occupants,
   externe. Un seul read model ne doit pas servir tous les publics.
5. Decider si les preuves publiques peuvent contenir des extraits courts.
   Recommandation: label seul par defaut, extrait seulement apres revue.
6. Valider la taxonomie publique initiale:
   `general`, `documents`, `confidentialite`, `syndic`, `ag`, `decisions`,
   `comptes`, `assurance`, `travaux`, `incidents`, `contrats`.
7. Decider si `alerts` est generique ou specialise en `sync_alerts` /
   `privacy_alerts`. Recommandation: table generique typee.

## Tests recommandes

- `proof_recorded`: preuve creee, liee a `expected_piece`, piece satisfaite,
  aucune fuite publique.
- Update sparse: une mise a jour partielle ne vide pas titre, domaine, owner,
  proof attendu ou liens.
- `status_changed`: statut courant mis a jour ou conflit explicite.
- Conflit resolu puis nouveau conflit: le nouveau conflit reste visible.
- Fork `(device_id, sequence)` detecte en reconstruction DB.
- Domaines publics: `assurance`, `travaux`, `contrats`, `compta` normalises
  pareil entre actions et pieces.
- `public_missing_pieces_v1`: schema/version/allowlist symetriques avec
  `public_actions_v1`.
- Incident: fuite + assurance cree `incident`, action, piece attendue, request
  optionnelle; cloture refusee sans preuve ou sans-suite motive.
- Travaux: resolution + devis + attestation + facture + PV reception projettent
  un `works_project` avec milestones; facture seule ne cloture pas.
- Compta: cinq lignes synthetiques couvrant vert, facture manquante, decision
  manquante, conflit montant, orange avec reserve.
- Validation comptable: deux validations successives, derniere active,
  historique conserve.
- Export AG: rouge bloque, orange exige reserve visible, suggestion machine
  jamais exportee comme verite.
- Privacy read models: aucun chemin, token, email, telephone, IBAN complet,
  payload brut, OCR/log, brouillon ou blob id dans actions, pieces, demandes,
  exports, cellules, bundles, validations, questions.

## Verification locale

Commandes executees le 2026-05-27 23:13 +02:00:

```powershell
cd server
.\.venv\Scripts\python.exe -m unittest tests.test_audit360_import tests.test_public_read_models tests.test_requestops tests.test_decisionops tests.test_incidentops tests.test_vault_projection_events tests.test_vault_reconstruction_local tests.test_vault_reconstruction_archive tests.test_comptascope tests.test_accounts_identity -v
cd ..
.\server\.venv\Scripts\python.exe .\tools\check_code_line_limit.py
git diff --check
```

Resultats:

- 70 tests OK.
- Garde-fou 600 lignes OK.
- `git diff --check` OK; avertissements CRLF preexistants sur fichiers deja
  modifies hors de ce lot.
- Aucun serveur, aucune migration, aucune donnee d'instance.

## BOT-END

- Heure: 2026-05-27 23:13 +02:00.
- Livrables: ce document et le point `DB-20260527-03` dans
  `docs/passerelle_db_vers_ux_2026-05-21.md`.
- Sortie: challenge DB livre sans patch applicatif; backlog de corrections DB
  et arbitrages Brice identifies.

## Addendum implementation - CONV-2026-1808 / ORD-P0-065

Le verrou multi-suivis demande ensuite par Brice a ete implemente dans le vault,
sur donnees synthetiques uniquement.

Contrat livre:

- `object_links` reste la relation N:N canonique entre parent et enfant.
- Table interne append-only `object_followups`, exposee cote UX/tests comme
  read model `object_followups_v1`.
- Evenements V1 ajoutes: `proof_recorded` et `object_followup_recorded`.
- Relations normalisees: `followed_by`, `expects`, `partially_proven_by`,
  `proven_by`, `requested_via`, `reviewed_by`.
- `proof_recorded` cible explicitement une `expected_piece`, une
  `reconciliation_cell`, une `reconciliation_line`, un `milestone`, une
  `action`, une `request`, un `point` ou un `incident`.
- Une preuve met a jour seulement l'enfant cible, par exemple
  `expected_pieces.proof_ids_json` et `expected_pieces.status`.
- Le statut du parent `point`, `incident`, ligne/cellule de rapprochement ou
  chantier n'est jamais ferme automatiquement par un enfant.
- Les effets publics possibles sont: `opens`, `updates`,
  `partially_resolves`, `resolves`, `keeps_open`, `waives`.

Scenarios verrouilles par tests:

- point avec deux pieces attendues: la premiere preuve passe le parent en suivi
  public `partially_resolves`, garde le point `open` et laisse la deuxieme piece
  `open`;
- incident avec deux actions et une preuve photo partielle: les trois suivis
  restent chronologiques sous le meme parent, sans dupliquer l'incident;
- rapprochement compta avec facture rapprochee mais banque manquante: le suivi
  reste `orange` / `keeps_open` avec raison restante;
- read model public: synthese `leve partiellement`, raison restante et
  visibilite conservatrice, sans chemins, payloads, locators, brouillons,
  contacts, tokens ni marqueurs bruts.

Tests executes:

```powershell
cd server
.\.venv\Scripts\python.exe -m unittest tests.test_vault_object_followups tests.test_event_types -v
.\.venv\Scripts\python.exe -m unittest tests.test_vault_object_followups tests.test_public_read_models tests.test_audit360_import tests.test_vault_reconstruction_local tests.test_vault_projection_events tests.test_event_types -v
.\.venv\Scripts\python.exe -m unittest tests.test_ui_comptes_rapprochement -v
.\.venv\Scripts\python.exe -m unittest tests.test_security_no_private_sync_leaks -v
```

Resultats: 10 tests cibles OK, puis 40 tests de non-regression OK, puis 4
tests UI compta rapprochement OK, puis 8 tests anti-fuite/sync prive OK. Aucun
serveur, aucune instance privee, aucune migration et aucun push.
