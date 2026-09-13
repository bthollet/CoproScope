# Equipe reconstruction - DOC-0142 OCR energie

BOT-START - Coordinateur-dev reconstruction P0 - 2026-06-01 15:44 +02:00

Roadmap: `RM-2026-0017`
Ordre: `ORD-P0-990`
Chantier: `CH-20260601-154439-RM-2026-0017-doc142-ocr-energy`
Conversation: `CONV-2026-1975`
Role: coordinateur-dev avec roles expert, designer, novice, CoproScope et QA joues via le protocole reconstruction.
Mission: corriger le point bloquant observe sur une facture energie scannee: CoproScope ne devait plus deduire les informations depuis le nom technique quand le texte local etait insuffisant.

## Retour multi-roles

- Expert metier: la facture pouvait seulement etre traitee comme piece a controler tant que l'OCR local ne lisait pas les champs essentiels; les totaux, la periode et le mode de paiement doivent rester sous reserve avant validation comptable.
- Novice CoproScope: l'ecran doit dire clairement ce que la machine a lu, ce qui manque et ce qui reste a verifier; une date deduite du nom de fichier est trompeuse.
- Designer: correction avant document suivant pour l'OCR local et le routage energie; les champs fins energie restent en backlog.
- CoproScope: apres OCR local, la piece passe en lecture locale OCR, avec date facture, total hors taxes, TVA, TTC, compte energie et statut de controle incertain.
- QA privacy: les pages controlees restent protegees; pas d'affichage de chemin local, fichier brut, texte OCR brut, email, telephone ou reference bancaire.

## Changements livres

- OCR local Tesseract ajoute comme moteur DocAI utilisable et visible dans le statut local.
- CLI `docai ocr` et configuration locale acceptent maintenant `tesseract`.
- Extracteur energie renforce pour lire une facture scannee avec date en mois francais, numero facture, HT final, TVA et TTC.
- Routage facture renforce pour envoyer les factures energie vers le compte propose `606100` et la famille `energie_electricite`.
- Tests unitaires ajoutes pour l'OCR Tesseract simule et le routage facture energie OCR.

## Preuves

- Tests cibles: `server.tests.test_docai`, `server.tests.test_factureops_provider_routing`, `server.tests.test_ui_factures_review` = 20 OK.
- Garde-fou lignes: `tools/check_code_line_limit.py` OK.
- Controle diff: `git diff --check` OK.
- Build desktop: `CoproScope.exe` reconstruit dans `server/dist/reconstruction-ocr-energy-p0-20260601-1604-ready`.
- SHA-256: `2E9E5780265743B0B68A388BFA06603BC9334DF173A3665FFD7708F61470BFAF`.
- Smokes executable: file factures, fiche document energie et mode fenetre OK.
- Protocole prive: test executable supplementaire enregistre pour `DOC-0142`.

## Backlog conserve

- Extraire plus finement periode, echeance, mode de paiement, consommation, puissance et taxes energie.
- Afficher une explication novice sur la source de chaque champ: lu dans OCR, deduit, manquant ou a verifier.
- Ajouter un suivi comparatif energie par periode et par serie de factures similaires.
- Continuer a separer strictement resume diffusable et donnees brutes sensibles.

BOT-END - Coordinateur-dev reconstruction P0 - 2026-06-01 16:11 +02:00

Statut: `PRET_A_INTEGRER`
Fichiers modifies: DocAI, FactureOps, extracteur energie, configuration CLI/instance, tests cibles, traces presence/roadmap.
Fichiers volontairement evites: documents bruts, OCR brut, journaux prives, chemins locaux, Drive, donnees reelles dans Git.
Limites: l'analyse metier fine de l'energie reste en backlog; cette livraison stabilise la lecture machine et la preuve executable.
