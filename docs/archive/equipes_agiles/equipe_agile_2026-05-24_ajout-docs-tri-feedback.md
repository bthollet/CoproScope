# Equipe agile - ajout documents + tri feedback DocOps

Date de lancement: 2026-05-24 10:46 +02:00.
Roadmap principale: `RM-2026-0003`.
Roadmap associee: `RM-2026-0029`.
Chantier: `CH-20260524-104614-RM-2026-0003-ajout-docs-tri-feedback`.
Conversation coordination: `CONV-2026-1519`.
Mode: equipe agile gouvernail, cadrage UI reelle avant dev.
Statut: cloture - blocage leve par integration DocOps separee, suite reprise.

## BOT-START

BOT-START - Coordinateur-scribe agile - 2026-05-24 10:46 +02:00

Roadmap: `RM-2026-0003` avec rattachement `RM-2026-0029`
Chantier: `CH-20260524-104614-RM-2026-0003-ajout-docs-tri-feedback`
Conversation: `CONV-2026-1519`
Role: Coordinateur-scribe agile
Mission: lancer une equipe agile guidee par le gouvernail pour transformer le socle P0 `ajout-docs novice + tri feedback humain` en chantier executable, sans dupliquer une equipe vivante et sans toucher a `RM-2026-0017`.
Ownership modifiable: ce document, `docs/presence_agents.md`, lignes de gouvernail liees a `RM-2026-0003` et `RM-2026-0029`.
Fichiers a eviter: code applicatif avant GO novice/commande stabilisee, instances privees, secrets, exports bruts, serveurs locaux, `RM-2026-0017` bloque, routes/templates/viewmodels sans owner unique.
Passerelle/registre de trace: ce document, `docs/presence_agents.md`, `docs/roadmap_backlog_central.md`.
Dernier point lu: `AGENTS.md`, `docs/orchestration_agents.md`, `docs/protocole_equipe_agile_agents.md`, `docs/protocole_roadmap_presence_agents.md`, `docs/consignes_bots_interconversations.md`, gouvernail et presence au 2026-05-24 10:46 +02:00.
Tests/preuves attendus: commande UI reelle ciblee, GO/NO-GO novice, cartographie front/back, plan QA anti-fuite; aucun test applicatif tant que le dev n'est pas ouvert.
Risque de collision: plusieurs recherches UX/UI recentes sont cloturees; aucune equipe agile vivante n'est visible sur `RM-2026-0003` / `RM-2026-0029`; `RM-2026-0017` reste bloque et exclu.
Lease ownership: 2026-05-24 12:46 +02:00.
Prochaine action: lancer les roles de cadrage et garder les devs en lecture jusqu'au GO novice.

## UI Cible

- Route existante a consolider: `/documents/ajouter`.
- Route prototype proposee: `/documents/tri-feedback`.
- Reference UX: recherches ajout-docs du 2026-05-24, commande `docs/commandes/commande_interface_tri_docops_feedback_2026-05-24.md`.
- Gate avant dev: confirmer que `Reserve CS`, motifs fermes v1 et pages sensibles avant derive diffusable s'articulent avec le tri feedback sans confusion novice.

## Roles

