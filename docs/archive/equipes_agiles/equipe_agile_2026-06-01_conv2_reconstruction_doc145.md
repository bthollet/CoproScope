# Equipe reconstruction - CONV2 DOC-0145

BOT-START - Coordinateur-scribe reconstruction P0 - 2026-06-01 16:11 +02:00

Roadmap: `RM-2026-0017`
Ordre: `ORD-P0-990`
Chantier: `CH-20260601-161100-RM-2026-0017-doc145-protocole`
Conversation: `CONV-2026-1979` / conversation utilisateur No2
Role: coordinateur-scribe, avec roles expert, designer, novice, CoproScope et QA joues via sous-agents courts et protocole.
Mission: traiter le document courant libre du protocole reconstruction sans chevaucher `CONV-2026-1975` et sans publier de contenu prive.
Equipe-type: `RECHERCHE_METIER` adaptee au protocole reconstruction.
Ownership modifiable: ce document, `docs/presence_agents.md`, `docs/roadmap_backlog_central.md`, journal prive du protocole reconstruction via `tools/reconstruction-protocol.cmd`.
Fichiers a eviter: code applicatif, extracteurs, fichiers OCR/energie reserves par `CONV-2026-1975`, instances privees hors journal protocole, documents bruts, OCR/logs, exports bruts, secrets, Drive, serveurs durables, scan/kill, push GitHub.
Dernier point lu: protocole `WAIT_MERGE` mais safe summary `DOC-0145` actionnable, document courant `DOC-0145`, dernier document clos `DOC-0144`; aucune trace publique ou worktree vivant `DOC-0145` trouve au preflight.
Lease ownership: 2026-06-01 18:11 +02:00.

ROUTAGE_EQUIPE
Preflight: OK sur le document courant, `WAIT_MERGE` maintenu pour l'integration Git concurrente
Equipe-type: `RECHERCHE_METIER`
Orchestration: serie stricte document par document
Roadmap / ORD: `RM-2026-0017` / `ORD-P0-990`
Chantier: `CH-20260601-161100-RM-2026-0017-doc145-protocole`
Coordinateur: `CONV-2026-1979`
Owner code unique: aucun; code evite.
Roles lances: expert metier/privacy, designer tri, novice CoproScope, observation CoproScope, QA privacy.
Roles explicitement non lances: dev front/back, integration release, Drive.
Condition d'arret: gate document OK et document clos, ou blocage explicite reutilisable.

## Cloture

Le document a ete traite dans le journal prive du protocole reconstruction. La trace publique ne reprend pas le contenu du document: pas de nom de fichier, chemin local, OCR brut, identifiant, reference bancaire, extrait ou donnee personnelle.

Constat partageable: la piece est exploitable en interne apres lecture locale de secours, mais elle conserve une reserve de controle fournisseur. La conclusion produit reste prudente: passage au document suivant autorise, validation comptable finale non acquise, publication brute interdite.

Retours roles:

- Expert metier: GO cloture interne, NO-GO validation comptable finale.
- Designer: l'ecran doit distinguer pret au traitement, controle fait et piece publiable.
- Novice: la reserve doit etre formulee simplement, sans donner l'impression que "pret" veut dire "partageable".
- CoproScope: pages de revue et fiche protegee consultees; lecture machine revue.
- QA: routes controlees sans marqueurs cibles de fuite; partage seulement sous forme de synthese nettoyee.

Preuves:

- protocole prive: `DOC-0145` ferme;
- routes controlees: inbox, file factures et fiche protegee;
- smoke executable initial OK;
- smoke executable supplementaire enregistre avec le build OCR/energie `2E9E5780265743B0B68A388BFA06603BC9334DF173A3665FFD7708F61470BFAF`;
- aucun contenu brut publie dans cette trace.

BOT-END - Coordinateur-scribe reconstruction P0 - 2026-06-01 16:14 +02:00

Statut: `PRET_A_INTEGRER`
Fichiers modifies: cette trace, `docs/presence_agents.md`, `docs/roadmap_backlog_central.md`, journal prive protocole.
Fichiers volontairement evites: code applicatif, extracteurs, documents bruts, OCR/logs, exports bruts, secrets, Drive.
Limites: pas de nouvelle fonctionnalite produit dans ce passage; les reserves metier restent dans le journal prive et le backlog.
