# Equipe agile - compta multi-sources verrouillage

Date de lancement: 2026-05-24 20:08 +02:00.
Roadmap: `RM-2026-0030`.
Chantier: `CH-20260524-200801-RM-2026-0030-compta-multisources-verrouillage`.
Conversation coordination: `CONV-2026-1532`.
Mode: equipe agile gouvernail, verrouillage avant chantier dev.
Statut: verrouillage consolide - pret a arbitrage dev separe.

## BOT-START

BOT-START - Coordinateur-scribe agile - 2026-05-24 20:08 +02:00

Roadmap: `RM-2026-0030`.
Chantier: `CH-20260524-200801-RM-2026-0030-compta-multisources-verrouillage`.
Conversation: `CONV-2026-1532`.
Role: Coordinateur-scribe agile.
Mission: lancer immediatement une equipe agile guidee par le gouvernail pour verrouiller les questions ouvertes du cadrage compta multi-sources avant tout chantier dev.
Ownership modifiable: ce document, `docs/presence_agents.md`, ligne gouvernail `RM-2026-0030`.
Fichiers a eviter: code applicatif, tests applicatifs, instances privees, donnees comptables reelles, exports bruts, secrets, serveur local `CONV-2026-1525`, chantier bloque `RM-2026-0017`, fichiers sales sans owner explicite.
Passerelle/registre de trace: ce document, `docs/presence_agents.md`, `docs/roadmap_backlog_central.md`.
Dernier point lu: `AGENTS.md`, `docs/protocole_equipe_agile_agents.md`, `docs/protocole_roadmap_presence_agents.md`, `docs/consignes_bots_interconversations.md`, `docs/equipe_agile_2026-05-24_compta-multisources.md`, gouvernail et presence au 2026-05-24 20:08 +02:00.
Tests/preuves attendus: arbitrage MVP, contrat data v1 ferme, GO/NO-GO novice final, panier QA, owner code futur; aucun test applicatif tant que le dev n'est pas ouvert.
Risque de collision: worktree tres sale; le lot `ajout-docs/tri-feedback` est deja bloque par collisions; cette equipe reste sur `RM-2026-0030` et ne touche pas le code.
Lease ownership: 2026-05-24 22:08 +02:00.
Prochaine action: lancer les cinq roles en lecture seule et consolider leurs retours.

## UI cible

- Route candidate: `/comptes/rapprochement`.
- Ecran source: `Controle des comptes`.
- Visuels de reference:
  - `docs/assets/compta-multisources-2026-05-24/01-file-validation-4-sources.png`
  - `docs/assets/compta-multisources-2026-05-24/02-matrice-rapprochement.png`
  - `docs/assets/compta-multisources-2026-05-24/03-suggestions-classees.png`
- Cadrage source: `docs/equipe_agile_2026-05-24_compta-multisources.md`.

## Questions a verrouiller

- `Decision / devis` couvre-t-il aussi contrat, PV AG, bon de commande et reception des le MVP ?
- Les statuts orange non revus bloquent-ils l'export AG ou seulement les rouges ?
- `Sources orphelines` entre-t-il dans la premiere tranche ou reste-t-il hors MVP ?
- Qui peut marquer une ligne comme verifiee ?
- Ou persister exactement les evenements append-only de validation humaine ?
- Le Concept 1 suffit-il comme reference visuelle ou faut-il un blueprint derive avant dev ?

## Roles actifs

| Role | Conversation | Statut | Mission |
|---|---|---|---|
| Coordinateur-scribe | `CONV-2026-1532` | `EN_COURS` | Cadrer, relancer, consolider, tenir presence et gouvernail. |
| Designer service / facilitateur | `CONV-2026-1533` / Meitner `019e5b2f-6951-79d1-b1aa-95d358fe868d` | `CLOTURE` | Concept 1 retenu, blueprint textuel leger requis, no-go si les trois concepts restent a egalite. |
| Utilisateur novice / representant CS | `CONV-2026-1534` / Ampere `019e5b2f-6ac1-7b92-954a-21d6d4f12705` | `CLOTURE` | GO novice conditionnel; rouge bloque, orange seulement avec reserve explicite. |
| Dev back / read model | `CONV-2026-1535` / Gauss `019e5b2f-6b60-7323-9959-ea71e70c6be3` | `CLOTURE` | Contrat `compta_reconciliation_queue_v1`, event append-only et champs interdits consolides. |
| Dev front | `CONV-2026-1536` / Mencius `019e5b2f-6c1e-72f1-a801-1d40ed60c561` | `CLOTURE` | Owner front futur isole; route/template/CSS/tests dedies recommandes; collision `part_003.pyfrag`. |
| QA privacy / regression | `CONV-2026-1537` / Euler `019e5b2f-6cfd-7682-b856-4198dfbc7305` | `CLOTURE` | Panier QA token, anti-fuite, read model public, events append-only et export AG consolide. |

