# Equipe agile - Audit360 ORD-P0-012 AG contentieux

Date de lancement: 2026-05-25 02:25 +02:00.
Mode: equipe agile de cadrage produit, lecture seule, sans dev.

## BOT-START

```text
BOT-START - Coordinateur-scribe agile - 2026-05-25 02:25 +02:00
Roadmap: RM-2026-0008 / RM-2026-0024 / RM-2026-0025
Ordre: ORD-P0-012 / AUDIT360-AG-CONTENTIEUX
Chantier: CH-20260525-022537-RM-2026-0008-audit360-ag-contentieux
Conversation: CONV-2026-1660
Role: Coordinateur-scribe agile
Mission: cadrer un dossier probatoire restreint AG/contentieux qui rassemble pieces, questions, echeances et restrictions, sans avis juridique automatique ni diffusion sensible implicite.
Ownership modifiable: docs/equipe_agile_2026-05-25_audit360-ag-contentieux.md, docs/presence_agents.md, trace append-only docs/roadmap_backlog_central.md et heartbeat relance-equipe-agile-gouvernail-autonome.
Fichiers a eviter: code applicatif, tests applicatifs, templates, CSS, worktree principal sale, instances privees, documents bruts, rapports juridiques nominatifs, OCR/logs, exports bruts, secrets, push GitHub, serveurs non reserves, RM-2026-0017 / ORD-P0-990, reouverture ORD-P0-010 ou ORD-P0-011 sans nouveau diff ou decision Brice.
Dernier point lu: AGENTS.md, protocoles equipe agile/orchestration/roadmap/presence, consignes interconversations, gouvernail, presence, mission ORD-P0-011 cloturee, docs/ui_ag_contentieux_passation.md, docs/ag_contentieux_passation.md, docs/test_novice_live_8766_2026-05-21.md, docs/recherche_ux_ui_2026-05-24_gouvernance.md.
Tests/preuves attendus: synthese multi-roles, GO/NO-GO novice, gate privacy conversationnelle, cible UI reelle `/ag-contentieux` ou route future bornee, contrat public fictif/anonymise, panier privacy/security/no-private/line-limit/smoke, decision explicite avant tout owner code.
Risque de collision: worktree principal sale; route historique `/ag-contentieux` existe deja mais le lot `ORD-P0-012` n'a pas de role vivant. Aucun patch code autorise dans ce chantier.
Lease ownership: jusqu'au 2026-05-25 04:25 +02:00.
Prochaine action: lancer les roles designer, novice, front, back/viewmodel et QA en lecture seule, puis consolider une commande bornee ou un NO-GO dev.
```

## Etat initial

- A tester maintenant: aucune UI live. La route historique `/ag-contentieux`
  existe comme surface a examiner en lecture seule dans les docs et le code si
  utile, mais aucun serveur n'est reserve.
- En dev maintenant: aucun dev; pas de worktree code ouvert.
- En enquete maintenant: roles a lancer en lecture seule.
- Commande prete: non. La cible produit est un dossier probatoire restreint
  AG/contentieux, pas un avis juridique, pas un export large.
- Comparaison visuels enquete: utiliser les blueprints gouvernance du
  2026-05-24, le test novice live du 2026-05-21 et les commandes Audit360
  ORD-P0-010/011 comme references de prudence.
- Agents idle a relancer: designer, novice, front, back/viewmodel et QA.
- Decision requise: aucune decision Brice immediate. Un owner code futur devra
  etre valide explicitement et partir en worktree dedie.
- Prochain mouvement: lancer les roles et recuperer les retours.
- Tests/preuves: `git diff --check` documentaire; aucun serveur, aucun test
  applicatif, aucune instance privee.

## Roles

