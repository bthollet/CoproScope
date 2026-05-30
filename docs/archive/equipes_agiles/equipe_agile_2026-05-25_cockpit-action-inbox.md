# Equipe agile - ORD-P0-030 Cockpit action inbox

Date de lancement: 2026-05-25 02:50 +02:00.
Mode: equipe agile de cadrage produit, lecture seule, sans dev.

## BOT-START

```text
BOT-START - Coordinateur-scribe agile - 2026-05-25 02:50 +02:00
Roadmap: RM-2026-0003 / RM-2026-0006 / RM-2026-0009
Ordre: ORD-P0-030 / COCKPIT-ACTION-INBOX
Chantier: CH-20260525-025000-RM-2026-0003-cockpit-action-inbox
Conversation: CONV-2026-1672
Role: Coordinateur-scribe agile
Mission: cadrer le prochain lot P0 actionnable apres Comptes guide AG: ouvrir CoproScope, comprendre 3 a 5 sujets urgents, puis choisir une prochaine action sans documentation externe.
Ownership modifiable: docs/equipe_agile_2026-05-25_cockpit-action-inbox.md, docs/presence_agents.md, trace append-only docs/roadmap_backlog_central.md et heartbeat relance-equipe-agile-gouvernail-autonome.
Fichiers a eviter: code applicatif, tests applicatifs, templates, CSS, worktree principal sale, lots PRET_A_INTEGRER sans decision d'integration, instances privees, documents bruts, OCR/logs, exports bruts, secrets, serveurs locaux, push GitHub, RM-2026-0017 / ORD-P0-990, reouverture ORD-P0-020/021 sans nouveau diff ou decision Brice.
Dernier point lu: AGENTS.md, protocoles equipe agile/orchestration/roadmap/presence, consignes interconversations, gouvernail, presence, mission ORD-P0-020 cloturee, onboarding premier succes et sources UX cockpit.
Tests/preuves attendus: retours designer/novice/front/back/QA, GO/NO-GO novice, cartographie de la surface cockpit actuelle, contrat action inbox borne, panier security/privacy/no-private/line-limit/smoke/captures futures.
Risque de collision: ORD-P0-021 reste PRET_A_INTEGRER sans decision; onboarding premier succes est deja integre et ne doit pas etre relance. Ce lot reste borne au cockpit/action inbox et ne lance aucun dev.
Lease ownership: jusqu'au 2026-05-25 04:50 +02:00.
Prochaine action: lancer les roles designer, novice, front, back/viewmodel et QA en lecture seule, puis consolider une commande future bornee ou un NO-GO dev.
```

## Etat initial

- A tester maintenant: pas de recette live; aucun serveur reserve.
- En dev maintenant: aucun dev; aucun owner code ouvert.
- En enquete maintenant: roles a lancer en lecture seule sur le cockpit `/`.
- Commande prete: non; l'objectif est de borner la commande `cockpit_action_inbox_v1`.
- Comparaison visuels enquete: reference obligatoire
  `docs/assets/etude-utilisateurs/cockpit-conseil-syndical.png`.
- Agents idle a relancer: designer, novice, front, back/viewmodel et QA.
- Decision requise: aucune decision Brice immediate. Un owner code futur doit
  etre explicite et en worktree dedie.
- Prochain mouvement: lancer les roles et recuperer les retours.
- Tests/preuves: `git diff --check` documentaire; aucun test applicatif tant
  qu'aucun code n'est livre.

## Roles

| Conversation | Role | Statut | Agent |
|---|---|---|---|
| `CONV-2026-1672` | Coordinateur-scribe agile | CLOTURE | local |
| `CONV-2026-1673` | Designer service / facilitateur | CLOTURE | Confucius `019e5ca1-8299-7c83-a9d7-9caa76cde0bd` |
| `CONV-2026-1674` | Utilisateur novice / membre CS | CLOTURE | Dalton `019e5ca1-82fd-79c1-b1d4-b83332a1a504` |
| `CONV-2026-1675` | Dev front lecture seule | CLOTURE | Arendt `019e5ca1-837b-7b30-a9c3-81e0adcadc87` |
| `CONV-2026-1676` | Dev back / viewmodel lecture seule | CLOTURE | local, reprise faute capacite threads |
| `CONV-2026-1677` | QA privacy / regression | CLOTURE | local, reprise faute capacite threads |

