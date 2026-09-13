# Equipe agile - conversation No2 - rectification DOC-0197 a DOC-0199

BOT-START - Coordinateur-scribe reconstruction P0 - 2026-06-01 19:52 +02:00

Roadmap: `RM-2026-0017`
Ordre: `ORD-P0-990`
Chantier: `CH-20260601-195200-RM-2026-0017-doc197-doc199-rectification`
Conversation: `CONV-2026-2024`
Mission: rectifier la consignation privee de `DOC-0197`, `DOC-0198` et `DOC-0199`, sans publier de contenu documentaire.
Equipe-type: expert metier + designer + novice CoproScope + QA privacy, joues en correction locale apres OCR.
Ownership modifiable: ce document, `docs/presence_agents.md`, `docs/roadmap_backlog_central.md`, journal prive du protocole reconstruction.
Fichiers a eviter: documents bruts, OCR/logs, exports bruts, secrets, Drive, chemins locaux, noms de fichiers sources, donnees bancaires, references client ou compteur, donnees personnelles.

RECTIFICATION
- Les trois documents etaient en `OCR_REQUIRED` lors de la premiere consignation; l'ancienne conclusion "montant absent" etait donc prematuree.
- Apres OCR local et recalcul facture, les montants principaux sont presents.
- Le statut utile est `INCERTAIN`: facture energie a controler, identifiant fournisseur a completer, validation automatique interdite.
- Les notes expert, designer, novice, CoproScope et QA ont ete ajoutees dans le protocole prive.
- Les fiches document ont ete testees sur le dernier executable; `OCR_DONE` et le moteur OCR sont visibles.

DIF
- Ajout produit: retirer automatiquement un P0 "montant absent" quand un OCR ulterieur lit bien le TTC.
- Ajout UX: afficher ensemble OCR reussi, montant present, statut `INCERTAIN`, preuve OCR locale et anomalie fournisseur.
- Ajout metier: comparer les factures energie d'une meme periode par compteur masque, montant et consommation, sans conclure trop vite a un doublon.
- Ajout confidentialite: masquer les references energie, compteur, mandat, banque, contacts et donnees personnelles dans les apercus et exports.
- Exploration future: rapprochement contrat energie / compteur / facture / banque et suivi cout-consommation.

PREUVES
- Gate protocole OK pour `DOC-0197`, `DOC-0198` et `DOC-0199`.
- Smokes executable HTTP OK sur les trois fiches document.
- `CoproScope.exe` SHA-256 `BDEE0DBC0368161500798D0341CA2D1EB172D543B1803E725FEB47150AF7E54E`.
- Compteur DIF apres rectification: backlog immediat et explorations futures augmentes; aucun point "avant document suivant" non resolu.

BOT-END - Coordinateur-scribe reconstruction P0 - 2026-06-01 19:52 +02:00
Statut: `INTEGRE`
Limites: trace publique volontairement anonymisee; aucune validation metier definitive; aucun contenu brut publie.
