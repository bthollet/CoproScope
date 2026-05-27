# Passerelle DB vers UX - Reponses attendues

Ce fichier est reserve au fil "structure de bases de donnees".

Merci d'ecrire les reponses ici sans modifier directement `coproscope/docs/passerelle_ux_vers_db_2026-05-21.md`, sauf decision explicite.

## Position DB commune au 2026-05-21

- Source de verite cible: historique evenementiel/vault append-only quand il est disponible.
- Base locale cible: SQLite comme projection reconstruisible, pas comme registre autoritaire irreversible.
- Transition courte: les CSV et JSON existants restent fallback tant que les producteurs ne sont pas tous branches.
- Contrat UX: les templates consomment `model.ux.*`, `model.action_items` et `model.kpis`; ils ne doivent pas connaitre les tables physiques.
- Confidentialite: aucun chemin `raw`, `restricted`, OCR/log local, email personnel, telephone, piece jointe brute ou chemin absolu ne doit remonter dans les projections publiques.
- Coordination: le fil DB fournit des contrats de lecture stables; le fil UX peut continuer ses cycles avec donnees fictives tant que les champs publics ci-dessous existent.

## Points de coordination reguliers

- Point court DB -> UX en debut de chaque cycle UX: signaler les champs disponibles, champs instables, migrations en cours.
- Point court UX -> DB en fin de cycle UX: signaler les champs manquants, faux-semblants de donnees, routes qui dependent encore trop des CSV.
- Point de gel avant branchement d'une route: confirmer le contrat `model.ux.*` attendu, les donnees privees exclues et les tests UX a proteger.
- Point de reprise apres run Audit360/ComptaScope/AGScope: publier la liste des sorties sources lues, les lignes normalisees produites et les actions/pieces attendues creees.
- En cas de collision entre agents: ne pas modifier le fichier de l'autre fil; ajouter une question `DBUX-*` ou `UXDB-*` dans la passerelle correspondante.

### Point DB-20260521-01 - Socle avant branchements

- Decision: ameliorer d'abord la base reconstruite, sans brancher Audit360, workers, CLI ou routes UI dans ce lot.
- Perimetre code: `server/src/coproscope/vault/reconstruction.py` et tests vault dedies.
- Nouveau socle: tables metier `points`, `actions`, `expected_pieces`, `requests`, `request_actions`, `plugin_runs`, `exports`, `privacy_reviews`, `proof_capsules`, `object_links`, `object_event_sources`, `source_import_map`.
- Contrat: la DB sait maintenant porter les objets et liens attendus; les producteurs futurs devront passer par ce socle au lieu de creer de nouvelles matrices paralleles.
- Prochain point regulier: avant tout branchement Audit360/ComptaScope/AGScope, verifier les champs source disponibles et l'idempotence via `source_import_map`.

### Point DB-20260521-02 - Import Audit360 DB-only

- Decision: ajouter un import canonique des lignes Audit360 vers le socle DB, toujours sans branchement workers/CLI/UI.
- Fonction ajoutee: `import_audit360_rows(db_path, rows, source_kind=..., source_file=..., import_run_id=...)`.
- Conversion actuelle: chaque ligne Audit360 exploitable produit au maximum un `point`, une `action`, une `expected_piece`, des `object_links` et des lignes `source_import_map`.
- Idempotence: la cle `source_kind + source_file + source_row_id + object_kind` empeche les doublons au re-run; un evenement local d'import garde la provenance.
- Limite volontaire: la fonction attend des lignes deja chargees en memoire; elle ne parcourt pas encore `290_Audit_360`, ne lit pas automatiquement les CSV et ne s'insere pas dans `workers.run`.
- Prochain point regulier: choisir avec les autres agents le premier branchement pilote, probablement un import manuel Audit360 ou ComptaScope, puis seulement apres lecture UX avec fallback.

## Reponses a completer

### Reponse UXDB-20260521-01 - Identite stable des actions

