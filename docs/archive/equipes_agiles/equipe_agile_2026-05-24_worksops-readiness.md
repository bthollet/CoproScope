# Equipe agile - WorksOps readiness

Date de lancement: 2026-05-24 20:26 +02:00.
Roadmap: `RM-2026-0032`.
Chantier: `CH-20260524-202603-RM-2026-0032-worksops-readiness`.
Conversation coordination: `CONV-2026-1550`.
Mode: equipe agile gouvernail, cadrage UI reelle avant dev.
Statut: pret a integrer - no-go dev immediat.

## BOT-START

BOT-START - Coordinateur-scribe agile WorksOps - 2026-05-24 20:26 +02:00

Roadmap: `RM-2026-0032`.
Chantier: `CH-20260524-202603-RM-2026-0032-worksops-readiness`.
Conversation: `CONV-2026-1550`.
Role: Coordinateur-scribe agile.
Mission: transformer l'approfondissement UX/UI WorksOps cloture en commande UI/dev testable pour `Travaux suivis`, sans ouvrir de patch applicatif tant que la cible UI, le corpus synthetique, le contrat front/back et le panier QA ne sont pas verrouilles.
Ownership modifiable: ce document, `docs/presence_agents.md`, ligne gouvernail `RM-2026-0032`.
Fichiers a eviter: code applicatif, routes, templates, CSS, tests applicatifs, instances privees, secrets, exports bruts, serveurs locaux, donnees reelles, `RM-2026-0017` bloque et serveur local `CONV-2026-1525`.
Passerelle/registre de trace: ce document, `docs/presence_agents.md`, `docs/roadmap_backlog_central.md`.
Dernier point lu: `AGENTS.md`, `docs/protocole_equipe_agile_agents.md`, `docs/protocole_roadmap_presence_agents.md`, `docs/consignes_bots_interconversations.md`, `docs/roadmap_backlog_central.md`, `docs/presence_agents.md`, `docs/recherche_ux_ui_2026-05-24_travaux_approfondissement.md`, `docs/cadrage_metier_worksops_2026-05-24.md`, `docs/recherche_ux_ui_2026-05-24_travaux_operation-model.md` au 2026-05-24 20:26 +02:00.
Tests/preuves attendus: point court, cible UI nommee, comparaison au blueprint travaux, GO/NO-GO novice, cartographie front/back, contrat `model.ux.worksops_travaux`, panier QA anti-fuite; aucun test applicatif tant qu'aucun code n'est modifie.
Risque de collision: `CONV-2026-1519` reste bloque sur ajout-docs/tri-feedback; `CONV-2026-1525` garde un serveur local; `RM-2026-0017` reste bloque; cette vague reserve `CONV-2026-1550`..`1555`.
Lease ownership: 2026-05-24 22:26 +02:00.
Prochaine action: ouvrir un chantier dev separe seulement apres owner code unique, worktree propre et corpus synthetique verrouille.

## Choix Gouvernail

Les vagues `RM-2026-0030` compta et `RM-2026-0033` coffre sont deja pretes a
integrer. Le lot `RM-2026-0003` / `RM-2026-0029` reste bloque par collision de
worktree. Le prochain P0 exploitable sans toucher au code est donc `RM-2026-0032`
WorksOps, avec recherche UX/UI cloturee et blueprint existant a annoter.

## UI Cible

- Ecran cible: `Travaux suivis`.
- Surface reelle actuelle a comparer: `/chantiers?categorie=travaux` et detail `/chantiers/{event_id}`.
- Route future candidate, si l'equipe la confirme: `/travaux`.
- Blueprint de reference:
  `docs/assets/ux-ui-recherche-2026-05-24-travaux/01-console-travaux-portefeuille-fiche.svg`.
- Sources UX/metier:
  `docs/recherche_ux_ui_2026-05-24_travaux_approfondissement.md`,
  `docs/cadrage_metier_worksops_2026-05-24.md`,
  `docs/recherche_ux_ui_2026-05-24_travaux_operation-model.md`.

Si la route dediee n'existe pas, le premier objectif futur sera de rendre une UI
minimale testable sur donnees fictives ou demo. Aucun dev ne demarre dans cette
vague.

## Roles

