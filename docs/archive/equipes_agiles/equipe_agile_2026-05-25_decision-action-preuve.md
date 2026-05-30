# Equipe agile - ORD-P0-032 Decision action preuve

Date de lancement: 2026-05-25 03:18 +02:00.
Mode: equipe agile de cadrage produit, lecture seule, sans dev.

## BOT-START

```text
BOT-START - Coordinateur-scribe agile - 2026-05-25 03:18 +02:00
Roadmap: RM-2026-0038 / RM-2026-0003 / RM-2026-0006
Ordre: ORD-P0-032 / DECISION-ACTION-PREUVE
Chantier: CH-20260525-031800-RM-2026-0038-decision-action-preuve
Conversation: CONV-2026-1684
Role: Coordinateur-scribe agile
Mission: cadrer le registre visible decisions -> actions -> preuves, raccorde aux demandes, pieces et travaux, sans lancer de dev dans le worktree principal sale.
Ownership modifiable: docs/equipe_agile_2026-05-25_decision-action-preuve.md, docs/presence_agents.md, trace append-only docs/roadmap_backlog_central.md et heartbeat relance-equipe-agile-gouvernail-autonome.
Fichiers a eviter: code applicatif, tests applicatifs, routes, templates, CSS, worktree principal sale, lots PRET_A_INTEGRER sans decision d'integration, instances privees, documents bruts, OCR/logs, exports bruts, secrets, serveurs locaux, push GitHub, RM-2026-0017 / ORD-P0-990, reouverture ORD-P0-002/010/011/012/020/030/031 sans nouveau diff ou decision Brice.
Dernier point lu: AGENTS.md, protocoles equipe agile/orchestration/roadmap/presence, consignes interconversations, gouvernail, presence et mission ORD-P0-031 cloturee.
Tests/preuves attendus: retours designer/novice/front/back/QA, cartographie DecisionOps et /actions, contrat public borne, GO/NO-GO novice, panier security/privacy/no-private/line-limit/smoke/captures futures.
Risque de collision: ORD-P0-021 reste PRET_A_INTEGRER sans decision; ORD-P0-030 et ORD-P0-031 sont AGILE-DONE et ne doivent pas etre rouverts. Ce lot reste borne au cadrage DecisionOps, sans patch code.
Lease ownership: jusqu'au 2026-05-25 05:18 +02:00.
Prochaine action: lancer les roles designer, novice, front, back/viewmodel et QA en lecture seule, puis consolider une commande future bornee ou un NO-GO dev.
```

## Etat initial

- A tester maintenant: pas de recette live; aucun serveur reserve.
- En dev maintenant: aucun dev; aucun owner code ouvert.
- En enquete maintenant: roles a lancer en lecture seule sur `/actions`,
  `workstreams`, DecisionOps et les sources visuelles registre.
- Commande prete: non; l'objectif est de borner la commande
  `decision_action_preuve_v1`.
- Comparaison visuels enquete: references obligatoires
  `docs/assets/etude-utilisateurs/registre-decisions-actions-preuves.png` et
  `docs/assets/ux-realignement-2026-05-20/02_registre_decisions_actions_preuves.png`.
- Agents idle a relancer: designer, novice, front, back/viewmodel et QA.
- Decision requise: aucune decision Brice immediate. Un owner code futur doit
  etre explicite et en worktree dedie.
- Prochain mouvement: lancer les roles et recuperer les retours.
- Tests/preuves: `git diff --check` documentaire; tests applicatifs en lecture
  seulement si utiles a la cartographie, sans serveur.

## Roles

| Conversation | Role | Statut | Agent |
|---|---|---|---|
| `CONV-2026-1684` | Coordinateur-scribe agile | CLOTURE | local |
| `CONV-2026-1685` | Designer service / facilitateur | CLOTURE | Descartes `019e5cb7-e588-79c0-8f55-1d395233a9b2` |
| `CONV-2026-1686` | Utilisateur novice / membre CS | CLOTURE | Anscombe `019e5cb7-fe82-74e1-bbf1-fe9f3da2d9d8` |
| `CONV-2026-1687` | Dev front lecture seule | CLOTURE | Faraday `019e5cb8-15a7-7283-bd7f-39d00dd3da0e` |
| `CONV-2026-1688` | Dev back / viewmodel lecture seule | CLOTURE | local, reprise faute capacite threads |
| `CONV-2026-1689` | QA privacy / regression | CLOTURE | local, reprise faute capacite threads |

## Contraintes produit

- Une decision AG/CS doit devenir une action suivie jusqu'a preuve de cloture.
- La ligne doit toujours afficher: decision/source, action attendue,
  responsable, echeance, preuve attendue, statut, diffusion et memoire.
- Une action sans preuve attendue ou diffusion lisible reste incomplete.
- Le produit ne doit jamais presenter une preuve candidate comme preuve finale.
- Aucune conclusion juridique/comptable automatique; validation humaine
  obligatoire.
