# Equipe agile - Audit360 ORD-P0-011 boite de reprise

Date de lancement: 2026-05-25 02:14 +02:00.
Mode: equipe agile de cadrage produit, lecture seule, sans dev.

## BOT-START

```text
BOT-START - Coordinateur-scribe agile - 2026-05-25 02:14 +02:00
Roadmap: RM-2026-0008 / RM-2026-0006
Ordre: ORD-P0-011 / AUDIT360-BOITE-REPRISE
Chantier: CH-20260525-021441-RM-2026-0008-audit360-boite-reprise
Conversation: CONV-2026-1654
Role: Coordinateur-scribe agile
Mission: qualifier une fiche ou un atelier de reprise d'un constat unique, permettant de transformer un constat epars en reprise prudente: fait, preuve attendue, action humaine, limite.
Ownership modifiable: docs/equipe_agile_2026-05-25_audit360-boite-reprise.md, docs/presence_agents.md, trace append-only docs/roadmap_backlog_central.md et heartbeat relance-equipe-agile-gouvernail-autonome.
Fichiers a eviter: code applicatif, tests applicatifs, templates, CSS, worktree principal sale, instances privees, documents bruts, OCR/logs, exports bruts, secrets, push GitHub, serveurs non reserves, RM-2026-0017 / ORD-P0-990, reouverture ORD-P0-010 sans nouveau diff ou decision Brice.
Dernier point lu: AGENTS.md, protocoles equipe agile/orchestration/roadmap/presence, consignes interconversations, gouvernail, presence, mission ORD-P0-010 cloturee et commande Cycle 9 boite de reprise probatoire.
Tests/preuves attendus: synthese multi-roles, GO/NO-GO novice, distinction explicite avec la fiche Point a verifier ORD-P0-010, cible UI future, contrat public fictif ou anonymise, panier privacy/security/no-private/line-limit/smoke, decision explicite avant tout owner code.
Risque de collision: worktree principal sale; aucun patch code autorise dans ce chantier. Back/viewmodel et QA sont reserves mais non lances faute de capacite initiale.
Lease ownership: jusqu'au 2026-05-25 04:14 +02:00.
Prochaine action: attendre les retours designer, novice et front; lancer back/viewmodel et QA si capacite de threads disponible, sinon reprise coordinateur minimale au prochain heartbeat.
```

## Etat initial

- A tester maintenant: aucune UI live. Le lot doit d'abord stabiliser la
  commande produit et les preuves attendues sur donnees fictives ou derivees
  anonymisees.
- En dev maintenant: aucun dev; pas de worktree code ouvert.
- En enquete maintenant: designer, novice et front lecture seule lances;
  back/viewmodel et QA reserves faute de capacite de threads.
- Commande prete: pas encore. La direction produit est une reprise prudente
  d'un constat unique, pas un tableau Audit360 large et pas un verdict.
- Comparaison visuels enquete: comparer aux blueprints Audit360 du 2026-05-24
  et a la commande ORD-P0-010, sans rouvrir le lot `Point a verifier`.
- Agents idle a relancer: `CONV-2026-1658` back/viewmodel et
  `CONV-2026-1659` QA/privacy sont reserves mais non lances.
- Decision requise: aucune decision Brice immediate. Un owner code futur devra
  etre valide explicitement et partir en worktree dedie.
- Prochain mouvement: recuperer les retours designer/novice/front, puis lancer
  back/QA ou consolider une commande bornee en lecture seule.
- Tests/preuves: `git diff --check` documentaire; aucun serveur, aucun test
  applicatif, aucune instance privee.

## Roles

