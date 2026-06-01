# Equipe agile - conversation No2 - reconstruction DOC-0149

BOT-START - Coordinateur-scribe reconstruction P0 - 2026-06-01 16:22 +02:00

Roadmap: `RM-2026-0017`
Ordre: `ORD-P0-990`
Chantier: `CH-20260601-162200-RM-2026-0017-doc149-protocole`
Conversation: `CONV-2026-1980`
Mission: traiter le document courant `DOC-0149` du protocole reconstruction sans chevaucher les autres conversations.
Equipe-type: petite iteration agile avec expert confidentialite, novice/designer, observation CoproScope et QA.
Ownership modifiable: ce document, `docs/presence_agents.md`, `docs/roadmap_backlog_central.md`, journal prive du protocole reconstruction via `tools/reconstruction-protocol.cmd`.
Fichiers a eviter: code applicatif, extracteurs, fichiers OCR/energie, instances privees hors journal protocole, documents bruts, OCR/logs, exports bruts, secrets, Drive, serveurs durables, scan/kill, push GitHub.
Dernier point lu: protocole `READY`, document courant `DOC-0149`, dernier document clos `DOC-0148`; aucune trace publique `DOC-0149` trouvee au preflight.
Lease ownership: 2026-06-01 18:22 +02:00.

ROUTAGE_EQUIPE
- Expert metier/confidentialite: verifier que la cloture ne publie aucun contenu brut et que les controles obligatoires sont presents.
- Novice/designer: verifier que la trace publique reste claire pour Brice et n'emploie pas de mots qui font croire a une validation comptable definitive.
- CoproScope: controler les routes UI protegees utiles au protocole.
- QA: verifier absence de marqueurs cibles de fuite et test executable avec SHA-256.

Contraintes de wording public: ne pas ecrire que le document est valide, complet, publiable ou sans risque. Dire seulement que les controles du protocole sont realises, si le gate passe.

EXECUTION
- Le premier controle TestClient a trouve le marqueur technique `inbox-reconstruction:` sur l'ecran inbox.
- Correctif UI applique: la reference locale inbox est remplacee par `Reference locale masquee`, sans changer le `doc_id` utile au rattachement.
- Tests cibles `test_ui_document_intake_route`: 8 OK.
- TestClient prive apres correctif: inbox, file factures et fiche protegee en 200, sans marqueurs cibles de fuite.
- Build desktop reconstruit pour inclure le correctif UI.
- Smoke executable HTTP sur l'inbox OK, SHA-256 `F9BF56C31DD049DAED95D057F5466A8ED3EF0077DDE55958D3C1BA9C391729C3`.
- Roles protocole notes: expert, designer, novice, CoproScope et QA.
- Gate protocole: `OK`; `DOC-0149` clos.

LIMITES
- La ligne roadmap `ABANDON_CONV2_RECONSTRUCTION_DOC149_STALE` etait un point intermediaire de course; elle est remplacee par la presente cloture, apres verification protocole.
- Aucun contenu brut, OCR, chemin local de source, fournisseur, extrait ou contenu documentaire n'est repris dans Git.
- Aucun serveur durable n'a ete laisse ouvert; le smoke executable gere son propre processus.

BOT-END - Coordinateur-scribe reconstruction P0 - 2026-06-01 16:35 +02:00
Roadmap: `RM-2026-0017`
Chantier: `CH-20260601-162200-RM-2026-0017-doc149-protocole`
Conversation: `CONV-2026-1980`
Statut: `INTEGRE`
Fichiers modifies: ce document, `docs/presence_agents.md`, `docs/roadmap_backlog_central.md`, `server/src/coproscope/web/document_intake_route.py`, `server/tests/test_ui_document_intake_route.py`, journal prive protocole reconstruction hors Git.
Fichiers volontairement evites: documents bruts, OCR/logs, exports bruts, secrets, Drive, serveurs durables, scan/kill, push GitHub.
Tests/preuves: test UI intake route 8 OK, TestClient prive 3 routes OK sans marqueurs cibles, smoke executable HTTP OK, gate protocole OK, `DOC-0149` clos.
Prochain mouvement propose: ouvrir le prochain document uniquement si le protocole reste `READY` et si aucune autre conversation ne l'a pris.
