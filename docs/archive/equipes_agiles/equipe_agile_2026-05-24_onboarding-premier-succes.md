# Equipe agile - Onboarding premier succes

Date de lancement: 2026-05-24 21:20 +02:00.
Roadmap: `RM-2026-0009`.
Chantier: `CH-20260524-212000-RM-2026-0009-onboarding-premier-succes`.
Conversation coordination: `CONV-2026-1571`.
Mode: cadrage agile lecture seule avant owner code unique.
Statut: pret a integrer.

## BOT-START

BOT-START - Coordinateur-scribe agile onboarding - 2026-05-24 21:20 +02:00.

Mission: transformer la strategie onboarding en commande UI/dev testable pour un
premier succes novice en moins de 10 minutes, sans ouvrir de patch applicatif
tant que la cible UI, les intentions, le contrat front/back et le panier QA ne
sont pas verrouilles.

UI reelle cible: `/` pour le bloc d'entree `Premier succes conseille`, avec
succes principal via `/demandes#nouvelle-demande`.

Fichiers autorises pour ce cadrage:

- `docs/equipe_agile_2026-05-24_onboarding-premier-succes.md`;
- `docs/presence_agents.md`;
- ligne gouvernail `RM-2026-0009`.

Fichiers a eviter: code applicatif, routes, templates, CSS, tests applicatifs,
serveurs, instances privees, documents bruts, derives OCR, exports bruts,
secrets, `RM-2026-0017` et serveur `CONV-2026-1525`.

Sources lues:

- `docs/strategie_onboarding.md`;
- `docs/ux_novice_p0.md`;
- `docs/audit_adequation_ux_ui_enquete_2026-05-22.md`;
- `docs/test_novice_live_8766_2026-05-21.md`;
- `docs/roadmap_backlog_central.md`;
- `docs/presence_agents.md`;
- `AGENTS.md`.

## Roles

| Role | Conversation | Statut | Sortie attendue |
|---|---|---|---|
| Coordinateur-scribe | `CONV-2026-1571` | `PRET_A_INTEGRER` | Commande onboarding consolidee. |
| Designer parcours / service | `CONV-2026-1572` / Kepler `019e5b74-b86f-70d3-88ab-95538172a61d` puis reprise locale | `CLOTURE` | Route cockpit + quatre intentions + boucle preuve-action-trace. |
| Utilisateur novice / CS entrant | `CONV-2026-1573` / James `019e5b75-caba-7b31-aaea-6567432f5f33` puis reprise locale | `CLOTURE` | GO conditionnel sur demande locale; no-go sur dev sans resultat visible. |
| Dev front lecture | `CONV-2026-1574` / Faraday `019e5b75-cb86-7942-bdaf-86980b1e8d05` puis reprise locale | `CLOTURE` | Cartographie routes/templates/CSS et owner futur sans patch. |
| Data / viewmodel lecture | `CONV-2026-1575` / Mencius `019e5b75-ccb1-7893-948d-2600e5e7b093` puis reprise locale | `CLOTURE` | Contrat `model.ux.onboarding` et trace RequestOps. |
| QA novice / privacy | `CONV-2026-1576` / Raman `019e5b75-ce96-7c01-bef5-6ceacc60cab0` puis reprise locale | `CLOTURE` | Panier QA token, privacy, mobile et resultat. |

## Point Initial

A produire: commande dev precise pour un premier succes novice, route ou surface
cible, quatre intentions, contrat `model.ux.onboarding`, criteres GO novice et
panier QA.

En dev: rien, volontairement.

En test: tests existants novice/static/security a selectionner; aucun test
applicatif tant qu'aucun code n'est modifie.

Blocages: ne pas rouvrir les chantiers `PRET_A_INTEGRER`; ne pas toucher au
serveur vivant `CONV-2026-1525`; ne pas reprendre `RM-2026-0017`.

