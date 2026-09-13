# Equipe agile - Audit360 ORD-P0-010 points a verifier

Date de lancement: 2026-05-25 01:56 +02:00.
Mode: equipe agile de cadrage produit, lecture seule, sans dev.

## BOT-START

```text
BOT-START - Coordinateur-scribe agile - 2026-05-25 01:56 +02:00
Roadmap: RM-2026-0008
Ordre: ORD-P0-010 / AUDIT360-POINTS-A-VERIFIER
Chantier: CH-20260525-015603-RM-2026-0008-audit360-points-a-verifier
Conversation: CONV-2026-1648
Role: Coordinateur-scribe agile
Mission: convertir les recherches Audit360 cloturees en commande produit bornee pour une fiche `Point a verifier`, sur donnees fictives ou instance de test uniquement, avec validation humaine obligatoire.
Ownership modifiable: docs/equipe_agile_2026-05-25_audit360-points-a-verifier.md, docs/presence_agents.md, trace append-only docs/roadmap_backlog_central.md et heartbeat `relance-equipe-agile-gouvernail-autonome`.
Fichiers a eviter: code applicatif, tests applicatifs, templates, CSS, worktree principal sale, instances privees, documents bruts, OCR/logs, exports bruts, secrets, push GitHub, serveurs non reserves, RM-2026-0017 / ORD-P0-990.
Dernier point lu: AGENTS.md, protocoles equipe agile/orchestration/roadmap/presence, consignes interconversations, gouvernail, presence, mission ORD-P0-002 stationnee, docs/audit360.md, recherches UX/UI Audit360 anomalies et approfondissement.
Tests/preuves attendus: synthese multi-roles, GO/NO-GO novice, cible UI/code a confirmer en lecture seule, contrat fictif minimal, panier privacy/security/no-private/line-limit/smoke, decision explicite avant tout owner code.
Risque de collision: worktree principal sale; aucun patch code autorise dans ce chantier. Les anciens runs UX/UI Audit360 sont CLOTURE/UXUI-DONE et ne doivent pas etre rouverts sans nouveau diff ou demande explicite.
Lease ownership: jusqu'au 2026-05-25 03:56 +02:00.
Prochaine action: attendre les retours designer, novice et front; lancer back/viewmodel et QA si capacite de threads disponible, sinon reprise coordinateur minimale au prochain heartbeat.
```

## Etat initial

- A tester maintenant: aucune UI live. Il faut d'abord identifier la surface
  produit cible et les preuves attendues sur donnees fictives.
- En dev maintenant: aucun dev; pas de worktree code ouvert.
- En enquete maintenant: designer, novice et front lecture seule lances; back
  viewmodel et QA reserves faute de capacite de threads.
- Commande prete: pas encore. La direction produit est connue: fiche
  `Point a verifier`, pas tableau Audit360, avec `Impact propose` puis
  `Validation humaine requise`.
- Comparaison visuels enquete: utiliser les blueprints Audit360 du 2026-05-24
  comme source de decision; ne pas regenerer d'image tant que la commande
  produit n'exige pas un nouvel ecart visuel.
- Agents idle a relancer: `CONV-2026-1652` back/viewmodel et `CONV-2026-1653`
  QA/privacy sont reserves mais non lances.
- Decision requise: GO/NO-GO sur ouverture ulterieure d'un owner code unique en
  worktree dedie pour une fiche `Point a verifier`.
- Prochain mouvement: consolider les retours et produire une commande bornee ou
  un NO-GO dev.
- Tests/preuves: aucun test applicatif attendu avant code; `git diff --check`
  documentaire, puis panier futur security/privacy/no-private/line-limit/smoke.

## Roles

| Conversation | Role | Statut | Agent |
|---|---|---|---|
| `CONV-2026-1648` | Coordinateur-scribe agile | EN_COURS | local |
| `CONV-2026-1649` | Designer service / facilitateur | CLOTURE | Gauss `019e5c6c-cf97-7640-a4ca-5ffdcf969547` |
| `CONV-2026-1650` | Utilisateur novice / membre CS | CLOTURE | Locke `019e5c6c-d0f9-7182-8cdd-5e45f8140188` |
| `CONV-2026-1651` | Dev front lecture seule | CLOTURE | Mill `019e5c6c-d1b1-7292-a8d9-79b20cfccd82` |
| `CONV-2026-1652` | Dev back / viewmodel lecture seule | CLOTURE | Halley `019e5c71-5d8c-7ec3-ae75-d8b5c559ef16` |
| `CONV-2026-1653` | QA privacy / regression | CLOTURE | Noether `019e5c71-5dfd-7601-8381-f517cc07963b` |