- Aucun bouton ne doit promettre envoi automatique, publication ou cloture sans
  controle.
- Les donnees de cadrage restent fictives, publiques de test ou deja
  anonymisees.

## Attendus par role

- Designer: blueprint de la fiche ou file Decision -> action -> preuve, premier
  viewport, ligne type, etat vide et relation avec pieces/demandes/travaux.
- Novice: verifier si un membre CS comprend quoi faire, ce qui manque comme
  preuve et ce qui peut etre partage.
- Front: cartographier routes/templates/CSS existants pour `/actions`,
  `workstreams` et detail action; proposer un futur owner front borne.
- Back/viewmodel: cartographier DecisionOps, read models, champs publics,
  allowlist future et champs interdits.
- QA: panier futur token/privacy/no-private/line-limit/smoke/captures, anti
  verdict automatique, anti-fuite et etats incomplets.

## Journal

| Horodatage | Conversation | Evenement | Trace |
|---|---|---|---|
| 2026-05-25 03:18 +02:00 | `CONV-2026-1684` | `START_AGILE_DECISION_ACTION_PREUVE` | `ORD-P0-031` est `AGILE-DONE`; les lots plus petits sont clos, stationnes ou non actionnables sans decision/recette. Nouveau chantier P0 ouvert sur `ORD-P0-032` en lecture/cadrage uniquement, sans code ni serveur. |
| 2026-05-25 03:18 +02:00 | `CONV-2026-1685`..`CONV-2026-1689` | `ROLES_RESERVED_DECISION_ACTION_PREUVE` | Designer, novice, front, back/viewmodel et QA reserves en lecture seule; aucun code, serveur, instance privee, document brut, export brut, secret, push GitHub ou `RM-2026-0017`. |
| 2026-05-25 03:19 +02:00 | `CONV-2026-1685`..`CONV-2026-1689` | `AGENTS_LAUNCH_PARTIAL_DECISION_ACTION_PREUVE` | Designer Descartes, novice Anscombe et front Faraday lances en lecture seule; back/viewmodel et QA repris localement faute de capacite de threads. |
| 2026-05-25 03:26 +02:00 | `CONV-2026-1685`..`CONV-2026-1689` | `ROLE_RETURNS_DECISION_ACTION_PREUVE` | Retours designer, novice et front integres; back/viewmodel et QA consolides localement. Tous les roles sont clos; aucun code, serveur, instance privee ou export brut n'a ete touche. |
| 2026-05-25 03:27 +02:00 | `CONV-2026-1684` | `AGILE_DONE_DECISION_ACTION_PREUVE` | Lot cloture sans dev. Commande future `decision_action_preuve_v1` bornee; prochain heartbeat doit passer a `ORD-P0-033` si aucun nouveau diff ou arbitrage ne rouvre ce lot. |
| 2026-05-25 03:28 +02:00 | `relance-equipe-agile-gouvernail-autonome` | `AUTOMATION_RECADRAGE_DECISION_ACTION_PREUVE` | Heartbeat conservee et recadree vers le prochain P0 actionnable; ne pas rouvrir ce lot sans nouveau diff ou decision Brice. |

## Retour designer - CONV-2026-1685

Verdict: GO blueprint, NO-GO dev immediat. La bonne cible est de durcir
`/actions` comme registre decision -> action -> preuve, avec entree dediee
`/actions?scope=decisions`, sans creer un ecran concurrent.

Premier viewport cible: titre `Decisions a suivre`, decisions groupees par
AG/CS a gauche et fiche decision a droite. Le bandeau court doit afficher
responsable, echeance, statut, preuve attendue et diffusion. Les onglets utiles
sont action, preuves, pieces liees, demande ou relance, historique.

Ligne type: decision/source -> action attendue -> responsable -> echeance ->
preuve attendue -> piece candidate ou preuve verifiee -> prochaine action
humaine -> diffusion -> memoire/passation.

Risques clefs: une piece candidate ne doit pas etre presentee comme preuve
finale; diffusion et preuve sont deux decisions differentes; une action sans
preuve attendue nommee ou diffusion lisible reste incomplete.

## Retour novice - CONV-2026-1686

Verdict: GO comprehension conditionnel, NO-GO livraison produit. Un membre CS
comprend le chemin si l'ecran garde la chaine simple: decision/source -> action
attendue -> responsable -> echeance -> preuve attendue -> relance ou piece ->
preuve validee -> diffusion/memoire.

