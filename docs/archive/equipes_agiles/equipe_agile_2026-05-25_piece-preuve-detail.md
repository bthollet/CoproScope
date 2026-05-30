# Equipe agile - ORD-P0-034 Piece preuve detail

Date de lancement: 2026-05-25 03:46 +02:00.
Mode: equipe agile de cadrage produit, lecture seule, sans dev.

## BOT-START

```text
BOT-START - Coordinateur-scribe agile - 2026-05-25 03:46 +02:00
Roadmap: RM-2026-0003 / RM-2026-0006 / RM-2026-0025
Ordre: ORD-P0-034 / PIECE-PREUVE-DETAIL
Chantier: CH-20260525-034601-RM-2026-0003-piece-preuve-detail
Conversation: CONV-2026-1696
Role: Coordinateur-scribe agile
Mission: cadrer la fiche piece/preuve depuis `/pieces` et `/documents`: comprendre quelle preuve une piece porte, rattacher, relancer ou verifier, sans servir de brut ni confondre piece candidate et preuve confirmee.
Ownership modifiable: docs/equipe_agile_2026-05-25_piece-preuve-detail.md, docs/presence_agents.md, trace append-only docs/roadmap_backlog_central.md et heartbeat relance-equipe-agile-gouvernail-autonome.
Fichiers a eviter: code applicatif, tests applicatifs, routes, templates, CSS, worktree principal sale, lots PRET_A_INTEGRER sans decision d'integration, instances privees, documents bruts, OCR/logs, exports bruts, secrets, serveurs locaux, push GitHub, RM-2026-0017 / ORD-P0-990, reouverture ORD-P0-002/010/011/012/020/030/031/032/033 sans nouveau diff ou decision Brice.
Dernier point lu: AGENTS.md, protocoles equipe agile/orchestration/roadmap/presence, consignes interconversations, gouvernail, presence et mission ORD-P0-033 cloturee.
Tests/preuves attendus: retours designer/novice/front/back/QA, cartographie `/pieces`, `/pieces/{piece_id}`, `/documents`, `/documents/{doc_id}` si accessible, detail piece/preuve, rattachements action/demande/decision, diffusion et panier security/privacy/no-private/line-limit/smoke/captures futures.
Risque de collision: ORD-P0-021 reste PRET_A_INTEGRER sans decision; ORD-P0-030/031/032/033 sont AGILE-DONE et ne doivent pas etre rouverts. Ce lot reste borne au cadrage Piece/Preuve detail, sans patch code.
Lease ownership: jusqu'au 2026-05-25 05:46 +02:00.
Prochaine action: lancer les roles designer, novice, front, back/viewmodel et QA en lecture seule, puis consolider une commande future bornee ou un NO-GO dev.
```

## Etat initial

- A tester maintenant: pas de recette live; aucun serveur reserve.
- En dev maintenant: aucun dev; aucun owner code ouvert.
- En enquete maintenant: roles a lancer en lecture seule sur `/pieces`,
  `/pieces/{piece_id}`, `/pieces?proof=missing`, `/documents` et les ecrans de
  detail/rattachement existants.
- Commande prete: non; l'objectif est de borner la commande
  `piece_preuve_detail_v1`.
- Comparaison visuels enquete: references a relire
  `docs/roadmap_produit_fini_visuels_enquete.md`,
  `docs/backlog_produit_fini_refonte_ux.md`,
  `docs/equipe_agile_2026-05-25_files-reprise-cockpit.md`,
  `docs/equipe_agile_2026-05-25_decision-action-preuve.md` et
  `docs/equipe_agile_2026-05-25_demandes-syndicops.md`.
- Agents idle a relancer: designer, novice, front, back/viewmodel et QA.
- Decision requise: aucune decision Brice immediate. Un owner code futur doit
  etre explicite et en worktree dedie.
- Prochain mouvement: lancer les roles et recuperer les retours.
- Tests/preuves: `git diff --check` documentaire; tests applicatifs en lecture
  seulement si utiles a la cartographie, sans serveur.

## Roles

| Conversation | Role | Statut | Agent |
|---|---|---|---|
| `CONV-2026-1696` | Coordinateur-scribe agile | CLOTURE | local |
| `CONV-2026-1697` | Designer service / facilitateur | CLOTURE | Mendel `019e5cd1-ed48-7ab1-8923-1f7a1d78cd32` |
| `CONV-2026-1698` | Utilisateur novice / membre CS | CLOTURE | Cicero `019e5cd2-179b-7702-bb77-65012b8fee82` |
| `CONV-2026-1699` | Dev front lecture seule | CLOTURE | Sagan `019e5cd2-358c-7ca1-843d-478ae5c89b8f` |
| `CONV-2026-1700` | Dev back / viewmodel lecture seule | CLOTURE | local, reprise faute capacite threads |
| `CONV-2026-1701` | QA privacy / regression | CLOTURE | local, reprise faute capacite threads |

## Contraintes produit

