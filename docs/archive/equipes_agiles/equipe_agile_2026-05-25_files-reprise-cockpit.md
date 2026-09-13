# Equipe agile - ORD-P0-031 Files reprise cockpit

Date de lancement: 2026-05-25 03:04 +02:00.
Mode: equipe agile de cadrage produit, lecture seule, sans dev.

## BOT-START

```text
BOT-START - Coordinateur-scribe agile - 2026-05-25 03:04 +02:00
Roadmap: RM-2026-0003 / RM-2026-0006 / RM-2026-0037 / RM-2026-0038
Ordre: ORD-P0-031 / FILES-REPRISE-COCKPIT
Chantier: CH-20260525-030400-RM-2026-0003-files-reprise-cockpit
Conversation: CONV-2026-1678
Role: Coordinateur-scribe agile
Mission: cadrer les files ouvertes depuis le cockpit pour agir sur une ligne: actions P1, relances syndic, demandes a faire et pieces manquantes.
Ownership modifiable: docs/equipe_agile_2026-05-25_files-reprise-cockpit.md, docs/presence_agents.md, trace append-only docs/roadmap_backlog_central.md et heartbeat relance-equipe-agile-gouvernail-autonome.
Fichiers a eviter: code applicatif, tests applicatifs, templates, CSS, worktree principal sale, lots PRET_A_INTEGRER sans decision d'integration, instances privees, documents bruts, OCR/logs, exports bruts, secrets, serveurs locaux, push GitHub, RM-2026-0017 / ORD-P0-990, reouverture ORD-P0-002/010/011/012/020/030 sans nouveau diff ou decision Brice.
Dernier point lu: AGENTS.md, protocoles equipe agile/orchestration/roadmap/presence, consignes interconversations, gouvernail, presence et mission ORD-P0-030 cloturee.
Tests/preuves attendus: retours designer/novice/front/back/QA, GO/NO-GO novice, cartographie routes /actions et /pieces actuelles, contrat file borne, panier security/privacy/no-private/line-limit/smoke/captures futures.
Risque de collision: ORD-P0-021 reste PRET_A_INTEGRER sans decision; ORD-P0-030 est AGILE-DONE sans dev et ne doit pas etre rouvert. Ce lot reste borne aux files detaillees, sans modifier le cockpit.
Lease ownership: jusqu'au 2026-05-25 05:04 +02:00.
Prochaine action: lancer les roles designer, novice, front, back/viewmodel et QA en lecture seule, puis consolider une commande future bornee ou un NO-GO dev.
```

## Etat initial

- A tester maintenant: pas de recette live; aucun serveur reserve.
- En dev maintenant: aucun dev; aucun owner code ouvert.
- En enquete maintenant: roles a lancer en lecture seule sur `/actions` et `/pieces`.
- Commande prete: non; l'objectif est de borner la commande des files de reprise.
- Comparaison visuels enquete: references obligatoires
  `docs/assets/ux-livraison-reelle-2026-05-21-8766-p0-live/actions-p1.png`,
  `docs/assets/ux-livraison-reelle-2026-05-21-8766-pieces-n2/pieces-manquantes-live.png`
  et `docs/assets/etude-utilisateurs/registre-decisions-actions-preuves.png`.
- Agents idle a relancer: designer, novice, front, back/viewmodel et QA.
- Decision requise: aucune decision Brice immediate. Un owner code futur doit
  etre explicite et en worktree dedie.
- Prochain mouvement: lancer les roles et recuperer les retours.
- Tests/preuves: `git diff --check` documentaire; tests applicatifs en lecture
  seulement si utiles a la cartographie, sans serveur.

## Roles

| Conversation | Role | Statut | Agent |
|---|---|---|---|
| `CONV-2026-1678` | Coordinateur-scribe agile | CLOTURE | local |
| `CONV-2026-1679` | Designer service / facilitateur | CLOTURE | Ramanujan `019e5cac-2662-75c1-8c1b-dc24ea6a0df2` |
| `CONV-2026-1680` | Utilisateur novice / membre CS | CLOTURE | Nietzsche `019e5cac-4124-7e80-a4dd-12012d449606` |
| `CONV-2026-1681` | Dev front lecture seule | CLOTURE | Hilbert `019e5cac-585e-7a92-ace1-3e1df1035b2a` |
| `CONV-2026-1682` | Dev back / viewmodel lecture seule | CLOTURE | local, reprise faute capacite threads |
| `CONV-2026-1683` | QA privacy / regression | CLOTURE | local, reprise faute capacite threads |

