# Equipe agile - ContractOps obligations

Date: 2026-05-26.

## BOT-START - owner code ContractOps - 2026-05-26 00:26 +02:00

Roadmap: `RM-2026-0035` / `RM-2026-0030` / `RM-2026-0032` / `RM-2026-0006`.
Chantier: `CH-20260526-002600-RM-2026-0035-contractops-obligations`.
Conversation: `CONV-2026-1788`.
Role: owner code unique front/back/viewmodel `ORD-P1-080`.
Mission: livrer `/contrats` pour suivre contrats, obligations, attestations, echeances, preuves attendues et liens metier sans action automatique.
Ownership modifiable: route/viewmodel/template/CSS/tests ContractOps declares, presence, roadmap et cette trace.
Fichiers evites: instances privees, documents bruts, OCR/logs, exports bruts, secrets, contrat reel, attestation originale, rappel juridique automatique, mise en concurrence automatique, serveurs non reserves, scans/kills, push GitHub, `RM-2026-0017`, `ORD-P0-990`.
Dernier point lu: `CONV-2026-1787` integre a 00:24 +02:00; `CONV-2026-1772` reste bloque par recharge manuelle `8788`.
Tests/preuves attendus: test UI dedie, smoke/security/no-private, langue/accessibilite si pertinent, line-limit, diff-check.
Risque de collision: moyen sur `base.html`, `feature_routes.py` et `styles.css`; owner unique declare dans la ligne de presence.
Lease ownership: 2026-05-26 02:26 +02:00.
Prochaine action: lire les patterns routes recentes, ajouter la route et ses tests sans serveur live.

## BOT-END - owner code ContractOps - 2026-05-26 00:34 +02:00

Roadmap: `RM-2026-0035` / `RM-2026-0030` / `RM-2026-0032` / `RM-2026-0006`.
Chantier: `CH-20260526-002600-RM-2026-0035-contractops-obligations`.
Conversation: `CONV-2026-1788`.
Statut: `INTEGRE`.
Scenario utilisateur vise: ouvrir `/contrats`, voir contrats/obligations/attestations/echeances, comprendre la preuve attendue et rejoindre pieces, charges, travaux ou incidents sans action automatique.
Fichiers modifies: `server/src/coproscope/web/contractops_view.py`, `server/src/coproscope/web/templates/contracts.html`, `server/src/coproscope/web/static/styles_part_23.css`, `server/src/coproscope/web/static/styles.css`, `server/src/coproscope/web/feature_routes.py`, `server/src/coproscope/web/templates/base.html`, tests UI/smoke/security/no-private, presence et roadmap.
Fichiers volontairement evites: instances privees, documents bruts, OCR/logs, exports bruts, secrets, contrat reel, attestation originale, serveurs, scans/kills, push GitHub, `RM-2026-0017`, `ORD-P0-990`.
Tests/preuves: ContractOps 5 OK; smoke/security/no-private 17 OK; langue/accessibilite 15 OK; line-limit OK; diff-check OK avec warning CRLF `styles.css`.
Verdict novice/QA: GO integre local, libelles lisibles, actions sensibles bloquees, liens tokenises vers pieces/charges/travaux/incidents, aucune fuite `raw`, `restricted`, `logs`, `private`, chemin local, secret ou original.
Limites: pas de recette navigateur live/capture car aucun serveur reserve; la vue lit seulement les syntheses documentaires derivees disponibles ou des exemples FICTIFS.
Questions ouvertes: raccorder plus tard un registre contrats dedie si le produit stabilise les champs source, clause, echeance et renouvellement.
Prochain mouvement propose: continuer la chaine autonome vers le prochain `ORD-*` actionnable hors lots P1 integres, blocage manuel `8788`, secrets et reconstruction Beauvallon.