## Contraintes produit

- Premier ecran: `Point a verifier`, `Validation humaine requise`,
  `Ce document change quoi ?`, `Preuve de quoi ?`, prochaine action.
- Interdits UX: score IA, verdict automatique, tableau dense comme entree,
  `P1/P2` non traduit, `aggravation` en premier niveau, `levee` sans
  validateur, motif et reserve.
- Toute preuve reste candidate tant que l'humain n'a pas valide le perimetre,
  la source, la limite et la reserve eventuelle.
- Le flux cible est `fait -> preuve -> regle -> action`, avec historique
  avant/apres.
- Les sorties diffusable restent generiques: aucun nom reel, chemin local,
  montant prive, OCR brut, log, token ou marqueur `raw/restricted/private`.

## Retour designer - CONV-2026-1649

Verdict: GO cadrage, NO-GO dev immediat tant que la matrice preuve minimale /
validateur / reserve n'est pas representee et que le futur chantier ne travaille
pas sur donnees fictives ou instance de test.

Premier viewport recommande:

- titre `Point a verifier`, pas `Audit360`;
- bandeau `Validation humaine requise`;
- phrase novice: `Ce document peut aider, mais ne clot pas le point seul.`;
- blocs `Ce que l'on sait`, `Ce qui manque`, `Preuve attendue`,
  `Prochaine action`;
- panneau `Ce document change quoi ?` avec impact propose, jamais decision;
- timeline courte: `Signal detecte -> Preuve attendue -> Document recu ->
  Decision humaine -> Suivi`;
- badges discrets `Donnees fictives / test` et `Diffusion a verifier`.

Commande future bornee proposee, non executee par ce role:

```text
Creer une fiche web token-safe `Point a verifier` Audit360 sur donnees
fictives/test uniquement, route future dediee par exemple
`/audit360/points-a-verifier`, contrat `model.ux.audit360_point_to_verify_v1`,
validation humaine obligatoire, timeline 5 evenements maximum, tests route
token-safe, anti-fuite, etat vide, impact propose, validation obligatoire et
line-limit.
```

## Retour novice - CONV-2026-1650

Verdict: GO comprehension si le premier ecran dit clairement que ce n'est pas un
verdict automatique. NO-GO dev immediat sans matrice `famille de point -> preuve
minimale -> validateur -> reserve`, blueprint/ecran cible et validation novice.

Message a comprendre en 30 secondes:

```text
Ce n'est pas un verdict, c'est un point a verifier. On sait quelque chose, il
manque une preuve ou une validation, un document peut aider, mais une personne
doit decider quoi faire.
```

Libelles acceptables:

- `Point a verifier`;
- `Validation humaine requise`;
- `Ce document change quoi ?`;
- `Document qui peut aider`;
- `Preuve candidate recue`;
- `Preuve de quoi exactement ?`;
- `Reste a verifier`;
- `Impact propose, a valider`;
- `Peut etre regle, a valider`;
- `En partie regle`;
- `Documents qui ne disent pas la meme chose`;
- `A soumettre au syndic`;
- `Valider avec reserve`, `Corriger l'impact`, `Refuser le lien`,
  `Demander une piece`.

Termes a bloquer au premier ecran: `Audit360`, `anomalie`, `P1/P2`, `L4`,
`controle`, `probatoire`, `aggravation`, `levee` seule, `score IA`,
`verdict IA`, `levee automatique`, tableau dense.

## Retour front - CONV-2026-1651

Verdict: Audit360 n'a pas encore de route/template UI dediee. GO cadrage pour
une route dediee future; NO-GO pour porter la fiche dans une route action
existante ou dans le hub principal.

Surfaces proches existantes:

- `/actions`: meilleur precedent UI pour une fiche avec pourquoi, preuve/source,
  prochaine action et prudence diffusion.
- `/pieces` et `/pieces/{piece_id}`: precedent pour preuve attendue, candidate
  ou finale.
- `/ag-contentieux`: utile pour les points AG/contentieux, mais trop large pour
  une fiche unique.
- `/exports/passation/blocages/{blocker_id}`: bon modele de detail securise
  avec identifiants masques, raisons de non-export, preuves requises et
  `source_of_truth=false`.

Cible future recommandee:

```text
Route: /audit360/points/{point_id}
Module: audit360_point_view.py
Template: templates/audit360_point.html
Read model public: model.ux.audit360_point_to_verify_v1
```

Structure premier ecran:

- `Point a verifier`;
- `Fait constate`;
- `Preuve attendue`;
- `Regle ou source de controle`;
- `Action humaine`;
- badges priorite, validation et diffusion;
- CTA sobres: `Demander la preuve`, `Rattacher une piece`,
  `Ouvrir l'action liee`, `Verifier diffusion`;
- mentions `Validation humaine obligatoire` et `Non source de verite`.

Risques front:

- `server/src/coproscope/web/_app_fragments/part_003.pyfrag` est deja proche du
  plafond; ne pas y ajouter l'implementation reelle.
- Les catch-all de `part_004.pyfrag` imposent d'enregistrer `/audit360/...`
  avant les routes generiques.
- La navigation principale est dense; ne pas ajouter `Audit360` en entree
  principale au premier increment. Preferer un lien depuis actions, pieces ou
  cockpit.
- Eviter les libelles techniques `source_import_map`, `source_file`,
  `source_row_id`, `payload_json`, `event_path`, `vault`, `raw`,
  `restricted`, `private`, `logs`, `source_sha256`.

Tests futurs proposes:

- test dedie `server/tests/test_ui_audit360_point_route.py`;
- 403 sans token, 200 avec token;
- rendu d'un point fictif avec `Point a verifier`, `Fait constate`,
  `Preuve attendue`, `Action humaine`, `Validation humaine obligatoire`;
- aucun leak `C:\Users`, `raw`, `restricted`, `private`, `logs`, `source_file`,
  `payload_json`, `source_sha256`;
- identifiant prive ou inconnu masque;
- liens tokenises vers action/piece/demande;
- route non capturee par catch-all;
- etat vide sur absence de read model;
- absence des labels interdits: `Envoyer automatiquement`, `source de verite`,
  `P1 Prioritaire`, `DocOps feedback`, `A_MASQUER`, `BLOQUE`.

## Retour QA - CONV-2026-1653

Verdict: panier QA pret pour un owner code futur, mais aucun GO produit sans
route livree, tests verts et preuves navigateur desktop/mobile. Le repo courant
reste sale; tout dev doit partir en worktree dedie.

Panier minimum futur depuis `server/`:

```powershell
.\.venv\Scripts\python.exe -m unittest tests.test_audit360_import tests.test_vault tests.test_privacy tests.test_security_no_private_sync_leaks tests.test_ui_security_routes tests.test_ui_smoke_routes_expanded tests.test_code_line_limit -v
```

Panier depuis la racine:

```powershell
.\tools\check_code_line_limit.py
git diff --check
.\tools\agent-check.cmd -Ui
```

Test dedie a creer si la route est developpee:
`server/tests/test_ui_audit360_point_route.py`, couvrant 403 sans token, 200
avec token, route non capturee par catch-all, etat vide, liens tokenises,
absence de fuite, libelles novice et absence de verdict automatique.

Attendus privacy/no-private:

- aucun chemin `C:\Users`, `/Users`, `/home`, `file://`;
- aucune racine `raw`, `restricted`, `private`, `logs`;
- aucun OCR brut, nom de fichier brut, email, telephone, IBAN/RIB, token,
  secret ou table de correspondance;
- pas de `source_file`, `source_row_id`, `payload_json`, `event_path`,
  `source_sha256`;
- identifiant prive ou inconnu masque ou rendu 404/etat vide sans echo;
- sorties derivees seulement, jamais `source_of_truth=true`.

Preuve navigateur attendue sur instance fictive/test avec port reserve:

- sans token, `/audit360/points/{id}` renvoie 403 sans contenu metier;
- avec token, desktop et mobile affichent dans le premier viewport
  `Point a verifier`, `Validation humaine requise`,
  `Ce document peut aider, mais ne clot pas le point seul`,
  `Ce que l'on sait`, `Ce qui manque`, `Preuve attendue`,
  `Ce document change quoi ?`, `Impact propose, a valider` et prochaine action;
- les CTA `Demander la preuve`, `Rattacher une piece`,
  `Ouvrir l'action liee`, `Verifier diffusion` gardent le token et
  n'envoient/exportent rien automatiquement;
- capture desktop + mobile comparee au blueprint Audit360 du 2026-05-24;
- timeline limitee a 5 evenements, sans tableau dense, chevauchement ou texte
  illisible.