## Contraintes produit

- Les entrees cibles sont `/actions?priority=P1`, `/actions?scope=syndic`,
  `/actions?status=a_demander` et `/pieces?proof=missing`.
- Premier viewport: une file directement actionnable ou un etat vide dedie,
  jamais une page generale qui force a comprendre les filtres.
- Chaque ligne doit afficher raison, preuve attendue ou source, prochaine action
  humaine, echeance/statut utile et prudence de diffusion.
- Aucun bouton ne doit pretendre envoyer une relance, valider juridiquement,
  cloturer automatiquement ou exposer un document brut.
- Les libelles doivent rester humains: pas de `P1` seul, pas de jargon
  `SyndicOps`, `DecisionOps`, `hash`, `payload`, `vault` au premier niveau.
- Les donnees de cadrage restent fictives, publiques de test ou deja
  anonymisees.

## Attendus par role

- Designer: blueprint des quatre files, etat vide dedie, ligne type et relation
  avec le cockpit `ORD-P0-030`.
- Novice: verifier si un membre CS comprend quoi faire sur une ligne sans aide
  externe, avec les mots a garder/interdire.
- Front: cartographier routes/templates/CSS actuels, filtres query, premier
  viewport, token, catch-all et fichiers a toucher ou eviter.
- Back/viewmodel: cartographier contrats publics existants, champs disponibles,
  allowlist future et champs interdits.
- QA: panier futur token/privacy/no-private/line-limit/smoke/captures, anti
  envoi automatique, anti fuite et tests d'etats vides.

## Retour designer - CONV-2026-1679

Verdict: GO blueprint, NO-GO dev immediat.

`ORD-P0-031` doit etre le drill-down du cockpit, pas une reprise du cockpit.
Les quatre routes gardent la meme structure:

- `/actions?priority=P1`: `Actions a traiter en priorite`;
- `/actions?scope=syndic`: `Relances syndic a preparer`;
- `/actions?status=a_demander`: `Preuves ou reponses a demander`;
- `/pieces?proof=missing`: `Pieces manquantes`.

Premier viewport attendu: contexte local compact, H1 humain, phrase qui dit
pourquoi la ligne est ici et quoi faire ensuite, 3 a 4 compteurs utiles, liste
actionnable a gauche et detail utile a droite. Ne pas ouvrir une page generale
ou l'utilisateur doit comprendre les filtres.

Ligne type obligatoire:

1. Sujet concret.
2. Pourquoi cette ligne est dans la file.
3. Preuve/source disponible.
4. Preuve ou reponse attendue.
5. Qui agit ou qui relancer.
6. Echeance, retard ou blocage.
7. Prochaine action humaine.
8. Prudence de diffusion.

CTA surs: `Preparer la relance`, `Preparer la demande`, `Ajouter une piece
recue`, `Voir l'action liee`, `Noter l'envoi fait hors CoproScope`. CTA a
eviter: `Envoyer`, `Relancer` seul, `Diffuser`, `Publier`, `Valider`,
`Clore`.

Etats vides dedies:

- `Aucune action prioritaire a reprendre pour le moment.`
- `Aucune relance syndic a preparer.`
- `Aucune preuve ou reponse a demander.`
- `Aucune piece manquante identifiee.`

Mapping avec `ORD-P0-030`: carte cockpit action critique -> `/actions?priority=P1`;
relance syndic -> `/actions?scope=syndic`; preuve/reponse a demander ->
`/actions?status=a_demander`; piece manquante -> `/pieces?proof=missing`.
Le vocabulaire reste `sujet`, `pourquoi`, `preuve/source`, `prochaine action`,
`prudence diffusion`.

## Retour novice - CONV-2026-1680

Verdict: GO novice conditionnel, NO-GO produit sans recette navigateur/captures
et sans preuve stricte que les filtres affichent les bonnes lignes.

Points compris:

- `/actions?priority=P1` est clair si `Critique` est toujours explique par
  retard, preuve bloquante ou action prioritaire.