| Conversation | Role | Statut | Agent |
|---|---|---|---|
| `CONV-2026-1660` | Coordinateur-scribe agile | CLOTURE | local |
| `CONV-2026-1661` | Designer service / facilitateur | CLOTURE | Chandrasekhar `019e5c87-e7a7-7581-9184-177e2e0281d3` |
| `CONV-2026-1662` | Utilisateur novice / membre CS | CLOTURE | Laplace `019e5c87-e810-7d62-9a83-7a4a0367ca2f` |
| `CONV-2026-1663` | Dev front lecture seule | CLOTURE | Planck `019e5c87-e880-7a01-8b16-77879b46ea50` |
| `CONV-2026-1664` | Dev back / viewmodel lecture seule | CLOTURE | Beauvoir `019e5c89-7c5d-7cf1-a1af-22f6bda6798c` |
| `CONV-2026-1665` | QA privacy / regression | CLOTURE | Curie `019e5c8a-6b78-7100-8491-b506fbbfe50b` |

## Contraintes produit

- Le dossier AG/contentieux doit rester factuel, restreint et separe.
- Aucune analyse sensible ne devient diffusable sans restriction explicite.
- Aucun avis juridique, chance de gagner, strategie judiciaire ou consigne
  d'assigner ne doit etre produit automatiquement.
- Le flux cible est `piece -> question -> echeance -> restriction -> action`.
- Les personnes, lots, pieces et organisations doivent rester sous alias ou
  identifiants opaques dans les sorties d'equipe.
- Les sorties diffusable restent derivees: aucun chemin local, nom brut, OCR,
  log, token, secret, email, telephone, IBAN/RIB, export brut ou table alias.
- Les donnees de cadrage sont fictives, test ou deja anonymisees.

## Sources de decision

- `docs/ui_ag_contentieux_passation.md`
- `docs/ag_contentieux_passation.md`
- `docs/test_novice_live_8766_2026-05-21.md`
- `docs/recherche_ux_ui_2026-05-24_gouvernance.md`
- `docs/equipe_agile_2026-05-25_audit360-points-a-verifier.md`
- `docs/equipe_agile_2026-05-25_audit360-boite-reprise.md`
- `docs/roadmap_backlog_central.md`
- `docs/presence_agents.md`

## Gate privacy conversationnelle

Tout retour doit rester au niveau role, piece, periode, statut, echeance et
restriction. Les alias recommandes sont `PERS-01`, `CS-01`, `SYNDIC-01`,
`LOT-01`, `PIECE-AG-001`, `DOSSIER-AG-001` et `DOSSIER-CONT-001`.

No-go immediat si un livrable contient une identite reelle inutile, une piece
brute, une citation longue, un chemin local, un token, un secret, une allegation
non sourcee ou une diffusion qui ne dit pas qui peut voir.

## Retour novice - CONV-2026-1662

Verdict: GO concept, NO-GO dev immediat.

Le novice comprend l'intention de `/ag-contentieux`: dossier de travail restreint
pour preparer une AG, suivre des sujets contentieux factuels, voir les preuves,
les echeances, les restrictions et preparer une passation. Mais la page actuelle
reste percue comme une table de lecture avec ancres, pas encore comme un parcours
actionnable.

Parcours 30 secondes attendu:

1. Lire le bandeau `AG, contentieux, passation`.
2. Voir immediatement `brouillon interne / non officiel`, `qui peut voir`,
   `prochaine action`, `echeance`, `preuve manquante`.
3. Choisir une carte: `Question AG`, `Piece de convocation`,
   `Dossier contentieux`, `Note non juridique`, `Pack passation`.
4. Comprendre pour chaque ligne: source, preuve attendue, restriction,
   diffusion, statut, action suivante.
5. Sortir avec une reponse simple: verifier telle piece avant telle date,
   visible seulement CS, pas encore diffusable.

