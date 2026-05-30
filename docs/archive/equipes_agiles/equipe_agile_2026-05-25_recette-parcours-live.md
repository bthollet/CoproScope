# Equipe agile - ORD-P0-036 Recette parcours live

Date de lancement: 2026-05-25 15:14 +02:00.
Mode: recette produit live, vitesse standard, serveur visible reserve, lecture seule tant qu'un ecart n'est pas qualifie.

## BOT-START

```text
BOT-START - Coordinateur-scribe recette parcours live - 2026-05-25 15:14 +02:00
Roadmap: RM-2026-0006 / RM-2026-0003
Ordre: ORD-P0-036 / RECETTE-NAVIGATEUR-PARCOURS
Chantier: CH-20260525-151456-RM-2026-0006-recette-parcours-live
Conversation: CONV-2026-1756
Role: Coordinateur-scribe recette parcours live
Mission: lever le blocage CONV-2026-1708 en reservant une recette live standard, puis faire qualifier le parcours cockpit -> audit/comptes -> action -> piece/demande -> preuve -> diffusion par designer, novice, dev-readiness et QA.
Ownership modifiable: docs/equipe_agile_2026-05-25_recette-parcours-live.md, docs/presence_agents.md, trace append-only docs/roadmap_backlog_central.md, heartbeat relance-equipe-agile-gouvernail-autonome, port temporaire 8788.
Fichiers a eviter: code applicatif, tests applicatifs hors execution, routes, templates, CSS, instances privees reelles, documents bruts, OCR/logs, exports bruts, secrets, serveurs non reserves, push GitHub, RM-2026-0017, ORD-P0-990, lots AGILE-DONE clos sans nouveau diff.
Passerelle/registre de trace: ce fichier, docs/presence_agents.md, docs/roadmap_backlog_central.md.
Dernier point lu: AGENTS.md, docs/protocole_equipe_agile_agents.md, docs/consignes_bots_interconversations.md, docs/protocole_roadmap_presence_agents.md, docs/orchestration_agents.md, docs/presence_agents.md, docs/roadmap_backlog_central.md, docs/equipe_agile_2026-05-25_recette-navigateur-parcours.md.
Tests/preuves attendus: serveur visible 8788, token 200/403, captures ou constats multi-viewport, test live cible si possible, watchdog/superviseur OK, absence de fuite.
Risque de collision: repo principal sale; roles en lecture seule; aucun owner code ouvert tant que la QA/novice/designer n'a pas qualifie un ecart et qu'une commande dev n'existe pas.
Lease ownership: 2026-05-25 17:14 +02:00.
Prochaine action: lancer le serveur visible sur port 8788, puis deleguer designer, novice, front-readiness, back-readiness et QA live.
```

## Reservation live

- Port reserve: `8788`.
- Instance cible: `C:\Users\brice\CoproScope\instances\beauvallon_test`.
- Token de recette: `parcours-live-local`.
- URL cible: `http://127.0.0.1:8788/?token=parcours-live-local`.
- Commande serveur prevue dans un PowerShell visible:

```powershell
.\server\.venv\Scripts\python.exe -m coproscope.cli ui open-test --instance-root C:\Users\brice\CoproScope\instances\beauvallon_test --year 2025 --host 127.0.0.1 --port 8788 --token parcours-live-local
```

## Roles ouverts

| Conversation | Role | Statut | Ownership |
|---|---|---|---|
| `CONV-2026-1756` | Coordinateur-scribe | EN_ATTENTE_USER | Registres et consolidation, port 8788 laisse ouvert pour reprise |
| `CONV-2026-1757` | Designer service / facilitateur | CLOTURE | Helmholtz `019e5f48-a541-7c43-bf64-20cc9261dc28` / lecture seule: GO partiel desktop, NO-GO mobile/diffusion large |
| `CONV-2026-1758` | Utilisateur novice / membre CS | CLOTURE | Gauss `019e5f48-a6a1-7881-a56f-f854ee2b27c2` / lecture seule: NO-GO novice |
| `CONV-2026-1759` | Dev front readiness | CLOTURE | Euclid `019e5f48-a71e-77f2-a0b9-a83ecfd77880` / lecture seule: cartographie front, aucun patch |
| `CONV-2026-1760` | Dev back/viewmodel readiness | CLOTURE | Carver `019e5f48-a7e1-7233-b449-cb3083525bb7` / lecture seule: cartographie back/perf, aucun patch |
| `CONV-2026-1761` | QA live / privacy | CLOTURE | Lovelace `019e5f48-a893-7690-a8fa-f4b0e37ac9cb` / lecture seule: NO-GO QA live |
| `CONV-2026-1767` | Testeur expert metier | CLOTURE | Hooke `019e5f53-6952-78b3-a449-d1737697688c` / lecture seule: NO-GO metier juridique, compta, process chantier, syndic |