Decisions ouvertes: route dediee ou integration sur `/`; ordre des quatre
intentions; niveau de configuration locale visible avant l'action; definition
d'un premier succes mesurable sans compte cloud.

Prochain mouvement: lancer les cinq roles lecture, consolider une commande dev
minimale, puis stopper sans patch si les collisions restent trop fortes.

## Point Coordinateur 21:32

Etat: equipe vivante declaree, retours agents attendus dans le registre
canonique. Les agents Kepler, James, Faraday, Mencius et Raman sont conserves;
les doublons lances par course locale ont ete fermes.

A produire: arbitrage final du premier succes novice et commande dev/test. La
base locale montre deux surfaces deja actionnables:

- `/documents/ajouter`: depot local, qualification confidentialite,
  rattachement point/action/preuve, retour tokenise depuis `/depot`;
- `/demandes`: creation d'une demande simple, preuve/source, diffusion,
  prochaine action et journal de relance via `/demandes/relance`.

Hypothese coordinateur initiale, avant consolidation: `/documents/ajouter`
produit la boucle la plus complete `piece -> confidentialite -> action ->
preuve -> trace`. L'arbitrage final ci-dessous retient toutefois `/demandes`
comme premier succes v1, car il ne depend pas d'un fichier local fourni.
`/documents/ajouter` reste l'intention document forte.

En dev: rien. Le fragment `part_003.pyfrag` fait deja 594 lignes et reste a
eviter pour toute suite; un chantier dev futur devra extraire/brancher via
fichier dedie ou owner unique.

En test: paniers existants reperes sans lancement de serveur:
`test_ui_document_intake_route.py`, `test_ui_requests_route.py`,
`test_ui_smoke_routes_expanded.py`, `test_ui_security_routes.py` et test
statique novice `test_ui_novice_language_static.py`.

Blocages: attendre les retours des roles canoniques ou, au prochain heartbeat,
consolider en signalant explicitement les retours manquants. Aucun code,
serveur, navigateur, instance privee, export brut ou reprise `RM-2026-0017`.

Prochain mouvement: integrer les retours designer/novice/front/data/QA si la
trace bouge; sinon produire une commande dev separee "onboarding premier
document" sans patch applicatif.

## Consolidation 21:32

Verdict: GO cadrage, NO-GO dev immediat dans le worktree principal sale.

Route primaire future: `/`, avec un bloc de premier viewport `Premier succes
conseille`. Le cockpit reste l'entree novice parce qu'il porte deja les routes
vivantes et le contexte local. Le premier succes mesurable ne doit pourtant pas
etre une simple visite du cockpit: il doit ouvrir une action reelle et produire
une trace.

Premier succes v1 recommande: creer une demande locale depuis
`/demandes#nouvelle-demande`, puis afficher le resultat `status=created` et la
ligne de registre. Cette action existe deja cote route et tests: elle ne requiert
ni fichier, ni cloud, ni serveur externe, et produit une trace RequestOps
rejouable. Les chemins `/documents/ajouter` et `/depot?intent=document` restent
l'intention document, plus forte mais dependante d'un fichier local fourni.

Les quatre intentions a afficher depuis le cockpit:

| Intention | Route cible | Premier resultat attendu |
|---|---|---|
| `Traiter une priorite` | `/actions?priority=P1` | voir pourquoi, preuve/source, prochaine action et prudence diffusion. |
| `Ajouter ou rattacher un document` | `/documents/ajouter` puis `/depot?intent=document` | depot local, qualification, confidentialite et rattachement. |
| `Demander une piece ou relancer le syndic` | `/demandes#nouvelle-demande` ou `/demandes/relance` | demande locale creee ou brouillon local prepare, non envoye automatiquement. |
| `Transmettre ou reprendre la memoire` | `/exports/passation` | apercu prudent avec blocages explicites; perf a traiter via `RM-2026-0016`. |