NO-GO immediat si donnees reelles, instance privee, `RM-2026-0017`,
`ORD-P0-990`, verdict automatique, preuve candidate qui clot seule, matrice
preuve minimale/validateur/reserve absente, echec token/no-private, fichier code
au-dessus de 600 lignes ou absence de preuve navigateur pour un GO produit.

Statut maximal sans preuve navigateur: `PRET_A_INTEGRER` technique, pas GO
produit.

## Retour back/viewmodel - CONV-2026-1652

Verdict: le socle d'import Audit360 existe deja et alimente les bons objets
metier. Le manque principal est une projection publique dediee, construite par
allowlist au-dessus de `points`, `actions`, `expected_pieces` et `object_links`,
sans exposer les tables et champs d'origine.

Faits backend:

- import Audit360 existant via `coproscope.modules.audit360.import_audit360_file`;
- reconstruction existante via `reconstruction.import_audit360_rows`;
- objets produits: `points`, `actions`, `expected_pieces`, `object_links`,
  `object_event_sources`, `source_import_map`;
- identifiants deterministes internes: `POINT-AUD-*`, `ACT-AUD-*`,
  `PCE-AUD-*`;
- read models publics existants pour actions/pieces, mais pas pour une fiche
  publique `point`;
- aucune route/template `/audit360/...` ni `model.ux.audit360_point_to_verify_v1`
  n'existe actuellement.

Contrat minimal fictif futur:

```json
{
  "schema": "model.ux.audit360_point_to_verify_v1",
  "version": "2026-05-25.fictive-v1",
  "data_scope": "FICTIF_TEST_ONLY",
  "point": {
    "id": "POINT-AUD-FICTIF-001",
    "title": "Point a verifier",
    "status_label": "Validation humaine requise",
    "priority_label": "A traiter",
    "diffusion_label": "Conseil syndical uniquement"
  },
  "fact": {
    "label": "Fait constate",
    "summary": "Une piece attendue n'est pas encore confirmee.",
    "state": "candidat"
  },
  "expected_proof": {
    "label": "Preuve attendue",
    "summary": "Document ou justification a produire avant conclusion.",
    "request_label": "Demander la preuve"
  },
  "rule": {
    "label": "Regle ou source de controle",
    "summary": "Controle a verifier par un humain avant tout impact."
  },
  "impact": {
    "question": "Ce document change quoi ?",
    "answer": "Il peut aider a confirmer le point, sans le clore seul."
  },
  "human_validation": {
    "required": true,
    "allowed_decisions": [
      "demander_piece",
      "rattacher_piece",
      "valider_avec_reserve",
      "corriger_impact",
      "refuser_lien"
    ],
    "motive_required": true,
    "reserve_required_if_not_full": true
  },
  "next_action": {
    "label": "Demander ou rattacher une preuve",
    "href": "/actions?selected=ACT-AUD-FICTIF-001"
  }
}
```

Contraintes back:

- projection en allowlist stricte uniquement, sans `SELECT *`;
- interdits UX: `source_import_map`, `source_file`, `source_row_id`,
  `source_sha256`, `payload_json`, `event_path`, chemins locaux, `raw`,
  `restricted`, `private`, `logs`, OCR, exports, tokens et emails;
- priorites brutes `P1/P2` internes seulement, exposees en libelles humains;
- preuve candidate jusqu'a validation humaine du perimetre, de la source, de la
  limite et de la reserve.

Tests futurs proposes:

- test read model `public_audit360_point_to_verify_v1` sur base reconstruite
  fictive;
- import fictif bout-en-bout -> objets metier -> modele UX point;
- injection de chemins prives, token, email, `raw/restricted/private/logs`,
  `source_sha256` et verification d'absence JSON/HTML;
- validation humaine: `required=true`, decisions autorisees bornees, motif
  requis, reserve requise si validation partielle;
- route future `/audit360/points/{point_id}`: 403 sans token, 200 avec token,
  inconnu = modele vide sur, pas de fuite;
- absence de `P1/P2`, score IA, verdict automatique ou `levee` autonome.

## Consolidation ORD-P0-010

Verdict equipe: `AGILE-DONE - equipe agile a fini son job`.

- A tester maintenant: rien en live; aucun serveur reserve.
- En dev maintenant: aucun dev. Le worktree principal reste sale et exclu.
- En enquete maintenant: tous les roles canoniques sont clotures.
- Commande prete: oui, comme commande future bornee, pas executee.
- Comparaison visuels enquete: la commande reprend les blueprints Audit360 du
  2026-05-24: fiche unique, validation humaine, impact propose et timeline
  probatoire courte.
