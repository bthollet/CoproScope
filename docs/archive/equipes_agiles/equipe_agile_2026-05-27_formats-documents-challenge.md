# Equipe agile - formats ingestion et types documentaires

Date: 2026-05-27
Roadmap: `RM-2026-0041`
Chantier: `CH-20260527-230735-RM-2026-0041-formats-documents-challenge`
Conversation coordinatrice: `CONV-2026-1797`
Statut: integre documentairement, sans dev.

## BOT-START

- Heure: 2026-05-27 23:07 +02:00.
- Role: coordinateur-scribe formats ingestion et typologie documentaire.
- Mission: challenger les formats que CoproScope doit ingerer, les preuves
  techniques necessaires, les types documentaires metier et les frontieres entre
  document, piece, preuve, demande, decision, contrat, incident, chantier et
  rapprochement comptable.
- Roadmap/chantier/conversation: `RM-2026-0041` /
  `CH-20260527-230735-RM-2026-0041-formats-documents-challenge` /
  `CONV-2026-1797`.
- Ownership modifiable: ce document, `docs/roadmap_backlog_central.md`,
  `docs/presence_agents.md`.
- Fichiers a eviter: code applicatif, routes, templates, CSS, tests
  applicatifs, instances privees, documents bruts, OCR/logs, exports bruts,
  secrets, migrations, serveurs, scans/kills, push GitHub, `RM-2026-0017`,
  `ORD-P0-990`.
- Passerelle/registre de trace: ce document, presence agents, gouvernail.
- Dernier point lu: presence/gouvernail au 2026-05-27 23:05 +02:00; challenge
  DB `CONV-2026-1795` en cours; dev compta `CONV-2026-1796` en cours.
- Tests/preuves attendus: retours agents, matrice backlog, `git diff --check`
  documentaire.
- Risque de collision: `CONV-2026-1795` possede deja le challenge DB. Ce lot est
  un sous-challenge DocOps/format/type, sans dev et sans second owner code.
- Lease ownership: 2026-05-28 01:07 +02:00.
- Prochaine action: integrer les retours des agents experts dans un backlog
  exploitable.

## Equipe lancee

| Conversation | Agent | Role | Scope | Sortie attendue |
| --- | --- | --- | --- | --- |
| `CONV-2026-1798` | Lorentz | Backend DocOps/DocAI/FactureOps | Ingestion, extraction, OCR, Docling, e-factures, generateurs extracteurs | Formats supportes/manquants, risques backend, backlog technique. |
| `CONV-2026-1799` | Erdos | Syndic, gouvernance, juridique documentaire | AG, PV, convocation, decision, demandes, diffusion prudente | Typologie metier, distinctions dangereuses, backlog gouvernance. |
| `CONV-2026-1800` | Maxwell | Compta/audit copro | Factures, devis, annexes, grand livre, banque, budget, impayes | Types comptables, sources a ingerer, validations humaines. |
| `CONV-2026-1801` | Planck | Travaux, incidents, contrats, privacy | Chantiers, sinistres, assurances, photos, contrats, biffage | Typologie travaux/incidents/contrats et garde-fous diffusion. |
| `CONV-2026-1802` | Rawls | QA produit / novice | `/documents/ajouter`, `/documents/tri-feedback`, libelles et corrections humaines | UX de correction du type documentaire et etats ambigus. |

Tous les agents sont en lecture seule. Ils ne doivent modifier aucun fichier,
ne lancer aucun serveur et ne consulter aucune donnee d'instance privee.

## UI et surfaces reelles a challenger

- Parcours existant: `/documents/ajouter`.
- Parcours existant: `/documents/tri-feedback`.
- Surface backend: `docuscope`, `docai`, `factureops`, generateurs
  `extractors/invoices`.
- Sortie attendue: une matrice `format source -> preuve technique -> type
  documentaire possible -> action humaine -> garde-fou privacy`.

## Questions a trancher

1. Quels formats sont des entrees V1 obligatoires, optionnelles ou refusees ?
2. Quels formats doivent produire texte natif, OCR, structure locale ou revue
   humaine avant toute classification ?
3. Quels types documentaires manquent a la taxonomie de copropriete ?
4. Quelles frontieres doivent etre bloquees pour eviter une confusion entre
   document, piece candidate, preuve validee, decision, action et export ?
5. Quels extracteurs peuvent rester generiques et lesquels doivent etre par
   fournisseur, par famille comptable ou par type metier ?

## Synthese consolidee

L'equipe converge sur un meme diagnostic: CoproScope sait deja inventorier
largement, extraire plusieurs formats courants et traiter les factures, mais il
manque encore une couche canonique qui relie format technique, preuve
exploitable, type metier et decision humaine.