## Point de coordination initial

- A tester maintenant: cockpit, comptes/audit, actions, pieces, demandes/depot, confidentialite et export passation sur `8788`.
- En dev maintenant: aucun dev; front/back restent en readiness lecture seule.
- En enquete maintenant: designer et novice qualifient l'UI reelle, pas une intention abstraite.
- Commande prete: recette live `ORD-P0-036`; aucune commande de patch.
- Comparaison visuels enquete: verifier premier viewport, action principale, preuve/source, prudence de diffusion et absence de jargon moteur visible.
- Agents idle a relancer: aucun pour l'instant.
- Decision requise: si la recette remonte un ecart, ouvrir ensuite seulement un owner code dedie avec commande bornee.
- Prochain mouvement: serveur visible, puis retours agents et preuves.
- Tests/preuves: watchdog/superviseur OK a 15:13; serveur et checks live a produire.

## Synthese des retours

Verdict global: **NO-GO produit live**.

Points positifs:

- serveur visible `8788` disponible; cockpit tokenise `200`, acces sans token `403`;
- routes HTML principales tokenisees et rapides dans les checks back-readiness;
- garde-fous token/confidentialite OK sur le perimetre QA;
- cockpit desktop comprehensible en recette accompagnee.

Blocages confirmes:

- `/pieces?proof=missing` est vide, donc le parcours piece -> relance -> depot ne peut pas etre deroule;
- `/actions?priority=P1` ne porte pas clairement l'action `Rattacher une piece`;
- `/pieces?proof=missing` manque les actions humaines `Creer demandes syndic` et `Ajouter reponse recue`;
- `/documents/ajouter` manque `Ajout de document` et `Prochaine action` assez haut dans le premier viewport;
- mobile: navigation, titres et CTA tronques ou trop serres;
- novice: incoherence percue entre compteurs du cockpit et listes vides;
- langage encore trop technique sur certains ecrans (`P0/P1/P2`, `preuve candidate`, `biffage`, `artefacts`, etc.);
- performance: `/api/model` et lecture complete de certains exports depassent les delais acceptables.

## Commande corrective bornee proposee

Objectif utilisateur:

- permettre a un membre de conseil syndical novice de suivre le parcours `ORD-P0-036` sans contradiction: voir les priorites, ouvrir les actions, comprendre les pieces manquantes, preparer une demande ou ajouter une reponse recue, puis verifier la diffusion.

UI cible reelle:

- serveur actuel: `http://127.0.0.1:8788/?token=parcours-live-local`;
- routes minimales: `/actions?priority=P1`, `/pieces?proof=missing`, `/documents/ajouter`, `/demandes/relance`, `/depot`, mobile 390px.

Structure visuelle attendue:

- premier viewport de chaque route avec titre humain, etat de la file, prochaine action et prudence de diffusion;
- etats vides utiles qui proposent une action humaine, pas seulement `0`;
- CTA mobile non tronques et navigation compacte lisible.

Composants et donnees:

- conserver les donnees de test locales et les derives publics;
- si aucune piece manquante n'existe, afficher un etat vide actionnable avec `Creer demande syndic` et `Ajouter reponse recue`;
- ne pas utiliser d'id synthetique introuvable comme preuve de parcours.

Interactions:

- aucun envoi automatique;
- liens tokenises conserves;
- actions `Rattacher une piece`, `Creer demande syndic`, `Ajouter reponse recue` visibles et dirigeant vers une route utile ou un etat explique.

Criteres d'acceptation:

- `tests.test_ui_live_ux_contract -v` vert ou limitation documentee si l'instance n'a volontairement aucune piece manquante;
- `/documents/ajouter` expose `Ajout de document` et `Prochaine action` dans le premier viewport;
- mobile 390px sans CTA principal tronque ni navigation coupee;
- token `200/403` conserve;
- pas de fuite de chemin local, raw/restricted/logs/secret;
- `tools/check_code_line_limit.py` OK.

Ownership futur conseille:

- un seul owner front pour templates/CSS et etats vides;
- un seul owner back/viewmodel separe si la correction touche projections ou `/api/model`;
- ne pas modifier `server/src/coproscope/web/_app_fragments/part_003.pyfrag` sans extraction ou justification, car il est au plafond.

## Resultat

Statut: recette qualifiante terminee sans patch code; coordinateur en
`EN_ATTENTE_USER` pour decision avant owner code. Le serveur visible `8788`
reste ouvert volontairement pour reprise locale; arret uniquement par `Ctrl+C`
dans la fenetre PowerShell visible.

