# Equipe agile - Suggestions utiles

Date: 2026-05-26.

## BOT-START - owner code suggestions utiles - 2026-05-26 00:43 +02:00

Roadmap: `RM-2026-0003` / `RM-2026-0036` / `RM-2026-0006`.
Chantier: `CH-20260526-004300-RM-2026-0003-suggestions-utiles`.
Conversation: `CONV-2026-1790`.
Role: owner code unique front/back/viewmodel `ORD-P2-050`.
Mission: livrer `/suggestions` pour afficher seulement des suggestions sourcees, avec preuve, revue humaine, destination possible et aucune creation automatique.
Ownership modifiable: route/viewmodel/template/CSS/tests suggestions declares, presence, roadmap et cette trace.
Fichiers evites: instances privees, documents bruts, OCR/logs, exports bruts, secrets, chemins locaux, transformations automatiques, envois automatiques, serveurs non reserves, scans/kills, push GitHub, `RM-2026-0017`, `ORD-P0-990`.
Dernier point lu: `CONV-2026-1789` Activite en cours integre a 00:41 +02:00; `CONV-2026-1772` reste bloque par recharge manuelle `8788`.
Tests/preuves attendus: test UI dedie, `suggestionops`/`suggestionview`, smoke/security/no-private, langue/accessibilite si pertinent, line-limit, diff-check.
Risque de collision: moyen sur `base.html`, `feature_routes.py` et `styles.css`; owner unique declare dans la ligne de presence.
Lease ownership: 2026-05-26 02:43 +02:00.
Prochaine action: brancher `suggestionops`/`suggestionview` dans une route prudente, exemples FICTIFS si aucun registre derive n'existe.

## BOT-END - owner code suggestions utiles - 2026-05-26 00:46 +02:00

Roadmap: `RM-2026-0003` / `RM-2026-0036` / `RM-2026-0006`.
Chantier: `CH-20260526-004300-RM-2026-0003-suggestions-utiles`.
Conversation: `CONV-2026-1790`.
Statut: `INTEGRE`.
Scenario utilisateur vise: ouvrir `/suggestions`, voir une suggestion sourcee, sa preuve, sa revue humaine et la suite possible sans creation automatique.
Fichiers modifies: `server/src/coproscope/web/suggestions_view.py`, `server/src/coproscope/web/templates/suggestions.html`, `server/src/coproscope/web/static/styles_part_25.css`, `server/src/coproscope/web/static/styles.css`, `server/src/coproscope/web/feature_routes.py`, `server/src/coproscope/web/templates/base.html`, tests UI/smoke/security/no-private, presence et roadmap.
Fichiers volontairement evites: instances privees, documents bruts, OCR/logs, exports bruts, secrets, chemins locaux, transformations automatiques, envois automatiques, serveurs, scans/kills, push GitHub, `RM-2026-0017`, `ORD-P0-990`.
Tests/preuves: Suggestions UI + `suggestionops` + `suggestionview` 18 OK; smoke/security/no-private 17 OK; langue/accessibilite 15 OK; line-limit OK; diff-check OK avec warning CRLF `styles.css`.
Verdict novice/QA: GO integre local, cartes affichees seulement avec source/preuve/revue acceptee, suggestions sans revue ou preuve gardees en file de revue, actions automatiques bloquees, liens tokenises, cas derive avec chemin local biffe.
Limites: pas de recette navigateur live/capture car aucun serveur reserve; les transformations restent des intentions de suite, pas des creations persistantes.
Questions ouvertes: brancher plus tard une ecriture explicite vers action/demande/point/indicateur apres design de validation humaine.
Prochain mouvement propose: continuer le P2 restant sur roles/commissions (`ORD-P2-040`) ou gouvernance complexe (`ORD-P2-060`) si aucun owner vivant plus recent n'est declare.