Libelles acceptables: `Projet CS - non officiel`, `Brouillon interne`,
`Version de travail`, `Question AG a preparer`, `Piece source`,
`Preuve a verifier`, `Preuve manquante`, `Diffusion: conseil syndical`,
`Diffusion: coproprietaires apres revue`, `Contentieux restreint`,
`Note non juridique`, `Revue de diffusion`, `Pack passation incomplet`,
`A faire constater au PV si non leve`, `Validation humaine requise`.

Libelles dangereux: `convocation officielle`, `PV d'AG` pour un document CS,
`avis juridique`, `conseil juridique`, `chances de gagner`,
`il faut assigner / poursuivre / attaquer`, `signature` sans portee,
`publier` sans revue de diffusion, `public` ou `coproprietaires` par defaut sur
un dossier contentieux.

NO-GO avant dev tant que:

- le premier ecran ne dit pas statut, preuve, diffusion et prochaine action en
  moins de 30 secondes;
- le pack passation ressemble a un export disponible sans bouton reel;
- les cartes restent seulement des ancres;
- le statut `non officiel` n'est pas permanent sur la partie AG;
- la difference entre AG, contentieux, note non juridique et passation n'est
  pas evidente;
- le dossier contentieux peut etre confondu avec un avis juridique.

## Retour designer - CONV-2026-1661

Verdict: GO cadrage produit, NO-GO dev immediat tant que novice, back/viewmodel
et QA privacy n'ont pas valide une commande bornee. Dev futur seulement en
worktree dedie, sur donnees fictives/test ou derivees anonymisees.

Route cible retenue: `/ag-contentieux`, comme dossier probatoire restreint
AG/contentieux.

Promesse utilisateur:

```text
Je vois les pieces, les questions, les echeances, les restrictions et ce qui
reste a faire, sans que CoproScope me donne un avis juridique ou diffuse quoi
que ce soit automatiquement.
```

Structure du dossier:

1. `Synthese restreinte`: statut du dossier, prochaine action, echeance la plus
   proche, diffusion actuelle.
2. `Pieces`: source, preuve attendue, statut, restriction, diffusion, echeance.
3. `Questions AG`: question a formuler, piece liee, preuve manquante, action
   humaine.
4. `Contentieux factuel`: faits dates, pieces, echeances, actions ouvertes,
   aucune qualification juridique automatique.
5. `Chronologie`: avant AG, pendant AG/PV, apres AG, passation.
6. `Exports controles`: apercu avant export, public autorise obligatoire,
   restriction la plus forte heritee.

Premier viewport recommande:

- H1 reel `AG, contentieux, passation`, pas `Cockpit Conseil Syndical`;
- bandeau permanent `Dossier factuel - pas d'avis juridique automatique`;
- badge `Diffusion actuelle: conseil syndical uniquement`;
- bloc `A faire maintenant`: 3 a 5 actions maximum, chacune avec piece, preuve,
  echeance et restriction;
- CTA primaire `Traiter la prochaine action`;
- CTA secondaire `Preparer un apercu`, bloque si diffusion non revue;
- aucun export brut comme action principale.

Interactions attendues par ligne: `Rattacher une preuve`,
`Formuler la question AG`, `Demander une piece`,
`Marquer recu hors CoproScope` avec date + canal + note, `Revoir diffusion`,
`Preparer apercu`.

Exports autorises uniquement comme derives: `Liste de travail CS`,
`Pack passation restreint`, `Synthese coproprietaires apres masquage`.
Blocage export si restriction ou diffusion absente, contenu contentieux non
revu, chemin local, OCR/log, document brut, secret, nom nominatif inutile ou
table d'alias.

Contrat propose: `model.ux.ag_contentieux_dossier_probatoire_v1`.

## Retour back/viewmodel - CONV-2026-1664

Verdict: contrat public strict propose, sans modification code.

Nom canonique propose par back/viewmodel:
`model.ux.audit360_ag_contentieux_dossier_restreint_v1`.

Principes:

- projection publique en allowlist stricte;
- donnees autorisees: `examples/synthetic_copro`, fixtures fictives unitaires,
  lignes Audit360 fictives/publiques, derives deja anonymises;
