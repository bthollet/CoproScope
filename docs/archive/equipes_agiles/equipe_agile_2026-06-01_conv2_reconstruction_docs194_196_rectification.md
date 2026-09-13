# Equipe agile - conversation No2 - rectification DOC-0194 a DOC-0196

BOT-START - Coordinateur-scribe reconstruction P0 - 2026-06-01 19:40 +02:00

Roadmap: `RM-2026-0017`
Ordre: `ORD-P0-990`
Chantier: `CH-20260601-194000-RM-2026-0017-doc194-doc196-rectification`
Conversation: `CONV-2026-2021`
Mission: rectifier la consignation privee de `DOC-0194`, `DOC-0195` et `DOC-0196`, sans publier de contenu documentaire.
Equipe-type: designer + novice CoproScope + QA privacy, avec rectification d'audit pour ne pas conserver un faux etat "montant absent".
Ownership modifiable: ce document, `docs/presence_agents.md`, `docs/roadmap_backlog_central.md`, journal prive du protocole reconstruction.
Fichiers a eviter: documents bruts, OCR/logs, exports bruts, secrets, Drive, chemins locaux, noms de fichiers sources, donnees bancaires, references client ou compteur, donnees personnelles.

RECTIFICATION
- Les trois documents sont des factures energie scannees traitees en serie.
- Le registre prive a ete rectifie: les montants principaux sont presents apres OCR local; l'etat utile est `INCERTAIN`, avec controle fournisseur a completer.
- Les anciennes formulations laissant croire a un montant total absent ne doivent plus etre utilisees pour cette serie.
- Les retours designer, novice, CoproScope et QA privacy ont ete ajoutes au protocole prive.

DIF
- Ajouts consignes: affichage conjoint du montant, de l'OCR reussi, de la preuve OCR locale, du statut `INCERTAIN` et de l'anomalie fournisseur.
- Ajouts developpement: eviter la confusion "OCR reussi = facture validee"; bloquer la validation comptable automatique tant que les controles metier restent incomplets.
- Ajouts confidentialite: renforcer le masquage des references energie, coordonnees, donnees bancaires et donnees personnelles dans les vues et exports.
- Ajouts exploration: vue serie energie pour comparer periode, montant, doublons et chevauchements; audit consommation/cout et rapprochement contrat-facture-paiement.

BOT-END - Coordinateur-scribe reconstruction P0 - 2026-06-01 19:40 +02:00
Statut: `INTEGRE`
Limites: trace publique volontairement anonymisee; aucune validation metier definitive; aucun contenu brut publie.