## Journal

| Horodatage | Conversation | Evenement | Trace |
|---|---|---|---|
| 2026-05-25 15:14 +02:00 | `CONV-2026-1756` | `START_AGILE_RECETTE_PARCOURS_LIVE` | Demande Brice: lancer une equipe agile, vitesse standard. Reprise de `ORD-P0-036` avec serveur visible reserve `8788`, instance `beauvallon_test`, token `parcours-live-local`; roles lecture seule ouverts, aucun owner code. |
| 2026-05-25 15:16 +02:00 | `CONV-2026-1756` | `SERVER_LIVE_8788` | Serveur `ui open-test` lance dans un PowerShell visible: `/health` 200, `/?token=parcours-live-local` 200, `/` sans token 403. Le serveur reste a arreter par `Ctrl+C` dans la fenetre visible. |
| 2026-05-25 15:17 +02:00 | `CONV-2026-1757`..`CONV-2026-1761` | `AGENTS_LAUNCHED_RECETTE_PARCOURS_LIVE` | Agents Helmholtz, Gauss, Euclid, Carver et Lovelace lances en lecture seule; livrables attendus = GO/NO-GO designer, novice, readiness front/back et QA live. |
| 2026-05-25 15:19 +02:00 | `CONV-2026-1756` | `LIVE_CONTRACT_NO_GO` | `tests.test_ui_live_ux_contract -v` sur `http://127.0.0.1:8788`, token `parcours-live-local`: 6 tests lances, 2 OK, 6 sous-echecs. Echecs: `/actions?priority=P1` manque `Rattacher une piece`; `/pieces?proof=missing` manque `Creer demandes syndic`; detail piece utilise l'id synthetique introuvable; relance piece manque `Brouillon a copier, non envoye`; `/documents/ajouter` manque `Ajout de document` et contenu utile trop bas. NO-GO produit live; aucun patch ouvert avant retours designer/novice/QA et commande bornee. |
| 2026-05-25 15:25 +02:00 | `CONV-2026-1757`..`CONV-2026-1761` | `AGENTS_RETURNED_RECETTE_PARCOURS_LIVE` | Retours consolides: designer GO partiel desktop mais NO-GO mobile/diffusion large; novice NO-GO a cause des compteurs/listes incoherents, filtres actions et exports; front-readiness identifie les templates/routes/CSS candidats sans patch et signale `part_003.pyfrag` a 600 lignes; back-readiness confirme routes HTML tokenisees OK mais `/api/model` depasse 120 s; QA live confirme NO-GO, token `200/403`, probes prives sans fuite evidente et contrat live rouge. |
| 2026-05-25 15:27 +02:00 | `CONV-2026-1756` | `RECETTE_PARCOURS_LIVE_POINT_REPRISE` | Preuves complementaires coordinateur: `test_ui_smoke_routes_expanded`, `test_ui_security_routes` et `test_security_no_private_sync_leaks` = 17 OK; navigateur integre indisponible cote coordinateur apres erreur transport, captures headless produites hors depot par designer/QA mais pas de clic interactif ni depot fichier. Verdict: NO-GO produit live, roles standard clos, coordinateur en attente decision Brice pour ouvrir ou non un owner code unique avec commande de correction bornee. |
| 2026-05-25 15:28 +02:00 | `CONV-2026-1767` | `TESTEUR_EXPERT_METIER_RETURN` | Demande Brice: ajouter ce role si le budget de threads le permet. Hooke rendu: NO-GO metier global, avec NO-GO juridique, compta, process chantier et syndic. P0: boucle action -> piece -> demande syndic -> preuve a fermer; statut `brouillon non envoye` obligatoire. P1: coherences compteurs/listes et performance. P2: contenu utile de l'ajout document a remonter. Checklist future: preuve attendue, source, action humaine suivante, statut d'envoi, statut de diffusion et coherence inter-ecrans. |
| 2026-05-25 15:31 +02:00 | `CONV-2026-1756` | `COMMANDE_CORRECTIVE_BORNEE` | Commande corrective bornee ajoutee: UI cible `/actions?priority=P1`, `/pieces?proof=missing`, `/documents/ajouter`, `/demandes/relance`, `/depot`, mobile 390px; owner code futur seulement sur decision Brice. |
| 2026-05-25 15:35 +02:00 | `CONV-2026-1756` / `CONV-2026-1771` | `DECISION_BRICE_RELANCE_CORRECTION` | Demande Brice: lancer une equipe agile. Decision interpretee comme GO operationnel pour ouvrir un owner code unique sur la commande corrective bornee; le lot recette live passe en reprise par `CH-20260525-153000-RM-2026-0006-correction-parcours-live`. |
