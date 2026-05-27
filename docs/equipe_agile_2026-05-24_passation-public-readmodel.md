# Equipe agile - Passation public read model

Date de lancement: 2026-05-24 21:11 +02:00.
Roadmap: `RM-2026-0016`.
Chantier: `CH-20260524-211130-RM-2026-0016-passation-public-readmodel`.
Conversation coordination: `CONV-2026-1567`.
Mode: cadrage agile lecture seule avant owner code unique.
Statut: pret a integrer.

## BOT-START

BOT-START - Coordinateur-scribe agile passation public read model -
2026-05-24 21:11 +02:00.

Mission: debloquer la suite `RM-2026-0016` sans serveur, sans instance privee
et sans reprise de `RM-2026-0017`: cadrer le lot `public_passation_v1` pour que
`/exports/passation`, `/exports/passation.json` et `/exports/passation.txt`
puissent eviter le dashboard complet quand une projection publique existe.

UI reelle cible: `/exports/passation` et exports derives associes.

Fichiers autorises pour ce cadrage:

- `docs/equipe_agile_2026-05-24_passation-public-readmodel.md`;
- `docs/presence_agents.md`;
- ligne gouvernail `RM-2026-0016`.

Fichiers a eviter: code applicatif, tests, serveurs, instances privees,
documents bruts, derives OCR, exports bruts, secrets, `RM-2026-0017` et serveur
`CONV-2026-1525`.

## Roles

| Role | Conversation | Statut | Sortie attendue |
|---|---|---|---|
| Coordinateur-scribe | `CONV-2026-1567` | `PRET_A_INTEGRER` | Declaration, arbitrage et consolidation livres. |
| Cartographie technique passation | `CONV-2026-1568` / Carson `019e5b68-91b3-7693-9478-1e8fcdbc6cbb` | `CLOTURE` | Retour agent integre: owner futur, fichiers a toucher/eviter, ordre routes, tests minimaux et no-go. |
| QA perf / privacy | `CONV-2026-1569` / Aristotle `019e5b68-b409-7dc1-83bb-90497764382d` | `CLOTURE` | Retour agent integre: gates token, anti-fuite, perf, scope event, read model allowliste et panier tests. |
| Utilisateur novice / passation | `CONV-2026-1570` / Huygens `019e5b68-dad8-7be1-a76b-152545000e14` | `CLOTURE` | Retour agent integre: GO novice conditionnel, vocabulaire a garder/refuser et conditions avant dev. |

## Point Initial

A produire: commande dev precise pour un owner unique `public_passation_v1`.

En dev: rien, volontairement.

En test: tests existants passation/security a selectionner.

Blocages: le worktree principal est sale; toute implementation devra passer par
un worktree dedie propre et un owner code unique.

Agents vivants/idle: trois roles lecture a lancer si capacite disponible.

Decisions ouvertes: confirmer si l'objectif prioritaire est performance
`/exports/passation` par projection publique, ou seulement cadrage avant
integration des chantiers deja `PRET_A_INTEGRER`.

Prochain mouvement: lancer les roles lecture, consolider une commande dev
minimale, puis stopper sans patch si les collisions restent trop fortes.

## Consolidation Technique

Constat: les routes passation sont fonctionnelles et securisees, mais restent
branchees au modele dashboard complet.

Points lus:

- `server/src/coproscope/web/_app_fragments/part_004.pyfrag`: les routes
  `/exports/passation`, `/exports/passation.json`, `/exports/passation.txt` et
  `/exports/passation/blocages/{blocker_id}` appellent `_dashboard_model()`.
  Le test actuel verrouille seulement une construction dashboard par requete,
  pas zero construction.
- `server/src/coproscope/web/_app_fragments/part_001.pyfrag` et
  `part_002.pyfrag`: `_passation_export_document`, `_scoped_passation_preview`
  et `_assert_passation_export_route_safe` sont les points d'integration
  actuels.
- `server/src/coproscope/vault/public_actions_read_model.py` et
  `server/src/coproscope/vault/public_read_models.py`: pattern existant pour
  lire une projection publique allowlistee sans `SELECT *`, sans `CREATE VIEW`,
  sans fuite de chemins, tokens ou champs bruts.

Commande dev future:

1. Creer `server/src/coproscope/vault/public_passation_read_model.py` avec un
   contrat `public_passation_v1` versionne, lu depuis la base de reconstruction
   publique quand `public_reconstruction_db_path(instance)` est disponible.
2. Produire un document export compatible avec
   `render_passation_derived_json()` et `render_passation_derived_markdown()`,
   plus un modele preview compatible `passation_export.html`, sans passer par
   `build_dashboard_model`.
3. Brancher les routes passation pour tenter le read model public avant le
   fallback actuel. Si le coffre public est configure mais la projection est
   absente ou incompatible, rendre un etat vide public et prudent plutot que
   reconstruire le dashboard complet.
4. Conserver `source_of_truth=false`, watermark export derive, token obligatoire
   et scope prudent. `scope=event` ou `selected` prive doit rester borne a un
   extrait vide ou masque, jamais elargi au pack global.

