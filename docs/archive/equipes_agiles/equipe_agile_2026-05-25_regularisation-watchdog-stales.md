# Equipe agile - Regularisation watchdog stales

Date de lancement: 2026-05-25 15:02 +02:00.
Roadmap: `RM-2026-0005`.
Chantier: `CH-20260525-150239-RM-2026-0005-regularisation-watchdog-stales`.
Conversation coordination: `CONV-2026-1751`.
Mode: equipe agile gouvernail courte, hygiene orchestration.
Statut: cloture.

## BOT-START

BOT-START - Coordinateur-scribe agile - 2026-05-25 15:02 +02:00

Mission: traiter le rouge watchdog sans masquer les blocages produit. La vague
regularise uniquement les conversations `EN_COURS` dont le lease est expire
(`CONV-2026-1525` et `CONV-2026-0120`), confirme le stationnement de
`CONV-2026-1708` et verifie qu'aucun `ORD-*` P0 produit ne peut etre relance
sans serveur, token, decision Brice ou nouveau diff.

Ownership modifiable: ce document, `docs/presence_agents.md` et
`docs/roadmap_backlog_central.md`.

Fichiers a eviter: code applicatif, tests applicatifs, routes, templates, CSS,
instances privees, documents bruts, OCR/logs, exports bruts, secrets, serveurs
locaux, push GitHub, `RM-2026-0017` et `ORD-P0-990`.

## Roles

| Role | Conversation | Statut | Ownership |
|---|---|---|---|
| Coordinateur-scribe | `CONV-2026-1751` | `CLOTURE` | Registres, decision de stationnement et synthese. |
| Auditeur presence leases | `CONV-2026-1752` | `CLOTURE` | Agent Poincare `019e5f3d-5ff0-76a3-a9ec-fa99c908cb61`; lecture seule. |
| Gardien roadmap P0 | `CONV-2026-1753` | `CLOTURE` | Agent Kepler `019e5f3d-6182-7051-86ea-c5260d6282bb`; lecture seule. |
| QA watchdog / privacy | `CONV-2026-1754` | `CLOTURE` | QA local par coordinateur faute de capacite thread. |

## Point Court Initial

A tester maintenant: superviseur et watchdog uniquement.

En dev maintenant: aucun owner code, aucun patch produit.

En enquete maintenant: `CONV-2026-1525`, `CONV-2026-0120`, `CONV-2026-1708` et
les `ORD-*` P0 restants.

Commande prete: regularisation administrative des leases expires; aucune
commande feature.

Agents idle: trois roles lecture seule reserves.

Decision requise: Brice devra fournir serveur/token pour `ORD-P0-036` ou une
decision explicite d'integration/dev pour rouvrir un lot `PRET_A_INTEGRER` ou
`AGILE-DONE`.

Prochain mouvement: marquer les deux conversations stale en `EXPIRE`, puis
verifier que le watchdog ne remonte plus que le blocage volontaire
`CONV-2026-1708` et les lots `PRET_A_INTEGRER`.

Tests/preuves: `orchestration-supervise --emit-recovery-prompt`,
`orchestration-watch --emit-prompt`, `git diff --check` sur les registres.

## Journal

| Heure | Conversation | Evenement | Note |
|---|---|---|---|
| 2026-05-25 15:02 +02:00 | `CONV-2026-1751` | `BOT-START` | Vague agile courte ouverte pour regulariser les stales watchdog; aucun code, serveur, instance privee, secret, export brut, push GitHub, `RM-2026-0017` ou `ORD-P0-990`. |
| 2026-05-25 15:03 +02:00 | `CONV-2026-1752`, `CONV-2026-1753` | `AGENTS_LAUNCHED` | Agents Poincare et Kepler lances en lecture seule; le role QA watchdog `CONV-2026-1754` sera traite localement faute de capacite thread. |
| 2026-05-25 15:08 +02:00 | `CONV-2026-1752` | `LEASES_GO` | Poincare valide l'expiration administrative de `CONV-2026-1525` et `CONV-2026-0120`; il signale aussi `CONV-2026-0201`, regularise dans le registre. |
| 2026-05-25 15:08 +02:00 | `CONV-2026-1753` | `P0_NO_GO_FEATURE_TEAM` | Kepler confirme le no-go feature team produit: `ORD-P0-036` bloque, `ORD-P0-050` AGILE-DONE/no-go dev sans validation, `ORD-P0-900` bloque secret, `ORD-P0-990` interdit. |
| 2026-05-25 15:08 +02:00 | `CONV-2026-1751`..`CONV-2026-1754` | `AGILE_DONE` | Equipe cloturee sans dev: trois conversations expirees regularisees, aucun serveur ou instance touche, prochain mouvement = stationner jusqu'a serveur/token/decision/diff. |

## BOT-END

BOT-END - Coordinateur-scribe agile - 2026-05-25 15:08 +02:00

Roadmap: `RM-2026-0005`.
Chantier: `CH-20260525-150239-RM-2026-0005-regularisation-watchdog-stales`.
Conversation: `CONV-2026-1751`.
Statut: CLOTURE.
Livrable: regularisation watchdog des conversations expirees
`CONV-2026-1525`, `CONV-2026-0120` et `CONV-2026-0201`; confirmation qu'aucun
P0 produit n'est actionnable sans dependance nouvelle ou decision Brice.
Fichiers modifies: `docs/equipe_agile_2026-05-25_regularisation-watchdog-stales.md`,
`docs/presence_agents.md`, `docs/roadmap_backlog_central.md`.
Fichiers evites: code applicatif, tests applicatifs, serveurs, instances
privees, documents bruts, OCR/logs, exports bruts, secrets, push GitHub,
`RM-2026-0017` et `ORD-P0-990`.
Preuves: retours Poincare et Kepler, QA local watchdog/superviseur, diff-check
cible.