- Une piece affichee n'est pas automatiquement une preuve validee.
- La fiche doit dire: ce que la piece montre, pour quel sujet/action/demande,
  quelle preuve est attendue, ce qui manque, qui peut voir, et le prochain geste
  humain.
- Aucun brut, chemin local, OCR/log, `raw`, `restricted`, `private`, email,
  telephone ou fichier source sensible ne doit apparaitre dans l'UI ou les
  traces diffusable.
- Les rattachements doivent distinguer piece recue, piece candidate, preuve a
  verifier, preuve validee et diffusion autorisee.
- Les actions possibles restent humaines: rattacher, demander une preuve,
  preparer une relance, verifier la diffusion, marquer une reserve.

## Attendus par role

- Designer: blueprint de la fiche piece/preuve, premier viewport, etats vides,
  ligne de rattachement, CTA prudents, relation avec actions/demandes/decisions.
- Novice: verifier si un membre CS comprend la difference entre piece,
  preuve attendue, preuve candidate, preuve verifiee, diffusion et relance.
- Front: cartographier routes/templates/CSS existants pour `/pieces`,
  `/pieces/{piece_id}`, `/pieces?proof=missing`, `/documents` et detail
  document si pertinent; proposer un owner front futur borne.
- Back/viewmodel: cartographier viewmodels pieces/documents, contrats publics,
  champs publics, allowlist future et champs interdits.
- QA: panier futur token/privacy/no-private/line-limit/smoke/captures,
  distinction piece/preuve, anti-fuite, etats incomplets et tests novice.

## Retours consolides

### Designer `CONV-2026-1697`

Verdict: GO blueprint produit, NO-GO dev immediat. La route pivot est
`/pieces/{piece_id}`, avec entrees depuis `/pieces`, `/pieces?proof=missing` et
`/documents` quand un document est deja classe comme piece candidate.

Premier viewport cible: titre humain `Piece a verifier` ou `Preuve rattachee`,
badge `Candidate` / `A verifier` / `Preuve confirmee` / `Reserve` /
`Diffusion a revoir`, sujet lie, phrase `ce que la piece semble montrer`,
preuve attendue, prochain geste humain et diffusion. Ligne type:
`Sujet`, `Statut preuve`, `Preuve attendue`, `Lien metier`,
`Prochain geste`, `Diffusion`.

CTA autorises: `Rattacher a une action`, `Rattacher a une demande`,
`Rattacher a une decision`, `Preparer une demande de preuve`,
`Noter une verification humaine`, `Marquer une reserve`,
`Revoir la diffusion`, `Ouvrir le resume derive`. Interdits:
`Envoyer`, `Partager automatiquement`, `Valider juridiquement`,
`Cloturer sans verification`, `Afficher le brut`, `Telecharger original`,
`Voir chemin source`.

### Novice `CONV-2026-1698`

Verdict: GO comprehension du cadrage, NO-GO produit avant ecran reel/captures.
Un membre CS comprend si la fiche est structuree autour de `ce que la piece
montre`, `preuve attendue`, `preuve candidate`, `preuve verifiee`,
`rattachee a`, `qui peut voir` et `prochain geste humain`.

Mots a garder: `Piece recue`, `Ce que cela montre`, `Preuve attendue`,
`Preuve candidate`, `Preuve verifiee`, `A verifier`,
`Rattache a une action / demande / decision`, `Diffusion autorisee`,
`Prochain geste`, `Preparer une relance`, `Marquer une reserve`. Confusions a
lever: une piece recue n'est pas forcement une preuve; une piece candidate ne
cloture rien seule; une reponse syndic n'est pas automatiquement une preuve; la
diffusion doit etre decidee avant partage.

### Front `CONV-2026-1699`

Routes confirmees: `/pieces`, `/pieces?proof=missing` et `/pieces/{piece_id}`
dans `server/src/coproscope/web/_app_fragments/part_003.pyfrag`; templates
`pieces.html` et `piece_detail.html`; viewmodel `piece_detail_view.py`.
`/documents` et `/documents/{doc_id}` sont aussi dans `part_003.pyfrag`, avec
templates `documents.html` et `document_detail.html`.

Etat actuel: `/pieces/{piece_id}` est proche de la cible et distingue deja
candidate/preuve finale; `/pieces?proof=missing` reste utile mais contient le
CTA ambigu `Voir pieces privees`; `/documents` et `/documents/{doc_id}` sont
encore trop generalistes pour faire remonter directement preuve portee,
rattachement et diffusion. Futur owner front: `pieces.html`,
`piece_detail.html`, `documents.html`, `document_detail.html`, CSS cible. A
eviter ou extraire avant extension: `part_003.pyfrag` proche 600 lignes,
`styles_part_09.css`, `styles_part_08.css`, `styles_part_11.css` et
`viewmodels/_pieces_ux.py` deja denses.

### Back / viewmodel `CONV-2026-1700`