## Contraintes produit

- Le cockpit doit montrer 3 a 5 sujets `A faire maintenant`, pas une liste
  decorative de compteurs.
- Chaque carte doit afficher: sujet, preuve ou source, prochaine action et
  prudence de diffusion.
- Le bloc `Premier succes conseille` deja integre reste un acquis, pas le
  perimetre principal du lot.
- Les files specialisees de reprise (`/actions?priority=P1`,
  `/actions?scope=syndic`, `/actions?status=a_demander`,
  `/pieces?proof=missing`) relevent de `ORD-P0-031`; ce lot doit seulement
  dire comment le cockpit les priorise et les ouvre.
- Rien ne doit suggerer un envoi automatique, une diffusion publique, une
  validation juridique/comptable ou une exposition de bruts.
- Les donnees de cadrage restent fictives, publiques de test ou deja
  anonymisees.

## Retour designer - CONV-2026-1673

Verdict: GO design pour le blueprint `ORD-P0-030`. NO-GO dev immediat tant que
novice, front, back/viewmodel et QA n'ont pas confirme le contrat, l'owner code
dedie, la cible UI reelle `/` et les tests/captures futures.

Le cockpit doit devenir une page `Aujourd'hui au conseil syndical`, pas un mur
de compteurs. Premier viewport recommande:

- bandeau compact: coffre actif, role, exercice, derniere verification et
  mention `Local - rien n'est envoye automatiquement`;
- H1 `A faire maintenant`;
- sous-titre `3 a 5 sujets a traiter, avec preuve, action et prudence de
  diffusion`;
- grille de 3 a 5 cartes urgentes visibles sans scroller sur desktop et
  empilees proprement sur mobile;
- bloc `Premier succes conseille` conserve comme acquis, mais il ne pilote pas
  ce lot.

Cartes urgentes proposees:

| Sujet | Preuve/source affichee | Prochaine action | Prudence diffusion |
|---|---|---|---|
| Relance syndic en retard | Demande ou action ouverte, echeance depassee, derniere relance | Preparer la relance / ouvrir la file syndic | Brouillon CS, aucun envoi automatique |
| Piece manquante | Decision, compte ou dossier lie sans preuve locale | Demander la piece / ouvrir pieces manquantes | Ne pas diffuser tant que la preuve manque |
| Compte a verifier avant AG | Point P1/P2 ComptaScope, facture ou annexe attendue | Preparer la question syndic | Question de travail, pas conclusion comptable |
| Decision sans preuve de cloture | Resolution/action suivie sans preuve de fin | Rattacher ou demander une preuve | Statut incomplet visible avant partage |
| Diffusion a revoir | Action, piece ou synthese avec restriction ou doute | Ouvrir la revue de diffusion | Partage bloque tant que destinataire non choisi |

Ordre obligatoire dans chaque carte: sujet, raison en une phrase,
preuve/source, bouton d'action, badge de prudence. Jargon premier niveau a
eviter: `DocOps`, `SyndicOps`, `PrivacyOps`, `vault`, `hash`.

Limite avec `ORD-P0-031`: ce lot choisit seulement quoi montrer en haut du
cockpit et vers quelle file ouvrir. Les vues file/etat vide dediees, lignes,
filtres, statuts et preuves attendues par ligne relevent du lot suivant.

Commande design future: `cockpit_action_inbox_v1` sur `/`, read model public
de 3 a 5 cartes maximum avec `title`, `reason`, `source_label`, `source_kind`,
`action_label`, `action_href`, `diffusion_caution`, `priority` et
`empty_state`. Liens token-safe; aucun bouton ne promet envoi, validation
juridique/comptable, diffusion publique ou ouverture de brut.

## Retour novice - CONV-2026-1674

Verdict: GO cadrage, NO-GO dev immediat.