- `/actions?scope=syndic` est clair avec la mention `envoi hors CoproScope`.
- `/actions?status=a_demander` est utile, mais `Demander au syndic` peut etre
  faux si le detenteur n'est pas le syndic.
- `/pieces?proof=missing` est clair, sauf les libelles `Detail piece/preuve`
  pour une piece absente et `Voir pieces privees`, trop ambigus.

Mots a garder: `preuve attendue`, `pourquoi`, `prochaine action`, `relancer
syndic`, `ajouter reponse recue`, `rattacher une piece`, `conseil syndical
seulement`, `envoi hors CoproScope`.

Mots a interdire au premier niveau: `P1` seul, `scope`, `status`, `proof`,
`SyndicOps`, `DecisionOps`, `DocOps`, `hash`, `payload`, `vault`, `raw`,
`restricted`, `private`, `logs`, `envoyer automatiquement`, `valider
juridiquement`.

Preuve minimale par ligne: titre du sujet, raison concrete, detenteur ou
responsable, preuve attendue nommee, prochaine action humaine, echeance/statut
utile et regle de diffusion. Toute ligne qui garde `A preciser` sur preuve ou
action reste NO-GO.

## Retour front - CONV-2026-1681

Verdict: GO cartographie front, NO-GO dev dans le worktree courant.

Routes actuelles:

- `/actions` accepte `scope`, `priority` et `status` dans
  `server/src/coproscope/web/_app_fragments/part_003.pyfrag`;
- `/actions/{action_id}` redirige vers `/actions?selected=...` ou
  `action_missing=...` avec masquage des references privees;
- `/pieces` a une branche specifique pour `proof=missing`;
- `/pieces/{piece_id}` rend le detail piece/preuve depuis le modele dashboard.

Templates actuels:

- `server/src/coproscope/web/templates/actions.html`;
- `server/src/coproscope/web/templates/_actions_reprise_actions.html`;
- `server/src/coproscope/web/templates/_actions_reprise_syndic.html`;
- `server/src/coproscope/web/templates/pieces.html`.

CSS actuel: styles reprise dans `styles_part_11.css` et complements responsive
dans `styles_part_12.css`.

Ecarts premier viewport:

- `/actions?priority=P1` ouvre `Toutes les actions en retard`; cible future:
  `Actions prioritaires a reprendre`, car `P1` n'est pas forcement un retard.
- `/actions?scope=syndic` ouvre bien `Relance syndic`, mais le chemin modele
  public peut produire une liste de relances vide pendant que les lignes
  filtrees restent plus bas.
- `/actions?status=a_demander` est le plus proche de la cible.
- `/pieces?proof=missing` est proche, mais `Voir pieces privees` et `Relancer
  syndic` doivent devenir plus prudents.

Risques front: ne pas ajouter a `part_003.pyfrag` qui est deja proche du seuil
600 lignes; preferer les templates/includes cites, un CSS dedie borne et un
test TestClient cible.

## Retour back/viewmodel local - CONV-2026-1682

Verdict: GO contrat existant, NO-GO dev immediat sans owner unique.

Contrats existants utiles:

- `read_public_actions_v1` filtre par priorite, statut, domaine ou canal;
- `PUBLIC_ACTIONS_COLUMNS` expose seulement id, titre, source, priorite,
  statut, domaine, responsable, prochaine etape, preuve attendue, canal,
  diffusion, ids publics lies et hrefs derives;
- `_build_priority_views` construit `late_actions`, `missing_pieces` et
  `syndic_followups`;
- les pieces manquantes exposent deja `expected_piece`, `reason`,
  `proof_expected_label`, `request_href`, `deposit_href`, `action_href`,
  `owner_label`, `source_label`, `diffusion_label` et `next_step`;
- le detail piece/preuve distingue piece candidate et preuve finale.

Champs manquants ou a durcir pour la commande future:

- titre de contexte distinct pour `priority=P1` au lieu de toujours `retards`;
- raison visible par filtre (`pourquoi cette ligne est ici`);
- preuve/source disponible separee de preuve attendue;
- detenteur non reduit au syndic quand la source n'est pas le syndic;
- etats vides dedies par filtre;
- preuve stricte que le modele public alimente aussi la file syndic.

