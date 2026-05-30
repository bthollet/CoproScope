# Equipe agile - Pont ajout documents vers tri feedback

Date de lancement: 2026-05-24 21:59 +02:00.
Roadmap: `RM-2026-0003`.
Chantier: `CH-20260524-215900-RM-2026-0003-ajout-docs-tri-bridge-dev`.
Conversation coordination: `CONV-2026-1591`.
Mode: owner code unique dans le worktree principal local, car le prototype
DocOps feedback est integre localement mais non encore committe.
Statut: integre localement.

## BOT-START

BOT-START - Owner code pont ajout-docs tri-feedback - 2026-05-24 21:59 +02:00.

Mission: implementer `ajout_docs_tri_bridge_v1`, un pont volontaire depuis
`/documents/ajouter` vers `/documents/tri-feedback`, sans nouvelle route,
sans nouvelle persistance et sans serveur live.

Ownership modifiable:

- `server/src/coproscope/web/templates/document_intake.html`;
- `server/tests/test_ui_document_intake.py`;
- `server/tests/test_ui_document_intake_route.py`;
- ce document;
- `docs/presence_agents.md`;
- `docs/roadmap_backlog_central.md`.

Fichiers a eviter: fragments de routes, `document_intake_view.py` proche du
plafond 600 lignes, `viewmodel.py`, `depot.py`, passation/read models publics,
instances privees, exports bruts, secrets, serveurs locaux et `RM-2026-0017`.

Preuves attendues: tests intake et DocOps feedback, routes securite,
anti-fuite, garde-fou 600 lignes, `git diff --check`.

## Journal

| Heure | Acteur | Evenement | Detail |
|---|---|---|---|
| 2026-05-24 21:59 +02:00 | `CONV-2026-1591` | `BOT-START` | Pont UI volontaire ouvert; aucun serveur, port, instance privee, secret, export brut ou `RM-2026-0017`. |
| 2026-05-24 22:00 +02:00 | `CONV-2026-1591` | `PATCH_UI` | Bloc conditionnel ajoute dans `/documents/ajouter`: `Corriger une file de documents`, CTA `Ouvrir le tri de lot`, sortie `Continuer document par document`, microcopy privacy. |
| 2026-05-24 22:01 +02:00 | `CONV-2026-1591` | `TESTS_CIBLES_OK` | `test_ui_document_intake`, `test_ui_document_intake_route`, `test_ui_docops_feedback_route`: 20 tests OK. |
| 2026-05-24 22:02 +02:00 | `CONV-2026-1591` | `REGRESSION_OK` | Suite cible 33 tests OK; `tools\check_code_line_limit.py` OK; `git diff --check` OK. |

## Livraison

Implementation:

- `/documents/ajouter` affiche un pont `Tri de lot` seulement quand il y a des
  documents a qualifier;
- le bouton principal ouvre `/documents/tri-feedback` avec le token existant;
- le bouton secondaire ramene a la liste `Documents a ajouter`;
- la microcopy rappelle les regles locales: fichier local, confirmation
  humaine, motif `Reserve CS`, pages/plages pour `A masquer`, pas de diffusion
  pour `A decider plus tard`.

Fichiers modifies:

- `server/src/coproscope/web/templates/document_intake.html`;
- `server/tests/test_ui_document_intake.py`;
- `server/tests/test_ui_document_intake_route.py`.

Fichiers volontairement evites: routes, `document_intake_view.py`, `depot.py`,
`viewmodel.py`, instances privees, exports bruts, serveurs locaux et
`RM-2026-0017`.

Preuves:

- `server.tests.test_ui_document_intake`: OK;
- `server.tests.test_ui_document_intake_route`: OK;
- `server.tests.test_ui_docops_feedback_route`: OK;
- suite cible 33 tests: OK;
- `tools\check_code_line_limit.py`: OK;
- `git diff --check`: OK.

## BOT-END

BOT-END - 2026-05-24 22:02 +02:00.

Pont `ajout_docs_tri_bridge_v1` integre localement et verifie. Aucun serveur,
port, instance privee, secret, export brut ou `RM-2026-0017` n'a ete touche.
