# Equipe agile - compta multi-sources

Date de lancement: 2026-05-24 19:55 +02:00.
Roadmap: `RM-2026-0030`.
Chantier: `CH-20260524-195535-RM-2026-0030-compta-multisources-agile`.
Conversation coordination: `CONV-2026-1526`.
Mode: equipe agile gouvernail, cadrage UI/DB avant dev.
Statut: cadrage termine - no-go dev immediat.

## BOT-START

BOT-START - Coordinateur-scribe agile - 2026-05-24 19:55 +02:00

Roadmap: `RM-2026-0030`.
Chantier: `CH-20260524-195535-RM-2026-0030-compta-multisources-agile`.
Conversation: `CONV-2026-1526`.
Role: Coordinateur-scribe agile.
Mission: lancer une equipe agile guidee par le gouvernail pour choisir le MVP compta multi-sources et stabiliser le contrat `compta_reconciliation_queue_v1`, sans dev tant que le MVP, la cible UI et le contrat de donnees ne sont pas consolides.
Ownership modifiable: ce document, `docs/presence_agents.md`, ligne gouvernail `RM-2026-0030`.
Fichiers a eviter: code applicatif, tests applicatifs, instances privees, donnees comptables reelles, exports bruts, secrets, serveurs locaux et tout fichier deja sale sans owner explicite.
Passerelle/registre de trace: ce document, `docs/presence_agents.md`, `docs/roadmap_backlog_central.md`.
Dernier point lu: `AGENTS.md`, `docs/protocole_equipe_agile_agents.md`, `docs/protocole_roadmap_presence_agents.md`, `docs/consignes_bots_interconversations.md`, `docs/presence_agents.md`, `docs/roadmap_backlog_central.md`, `docs/compta_multi_sources_rapprochement_ui_backend_2026-05-24.md` au 2026-05-24 19:55 +02:00.
Tests/preuves attendus: point court, choix MVP argumente, UI cible nommee, contrat read model minimal, GO/NO-GO novice, panier QA anti-fuite; aucun test applicatif tant que le dev n'est pas ouvert.
Lease ownership: 2026-05-24 21:55 +02:00.
Prochaine action: lancer les roles de cadrage et garder front/back en lecture.

## UI cible

- Route candidate: `/comptes/rapprochement`.
- Ecran source: `Controle des comptes`.
- Visuels de reference: `docs/assets/compta-multisources-2026-05-24/01-file-validation-4-sources.png`, `02-matrice-rapprochement.png`, `03-suggestions-classees.png`.
- Decision attendue avant dev: choisir la premiere tranche entre file principale, matrice de completude et detail de suggestions classees.

## Roles

| Role | Conversation | Statut | Ownership |
|---|---|---|---|
| Coordinateur-scribe | `CONV-2026-1526` | `PRET_A_INTEGRER` | Registres et synthese de mission. |
| Designer service / facilitateur MVP | `CONV-2026-1527` / Einstein `019e5b24-d166-7f22-8330-dc15901bbee1` | `CLOTURE` | Concept 1 retenu comme premier ecran; concept 2 audit, concept 3 detail ambigu. |
| Utilisateur novice / representant CS | `CONV-2026-1528` / Carver `019e5b24-d2d3-7633-87f0-939dc7acc13a` | `CLOTURE` | GO partiel sur file 4 sources, NO-GO dev avant libelles/garde-fous. |
| Data / read model | `CONV-2026-1529` / Gibbs `019e5b24-d34d-7e33-bdc5-dcf3a15b3c1c` | `CLOTURE` | Contrat minimal `compta_reconciliation_queue_v1` propose, champs interdits et no-go backend poses. |
| Dev front lecture | `CONV-2026-1530` / Aquinas `019e5b24-d411-7b61-897c-b80838276cc8` | `CLOTURE` | Route dediee `/comptes/rapprochement`, surface UI et risques integration cartographies. |
| QA privacy / regression | `CONV-2026-1531` / Linnaeus `019e5b24-d543-7443-8348-700b092715a4` | `CLOTURE` | Panier anti-fuite, token, export AG et validation append-only consolides. |

