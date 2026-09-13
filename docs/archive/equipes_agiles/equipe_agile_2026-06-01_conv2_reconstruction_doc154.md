# Equipe agile - conversation No2 - reconstruction DOC-0154

BOT-START - Coordinateur-scribe reconstruction P0 - 2026-06-01 16:45 +02:00

Roadmap: `RM-2026-0017`
Ordre: `ORD-P0-990`
Chantier: `CH-20260601-164500-RM-2026-0017-doc154-protocole`
Conversation: `CONV-2026-1983`
Mission: traiter le document courant `DOC-0154` du protocole reconstruction sans chevaucher les autres conversations.
Equipe-type: petite iteration agile avec expert confidentialite, novice/designer, observation CoproScope et QA.
Ownership modifiable: ce document, `docs/presence_agents.md`, `docs/roadmap_backlog_central.md`, journal prive du protocole reconstruction via `tools/reconstruction-protocol.cmd`.
Fichiers a eviter: code applicatif hors build executable si necessaire, extracteurs, instances privees hors journal protocole, documents bruts, OCR/logs, exports bruts, secrets, Drive, serveurs durables, scan/kill, push GitHub.
Dernier point lu: protocole `READY`, document courant `DOC-0154`, dernier document clos `DOC-0153`; aucune trace publique `DOC-0154` trouvee au preflight.
Lease ownership: 2026-06-01 18:45 +02:00.

ROUTAGE_EQUIPE
- Expert metier/confidentialite: confirmer que la cloture ne publie aucun contenu brut et que les controles obligatoires sont presents.
- Novice/designer: garder une formulation simple pour Brice et eviter les mots qui promettent une validation comptable definitive.
- CoproScope: controler les routes UI protegees utiles au protocole.
- QA: verifier absence de marqueurs cibles de fuite et test executable avec SHA-256.

Contraintes de wording public: ne pas ecrire que le document est valide, complet, publiable ou sans risque. Dire seulement que les controles du protocole sont realises, si le gate passe.

EXECUTION
- Lecture brute IA cote expert: document de la serie factures energie, lisible apres OCR local de secours, avec informations principales recuperees par CoproScope.
- Audit metier: cloture interne possible, mais pas de validation comptable finale. L'identifiant fiscal fournisseur reste absent et doit rester visible comme reserve avant tout usage officiel.
- Retour novice CoproScope: l'ecran doit faire comprendre "facture lue, mais encore a verifier", sans donner l'impression que CoproScope certifie la piece.
- Retour designer: pas de blocage avant document suivant, car le probleme restant est une reserve de verification et non une impossibilite de traitement. A conserver dans le backlog immediat de la serie energie.
- QA confidentialite: diffusion brute interdite; seules des syntheses agregees et nettoyees peuvent sortir du dossier prive.
- CoproScope/UI: fiche document protegee et file des factures a revoir controlees sur la derniere version de l'executable.

TRI DESIGNER
- Avant document suivant: aucun point bloquant restant.
- Backlog immediat: rendre encore plus explicite la reserve "identifiant fiscal fournisseur absent" dans les series de factures energie.
- Exploration future: tableau energie par periode/compteur/puissance, uniquement apres biffage et controles metier.

PREUVES
- Smoke executable HTTP sur la fiche document protegee: OK.
- Smoke executable HTTP sur la file des factures a revoir: OK.
- Version testee: `CoproScope.exe` SHA-256 `7E685F2DB5B1F7CFA38E38C69788955AE168E75A2FF97B6A2FCC0AE1F8B1B6D4`.
- Protocole prive: roles expert, designer, novice, CoproScope et QA notes; tri realise; gate clos.

BOT-END - Coordinateur-scribe reconstruction P0 - 2026-06-01 16:49 +02:00
Roadmap: `RM-2026-0017`
Chantier: `CH-20260601-164500-RM-2026-0017-doc154-protocole`
Conversation: `CONV-2026-1983`
Statut: `INTEGRE`
Fichiers modifies: ce document, `docs/presence_agents.md`, `docs/roadmap_backlog_central.md`, journal prive du protocole reconstruction.
Fichiers volontairement evites: documents bruts, OCR/logs, exports bruts, secrets, Drive, code applicatif, serveurs durables, chemins ou noms de fichiers sources.
Limites: la cloture signifie seulement que le protocole local est complet pour ce document; la reserve fournisseur reste a traiter dans le backlog metier.
