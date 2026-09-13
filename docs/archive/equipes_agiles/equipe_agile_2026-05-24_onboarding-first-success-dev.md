# Equipe agile - Onboarding premier succes dev

Date de lancement: 2026-05-24 22:04 +02:00.
Roadmap: `RM-2026-0009`.
Chantier: `CH-20260524-220400-RM-2026-0009-onboarding-first-success-dev`.
Conversation coordination: `CONV-2026-1592`.
Mode: owner code unique, sans serveur live.
Statut: integre localement.

## BOT-START

BOT-START - Owner code onboarding premier succes - 2026-05-24 22:04 +02:00.

Mission: livrer un premier bloc cockpit `Premier succes conseille` sur `/`,
avec une action recommandee vers une demande locale, quatre intentions et les
garde-fous `rien n'est envoye automatiquement`, preuve/source, prochaine action
et prudence diffusion.

Ownership modifiable:

- `server/src/coproscope/web/templates/overview.html`;
- `server/tests/test_ui_onboarding_first_success.py`;
- ce document;
- `docs/presence_agents.md`;
- `docs/roadmap_backlog_central.md`.

Fichiers a eviter: fragments de routes, `test_ui_demo.py` proche du plafond
600 lignes, `viewmodel.py`, templates hors cockpit, serveurs locaux, instances
privees, exports bruts, secrets et `RM-2026-0017`.

Preuves attendues: test dedie onboarding, demandes, document intake, anti-fuite
et garde-fou 600 lignes.

## Journal

| Heure | Acteur | Evenement | Detail |
|---|---|---|---|
| 2026-05-24 22:04 +02:00 | `CONV-2026-1592` | `BOT-START` | Owner code onboarding ouvert; aucun serveur, port, instance privee, export brut, secret ou `RM-2026-0017`. |
| 2026-05-24 22:05 +02:00 | `CONV-2026-1592` | `PATCH_UI` | Bloc `Premier succes conseille` ajoute au cockpit `/`: demande locale recommandee, quatre intentions, microcopy preuve/source, prochaine action, prudence diffusion et trace passation. |
| 2026-05-24 22:07 +02:00 | `CONV-2026-1592` | `TESTS_CIBLES_OK` | Test dedie onboarding + demandes + document intake + anti-fuite: 24 tests OK; `tools\check_code_line_limit.py` OK. |
| 2026-05-24 22:09 +02:00 | `CONV-2026-1592` | `REGRESSION_OK` | Regression UI demo + onboarding + demandes + document intake + anti-fuite + line-limit: 37 tests OK; `git diff --check` OK avec avertissements CRLF preexistants seulement. |

## Livraison

Implementation:

- le cockpit `/` affiche un bloc `Premier succes conseille` juste apres
  l'introduction;
- l'action recommandee ouvre `/demandes#nouvelle-demande` avec un href
  token-safe: le token reste avant l'ancre;
- quatre intentions sont visibles: demande locale, priorite, document,
  passation;
- la microcopy rappelle `Rien n'est envoye automatiquement`, `Preuve ou
  source`, `prochaine action`, `Prudence diffusion` et `Trace gardee pour la
  passation`.

Fichiers modifies:

- `server/src/coproscope/web/templates/overview.html`;
- `server/tests/test_ui_onboarding_first_success.py`.

Fichiers volontairement evites: fragments de routes, `test_ui_demo.py`,
`viewmodel.py`, serveurs locaux, instances privees, exports bruts, secrets et
`RM-2026-0017`.

Preuves:

- `server.tests.test_ui_onboarding_first_success`: OK;
- `server.tests.test_ui_requests_route`: OK;
- `server.tests.test_ui_document_intake_route`: OK;
- `server.tests.test_security_no_private_sync_leaks`: OK;
- `server.tests.test_ui_demo`: OK;
- `server.tests.test_code_line_limit`: OK;
- suite cible 37 tests: OK;
- `tools\check_code_line_limit.py`: OK;
- `git diff --check`: OK, avertissements CRLF preexistants seulement.

## BOT-END

BOT-END - 2026-05-24 22:09 +02:00.

`onboarding_first_success_v1` est integre localement et verifie. Aucun serveur,
port, instance privee, export brut, secret ou `RM-2026-0017` n'a ete touche.
