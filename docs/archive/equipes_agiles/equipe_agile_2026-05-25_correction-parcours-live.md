# Equipe agile - correction parcours live

Date: 2026-05-25.
Roadmap: `RM-2026-0006` / `RM-2026-0003`.
Ordre: `ORD-P0-036` / `RECETTE-NAVIGATEUR-PARCOURS`.
Chantier: `CH-20260525-153000-RM-2026-0006-correction-parcours-live`.
Conversation coordinatrice: `CONV-2026-1771`.

## BOT-START - coordinateur-scribe - 2026-05-25 15:35 +02:00

Mission: ouvrir la reprise corrective bornee du NO-GO live `8788` apres
arbitrage Brice "lance une equipe agile".

Ownership modifiable coordinateur:

- `docs/equipe_agile_2026-05-25_correction-parcours-live.md`;
- `docs/equipe_agile_2026-05-25_recette-parcours-live.md` en append-only;
- `docs/presence_agents.md`;
- `docs/roadmap_backlog_central.md`;
- heartbeat `relance-equipe-agile-gouvernail-autonome`.

Fichiers evites:

- instances privees reelles, documents bruts, OCR/logs, exports bruts,
  secrets;
- serveurs non reserves, scans/kills de processus, push GitHub;
- `RM-2026-0017`, `ORD-P0-990`;
- code produit hors ownership de l'owner code unique.

Dernier point lu:

- `docs/equipe_agile_2026-05-25_recette-parcours-live.md` a 15:31;
- watchdog a 15:28: `EN_ATTENTE_USER` sur `CONV-2026-1756`;
- superviseur a 15:28: heartbeat ACTIVE 5 minutes, doublon actif absent.

Tests/preuves attendus:

- `python -m unittest server.tests.test_ui_live_ux_contract -v`;
- tests cibles routes/actions/pieces/documents touches;
- token live `200/403` conserve sur `8788`;
- absence de fuite `raw`, `restricted`, chemin local, logs, secret;
- `tools/check_code_line_limit.py` si fichier code touche;
- `git diff --check` sur fichiers touches.

Lease ownership: 2026-05-25 17:35 +02:00.

## Commande Dev Bornee

Objectif utilisateur: un membre de conseil syndical doit ouvrir le parcours
P0 et comprendre immediatement quoi faire pour rattacher une piece, demander
une preuve, preparer une relance non envoyee et ajouter un document, sans
confondre brouillon, preuve candidate et diffusion.

UI cible reelle:

- `/actions?priority=P1`;
- `/pieces?proof=missing`;
- `/pieces/<id>` depuis une piece manquante reelle du modele;
- `/documents/ajouter`;
- premier viewport desktop/mobile/tablette du parcours live `8788`.

Correction in-scope:

- afficher `Rattacher une piece` dans la file actions P1;
- afficher `Creer demandes syndic` dans la file pieces manquantes;
- corriger le lien/id de detail piece pour ne pas pointer vers un identifiant
  synthetique introuvable;
- afficher `Brouillon a copier, non envoye` dans la relance/contextualisation
  piece;
- remonter `Ajout de document` et le contenu utile dans le premier viewport
  de `/documents/ajouter`.

Hors scope sauf note de risque:

- refonte globale de navigation ou CSS;
- optimisation large `/api/model`;
- reconstruction d'instance ou donnees reelles;
- envoi automatique de demande ou de relance;
- modification de `server/src/coproscope/web/_app_fragments/part_003.pyfrag`
  sans extraction, car le fichier est au plafond.

## Roles Ouverts

| Conversation | Role | Agent | Statut | Ownership |
|---|---|---|---|---|
| `CONV-2026-1771` | Coordinateur-scribe | coordinateur local | EN_COURS | Registres, heartbeat, consolidation, integration/revue |
| `CONV-2026-1768` | Designer service / facilitateur | Dirac `019e5f55-459c-7812-a980-86b3ee30c1de` | CLOTURE | Lecture seule, GO designer correction bornee, aucun fichier modifie |
| `CONV-2026-1769` | Utilisateur novice / membre CS | Ampere `019e5f55-46df-7812-b713-5c038aef4bf1` | CLOTURE | GO correction bornee; NO-GO produit live actuel |
| `CONV-2026-1770` | Owner code unique front/back/viewmodel | Anscombe `019e5f55-475a-7443-9cfe-fd50edab13c3` | CLOTURE | Correctif borne livre sur actions, pieces, detail piece, ajout document et exemples UX |
| `CONV-2026-1772` | QA live / privacy locale + checklist expert metier | coordinateur local, faute de thread disponible | BLOQUE | Tests locaux OK; contrat live a reprendre apres rechargement du serveur reserve `8788` |