| Conversation | Role | Statut | Agent |
|---|---|---|---|
| `CONV-2026-1654` | Coordinateur-scribe agile | CLOTURE | local |
| `CONV-2026-1655` | Designer service / facilitateur | CLOTURE | Raman `019e5c7c-913a-71b0-b6e9-99fe3724e41e` |
| `CONV-2026-1656` | Utilisateur novice / membre CS | CLOTURE | Newton `019e5c7c-919e-7c90-b359-accf550f9716` |
| `CONV-2026-1657` | Dev front lecture seule | CLOTURE | Mencius `019e5c7c-9211-7603-b44f-680b02a17aa8` |
| `CONV-2026-1658` | Dev back / viewmodel lecture seule | CLOTURE | James `019e5c7e-529b-7c60-b423-fb8c9b39bf96` |
| `CONV-2026-1659` | QA privacy / regression | CLOTURE | Kant `019e5c7f-cf95-7192-84d7-a64c98015430` |

## Contraintes produit

- Le premier ecran doit dire qu'il s'agit d'une reprise de constat, pas d'un
  verdict juridique, comptable ou automatique.
- Le flux cible reste `fait -> preuve -> regle -> action`, avec limite,
  reserve et diffusion lisibles.
- Les donnees doivent etre fictives, de test ou derivees anonymisees.
- Une preuve candidate ne clot jamais seule un constat.
- Toute action reste humaine: demander une preuve, rattacher une piece,
  noter une reserve, preparer une question ou ouvrir une action liee.
- Les sorties diffusable restent derivees et token-safe: aucun nom reel,
  chemin local, OCR brut, log, token, export brut ou champ source interne.

## Difference avec ORD-P0-010

`ORD-P0-010` a cadre une fiche `Point a verifier`: une unite de controle avec
preuve attendue et validation humaine.

`ORD-P0-011` cadre une boite de reprise: un espace de travail pour reprendre un
constat epars, expliciter ce qui est acquis, ce qui manque, ce qu'un humain doit
faire et ce qui ne peut pas etre affirme. Il peut consommer un point a verifier,
mais ne doit pas le dupliquer ni rouvrir le lot precedent.

## Retour designer - CONV-2026-1655

Verdict: GO cadrage produit, NO-GO dev immediat dans ce chantier. GO dev
seulement dans un chantier dedie, avec donnees fictives ou derivees anonymisees,
read model public allowlist, qualification novice et tests anti-fuite.

Separation produit:

- `ORD-P0-010`: fiche `Point a verifier`, un point deja cadre, avec preuve ou
  validateur a demander.
- `ORD-P0-011`: atelier de reprise d'un constat epars, pour transformer un
  signal mal range ou incomplet en quatre blocs humains: fait, preuve attendue,
  action humaine, limite.

Route future suggeree: `/audit360/reprises/{reprise_id}`.
Nom ecran: `Reprise prudente d'un constat`.
Contrat UX initial propose: `model.ux.audit360_constat_recovery_v1`;
consolidation finale: `model.ux.audit360_constat_reprise_v1`, pour rester
coherent avec le vocabulaire produit francais et eviter deux schemas.

Premier viewport recommande:

- bandeau `Brouillon interne - validation humaine requise`;
- phrase courte `Ce n'est pas un verdict. On transforme un constat en travail
  verifiable.`;
- bloc `Fait formule prudemment`, avec ce qui est constate et ce qui reste
  suppose;
- bloc `Preuve attendue`, avec type de preuve, periode, source attendue et
  validateur;
- bloc `Action humaine`, avec prochain geste, role responsable et echeance
  eventuelle;
- bloc `Limite`, avec ce que le constat ne permet pas de conclure et qui peut
  voir;
- actions: `Demander la preuve`, `Rattacher une piece`,
  `Creer un point a verifier`, `Soumettre au syndic`,
  `Mettre en attente avec motif`;
- timeline courte visible: `Signal -> Reformulation -> Preuve attendue ->
  Decision humaine -> Suivi`.

Risque principal: effet de verdict automatique si une piece recue est percue
comme une cloture. Mitigation: toujours afficher `impact propose, a valider`,
validateur humain, motif et reserve.

## Retour novice - CONV-2026-1656

Verdict: GO comprehension conditionnel, NO-GO dev immediat tant que l'ecran ou
blueprint ne montre pas explicitement:

```text
fait -> preuve attendue -> action humaine -> limite -> reserve -> diffusion
```

Message a comprendre en 30 secondes:

```text
Ce n'est pas un verdict. C'est une fiche pour reprendre un constat. On sait
quelque chose, il manque une preuve ou une validation, une personne doit decider
quoi faire, et il faut savoir qui peut voir le resultat.
```

Libelles acceptables:

- `Boite de reprise`;
- `Constat a reprendre`;
- `Fait constate`;
- `Ce que l'on sait`;
- `Ce qui manque`;
- `Preuve attendue`;
- `Preuve candidate`;
- `Preuve de quoi exactement ?`;
- `Action humaine a faire`;
- `Qui doit valider ?`;
- `Limite du constat`;
- `Reserve a garder`;
- `Diffusion a verifier`;
- `Conseil syndical uniquement`;
- `Impact propose, a valider`;
- `Valider avec reserve`;
- `Corriger le constat`;
- `Refuser le lien`;
- `Demander une piece`;
- `Rattacher une piece`.

Interdits au premier ecran: `Audit360` comme titre principal, verdict, score IA,
conforme/non conforme sans validation humaine, anomalie, aggravation, levee
automatique, `P1/P2`, `L4`, probatoire, controle, `Preuve validee` pour une
preuve candidate, source de verite, envoyer, publier, partager a tous sans
revue humaine, champs techniques `source_file`, `payload_json`, `raw`,
`restricted`, `private` ou `logs`.

Confusions a bloquer: fait + preuve ne signifie pas que CoproScope a tranche;
un bouton ne doit pas laisser croire qu'il envoie au syndic; une piece recue est
une preuve candidate; `Conseil syndical uniquement` ne signifie pas que le
partage a deja eu lieu.

## Retour front - CONV-2026-1657

Verdict: creer une fiche-atelier dediee pour un constat unique, sans item
principal `Audit360` en navigation au premier increment.

Cible future recommandee:

```text
Route: /audit360/reprises/{reprise_id}
Module route: audit360_reprise_route.py
Builder/view model: audit360_reprise_view.py
Template: templates/audit360_reprise.html
Read model public: model.ux.audit360_constat_reprise_v1
```

Placement UI:

- lien depuis `/actions` via une action source Audit360 ou `selected=ACT-AUD-*`;
- lien depuis `/pieces/{piece_id}` ou `/pieces?proof=missing` quand une preuve
  attendue est liee;
- lien depuis la future fiche `/audit360/points/{point_id}`;
- carte cockpit seulement si la reprise devient actionnable, pas navigation
  permanente.

Premier viewport recommande: `Reprise de constat`,
`Validation humaine requise`, phrase `Ce document peut aider, mais ne clot pas
le constat seul`, blocs `Ce que l'on sait`, `Ce qui manque`,
`Preuve attendue`, `Action humaine`, puis panneau `Ce document change quoi ?`
avec `Impact propose, a valider`, `Preuve de quoi ?`, `Limite`, `Motif`,
`Reserve`.

Risques front:

- enregistrer les routes `/audit360/reprises/...` avant le catch-all global;
- ne pas creer un fragment trop tardif trie apres le catch-all;
- eviter d'ajouter du vrai code dans `part_003.pyfrag`, deja proche du plafond;
- reutiliser les classes `cs-reprise-*` existantes si possible;
- liens locaux sans token dans les donnees, tokenises au rendu par les helpers
  existants, avec test anti double-token.

Tests futurs: `server/tests/test_ui_audit360_reprise_route.py`, avec token
403/200, route non capturee par catch-all, etat vide sur identifiant inconnu ou
path-like, liens tokenises, absence de fuite et absence de libelles de verdict.

## Retour back/viewmodel - CONV-2026-1658

Verdict: le contrat public futur doit etre
`model.ux.audit360_constat_reprise_v1`. Il affiche une reprise prudente d'un
constat unique, pas une decision.

Principes back:

- projection publique en allowlist stricte au-dessus de `points`, `actions`,
  `expected_pieces` et `object_links`;