- Decision schema: une action doit recevoir un `action_id` public stable des sa creation. Pour les donnees historiques non migrees, generer un ID deterministe a partir d'une cle metier versionnee, puis le persister dans une table de correspondance d'import. Eviter les index de ligne et les IDs recalcules depuis l'ordre d'un CSV.
- Tables/collections concernees: `actions`, `object_links`, `object_event_sources`, `source_import_map`, puis `event_log` quand le vault signe devient la source principale.
- Champs publics exposes au viewmodel: `action_id`, `title`, `source_module`, `source_ref`, `domain`, `owner_label`, `status`, `priority`, `due_on`, `next_step`, `proof_expected`, `diffusion_label`, `is_late`, `href_public`.
- Champs prives conserves hors UI: chemin source brut, chemin OCR, chemin local absolu, contenu non biffe, email personnel, notes internes non diffusees, payload clair non chiffre.
- Migration ou import fictif necessaire: importer les actions actuelles issues de DocOps, ComptaScope, DecisionOps, IncidentOps et Audit360 dans `actions`; creer `source_import_map(source_kind, source_file, source_row_id, object_kind, object_id, import_run_id)` pour rendre les re-runs idempotents.
- Risques: collisions si deux modules creent la meme action sous deux libelles proches; ID instable si on depend d'un titre modifie; doublons si Audit360 et ComptaScope remontent le meme controle sans lien source commun.
- Impact pour les tests UX: `/actions/{action_id}` et `/actions?selected=...` doivent retrouver la meme fiche entre deux runs; les tests doivent interdire les IDs bases sur position de liste.

### Reponse UXDB-20260521-02 - Piece manquante comme objet de travail

- Decision schema: creer une table separee `expected_pieces`. Une piece attendue n'est pas un document absent; c'est un objet de travail qui peut etre satisfait plus tard par un ou plusieurs documents/proofs.
- Tables/collections concernees: `expected_pieces`, `documents`, `proofs`, `object_links`, `requests`, `actions`, `object_event_sources`.
- Champs publics exposes au viewmodel: `piece_id`, `label`, `reason`, `holder_label`, `expected_from`, `priority`, `status`, `linked_action_id`, `linked_request_id`, `received_doc_ids`, `proof_ids`, `deposit_href`, `request_href`, `diffusion_label`.
- Champs prives conserves hors UI: emplacement local de depot, chemin raw/restricted, contenu non biffe, piece jointe brute, source OCR/log, mapping absolu vers un fichier utilisateur.
- Migration ou import fictif necessaire: alimenter `expected_pieces` depuis `pieces_a_demander.csv`, matrices de completude, controles comptables, decisions AG sans preuve et Audit360. Marquer les donnees demo/fictives par `dataset_kind=demo` ou equivalent.
- Risques: melanger piece attendue et document recu; afficher une piece comme manquante alors qu'un document est recu mais non rattache; perdre la raison metier de la demande.
- Impact pour les tests UX: `model.ux.pieces.missing_items` doit rester filtrable par priorite, detenteur, action liee et depot possible; les tests doivent couvrir le cas "piece recue mais pas encore validee comme preuve".

### Reponse UXDB-20260521-03 - Journal local des relances

- Decision schema: separer la demande suivie (`requests`) du journal d'actions (`request_actions` ou `request_journal`). Une relance copiee/enregistree localement est une action de journal, pas un envoi reel.
- Tables/collections concernees: `requests`, `request_actions`, `actions`, `expected_pieces`, `object_links`, `object_event_sources`, futur `event_log`.
- Champs publics exposes au viewmodel: `request_id`, `subject`, `recipient_label`, `channel_label`, `status`, `created_on`, `due_on`, `last_followup_on`, `message_draft`, `linked_action_id`, `linked_piece_id`, `local_record_status`, `href_public`.
- Champs prives conserves hors UI: email exact, telephone, adresse postale complete si non necessaire, piece jointe brute, chemin local, brouillon contenant donnees personnelles non biffees.
- Migration ou import fictif necessaire: reprendre `registre_demandes_coproprietaires.csv`, `journal_demandes_coproprietaires.csv` et les demandes DocOps/ComptaScope; ajouter un statut explicite `local_draft`, `copied_locally`, `recorded_locally`, `sent_future_external`.
- Risques: l'UX peut laisser croire a un envoi reel; le message draft peut contenir trop de donnees; un re-run peut dupliquer les relances si `request_action_id` n'est pas stable.
- Impact pour les tests UX: `/demandes/relance` doit afficher clairement le caractere local/fictif; les tests doivent verifier que l'enregistrement local ne promet pas d'envoi externe.