Champs interdits: chemin local, brut, `payload_json`, `event_path`,
`source_file`, `source_path`, `original_path`, `current_blob_id`,
`source_sha256`, `locator_json`, `message_draft`, token, email, `raw`,
`restricted`, `logs`, `private`, `secret`.

Allowlist future conseillee `reprise_files_from_cockpit_v1`: `route`,
`title`, `subtitle`, `summary`, `items[].id`, `items[].subject`,
`items[].why_here`, `items[].source_label`, `items[].expected_proof_label`,
`items[].holder_label`, `items[].status_label`, `items[].next_action_label`,
`items[].next_action_href`, `items[].diffusion_caution`, `items[].related_href`
et `empty_state`.

## Retour QA local - CONV-2026-1683

Verdict: GO cadrage QA, NO-GO produit complet.

Preuves lancees en lecture seule:

```text
server\.venv\Scripts\python.exe -m unittest server.tests.test_ui_registre_actions server.tests.test_ui_pieces_viewmodel server.tests.test_ui_piece_detail_route server.tests.test_ui_smoke_routes_expanded server.tests.test_ui_security_routes server.tests.test_security_no_private_sync_leaks -v
```

Resultat: 37 tests OK, 1 test saute connu sur une livraison front hors scope.

```text
server\.venv\Scripts\python.exe tools\check_code_line_limit.py
```

Resultat: OK, aucun fichier code scope ne depasse 600 lignes.

Risques restants:

- aucune recette navigateur ni capture desktop/mobile/tablette;
- tests existants prouvent les routes utiles, tokenisees et sans fuite, mais
  pas encore l'exactitude stricte des filtres par file;
- parcours complet relance/depot/memoire a verifier avec token;
- libelles `Voir pieces privees`, `Relancer syndic` et `Detail piece/preuve`
  a clarifier avant livraison produit.

Panier futur: test dedie sur les quatre URLs avec token, premier bloc attendu,
absence de promesse d'envoi automatique, token conserve dans les CTA, etats
vides dedies, anti-jargon, anti-fuite et captures desktop/mobile/tablette sur
port reserve.

## Consolidation

Verdict equipe: `AGILE-DONE - equipe agile a fini son job`.

- A tester maintenant: aucun serveur live reserve; tests unitaires cibles OK.
- En dev maintenant: aucun dev ouvert; aucun patch code.
- En enquete maintenant: tous les roles canoniques sont clotures.
- Commande prete: oui, comme commande future bornee, pas executee.
- Comparaison visuels enquete: reprise des visuels actions P1, pieces
  manquantes et registre decisions/actions/preuves.
- Agents idle a relancer: aucun sans nouveau diff ou decision d'owner code.
- Decision requise: Brice doit decider explicitement s'il veut une reprise code
  dediee des files; sinon le heartbeat passe au prochain `ORD-*` actionnable.
- Prochain mouvement: prochain heartbeat = lire la file `ORD-*` et choisir le
  prochain P0 actionnable, probablement `ORD-P0-032`, en excluant les lots
  `PRET_A_INTEGRER` sans decision et les lots `AGILE-DONE` sans nouveau diff.
- Tests/preuves: 37 tests OK, line-limit OK, `git diff --check`
  documentaire a lancer.

Commande future bornee:

```text
Roadmap/chantier:
RM-2026-0003 / RM-2026-0006 / RM-2026-0037 / RM-2026-0038 / nouveau CH owner
code dedie a creer si Brice valide.

Objectif:
Stabiliser les files ouvertes depuis le cockpit: actions prioritaires,
relances syndic, preuves/reponses a demander et pieces manquantes.

Routes:
/actions?priority=P1
/actions?scope=syndic
/actions?status=a_demander
/pieces?proof=missing

UI cible:
Premier viewport dedie par file, avec titre humain, compteur utile, liste
actionnable et detail. Chaque ligne affiche Sujet, Pourquoi ici, Preuve/source,
Preuve ou reponse attendue, Detenteur/responsable, Prochaine action humaine,
Echeance/statut et Prudence diffusion.

Front:
Modifier surtout actions.html, _actions_reprise_actions.html,
_actions_reprise_syndic.html, pieces.html et CSS dedie borne. Eviter
part_003.pyfrag, deja proche de 600 lignes.

Back/viewmodel:
Formaliser reprise_files_from_cockpit_v1 sur allowlist publique. Durcir la
file syndic public model, les etats vides dedies, le detenteur non-syndic et la
separation source disponible / preuve attendue.

Garde-fous:
Token conserve, aucune donnee privee, aucun brut, aucun chemin local, aucun
envoi automatique, aucun jargon technique au premier niveau, aucune validation
juridique/comptable, aucun P1 seul.

Corrections UX obligatoires:
Renommer Voir pieces privees; preferer Voir restrictions de diffusion ou
Pieces avec restriction. Clarifier Relancer syndic en Preparer une relance.
Clarifier Detail piece/preuve quand la piece est absente.

Tests:
test_ui_reprise_files_from_cockpit, test_ui_registre_actions,
test_ui_pieces_viewmodel, test_ui_piece_detail_route,
test_ui_smoke_routes_expanded, test_ui_security_routes,
test_security_no_private_sync_leaks, test_code_line_limit,
tools/check_code_line_limit.py, git diff --check, captures
desktop/mobile/tablette sur port reserve si recette live demandee.
```