- Agents idle a relancer: aucun sans nouveau diff ou decision d'owner code.
- Decision requise: Brice doit decider explicitement s'il veut ouvrir un owner
  code dedie pour cette commande. Sans cela, le heartbeat passe au prochain
  `ORD-*` actionnable.
- Prochain mouvement: prochain heartbeat = choisir le prochain `ORD-*` P0
  actionnable, sans rouvrir ce lot.
- Tests/preuves: retours designer/novice/front/back/QA integres; `git diff
  --check` documentaire; aucun test applicatif, serveur, instance privee ou
  export.

Commande future bornee:

```text
Roadmap/chantier:
RM-2026-0008 / nouveau CH owner code dedie a creer si Brice valide.

Objectif:
Livrer une fiche web token-safe `Point a verifier` Audit360, sur donnees
fictives/test uniquement.

UI cible:
Route dediee `/audit360/points/{point_id}` enregistree avant catch-all,
module `audit360_point_view.py`, template `templates/audit360_point.html`.
Ne pas ajouter `Audit360` comme entree principale de navigation au premier
increment; lier depuis actions, pieces ou cockpit.

Read model:
`model.ux.audit360_point_to_verify_v1`, projection publique allowlist depuis
`points`, `actions`, `expected_pieces` et `object_links`.

Premier viewport:
`Point a verifier`, `Validation humaine requise`,
`Ce document peut aider, mais ne clot pas le point seul`, `Fait constate`,
`Preuve attendue`, `Regle ou source de controle`, `Action humaine`,
`Ce document change quoi ?`, `Impact propose, a valider`.

Interactions:
CTA tokenises `Demander la preuve`, `Rattacher une piece`,
`Ouvrir l'action liee`, `Verifier diffusion`. Aucun envoi, export ou cloture
automatique.

Garde-fous:
donnees fictives/test; validation humaine obligatoire; motif requis; reserve
requise si validation partielle; timeline 5 evenements maximum; sorties
derivees, jamais source de verite.

Interdits:
instances privees, documents bruts, OCR/logs, exports bruts, secrets,
RM-2026-0017/ORD-P0-990, `source_file`, `source_row_id`, `source_sha256`,
`payload_json`, `event_path`, chemins locaux, `raw`, `restricted`, `private`,
`logs`, `P1/P2` visibles, score IA, verdict automatique, `levee` autonome.

