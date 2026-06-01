# Equipe reconstruction - alerte facture DOC-0142

BOT-START - Coordinateur-scribe correction P0 - 2026-06-01 15:44 +02:00

Roadmap: `RM-2026-0017`
Ordre: `ORD-P0-990`
Chantier: `CH-20260601-154400-RM-2026-0017-doc142-alerte-facture`
Conversation: `CONV-2026-1976` / conversation utilisateur No2
Role: coordinateur-scribe, avec QA privacy locale et retour novice simule depuis le protocole.
Mission: traiter le point produit remonte par `DOC-0142`: rendre plus visible dans la file factures le cas ou la lecture locale est insuffisante et ou le montant manque.
Equipe-type: `AGILE_UI_PRODUIT` micro-iteration, sans visuel IA ni blueprint car la structure de table existante ne change pas.
Ownership modifiable: `server/src/coproscope/web/factures_review_view.py`, `server/src/coproscope/web/templates/factures_review.html`, `server/tests/test_ui_factures_review.py`, ce document, `docs/presence_agents.md`, `docs/roadmap_backlog_central.md`.
Fichiers a eviter: documents bruts, OCR/logs, journal prive hors synthese anonymisee, FactureOps extracteurs, Drive, serveurs durables, scan/kill, push GitHub.
Dernier point lu: protocole `DOC-0142` gate bloque par OCR/controle humain; `CONV-2026-1975` a ensuite reserve le correctif OCR/energie, donc No2 borne ce lot a l'alerte UI.
Lease ownership: 2026-06-01 17:44 +02:00.

ROUTAGE_EQUIPE
Preflight: OK pour une correction UI bornee.
Equipe-type: `AGILE_UI_PRODUIT`
Roadmap / ORD: `RM-2026-0017` / `ORD-P0-990`
Chantier: `CH-20260601-154400-RM-2026-0017-doc142-alerte-facture`
Coordinateur: `CONV-2026-1976`
Owner code unique: No2 sur la file factures uniquement.
Roles joues: designer/novice/QA privacy sequentiels.
Roles explicitement non lances: Drive, OCR, ingestion brute, publication.
Condition d'arret: libelle visible, test anti-fuite OK, `DOC-0142` reste bloque sans fausse cloture.

EXECUTION
- La file `/comptes/factures-a-revoir` affiche maintenant `Lecture locale insuffisante` quand une facture a un montant TTC absent et un statut machine a reprendre.
- L'action suivante dit explicitement de retrouver le montant ou relancer OCR avant conclusion.
- La correction ne change pas les extracteurs ni les donnees de l'instance.
- `DOC-0142` n'est pas clos par No2: le protocole exige encore OCR exploitable ou controle humain avant de passer au document suivant.

PREUVES
- Tests cibles `server.tests.test_ui_factures_review`: 5 OK.
- `git diff --check`: OK.
- TestClient sur l'instance reconstruction: `/comptes/factures-a-revoir` en 200, libelle `Lecture locale insuffisante` present, aucun marqueur prive detecte.
- Avant correction, le protocole `DOC-0142` signalait explicitement le besoin d'alerte plus visible.

LIMITES
- Pas de rebuild executable dans ce passage; verification faite par TestClient sur le code courant.
- Les donnees `DOC-0142` restent a reprendre hors Git par OCR exploitable ou controle humain protege.

BOT-END - Coordinateur-scribe correction P0 - 2026-06-01 15:46 +02:00
Roadmap: `RM-2026-0017`
Chantier: `CH-20260601-154400-RM-2026-0017-doc142-alerte-facture`
Conversation: `CONV-2026-1976`
Statut: `INTEGRE`
Fichiers modifies: `factures_review_view.py`, `factures_review.html`, `test_ui_factures_review.py`, ce document, `docs/presence_agents.md`, `docs/roadmap_backlog_central.md`.
Fichiers volontairement evites: documents bruts, OCR/logs, Drive, extracteurs, serveurs durables, scan/kill, push GitHub.
Tests/preuves: tests factures 5 OK, diff-check OK, TestClient reconstruction 200 avec alerte visible et sans fuite.
Limites: `DOC-0142` reste bloque sur OCR/controle humain; ce lot livre seulement l'alerte UI issue du blocage.
Prochain mouvement propose: laisser `CONV-2026-1975` traiter OCR/energie, puis reprendre le protocole seulement apres gate clarifie.
