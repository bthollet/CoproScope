# Equipe agile - recette DocOps Codex

Date: 2026-05-25 01:17 +02:00.
Rattachement: `ORD-P0-001`, `RM-2026-0003`, `RM-2026-0029`, `RM-2026-0006`, `RM-2026-0022`.
Chantier: `CH-20260525-011716-RM-2026-0003-recette-docops-agile`.

## BOT-START - Coordinateur-scribe - 2026-05-25 01:17 +02:00

Roadmap: `RM-2026-0003` / `RM-2026-0029` / `RM-2026-0006` / `RM-2026-0022`.
Chantier: `CH-20260525-011716-RM-2026-0003-recette-docops-agile`.
Conversation: `CONV-2026-1639` (renumerote depuis `CONV-2026-1633` pour lever une collision de presence).
Role: coordinateur-scribe agile.
Mission: lancer une equipe agile autour de la recette active `ORD-P0-001`, sans dupliquer la QA `CONV-2026-1632`.
Ownership modifiable: cette trace, `docs/presence_agents.md`, heartbeat `relance-equipe-agile-gouvernail-autonome`.
Fichiers a eviter: code, tests, templates, CSS, instances privees, documents bruts, OCR/logs, exports bruts, secrets, push GitHub, `RM-2026-0017`.
Passerelle/registre de trace: ce fichier et `docs/presence_agents.md`.
Dernier point lu: `AGENTS.md`, `docs/protocole_equipe_agile_agents.md`, `docs/protocole_roadmap_presence_agents.md`, `docs/consignes_bots_interconversations.md`, `docs/roadmap_backlog_central.md`, `docs/presence_agents.md`, point live `docs/point_coordination_live_8766_2026-05-21.md`.
Tests/preuves attendus: GO/NO-GO sur routes reelles inbox physique configurable -> `/documents/ajouter?source=inbox`, puis `/documents/ajouter` et `/documents/tri-feedback`, port `8771` deja reserve par `CONV-2026-1632`, captures ou raison explicite de non-capture, aucune fuite de donnees privees.
Risque de collision: depot principal sale; aucun dev code ne demarre depuis ce chantier sans nouveau worktree/owner unique.
Lease ownership: 2026-05-25 03:17 +02:00.
Prochaine action: mettre a jour la heartbeat, lancer designer/novice/front/back en lecture seule, consolider leurs retours avec la QA existante.

## Point de coordination initial

- A tester maintenant: lien inbox physique configurable -> `/documents/ajouter?source=inbox`, puis `/documents/ajouter` et `/documents/tri-feedback` sur la recette `ORD-P0-001` port `8771`.
- En dev maintenant: aucun dev code dans le worktree principal; dev front/back en lecture seule.
- En enquete maintenant: designer et novice qualifient l'UI reelle, les libelles, les CTA et les risques de confusion.
- Commande prete: recette navigateur active `CONV-2026-1632`; pas de commande dev tant que la recette n'a pas rendu un manque fonctionnel borne.
- Comparaison visuels enquete: utiliser les recherches UX ajout-docs du 2026-05-24 comme reference; si aucune image precise ne s'applique, tracer la justification.
- Agents idle a relancer: designer, novice, dev front lecture, dev back lecture; QA deja active via `CONV-2026-1632`.
- Decision requise: aucune decision Brice immediate; no-go si le parcours ne montre pas clairement inbox physique, ajout, tri/correction, restriction de diffusion et trace.
- Prochain mouvement: sous-agents lisent le code/doc utile en lecture seule et rendent leurs criteres avant integration ou patch.
- Tests/preuves: `git diff --check` documentaire apres inscription; preuves UI attendues par `CONV-2026-1632`.

## Roles lances

| Conversation | Role | Agent | Statut |
|---|---|---|---|
| `CONV-2026-1634` | Designer service / facilitateur | Huygens `019e5c4a-f6e5-7370-aa31-f5fd536ae3dc` | Lecture seule |
| `CONV-2026-1635` | Utilisateur novice / membre CS | Heisenberg `019e5c4a-f786-7ee3-9982-ddcab4e708d0` | Lecture seule |
| `CONV-2026-1636` | Dev front lecture seule | Schrodinger `019e5c4a-f96e-72a1-b28d-6dc49e99b358` | CLOTURE |
| `CONV-2026-1637` | Dev back / viewmodel lecture seule | Bacon `019e5c4a-fb9d-7af3-ba2b-03f849d320d9` | CLOTURE |