## Point court initial

A produire: arbitrage des six questions ouvertes, commande UI stabilisee, owner code futur, panier QA.

En dev: rien. Aucun patch tant que les roles n'ont pas donne le GO et que le worktree sale n'a pas un owner explicite.

En test: aucun test applicatif lance; QA prepare le panier.

En enquete: comparaison du Concept 1 avec les deux vues secondaires et les libelles novice.

Agents idle a relancer: aucun; cinq roles lances en lecture seule.

Decision requise: ouvrir ou non un chantier dev separe apres consolidation.

Prochain mouvement: attendre les retours roles, consolider, puis marquer `PRET_A_INTEGRER`, `BLOQUE` ou ouvrir une commande dev separee.

Tests/preuves: trace de mission, presence agents, retours roles, puis `git diff --check` documentaire.

## Synthese consolidee

Verdict: equipe agile lancee et verrouillage termine. La suite peut etre
preparee, mais le dev reste no-go dans ce passage.

MVP retenu: Concept 1, file de lignes a verifier sur
`/comptes/rapprochement`. Le Concept 2 devient une vue secondaire
audit/completude. Le Concept 3 devient le panneau detail d'une ligne ambigue.

Reference visuelle: `docs/assets/compta-multisources-2026-05-24/01-file-validation-4-sources.png`.
Pas de nouvelle image requise avant dev si le blueprint textuel ci-dessous est
repris tel quel.

Message obligatoire en haut de page:

- `Suggestions de controle, pas comptabilite officielle`;
- `Mode prive local`;
- `Lignes a verifier avec leurs preuves`.

Regle novice: aucune ligne n'est validee par la machine seule. Toute action
humaine est datee et append-only. Aucun bouton ne doit suggerer un envoi
automatique au syndic.

## Decisions verrouillees

- `Decision / devis` devient `Decision, devis ou contrat` dans l'UI novice,
  avec extension future possible a PV AG, bon de commande et reception.
- `Sources orphelines` reste hors MVP; libelle futur possible:
  `Pieces sans ligne comptable trouvee`.
- Rouge: bloque l'ajout au rapport AG tant qu'un humain n'a pas revu le point.
- Orange: autorise seulement une sortie avec reserve explicite et visible.
- `Ajouter au rapport AG` devient `Ajouter au brouillon du rapport AG avec
  reserve`.
- `Valider` seul est evite; utiliser `Marquer comme verifie` ou
  `Valider avec reserve`.

## Contrat v1

Read model public: `compta_reconciliation_queue_v1`.

Objets exposes:

- `context`: schema, route, exercice, mode prive, `source_of_truth=false`,
  date de generation;
- `summary`: lignes totales, a revoir, sources manquantes, conflits,
  validees, validees avec reserve, bloquees export;
- `queue[]`: identifiant public de ligne, date, montant, compte public,
  libelle public, statut, raison publique, prochaine action, href, cellules,
  candidats et derniere validation humaine;
- `source_cell`: famille `accounting`, `bank`, `invoice` ou
  `decision_evidence`, statut, raison publique, refs publiques, lien detail,
  blocage export;
- `candidate_bundle`: rang, confiance lisible, raisons publiques, familles
  manquantes, conflits, etat de validation;
- `human_validation`: decision append-only, acteur par role non nominatif,
  horodatage, reserve publique, visibilite rapport AG, remplacement logique
  eventuel.

Decisions humaines v1: `validate`, `validate_with_reserve`, `reject`,
`request_piece`, `request_decision_or_quote`, `add_to_ag_report`,
`leave_open`.

Persistance candidate: evenement append-only signe, type a stabiliser avant
dev, par exemple `accounting.reconciliation_human_validation_recorded`.
La projection publique reste reconstructible et ne devient pas source de verite.

Champs interdits: chemins locaux, racines `raw` / `restricted` / `logs` /
`private`, `file://`, token, secret, email, IBAN/RIB complet, hash/source SHA
prive, `payload_json`, `event_path`, `source_path`, `source_file`,
`original_path`, `original_name`, `locator_json`, texte OCR brut, brouillon brut
et note interne non nettoyee.