Tests:
`server/tests/test_ui_audit360_point_route.py`,
read model `public_audit360_point_to_verify_v1`, import fictif bout-en-bout,
anti-fuite JSON/HTML, token 403/200, etat vide, liens tokenises, catch-all,
line-limit, `git diff --check`, `agent-check -Ui`, captures desktop/mobile.
```

## Sources de decision

- `docs/audit360.md`
- `docs/recherche_ux_ui_2026-05-24_audit360-anomalies.md`
- `docs/recherche_ux_ui_2026-05-24_audit360-anomalies_approfondissement.md`
- `docs/commande_cycle9_module_audit_boite_reprise_probatoire.md`
- `docs/roadmap_backlog_central.md`
- `docs/presence_agents.md`

## Point heartbeat - 2026-05-25 02:02 +02:00

- A tester maintenant: aucune recette live; pas de serveur reserve.
- En dev maintenant: aucun dev; le worktree principal reste sale et hors
  perimetre code.
- En enquete maintenant: front Mill, back/viewmodel Halley et QA Noether en
  lecture seule. Designer Gauss et novice Locke sont clotures.
- Commande prete: non. Direction produit connue, mais il manque encore la
  cartographie front, le contrat read model et le panier QA final.
- Comparaison visuels enquete: reference maintenue sur les blueprints Audit360
  du 2026-05-24, surtout `nouveau document -> impact propose -> validation
  humaine -> timeline probatoire`.
- Agents idle a relancer: aucun role reserve non lance; attendre les trois
  retours en cours.
- Decision requise: aucune decision Brice immediate. Dev futur seulement si les
  retours convergent vers une commande bornee en worktree dedie sur donnees
  fictives/test.
- Prochain mouvement: recuperer les retours front/back/QA, puis consolider
  GO/NO-GO et commande future ou NO-GO dev.
- Tests/preuves: lecture `git status`, lecture code read-only et
  `git diff --check` documentaire; aucun test applicatif lance.

## Point heartbeat - 2026-05-25 02:08 +02:00

- A tester maintenant: aucune recette live; QA a fourni le panier futur sans
  lancer de test.
- En dev maintenant: aucun dev et aucun worktree code ouvert.
- En enquete maintenant: back/viewmodel Halley reste en cours; designer,
  novice, front et QA sont clotures.
- Commande prete: presque, mais il manque le contrat back/read-model final
  avant de transformer en commande owner code.
- Comparaison visuels enquete: reference maintenue sur les blueprints Audit360
  du 2026-05-24 et sur le premier viewport valide par designer/novice.
- Agents idle a relancer: aucun; attendre Halley ou faire reprise coordinateur
  minimale au prochain passage.
- Decision requise: aucune decision Brice immediate. Pas de dev sans retour
  back ou reprise coordinateur suffisante.
- Prochain mouvement: recuperer le retour back/viewmodel, consolider la
  commande bornee ou fermer en NO-GO dev immediat.
- Tests/preuves: `git diff --check` documentaire cible; aucun serveur, aucun
  test applicatif, aucune instance privee.

## Journal

| Horodatage | Conversation | Evenement | Trace |
|---|---|---|---|
| 2026-05-25 01:56 +02:00 | `CONV-2026-1648` | `START_AGILE_AUDIT360_POINTS_A_VERIFIER` | `ORD-P0-002` est stationne sans nouveau token/base; nouveau chantier P0 ouvert sur `ORD-P0-010` en lecture/cadrage uniquement. |
| 2026-05-25 01:56 +02:00 | `CONV-2026-1649`..`CONV-2026-1653` | `AGENTS_LAUNCH_PARTIAL` | Designer Gauss, novice Locke et front Mill lances; back/viewmodel et QA reserves mais non lances faute de capacite de threads. Aucun code, serveur ou instance privee. |
| 2026-05-25 01:57 +02:00 | `CONV-2026-1649` | `DESIGNER_RETURN_AUDIT360_POINTS` | Gauss cloture: blueprint premier viewport `Point a verifier`, validation humaine, panneau `Ce document change quoi ?`, timeline 5 et commande future route dediee `/audit360/points-a-verifier`; NO-GO si tableau/score/verdict ou donnees non fictives. |
| 2026-05-25 01:57 +02:00 | `CONV-2026-1650` | `NOVICE_RETURN_AUDIT360_POINTS` | Locke cloture: comprehension 30 secondes validee seulement si l'ecran dit que ce n'est pas un verdict; NO-GO dev sans matrice preuve minimale / validateur / reserve, blueprint cible et validation novice. |
| 2026-05-25 02:02 +02:00 | `CONV-2026-1652`, `CONV-2026-1653` | `BACK_QA_LAUNCHED_AUDIT360_POINTS` | Capacite liberee: Halley back/viewmodel et Noether QA lances en lecture seule. Front Mill reste en cours. Aucun code, serveur, instance privee, export brut, secret ou `RM-2026-0017`. |
| 2026-05-25 02:03 +02:00 | `CONV-2026-1651` | `FRONT_RETURN_AUDIT360_POINTS` | Mill cloture: aucune route/template Audit360 dediee; route future conseillee `/audit360/points/{point_id}` avec module/template dedies, read model public, enregistrement avant catch-all et tests token/anti-fuite/etat vide. |
| 2026-05-25 02:08 +02:00 | `CONV-2026-1653` | `QA_RETURN_AUDIT360_POINTS` | Noether cloture: panier QA futur fourni, tests non lances; GO technique seulement avec tests verts, nouveau test route, line-limit, diff-check, captures desktop/mobile, anti-fuite HTML/API/export et verdict novice. Sans preuve navigateur: `PRET_A_INTEGRER` technique maximum. |
| 2026-05-25 02:09 +02:00 | `CONV-2026-1652` | `BACK_RETURN_AUDIT360_POINTS` | Halley cloture: socle import/reconstruction Audit360 existe; manque principal = projection publique allowlist `model.ux.audit360_point_to_verify_v1` et route/template dedies, sans exposer champs source internes. |
| 2026-05-25 02:09 +02:00 | `CONV-2026-1648`..`CONV-2026-1653` | `AGILE_DONE_AUDIT360_POINTS_A_VERIFIER` | Equipe cloturee sans dev: commande future `/audit360/points/{point_id}` prete pour owner code dedie si Brice valide; aucun code, serveur, instance privee, export brut, secret, push GitHub ni `RM-2026-0017`. |