- sources derivees possibles seulement si elles sont deja anonymisees;
- pas de `SELECT *`, pas de vue persistante, pas de fallback dashboard;
- donnees uniquement fictives, de test ou `examples/synthetic_copro`;
- priorites brutes `P1/P2` internes seulement, exposees en libelles novices.

Champs publics requis:

- `reprise`: identifiant opaque, titre, statut validation humaine, famille,
  priorite novice, diffusion, notice derivee non source de verite;
- `fact`: fait constate, resume, etat a verifier, pourquoi cela compte;
- `expected_proof`: preuve attendue, preuve de quoi, minimum attendu,
  validateur, statut candidate/manquante;
- `human_action`: obligatoire, actions autorisees bornees, motif requis,
  reserve requise si partiel, envoi automatique interdit, cloture automatique
  interdite;
- `limit_reserve_diffusion`: conclusion non automatique, reserve, revue
  diffusion obligatoire;
- `links`: actions, pieces attendues et sources derivees par identifiants
  opaques;
- `timeline`: cinq evenements maximum.

Champs interdits en JSON, HTML et export derive: `source_import_map`,
`source_file`, `source_row_id`, `source_sha256`, `import_run_id`,
`payload_json`, `event_path`, `event_hash`, `event_id`,
`source_event_ids_json`, `created_from_event_hash`, `updated_from_event_hash`,
`locator_json`, `message_draft`, `original_path`, `original_name`,
`source_path`, `current_blob_id`, chemins locaux, tokens, secrets, emails,
telephones, IBAN/RIB, OCR brut, logs, exports bruts, `raw`, `restricted`,
`private`, `file://` et tables alias vers identite reelle.

Tests futurs: `test_public_audit360_reprise_read_model.py`, couvrant allowlist
exacte, import fictif -> objets metier -> reprise publique, anti-fuite JSON/HTML,
source derivee opaque, liens action/piece publics sans token embarque,
validation humaine obligatoire, retour vide sur projection absente ou schema
incompatible, et absence de `SELECT *`, `MATCH`, FTS ou `CREATE VIEW`.

## Retour QA - CONV-2026-1659

Verdict: GO cadrage QA, mais NO-GO produit et NO-GO dev dans le worktree
courant.

Un owner code futur ne peut etre ouvert que dans un chantier dedie, sur donnees
fictives/test ou derivees anonymisees, pour une route
`/audit360/reprises/{reprise_id}` et un contrat public allowlist. Le nom
canonique retenu par consolidation est `model.ux.audit360_constat_reprise_v1`
afin d'eviter un doublon avec `model.ux.audit360_constat_recovery_v1`.

Panier QA futur depuis `server/`:

```powershell
$env:PYTHONPATH="src"
.\.venv\Scripts\python.exe -m unittest tests.test_audit360_import tests.test_vault tests.test_public_read_models tests.test_privacy tests.test_security_no_private_sync_leaks tests.test_ui_security_routes tests.test_ui_smoke_routes_expanded tests.test_code_line_limit -v
.\.venv\Scripts\python.exe -m unittest tests.test_ui_audit360_reprise_route -v
```

Panier depuis la racine:

```powershell
.\tools\check_code_line_limit.py
git diff --check
.\tools\agent-check.cmd -Ui
```

Test dedie futur: `server/tests/test_ui_audit360_reprise_route.py`, couvrant:

- 403 sans token HTML/API/export;
- 200 avec token;
- liens internes tokenises;
- absence de token dans le corps de reponse;
- route non capturee par catch-all;
- etat vide sur;
- smoke route.

Anti-fuite obligatoire sur HTML, JSON/API, CSV/JSON export eventuel: aucun
`C:\Users`, `/Users`, `/home`, `file://`, `raw`, `restricted`, `private`,
`logs`, OCR brut, nom brut, email, telephone, IBAN/RIB, secret, token,
`source_file`, `source_row_id`, `payload_json`, `event_path`, `source_sha256`
ou table alias -> identite.

Tests metier bloquants: la page doit afficher `Ce n'est pas un verdict`,
`Validation humaine requise`, `Preuve candidate`, `Impact propose, a valider`,
`Limite du constat`, `Diffusion a verifier`. Une preuve candidate ne doit
jamais passer le constat en `clos`, produire `source_of_truth=true`, ni masquer
le besoin de validateur humain, motif et reserve.