## Owner code futur

Ouvrir un chantier dev separe seulement avec owner unique, idealement dans un
worktree propre:

- route: insertion minimale `/comptes/rapprochement`, probablement dans
  `server/src/coproscope/web/_app_fragments/part_003.pyfrag`, fichier deja sale
  et proche de 600 lignes;
- template: nouveau
  `server/src/coproscope/web/templates/accounting_reconciliation.html`;
- CSS: nouveau bloc ou fichier dedie, plutot que grossir
  `styles_part_07.css` / `styles_part_08.css`;
- tests: nouveau `server/tests/test_ui_comptes_rapprochement.py`, plus
  securite/read model/privacy/export selon perimetre.

Ne pas reutiliser `accounting.html` comme ecran principal du MVP.

## Panier QA futur

Tests cibles a reprendre selon lot:

- `server/tests/test_ui_security_routes.py`;
- `server/tests/test_security_no_private_sync_leaks.py`;
- `server/tests/test_public_read_models.py`;
- `server/tests/test_ui_comptes_guide.py`;
- `server/tests/test_ui_passation_export_route.py`;
- `server/tests/test_passation_exports.py`;
- `server/tests/test_comptascope.py`;
- `server/tests/test_ui_smoke_routes_expanded.py`;
- `server/tests/test_events_v1.py`;
- `server/tests/test_plugins_results.py`.

Donnees de test: 100 % synthetiques, avec cinq lignes novice minimales:
ligne complete, facture manquante, decision/devis/contrat manquant, conflit de
montant, brouillon AG avec reserve.

Preuves attendues avant GO QA: route reelle tokenisee, hrefs token-safe,
read model allowliste, deux validations successives append-only, export derive
avec `source_of_truth=false`, scan anti-marqueurs sur HTML/JSON/exports.

## Decision finale

Statut: `PRET_A_INTEGRER` cote cadrage. `NO-GO_DEV_IMMEDIAT` tant que:

- le worktree reste sale sur les routes/read models/tests sensibles;
- l'owner code unique n'est pas declare;
- le type d'evenement append-only n'est pas stabilise;
- le jeu synthetique et les tests dedies ne sont pas ouverts.

Prochain mouvement: si Brice confirme la suite dev, ouvrir un chantier separe
sur `/comptes/rapprochement` avec owner unique route/read model/template/CSS/test
et aucune instance privee.

## BOT-END

BOT-END - Coordinateur-scribe agile - 2026-05-24 20:15 +02:00

Roadmap: `RM-2026-0030`.
Chantier: `CH-20260524-200801-RM-2026-0030-compta-multisources-verrouillage`.
Conversation: `CONV-2026-1532`.
Statut: PRET_A_INTEGRER.
Fichiers modifies: `docs/equipe_agile_2026-05-24_compta-multisources-verrouillage.md`, `docs/presence_agents.md`, `docs/roadmap_backlog_central.md`.
Fichiers volontairement evites: code applicatif, tests, instances privees, donnees comptables reelles, exports bruts, secrets, serveur local, fichiers sales sans owner explicite, `RM-2026-0017` bloque.
Tests/preuves: cinq roles lecture seule consolides; doublons fermes; `git diff --check` documentaire a lancer.
Limites: pas de route livree, pas de test navigateur, pas de patch; GO produit conditionnel uniquement.
Questions ouvertes: arbitrage Brice pour ouvrir un chantier dev separe avec worktree propre ou owner unique sur route/read model/tests.
Prochain mouvement propose: ouvrir une suite dev dediee `comptes-rapprochement-v1` si Brice valide le blueprint textuel et les gates QA.

## Journal

| Heure | Conversation | Evenement | Note |
|---|---|---|---|
| 2026-05-24 20:08 +02:00 | `CONV-2026-1532` | `BOT-START` | Vague de verrouillage lancee sur `RM-2026-0030`; aucun code, serveur, instance privee ni donnee comptable reelle. |
| 2026-05-24 20:10 +02:00 | `CONV-2026-1533`..`CONV-2026-1537` | `AGENTS_LAUNCHED` | Agents Meitner, Ampere, Gauss, Mencius et Euler lances en lecture seule. |
| 2026-05-24 20:15 +02:00 | `CONV-2026-1533`..`CONV-2026-1537` | `VERROUILLAGE_DONE` | Roles consolides: Concept 1, GO novice conditionnel, read model public, owner front futur et panier QA anti-fuite. `NO-GO_DEV_IMMEDIAT`. |
