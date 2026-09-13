# Equipe agile - DocOps tri feedback dev

Date de lancement: 2026-05-24 20:45 +02:00.
Roadmap: `RM-2026-0003` / `RM-2026-0029`.
Chantier: `CH-20260524-204500-RM-2026-0029-docops-feedback-dev`.
Conversation coordination: `CONV-2026-1556`.
Mode: owner code unique dans worktree dedie.
Statut: pret a integrer.

## BOT-START

BOT-START - Coordinateur-scribe agile DocOps feedback - 2026-05-24 20:45 +02:00

Mission: implementer le prototype `/documents/tri-feedback` dans un worktree
dedie propre, sans toucher au worktree principal sale.

Ownership code dedie:
`C:\Users\brice\CoproScope\dev\worktrees_existing\coproscope-docops-feedback`
sur branche `codex/docops-feedback-tri-20260524`.

Sources de commande:

- `docs/equipe_agile_2026-05-24_ajout-docs-tri-feedback.md`;
- `docs/commandes/commande_interface_tri_docops_feedback_2026-05-24.md`;
- `docs/relecture_ia_docops_feedback_2026-05-24.md`;
- `docs/presence_agents.md`;
- `docs/roadmap_backlog_central.md`;
- `AGENTS.md`.

Fichiers autorises dans le worktree dedie:

- `server/src/coproscope/web/docops_feedback_route.py`;
- `server/src/coproscope/web/docops_feedback_view.py`;
- `server/src/coproscope/web/templates/docops_feedback.html`;
- `server/src/coproscope/web/static/styles_part_13.css`;
- `server/tests/test_ui_docops_feedback_route.py`;
- hook minimal de route/import si necessaire dans les fragments web existants.

Fichiers a eviter: worktree principal code, `document_intake_*`, `depot.py`,
instances privees, secrets, exports bruts, serveurs locaux, `RM-2026-0017`.

## Roles

| Role | Conversation | Statut | Sortie attendue |
|---|---|---|---|
| Coordinateur-scribe | `CONV-2026-1556` | `PRET_A_INTEGRER` | Declaration, integration et verification livrees. |
| Owner code DocOps feedback | `CONV-2026-1557` / Anscombe `019e5b4f-82bf-7eb2-8130-50dcb7a8502c` | `CLOTURE` | Base route/vue/tests produite; exports et validation finale completes par coordinateur apres shutdown. |
| QA privacy / novice | `CONV-2026-1558` / Ramanujan `019e5b4f-b2b8-76f1-85cd-b6819589602b` | `CLOTURE` | Checklist QA integree: token, route shadow, anti-fuite, restrictions, exports et tests cibles. |
| QA reprise privacy / novice | `CONV-2026-1566` / Helmholtz `019e5b61-5593-7750-a8fb-1f03f0f42d08` | `CLOTURE` | NO-GO initial corrige: fallback memoire isole par instance et CSV marque comme export derive. |

## Point Initial

A produire: route `/documents/tri-feedback`, correction des propositions DocOps,
enregistrement local des feedbacks et export derive sans fuite.

En dev: owner code a lancer dans le worktree dedie.

En test: cible principale `server/tests/test_ui_docops_feedback_route.py`.

Blocages: aucun blocage de worktree; integration future a faire prudemment car
le worktree principal reste sale.

Prochain mouvement: integrer/revoir le worktree dedie
`C:\Users\brice\CoproScope\dev\worktrees_existing\coproscope-docops-feedback`
vers le worktree principal seulement apres revue explicite; ne pas coder dans
le worktree principal sale.

## Retour QA Privacy / Novice

Constat worktree: le worktree dedie
`C:\Users\brice\CoproScope\dev\worktrees_existing\coproscope-docops-feedback`
est propre sur `codex/docops-feedback-tri-20260524`, mais ne contient pas encore
`docops_feedback_route.py`, `docops_feedback_view.py`,
`templates/docops_feedback.html`, `styles_part_13.css` ni
`test_ui_docops_feedback_route.py`.

NO-GO avant integration tant que `GET/POST /documents/tri-feedback` et les
exports derives CSV/JSON n'existent pas avec garde token 403 sans token.