QA terminee: `CONV-2026-1632`, recette navigateur Codex sur port `8771`, GO Codex conditionnel sur donnees fictives; limite: `tri-feedback` reste synthetique et pas relie au fichier uploade.
Heartbeat active: `relance-equipe-agile-gouvernail-autonome`, cadence 5 minutes.

## Retour novice - `CONV-2026-1635`

Statut: `CLOTURE`, aucun fichier modifie, aucun serveur lance.

Verdict: GO conditionnel pour continuer la recette sur donnees fictives; NO-GO produit avant dev fonctionnel large.

Points bloquants ou a surveiller:

- Premier viewport de `/documents/ajouter` trop domine par la coque, le titre `Cockpit Conseil Syndical`, la recherche et `+ Nouvelle demande`.
- Le novice doit voir sans scroller: `Ajouter des documents`, l'action de depot et `Le fichier reste local. Rien n'est envoye ni partage.`
- `/documents/tri-feedback` est globalement clair, mais `Exporter le registre local CSV/JSON` arrive trop tot et peut etre compris comme un envoi ou une publication.
- Le parcours ne doit pas laisser croire que `tri-feedback` corrige le fichier reellement uploade si le jeu teste reste synthetique.
- `Reserve CS` exige un motif; `Masquer avant partage` exige pages/plages; `A decider plus tard` signifie explicitement aucune diffusion.

Libelles candidats si un futur owner code est ouvert:

- `Exporter le registre local CSV/JSON` -> `Telecharger la trace locale des corrections`.
- `Reserve CS` -> `Reserve au conseil syndical avec motif`.
- `A masquer avant partage` -> `Masquer des pages avant partage`.
- `A decider plus tard` -> `A decider plus tard - rien ne sera partage`.
- `doc_id`, `empreinte`, `reference opaque` -> `reference interne`.

## Retour designer - `CONV-2026-1634`

Statut: `CLOTURE`, aucun fichier modifie, aucun serveur lance.

References utilisees: captures fictives de recette `01-ajouter-initial.png`, `03b-ajouter-qualifie-details.png`, `05-ajouter-documents-section.png`, `07-tri-feedback-top.png`, `08b-tri-feedback-status.png`; recherches UX ajout-docs du 2026-05-24.

Blueprint court:

- `/documents/ajouter?source=inbox` doit rester l'atelier novice: tache claire, depot local, badges `sans IA/cloud` et `rien n'est partage`, progression en 4 etapes.
- Apres depot: carte par piece avec type, confidentialite, motif/pages si restriction, puis rattachement point -> action -> preuve.
- Le tri de lot reste un choix volontaire: `Corriger une file de documents`, CTA `Ouvrir le tri de lot`, secondaire `Continuer document par document`.
- `/documents/tri-feedback` reste la vue de correction rapide: DocOps propose, l'humain confirme; exports CSV/JSON secondaires sous un bloc `trace locale`.

Commande novice pre-dev:

> J'ouvre `/documents/ajouter?source=inbox`. Je dois comprendre en moins de 30 secondes que mes fichiers restent locaux, choisir soit un traitement document par document, soit `Ouvrir le tri de lot` si une file existe. Dans le tri, je corrige type, visibilite, motif et pages sensibles, puis j'enregistre une trace locale avant tout export.

GO pre-dev conditionnel: captures desktop + mobile prouvent le pont visible, le choix volontaire, le CTA principal correct, la trace locale, le retour possible vers ajout et aucune fuite privee.

NO-GO: tri automatique, jargon non explique, export avant decision, restriction sans motif, page sensible non bloquante ou donnee brute visible.

## Retour front - `CONV-2026-1636`

Statut: `CLOTURE`, aucun fichier modifie, aucun serveur lance, aucun test execute.

Risques front:

- Premier viewport `/documents/ajouter`: l'action de depot est en deuxieme bloc apres titre, badges, KPI et progression; sur petit ecran le CTA peut passer sous le pli.
- Premier viewport `/documents/tri-feedback`: exports CSV/JSON visibles avant les corrections, donc mauvais signal possible.
- Responsive: table 6 colonnes dans `/documents/ajouter`; 5 KPI dans une grille generique prevue pour 4 colonnes dans `tri-feedback`.
- Libelles techniques visibles: `DocOps feedback`, `DocOps local`, `PV_AG`, `A_MASQUER`, `A_DECIDER`, `reserve CS`.
- Token et ordre route: pas de fail identifie; `/documents/tri-feedback` reste bien enregistre avant `/documents/{doc_id}`.

Correctifs minimaux candidats, uniquement si QA/novice confirment:

- Ajouter un titre/topbar specifique a `/documents/ajouter` et remonter le bloc depot avant KPI/progression.
- Mettre les exports de `/documents/tri-feedback` en secondaires apres la liste, sous `trace locale`.
- Remplacer les valeurs techniques par labels humains.
- Ajouter un lien retour tokenise vers `/documents/ajouter` depuis `tri-feedback`.

Contraintes: `part_003.pyfrag` fait 597 lignes et `document_intake_view.py` 587 lignes; toute retouche doit probablement extraire plutot qu'ajouter.

## Retour back/viewmodel - `CONV-2026-1637`

Statut: `CLOTURE`, aucun fichier modifie, aucun serveur lance, aucun test execute.

Risques back/viewmodel:

- Token: garde OK; ne pas recopier captures/HTML avec token.
- Ordre routes: OK, `register_docops_feedback_routes(...)` passe avant `/documents/{doc_id}`.
- Anti-fuite: globalement OK; vigilance sur `inbox-reconstruction:<doc_id>` qui est opaque mais mauvais signal produit pour ce chantier hors `RM-2026-0017`.
- Exports derives: OK, `source_of_truth=false`, `dataset_kind=derived_feedback_register`, `DERIVED_DOCOPS_FEEDBACK`, tokenises.
- Manque principal: `/documents/tri-feedback` lit `SYNTHETIC_DOCOPS_PROPOSALS`; il ne reprend pas le fichier uploade ni les lignes inbox de `/documents/ajouter`.
- Contrat viewmodel: ces surfaces passent par contextes top-level `document_intake` et `docops_feedback`, pas par `model.ux.*`.

Panier de tests recommande avant futur GO code:

```powershell
.\.venv\Scripts\python.exe -m unittest tests.test_ui_docops_feedback_route tests.test_ui_document_intake_route tests.test_ui_document_intake tests.test_document_intake tests.test_ui_security_routes tests.test_security_no_private_sync_leaks tests.test_code_line_limit -v
```

## BOT-END - Coordinateur-scribe - 2026-05-25 01:29 +02:00

Roadmap: `RM-2026-0003` / `RM-2026-0029` / `RM-2026-0006` / `RM-2026-0022`.
Chantier: `CH-20260525-011716-RM-2026-0003-recette-docops-agile`.
Conversation: `CONV-2026-1639`.
Statut: `CLOTURE`.
Fichiers modifies: ce fichier et `docs/presence_agents.md`.
Fichiers volontairement evites: code, tests, templates, CSS, instances privees, documents bruts, OCR/logs, exports bruts, secrets, serveurs locaux, push GitHub, `RM-2026-0017`.
Tests/preuves: retours QA `CONV-2026-1632`, designer `CONV-2026-1634`, novice `CONV-2026-1635`, front `CONV-2026-1636`, back `CONV-2026-1637`; `git diff --check` documentaire attendu.
Limites: recette conditionnelle sur donnees fictives; pas de dev, pas de tests applicatifs lances par le coordinateur; `tri-feedback` reste synthetique et non relie au fichier uploade; serveur `8771` annonce actif par QA a arreter manuellement par `Ctrl+C` si encore ouvert.
Questions ouvertes: faut-il ouvrir `ORD-P0-002` pour raccorder reellement inbox/upload -> tri-feedback et nettoyer les libelles?
Prochain mouvement propose: soit recette navigateur desktop/mobile du pont inbox existant, soit owner code unique en worktree dedie pour un increment borne.

AGILE-DONE - equipe agile a fini son job