## Point court initial

A produire: arbitrage MVP, contrat minimal du read model, criteres de GO novice et panier QA.

En dev: rien. Les roles techniques restent en lecture jusqu'a commande stabilisee et owner code unique.

En enquete: comparer les trois visuels compta, retenir la tranche la plus testable et nommer les libelles novice.

Commande prete: non. La route candidate `/comptes/rapprochement` et le read model `compta_reconciliation_queue_v1` doivent etre verrouilles.

Comparaison visuels enquete: obligatoire sur les trois captures `compta-multisources`.

Agents idle a relancer: aucun pour l'instant; cinq roles lances en lecture seule.

Decision requise: aucun dev tant que le MVP n'est pas choisi et que le novice n'a pas donne GO sur le parcours.

Prochain mouvement: lancer les cinq roles de cadrage, consolider leurs retours, puis decider si un chantier dev separe peut etre ouvert.

Tests/preuves: aucun test applicatif lance; preuve attendue = doc de cadrage, registry presence, et sortie agents.

## Decision consolidee

Verdict: equipe agile lancee et cadrage termine. Le MVP recommande est une
route dediee `/comptes/rapprochement` fondee sur le Concept 1, la file de
validation 4 sources. Le Concept 2 devient vue secondaire d'audit et de
completude. Le Concept 3 devient le detail d'une ligne ambigue.

GO partiel: la direction produit est lisible pour un membre CS novice si l'ecran
dit clairement que CoproScope propose des controles a verifier et ne valide pas
la comptabilite officielle.

NO-GO dev immediat: le contrat read model, la persistance append-only des
validations humaines, les libelles novice et le gate export AG doivent etre
verrouilles avant tout patch.

## Commande UI a stabiliser

Premier ecran:

- titre: `Rapprochement compta multi-sources`;
- badge: `Mode prive local`;
- mention obligatoire: `Suggestions de controle, pas comptabilite officielle`;
- filtres: `A traiter avant AG`, `A confirmer`, `Source absente`, `Conflit
  montant`, `Valide avec reserve`;
- file principale: une ligne par ligne comptable;
- cellules visibles: `Compta`, `Banque`, `Facture`, `Decision / devis`;
- panneau detail: preuves rapprochees, raisons, manques, historique de
  validation;
- actions: `Marquer comme verifie`, `Valider avec reserve`, `Ecarter`,
  `Demander une piece`, `Demander une decision ou un devis`, `Ajouter au
  rapport AG avec reserve`.

Libelles a utiliser:

- `Ligne a verifier`;
- `Preuve trouvee`;
- `Preuve manquante`;
- `Decision ou devis a confirmer`;
- `Question a poser au syndic`;
- `Laisser ouvert`.

Libelles a eviter au premier niveau:

- `rapprochement` sans explication;
- `matrice`;
- `faisceau`;
- `score`;
- `export`;
- `cellule`;
- `strong match`;
- `candidate bundle`;
- `validation proposee`.

## Contrat data minimal

Read model public: `compta_reconciliation_queue_v1`.

Objets minimaux:

- `context`: route, exercice, libelle mode prive;
- `summary`: total lignes, a revoir, sources manquantes, conflits, validees,
  bloquees export;
- `queue[]`: `line_id`, exercice, date, montant, compte public, libelle public,
  statut, raison, prochaine action, href relatif, cellules source, faisceaux,
  validations humaines;
- `source_cell`: famille `bank`, `invoice`, `decision_evidence` ou
  `accounting`, statut, raison, references source publiques, blocage export;
- `candidate_bundle`: rang, confiance, raisons, familles manquantes, conflits,
  etat de validation;
- `human_validation`: decision append-only, role acteur non nominatif,
  horodatage, visibilite rapport AG, lien de remplacement.

Decisions humaines minimales:

- `validate`;
- `validate_with_reserve`;
- `reject`;
- `request_piece`;
- `request_decision_or_quote`;
- `add_to_ag_report`;
- `leave_open`.