## Point de Coordination

- A tester maintenant: contrat live rouge et routes ciblees du NO-GO.
- En dev maintenant: owner unique Anscombe, apres verification de sa ligne
  `CONV-2026-1770`.
- En enquete maintenant: Dirac et Ampere qualifient la commande, pas de nouveau
  blueprint lourd sauf ecart bloquant.
- Commande prete: oui, bornee aux libelles/contenu/id piece/document-intake.
- Comparaison visuels enquete: verifier premier viewport, CTA, statuts,
  preuve attendue, brouillon non envoye et absence de diffusion trompeuse.
- Agents idle a relancer: back/perf, QA distante et testeur expert metier
  distant non lances faute de thread; s'appuyer sur Carver/Lovelace/Hooke
  precedents et QA/coordinateur local pour la checklist metier canonique.
- Decision requise: aucune nouvelle decision Brice avant retour owner, sauf si
  le correctif exige une refonte ou une optimisation hors scope.
- Prochain mouvement: relancer Anscombe apres trace presence, puis attendre les
  retours Dirac/Ampere/Anscombe.
- Preuves: superviseur OK, watchdog `EN_ATTENTE_USER` leve par relance Brice,
  serveur reserve `8788` conserve.

## Journal

| Horodatage | Conversation | Evenement | Trace |
|---|---|---|---|
| 2026-05-25 15:35 +02:00 | `CONV-2026-1768`..`CONV-2026-1772` | `START_AGILE_CORRECTION_PARCOURS_LIVE` | Demande Brice: lancer une equipe agile. Ouverture de la reprise corrective bornee du NO-GO live `8788`; designer Dirac, novice Ampere et owner code Anscombe lances; QA locale faute de thread disponible; aucun serveur nouveau, aucune instance privee reelle, aucun push. |
| 2026-05-25 15:36 +02:00 | `CONV-2026-1769` | `NOVICE_RETURN_CORRECTION_PARCOURS_LIVE` | GO novice pour lancer la correction bornee; NO-GO produit live actuel. Priorites: compteurs coherents, `/pieces/<id>` ouvrable, libelles naturels, `/documents/ajouter` utile dans le premier viewport, mobile 390px, statut `Brouillon a copier, aucun envoi automatique`, export/passation hors chemin critique. |
| 2026-05-25 15:36 +02:00 | `CONV-2026-1772` / `CONV-2026-1773` | `COMPOSITION_EXPERT_METIER_REPLI_QA` | Nouvelle composition integree au premier chantier relance: le testeur expert metier n'est pas relance faute de thread disponible; QA/coordinateur local reprend explicitement la checklist juridique, compta, process chantier et syndic en s'appuyant sur le retour Hooke `CONV-2026-1767`. |
| 2026-05-25 15:39 +02:00 | `CONV-2026-1768` | `DESIGNER_RETURN_CORRECTION_PARCOURS` | Dirac cloture: GO designer pour la commande corrective bornee, NO-GO produit live tant que les ecarts actions, pieces, detail piece, relance et ajout document restent visibles. Libelles prioritaires confirmes: `Rattacher une piece`, `Creer demandes syndic`, `Brouillon a copier, non envoye`, `Ajout de document`, `Prochaine action`; aucun fichier modifie. |
| 2026-05-25 15:50 +02:00 | `CONV-2026-1770` / `CONV-2026-1772` | `OWNER_RETURN_QA_BLOQUEE_RELOAD` | Anscombe cloture avec correctif borne livre. Revue coordinateur: perimetre conforme, aucun second owner. Tests cibles TestClient `31 OK`, line-limit OK, diff-check OK; live `8788` conserve token/anti-fuite mais reste rouge sur 2 sous-echecs car `piece_detail_view.py` n'est pas recharge dans le serveur visible. QA/metier reste bloquee jusqu'au rechargement du serveur reserve, sans scan/kill ni serveur concurrent. |