Risques a verrouiller:

- declarer `/documents/tri-feedback` avant `/documents/{doc_id}` pour eviter le
  route shadow;
- interdire chemins locaux, `file://`, `raw`, `restricted`, `logs`, `private`,
  noms prives, OCR brut, secrets et tables de biffage dans HTML, erreurs, CSV
  et JSON;
- exiger des libelles novice: `Corriger les propositions DocOps`,
  `Enregistrer les corrections`, `Exporter le registre local`;
- persister un registre derive `registers/registre_feedback_docops.csv` avec
  `doc_id`, `sha256`, avant/apres, justification, reviewer, date, source et
  statut;
- refuser cote serveur les valeurs invalides, les restrictions sans
  justification et `A masquer avant partage` sans pages/plages;
- exporter seulement des projections derivees, tokenisees, sans `original_path`,
  `file_name`, `text_path`, contenu brut ni mapping.

Tests cibles attendus: `server/tests/test_ui_docops_feedback_route.py`,
securite routes, intake regression, no private leaks et garde-fou 600 lignes.

## Livraison Integree

Worktree livre:
`C:\Users\brice\CoproScope\dev\worktrees_existing\coproscope-docops-feedback`
sur branche `codex/docops-feedback-tri-20260524`.

Fichiers modifies dans le worktree dedie:

- `server/src/coproscope/web/docops_feedback_route.py`;
- `server/src/coproscope/web/docops_feedback_view.py`;
- `server/src/coproscope/web/templates/docops_feedback.html`;
- `server/src/coproscope/web/_app_fragments/part_003.pyfrag`;
- `server/src/coproscope/web/_app_fragments/part_004.pyfrag`;
- `server/src/coproscope/web/static/styles.css`;
- `server/src/coproscope/web/static/styles_part_13.css`;
- `server/tests/test_ui_docops_feedback_route.py`.

Comportement livre: `GET/POST /documents/tri-feedback` tokenise, declare avant
`/documents/{doc_id}`, jeu synthetique allowliste sans chemins ni noms prives,
registre derive `registers/registre_feedback_docops.csv`, validation serveur
des valeurs, justification obligatoire pour restriction, pages/plages
obligatoires pour `A masquer avant partage`, exports tokenises
`/exports/docops-feedback-tri.csv` et `/exports/docops-feedback-tri.json`.

Preuves: `git diff --check` OK; tests depuis le worktree dedie avec
`PYTHONPATH` sur `server/src` et le venv du repo principal:
`test_ui_docops_feedback_route.py` = 6 tests OK; panier voisin
`test_ui_document_intake*.py`, `test_ui_security_routes.py`,
`test_security_no_private_sync_leaks.py`, `test_code_line_limit.py` =
21 tests OK. Garde-fou `tools\check_code_line_limit.py` OK. Comptage fichiers
apres verification: `docops_feedback_route.py` 141 lignes,
`docops_feedback_view.py` 69 lignes, `docops_feedback.html` 79 lignes,
`styles.css` 15 lignes, `styles_part_13.css` 24 lignes,
`test_ui_docops_feedback_route.py` 144 lignes, `part_003.pyfrag` 476 lignes,
`part_004.pyfrag` 286 lignes.

Limites: pas de serveur local lance, pas de navigateur live, pas d'instance
privee, pas d'export brut. Integration dans le worktree principal a faire dans
un passage separe, car le principal reste sale.

## Decision de cloture

Commande prete: oui, comme branche/worktree dedie a integrer.

En dev maintenant: fini dans le worktree dedie; ne pas dupliquer l'owner code.

En test maintenant: cible unitaire OK; recette navigateur et regression plus
large a faire lors de l'integration principale.

## Retour QA Reprise

Verdict: `GO_INTEGRATION_PRUDENTE` depuis le worktree dedie, sans integration
directe dans le worktree principal sale.

Points verrouilles: token requis sur page et exports, route declaree avant
`/documents/{doc_id}`, restrictions refusees sans justification, pages/plages
requises pour `A masquer avant partage`, exports CSV/JSON derives et absence
des marqueurs interdits dans HTML, CSV et JSON.