| Role | Conversation | Statut | Ownership |
|---|---|---|---|
| Coordinateur-scribe | `CONV-2026-1519` | `EN_COURS` | Registres et synthese de mission. |
| Designer service / facilitateur | `CONV-2026-1520` / Pascal `019e592c-5681-7881-9d89-004c87255134` | `CLOTURE` | GO designer conditionnel, commande UI et questions ouvertes consolidees. |
| Utilisateur novice | `CONV-2026-1521` / Leibniz `019e592c-56ea-72a1-9a80-af3a74584c12` | `CLOTURE` | GO novice conditionnel, no-go livraison et libelles consolides. |
| Dev front | `CONV-2026-1522` / Raman `019e592c-5771-7111-890e-38138d96001c` | `CLOTURE` | Cartographie templates/CSS/tests consolidee; aucun patch. |
| Dev back / viewmodel | `CONV-2026-1523` / Singer `019e592c-5826-7a53-8c3f-a1fb50fa2490` | `CLOTURE` | Cartographie routes/helpers/registres/tests consolidee; aucun patch. |
| QA securite / regression | `CONV-2026-1524` / Copernicus `019e592c-58ee-71b0-b8fe-f230816c7fae` | `CLOTURE` | Panier QA anti-fuite et criteres GO/NO-GO consolides. |
| Facilitateur ownership / worktree | `CONV-2026-1546` / Gauss `019e5b2d-a18b-7620-8e9a-d1424a708c17` | `CLOTURE` | Recommande un worktree dedie propre; no-go patch dans le worktree principal sale. |
| Dev front relance | `CONV-2026-1547` / Chandrasekhar `019e5b2d-a3f6-7f90-92c2-03501a14eca9` | `CLOTURE` | Confirme route avant `/documents/{doc_id}`, `part_003.pyfrag` sale et proche du plafond, template/CSS/test dedies. |
| Dev back / viewmodel relance | `CONV-2026-1548` / Avicenna `019e5b2d-a49e-7263-83e0-b52b43190124` | `CLOTURE` | Isole route/view/exports dans `docops_feedback_*`, mais branchement route bloque dans le worktree principal. |
| QA privacy / novice relance | `CONV-2026-1549` / Hooke `019e5b2d-a597-7b43-8242-b0808f909232` | `CLOTURE` | NO-GO novice pour dev immediat; test cible `test_ui_docops_feedback_route.py`. |

## Point Court

A produire: worktree dedie propre ou arbitrage explicite avant tout dev, commande dev unifiee `ajout-docs + tri-feedback`, test cible et criteres QA.

En dev: rien. Le worktree principal reste en NO-GO dev.

En test: aucun test applicatif lance; le prochain test a produire est `server/tests/test_ui_docops_feedback_route.py`.

Blocages: `part_003.pyfrag` sale et proche du plafond 600 lignes; `/documents/tri-feedback` doit etre branche avant `/documents/{doc_id}`; `part_001.pyfrag`, intake, CSS et tests proches sont deja sales.

Prochain mouvement: creer un worktree dedie propre pour le prototype `docops_feedback_*`, ou garder le chantier bloque.

## Decision Premiere Passe

Verdict: equipe agile lancee et cadrage termine. `GO conditionnel` pour preparer
un prototype `/documents/tri-feedback`, mais `NO-GO dev immediat` dans ce
passage.

Raisons du no-go dev immediat:

- la commande doit fixer noir sur blanc `Reserve conseil syndical` avec motif
  obligatoire, `Bloque` avec justification, et pages sensibles avant derive
  diffusable;
- `/documents/tri-feedback` est encore une route proposee, pas une UI livree;
- le worktree est deja sale sur plusieurs fichiers front/back proches;
- `part_003.pyfrag` et `document_intake_view.py` sont proches du plafond 600
  lignes et ne doivent pas recevoir de logique metier tri-feedback.

## Commande UI Consolidee

Parcours:

1. `/documents/ajouter` reste le guide novice pour 1 a 3 documents.
2. A partir de 4 documents, proposer `Passer en tri de lot`.
3. A partir de 10 documents ou depuis une file DocOps, recommander
   `/documents/tri-feedback`, sans bascule automatique.
4. Apres tri feedback, permettre le retour vers `/documents/ajouter?source=inbox`
   pour completer un document sensible ou incomplet.

Structure `/documents/tri-feedback`:

- bandeau: `Documents`, `A corriger`, `A masquer`, `Reserve CS`, `Bloques`,
  `A decider`, `Modifications non enregistrees`;
- colonnes: `Ouvert coproprietaires`, `A masquer avant partage`, `Reserve
  conseil syndical`, `Ne pas partager`, `A decider plus tard`;
- carte document reduite: `doc_id`, type propose, confidentialite proposee,
  raison courte DocOps, confiance si disponible, etat local, selecteur type,
  selecteur visibilite, motif obligatoire si restriction;
- actions: `Enregistrer les corrections`, `Revoir avant application`, `Exporter
  le registre local`, `Retour au guide`.