Confusions a lever: `piece liee` n'est pas forcement `preuve`; `preuve
candidate` n'est pas `preuve validee`; `terminee` peut etre compris comme fini
sans preuve; `relance syndic` doit rester un brouillon ou une trace d'envoi hors
CoproScope, jamais un envoi automatique.

Mots a garder au premier niveau: decision AG/CS, action attendue, preuve
attendue, preuve a verifier, preuve validee, piece liee, responsable, echeance,
prochaine action, diffusion, memoire, envoi hors CoproScope.

## Retour front - CONV-2026-1687

Verdict: socle front exploitable, NO-GO produit sans owner dedie et recette
navigateur. Routes utiles: `/actions`, `/actions/{action_id}`, `/pieces`,
`/pieces/{piece_id}`, `/demandes`, `/demandes/relance`, `/chantiers`; le
template `workstreams.html` sert la route `/chantiers`.

Le premier viewport actuel de `/actions` affiche contexte, recherche, mode local
et cartes de parcours avant la paire `Registre des AG` + `Fiche decision`. Pour
`decision_action_preuve_v1`, la fiche decision doit remonter dans le premier
viewport desktop/mobile/tablette.

Fichiers candidats si owner code futur: `actions.html`,
`_actions_registry_body.html`, `_actions_reprise_actions.html`,
`_actions_reprise_syndic.html`, `pieces.html`, `piece_detail.html`,
`requests.html`, `relance_syndic.html`, `workstreams.html`, `base.html`, CSS
`styles_part_06.css` a `styles_part_12.css`. Eviter d'alourdir
`_app_fragments/part_003.pyfrag`, deja proche du seuil 600 lignes.

Risque front: les filtres `/actions?scope/status/priority` filtrent les lignes
action, mais le registre DAP complet reste largement rendu cote template. Un lot
futur doit prouver le filtrage novice voulu ou le documenter comme vue hub.

## Retour back/viewmodel local - CONV-2026-1688

`decisionops.py` produit deja `registre_decisions_actions_preuves.csv` avec
`decision_action_id`, `ag_id`, source, resolution, decision, action attendue,
responsable, echeance, preuve attendue, pieces/preuves liees, demandes liees,
travaux/factures, statut, priorite et notes.

Le viewmodel `ux.registre` expose deja items, groupes AG, selected, compteurs,
facettes, preuves, pieces, relances, historique, diffusion et memoire. Le detail
separe preuves verifiees, preuves candidates et pieces liees; `can_close` n'est
vrai que si une preuve verifiee existe.

Commande back future: stabiliser un contrat public explicite
`model.ux.decision_action_preuve_v1` ou un alias strict de `ux.registre`, avec
allowlist des champs publics, libelles humains, references opaques et aucun
chemin brut `source_file`, `raw`, `restricted`, `logs`, `private` ou secret.

## Retour QA local - CONV-2026-1689

Panier lance en lecture seule:

```text
server\.venv\Scripts\python.exe -m unittest server.tests.test_decisionops server.tests.test_ui_registre_actions server.tests.test_ui_action_detail_route server.tests.test_ui_pieces_viewmodel server.tests.test_ui_requests server.tests.test_ui_requests_route server.tests.test_ui_smoke_routes_expanded server.tests.test_ui_security_routes server.tests.test_security_no_private_sync_leaks -v
```

Resultat: 51 tests OK, 1 skip attendu. Le skip documente que le layout front
Cycle 2 `/actions` n'est pas livre dans ce perimetre et que certains libelles de
template restent une cible front dediee.

Garde-fou:

```text
server\.venv\Scripts\python.exe tools\check_code_line_limit.py
```

Resultat: OK, aucun fichier code scope ne depasse 600 lignes.

## Consolidation

Statut: AGILE-DONE - equipe agile a fini son job.

Verdict produit: NO-GO produit complet, car aucun owner code n'a ete ouvert,
aucun serveur reserve n'a ete lance et aucune capture desktop/mobile/tablette
n'a ete produite. Le cadrage est suffisamment ferme pour une commande future
bornee si Brice valide un owner code dedie.

Commande future bornee:

- livrer `decision_action_preuve_v1` sur `/actions?scope=decisions` et fiche
  `/actions/{action_id}` ou `selected=...`;
- remonter dans le premier viewport la fiche decision avec decision/source,
  action attendue, responsable, echeance, preuve attendue, etat de preuve,
  prochaine action humaine, diffusion et memoire;
- distinguer strictement preuve attendue, piece liee, preuve candidate et
  preuve verifiee;
- garder les relances en brouillon ou trace d'envoi hors CoproScope;
- relier demandes, pieces, chantiers/travaux et historique sans exposer de
  chemin brut ni de donnee privee;
- interdire en premier niveau les libelles techniques DecisionOps, SyndicOps,
  DocOps, hash, payload, vault, raw, restricted, logs, P1/P2 seuls;
- ajouter tests token, anti-fuite, no-private, line-limit, smoke et captures
  desktop/mobile/tablette avant tout GO produit.

Prochain mouvement heartbeat: ne pas rouvrir `ORD-P0-032` sans nouveau diff ou
decision Brice; choisir le prochain P0 actionnable, a priori `ORD-P0-033` /
`DEMANDES-SYNDICOPS`.