En moins d'une minute, un membre CS comprend les familles de sujets: actions en
retard, pieces manquantes, demandes syndic, echeances AG et alertes/risques.
Il ne comprend pas encore assez bien les 3 a 5 sujets urgents eux-memes, car les
cartes actuelles restent surtout `compteur + categorie + sous-titre`, pas
`sujet + preuve/source + prochaine action + prudence diffusion`.

Libelles acceptables:

- `A faire maintenant`;
- `Actions en retard`;
- `Pieces manquantes`;
- `Demandes syndic`;
- `Preuve ou source`;
- `Prochaine action`;
- `Prudence diffusion`;
- `Conseil syndical seulement`;
- `Rien n'est envoye automatiquement`;
- `Trace gardee pour la passation`;
- `A verifier avant partage`;
- `Diffusion bloquee`.

Mots dangereux:

- `urgent` sans expliquer pourquoi;
- `alerte` sans preuve/source;
- `valider`, `OK`, `clore` sans consequence claire;
- `envoyer`, `publier`, `partager` si rien n'est vraiment envoye;
- `exporter` si c'est seulement un apercu;
- `P1`, `P2`, `sync`, `vault`, `raw`, `restricted`, `logs`, `private`;
- `piece documentaire` repete comme titre principal;
- `demande syndic` si la cible est en fait une file d'actions.

Condition novice avant dev: une commande future `cockpit_action_inbox_v1` doit
contenir 3 a 5 cartes exemple, chacune au format `Sujet`, `Pourquoi
maintenant`, `Preuve ou source`, `Prochaine action`, `Prudence diffusion`.
Le bloc `Premier succes conseille` reste acquis mais ne remplace pas l'action
inbox. Les cartes ouvrent les files specialisees sans envoi automatique, sans
brut, sans chemin local, sans donnee privee et avec une recette navigateur
desktop/mobile prevue.

## Retour front - CONV-2026-1675

Verdict: GO cadrage front, NO-GO dev immediat dans ce fil. Aucun fichier
modifie, aucun serveur lance, aucun test execute par l'agent.

Surface actuelle:

- route `/` declaree dans
  `server/src/coproscope/web/_app_fragments/part_003.pyfrag`, qui rend
  `server/src/coproscope/web/templates/overview.html`;
- bloc `Premier succes conseille` hard-code dans `overview.html`, juste apres
  l'intro, sans consommer un `model.ux.onboarding` dedie;
- `model.ux.cockpit.now` existe dans
  `server/src/coproscope/web/viewmodels/_ux_model.py` avec `why`, `proof`,
  `action`, `diffusion` et `source`, mais le template n'affiche pas ces items
  comme cartes principales;
- `/` affiche surtout `summary_cards` sous forme de compteurs dans `A traiter`;
- `base.html` porte une navigation hard-codee; `ux.shell.nav_sections` existe
  mais n'est pas utilise par le template;
- helpers token existants: `_token_suffix`, `_url_with_token`, `ui_token_param`
  et macros `token_href`; vigilance sur les ancres, notamment
  `/demandes?token=...#nouvelle-demande`;
- CSS cockpit/cards dans `styles_part_05.css`, mobile dans `styles_part_06.css`.

Risques front:

- gate `ORD-P0-030` non rempli visuellement: les 3 a 5 sujets existent en
  modele mais ne sont pas visibles comme cartes sujet/preuve/action/diffusion;
- first viewport: topbar, contexte, intro, onboarding et compteurs peuvent
  pousser les vraies actions sous le pli;
- responsive a verifier en `1440x900`, `1366x768` et `390x844`;
- `part_003.pyfrag` est a 597 lignes et `document_intake_view.py` a 587 lignes:
  ne rien ajouter dedans;
- aucune nouvelle route n'est necessaire pour ce lot, ce qui evite les
  catch-all de `part_004.pyfrag`.

Commande front future bornee:

```text
Commande: cockpit_action_inbox_v1

Objectif:
Sur `/`, remplacer le bloc compteur `A traiter` par 3 a 5 cartes issues de
`model.ux.cockpit.now`, chacune affichant sujet, pourquoi, preuve/source,
prochaine action et prudence diffusion. Conserver le bloc `Premier succes
conseille`, mais le compacter si le first viewport masque les cartes urgentes.

Fichiers modifiables probables:
- server/src/coproscope/web/templates/overview.html
- server/src/coproscope/web/static/styles.css
- server/src/coproscope/web/static/styles_part_14.css
- server/tests/test_ui_cockpit_action_inbox.py

Fichiers a eviter:
- server/src/coproscope/web/_app_fragments/part_003.pyfrag
- server/src/coproscope/web/document_intake_view.py
- routes/catch-all, serveur local, instances privees, exports bruts, secrets.

Tests futurs:
server.tests.test_ui_cockpit_action_inbox
server.tests.test_ui_onboarding_first_success
server.tests.test_ui_cockpit
server.tests.test_ui_smoke_routes_expanded
server.tests.test_ui_security_routes
server.tests.test_security_no_private_sync_leaks
server.tests.test_code_line_limit
tools/check_code_line_limit.py
git diff --check
captures desktop/mobile/tablette sur port reserve.
```

## Retour back/viewmodel - CONV-2026-1676

Verdict: contrat public deja partiellement present. Le role n'a pas pu etre
lance comme sub-agent faute de capacite; reprise locale par le coordinateur,
sans patch code.

Surface lue:

- `server/src/coproscope/web/viewmodels/_dashboard.py`;
- `server/src/coproscope/web/viewmodels/_ux_model.py`;
- `server/src/coproscope/web/viewmodels/_summaries.py`;
- `server/src/coproscope/web/viewmodels/_actions.py`;
- `server/src/coproscope/vault/public_actions_read_model.py`;
- `server/tests/test_ui_cockpit.py`;
- `server/tests/test_public_read_models.py`.

Contrat existant utile: `model.ux.cockpit.now[]`.

Champs existants et deja testes:

- `id`, `kind`, `title`, `priority`, `status`, `status_label`, `tone`, `lane`;
- `why`;
- `proof.state`, `proof.label`, `proof.refs`;
- `action.label`, `action.kind`, `action.owner`;
- `diffusion.status`, `diffusion.label`, `diffusion.reason`;
- `memory.timeline_ref`, `memory.handover_note`, `memory.pack_section`;
- `href`;
- `source.module`, `source.object_id`.

Commande back future: formaliser `model.ux.cockpit_action_inbox_v1` ou aliaser
explicitement `model.ux.cockpit.now` comme source UI de ce lot. Le read model
doit rester une allowlist publique issue de `action_items`, pieces manquantes,
decisions, incidents, confidentialite et comptes, sans exposer chemins,
payloads, fichiers sources, OCR brut, logs, tokens ou donnees privees.

Selection future recommandee:

- maximum 5 cartes;
- priorite: bloque / P1 / a_demander / preuve manquante / diffusion bloquee;
- de-duplication par sujet source;
- fallback empty state actionnable si aucune carte;
- champs humains `reason`, `source_label`, `action_label`,
  `diffusion_caution` prets pour rendu direct.

Tests back futurs: etendre `server.tests.test_ui_cockpit` ou creer
`server.tests.test_ui_cockpit_action_inbox` pour verifier 3 a 5 cartes,
champs obligatoires, hrefs locaux, absence de marqueurs interdits et empty
state utile.

## Retour QA - CONV-2026-1677

Verdict: GO technique local sur tests existants, NO-GO produit complet sans
recette navigateur live et captures desktop/mobile/tablette. Le role n'a pas
pu etre lance comme sub-agent faute de capacite; reprise locale par le
coordinateur, sans patch code.

Preuves executees:

```text
python tools/check_code_line_limit.py
OK: no scoped code file exceeds 600 lines.

server\.venv\Scripts\python.exe -m unittest server.tests.test_ui_cockpit server.tests.test_ui_onboarding_first_success server.tests.test_ui_security_routes server.tests.test_security_no_private_sync_leaks -v
18 tests OK.
```

Panier QA futur si un owner code touche `/`:

- token: `/`, liens internes, ancres et routes cible conservent le token et
  font 403 sans token configure;
- action inbox: 3 a 5 cartes maximum, pas seulement compteurs, chacune avec
  sujet, pourquoi maintenant, preuve/source, prochaine action et prudence
  diffusion;
