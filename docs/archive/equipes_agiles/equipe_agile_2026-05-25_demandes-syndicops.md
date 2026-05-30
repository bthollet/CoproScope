# Equipe agile - ORD-P0-033 Demandes SyndicOps

Date de lancement: 2026-05-25 03:32 +02:00.
Mode: equipe agile de cadrage produit, lecture seule, sans dev.

## BOT-START

```text
BOT-START - Coordinateur-scribe agile - 2026-05-25 03:32 +02:00
Roadmap: RM-2026-0037 / RM-2026-0003 / RM-2026-0006 / RM-2026-0031
Ordre: ORD-P0-033 / DEMANDES-SYNDICOPS
Chantier: CH-20260525-033200-RM-2026-0037-demandes-syndicops
Conversation: CONV-2026-1690
Role: Coordinateur-scribe agile
Mission: cadrer la boite demandes/SyndicOps multi-canaux: creer ou recevoir une demande, relancer, noter l'envoi hors CoproScope, rattacher une reponse ou preuve, sans lancer de dev dans le worktree principal sale.
Ownership modifiable: docs/equipe_agile_2026-05-25_demandes-syndicops.md, docs/presence_agents.md, trace append-only docs/roadmap_backlog_central.md et heartbeat relance-equipe-agile-gouvernail-autonome.
Fichiers a eviter: code applicatif, tests applicatifs, routes, templates, CSS, worktree principal sale, lots PRET_A_INTEGRER sans decision d'integration, instances privees, documents bruts, OCR/logs, exports bruts, secrets, serveurs locaux, push GitHub, RM-2026-0017 / ORD-P0-990, reouverture ORD-P0-002/010/011/012/020/030/031/032 sans nouveau diff ou decision Brice.
Dernier point lu: AGENTS.md, protocoles equipe agile/orchestration/roadmap/presence, consignes interconversations, gouvernail, presence et mission ORD-P0-032 cloturee.
Tests/preuves attendus: retours designer/novice/front/back/QA, cartographie `/demandes`, `/demandes/relance`, `/actions?scope=syndic` et `/pieces?proof=missing`, contrat public borne, GO/NO-GO novice, panier security/privacy/no-private/line-limit/smoke/captures futures.
Risque de collision: ORD-P0-021 reste PRET_A_INTEGRER sans decision; ORD-P0-030/031/032 sont AGILE-DONE et ne doivent pas etre rouverts. Ce lot reste borne au cadrage SyndicOps/demandes, sans patch code.
Lease ownership: jusqu'au 2026-05-25 05:32 +02:00.
Prochaine action: lancer les roles designer, novice, front, back/viewmodel et QA en lecture seule, puis consolider une commande future bornee ou un NO-GO dev.
```

## Etat initial

- A tester maintenant: pas de recette live; aucun serveur reserve.
- En dev maintenant: aucun dev; aucun owner code ouvert.
- En enquete maintenant: roles a lancer en lecture seule sur `/demandes`,
  `/demandes/relance`, `/actions?scope=syndic`, `/pieces?proof=missing`,
  `requestops`, `syndicops` et les sources UX demandes/sollicitations.
- Commande prete: non; l'objectif est de borner la commande
  `demandes_syndicops_v1`.
- Comparaison visuels enquete: references a relire
  `docs/recherche_ux_ui_2026-05-24_alertes-sollicitations-copro.md`,
  `docs/recherche_ux_ui_2026-05-24_alertes-sollicitations-copro_relance.md`,
  `docs/roadmap_produit_fini_visuels_enquete.md` et les assets associes.
- Agents idle a relancer: designer, novice, front, back/viewmodel et QA.
- Decision requise: aucune decision Brice immediate. Un owner code futur doit
  etre explicite et en worktree dedie.
- Prochain mouvement: lancer les roles et recuperer les retours.
- Tests/preuves: `git diff --check` documentaire; tests applicatifs en lecture
  seulement si utiles a la cartographie, sans serveur.

## Roles

| Conversation | Role | Statut | Agent |
|---|---|---|---|
| `CONV-2026-1690` | Coordinateur-scribe agile | CLOTURE | local |
| `CONV-2026-1691` | Designer service / facilitateur | CLOTURE | Ptolemy `019e5cc5-42bb-7260-b665-6714b5891d50` |
| `CONV-2026-1692` | Utilisateur novice / membre CS | CLOTURE | Hubble `019e5cc5-432a-7b32-964c-4741116d486e` |
| `CONV-2026-1693` | Dev front lecture seule | CLOTURE | Tesla `019e5cc5-439b-7bb3-bd7e-67d54875c0bb` |
| `CONV-2026-1694` | Dev back / viewmodel lecture seule | CLOTURE | local, reprise faute capacite threads |
| `CONV-2026-1695` | QA privacy / regression | CLOTURE | local, reprise faute capacite threads |

## Contraintes produit