Captures futures requises sur instance fictive/test avec port reserve:
desktop, mobile et tablette. Les captures doivent prouver le premier viewport,
l'absence de chevauchement, la lisibilite des CTA, et la distinction fait /
preuve attendue / action humaine / limite / reserve / diffusion.

NO-GO immediat si instance privee, raw/OCR/logs/export brut/secret,
`RM-2026-0017`, `ORD-P0-990`, verdict automatique, cloture automatique par
preuve candidate, validation humaine absente, token casse, fuite
HTML/API/export, smoke rouge ou fichier suivi >600 lignes.

## Consolidation ORD-P0-011

Verdict equipe: `AGILE-DONE - equipe agile a fini son job`.

- A tester maintenant: rien en live; aucun serveur reserve.
- En dev maintenant: aucun dev. Le worktree principal reste sale et exclu.
- En enquete maintenant: tous les roles canoniques sont clotures.
- Commande prete: oui, comme commande future bornee, pas executee.
- Comparaison visuels enquete: la commande reprend les blueprints Audit360 du
  2026-05-24 et se distingue de la fiche `Point a verifier` ORD-P0-010.
- Agents idle a relancer: aucun sans nouveau diff ou decision d'owner code.
- Decision requise: Brice doit decider explicitement s'il veut ouvrir un owner
  code dedie pour cette commande. Sans cela, le heartbeat passe au prochain
  `ORD-*` actionnable.
- Prochain mouvement: prochain heartbeat = choisir le prochain `ORD-*` P0
  actionnable, sans rouvrir ce lot.
- Tests/preuves: retours designer/novice/front/back/QA integres;
  `git diff --check` documentaire; aucun test applicatif, serveur, instance
  privee ou export.

Commande future bornee:

```text
Roadmap/chantier:
RM-2026-0008 / RM-2026-0006 / nouveau CH owner code dedie a creer si Brice
valide.

Objectif:
Livrer une fiche-atelier token-safe `Reprise de constat`, sur donnees fictives,
de test ou derivees anonymisees uniquement.

UI cible:
Route dediee `/audit360/reprises/{reprise_id}` enregistree avant catch-all,
module `audit360_reprise_route.py`, builder `audit360_reprise_view.py`,
template `templates/audit360_reprise.html`.
Ne pas ajouter `Audit360` comme entree principale de navigation au premier
increment; lier depuis actions, pieces, cockpit ou future fiche point.

Read model:
`model.ux.audit360_constat_reprise_v1`, projection publique allowlist depuis
`points`, `actions`, `expected_pieces`, `object_links` et sources derivees deja
anonymisees si necessaire.

Premier viewport:
`Reprise de constat`, `Validation humaine requise`,
`Ce document peut aider, mais ne clot pas le constat seul`,
`Ce que l'on sait`, `Ce qui manque`, `Preuve attendue`, `Action humaine`,
`Ce document change quoi ?`, `Impact propose, a valider`,
`Limite du constat`, `Reserve a garder`, `Diffusion a verifier`.

Interactions:
CTA tokenises `Demander la preuve`, `Rattacher une piece`,
`Creer un point a verifier`, `Soumettre au syndic`,
`Mettre en attente avec motif`. Aucun envoi, export, partage ou cloture
automatique.

Garde-fous:
validation humaine obligatoire; motif requis; reserve requise si validation
partielle; timeline 5 evenements maximum; sorties derivees, jamais source de
verite; preuve candidate jamais cloturante.

Interdits:
instances privees, documents bruts, OCR/logs, exports bruts, secrets,
RM-2026-0017/ORD-P0-990, `source_file`, `source_row_id`, `source_sha256`,
`payload_json`, `event_path`, chemins locaux, `raw`, `restricted`, `private`,
`logs`, `P1/P2` visibles, score IA, verdict automatique, cloture automatique,
envoi ou partage automatique.

