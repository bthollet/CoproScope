# Equipe agile - conversation No2 - reconstruction DOC-0165

BOT-START - Coordinateur-scribe reconstruction P0 - 2026-06-01 17:39 +02:00

Roadmap: `RM-2026-0017`
Ordre: `ORD-P0-990`
Chantier: `CH-20260601-173900-RM-2026-0017-doc165-protocole`
Conversation: `CONV-2026-1993`
Mission: traiter le document courant `DOC-0165` du protocole reconstruction sans chevaucher les autres conversations.
Equipe-type: petite iteration agile avec expert confidentialite, novice/designer, observation CoproScope et QA.
Ownership modifiable: ce document, `docs/presence_agents.md`, `docs/roadmap_backlog_central.md`, `server/src/coproscope/extractors/invoices/base.py`, `server/src/coproscope/modules/factureops.py`, `server/tests/test_factureops_provider_routing.py`, journal prive du protocole reconstruction via `tools/reconstruction-protocol.cmd`.
Fichiers a eviter: instances privees hors journal protocole, documents bruts, OCR/logs, exports bruts, secrets, Drive, serveurs durables, scan/kill, push GitHub hors integration.
Dernier point lu: protocole `READY`, document courant `DOC-0165`, dernier document clos `DOC-0164`; aucune trace publique `DOC-0165` trouvee au preflight.
Lease ownership: 2026-06-01 19:39 +02:00.

ROUTAGE_EQUIPE
- Expert metier/confidentialite: confirmer que la cloture ne publie aucun contenu brut et que les controles obligatoires sont presents.
- Novice/designer: garder une formulation simple, sans promettre de validation metier definitive.
- CoproScope: controler les routes UI protegees utiles au protocole.
- QA: verifier absence de marqueurs cibles de fuite et test executable avec empreinte SHA-256.

Contraintes de wording public: ne pas ecrire que le document est valide, complet, publiable ou sans risque. Dire seulement que les controles du protocole sont realises, si le gate passe.

SOUS-AGENTS LECTURE SEULE
- QA confidentialite: rester procedural, sans extrait, resume, montant, nom, adresse, lot, date sensible, chemin local, OCR/log, Drive, secret, token ou indice permettant d'identifier le document.
- Novice/designer: dire `traite dans le protocole prive`, `controles termines`, `test de l'executable CoproScope OK` et rappeler `aucune validation metier definitive`.

EXECUTION
- `DOC-0165` a ete traite dans le protocole prive uniquement.
- Les roles de controle sont notes: expert/confidentialite, designer, novice, CoproScope et QA.
- L'observation CoproScope a ete notee sur les routes protegees utiles au protocole.
- Le tri designer a signale un point machine a traiter avant suite: l'extraction generique confondait taux/montant de TVA, fournisseur et famille comptable.
- Correctif applique avant cloture: meilleure lecture de la TVA apres taux, rejet de faux fournisseurs techniques, date textuelle francaise reconnue, et classement des petits travaux electriques en entretien/maintenance.
- Le tri garde deux suites backlog UI: alerte facture visible sur la fiche document et masquage des noms techniques bruts.
- Aucun document brut, OCR/log, chemin local, Drive, secret ou serveur durable n'a ete publie.

PREUVES
- Synthese anonymisee du protocole: `DOC-0165`, controles termines, roles notes, document clos.
- Tests `server.tests.test_factureops_provider_routing` et `server.tests.test_docai`: 18 OK.
- Garde-fou taille code OK et `git diff --check` OK.
- Extraction privee regeneree: anomalie arithmetique levee et controle humain final conserve.
- Smokes executable derniere version OK sur fiche protegee et route de revue factures.
- Empreinte technique de l'executable: `CoproScope.exe` SHA-256 `68A720650BBF0951369F34FD45B5276F4ED952A1301C8B78E0F479E31E8946EB`.

BOT-END - Coordinateur-scribe reconstruction P0 - 2026-06-01 17:41 +02:00
Roadmap: `RM-2026-0017`
Chantier: `CH-20260601-173900-RM-2026-0017-doc165-protocole`
Conversation: `CONV-2026-1993`
Statut: `INTEGRE`
Fichiers modifies: ce document, `docs/presence_agents.md`, `docs/roadmap_backlog_central.md`, `server/src/coproscope/extractors/invoices/base.py`, `server/src/coproscope/modules/factureops.py`, `server/tests/test_factureops_provider_routing.py`, journal prive du protocole reconstruction.
Fichiers volontairement evites: documents bruts, OCR/logs, exports bruts, secrets, Drive, serveurs durables, chemins ou noms de fichiers sources.
Limites: cette trace indique seulement que `DOC-0165` a ete traite dans le protocole prive; elle ne vaut pas validation metier definitive et ne publie aucun contenu documentaire.