Preuves reprises: `test_ui_docops_feedback_route.py` 6 OK,
`test_ui_document_intake*.py` 8 OK, `test_ui_security_routes.py` 4 OK,
`test_security_no_private_sync_leaks.py` 8 OK, `test_code_line_limit.py` 1 OK,
`tools\check_code_line_limit.py` OK, `git diff --check` OK.

Correctif apres QA reprise: fallback memoire indexe par instance, cle memoire
hachee, CSV marque par `source_of_truth`, `dataset_kind` et `watermark`, test
explicite d'isolement inter-instances ajoute. Panier final: 28 tests OK.

Prochain mouvement: revue/integration du worktree dedie ou passage au prochain
P0 gouvernail si Brice laisse l'automatisation continuer.

## Verification Integration 21:38

Micro-chantier: `CONV-2026-1578` /
`CH-20260524-213700-RM-2026-0029-docops-feedback-integration-check`.

Verdict: `PRET_A_INTEGRER`, sans patch dans le worktree principal.

Preuves rejouees depuis le worktree dedie
`C:\Users\brice\CoproScope\dev\worktrees_existing\coproscope-docops-feedback`:

- panier `tests.test_ui_docops_feedback_route`,
  `tests.test_ui_document_intake`, `tests.test_ui_document_intake_route`,
  `tests.test_ui_security_routes`, `tests.test_security_no_private_sync_leaks`,
  `tests.test_code_line_limit`: 28 tests OK;
- `tools\check_code_line_limit.py`: OK;
- `git diff --check`: OK.

Etat du worktree dedie: changements attendus uniquement dans
`part_003.pyfrag`, `part_004.pyfrag`, `styles.css` et nouveaux fichiers
`docops_feedback_route.py`, `docops_feedback_view.py`,
`templates/docops_feedback.html`, `styles_part_13.css`,
`test_ui_docops_feedback_route.py`.

Comptage fichiers du lot: `docops_feedback_route.py` 192 lignes,
`docops_feedback_view.py` 77 lignes, `docops_feedback.html` 81 lignes,
`styles_part_13.css` 28 lignes, `test_ui_docops_feedback_route.py` 201 lignes.

Limite: pas d'integration dans le worktree principal, pas de serveur, pas de
navigateur, pas d'instance privee. L'integration devra etre faite par owner
unique, en preservant les changements concurrents du worktree principal.

## Correctif Accents 21:41

Micro-chantier: `CONV-2026-1579` /
`CH-20260524-213900-RM-2026-0029-docops-feedback-accents`.

Verdict: `PRET_A_INTEGRER`, toujours dans le worktree dedie.

Objet: accepter les accents francais dans les champs humains surs
`reviewer`, `justification` et `redaction_scope`, sans relacher les garde-fous
anti-fuite sur chemins locaux, marqueurs `raw/restricted/logs/private`,
`file://`, secrets ou racines utilisateur.

Preuves rejouees depuis le worktree dedie:

- `test_ui_docops_feedback_route`: 8 tests OK, dont
  `test_tri_feedback_human_fields_accept_accents_without_private_paths`;
- panier complet DocOps/intake/security/line-limit: 29 tests OK;
- `tools\check_code_line_limit.py`: OK;
- `git diff --check`: OK.

Limite: pas d'integration main, pas de serveur, pas de navigateur, pas
d'instance privee. Le prochain geste reste une integration par owner unique qui
preserve les changements concurrents du worktree principal.

BOT-END - Coordinateur-scribe agile DocOps feedback - 2026-05-24 21:03 +02:00

AGILE-DONE - equipe agile a fini son job

## Journal