Le risque principal n'est pas de ne pas accepter assez de fichiers. C'est
d'accepter un fichier sans dire clairement s'il est lisible, s'il demande OCR,
s'il est seulement une piece candidate, ou s'il peut devenir une preuve apres
revue.

Points decisifs:

- l'upload et l'extraction ne sont pas parfaitement alignes: `yaml/yml` peuvent
  etre acceptes sans extraction native, tandis que `xml/ubl/cii` sont lus par
  FactureOps mais pas integres proprement au parcours DocOps;
- Factur-X est declare comme cible, mais l'extraction XML embarquee dans un PDF
  n'est pas livree;
- les extracteurs fournisseurs existent en tests, mais le flux FactureOps
  principal reste surtout generique;
- la taxonomie courante couvre trop peu de types metier au regard de la
  privacy et de la completude attendue;
- `Annexe_Comptable`, `Facture`, `Devis` ne suffisent pas pour les comptes:
  grand livre, etat de depenses, banque, budget, appels, fonds travaux et
  impayes doivent devenir distincts;
- `/documents/tri-feedback` doit travailler sur les vrais documents a corriger,
  ou dire explicitement qu'il s'agit d'un brouillon/simulateur;
- aucun export ou "OK" metier ne doit etre autorise tant que la frontiere piece
  candidate -> preuve validee n'est pas explicite.

## Matrice cible

| Entree | Preuve technique attendue | Types metier concernes | Action humaine | Garde-fou |
| --- | --- | --- | --- | --- |
| PDF texte | Texte natif, pages, hash | AG, contrats, factures, annexes, courriers | Confirmer type, periode et diffusion | Pas de decision issue d'une convocation seule. |
| PDF scan / image | OCR local ou sidecar, qualite OCR | Photos incident, PV scan, devis scan, attestations | Revue si OCR faible | Original sensible non affiche dans export. |
| TXT/MD/CSV/TSV/JSON | Texte natif ou lignes structurees | Communications, registres, etats de depenses | Verifier source et schema | Pas de chemin local dans sortie. |
| XLSX | Feuilles et cellules lues | Comptes, budgets, etats de depenses, impayes | Valider exercice, colonnes, total | Impayes et banque restreints/agreges. |
| DOCX/HTML | Texte visible, tableaux | CR CS, courriers, contrats, PV projet | Distinguer projet/officiel | Badge `Projet CS - non officiel` si besoin. |
| XML/UBL/CII/Factur-X | Source structuree e-facture | Facture, avoir, note d'honoraires | Controler fournisseur, montants, periode | Ne pas pretendre Factur-X livre tant que XML embarque non extrait. |
| EML/MSG/MBOX | Message + pieces jointes + hash par piece | Communication, notification, preuve d'envoi | Distinguer trace mail et notification officielle | Connecteur/envoi automatique hors V1. |
| ZIP/export extranet | Manifeste local, parent/enfants, hash | Dossier travaux, AG + annexes, exports syndic | Classer chaque enfant, pas seulement le zip | Quarantaine locale, aucun raw cloud. |
| OFX/QIF/CAMT/CSV banque | Mouvements normalises | Banque, paiements, rapprochements | Validation humaine, masquage IBAN/RIB | Sortie publique agregatee seulement. |
| Formats inconnus | Hash, statut unsupported/manual review | A classer | Dire pourquoi c'est bloque | Pas de conclusion metier. |

## Typologie documentaire cible

Types P0 a aligner entre taxonomie, privacy, completude, UI et schemas:

- referentiel copro: `Reglement_Copropriete`, `EDD`, modificatifs, fiche
  synthetique, carnet entretien, diagnostics, plans;
- AG/gouvernance: `Convocation_AG`, ordre du jour, `Annexe_AG`, `PV_AG`,
  notification PV, feuille de presence, pouvoirs, vote par correspondance,
  CR CS, projet CS non officiel;
- syndic: contrat syndic projet, contrat syndic signe, garantie financiere,
  assurance RC, carte professionnelle, mandat;
- compta: facture, avoir, note d'honoraires, devis, bon de commande, ordre de
  service, annexe comptable, grand livre, balance, etat de depenses, budget,
  appel de fonds, fonds travaux, releve bancaire, impayes;
- contrats/fournisseurs: contrat fournisseur, contrat assurance, attestation,
  avenant, obligation, echeance, bon d'intervention;
- travaux/incidents: dossier travaux, devis compare, marche, situation,
  reception, reserve, levee de reserve, garantie, DOE, photo incident,
  declaration assurance, expertise;
- communications/preuves: mail local, courrier, LRAR, accuse reception, preuve
  d'envoi, preuve d'execution, reponse syndic;
- contentieux/restreint: contentieux nominatif, recouvrement, pieces sensibles
  a diffusion bloquee ou agregee.

## Frontieres non negociables