- donnees exclues: `instances/`, instance privee, documents sources, OCR, logs,
  exports bruts, secrets, `RM-2026-0017` et `ORD-P0-990`;
- contentieux toujours factuel, confidentiel, CS uniquement par defaut;
- notes non juridiques seulement: rejet des avis juridiques, chances de gagner
  et consignes d'assigner;
- exports derives avec `source_of_truth=false`, watermark, omissions et
  restrictions heritees.

Objets publics autorises:

- `questions[]`: question, dossier, objectif, statut, source, preuves,
  decisions, actions, prochaine action, echeance, restriction et diffusion;
- `pieces[]`: piece, dossier, type document, preuve attendue, prochaine action,
  echeance, restriction et diffusion;
- `contentieux_cases[]`: dossier factuel, phase, resume factuel, derniere
  action, preuves, prochaine action, restriction confidentielle et diffusion CS;
- `non_legal_notes[]`: observations, signaux, preuves manquantes, limites,
  validateur, statut, prochaine action;
- `evidence[]`: preuve, source derivee, preuve de quoi, date, statut,
  restriction, diffusion, prochaine action;
- `timeline[]`: evenement, objet, resume, preuves, statut, restriction,
  diffusion;
- `controlled_exports[]`: profil, format, watermark, `source_of_truth=false`,
  restriction, diffusion, biffage requis, raison de blocage, omissions,
  apercu.

Champs interdits en JSON, HTML, export, logs de test et fixtures publiques:
`source_file`, `source_row_id`, `source_sha256`, `import_run_id`,
`payload_json`, `event_path`, `event_hash`, `event_id`,
`source_event_ids_json`, `created_from_event_hash`, `updated_from_event_hash`,
`locator_json`, `message_draft`, `original_path`, `original_name`,
`source_path`, `current_blob_id`, chemins locaux, `file://`, tokens, secrets,
emails, telephones, IBAN/RIB, OCR brut, logs, exports bruts, noms de fichiers
bruts sensibles, tables alias vers identite reelle, marqueurs `raw`,
`restricted`, `private`.

Tests back futurs: `test_public_ag_contentieux_dossier_read_model.py`, couvrant
allowlist exacte, import fictif -> dossier public, anti-fuite JSON/HTML/export,
restriction la plus forte, diffusion la plus limitee, non-avis-juridique,
export derive, modele vide sur et absence de `SELECT *`, `CREATE VIEW`,
FTS/MATCH.

## Retour front - CONV-2026-1663

Verdict: garder `/ag-contentieux` comme hub de synthese AG/contentieux/passation,
et creer ensuite une route detail dediee au lot, par exemple
`/ag-contentieux/dossiers/{dossier_id}`. Eviter une route utilisateur
`/audit360/...`: Audit360 reste provenance interne, l'ecran novice doit parler
de dossier AG/contentieux restreint.

Surface actuelle: route `/ag-contentieux`, template `agcontentieux.html` et
builder `agcontentieux_view.py`. Elle est utile comme vue d'ensemble, mais reste
surtout une page d'ancres/tableaux. Le test novice du 2026-05-21 confirme:
actions concretes insuffisantes par section, compteur nav incoherent, H1 topbar
encore `Cockpit Conseil Syndical`.

Implementation future recommandee:

- extraire la route actuelle et la future route detail dans
  `agcontentieux_route.py`;
- creer `agcontentieux_dossier_view.py`;
- creer `templates/agcontentieux_dossier.html`;
- enregistrer le routeur avant les catch-all de `part_004.pyfrag`;
- ne pas ajouter de logique dans `part_003.pyfrag`, proche du plafond;
- conserver un seul item principal `AG / contentieux` dans la navigation;
- ne jamais stocker le token dans le read model, utiliser `token_href(...)` au
  rendu;
