# Equipe agile - ORD-P0-036 Recette navigateur parcours

Date de lancement: 2026-05-25 04:07 +02:00.
Mode: recette/preflight produit, lecture seule, sans dev et sans serveur lance.

## BOT-START

```text
BOT-START - Coordinateur QA recette navigateur - 2026-05-25 04:07 +02:00
Roadmap: RM-2026-0006 / RM-2026-0003
Ordre: ORD-P0-036 / RECETTE-NAVIGATEUR-PARCOURS
Chantier: CH-20260525-040701-RM-2026-0006-recette-navigateur-parcours
Conversation: CONV-2026-1708
Role: Coordinateur QA recette navigateur
Mission: verifier si la recette navigateur bout-en-bout cockpit -> audit/comptes -> action -> piece/demande -> preuve -> diffusion est executable maintenant, puis produire un GO/NO-GO exploitable.
Ownership modifiable: docs/equipe_agile_2026-05-25_recette-navigateur-parcours.md, docs/presence_agents.md, trace append-only docs/roadmap_backlog_central.md et heartbeat relance-equipe-agile-gouvernail-autonome.
Fichiers a eviter: code applicatif, tests applicatifs, routes, templates, CSS, worktree principal sale, worktrees PRET_A_INTEGRER sans decision d'integration, instances privees reelles, documents bruts, OCR/logs, exports bruts, secrets, serveurs locaux non reserves, push GitHub, RM-2026-0017 / ORD-P0-990, reouverture des lots AGILE-DONE sans nouveau diff ou decision Brice.
Dernier point lu: AGENTS.md, protocoles equipe agile/orchestration/roadmap/presence, consignes interconversations, gouvernail, presence et mission ORD-P0-035 cloturee.
Tests/preuves attendus: presence ou absence d'un serveur live reserve, resultat test live, panier smoke/security/no-private/line-limit, decision sur captures desktop/mobile/tablette.
Risque de collision: aucun role vivant ORD-P0-036; ORD-P0-040 WorksOps est PRET_A_INTEGRER sans decision d'integration; ORD-P0-050 Coffre partage est PRET_A_INTEGRER/no-go dev immediat sans validation Brice; ORD-P0-900 bloque secret OAuth; ORD-P0-990 interdit.
Lease ownership: n/a, cloture en preflight.
Prochaine action: ne pas lancer de serveur non reserve; reprendre seulement si un terminal serveur visible, port, token et instance de recette sont fournis/reserves.
```

## Etat initial

- A tester maintenant: recette live attendue sur `http://127.0.0.1:8766` avec
  token local, mais aucun serveur reserve n'est disponible dans ce passage.
- En dev maintenant: aucun dev; aucun owner code ouvert.
- En enquete maintenant: verification de l'actionnabilite du parcours et des
  P0 suivants.
- Commande prete: oui pour une future recette live, pas executable sans serveur
  visible reserve.
- Comparaison visuels enquete: reportee; aucune capture navigateur ne peut etre
  produite sans serveur.
- Agents idle a relancer: aucun role navigateur n'est lance tant que le serveur
  n'est pas disponible.
- Decision requise: fournir ou reserver un serveur visible pour recette, ou
  valider explicitement une integration `PRET_A_INTEGRER`.
- Prochain mouvement: stationner ce lot et ne pas ouvrir les P0 suivants tant
  qu'ils restent `PRET_A_INTEGRER` sans decision.
- Tests/preuves: test live `test_ui_live_ux_contract`, panier smoke/security/
  no-private et line-limit.

## Roles

| Conversation | Role | Statut | Agent |
|---|---|---|---|
| `CONV-2026-1708` | Coordinateur QA recette navigateur | BLOQUE | local |

Les roles designer, novice, front, back/viewmodel et QA navigateur ne sont pas
ouverts pour eviter une equipe artificielle sans route live ni captures.

## Parcours cible futur

Scenario navigateur attendu quand un serveur est reserve:

1. Ouvrir le cockpit `/` et verifier que le premier viewport expose les sujets
   urgents, la preuve/source et la prochaine action.
2. Passer par comptes/audit: `/comptes`, `/ag-contentieux` ou l'equivalent
   Audit360 disponible, en restant sur libelles humains.
3. Ouvrir `/actions` puis une file pertinente: priorite, syndic ou decisions.
4. Ouvrir `/pieces?proof=missing` puis une fiche `/pieces/{piece_id}`.
5. Depuis la fiche, ouvrir `/demandes/relance` ou `/depot` en contexte preuve.
6. Verifier la prudence de diffusion sur `/confidentialite` et
   `/exports/passation`.
7. Capturer desktop, mobile et tablette, sans token ni donnee privee visible.

Commande de serveur future, a lancer seulement dans un terminal PowerShell
visible et reserve dans `presence_agents.md`:

```powershell
.\server\.venv\Scripts\python.exe -m coproscope.cli ui open-test --instance-root C:\Users\brice\CoproScope\instances\beauvallon_test --year 2025 --host 127.0.0.1 --port 8766 --token beauvallon-test-local
```

## Preuves

- `server\.venv\Scripts\python.exe -m unittest server.tests.test_ui_live_ux_contract -v`
  donne `OK (skipped=1)` car le serveur live est indisponible sur
  `http://127.0.0.1:8766` avec erreur de connexion refusee.
- `server\.venv\Scripts\python.exe -m unittest server.tests.test_ui_smoke_routes_expanded server.tests.test_ui_security_routes server.tests.test_security_no_private_sync_leaks -v`
  donne 17 tests OK.
- `server\.venv\Scripts\python.exe tools\check_code_line_limit.py` donne OK.

## Resultat

BLOQUE - recette navigateur non executable dans ce passage.

NO-GO produit: aucune capture desktop/mobile/tablette, aucun clic navigateur et
aucune preuve d'absence de chevauchement texte ne sont produits.

Le lot `ORD-P0-036` est stationne. Ne pas le relancer sans serveur visible
reserve, instance de test, token de test et protocole de capture. Les P0
suivants visibles dans la file ne sont pas actionnables automatiquement:

- `ORD-P0-040` / WorksOps est `PRET_A_INTEGRER` sans decision d'integration;
- `ORD-P0-050` / Coffre partage est `PRET_A_INTEGRER` et no-go dev immediat
  sans validation Brice;
- `ORD-P0-900` attend un secret OAuth hors Git;
- `ORD-P0-990` reste interdit.

## Journal

| Horodatage | Conversation | Evenement | Trace |
|---|---|---|---|
| 2026-05-25 04:07 +02:00 | `CONV-2026-1708` | `START_RECETTE_NAVIGATEUR_PARCOURS` | `ORD-P0-035` est clos; ouverture d'un preflight recette `ORD-P0-036` sans code ni serveur non reserve. |
| 2026-05-25 04:08 +02:00 | `CONV-2026-1708` | `LIVE_RECETTE_UNAVAILABLE` | Test live `test_ui_live_ux_contract` saute car `127.0.0.1:8766` refuse la connexion; aucune capture navigateur possible. |
| 2026-05-25 04:09 +02:00 | `CONV-2026-1708` | `BLOQUE_RECETTE_NAVIGATEUR_SANS_LIVE` | Panier smoke/security/no-private = 17 OK et line-limit OK; NO-GO produit faute de serveur/captures/clics. P0 suivants non actionnables sans decision explicite. |
