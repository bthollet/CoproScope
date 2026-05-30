# Equipe agile - ORD-P0-035 Diffusion revue

Date de lancement: 2026-05-25 03:55 +02:00.
Mode: equipe agile de cadrage produit, lecture seule, sans dev.

## BOT-START

```text
BOT-START - Coordinateur-scribe agile - 2026-05-25 03:55 +02:00
Roadmap: RM-2026-0025 / RM-2026-0013 / RM-2026-0006
Ordre: ORD-P0-035 / DIFFUSION-REVUE
Chantier: CH-20260525-035533-RM-2026-0025-diffusion-revue
Conversation: CONV-2026-1702
Role: Coordinateur-scribe agile
Mission: cadrer la revue de diffusion transversale avant partage ou export: qui peut voir, sous quelle forme, pourquoi, avec blocage si la decision de diffusion manque.
Ownership modifiable: docs/equipe_agile_2026-05-25_diffusion-revue.md, docs/presence_agents.md, trace append-only docs/roadmap_backlog_central.md et heartbeat relance-equipe-agile-gouvernail-autonome.
Fichiers a eviter: code applicatif, tests applicatifs, routes, templates, CSS, worktree principal sale, lots PRET_A_INTEGRER sans decision d'integration, instances privees, documents bruts, OCR/logs, exports bruts, secrets, serveurs locaux, push GitHub, RM-2026-0017 / ORD-P0-990, reouverture ORD-P0-002/010/011/012/020/030/031/032/033/034 sans nouveau diff ou decision Brice.
Dernier point lu: AGENTS.md, protocoles equipe agile/orchestration/roadmap/presence, consignes interconversations, gouvernail, presence et mission ORD-P0-034 cloturee.
Tests/preuves attendus: retours designer/novice/front/back/QA, cartographie des routes de diffusion/export/confidentialite et des ponts action/piece/demande/document, panier security/privacy/no-private/line-limit/smoke/captures futures.
Risque de collision: ORD-P0-021 reste PRET_A_INTEGRER sans decision; les lots ORD-P0-010/011/012/020/030/031/032/033/034 sont AGILE-DONE et ne doivent pas etre rouverts. Ce lot reste borne au cadrage Diffusion/Revue, sans patch code.
Lease ownership: jusqu'au 2026-05-25 05:55 +02:00.
Prochaine action: lancer les roles designer, novice, front, back/viewmodel et QA en lecture seule, puis consolider une commande future bornee ou un NO-GO dev.
```

## Etat initial

- A tester maintenant: pas de recette live; aucun serveur reserve.
- En dev maintenant: aucun dev; aucun owner code ouvert.
- En enquete maintenant: roles a lancer en lecture seule sur la revue de
  diffusion depuis actions, pieces, demandes, documents, confidentialite et
  exports derives.
- Commande prete: non; l'objectif est de borner la commande
  `diffusion_revue_v1`.
- Comparaison visuels enquete: references a relire
  `docs/roadmap_produit_fini_visuels_enquete.md`,
  `docs/confidentialite_et_biffage.md`,
  `docs/equipe_agile_2026-05-25_piece-preuve-detail.md`,
  `docs/equipe_agile_2026-05-25_demandes-syndicops.md`,
  `docs/equipe_agile_2026-05-25_decision-action-preuve.md` et
  `docs/equipe_agile_2026-05-25_files-reprise-cockpit.md`.
- Agents idle a relancer: designer, novice, front, back/viewmodel et QA.
- Decision requise: aucune decision Brice immediate. Un owner code futur doit
  etre explicite et en worktree dedie.
- Prochain mouvement: lancer les roles et recuperer les retours.
- Tests/preuves: `git diff --check` documentaire; tests applicatifs en lecture
  seulement si utiles a la cartographie, sans serveur.

## Roles