| Role | Conversation | Statut | Sortie attendue |
|---|---|---|---|
| Coordinateur-scribe | `CONV-2026-1550` | `PRET_A_INTEGRER` | Registres, synthese et arbitrage; equipe cloturee en cadrage. |
| Designer service / blueprint | `CONV-2026-1551` / Boole `019e5b41-9386-72a0-985c-29f455019090` | `CLOTURE` | Structure `Travaux suivis`, annotations blueprint, comparaison `/chantiers?categorie=travaux` et no-go visuels integres. |
| Utilisateur novice / representant CS | `CONV-2026-1552` / Pascal `019e5b41-99a9-7ee2-a11d-7451d3b8e3dd` | `CLOTURE` | GO conditionnel et NO-GO dev direct integres. |
| Data / read model | `CONV-2026-1553` / Wegener `019e5b41-9b67-7121-8278-eb56f4a864ee` | `CLOTURE` | Contrat `works_operations_v1`, corpus fictif et risques backend integres. |
| Dev front lecture | `CONV-2026-1554` / Plato `019e5b46-dc6f-76d0-8478-e0c01f0cc565` | `CLOTURE` | Route `/travaux`, template/CSS/viewmodel/tests futurs et risques 600 lignes integres. |
| QA privacy / regression | `CONV-2026-1555` / Hilbert `019e5b41-9e61-71c1-927e-2a60780c6d86` | `CLOTURE` | Panier QA token, diffusion, export, statuts probatoires et responsive integre. |

## Point Court Initial

A produire: commande UI/dev de `Travaux suivis`, route ou surface cible, corpus
synthetique minimal, contrat viewmodel, criteres GO novice et panier QA.

En dev maintenant: rien. Les devs restent en lecture.

En test maintenant: rien en execution applicative; la vague prepare des tests
futurs sur donnees fictives.

En enquete maintenant: comparer la surface `/chantiers?categorie=travaux` et le
blueprint `portefeuille + fiche probatoire`.

Commande prete: non; elle doit etre verrouillee par les cinq roles.

Comparaison visuels enquete: obligatoire sur le blueprint WorksOps existant.

Agents idle a relancer: aucun au lancement.

Decision requise: ouvrir ou non un chantier dev separe avec owner unique et
worktree propre une fois la commande stabilisee.

Prochain mouvement: attendre les retours des cinq roles, consolider, puis
continuer vers le prochain P0 actionnable si `AGILE-DONE` est atteint.

Tests/preuves: `git diff --check` sur docs; pas de test applicatif sans code.

## Retours Consolides

### Designer service / blueprint

Commande visuelle: construire `Travaux suivis`. Route future recommandee:
`/travaux`; surface transitoire acceptable: travaux issus de
`/chantiers?categorie=travaux` et un detail de chantier existant, seulement
comme comparaison.

Structure retenue: navigation gauche, en-tete, quatre compteurs, portefeuille
travaux a gauche et fiche probatoire a droite. Le premier viewport doit dire en
moins de 30 secondes quel chantier bloque, quelle preuve manque, quoi faire,
quel budget est en jeu et si le partage est possible.

Annotations blueprint indispensables:

- remplacer `Travaux` par `Travaux suivis`;
- remplacer `Ajouter` par une action secondaire `Creer une operation a
  qualifier`, ou retirer la creation du lot 1;
- colonnes: `Travaux`, `Ou en est-on ?`, `Ce qui bloque`, `A faire maintenant`,
  avec un badge diffusion;
- remplacer `Preparer relance` par `Preparer une demande`;
- placer `Ce qui bloque` avant la chaine probatoire;
- chaine: `Vote -> Devis -> Commande -> Travaux -> Reception -> Reserves ->
  Garantie`;
- blocs: `Pieces confirmees`, `A verifier`, `Manquantes`, `Seuils et mise en
  concurrence`, mini-budget `Vote`, `Commande`, `Facture`, `Paye`, `Reste a
  verifier`;
- mobile: cartes empilees, fiche verticale, frise en liste, CTA prudent sticky.

No-go designer: pas de dev si la creation devient action primaire, si une
facture cloture un chantier, si l'export contourne PrivacyOps, si un badge vert
fait croire a une validation juridique, ou si un statut repose seulement sur la
couleur.

### Utilisateur novice / representant CS

Verdict: GO novice conditionnel pour `/travaux` avec titre `Travaux suivis`.
NO-GO dev immediat tant que le blueprint n'est pas annote et que les actions
sensibles restent ambigues.

Libelles a garder: `Travaux suivis`, `Ou en est-on ?`, `Ce qui manque pour
continuer`, `A faire maintenant`, `Pieces manquantes`, `Pieces a verifier`,
`Pieces confirmees`, `A verifier avant partage`, `Voir l'apercu avant partage`,
`Preparer une demande`, `Rattacher une piece`.