- anti-fuite: aucun chemin local, `file://`, `raw`, `restricted`, `logs`,
  `private`, secret, email, telephone, IBAN/RIB, OCR brut ou export brut;
- anti-jargon: pas de `DocOps`, `SyndicOps`, `PrivacyOps`, `vault`, `hash`,
  `P1` ou `P2` seuls dans le premier niveau;
- non-envoi: aucun bouton ne pretend envoyer une relance, publier un document
  ou diffuser un export;
- responsive: captures `1440x900`, `1366x768`, `390x844`, plus tablette si
  recette complete; verifier que les cartes urgentes restent visibles sans
  chevauchement;
- line-limit et smoke: `test_ui_cockpit_action_inbox`, cockpit, onboarding,
  smoke routes, security, no-private, code line-limit et `git diff --check`.

Limite QA: aucun serveur reserve, aucune capture navigateur et aucune recette
utilisateur live pendant ce lot.

## Consolidation ORD-P0-030

Verdict equipe: `AGILE-DONE - equipe agile a fini son job`.

- A tester maintenant: pas de serveur live reserve; tests unitaires cibles OK.
- En dev maintenant: aucun dev ouvert; aucun patch code.
- En enquete maintenant: tous les roles canoniques sont clotures.
- Commande prete: oui, comme commande future bornee, pas executee.
- Comparaison visuels enquete: le lot reprend
  `docs/assets/etude-utilisateurs/cockpit-conseil-syndical.png`.
- Agents idle a relancer: aucun sans nouveau diff ou decision d'owner code.
- Decision requise: Brice doit decider explicitement s'il veut une reprise code
  dediee du cockpit; sinon le heartbeat passe au prochain `ORD-*`
  actionnable.
- Prochain mouvement: prochain heartbeat = lire la file `ORD-*` et choisir le
  prochain P0 actionnable, probablement `ORD-P0-031` si aucune integration
  prioritaire n'est decidee, en excluant les lots `PRET_A_INTEGRER` sans
  decision d'integration et les lots `AGILE-DONE` sans nouveau diff.
- Tests/preuves: `test_ui_cockpit` + onboarding + security/no-private 18 OK,
  `tools/check_code_line_limit.py` OK, `git diff --check` documentaire a
  lancer.

Commande future bornee:

```text
Roadmap/chantier:
RM-2026-0003 / RM-2026-0006 / RM-2026-0009 / nouveau CH owner code dedie a
creer si Brice valide.

Objectif:
Stabiliser le cockpit `/` comme action inbox novice: ouvrir CoproScope,
comprendre 3 a 5 sujets urgents et choisir une prochaine action.

UI cible:
Premier viewport: bandeau local compact, H1 `A faire maintenant`, 3 a 5 cartes
issues de `model.ux.cockpit.now` ou `model.ux.cockpit_action_inbox_v1`.
Chaque carte affiche `Sujet`, `Pourquoi maintenant`, `Preuve ou source`,
`Prochaine action` et `Prudence diffusion`.

Limite:
`ORD-P0-030` choisit et rend les cartes cockpit. Les files detaillees
`/actions?priority=P1`, `/actions?scope=syndic`, `/actions?status=a_demander`
et `/pieces?proof=missing` restent le lot `ORD-P0-031`.

Front:
Modifier surtout `overview.html` et CSS dedie. Eviter `part_003.pyfrag` et
`document_intake_view.py`. Ne pas ajouter de route.

Back/viewmodel:
Formaliser une allowlist publique de 3 a 5 cartes depuis les action items et
projections publiques existantes. Champs: title, reason, source_label,
source_kind, action_label, action_href, diffusion_caution, priority,
empty_state.

Garde-fous:
Token conserve, aucune donnee privee, aucun brut, aucun chemin local, aucun
envoi automatique, aucun jargon technique en premier niveau, aucun P1/P2 seul,
aucune conclusion juridique/comptable.

Tests:
test_ui_cockpit_action_inbox, test_ui_cockpit,
test_ui_onboarding_first_success, test_ui_smoke_routes_expanded,
test_ui_security_routes, test_security_no_private_sync_leaks,
test_code_line_limit, tools/check_code_line_limit.py, git diff --check,
captures desktop/mobile/tablette sur port reserve si recette live demandee.
```