- corriger le compteur de navigation ou le supprimer.

Premier viewport futur:

- titre `Dossier AG/contentieux restreint`;
- bandeau `Factuel - validation humaine requise - pas d'avis juridique`;
- quatre blocs: `Pieces`, `Questions AG`, `Echeances`, `Restrictions`;
- `Qui peut voir`;
- `Prochaine action`;
- CTA tokenises `Demander une preuve`, `Rattacher une piece`,
  `Preparer une question AG`, `Voir l'apercu de passation`.

Tests front futurs: `server/tests/test_ui_agcontentieux_dossier_route.py`,
couvrant 403/200 token, route non capturee par catch-all, H1 et premier
viewport, liens internes tokenises, anti-fuite, aucun verdict juridique,
etat vide sur identifiant inconnu ou path-like, captures desktop et mobile sans
scroll horizontal, plus smoke/security/no-private/line-limit.

Preuve executee par le role front: `python tools/check_code_line_limit.py` OK.

## Retour QA - CONV-2026-1665

Verdict: GO cadrage, NO-GO produit/livraison diffusable.

Raison: la surface `/ag-contentieux` et les tests existent deja, mais ce lot est
en lecture/cadrage, sans serveur reserve, sans captures live
desktop/mobile/tablette, et le novice a donne GO concept / NO-GO dev immediat.
Le worktree principal est sale. Aucun GO QA final sans owner dedie, instance
synthetique/test, token explicite et recette navigateur.

Panier QA futur obligatoire:

- token: `/ag-contentieux`, `/exports/passation`, `/exports/passation.json`,
  `/exports/passation.txt`, `/api/model` doivent faire 403 sans token et 200
  avec query/header/cookie; liens HTML token-safe, sans double token;
- anti-fuite HTML/API/export: refuser `C:\Users`, `file://`, `/Users`, `/home`,
  `raw`, `restricted`, `logs`, `private`, OCR brut, logs, secrets, emails,
  telephones, IBAN/RIB, tables alias;
- export controle: derive uniquement, `source_of_truth=false`, watermark
  obligatoire, preview avant telechargement, blocages visibles, pas de ZIP ou
  source brut;
- non-avis-juridique: autoriser seulement note non juridique, faits, preuves,
  echeances, actions humaines; bloquer chance de gagner, conseil juridique,
  assigner/poursuivre/attaquer, conclusion automatique;
- restrictions: chaque question/piece/dossier/note/pack affiche restriction,
  diffusion, statut, prochaine action et echeance; contentieux par defaut
  `confidentiel` + `conseil syndical`;
- no-private: utiliser seulement `examples/synthetic_copro` ou instance test
  anonymisee, jamais `instances/`, raw/OCR/logs/exports bruts/secrets;
- line-limit: garder tous fichiers code/templates/tests sous 600 lignes;
- smoke/regression: `test_ui_agcontentieux_route.py`,
  `test_ui_agcontentieux.py`, `test_agcontentieux.py`,
  `test_passation_exports.py`, `test_ui_passation_export_route.py`,
  `test_ui_security_routes.py`, `test_security_no_private_sync_leaks.py`,
  `test_ui_smoke_routes_expanded.py`, `test_code_line_limit.py`;
- captures live: desktop, mobile, tablette sur URL tokenisee avec port reserve;
  verifier premier viewport, absence de chevauchement, statut non officiel,
  diffusion, action reelle et pack verrouille si incomplet.

## Consolidation ORD-P0-012

Verdict equipe: `AGILE-DONE - equipe agile a fini son job`.

- A tester maintenant: rien en live; aucun serveur reserve.
- En dev maintenant: aucun dev. Le worktree principal reste sale et exclu.
- En enquete maintenant: tous les roles canoniques sont clotures.
- Commande prete: oui, comme commande future bornee, pas executee.
- Comparaison visuels enquete: la commande reprend la recherche gouvernance
  2026-05-24, le test novice live 2026-05-21 et les cadrages Audit360 P0-010
  et P0-011.