- Une demande doit indiquer: origine/canal, objet, responsable, echeance,
  preuve attendue, statut, derniere action, diffusion et prochaine action
  humaine.
- Une relance reste un brouillon copiable ou une trace d'envoi hors CoproScope;
  aucun bouton ne doit promettre l'envoi automatique.
- Une reponse recue ne vaut pas preuve de cloture tant que la preuve attendue
  n'est pas nommee et validee humainement.
- La boite doit distinguer demande sortante, sollicitation entrante, relance,
  reponse, piece rattachee, preuve validee et diffusion autorisee.
- Les donnees de cadrage restent fictives, publiques de test ou deja
  anonymisees; aucune instance privee, document brut, OCR/log ou export brut.

## Attendus par role

- Designer: blueprint de la boite demandes/SyndicOps, premier viewport, ligne
  type, etats vides, relation avec pieces/actions/decision et messages entrants.
- Novice: verifier si un membre CS comprend quoi faire, qui attend quoi, quel
  canal utiliser, ce qui a ete envoye hors outil et ce qui peut etre partage.
- Front: cartographier routes/templates/CSS existants pour `/demandes`,
  `/demandes/relance`, `/actions?scope=syndic` et `/pieces?proof=missing`;
  proposer un futur owner front borne.
- Back/viewmodel: cartographier `requestops`, `syndicops`, read models, champs
  publics, allowlist future et champs interdits.
- QA: panier futur token/privacy/no-private/line-limit/smoke/captures, anti
  envoi automatique, anti-fuite, etats incomplets et tests novice.

## Retours consolides

### Designer `CONV-2026-1691`

Verdict: GO blueprint, NO-GO dev immediat. La route pivot reste `/demandes`
avec le titre cible `Demandes et relances` et une promesse explicite:
CoproScope prepare et trace, il n'envoie rien.

Premier viewport cible: bandeau mode local/aucune synchro externe/diffusion a
verifier, compteurs `A qualifier`, `A relancer`, `Reponses a verifier` et
`Preuves manquantes`, filtres `Toutes`, `Au syndic`, `Messages recus`,
`Reponses recues`, `Cloturees`, puis master-detail file actionnable + detail
demande.

Chaque ligne doit porter type, canal, sujet, pourquoi ici, responsable ou
detenteur, echeance, preuve/source disponible, preuve attendue, derniere action,
diffusion et prochaine action humaine. Les CTA autorises sont des actions
humaines (`Preparer la relance`, `Copier le brouillon`, `Noter l'envoi fait
hors CoproScope`, `Rattacher la reponse recue`, `Verifier la diffusion`).
Sont interdits: `Envoyer`, `Relancer` seul, `Diffuser`, `Publier`, `Valider`,
`Clore automatiquement`, `Synchroniser la boite mail`, `Envoyer LRAR`.

### Novice `CONV-2026-1692`

Verdict: GO comprehension si l'ecran reste une boite de suivi humaine; NO-GO
livraison produit sans route reelle testee et captures desktop/mobile/tablette.
Un membre CS comprend la boucle seulement si demande, relance, envoi fait
ailleurs, reponse, piece, preuve et diffusion sont separes.

Libelles a garder: `Demandes au syndic`, `Messages recus`,
`Preparer une relance`, `Brouillon a copier`,
`Noter un envoi fait hors CoproScope`, `Reponse recue`, `Piece recue`,
`Preuve attendue`, `Preuve verifiee`, `Qui peut voir ?`, `Prochaine action`.
Eviter en premier niveau: `SyndicOps`, `workflow`, `read model`, `connecteur`,
`preuve candidate` non expliquee, `diligence`, `multi-canaux` sans exemples.

### Front `CONV-2026-1693`

Routes et fichiers existants confirmes: `/demandes` et `/demandes/relance`
dans `server/src/coproscope/web/_app_fragments/part_003.pyfrag`, templates
`requests.html` et `relance_syndic.html`, viewmodels `requests_view.py` et
`relance_syndic_view.py`; `/actions?scope=syndic` via `actions.html` et
`_actions_reprise_syndic.html`; `/pieces?proof=missing` via `pieces.html` et
`_priority_views.py`.

Owner front futur borne: transformer `requests.html` en boite demandes
master-detail, remonter les CTA `copier brouillon` / `noter hors CoproScope` /
`rattacher reponse-preuve` dans `relance_syndic.html`, aligner
`_actions_reprise_syndic.html`, corriger le CTA ambigu `Voir pieces privees`
dans `pieces.html`, utiliser plutot `styles_part_12.css` ou `styles_part_13.css`.
Eviter `part_003.pyfrag` proche du plafond 600 lignes et les gros CSS deja
proches du seuil.

### Back / viewmodel `CONV-2026-1694`

`requestops` fournit deja registre demandes + journal d'actions avec masquage
privacy, statuts et diffusion; `syndicops` fournit une normalisation utile sur
piece attendue, echeance, preuve attendue, reponse, preuve et statut. Il manque
toutefois un contrat public explicite `model.ux.demandes_syndicops_v1`.

