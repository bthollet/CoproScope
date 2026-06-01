# Equipe agile - conversation No2 - lecture TTC ENGIE prelevement

BOT-START - Coordinateur correction P0 factures energie - 2026-06-01 16:40 +02:00

Roadmap: `RM-2026-0017`
Ordre: `ORD-P0-990`
Chantier: `CH-20260601-164000-RM-2026-0017-engie-prelevement-ttc`
Conversation: `CONV-2026-1982`
Mission: finir le petit correctif P0 deja present dans le worktree pour lire le montant TTC d'une facture ENGIE scannee quand le total apparait pres de la mention de prelevement.
Equipe-type: mini iteration agile backend domaine avec lecture expert, QA et coordinateur-dev.
Ownership modifiable: `server/src/coproscope/extractors/invoices/providers/engie.py`, `server/tests/test_factureops_provider_routing.py`, ce document, `docs/presence_agents.md`, `docs/roadmap_backlog_central.md`.
Fichiers a eviter: documents bruts, OCR/logs, exports bruts, secrets, Drive, instances privees hors protocole, serveurs durables, autres extracteurs non lies.
Dernier point lu: protocole reconstruction `WAIT_MERGE` parce que ce correctif energie est non integre; test cible rouge car le TTC lu retombe sur le HT.
Lease ownership: 2026-06-01 18:40 +02:00.

ROUTAGE_EQUIPE
- Expert extraction facture: verifier si le test ou l'extracteur porte la bonne regle metier.
- QA: definir le panier minimal de non-regression facture avant commit.
- Coordinateur-dev No2: patch minimal, tests, trace et commit.

EXECUTION
- Avis expert lecture seule: corriger l'extracteur, pas le test; le cas est credible quand l'OCR coupe la ligne `MONTANT TTC a payer`.
- Avis QA lecture seule: surveiller la priorite du motif prelevement et eviter que la regle generale TTC capture un montant `hors TVA` a la ligne suivante.
- Correctif applique: le motif `montant TTC preleve` passe avant la regle generale, et la regle generale `MONTANT TTC a payer` reste sur la meme ligne.
- Test ajoute avec donnees synthetiques: facture ENGIE scannee avec total preleve, HT, TVA calculee et compte energie.

PREUVES
- `server.tests.test_factureops_provider_routing`: 12 OK.
- Panier factures/extracteurs/UI factures: 33 OK.
- `test_reconstruction_protocol_tool`: 8 OK.
- `tools/check_code_line_limit.py`: OK, aucun fichier code suivi au-dessus de 600 lignes.
- `git diff --check`: OK sur les fichiers du lot.

BOT-END - Coordinateur correction P0 factures energie - 2026-06-01 16:44 +02:00
Roadmap: `RM-2026-0017`
Chantier: `CH-20260601-164000-RM-2026-0017-engie-prelevement-ttc`
Conversation: `CONV-2026-1982`
Statut: `INTEGRE`
Fichiers modifies: `server/src/coproscope/extractors/invoices/providers/engie.py`, `server/tests/test_factureops_provider_routing.py`, ce document, `docs/presence_agents.md`, `docs/roadmap_backlog_central.md`.
Fichiers volontairement evites: documents bruts, OCR/logs, exports bruts, secrets, Drive, instances privees hors protocole, serveurs durables, autres extracteurs non lies.
Limites: pas de rebuild executable pour ce mini-lot backend; le prochain paquet desktop reprendra le correctif depuis le code.