Libelles et actions a rejeter: `WorksOps`, `OperationTravaux`, `preuve
candidate`, `Ajouter` en bouton principal, `Creer une operation` en action
primaire, `Cloturer le chantier`, `Valider la facture`, `Travaux OK`,
`Assurance OK`, `Reception faite`, `Diffuser aux coproprietaires` et `Envoyer
automatiquement`.

Conditions minimales avant dev: route confirmee, premier lot limite aux
operations detectees ou a qualifier, creation secondaire, corpus synthetique de
5 cas, statuts probatoires, seuils inconnus explicites, partage bloque par
apercu + gate PrivacyOps, chantier dev separe avec owner unique.

### Data / read model

Contrat recommande: `works_operations_v1`, expose a l'UI sous
`model.ux.worksops_travaux`, avec `dataset_kind = synthetic_demo` tant qu'aucune donnee
reelle n'est autorisee.

Champs minimum par operation: `operation_id`, `title`, `scope`, `status`,
`status_label`, `blocking_evidence`, `next_action`, `budget`,
`evidence_counts`, `diffusion_status`, `source_quality`.

Statuts autorises v1: `A_QUALIFIER`, `VOTE_A_RETROUVER`, `DEVIS_A_COMPARER`,
`DEVIS_RETENU`, `COMMANDE_A_CONFIRMER`, `TRAVAUX_EN_COURS`,
`RECEPTION_A_PROUVER`, `RESERVES_A_SUIVRE`, `GARANTIE_A_SURVEILLER`,
`CLOS_AVEC_PREUVES`.

Corpus synthetique minimal:

1. `WKS-DEMO-001` reprise etancheite toiture: vote introuvable, devis/facture
   candidats, budget inconnu, partage a verifier;
2. `WKS-DEMO-002` remplacement porte local velos: devis a comparer, mise en
   concurrence a verifier, diffusion CS seulement;
3. `WKS-DEMO-003` modernisation eclairage halls: commande a confirmer,
   vote/devis confirmes, assurance candidate;
4. `WKS-DEMO-004` refection cages d'escalier: reception avec reserves, levee
   non prouvee, export bloque;
5. `WKS-DEMO-005` remplacement pompe de relevage: garantie a surveiller, apercu
   possible apres controle.

Champs interdits: libelles `travaux_ok`, `assurance_ok`, `facture_validee`,
envoi automatique, cloture par facture, identite reelle, email, telephone,
adresse privee, IBAN, chemin local, hash de documents prives, extraits OCR
reels.

### Dev front lecture

Route cible recommandee: `/travaux`, titre UI `Travaux suivis`.

Surface transitoire: `/chantiers?categorie=travaux` et detail
`/chantiers/{event_id}` uniquement pour comparaison, pas comme destination
WorksOps durable.

Fichiers futurs a owner unique: `templates/travaux.html`, fragments
`_travaux_*.html`, `static/styles_part_13.css` et import dans `styles.css`,
nouveau viewmodel `viewmodels/_worksops_travaux.py`, raccord
`viewmodels/__init__.py` et `_ux_model.py`, route dans
`_app_fragments/part_004.pyfrag` avant le catch-all.

Risques front verifies localement: ne pas ajouter `/travaux` a
`_app_fragments/part_003.pyfrag` deja a 544 lignes; ne pas etendre
`workstreams.html` deja a 526 lignes pour WorksOps; preferer
`styles_part_13.css` plutot qu'un module CSS existant; enregistrer
`/travaux/{operation_id}` avant le catch-all; garder le worktree principal hors
dev.

Tests UI futurs: `/travaux` 403 sans token et 200 avec token, liens token-safe,
aucun chemin prive/brut/log/restricted, rendu des 5 operations synthetiques,
mobile sans tableau horizontal, libelles interdits absents et export/apercu
derive avec `source_of_truth=false`.

### QA privacy / regression

Panier QA prioritaire: export WorksOps toujours derive avec watermark,
`source_of_truth=false`, token obligatoire, aucun brut; gate PrivacyOps avant
partage; refus d'export direct depuis preuve candidate, facture seule,
assurance OK, reception non prouvee ou reserve ouverte; travaux/ITE non
sensibles par defaut sans signal reel.

Tests futurs: corpus `works_operations_v1` avec les 5 cas synthetiques; route
future `/travaux` 403 sans token, liens token-safe et aucun chemin prive;
export travaux JSON/TXT/MD derive sans `raw`, `logs`, `restricted`, `staging`,
chemin local, `file://`, token local ou payload brut.