## Sources de decision

- `docs/roadmap_backlog_central.md`
- `docs/presence_agents.md`
- `docs/roadmap_produit_fini_visuels_enquete.md`
- `docs/audit_adequation_ux_ui_enquete_2026-05-22.md`
- `docs/backlog_produit_fini_refonte_ux.md`
- `docs/commandes_reprise_live_8766.md`
- `docs/test_novice_live_8766_2026-05-21.md`
- `docs/equipe_agile_2026-05-24_onboarding-premier-succes.md`
- `docs/equipe_agile_2026-05-24_onboarding-first-success-dev.md`

## Journal

| Horodatage | Conversation | Evenement | Trace |
|---|---|---|---|
| 2026-05-25 02:50 +02:00 | `CONV-2026-1672` | `START_AGILE_COCKPIT_ACTION_INBOX` | `ORD-P0-020` est `AGILE-DONE`; `ORD-P0-021` est saute car PRET_A_INTEGRER sans decision d'integration. Nouveau chantier P0 ouvert sur `ORD-P0-030` en lecture/cadrage uniquement, sans code ni serveur. |
| 2026-05-25 02:50 +02:00 | `CONV-2026-1673`..`CONV-2026-1677` | `ROLES_RESERVED_COCKPIT_ACTION_INBOX` | Designer, novice, front, back/viewmodel et QA reserves en lecture seule; aucun code, serveur, instance privee, document brut, export brut, secret, push GitHub ou `RM-2026-0017`. |
| 2026-05-25 02:51 +02:00 | `CONV-2026-1673`..`CONV-2026-1675` | `AGENTS_LAUNCH_PARTIAL_COCKPIT_ACTION_INBOX` | Designer Confucius, novice Dalton et front Arendt lances en lecture seule; back/viewmodel et QA restent reserves faute de capacite de threads. |
| 2026-05-25 02:52 +02:00 | `CONV-2026-1673` | `DESIGNER_RETURN_COCKPIT_ACTION_INBOX` | Confucius cloture: GO design; cockpit `Aujourd'hui au conseil syndical`, 3 a 5 cartes urgentes, preuve/source, action, prudence diffusion; `ORD-P0-031` garde les files detaillees. |
| 2026-05-25 02:53 +02:00 | `CONV-2026-1674` | `NOVICE_RETURN_COCKPIT_ACTION_INBOX` | Dalton cloture: GO cadrage, NO-GO dev immediat; les familles sont comprehensibles mais les cartes actuelles ne disent pas encore assez `sujet`, `pourquoi`, `preuve`, `action`, `diffusion`. |
| 2026-05-25 02:54 +02:00 | `CONV-2026-1675` | `FRONT_RETURN_COCKPIT_ACTION_INBOX` | Arendt cloture: `model.ux.cockpit.now` existe avec `why/proof/action/diffusion/source`, mais `overview.html` rend surtout `summary_cards`; futur patch = remplacer/resserrer `A traiter`, ne pas toucher `part_003.pyfrag`. |
| 2026-05-25 02:55 +02:00 | `CONV-2026-1676` | `BACK_LOCAL_RETURN_COCKPIT_ACTION_INBOX` | Reprise locale faute de thread: contrat existant `model.ux.cockpit.now` exploitable; future allowlist `cockpit_action_inbox_v1` ou alias explicite, 3 a 5 cartes publiques, champs interdits consolides. |
| 2026-05-25 02:55 +02:00 | `CONV-2026-1677` | `QA_LOCAL_RETURN_COCKPIT_ACTION_INBOX` | Reprise locale faute de thread: line-limit OK, cockpit/onboarding/security/no-private 18 tests OK; NO-GO produit complet sans recette navigateur et captures. |
| 2026-05-25 02:56 +02:00 | `CONV-2026-1672`..`CONV-2026-1677` | `AGILE_DONE_COCKPIT_ACTION_INBOX` | Equipe cloturee sans dev: commande future `cockpit_action_inbox_v1` prete pour owner code dedie si Brice valide; aucun code, serveur, instance privee, export brut, secret, push GitHub ni `RM-2026-0017`. |