| Conversation | Role | Statut | Agent |
|---|---|---|---|
| `CONV-2026-1702` | Coordinateur-scribe agile | CLOTURE | local |
| `CONV-2026-1703` | Designer service / facilitateur | CLOTURE | Meitner `019e5cdb-9b6c-77d0-8fdd-67cdf518b5a4` |
| `CONV-2026-1704` | Utilisateur novice / membre CS | CLOTURE | Zeno `019e5cdb-9be8-7ad2-adfd-7e6d09aaf018` |
| `CONV-2026-1705` | Dev front lecture seule | CLOTURE | Helmholtz `019e5cdb-9c56-7663-89a5-ed66185265b1` |
| `CONV-2026-1706` | Dev back / viewmodel lecture seule | CLOTURE | local, reprise coordonnee |
| `CONV-2026-1707` | QA privacy / regression | CLOTURE | local, reprise coordonnee |

## Contraintes produit

- Une diffusion n'est jamais implicite: elle doit dire qui peut voir, sous
  quelle forme, pourquoi et avec quelle reserve.
- Un export est un derive controle, jamais une source de verite ni un brut.
- Si la decision de diffusion manque, le partage/export doit rester bloque ou
  en brouillon local.
- Les audiences doivent etre humaines et explicites: `CS seulement`,
  `coproprietaires apres relecture`, `AG/projet`, `restreint`, `bloque`.
- Les actions restent humaines: revoir diffusion, preparer un export derive,
  demander une validation, marquer une reserve, bloquer la diffusion.
- Aucun chemin local, brut, OCR/log, `raw`, `restricted`, `private`, email,
  telephone, token, secret ou document original ne doit apparaitre dans une
  projection diffusable.

## Attendus par role

- Designer: blueprint de la revue de diffusion, premier viewport, ligne type,
  etats vides, CTA prudents, relation avec action/piece/demande/document/export.
- Novice: verifier si un membre CS comprend qui voit quoi, pourquoi, sous quelle
  forme, et pourquoi un export peut etre bloque.
- Front: cartographier routes/templates/CSS existants pour confidentialite,
  exports, actions, pieces, demandes et documents; proposer un owner front futur
  borne et les fichiers a eviter.
- Back/viewmodel: cartographier read models, champs publics, decisions de
  diffusion, exports derives, allowlist future et champs interdits.
- QA: panier futur token/privacy/no-private/line-limit/smoke/captures, absence
  de brut, blocage export sans decision, non-regression des routes existantes.

## Retours consolides

### Designer `CONV-2026-1703`

Verdict: GO blueprint, NO-GO dev immediat. La revue de diffusion doit etre un
ecran place avant tout partage ou export, avec une regle bloquante: sans
decision de diffusion explicite, aucun partage/export.

Premier viewport cible: bandeau `diffusion a decider`, audience cible, forme de
sortie, justification, reserves, statut de biffage/agregation et file des
elements a revoir. Une action principale seulement si tout est complet. Ligne
type: `Objet metier`, `Source metier`, `Decision attendue`, `Audience`,
`Forme diffusable`, `Risque`, `Reserve`, `Prochaine action`.

CTA autorises: `Revoir la diffusion`, `Choisir l'audience`,
`Ajouter une justification`, `Marquer une reserve`,
`Preparer un export derive`, `Demander validation`, `Bloquer la diffusion`.
CTA interdits: `Partager`, `Envoyer`, `Publier`, `Telecharger original`,
`Afficher le brut`, `Valider automatiquement`, `Clore sans preuve`,
`Diffuser quand meme`.

### Novice `CONV-2026-1704`

Verdict: GO comprehension du cadrage, NO-GO dev/produit. Un membre CS novice
comprend si l'ecran repond toujours a cinq questions visibles: qui peut voir,
quoi sort, pourquoi on partage, quelle reserve reste et pourquoi c'est bloque.