Champs interdits: chemins locaux, `raw`, `restricted`, `logs`, `private`,
`file://`, token, secret, email, IBAN/RIB complet, hash/source SHA,
`payload_json`, `event_path`, `source_path`, `source_file`, `original_path`,
`original_name`, `locator_json`, brouillon message brut, texte OCR brut et note
interne non nettoyee.

## Cartographie front

Etat actuel lu par le role front:

- `/comptes` est branche dans
  `server/src/coproscope/web/_app_fragments/part_003.pyfrag`;
- le template courant est
  `server/src/coproscope/web/templates/accounting.html`;
- les styles comptes sont surtout dans
  `server/src/coproscope/web/static/styles_part_07.css` et
  `server/src/coproscope/web/static/styles_part_08.css`;
- `model.ux.comptes` existe deja cote viewmodel, mais `/comptes` consomme
  encore largement `model.accounting.*`.

Orientation future: preferer un nouveau template ou des partials dedies pour
`/comptes/rapprochement`, plus un bloc CSS separe, plutot que grossir les
fichiers comptes existants proches de la limite 600 lignes.

Etats vides obligatoires: read model absent, aucune ligne, banque absente,
facture absente, decision/devis absent, aucun faisceau candidat, aucun resultat
apres filtre, aucune ligne selectionnee, export AG bloque.

## Panier QA

Tests requis si dev ouvert:

- token obligatoire sur `/comptes/rapprochement`, details, filtres et exports;
- hrefs token-safe, token present une seule fois;
- aucun marqueur interdit dans HTML, JSON, TXT/MD, ZIP, rapport AG et captures:
  `C:\Users`, `/Users`, `raw`, `restricted`, `logs`, `private`, `file://`,
  email, IBAN, secret, `token=local-secret`;
- allowlist stricte du read model public;
- chaque validation humaine cree un evenement append-only date;
- suggestion machine toujours affichee comme candidate, jamais comme verite
  officielle;
- rapport AG derive uniquement, `source_of_truth=false`, reserves visibles;
- lignes rouges/oranges non revues bloquent ou avertissent avant rapport.

Panier de tests a reprendre:

- `tests.test_ui_security_routes`;
- `tests.test_security_no_private_sync_leaks`;
- `tests.test_privacy`;
- `tests.test_public_read_models`;
- `tests.test_passation_exports`;
- `tests.test_ui_passation_export_route`;
- `tests.test_ui_comptes_guide`;
- `tests.test_comptascope`.

## Questions ouvertes

- `Decision / devis` couvre-t-il aussi contrat, PV AG, bon de commande et
  reception des le MVP, ou seulement decision/devis ?
- Les statuts orange non revus bloquent-ils l'export AG ou seulement les rouges
  ?
- `Sources orphelines` entre-t-il dans la premiere tranche ou reste-t-il hors
  MVP ?
- Qui a le droit de marquer une ligne verifiee: membre CS, admin, simple lecteur
  ?
- Ou persister exactement les evenements append-only de validation humaine ?
- Faut-il un blueprint derive des trois concepts avant GO novice final, ou le
  Concept 1 suffit-il comme reference ?

## Journal

| Heure | Conversation | Evenement | Note |
|---|---|---|---|
| 2026-05-24 19:55 +02:00 | `CONV-2026-1526` | `BOT-START` | Equipe agile lancee en cadrage lecture seule sur `RM-2026-0030`; code, serveur, instance privee et donnees comptables reelles evites. |
| 2026-05-24 19:58 +02:00 | `CONV-2026-1527`..`CONV-2026-1531` | `AGENTS_LAUNCHED` | Agents Einstein, Carver, Gibbs, Aquinas et Linnaeus lances en lecture seule; aucun code, serveur, instance privee ni donnee comptable reelle. |
| 2026-05-24 20:04 +02:00 | `CONV-2026-1527`..`CONV-2026-1531` | `CADRAGE_DONE` | Cinq roles consolides: MVP Concept 1, GO novice partiel, contrat read model minimal, route dediee `/comptes/rapprochement`, panier QA anti-fuite. NO-GO dev immediat. |