Tests:
`server/tests/test_ui_audit360_reprise_route.py`,
`test_public_audit360_reprise_read_model.py`, import fictif bout-en-bout,
anti-fuite JSON/HTML/export, token 403/200, etat vide, liens tokenises,
catch-all, line-limit, `git diff --check`, `agent-check -Ui`, captures
desktop/mobile/tablette.
```

## Journal

| Horodatage | Conversation | Evenement | Trace |
|---|---|---|---|
| 2026-05-25 02:14 +02:00 | `CONV-2026-1654` | `START_AGILE_AUDIT360_BOITE_REPRISE` | `ORD-P0-010` est `AGILE-DONE`; nouveau chantier P0 ouvert sur `ORD-P0-011` en lecture/cadrage uniquement, sans code ni serveur. |
| 2026-05-25 02:14 +02:00 | `CONV-2026-1655`..`CONV-2026-1659` | `AGENTS_LAUNCH_PARTIAL` | Designer Raman, novice Newton et front Mencius lances; back/viewmodel et QA reserves mais non lances faute de capacite de threads. Aucun code, serveur, instance privee, export brut, secret ou `RM-2026-0017`. |
| 2026-05-25 02:15 +02:00 | `CONV-2026-1656` | `NOVICE_RETURN_AUDIT360_BOITE_REPRISE` | Newton cloture: GO comprehension conditionnel, NO-GO dev immediat sans matrice visible fait/preuve/action/limite/reserve/diffusion; libelles novices et confusions a bloquer fournis. |
| 2026-05-25 02:16 +02:00 | `CONV-2026-1655` | `DESIGNER_RETURN_AUDIT360_BOITE_REPRISE` | Raman cloture: route future suggeree `/audit360/reprises/{reprise_id}`, ecran `Reprise prudente d'un constat`, contrat initial `model.ux.audit360_constat_recovery_v1` normalise ensuite en `model.ux.audit360_constat_reprise_v1`, premier viewport et risques de verdict automatique fournis. |
| 2026-05-25 02:16 +02:00 | `CONV-2026-1658` | `BACK_LAUNCHED_AUDIT360_BOITE_REPRISE` | Capacite liberee: James lance en lecture seule sur contrat public allowlist pour une reprise d'un constat unique. QA reste a lancer. |
| 2026-05-25 02:17 +02:00 | `CONV-2026-1659` | `QA_LAUNCHED_AUDIT360_BOITE_REPRISE` | Capacite liberee: Kant lance en lecture seule sur GO/NO-GO QA, panier futur, anti-fuite, token, captures et non-verdict automatique. |
| 2026-05-25 02:18 +02:00 | `CONV-2026-1657` | `FRONT_RETURN_AUDIT360_BOITE_REPRISE` | Mencius cloture: route future `/audit360/reprises/{reprise_id}`, modules/template dedies, pas d'entree nav principale, route avant catch-all, prudence line-limit et test `test_ui_audit360_reprise_route.py`. |
| 2026-05-25 02:18 +02:00 | `CONV-2026-1658` | `BACK_RETURN_AUDIT360_BOITE_REPRISE` | James cloture: contrat public `model.ux.audit360_constat_reprise_v1`, allowlist stricte, champs interdits et tests read-model futurs fournis. |
| 2026-05-25 02:21 +02:00 | `CONV-2026-1659` | `QA_RETURN_AUDIT360_BOITE_REPRISE` | Kant cloture: GO cadrage QA, NO-GO produit et NO-GO dev dans le worktree courant; panier futur, tests metier bloquants, anti-fuite et captures desktop/mobile/tablette fournis. |
| 2026-05-25 02:21 +02:00 | `CONV-2026-1654`..`CONV-2026-1659` | `AGILE_DONE_AUDIT360_BOITE_REPRISE` | Equipe cloturee sans dev: commande future `/audit360/reprises/{reprise_id}` et contrat `model.ux.audit360_constat_reprise_v1` prets pour owner code dedie si Brice valide; aucun code, serveur, instance privee, export brut, secret, push GitHub ni `RM-2026-0017`. |