Mots a garder: `Qui peut voir ?`, `CS seulement`,
`coproprietaires apres relecture`, `apercu`, `synthese`, `version biffee`,
`a relire avant partage`, `validation humaine requise`, `partage bloque`,
`preparer un export`, `raison du blocage`. Mots a eviter: `public` sans
precision, `publier`, `envoyer`, `exporter` si ce n'est qu'un apercu,
`valider`, `OK`, `diffusable` sans audience, jargon interne, statuts techniques
en anglais et sigles non expliques.

Confusions a traiter: un export n'est pas le document de reference; une piece
recue ne se partage pas automatiquement; `coproprietaires` ne veut pas dire
`tout le monde`; le blocage doit dire s'il vient d'une reserve, d'une absence de
decision ou d'un contenu a masquer.

### Front `CONV-2026-1705`

Routes confirmees: routes UI dans
`server/src/coproscope/web/_app_fragments/part_003.pyfrag`, dont `/actions`,
`/documents`, `/documents/{doc_id}`, `/documents/ajouter`, `/pieces`,
`/pieces/{piece_id}`, `/demandes`, `/demandes/relance`, `/confidentialite`,
`/chantiers` et `/depot`. Exports et API dans `part_004.pyfrag`: `/api/model`,
`/exports/actions.csv`, `/exports/actions.md`, `/exports/local.zip`,
`/exports/passation`, `/exports/passation.json`, `/exports/passation.txt`,
`/exports/passation/blocages/{blocker_id}`. DocOps feedback expose aussi
`/documents/tri-feedback` et des exports dedies.

Templates candidats: `passation_export.html`,
`passation_blocker_detail.html`, `privacy.html`, `actions.html`,
`pieces.html`, `piece_detail.html`, `requests.html`, `relance_syndic.html`,
`documents.html`, `document_detail.html`, `document_intake.html`,
`docops_feedback.html`, `depot.html` et `base.html`. CSS candidats:
`styles_part_03.css`, `styles_part_05.css`, `styles_part_06.css`,
`styles_part_08.css`, `styles_part_09.css`, `styles_part_10.css` et
`styles_part_11.css`.

A eviter ou extraire avant ajout lourd: `part_003.pyfrag` a 546 lignes,
`workstreams.html` a 526 lignes et `document_intake_view.py` a 516 lignes.
`part_004.pyfrag` reste le point naturel pour les exports existants mais un
module dedie est preferable si la revue devient une route propre.

### Back / viewmodel `CONV-2026-1706`

Fondations existantes: `_build_passation_export_model` produit deja un apercu
de passation derive avec `watermark`, `source_of_truth=false`, formats TXT/JSON,
checklist, restrictions et `blockers`. Les routes passation JSON/TXT passent
par des rendus derives et une verification `_assert_passation_export_route_safe`.
`/confidentialite` s'appuie sur le modele PrivacyOps/BiffageOps, avec statuts
de revue, biffage, aggregation, blocage et justification.

Manque a borner avant dev: un contrat public transversal
`model.ux.diffusion_revue_v1`, ou alias strict, qui devient la source UI de la
revue pre-export. Allowlist future: id opaque, type d'objet, libelle metier,
source metier non brute, audience, forme de sortie, raison, reserve, statut de
decision, transformation requise, risque, blocages, prochaine action humaine,
`source_of_truth=false`, watermark, liens tokenisables et trace de validation
humaine. Champs interdits: chemin local, nom brut sensible, OCR, logs, email,
telephone, token, secret, `raw`, `private`, `restricted`, `source_file`,
`local_path`, `absolute_path`, contenu original et action d'envoi automatique.

### QA `CONV-2026-1707`

Panier local vert: `test_ui_passation_export_route`,
`test_ui_security_routes`, `test_security_no_private_sync_leaks`,
`test_ui_document_viewer`, `test_ui_requests_route` et
`test_ui_piece_detail_route` passent avec 55 tests OK. `tools/check_code_line_limit.py`
est OK.