Donnees interdites: tout `instances/`, Beauvallon, documents bruts, OCR, logs,
secrets, tokens, chemins locaux, noms, mails, telephones, lots nominatifs,
impayes, IBAN/RIB, contentieux, offres de negociation et tables de biffage.

GO QA: cadrage et futur chantier dev separe sur corpus 100 % synthetique.
NO-GO QA: export WorksOps diffusable tant que la regle PrivacyOps d'export, les
tests anti-fuite et le gate apercu avant partage ne sont pas implementes et
verts.

## Decision de cloture

Commande prete: oui, pour un futur chantier dev separe seulement.

En dev maintenant: rien. Le worktree principal reste sale et plusieurs fichiers
front sont proches du seuil de prudence; aucun patch applicatif n'est ouvert
dans cette vague.

Tests/preuves: pas de test applicatif car aucun code n'est modifie. Verification
documentaire: `git diff --check`.

Prochain mouvement: ouvrir un worktree propre avec owner unique si Brice valide
le passage dev; sinon passer au prochain P0 actionnable du gouvernail.

BOT-END - Coordinateur-scribe agile WorksOps - 2026-05-24 20:37 +02:00

AGILE-DONE - equipe agile a fini son job

## Journal

| Heure | Acteur | Evenement | Detail |
|---|---|---|---|
| 2026-05-24 20:26 +02:00 | `CONV-2026-1550` | `BOT-START` | Vague agile gouvernail ouverte sur `RM-2026-0032`; code, serveur, instance privee, donnees reelles et `RM-2026-0017` evites. |
| 2026-05-24 20:27 +02:00 | `CONV-2026-1551`..`CONV-2026-1555` | `AGENTS_LAUNCHED` | Agents Boole, Pascal, Wegener, Euclid et Hilbert lances en lecture seule; aucun code, serveur ou instance privee. |
| 2026-05-24 20:27 +02:00 | `CONV-2026-1551`..`CONV-2026-1555` | `AGENTS_LAUNCHED` | Agents Beauvoir, Bohr, Lorentz, Rawls et Tesla lances en lecture seule; aucun code, serveur ou instance privee. |
| 2026-05-24 20:34 +02:00 | hors registre canonique | `DUPLICATE_AGENTS_CLOSED` | Doublons Lorentz `019e5b40-55db-7b71-8b75-36c02b0a7a09`, Huygens `019e5b40-8364-7f72-97c3-e7e0faa851f2`, Tesla `019e5b40-a4c2-77f3-803d-dbfae38cf60e`, Euler `019e5b40-cbad-7252-aba4-d0af949637b5` et Erdos `019e5b40-ecbd-7110-aa5b-ce43d2ea8f26` fermes; retours Huygens novice et Erdos QA conserves comme notes non canoniques, non integrees tant que les roles `CONV-2026-1551`..`1555` officiels restent vivants. |
| 2026-05-24 20:37 +02:00 | `CONV-2026-1551`, `1552`, `1553`, `1555` | `PARTIAL_RETURNS_INTEGRATED` | Designer Boole, novice Pascal, data Wegener et QA Hilbert integres; Euclid `CONV-2026-1554` s'est arrete sans livrable et Plato le remplace en relance unique lecture seule. |
| 2026-05-24 20:35 +02:00 | hors registre canonique | `DUPLICATE_AGENTS_CLOSED_2` | Doublons Leibniz, Goodall, Hume, Beauvoir bis et Maxwell fermes sans integration canonique; les roles officiels restent `CONV-2026-1551`..`1555`. |
| 2026-05-24 20:37 +02:00 | `CONV-2026-1554` | `FRONT_RELAUNCH` | Plato `019e5b46-dc6f-76d0-8478-e0c01f0cc565` lance en remplacement d'Euclid shutdown; aucun role front vivant duplique. |
| 2026-05-24 20:37 +02:00 | `CONV-2026-1554` | `FRONT_RETURN_WORKSOPS_READINESS` | Plato integre: route cible `/travaux`, owner futur template/CSS/viewmodel/route/tests, attention catch-all et limites 600 lignes. |
| 2026-05-24 20:37 +02:00 | `CONV-2026-1550`..`CONV-2026-1555` | `AGILE_DONE_WORKSOPS_READINESS` | Vague cloturee: commande `Travaux suivis`, contrat `works_operations_v1`, corpus fictif, cartographie front, panier QA et NO-GO dev immediat dans le worktree principal. |