Allowlist future recommandee: identifiant opaque, type, canal, sujet,
pourquoi, echeance, responsable/detenteur, preuve source publique, preuve
attendue, statut, derniere action, diffusion, liens action/decision/piece,
CTA autorises, journal public synthetique, drapeaux
`can_mark_external_sent`, `can_attach_response`,
`can_close_with_verified_proof`. Champs interdits: chemin brut, `raw`,
`restricted`, `logs`, `private`, secret, email/telephone en clair, hash/payload
metier exposes et statut laissant croire a un envoi automatique.

### QA `CONV-2026-1695`

Panier existant vert: `test_syndicops`, `test_ui_requests`,
`test_ui_requests_route`, `test_ui_pieces_viewmodel`,
`test_ui_piece_detail_route`, `test_ui_registre_actions`,
`test_ui_smoke_routes_expanded`, `test_ui_security_routes` et
`test_security_no_private_sync_leaks` passent avec 55 tests OK, 1 skip front
cible attendu. `tools/check_code_line_limit.py` est OK.

NO-GO produit maintenu sans recette navigateur/captures desktop-mobile-tablette.
Tests futurs a ajouter si owner code: 4 routes tokenisees, absence de bouton
`Envoyer`, token conserve dans les liens proteges, libelles novice visibles
des le premier viewport, `Voir pieces privees` interdit, aucune fuite
raw/private/path/email/telephone, POST relance limite a une trace locale.

## Resultat

AGILE-DONE - equipe agile a fini son job.

Commande future bornee: `demandes_syndicops_v1`.

Routes: `/demandes`, `/demandes/relance`, `/actions?scope=syndic`,
`/pieces?proof=missing`.

Dev futur seulement si Brice valide un owner code dedie en worktree dedie,
sur donnees fictives/test ou derivees anonymisees. Cible: contrat public strict
`model.ux.demandes_syndicops_v1`, premier viewport demandes/relances
master-detail, separation demande sortante/message entrant/relance/reponse/
piece/preuve/diffusion, relance uniquement en brouillon ou trace hors
CoproScope, aucun envoi automatique, aucun jargon technique, aucun raw/private.

Fichiers candidats: `requests_view.py`, `relance_syndic_view.py`,
`requests.html`, `relance_syndic.html`, `_actions_reprise_syndic.html`,
`pieces.html`, CSS dedie sous seuil et tests dedies. `part_003.pyfrag` est a
eviter ou a extraire avant modification car proche du seuil 600 lignes.

Preuves de ce lot: lecture/cadrage uniquement, agents fermes, aucun code,
serveur, instance privee, document brut, export brut, secret ou push GitHub.
Panier local: 55 tests OK, 1 skip attendu; line-limit OK. Pas de recette
navigateur ni captures.

## Journal

| Horodatage | Conversation | Evenement | Trace |
|---|---|---|---|
| 2026-05-25 03:32 +02:00 | `CONV-2026-1690` | `START_AGILE_DEMANDES_SYNDICOPS` | `ORD-P0-032` est `AGILE-DONE`; les lots plus petits sont clos, stationnes ou non actionnables sans decision/recette. Nouveau chantier P0 ouvert sur `ORD-P0-033` en lecture/cadrage uniquement, sans code ni serveur. |
| 2026-05-25 03:32 +02:00 | `CONV-2026-1691`..`CONV-2026-1695` | `ROLES_RESERVED_DEMANDES_SYNDICOPS` | Designer, novice, front, back/viewmodel et QA reserves en lecture seule; aucun code, serveur, instance privee, document brut, export brut, secret, push GitHub ou `RM-2026-0017`. |
| 2026-05-25 03:33 +02:00 | `CONV-2026-1691`..`CONV-2026-1695` | `AGENTS_LAUNCH_PARTIAL_DEMANDES_SYNDICOPS` | Designer Ptolemy, novice Hubble et front Tesla lances en lecture seule; back/viewmodel et QA repris localement faute de capacite de threads. |
| 2026-05-25 03:38 +02:00 | `CONV-2026-1691`..`CONV-2026-1695` | `ROLE_RETURNS_DEMANDES_SYNDICOPS` | Retours designer, novice et front integres; back/viewmodel et QA consolides localement. Cible confirmee: boite demandes/relances humaine, aucun envoi automatique, reponse distincte de preuve, diffusion visible et contrat public strict. |
| 2026-05-25 03:39 +02:00 | `CONV-2026-1690`..`CONV-2026-1695` | `AGILE_DONE_DEMANDES_SYNDICOPS` | Lot cloture sans dev. Commande future `demandes_syndicops_v1` prete; tests demandes/pieces/actions/smoke/security/no-private = 55 OK, 1 skip front cible attendu, line-limit OK; NO-GO produit sans recette navigateur/captures. |