Tables source candidates: `projection_meta`, `actions`, `expected_pieces`,
`requests`, `points`, `proofs`, `object_links`, `exports`. Les colonnes doivent
etre listees explicitement et passer par les memes filtres anti-fuite que les
read models publics existants.

Fichiers owner futur:

- `server/src/coproscope/vault/public_passation_read_model.py`;
- `server/src/coproscope/web/_app_fragments/part_001.pyfrag` ou
  `part_002.pyfrag` pour le helper de document/preview;
- `server/src/coproscope/web/_app_fragments/part_004.pyfrag` pour les routes;
- `server/tests/test_public_read_models.py`;
- `server/tests/test_ui_passation_export_route.py`;
- `server/tests/test_security_no_private_sync_leaks.py`.

Fichiers a eviter: `server/src/coproscope/vault/public_read_models.py` sauf
import strictement minimal, templates, CSS, `viewmodel.py`, donnees d'instance,
exports bruts, serveur local et toute reprise `RM-2026-0017`.

## QA / Perf / Novice

Preuves lancees pendant le cadrage sur l'instance synthetique:

- `server.tests.test_ui_passation_export_route` = 20 tests OK;
- `server.tests.test_passation_exports` = 3 tests OK;
- `server.tests.test_security_no_private_sync_leaks` = 8 tests OK;
- `tools\check_code_line_limit.py` OK.

Mesure TestClient synthetique actuelle:

- `/exports/passation`: 0.559s froid puis 0.064s et 0.055s;
- `/exports/passation.json`: 0.069s, 0.076s, 0.082s;
- `/exports/passation.txt`: 0.064s, 0.082s, 0.062s.

Cette mesure ne leve pas le NO-GO perf observe sur l'instance plus lourde; elle
sert seulement de baseline synthetique. Le critere du futur lot est structurel:
quand une projection publique passation existe, les trois routes doivent rester
200 sans appeler `build_dashboard_model`.

Verdict novice: `GO_CONDITIONNEL` sur l'objectif "apercu de passation avant
export", car le vocabulaire existe deja. `NO-GO dev direct` dans le worktree
principal sale. L'etat vide doit dire quoi ajouter ou verifier, pas exposer une
erreur technique.

Retours agents finaux: Carson confirme l'owner code unique
`public_passation_v1` en worktree dedie propre, avec nouveau module
`public_passation_read_model.py`, branchement minimal dans `part_001.pyfrag` et
`part_004.pyfrag`, et test dedie `test_public_passation_read_model.py`.
Aristotle confirme les gates token, anti-fuite, `scope=event`, perf structurelle
sans fallback dashboard et read model allowliste. Huygens confirme le
`GO_CONDITIONNEL` novice si l'UI garde ses reperes et masque les mots
techniques `public`, `read model` et `projection`.

## Decision de cloture

Commande prete: oui, pour un owner code unique dans un worktree dedie.

En dev maintenant: rien dans le worktree principal.

Blocages: collisions probables sur fragments web et tests; imposer un worktree
dedie et un comptage 600 lignes avant integration.

Prochain mouvement: ouvrir un worktree `codex/passation-public-readmodel` si le
gouvernail priorise encore `RM-2026-0016`, sinon passer au prochain P0 non
bloque.

BOT-END - Coordinateur-scribe agile passation public read model -
2026-05-24 21:17 +02:00

AGILE-DONE - equipe agile a fini son job

## Journal

| Heure | Acteur | Evenement | Detail |
|---|---|---|---|
| 2026-05-24 21:11 +02:00 | `CONV-2026-1567` | `BOT-START` | Cycle autonome: ouverture d'un cadrage `RM-2026-0016` sur `public_passation_v1`, sans code, serveur, instance privee, secret, export brut ni reprise de `RM-2026-0017`. |
| 2026-05-24 21:12 +02:00 | `CONV-2026-1568`..`CONV-2026-1570` | `AGENTS_LAUNCHED` | Carson, Aristotle et Huygens lances en lecture seule sur cartographie technique, QA perf/privacy et lecture novice; aucun code, serveur, instance privee, secret ou export brut. |
| 2026-05-24 21:16 +02:00 | `CONV-2026-1567` | `TESTS_BASELINE_OK` | Tests synthetiques: passation route 20 OK, passation exports 3 OK, security no private sync leaks 8 OK, line-limit OK; aucune instance privee ni serveur. |
| 2026-05-24 21:17 +02:00 | `CONV-2026-1567`..`CONV-2026-1570` | `AGILE_DONE_PASSATION_PUBLIC_READMODEL` | Commande dev `public_passation_v1` consolidee apres premiere synthese locale; prochain geste = owner code unique en worktree dedie. |
| 2026-05-24 21:16 +02:00 | `CONV-2026-1568`..`CONV-2026-1570` | `WAIT_TIMEOUT_INITIAL` | Attente courte initiale sans retour final; roles maintenus brievement, puis retours reconcilies ligne suivante sans duplication. |
| 2026-05-24 21:23 +02:00 | `CONV-2026-1568`..`CONV-2026-1570` | `AGENT_RETURNS_RECONCILED` | Retours finaux Carson, Aristotle et Huygens recus puis reconcilies dans la commande deja cloturee: cartographie, QA et GO novice conditionnel confirment le cadrage; aucun code, serveur, instance privee ni export brut. |