Fondations existantes: `piece_detail_view.py` fabrique une fiche detail sure
avec identifiant public, masquage des references privees, etats preuve,
rattachements action/demande/depot, diffusion et actions tokenisables.
`_pieces_ux.py` produit `ux.pieces`, `missing`, `to_verify`, legendes et liens
vers relance/depot/documents. `_piece_workshop.py` agrege DocOps, DecisionOps et
IncidentOps. `_priority_views.py` transforme les pieces manquantes en file
publique `/pieces?proof=missing`.

Contrat futur requis: `model.ux.piece_preuve_detail_v1`, ou alias public strict,
avec allowlist: id opaque, libelle metier, resume derive, statut preuve,
preuve attendue, rattachements action/demande/decision, derniere verification
humaine, diffusion, prochaine action, liens tokenisables, pieces candidates et
preuve verifiee separees. Champs interdits: chemin, nom brut sensible, OCR,
logs, email, telephone, token, secret, `raw`, `private`, `restricted`, contenu
original servi directement et validation automatique.

### QA `CONV-2026-1701`

Panier actuel vert: `test_ui_piece_detail_route`, `test_ui_pieces_viewmodel`,
`test_ui_atelier_piece`, `test_ui_document_viewer`,
`test_ui_document_intake_route`, `test_ui_smoke_routes_expanded`,
`test_ui_security_routes` et `test_security_no_private_sync_leaks` passent avec
45 tests OK. `tools/check_code_line_limit.py` est OK.

NO-GO produit maintenu sans recette navigateur/captures desktop-mobile-tablette.
Tests futurs a ajouter si owner code: premier viewport strict
`piece_preuve_detail_v1`, interdiction de `Voir pieces privees`,
parcours `/documents` -> detail document -> fiche piece/preuve, absence de
brut/chemin/OCR, token conserve, piece candidate non validante, diffusion
requise avant partage/export.

## Resultat

AGILE-DONE - equipe agile a fini son job.

Commande future bornee: `piece_preuve_detail_v1`.

Routes: `/pieces`, `/pieces/{piece_id}`, `/pieces?proof=missing`, pont depuis
`/documents` et `/documents/{doc_id}`.

Dev futur seulement si Brice valide un owner code dedie en worktree dedie, sur
donnees fictives/test ou derivees anonymisees. Cible: contrat public strict
`model.ux.piece_preuve_detail_v1`, premier viewport fiche piece/preuve,
distinction piece recue / piece candidate / preuve verifiee / reserve /
diffusion, aucun brut servi, aucun envoi automatique, aucun jargon technique.

Fichiers candidats: `piece_detail_view.py`, `_pieces_ux.py`,
`_priority_views.py`, `pieces.html`, `piece_detail.html`, `documents.html`,
`document_detail.html`, CSS dedie et tests dedies. `part_003.pyfrag` est a
eviter ou a extraire avant modification car proche du seuil 600 lignes.

Preuves de ce lot: lecture/cadrage uniquement, agents fermes, aucun code,
serveur, instance privee, document brut, export brut, secret ou push GitHub.
Panier local: 45 tests OK; line-limit OK. Pas de recette navigateur ni
captures.

## Journal

| Horodatage | Conversation | Evenement | Trace |
|---|---|---|---|
| 2026-05-25 03:46 +02:00 | `CONV-2026-1696` | `START_AGILE_PIECE_PREUVE_DETAIL` | `ORD-P0-033` est `AGILE-DONE`; les lots plus petits sont clos, stationnes ou non actionnables sans decision/recette. Nouveau chantier P0 ouvert sur `ORD-P0-034` en lecture/cadrage uniquement, sans code ni serveur. |
| 2026-05-25 03:46 +02:00 | `CONV-2026-1697`..`CONV-2026-1701` | `ROLES_RESERVED_PIECE_PREUVE_DETAIL` | Designer, novice, front, back/viewmodel et QA reserves en lecture seule; aucun code, serveur, instance privee, document brut, export brut, secret, push GitHub ou `RM-2026-0017`. |
| 2026-05-25 03:47 +02:00 | `CONV-2026-1697`..`CONV-2026-1701` | `AGENTS_LAUNCH_PARTIAL_PIECE_PREUVE_DETAIL` | Designer Mendel, novice Cicero et front Sagan lances en lecture seule; back/viewmodel et QA repris localement faute de capacite de threads. |
| 2026-05-25 03:50 +02:00 | `CONV-2026-1697`..`CONV-2026-1701` | `ROLE_RETURNS_PIECE_PREUVE_DETAIL` | Retours designer, novice et front integres; back/viewmodel et QA consolides localement. Cible confirmee: fiche `/pieces/{piece_id}`, piece candidate distincte de preuve verifiee, diffusion visible, aucun brut servi. |
| 2026-05-25 03:51 +02:00 | `CONV-2026-1696`..`CONV-2026-1701` | `AGILE_DONE_PIECE_PREUVE_DETAIL` | Lot cloture sans dev. Commande future `piece_preuve_detail_v1` prete; tests pieces/documents/smoke/security/no-private = 45 OK, line-limit OK; NO-GO produit sans recette navigateur/captures. |