- Agents idle a relancer: aucun sans nouveau diff ou decision d'owner code.
- Decision requise: Brice doit decider explicitement s'il veut ouvrir un owner
  code dedie pour cette commande. Sans cela, le heartbeat passe au prochain
  `ORD-*` actionnable.
- Prochain mouvement: prochain heartbeat = choisir le prochain `ORD-*` P0
  actionnable, sans rouvrir ce lot.
- Tests/preuves: retours designer/novice/front/back/QA integres;
  `git diff --check` documentaire; front a lance `tools/check_code_line_limit.py`
  OK; aucun serveur, instance privee ou export.

Commande future bornee:

```text
Roadmap/chantier:
RM-2026-0008 / RM-2026-0024 / RM-2026-0025 / nouveau CH owner code dedie a
creer si Brice valide.

Objectif:
Livrer un dossier probatoire restreint AG/contentieux, token-safe, sur donnees
fictives/test ou derivees anonymisees uniquement.

UI cible:
Conserver `/ag-contentieux` comme hub. Ajouter si besoin une route detail
`/ag-contentieux/dossiers/{dossier_id}` avant catch-all, avec modules dedies
`agcontentieux_route.py`, `agcontentieux_dossier_view.py` et template
`agcontentieux_dossier.html`.

Read model:
`model.ux.audit360_ag_contentieux_dossier_restreint_v1`, projection publique
allowlist avec questions, pieces, dossiers contentieux factuels, notes non
juridiques, preuves, restrictions, diffusion, echeances, timeline et exports
controles.

Premier viewport:
`AG, contentieux, passation` ou `Dossier AG/contentieux restreint`,
`Dossier factuel - pas d'avis juridique automatique`,
`Diffusion actuelle: conseil syndical uniquement`, bloc `A faire maintenant`
avec 3 a 5 actions maximum, piece, preuve, echeance, restriction et prochaine
action.

Interactions:
`Rattacher une preuve`, `Formuler la question AG`, `Demander une piece`,
`Marquer recu hors CoproScope` avec date/canal/note, `Revoir diffusion`,
`Preparer apercu`. Aucun envoi, publication, qualification juridique, export
brut ou cloture automatique.

Exports:
Derives seulement: liste de travail CS, pack passation restreint, synthese
coproprietaires apres masquage. Preview avant telechargement, watermark,
`source_of_truth=false`, restriction la plus forte et diffusion la plus limitee.

Garde-fous:
validation humaine obligatoire; contentieux `confidentiel` et `conseil
syndical` par defaut; aucune note juridique automatique; pas de diffusion sans
revue explicite; preuve candidate non definitive.

Interdits:
instances privees, documents bruts, rapports nominatifs, OCR/logs, exports
bruts, secrets, RM-2026-0017/ORD-P0-990, chemins locaux, `file://`, tokens,
emails, telephones, IBAN/RIB, tables alias, `source_file`, `payload_json`,
`event_path`, `source_sha256`, `raw`, `restricted`, `private`, avis juridique,
chances de gagner, assigner/poursuivre/attaquer.