## Journal

| Horodatage | Conversation | Evenement | Trace |
|---|---|---|---|
| 2026-05-25 03:04 +02:00 | `CONV-2026-1678` | `START_AGILE_FILES_REPRISE_COCKPIT` | `ORD-P0-030` est `AGILE-DONE`; `ORD-P0-021` est saute car PRET_A_INTEGRER sans decision d'integration. Nouveau chantier P0 ouvert sur `ORD-P0-031` en lecture/cadrage uniquement, sans code ni serveur. |
| 2026-05-25 03:04 +02:00 | `CONV-2026-1679`..`CONV-2026-1683` | `ROLES_RESERVED_FILES_REPRISE_COCKPIT` | Designer, novice, front, back/viewmodel et QA reserves en lecture seule; aucun code, serveur, instance privee, document brut, export brut, secret, push GitHub ou `RM-2026-0017`. |
| 2026-05-25 03:05 +02:00 | `CONV-2026-1679`..`CONV-2026-1683` | `AGENTS_LAUNCH_PARTIAL_FILES_REPRISE_COCKPIT` | Designer Ramanujan, novice Nietzsche et front Hilbert lances en lecture seule; back/viewmodel et QA repris localement faute de capacite de threads. |
| 2026-05-25 03:07 +02:00 | `CONV-2026-1679` | `DESIGNER_RETURN_FILES_REPRISE_COCKPIT` | Ramanujan cloture: GO blueprint, NO-GO dev; quatre files dediees, ligne type sujet/pourquoi/preuve/action/diffusion, etats vides et CTA prudents. |
| 2026-05-25 03:08 +02:00 | `CONV-2026-1680` | `NOVICE_RETURN_FILES_REPRISE_COCKPIT` | Nietzsche cloture: GO novice conditionnel; NO-GO produit sans captures, preuve stricte des filtres, parcours CTA complet et correction de `Voir pieces privees`. |
| 2026-05-25 03:09 +02:00 | `CONV-2026-1681` | `FRONT_RETURN_FILES_REPRISE_COCKPIT` | Hilbert cloture: routes/templates/CSS cartographies; `P1` affiche trop `retard`, syndic public model fragile, `part_003.pyfrag` a eviter car proche du seuil 600 lignes. |
| 2026-05-25 03:09 +02:00 | `CONV-2026-1682` | `BACK_LOCAL_RETURN_FILES_REPRISE_COCKPIT` | Reprise locale: contrats publics actions/pieces exploitables; allowlist future `reprise_files_from_cockpit_v1`, champs interdits et manques viewmodel consolides. |
| 2026-05-25 03:10 +02:00 | `CONV-2026-1683` | `QA_LOCAL_RETURN_FILES_REPRISE_COCKPIT` | Reprise locale: 37 tests OK, line-limit OK; NO-GO produit complet sans recette navigateur/captures et test dedie strict des quatre files. |
| 2026-05-25 03:10 +02:00 | `CONV-2026-1678`..`CONV-2026-1683` | `AGILE_DONE_FILES_REPRISE_COCKPIT` | Equipe cloturee sans dev: commande future `reprise_files_from_cockpit_v1` prete pour owner code dedie si Brice valide; aucun code, serveur, instance privee, export brut, secret, push GitHub ni `RM-2026-0017`. |