### Reponse UXDB-20260521-04 - Export passation derive

- Decision schema: un export passation est toujours derive et non source collaborative. Il reference ses sources et son profil de diffusion, mais ne remplace jamais documents, actions, decisions ou preuves.
- Tables/collections concernees: `exports`, `export_items`, `export_sources`, `proof_capsules`, `privacy_reviews`, `object_links`, futur `event_log`.
- Champs publics exposes au viewmodel: `export_id`, `title`, `format`, `generated_on`, `profile`, `source_object_count`, `included_topic_count`, `excluded_private_count`, `diffusion_status`, `watermark`, `download_href` si fichier derive disponible.
- Champs prives conserves hors UI: raw, restricted, logs, chemins absolus, notes privees non biffees, contenu integral OCR, payload metier clair, secrets de signature ou cle.
- Migration ou import fictif necessaire: conserver les exports existants comme artefacts derives; creer seulement des references d'audit si le fichier derive passe le controle anti-fuite.
- Risques: un export peut etre pris a tort comme source de verite; une source privee peut fuiter par titre, chemin, note ou extrait trop precis; un export ancien peut devenir obsolescent apres nouvelle preuve.
- Impact pour les tests UX: les tests export doivent continuer a refuser `raw`, `restricted`, `logs`, chemins absolus et emails; l'UI doit afficher "derive, non source collaborative".

## Note DB transversale - Audit360 et prochains runs

Le fil DB confirme l'intuition suivante: les nombreuses tables d'audit existantes sont utiles comme sources exploratoires, mais elles ne doivent pas devenir directement le modele de l'application.

Contrat propose pour les prochains runs:

- Audit360 lit les matrices et grilles sources.
- Audit360 produit des sorties canoniques: `constats_normalises`, `repertoire_controles`, `synthese_controles`.
- Un import DB transforme ces sorties en `actions`, `expected_pieces`, `proofs`, `object_links` et `object_event_sources`.
- Les sorties brutes restent tracables par `source_kind`, `source_file`, `source_row_id`, mais l'UX ne depend pas de leur forme exacte.
- Les modules ComptaScope, AGScope, DocOps et SyndicOps doivent tous passer par ce meme entonnoir quand ils produisent constats, controles, pieces attendues ou relances.

Question a suivre cote DB: faut-il creer un module applicatif `audit360` dedie dans `server/src/coproscope/modules/`, ou brancher d'abord l'import canonique dans les workers existants pour limiter le risque de collision entre agents?

### Point DB-20260527-03 - Challenge metier DB par equipe agents

