# Equipe agile - conversation No2 - trace DOC-0156

BOT-START - Coordinateur-scribe reconstruction P0 - 2026-06-01 16:54 +02:00

Roadmap: `RM-2026-0017`
Ordre: `ORD-P0-990`
Chantier: `CH-20260601-165400-RM-2026-0017-doc156-trace`
Conversation: `CONV-2026-1984`
Mission: traiter puis regulariser la trace publique de `DOC-0156`, sans publier de contenu documentaire.
Equipe-type: petite iteration agile avec QA confidentialite, novice/designer et coordinateur-scribe.
Ownership modifiable: ce document, `docs/presence_agents.md`, `docs/roadmap_backlog_central.md`.
Fichiers a eviter: code applicatif, instances privees hors synthese anonymisee du protocole, documents bruts, OCR/logs, exports bruts, secrets, Drive, serveurs durables, scan/kill, push GitHub.
Dernier point lu: protocole bloque sur `DOC-0156`, piece classee facture mais initialement en OCR requis.
Lease ownership: 2026-06-01 18:54 +02:00.

ROUTAGE_EQUIPE
- QA confidentialite: verifier que la trace se limite a la synthese anonymisee du protocole et ne contient aucun extrait, chemin, nom source ou identifiant sensible.
- Novice/designer: garder une formulation simple, sans promettre de validation metier definitive.
- Coordinateur-scribe: appliquer seulement le traitement local necessaire, puis publier une trace anonymisee.

EXECUTION
- Analyse brute IA: facture energie scannee lisible sur image; les montants et la periode sont visibles dans le document brut.
- Ecart CoproScope initial: la piece etait classee facture, mais restait en OCR requis et la table factures ne recuperait pas les montants.
- Traitement machine avant document suivant: OCR local cible lance sur la piece, puis recalcul FactureOps.
- Resultat interne: fournisseur energie reconnu, montants HT/TVA/TTC recuperes, compte energie propose, statut maintenu `INCERTAIN`.
- Reserve metier: identifiant fiscal fournisseur absent; rapprocher avec le prelevement bancaire et la periode comptable avant toute conclusion officielle.

PREUVES
- Synthese anonymisee du protocole: `DOC-0156`, OCR cible applique, controles obligatoires termines, roles CoproScope/designer/expert/novice/QA notes.
- Version executable referencee par le protocole: `CoproScope.exe` SHA-256 `7E685F2DB5B1F7CFA38E38C69788955AE168E75A2FF97B6A2FCC0AE1F8B1B6D4`.
- Aucune trace publique `DOC-0156` existante trouvee avant cette regularisation.

BOT-END - Coordinateur-scribe reconstruction P0 - 2026-06-01 16:58 +02:00
Roadmap: `RM-2026-0017`
Chantier: `CH-20260601-165400-RM-2026-0017-doc156-trace`
Conversation: `CONV-2026-1984`
Statut: `INTEGRE`
Fichiers modifies: ce document, `docs/presence_agents.md`, `docs/roadmap_backlog_central.md`.
Fichiers volontairement evites: documents bruts, OCR/logs, exports bruts, secrets, Drive, code applicatif, serveurs durables, chemins ou noms de fichiers sources.
Limites: la cloture ne vaut pas validation comptable finale; les reserves fournisseur et rapprochement bancaire restent dans le backlog metier.