Libelles obligatoires:

- `/documents/ajouter`: `Le fichier reste local. Rien n'est partage.`
- `/documents/tri-feedback`: `Corriger les propositions DocOps`.
- CTA principal ajout: `Enregistrer localement`.
- CTA principal tri: `Enregistrer les corrections`.
- Export: `Exporter le registre local`.

## Regles Produit A Verrouiller

- `Reserve conseil syndical` n'est jamais un reflexe de prudence: motif
  obligatoire.
- `Bloque` n'est pas `je ne sais pas`: justification obligatoire.
- `A masquer avant partage` impose motif et pages/ranges avant toute derive
  diffusable.
- `A decider plus tard` ne peut jamais produire de diffusion.
- Un PDF avec une page sensible ne devient jamais diffusable brut.
- DocOps propose; l'humain confirme. L'UI ne doit jamais suggerer une validation
  juridique automatique.

Motifs fermes v1:

- `donnees personnelles`
- `RIB ou coordonnees bancaires`
- `impayes nominatifs`
- `contentieux en cours`
- `salarie ou prestataire`
- `negociation ou strategie`
- `pages mixtes`
- `qualite ou OCR insuffisant`
- `autre motif prudent a requalifier`

## Ownership Futur Recommande

Back / integration:

- `server/src/coproscope/web/docops_feedback_route.py`
- `server/src/coproscope/web/docops_feedback_view.py`
- `server/tests/test_ui_docops_feedback_route.py`
- branchement minimal dans `server/src/coproscope/web/_app_fragments/part_003.pyfrag`
  ou fragment route actuel, route exacte `/documents/tri-feedback` avant
  `/documents/{doc_id}`.

Front:

- `server/src/coproscope/web/templates/docops_feedback.html`
- eventuellement `server/src/coproscope/web/static/styles_part_13.css`
- eventuellement l'import dans `server/src/coproscope/web/static/styles.css`
- assertions HTML dans `server/tests/test_ui_docops_feedback_route.py`

Fichiers a eviter sauf owner explicite:

- `server/src/coproscope/web/viewmodel.py`
- `server/src/coproscope/web/depot.py`
- `server/src/coproscope/web/document_intake_view.py`
- `server/src/coproscope/web/document_intake_route.py`
- `server/src/coproscope/web/viewmodels/_source_models.py`
- passation et read models publics

## Modele Minimal

Registre local propose: `registers/registre_feedback_docops.csv`.

Champs minimaux:

`feedback_id`, `session_id`, `doc_id`, `sha256`, `document_type_before`,
`document_type_after`, `privacy_before`, `privacy_after`, `justification`,
`reviewer`, `reviewed_at`, `source`, `apply_status`, `apply_error`.

Exports locaux proposes:

- `outputs/reports/docops_feedback_tri.csv`
- `outputs/reports/docops_feedback_tri.json`
- routes tokenisees `/exports/docops-feedback-tri.csv` et
  `/exports/docops-feedback-tri.json`.

Ne jamais projeter: `original_path`, `file_name`, `text_path`, contenu brut,
OCR brut, table de correspondance, chemins locaux, secrets, exports bruts.

## Panier QA

Tests obligatoires si dev ouvert:

- token obligatoire sur GET/POST `/documents/tri-feedback` et exports;
- aucune fuite HTML, erreur, CSV ou JSON: chemin local, `file://`, `raw`,
  `restricted`, `logs`, `private`, nom prive, OCR brut, secret, mapping de
  biffage;
- refus serveur pour `doc_id`, `sha256`, type, confidentialite, reviewer ou
  justification invalides;
- `Reserve CS` et `Bloque` refuses sans justification;
- `A masquer avant partage` refuse tout derive diffusable sans pages/ranges et
  motif;
- export CSV/JSON de corrections sans fuite;
- regression `/documents/ajouter`;
- garde-fou 600 lignes.

Commandes probables apres patch:

```powershell
.\server\.venv\Scripts\python.exe .\tools\check_code_line_limit.py
cd .\server
.\.venv\Scripts\python.exe -m unittest tests.test_ui_docops_feedback_route -v
.\.venv\Scripts\python.exe -m unittest tests.test_ui_document_intake tests.test_ui_document_intake_route tests.test_ui_security_routes tests.test_security_no_private_sync_leaks tests.test_code_line_limit -v
```

## Prochaine Relance

La heartbeat doit reprendre ce chantier sans dupliquer les roles clotures.
Premier geste: auditer `git status --short` et les fichiers signales comme
sales. Si les collisions sont acceptables, ouvrir un owner code unique sur le
perimetre dedie `docops_feedback_*` + test dedie. Sinon marquer `BLOQUE` et
demander arbitrage avant patch.

## Audit Collision

Audit du 2026-05-24 10:56 +02:00:

- les nouveaux fichiers recommandes sont libres: `docops_feedback_route.py`,
  `docops_feedback_view.py`, `templates/docops_feedback.html`,
  `static/styles_part_13.css`, `tests/test_ui_docops_feedback_route.py`;
- le branchement route minimal n'est pas libre: `_app_fragments/part_003.pyfrag`
  est deja modifie et proche du plafond 600 lignes;
- `_app_fragments/part_001.pyfrag` est deja modifie et contient les imports
  d'intake;
- `document_intake_view.py`, `templates/document_intake.html`,
  `static/styles_part_12.css`, `viewmodels/_source_models.py`, `depot.py` et
  les tests intake/security sont deja modifies;
- `document_intake_route.py` est non suivi, donc probablement un travail local
  recent non integre;
- ouvrir le code maintenant imposerait de toucher un fichier sensible sale pour
  placer `/documents/tri-feedback` avant `/documents/{doc_id}`.

Decision: `BLOQUE`. Ne pas ouvrir l'owner code tant que Brice ou le
coordinateur n'a pas tranche entre:

1. integrer/nettoyer le worktree existant;
2. autoriser explicitement un owner unique sur les fragments sales;
3. creer un worktree dedie propre pour le prototype `docops_feedback_*`.

## Relance De Deblocage 2026-05-24 20:10

Relance demandee par Brice: equipe agile gouvernail lancee tout de suite, sans
dev, sans serveur, sans instance privee et sans rouvrir `RM-2026-0017`.
Collision d'identifiants detectee pendant la relance: les plages
`CONV-2026-1532`..`1537` sont reservees par compta multi-sources et
`CONV-2026-1540`..`1545` par `Coffre et partage`. Les sorties de cette vague
sont donc rattachees canoniquement a `CONV-2026-1546`..`1549`.

Verdict consolide: `NO-GO dev dans le worktree principal`. Le prochain geste
propre est de creer un worktree dedie propre, par exemple
`codex/rm-0003-0029-docops-feedback`, sous `C:\Users\brice\CoproScope\dev\...`.
Le patch futur peut ensuite rester borne a:

- `server/src/coproscope/web/docops_feedback_route.py`;
- `server/src/coproscope/web/docops_feedback_view.py`;
- `server/src/coproscope/web/templates/docops_feedback.html`;
- `server/src/coproscope/web/static/styles_part_13.css`;
- `server/tests/test_ui_docops_feedback_route.py`;
- hook minimal controle dans `server/src/coproscope/web/_app_fragments/part_003.pyfrag`;
- imports strictement necessaires dans `server/src/coproscope/web/_app_fragments/part_001.pyfrag`;
- import eventuel de `styles_part_13.css` depuis `server/src/coproscope/web/static/styles.css`.

Fichiers a eviter dans le worktree principal: `document_intake_*`, `depot.py`,
`viewmodel.py`, `_source_models.py`, passation/read models publics, fichiers
sales proches du lot intake et tout fichier d'instance privee.

Front: `/documents/tri-feedback` doit etre declare avant `/documents/{doc_id}`,
sinon la route est avalee comme `doc_id=tri-feedback`. `part_003.pyfrag` est
sale et proche du plafond, donc l'ajout direct dans le worktree principal reste
refuse. Le template `docops_feedback.html` et `styles_part_13.css` restent les
bons isolants front.

