# Equipe agile - WorksOps integration et recette

Date de lancement: 2026-05-25 09:19 +02:00.
Roadmap: `RM-2026-0032`.
Ordre: `ORD-P0-040` / `WORKSOPS-TRAVAUX-SUIVIS`.
Chantier: `CH-20260525-091900-RM-2026-0032-worksops-integration-recette`.

Mode: integration controlee depuis le worktree dedie WorksOps, puis recette
`/travaux`. Aucun code n'est modifie dans le repo principal par le
coordinateur tant que l'owner integration n'a pas livre un diff relu et un
panier de tests.

Statut de cette trace: doublon neutralise. La heartbeat a ouvert pendant ce
lancement le chantier canonique
`CH-20260525-092402-RM-2026-0032-worksops-integration-owner`. Cette trace
conserve seulement le lancement interrompu et le retour novice non canonique.

UI reelle cible: route tokenisee `/travaux`, ecran `Travaux suivis`, premier
viewport fiche chantier avec preuve attendue, prochaine action, demande de
piece et diffusion prudente.

References de comparaison:

- `docs/recherche_ux_ui_2026-05-24_travaux.md`;
- `docs/recherche_ux_ui_2026-05-24_travaux_operation-model.md`;
- `docs/recherche_ux_ui_2026-05-24_travaux_approfondissement.md`;
- `docs/cadrage_metier_worksops_2026-05-24.md`;
- `docs/equipe_agile_2026-05-25_worksops-recette-integration.md`.

## BOT-START

BOT-START - Coordinateur-scribe agile - 2026-05-25 09:19 +02:00

Roadmap: `RM-2026-0032`
Chantier: `CH-20260525-091900-RM-2026-0032-worksops-integration-recette`
Conversation: `CONV-2026-1725`
Role: coordinateur-scribe agile `ORD-P0-040`
Mission: ouvrir l'equipe d'integration WorksOps, maintenir l'owner unique,
recadrer la heartbeat 5 minutes et produire un point de reprise exploitable.
Ownership modifiable: ce document, `docs/presence_agents.md`,
`docs/roadmap_backlog_central.md`, heartbeat agile du fil courant.
Fichiers a eviter: code applicatif du repo principal, tests applicatifs du
repo principal, instances privees reelles, documents bruts, OCR/logs, exports
bruts, secrets, serveurs non reserves, push GitHub, `RM-2026-0017`,
`ORD-P0-990` et reouverture des lots `AGILE-DONE`.
Passerelle/registre de trace: ce document, `docs/presence_agents.md`,
journal append-only du gouvernail.
Dernier point lu: `AGENTS.md`,
`docs/consignes_bots_interconversations.md`,
`docs/protocole_roadmap_presence_agents.md`,
`docs/protocole_equipe_agile_agents.md`,
`docs/roadmap_backlog_central.md`, `docs/presence_agents.md`, et le lot
precedent WorksOps termine a 09:13.
Tests/preuves attendus: diff worktree relu, panier tests WorksOps/security/
smoke/no-private/line-limit, puis recette navigateur seulement sur port reserve.
Risque de collision: le worktree dedie touche `part_003.pyfrag`, `base.html`,
`styles.css`, `_dashboard.py` et `test_ui_demo.py`; un seul owner integration
peut ecrire dessus.
Lease ownership: 2026-05-25 11:19 +02:00.
Prochaine action: lancer owner integration, designer/novice et QA sans
dupliquer les roles clotures du lot precedent.

## Roles reserves

| Conversation | Role | Ownership | Statut initial |
|---|---|---|---|
| `CONV-2026-1725` | Coordinateur-scribe | Documents de coordination et heartbeat | `ABANDONNE` |
| `CONV-2026-1721` | Owner integration WorksOps | Worktree dedie `C:\Users\brice\CoproScope\dev\worktrees\coproscope-worksops-travaux-v1-20260525`: route, template, CSS, viewmodel dashboard et tests WorksOps | `ABANDONNE` |
| `CONV-2026-1722` | Designer service / facilitateur | Lecture seule: comparaison aux recherches UX WorksOps et blueprint du premier viewport | `ABANDONNE` |
| `CONV-2026-1723` | Utilisateur novice | Lecture seule: comprehension de `/travaux`, action attendue, preuve et diffusion | `CLOTURE` |
| `CONV-2026-1724` | QA privacy / regression | Lecture seule: panier tests, anti-fuite, line-limit, recette navigateur future | `ABANDONNE` |

## Agents lances

| Conversation | Agent | Id |
|---|---|---|
| `CONV-2026-1721` | Anscombe | `019e5e07-2b01-7462-afa4-0ccfb606c5e0` |
| `CONV-2026-1722` | Goodall | `019e5e07-2d94-73f3-97d4-5f53b8efcf2a` |
| `CONV-2026-1723` | Jason | `019e5e07-39e9-7c82-99d8-40171801d8ad` |
| `CONV-2026-1724` | Bacon | `019e5e07-3bb2-72b1-bae8-9cb696a3b39a` |

Ces agents ont ete fermes pour eviter un second owner code. Seul Jason a livre
une note novice non canonique: NO-GO live tant que `/travaux` n'est pas recette
en navigateur; GO cible conditionnel si le premier viewport montre chantier,
statut, preuve manquante, action humaine et diffusion prudente.

## Point de lancement

- A tester maintenant: worktree WorksOps dedie, route `/travaux`, tests
  `test_ui_worksops_travaux`, security, smoke, no-private et line-limit.
- En dev maintenant: uniquement `CONV-2026-1721`, dans le worktree dedie.
- En enquete maintenant: designer, novice et QA relisent les gates de recette
  sans modifier le code.
- Commande prete: integrer ou reviser le worktree `/travaux` en gardant un
  corpus fictif, une route tokenisee, aucun brut servi et un premier viewport
  comprehensible par un membre CS novice.
- Comparaison visuels enquete: references WorksOps du 2026-05-24, plus le
  verdict du lot `worksops-recette-integration`.
- Agents idle a relancer: aucun role cloture du lot precedent ne doit etre
  relance sans nouveau diff ou serveur live.
- Decision requise: aucune pour ouvrir l'owner integration; decision future
  seulement si conflit d'integration, test rouge non borne ou port live requis.
- Prochain mouvement: attendre le retour owner integration, puis lancer ou
  reprendre QA/novice sur le diff livre.
- Tests/preuves: a produire par l'owner integration et la QA.
