# Equipe reconstruction - CONV2 DOC-0132

BOT-START - Coordinateur-scribe reconstruction P0 - 2026-06-01 14:30 +02:00

Roadmap: `RM-2026-0017`
Ordre: `ORD-P0-990`
Chantier: `CH-20260601-143014-RM-2026-0017-doc132-protocole`
Conversation: `CONV-2026-1966` / conversation utilisateur No2
Role: coordinateur-scribe, avec roles expert metier, designer tri, novice CoproScope, observation CoproScope et QA privacy joues par sous-agents si disponibles, sinon sequentiellement.
Mission: faire avancer le document courant du protocole reconstruction sans toucher aux correctifs FactureOps/ASV ni exposer de donnees privees.
Equipe-type: `RECHERCHE_METIER` adaptee au protocole reconstruction.
Orchestration: serie stricte; aucune modification code tant que le protocole document par document n'en prouve pas le besoin.
Ownership modifiable: ce document, `docs/presence_agents.md`, `docs/roadmap_backlog_central.md`, journal prive du protocole reconstruction via `tools/reconstruction-protocol.cmd`.
Fichiers a eviter: `server/src/coproscope/modules/factureops.py`, `server/src/coproscope/extractors/invoices/providers/asv.py`, `server/tests/test_factureops_provider_routing.py`, instances privees hors journal protocole, documents bruts, OCR brut, logs, exports bruts, secrets, Drive, serveurs non reserves, scan/kill, push GitHub.
Passerelle/registre de trace: ce document, `docs/presence_agents.md`, `docs/roadmap_backlog_central.md`, journal prive `docs_de_travail/protocole_reconstruction`.
Dernier point lu: `AGENTS.md`, `docs/consignes_bots_interconversations.md`, `docs/protocole_roadmap_presence_agents.md`, `docs/strategie_equipes_multi_agents.md`, `docs/presence_agents.md`, `docs/roadmap_backlog_central.md`, statut protocole reconstruction du 2026-06-01 14:30 +02:00.
Risque de collision: repo principal contient ou contenait des travaux FactureOps/ASV; ce chantier utilise un worktree propre et evite ces fichiers.
Tests/preuves attendus: statut protocole `READY`, roles notes pour le document courant, tri designer, test executable ou blocage explicite, `git diff --check`, garde-fou line-limit.
Lease ownership: 2026-06-01 16:30 +02:00.
Prochaine action: traiter `DOC-0132` en notes anonymisees, ou tracer un blocage si le protocole impose un contenu brut ou une integration prealable.

ROUTAGE_EQUIPE
Preflight: OK
Equipe-type: `RECHERCHE_METIER`
Orchestration: serie stricte document par document
Roadmap / ORD: `RM-2026-0017` / `ORD-P0-990`
Chantier: `CH-20260601-143014-RM-2026-0017-doc132-protocole`
Coordinateur: `CONV-2026-1966`
Owner code unique: aucun; code evite.
Roles a lancer: expert metier, designer tri, novice CoproScope, observation CoproScope, QA privacy.
Roles explicitement non lances: dev front/back, integration release, Drive.
Gates avant dev: preuve protocole d'un defaut borne; sinon notes journal prive uniquement.
Livrable attendu: document courant avance ou blocage qualifie, sans fuite de contenu prive.
Condition d'arret: gate document OK et document clos, ou blocage explicite reutilisable.

EXECUTION
- `DOC-0131` etait deja clos au moment de la reprise; il n'a pas ete rouvert.
- `DOC-0132` a ete traite dans le journal prive uniquement, avec notes anonymisees des roles expert, designer, novice, CoproScope et QA.
- Le tri designer a ete resolu avant passage au document suivant: fuite brute detail, maintien en reprise humaine et risque de doublon/facture voisine.
- Aucun code applicatif n'a ete modifie; FactureOps/ASV sont restes hors ownership de cette conversation.

PREUVES
- Statut protocole avant execution: `READY`; document courant `DOC-0132`.
- Routes TestClient privees verifiees: inbox, file factures a revoir et fiche document en 200, sans marqueur `C:\`, `file://`, `raw/`, `raw\`, `restricted/`, `logs/` ou `private/`.
- Smoke executable HTTP sur la file factures a revoir: OK, SHA-256 `9C9D02A9938C4C98A40039AF284485586221EB9FCD2C0B4F1698397A0D6757F5`.
- Gate protocole: `OK - passage autorise`; `DOC-0132` clos.
- Statut protocole apres cloture: document courant `aucun`, dernier document clos `DOC-0132`; le `WAIT_MERGE` restant vient des traces Git de cette conversation a integrer.

LIMITES
- Aucune donnee brute, nom de fichier source, OCR, chemin local, fournisseur, extrait ou contenu documentaire n'est repris dans Git.
- Aucun serveur visible longue duree n'a ete laisse ouvert; le smoke executable ferme le processus qu'il lance.
- La prochaine ouverture de document doit attendre l'integration ou le rangement de cette trace, pour que le protocole repasse `READY`.

BOT-END - Coordinateur-scribe reconstruction P0 - 2026-06-01 14:36 +02:00
Roadmap: `RM-2026-0017`
Chantier: `CH-20260601-143014-RM-2026-0017-doc132-protocole`
Conversation: `CONV-2026-1966`
Statut: `PRET_A_INTEGRER`
Fichiers modifies: ce document, `docs/presence_agents.md`, `docs/roadmap_backlog_central.md`, journal prive protocole reconstruction hors Git.
Fichiers volontairement evites: code applicatif, FactureOps/ASV, documents bruts, OCR/logs, exports bruts, secrets, Drive, serveurs non reserves, scan/kill, push GitHub.
Tests/preuves: routes TestClient 200 sans marqueurs de fuite, smoke executable HTTP OK, gate protocole OK, `DOC-0132` clos.
Limites: pas de publication de contenu prive; pas d'ouverture du document suivant tant que les traces Git ne sont pas integrees.
Prochain mouvement propose: integrer ou ranger cette trace, puis ouvrir le prochain document via `tools/reconstruction-protocol.cmd next-doc`.