Tests:
`server/tests/test_ui_agcontentieux_dossier_route.py`,
`test_public_ag_contentieux_dossier_read_model.py`, `test_ui_agcontentieux*`,
`test_agcontentieux.py`, passation exports, security, no-private, smoke,
line-limit, `git diff --check`, `agent-check -Ui`, captures
desktop/mobile/tablette.
```

## Journal

| Horodatage | Conversation | Evenement | Trace |
|---|---|---|---|
| 2026-05-25 02:25 +02:00 | `CONV-2026-1660` | `START_AGILE_AUDIT360_AG_CONTENTIEUX` | `ORD-P0-011` est `AGILE-DONE`; nouveau chantier P0 ouvert sur `ORD-P0-012` en lecture/cadrage uniquement, sans code ni serveur. |
| 2026-05-25 02:25 +02:00 | `CONV-2026-1661`..`CONV-2026-1665` | `ROLES_RESERVED_AUDIT360_AG_CONTENTIEUX` | Designer, novice, front, back/viewmodel et QA reserves en lecture seule; aucun code, serveur, instance privee, document brut, export brut, secret ou `RM-2026-0017`. |
| 2026-05-25 02:26 +02:00 | `CONV-2026-1661`..`CONV-2026-1665` | `AGENTS_LAUNCH_PARTIAL_AUDIT360_AG_CONTENTIEUX` | Designer Chandrasekhar, novice Laplace et front Planck lances en lecture seule; back/viewmodel et QA restent reserves faute de capacite de threads. Aucun code, serveur, instance privee, document brut, export brut, secret ou `RM-2026-0017`. |
| 2026-05-25 02:27 +02:00 | `CONV-2026-1662` | `NOVICE_RETURN_AUDIT360_AG_CONTENTIEUX` | Laplace cloture: GO concept, NO-GO dev immediat tant que premier viewport, actions reelles par section, badges diffusion/restriction, statut non officiel, preuves manquantes et export controle ne sont pas clarifies. |
| 2026-05-25 02:27 +02:00 | `CONV-2026-1664` | `BACK_LAUNCHED_AUDIT360_AG_CONTENTIEUX` | Capacite liberee: Beauvoir lance en lecture seule sur contrat public allowlist AG/contentieux. QA reste a lancer. |
| 2026-05-25 02:28 +02:00 | `CONV-2026-1661` | `DESIGNER_RETURN_AUDIT360_AG_CONTENTIEUX` | Chandrasekhar cloture: route cible `/ag-contentieux`, premier viewport restreint, actions par ligne, exports controles et contrat `model.ux.ag_contentieux_dossier_probatoire_v1` proposes. |
| 2026-05-25 02:28 +02:00 | `CONV-2026-1665` | `QA_LAUNCHED_AUDIT360_AG_CONTENTIEUX` | Capacite liberee: Curie lancee en lecture seule sur panier QA, anti-fuite, non-avis-juridique, restrictions et exports controles. |
| 2026-05-25 02:29 +02:00 | `CONV-2026-1664` | `BACK_RETURN_AUDIT360_AG_CONTENTIEUX` | Beauvoir cloture: contrat public strict `model.ux.audit360_ag_contentieux_dossier_restreint_v1`, allowlist, champs interdits et tests back futurs fournis. |
| 2026-05-25 02:30 +02:00 | `CONV-2026-1663` | `FRONT_RETURN_AUDIT360_AG_CONTENTIEUX` | Planck cloture: garder `/ag-contentieux` comme hub, route detail future `/ag-contentieux/dossiers/{dossier_id}`, extraction route obligatoire, H1/compteur/nav a corriger et test `test_ui_agcontentieux_dossier_route.py`; line-limit OK. |
| 2026-05-25 02:30 +02:00 | `CONV-2026-1665` | `QA_RETURN_AUDIT360_AG_CONTENTIEUX` | Curie cloture: GO cadrage, NO-GO produit/livraison diffusable; panier futur token/anti-fuite/export controle/non-avis-juridique/restrictions/no-private/smoke/captures fourni. |
| 2026-05-25 02:30 +02:00 | `CONV-2026-1660`..`CONV-2026-1665` | `AGILE_DONE_AUDIT360_AG_CONTENTIEUX` | Equipe cloturee sans dev: commande future `/ag-contentieux` + detail `/ag-contentieux/dossiers/{dossier_id}` et contrat `model.ux.audit360_ag_contentieux_dossier_restreint_v1` prets pour owner code dedie si Brice valide; aucun code, serveur, instance privee, export brut, secret, push GitHub ni `RM-2026-0017`. |
