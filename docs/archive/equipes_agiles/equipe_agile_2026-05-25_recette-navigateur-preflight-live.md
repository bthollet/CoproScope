# Equipe agile - recette navigateur preflight live

Date: 2026-05-25 15:15 +02:00.
Rattachement: `RM-2026-0006` / `ORD-P0-036`.
Chantier: `CH-20260525-151516-RM-2026-0006-recette-navigateur-preflight-live`.
Cadence demandee: vitesse standard.

## BOT-START - coordinateur-scribe - 2026-05-25 15:15 +02:00

Roadmap: `RM-2026-0006` avec rappel `RM-2026-0003`.
Conversation: `CONV-2026-1756`.
Role: coordinateur-scribe agile.
Mission: relancer une equipe courte sur le blocage `ORD-P0-036` pour verifier si la recette navigateur peut reprendre maintenant, ou confirmer le stationnement `BLOQUE` si le serveur visible reserve manque encore.
Ownership modifiable: ce document, `docs/presence_agents.md`, `docs/roadmap_backlog_central.md`, heartbeat `relance-equipe-agile-gouvernail-autonome`.
Fichiers a eviter: code applicatif, tests applicatifs, routes, templates, CSS, instances privees reelles, documents bruts, OCR/logs, exports bruts, secrets, push GitHub, `RM-2026-0017`, `ORD-P0-990`.
Serveur: aucun serveur lance par ce BOT-START. Un serveur live ne pourra etre utilise que s'il est explicitement reserve avec port, instance de test, token, commande et terminal PowerShell visible.
Dernier point lu: `AGENTS.md`, `docs/protocole_equipe_agile_agents.md`, `docs/orchestration_watchdog.md`, `docs/presence_agents.md`, `docs/roadmap_backlog_central.md`, watchdog 2026-05-25 15:13 +02:00.
Tests/preuves attendus: superviseur/watchdog, decision GO/NO-GO live, et si serveur fourni ensuite seulement: token 200/403, captures desktop/tablette/mobile, absence de chevauchement et anti-fuite.
Risque de collision: repo principal sale; aucun patch code dans ce chantier.
Lease ownership: 2026-05-25 17:15 +02:00.
Prochaine action: lancer designer, novice et QA preflight en lecture seule, puis consolider le GO/NO-GO.

## Point de coordination initial

- A tester maintenant: etat `ORD-P0-036`, dependance serveur visible reserve, conditions token/captures.
- En dev maintenant: aucun owner code.
- En enquete maintenant: designer, novice et QA preflight lecture seule.
- Commande prete: reprise live seulement si port, instance de test, token, commande et terminal PowerShell visible sont nommes.
- Comparaison visuels enquete: utiliser les captures live 8766 et les routes P0 livrees comme reference; ne pas valider une intention abstraite.
- Agents idle a relancer: aucun role vivant a dupliquer.
- Decision requise: serveur live reserve disponible ou maintien `BLOQUE`.
- Prochain mouvement: consolider les retours des trois roles et recadrer la heartbeat canonique.
- Tests/preuves: `tools\orchestration-supervise.cmd --emit-recovery-prompt`, `tools\orchestration-watch.cmd --emit-prompt`; pas de serveur ni capture tant que la dependance live manque.

## Retours supplementaires

### Designer - Ptolemy / `CONV-2026-1763`

Verdict: GO designer sans nouvelle maquette si le serveur visible reserve est confirme; sinon NO-GO execution et maintien `BLOQUE`.

UI cible: parcours tokenise `/` -> `/comptes` ou audit disponible -> `/actions` -> `/pieces?proof=missing` ou fiche piece -> `/demandes` / relance / depot -> `/confidentialite` ou revue diffusion -> `/exports/passation`.

References: `docs/assets/etude-utilisateurs/` (`cockpit-conseil-syndical.png`, `registre-decisions-actions-preuves.png`, `controle-comptes-guide.png`, `memoire-copropriete.png`) et captures reelles `docs/assets/ux-livraison-reelle-2026-05-21-8766-final/`.

### Novice - Pasteur / `CONV-2026-1764`

Verdict: NO-GO novice tant que le serveur live reserve n'est pas confirme.

Le parcours doit montrer en mots simples: `Sujet a traiter`, `Pourquoi c'est important`, `Preuve attendue`, `Demander une piece`, `Reponse recue`, `A verifier avant partage`, `Qui peut voir`.

### QA - Arendt / `CONV-2026-1765`

Verdict: GO execution conditionnel. Le registre canonique indique un serveur reserve `127.0.0.1:8788`, instance `beauvallon_test`, token `parcours-live-local`, commande `ui open-test`.

Panier: `/health` 200, URL tokenisee 200, sans token 403, mauvais token 403, captures desktop/tablette/mobile, parcours cockpit -> audit/comptes -> action -> piece/demande -> preuve -> diffusion, anti-fuite.

## BOT-END - preflight supplementaire - 2026-05-25 15:20 +02:00

Statut: `CLOTURE`.
Raison: doublon neutralise apres detection du chantier canonique `CH-20260525-151456-RM-2026-0006-recette-parcours-live`, deja ouvert avec serveur visible reserve `8788` et equipe standard complete.
Fichiers modifies: `docs/equipe_agile_2026-05-25_recette-navigateur-preflight-live.md`, `docs/presence_agents.md`, `docs/roadmap_backlog_central.md`.
Fichiers evites: code applicatif, tests applicatifs, routes, templates, CSS, instances privees reelles, documents bruts, OCR/logs, exports bruts, secrets, push GitHub, `RM-2026-0017`, `ORD-P0-990`.
Tests/preuves: retours Ptolemy/Pasteur/Arendt; superviseur et watchdog executes.
Limites: aucune capture navigateur produite par ce preflight supplementaire.
Prochain mouvement: laisser l'equipe canonique `recette-parcours-live` poursuivre la recette sur `8788`; ne pas dupliquer ses roles.
