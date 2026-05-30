# Equipe agile - Activite en cours

Date: 2026-05-26.

## BOT-START - owner code activite arriere-plan - 2026-05-26 00:36 +02:00

Roadmap: `RM-2026-0012` / `RM-2026-0005` / `RM-2026-0006`.
Chantier: `CH-20260526-003600-RM-2026-0012-activite-arriere-plan`.
Conversation: `CONV-2026-1789`.
Role: owner code unique front/back/viewmodel `ORD-P2-020`.
Mission: livrer `/pilotage/activite` pour montrer les travaux actifs, derniers passages, prochains gestes, blocages et traces lisibles sans exposer logs, prompts, chemins ou secrets.
Ownership modifiable: route/viewmodel/template/CSS/tests activite declares, presence, roadmap et cette trace.
Fichiers evites: instances privees, logs bruts, prompts complets, automations privees, secrets, tokens, chemins locaux, documents bruts, exports bruts, serveurs non reserves, scans/kills, push GitHub, `RM-2026-0017`, `ORD-P0-990`.
Dernier point lu: `CONV-2026-1788` ContractOps integre a 00:34 +02:00; `CONV-2026-1772` reste bloque par recharge manuelle `8788`.
Tests/preuves attendus: test UI dedie, smoke/security/no-private, langue/accessibilite si pertinent, line-limit, diff-check.
Risque de collision: moyen sur `base.html`, `feature_routes.py` et `styles.css`; owner unique declare dans la ligne de presence.
Lease ownership: 2026-05-26 02:36 +02:00.
Prochaine action: implementer une projection derivee de `docs/presence_agents.md` et du gouvernail, sans lire les logs ni les automations app.

## BOT-END - owner code activite arriere-plan - 2026-05-26 00:41 +02:00

Roadmap: `RM-2026-0012` / `RM-2026-0005` / `RM-2026-0006`.
Chantier: `CH-20260526-003600-RM-2026-0012-activite-arriere-plan`.
Conversation: `CONV-2026-1789`.
Statut: `INTEGRE`.
Scenario utilisateur vise: ouvrir `/pilotage/activite`, voir ce qui travaille encore, ce qui bloque, le dernier passage, la prochaine relance et les traces lisibles sans ouvrir un terminal.
Fichiers modifies: `server/src/coproscope/web/activity_view.py`, `server/src/coproscope/web/templates/activity.html`, `server/src/coproscope/web/static/styles_part_24.css`, `server/src/coproscope/web/static/styles.css`, `server/src/coproscope/web/feature_routes.py`, `server/src/coproscope/web/templates/base.html`, tests UI/smoke/security/no-private, presence et roadmap.
Fichiers volontairement evites: instances privees, journaux bruts, consignes longues, automations privees, secrets, tokens, chemins locaux, documents bruts, exports bruts, serveurs, scans/kills, push GitHub, `RM-2026-0017`, `ORD-P0-990`.
Tests/preuves: Activite en cours 4 OK; smoke/security/no-private 17 OK; langue/accessibilite 15 OK; line-limit OK; diff-check OK avec warning CRLF `styles.css`.
Verdict novice/QA: GO integre local, statuts fermes en langage lisible, blocages et prochaines relances visibles, actions techniques bloquees, liens tokenises, cas de presence injectee avec chemin/valeur sensible/consigne longue biffe.
Limites: pas de recette navigateur live/capture car aucun serveur reserve; la vue lit seulement `docs/presence_agents.md` et `docs/roadmap_backlog_central.md`.
Questions ouvertes: ajouter plus tard une vraie page de trace consultable si un registre public dedie remplace la lecture directe des docs.
Prochain mouvement propose: continuer vers le prochain P2 actionnable, probablement `ORD-P2-040` roles/commissions ou `ORD-P2-050` suggestions utiles, sans rouvrir les lots integres.