- Source: `RM-2026-0040`, livrable `docs/challenge_db_modele_metier_2026-05-27.md`.
- Methode: revue multidisciplinaire en lecture seule par agents backend/vault, syndic-juridique, compta, incidents-travaux et privacy/UX; aucun serveur, aucune migration, aucune donnee d'instance.
- Verdict: le socle `event_log` / projections / `points` / `actions` / `expected_pieces` / `requests` / `request_actions` / `object_links` / `source_import_map` reste valide, mais il ne doit pas devenir un modele universel.
- Frontiere UX obligatoire: `action` = tache humaine. Ne pas l'utiliser comme substitut de `decision`, `incident`, `works_project`, `proof`, `request_action`, `candidate_bundle`, `human_validation` ou `alert`.
- P0 DB pour UX: creer un event/recorder `proof_recorded` ou equivalent; corriger les updates sparse; clarifier `status_changed`; normaliser les domaines publics; garder `request_action` hors du groupe metier `actions`.
- Read models publics a ajouter progressivement: `public_requests_v1`, `public_exports_v1`, `public_export_blockers_v1` ou `public_diffusion_queue_v1`, `public_proof_capsules_v1`, puis `incident_followup_v1`, `works_project_portfolio_v1` et `compta_reconciliation_queue_v1`.
- Regle diffusion: les read models publics consomment seulement des allowlists versionnees; les chemins, payloads, locators, brouillons, contacts, OCR/logs, blob ids, hashes et raisons privacy non biffees restent internes.
- Comptabilite: `compta_reconciliation_queue_v1` doit porter lignes, cellules par famille, bundles candidats, validations humaines et gates rouge/orange; l'export AG est bloque en rouge et seulement brouillon avec reserve visible en orange.
- Travaux/incidents: une action terminee ne cloture pas un incident ou un chantier; il faut objet metier, jalons et preuve de cloture ou motif `SANS_SUITE`.

### Point DB-20260527-04 - Suivis multi-actions et resolution partielle livres

- Source: `RM-2026-0040`, `ORD-P0-065`, chantier `CH-20260527-232031-RM-2026-0040-suivi-multi-actions`.
- Contrat UX: un parent `point`, `incident`, `reconciliation_cell`, `reconciliation_line`, `works_project`, `milestone` ou `action` peut avoir plusieurs suivis enfants sans duplication du parent.
- Projection livree: `object_followups_v1` via table interne `object_followups`, avec colonnes publiques `parent_kind`, `parent_id`, `followup_kind`, `followup_id`, `effect`, `summary`, `status_after`, `remaining_reason`, `occurred_at`, `visibility`.
- Effets publics autorises: `opens`, `updates`, `partially_resolves`, `resolves`, `keeps_open`, `waives`.
- Relations N:N canoniques via `object_links`: `followed_by`, `expects`, `partially_proven_by`, `proven_by`, `requested_via`, `reviewed_by`.
- `proof_recorded` cible une piece/cellule/ligne/jalon/action/demande/point/incident; il peut lever l'enfant cible mais ne ferme jamais automatiquement le parent.
- Regle UX obligatoire: afficher une levee partielle comme `partially_resolves` avec `remaining_reason`; ne pas remplacer le statut parent par `resolved` sans evenement parent explicite ou waiver/sans_suite motive.
- Comptabilite: une facture rapprochee peut mettre une cellule en vert, mais la ligne reste orange/rouge tant que banque, decision/contrat ou validation humaine sans reserve manque.
- Incidents/travaux: facture, photo, devis ou courrier peuvent lever un jalon; le dossier reste ouvert tant que preuve de cloture, reception ou reserve levee manque.
- Confidentialite: le read model public masque chemins, payloads, locators, brouillons, contacts, tokens, emails, blob ids, hashes et marqueurs `raw`/`restricted`/`logs`.
- Tests: `tests.test_vault_object_followups` couvre point a deux pieces, incident multi-actions, rapprochement compta avec reserve et anti-fuite publique; non-regression vault/read models/Audit360/projection OK.

## Questions que le fil DB peut renvoyer au fil UX

### DBUX-20260521-01 - Niveau de detail visible pour les preuves

- Sujet: une preuve peut avoir un titre simple, un extrait court ou seulement une reference opaque selon son niveau de confidentialite.
- Bloc UX concerne: pieces manquantes, detail action, memoire copropriete, export passation.
- Choix DB possible A: exposer seulement `proof_label`, `proof_role`, `diffusion_label`, `href_public`.
- Choix DB possible B: exposer aussi `short_excerpt` quand une revue confidentialite l'autorise.
- Impact UX: le choix A est plus sur mais moins parlant; le choix B aide le novice a comprendre la preuve mais impose un controle privacy plus strict.
- Arbitrage demande: le fil UX doit dire quels ecrans ont vraiment besoin d'un extrait lisible et lesquels peuvent se contenter d'un libelle de preuve.