| Heure | Acteur | Evenement | Detail |
|---|---|---|---|
| 2026-05-24 20:45 +02:00 | `CONV-2026-1556` | `BOT-START` | Cycle autonome Brice: ouverture du dev separe DocOps feedback dans le worktree propre `codex/docops-feedback-tri-20260524`; aucun serveur, instance privee, secret, export brut, code du worktree principal ni reprise de `RM-2026-0017`. |
| 2026-05-24 20:46 +02:00 | `CONV-2026-1557`, `CONV-2026-1558` | `AGENTS_LAUNCHED` | Anscombe owner code et Ramanujan QA lances; Anscombe modifie seulement le worktree dedie, Ramanujan reste en lecture seule. Aucun serveur, instance privee, secret, export brut ni reprise de `RM-2026-0017`. |
| 2026-05-24 20:53 +02:00 | `CONV-2026-1558` | `QA_RETURN` | Ramanujan cloture en lecture seule: worktree propre mais pas encore de livraison DocOps feedback; `NO-GO` integration avant route, registre derive, exports tokenises et tests cibles. |
| 2026-05-24 21:03 +02:00 | `CONV-2026-1557` | `OWNER_SHUTDOWN_REVIEWED` | Anscombe s'est arrete sans message final, avec un patch present dans le worktree dedie; route/vue/template/test relus par le coordinateur. |
| 2026-05-24 21:03 +02:00 | `CONV-2026-1556` | `COORDINATOR_COMPLETED_EXPORTS` | Exports CSV/JSON tokenises, liens UI, champ `redaction_scope` et validation `A masquer avant partage` completes dans le perimetre dedie. |
| 2026-05-24 21:03 +02:00 | `CONV-2026-1556` | `TESTS_OK` | `git diff --check` OK; `tests.test_ui_docops_feedback_route` = 6 OK; panier voisin = 21 OK; aucun fichier code suivi du lot au-dessus de 600 lignes. |
| 2026-05-24 21:07 +02:00 | `CONV-2026-1556` | `REGRESSION_OK` | Panier depuis le worktree dedie: `test_ui_docops_feedback_route` = 6 OK; `test_ui_document_intake_route`, `test_ui_security_routes`, `test_security_no_private_sync_leaks`, `test_code_line_limit` = 16 OK; garde-fou 600 lignes OK; `git diff --check` OK. |
| 2026-05-24 21:08 +02:00 | `CONV-2026-1566` | `QA_RELAUNCH_FINAL_DIFF` | Helmholtz lance en lecture seule sur le diff final: token, route shadow, restrictions, exports derives, anti-fuite HTML/CSV/JSON et panier regression; aucun fichier modifie, serveur, instance privee ou export brut. |
| 2026-05-24 21:03 +02:00 | `CONV-2026-1556`..`CONV-2026-1558` | `AGILE_DONE_DOCOPS_FEEDBACK_DEV` | BOT-END: prototype `/documents/tri-feedback` pret a integrer depuis le worktree dedie; aucun serveur, instance privee, secret, export brut ni code du worktree principal. |
| 2026-05-24 21:10 +02:00 | `CONV-2026-1566` | `QA_REPRISE_NO_GO` | Helmholtz signale deux blocages: fallback memoire global pouvant melanger deux instances sans registre documents, et CSV sans marqueur explicite de source derivee. Aucun fichier modifie par QA. |
| 2026-05-24 21:15 +02:00 | `CONV-2026-1556` | `QA_BLOCKERS_FIXED` | Correctif coordinateur dans le worktree dedie: memoire fallback isolee par instance avec cle hachee, CSV avec `source_of_truth`, `dataset_kind`, `watermark`, test d'isolement inter-instances. Panier final 28 tests OK, garde-fou 600 lignes OK, `git diff --check` OK. |
| 2026-05-24 21:38 +02:00 | `CONV-2026-1578` | `INTEGRATION_CHECK_OK` | Verification rejouee dans le worktree dedie: 28 tests OK, `tools\\check_code_line_limit.py` OK, `git diff --check` OK; integration main non tentee car worktree principal sale. |
| 2026-05-24 21:41 +02:00 | `CONV-2026-1579` | `ACCENTS_SAFE_FIELDS_OK` | Correctif accents francais dans champs humains surs verifie dans le worktree dedie: test accents OK, panier complet 29 tests OK, `tools\\check_code_line_limit.py` OK, `git diff --check` OK; aucun serveur, instance privee ni integration main. |