Back: le registre cible reste `registers/registre_feedback_docops.csv`. Les
exports CSV/JSON doivent etre generes depuis ce registre, via routes tokenisees,
pas servis comme fichiers arbitraires. La projection publique exclut
`original_path`, `file_name`, `text_path`, OCR brut, chemins locaux, secrets et
tables de correspondance.

QA/novice: `NO-GO novice` pour dev immediat. Le test cible futur
`server/tests/test_ui_docops_feedback_route.py` doit couvrir token GET/POST et
exports, non-shadowing par `/documents/{doc_id}`, refus des valeurs invalides,
justification obligatoire pour `Reserve CS`, `Bloque` et `A masquer`, pages ou
ranges obligatoires avant derive diffusable, exports sans fuite et regression
`/documents/ajouter`.

Decisions ouvertes:

- format exact des pages sensibles: page simple, plages, pages mixtes et cas
  ou l'utilisateur ne sait pas;
- regle courte visible pour distinguer `A masquer`, `Reserve CS`, `Bloque` et
  `A decider`;
- niveau d'indice neutre autorise sur une carte document;
- creation effective du worktree dedie ou maintien du blocage.

## Journal

| Heure | Conversation | Evenement | Note |
|---|---|---|---|
| 2026-05-24 10:46 +02:00 | `CONV-2026-1519` | `BOT-START` | Equipe agile lancee en cadrage sur `RM-2026-0003` + `RM-2026-0029`; `RM-2026-0017` bloque exclu; aucun dev, serveur ni instance privee. |
| 2026-05-24 10:47 +02:00 | `CONV-2026-1520`..`CONV-2026-1524` | `AGENTS_LAUNCHED` | Agents Pascal, Leibniz, Raman, Singer et Copernicus lances en lecture seule; devs limites a la cartographie tant que le GO novice manque. |
| 2026-05-24 10:52 +02:00 | `CONV-2026-1520`..`CONV-2026-1524` | `CADRAGE_DONE` | Cinq roles consolides; GO conditionnel prototype, NO-GO dev immediat; prochaine relance = audit collisions puis owner code unique si possible. |
| 2026-05-24 10:56 +02:00 | `CONV-2026-1519` | `AUDIT_COLLISION` | Branchement route non isolable sans toucher `part_003.pyfrag` et `part_001.pyfrag` deja modifies; chantier marque `BLOQUE`, aucun code lance. |
| 2026-05-24 20:10 +02:00 | `CONV-2026-1546`..`CONV-2026-1549` | `RELANCE_DEBLOCAGE` | Agents Gauss, Chandrasekhar, Avicenna et Hooke lances en lecture seule puis renumerotes apres collisions avec compta et coffre-partage; aucun code, serveur ou instance privee. |
| 2026-05-24 20:18 +02:00 | `CONV-2026-1546`..`CONV-2026-1549` | `DEBLOCAGE_DONE` | Verdict consolide: NO-GO dev dans le worktree principal; prochain geste propre = worktree dedie pour `docops_feedback_*` puis test cible `test_ui_docops_feedback_route.py`. |
| 2026-05-24 21:58 +02:00 | `CONV-2026-1519` | `CLOTURE_SUPERSEDE` | Le blocage est depasse par `CONV-2026-1580`: `/documents/tri-feedback` est integre localement et verifie; la suite fonctionnelle est reprise par `CONV-2026-1581` avec `ajout_docs_tri_bridge_v1`. |

## Cloture Apres Integration

Le blocage de ce chantier n'est plus a relancer tel quel.

Il a ete leve par un chemin separe:

- prototype `/documents/tri-feedback` livre dans un worktree dedie;
- integration locale reprise sous `CONV-2026-1580`;
- verification ciblee post-reprise: 33 tests OK, garde-fou 600 lignes OK,
  `git diff --check` OK;
- suite produit reprise sous `CONV-2026-1581` avec la commande
  `ajout_docs_tri_bridge_v1`.

Decision: ne plus relancer `CONV-2026-1519`. Tout nouveau travail doit partir
du prototype integre et du pont volontaire depuis `/documents/ajouter`.