Boucle obligatoire sur chaque intention: pourquoi ce sujet apparait, preuve ou
source connue, action possible maintenant, qui peut voir ou recevoir le resultat,
trace gardee dans la memoire.

Microcopy retenue:

- `Rien n'est envoye automatiquement.`
- `Creer une trace locale`
- `Preuve ou source`
- `Prochaine action`
- `Prudence diffusion`
- `Trace gardee pour la passation`
- `Choisir une autre intention`

## Commande Dev Future

Commande `onboarding_first_success_v1`.

Objectif utilisateur: a la premiere ouverture locale, un membre CS novice choisit
une intention, cree ou prepare une premiere trace en moins de 10 minutes, voit
ce qui a ete cree, ce qui n'a pas ete envoye, et la prochaine etape.

UI cible: `/` pour le module d'entree; routes appelees par les CTA:
`/demandes#nouvelle-demande`, `/documents/ajouter`, `/actions?priority=P1`,
`/pieces?proof=missing`, `/exports/passation`.

Visuel de reference: `docs/assets/ux-realignement-2026-05-20/01_cockpit_realigne.svg`
pour la priorisation cockpit, et
`docs/assets/ux-ui-recherche-2026-05-24-ajout-docs/01-atelier-qualification-novice.svg`
pour la boucle document `piece -> point -> action -> preuve`.

Structure front:

- bloc premier viewport `Premier succes conseille`;
- bandeau local compacte, sans pousser l'action sous le fold;
- carte action recommandee avec les cinq lignes de boucle;
- quatre intentions scannables;
- etat resultat visible apres retour `status=created`, `depot=...` ou `sent=1`;
- etat vide qui retire les compteurs a zero des CTA prioritaires.

Owner futur recommande:

- nouveau helper `server/src/coproscope/web/viewmodels/_onboarding.py`;
- integration minimale dans le builder UX existant, sans grossir les fragments
  proches du plafond;
- template `server/src/coproscope/web/templates/overview.html`;
- CSS dedie dans un `styles_part_*.css` si le bloc a besoin de styles;
- tests `server/tests/test_ui_onboarding_first_success.py` plus regression
  `test_ui_requests_route.py`, `test_ui_document_intake_route.py`,
  `test_ui_live_ux_contract.py` et `test_security_no_private_sync_leaks.py`.

Contrat `model.ux.onboarding`:

```text
recommended.label
recommended.href
recommended.why
recommended.proof_or_source
recommended.action_label
recommended.diffusion_label
recommended.trace_label
intentions[].id
intentions[].label
intentions[].href
intentions[].result_label
last_result.kind
last_result.label
last_result.next_step
```

Champs interdits dans ce contrat: chemin local absolu, `raw`, `restricted`,
`logs`, `private`, email, telephone, token, secret, nom de fichier brut non
masque et donnees d'instance reelle.

## QA Readiness

Panier avant dev:

- verifier que `/demandes`, `/documents/ajouter`, `/depot`, `/actions?priority=P1`
  et `/exports/passation` restent tokenises quand un token est configure;
- verifier que les routes ne sortent pas de chemin prive ni de marqueur
  `raw/restricted/logs/private`;
- verifier que la creation `/demandes` masque les chemins soumis dans le
  formulaire;
- verifier que `/documents/ajouter` retourne bien depuis `/depot` avec un
  manifeste et des references opaques;
- verifier que le premier viewport du cockpit garde le CTA principal visible en
  desktop et mobile avant un GO produit.

Tests cibles quand le dev sera ouvert:

```powershell
.\server\.venv\Scripts\python.exe -m unittest server.tests.test_ui_requests_route -v
.\server\.venv\Scripts\python.exe -m unittest server.tests.test_ui_document_intake_route -v
.\server\.venv\Scripts\python.exe -m unittest server.tests.test_security_no_private_sync_leaks -v
.\server\.venv\Scripts\python.exe -m unittest server.tests.test_ui_live_ux_contract -v
.\server\.venv\Scripts\python.exe .\tools\check_code_line_limit.py
```