| Frontiere | Regle |
| --- | --- |
| Format accepte != format exploitable | L'UI doit afficher texte extrait, OCR requis, structure disponible, non supporte ou revue manuelle. |
| Document != piece candidate | Un document local peut etre propose comme piece, mais reste candidat. |
| Piece candidate != preuve validee | Promotion seulement apres revue humaine, niveau d'evidence et privacy gate. |
| Convocation != decision votee | Une resolution issue d'une convocation reste candidate avant PV signe/notifie. |
| Projet CS != officiel | Badge projet et blocage des promesses de convocation/PV/officiel. |
| Email != notification officielle | Distinguer trace de communication et preuve d'envoi/notif. |
| Action != decision/preuve/demande | L'action reste une tache humaine derivee, pas l'objet source. |
| Diffusable brut != partage autorise partout | Diffusion contextualisee, biffage/agregation/justification si requis. |

## Backlog integre au gouvernail

| ID | Priorite | Sujet | Livrable attendu |
| --- | --- | --- | --- |
| `FMT-20260527-01` | P0 | Matrice formats/capabilities canonique | Source unique pour upload, DocOps, FactureOps, privacy et UI: accepte, texte natif, OCR, structure, biffage possible, statut refuse. |
| `FMT-20260527-02` | P0 | Taxonomie documentaire copro V1 | Aligner `taxonomy`, `document_completeness`, `privacy_rules`, options UI et schemas; ajouter les types P0 manquants. |
| `FMT-20260527-03` | P0 | Frontiere piece candidate -> preuve validee | Recorder/evenement ou contrat applicatif qui exige revue humaine, evidence level, diffusion et statut. |
| `FMT-20260527-04` | P0 | Tri feedback branche sur vrais documents | `/documents/tri-feedback` doit corriger le registre documentaire ou afficher un brouillon clairement non applique. |
| `FMT-20260527-05` | P0 | Routage extracteurs factures | Brancher les extracteurs fournisseurs dans le flux principal avec fallback generique et tests end-to-end. |
| `FMT-20260527-06` | P1 | Documents composes et pieces jointes | Parent/enfants, hash par piece, zip/export/mail avec manifeste local, sans copie brute inutile. |
| `FMT-20260527-07` | P1 | Sources compta et banque etendues | Schemas `accounting_line`, `bank_movement`, `budget_line`, `fund_call`, `arrears_snapshot`, sans fuite IBAN/RIB. |
| `FMT-20260527-08` | P1 | UX correction novice | Une piece active, question de type claire, motifs obligatoires si restriction, details techniques replies. |
| `FMT-20260527-09` | P2 | Corpus synthetique multi-format | Scans, e-factures, emails, zip, tableurs, banque, photos, pieces sensibles fictives et ambiguites. |

## Retours agents consolides

- Lorentz: support backend deja large, mais incoherences upload/extraction;
  e-factures et extracteurs fournisseurs a brancher vraiment.
- Erdos: taxonomie metier trop courte; AG officielle, referentiel copro,
  syndic, CS, participants AG et diffusion doivent etre mieux separes.
- Maxwell: le modele compta ne doit pas rester facture + etat des depenses;
  banque, budget, appels, fonds travaux et impayes demandent des objets/schemas
  dedies.
- Planck: travaux, incidents et contrats ont leurs cycles de vie propres;
  photos, reception, reserves, attestations et obligations exigent privacy gate
  et preuve de cloture.
- Rawls: l'UI novice doit cacher les codes techniques, distinguer les etats
  vides, rendre les motifs obligatoires et brancher le tri feedback sur des
  documents reels ou un brouillon explicite.

## BOT-END

- Heure: 2026-05-27 23:15 +02:00.
- Roadmap: `RM-2026-0041`.
- Chantier: `CH-20260527-230735-RM-2026-0041-formats-documents-challenge`.
- Conversation: `CONV-2026-1797`.
- Statut: `INTEGRE`.
- Fichiers modifies: ce document, `docs/roadmap_backlog_central.md`,
  `docs/presence_agents.md`.
- Fichiers volontairement evites: code applicatif, routes, templates, CSS,
  tests applicatifs, instances privees, documents bruts, OCR/logs, exports
  bruts, secrets, migrations, serveurs, scans/kills, push GitHub.
- Tests/preuves: cinq agents lecture seule termines; backlog `ORD-P0-060` a
  `ORD-P0-064` ajoute au gouvernail; verification documentaire `git diff
  --check` a lancer apres patch final.
- Limites: pas de dev, pas de recette navigateur, pas de modification de
  taxonomie ou schema dans ce lot.
- Questions ouvertes: prioriser entre taxonomie V1, matrice formats,
  preuve validee et tri feedback reel; recommandation: commencer par matrice
  formats + taxonomie, puis preuve validee.
- Prochain mouvement propose: ouvrir un owner dedie sur `ORD-P0-061` ou
  `ORD-P0-062` selon l'arbitrage produit.