NO-GO produit maintenu sans recette navigateur ni captures desktop/mobile/tablette.
Tests futurs a ajouter si owner code: premier viewport strict
`diffusion_revue_v1`, bouton/lien de telechargement inactif sans decision,
explication courte du blocage, aucun chemin/brut/OCR/log, token conserve,
`source_of_truth=false`, pas de doublon token, pas d'envoi automatique, et
captures desktop/mobile/tablette avant GO produit.

## Resultat

AGILE-DONE - equipe agile a fini son job.

Commande future bornee: `diffusion_revue_v1`.

Routes candidates: `/confidentialite`, `/exports/passation`,
`/exports/passation/blocages/{blocker_id}`, ponts depuis `/actions`,
`/pieces`, `/demandes`, `/documents` et les exports derives existants.

Dev futur seulement si Brice valide un owner code dedie en worktree dedie, sur
donnees fictives/test ou derivees anonymisees. Cible: contrat public strict
`model.ux.diffusion_revue_v1`, revue pre-export humaine, audience/forme/raison/
reserve visibles, blocage si decision absente, export derive
`source_of_truth=false`, aucun brut servi, aucun envoi automatique, aucun
jargon technique.

Fichiers candidats: nouveau module/viewmodel dedie diffusion revue ou extension
bornee `_passation.py`, `part_004.pyfrag` si route export seulement,
`passation_export.html`, `passation_blocker_detail.html`, `privacy.html`, CSS
passation/confidentialite et tests dedies. A eviter ou extraire avant ajout
lourd: `part_003.pyfrag`, `workstreams.html`, `document_intake_view.py`.

Preuves de ce lot: lecture/cadrage uniquement, agents fermes, aucun code,
serveur, instance privee, document brut, export brut, secret ou push GitHub.
Panier local: 55 tests OK; line-limit OK. Pas de recette navigateur ni
captures.

## Journal

| Horodatage | Conversation | Evenement | Trace |
|---|---|---|---|
| 2026-05-25 03:55 +02:00 | `CONV-2026-1702` | `START_AGILE_DIFFUSION_REVUE` | `ORD-P0-034` est `AGILE-DONE`; les lots plus petits sont clos, stationnes ou non actionnables sans decision/recette. Nouveau chantier P0 ouvert sur `ORD-P0-035` en lecture/cadrage uniquement, sans code ni serveur. |
| 2026-05-25 03:55 +02:00 | `CONV-2026-1703`..`CONV-2026-1707` | `ROLES_RESERVED_DIFFUSION_REVUE` | Designer, novice, front, back/viewmodel et QA reserves en lecture seule; aucun code, serveur, instance privee, document brut, export brut, secret, push GitHub ou `RM-2026-0017`. |
| 2026-05-25 03:56 +02:00 | `CONV-2026-1703`..`CONV-2026-1707` | `AGENTS_LAUNCHED_DIFFUSION_REVUE` | Designer Meitner, novice Zeno et front Helmholtz lances en lecture seule; back/viewmodel et QA repris localement. Aucun code, serveur, instance privee, document brut, export brut, secret, push GitHub ou `RM-2026-0017`. |
| 2026-05-25 04:01 +02:00 | `CONV-2026-1703`..`CONV-2026-1707` | `ROLE_RETURNS_DIFFUSION_REVUE` | Retours designer, novice et front integres; back/viewmodel et QA consolides localement. Cible confirmee: revue pre-export humaine, audience/forme/raison/reserve visibles, blocage si decision absente, export derive `source_of_truth=false`. |
| 2026-05-25 04:02 +02:00 | `CONV-2026-1702`..`CONV-2026-1707` | `AGILE_DONE_DIFFUSION_REVUE` | Lot cloture sans dev. Commande future `diffusion_revue_v1` prete; tests passation/security/no-private/documents/demandes/pieces = 55 OK, line-limit OK; NO-GO produit sans recette navigateur/captures. |