Limite: pas de preuve navigateur produite dans ce cycle, car aucun serveur ne
devait etre lance et le serveur `CONV-2026-1525` reste reserve.

## BOT-END

BOT-END - Coordinateur-scribe agile onboarding - 2026-05-24 21:32 +02:00.

Roadmap: `RM-2026-0009`.
Chantier: `CH-20260524-212000-RM-2026-0009-onboarding-premier-succes`.
Conversation: `CONV-2026-1571`.
Statut: `PRET_A_INTEGRER`.

Fichiers modifies: ce document, `docs/presence_agents.md`,
`docs/roadmap_backlog_central.md`.

Fichiers evites: code applicatif, routes, templates, CSS, tests applicatifs,
serveurs, instances privees, documents bruts, derives OCR, exports bruts,
secrets, port `8798`, `RM-2026-0017`.

Tests/preuves: lecture des routes, templates, viewmodels et tests cibles; pas
de serveur; `test_ui_requests_route`, `test_ui_document_intake_route` et
`test_security_no_private_sync_leaks` passent avec 23 tests OK; `git diff
--check` OK sur ce livrable, la presence et le gouvernail.

Limites: les agents canoniques inscrits a 21:25 sont introuvables dans le
contexte courant au moment de l'attente; leurs roles sont donc clotures par
reprise locale lecture seule. Un chantier dev separe reste necessaire pour
livrer `onboarding_first_success_v1`.

Prochain mouvement propose: ouvrir un owner code unique en worktree dedie si
`RM-2026-0009` devient le prochain P0 de livraison; sinon passer au prochain P0
gouvernail non bloque.

AGILE-DONE - equipe agile a fini son job

## Journal

| Heure | Acteur | Evenement | Detail |
|---|---|---|---|
| 2026-05-24 21:20 +02:00 | `CONV-2026-1571` | `BOT-START` | Cycle autonome: ouverture du cadrage onboarding premier succes sur `RM-2026-0009`, sans code, serveur, instance privee, secret, export brut ni reprise de `RM-2026-0017`. |
| 2026-05-24 21:25 +02:00 | `CONV-2026-1572`..`CONV-2026-1576` | `AGENTS_PARTIAL_LAUNCH` | Kepler lance sur le role designer. Limite de threads atteinte pour novice/front/data/QA; reprise locale lecture seule par le coordinateur, sans code, serveur, instance privee ni `RM-2026-0017`. |
| 2026-05-24 21:28 +02:00 | `CONV-2026-1573`..`CONV-2026-1576` | `DEDUP_ROLES_VIVANTS` | Registre canonique conserve James, Faraday, Mencius et Raman sur les roles novice, front, data/viewmodel et QA. Newton, Nash, Lagrange, Locke et Arendt fermes comme doublons pour ne pas dupliquer l'equipe vivante. |
| 2026-05-24 21:32 +02:00 | `CONV-2026-1571` | `COORD_POINT` | Cartographie locale sans dev: `/documents/ajouter` et `/demandes` sont actionnables; hypothese premier succes = document ajoute, qualifie et rattache; `part_003.pyfrag` a 594 lignes, donc no-go patch direct. |
| 2026-05-24 21:32 +02:00 | `CONV-2026-1571` | `AGILE_DONE` | Commande `onboarding_first_success_v1` consolidee: cockpit comme entree, premier succes via creation d'une demande locale, quatre intentions, contrat `model.ux.onboarding`, owner futur et panier QA. Aucun code, serveur, instance privee ni `RM-2026-0017`. |
| 2026-05-24 21:36 +02:00 | `CONV-2026-1571` | `VERIFY` | Verification ciblee: `test_ui_requests_route`, `test_ui_document_intake_route` et `test_security_no_private_sync_leaks` = 23 tests OK; `git diff --check` OK sur doc/presence/gouvernail. |
