# Veille open source et integration

Date de veille: 2026-05-20

Objectif: identifier les briques open source ou outils de bureau qui peuvent aider CoproScope sans verrouiller trop tot l'architecture. Le cap reste: noyau local sobre, source de verite CoproScope, plugins officiels signes, exports reversibles, transports de sync non fiables par defaut.

## Contrat d'architecture

- Noyau: seulement ce qui est indispensable a l'ouverture, la reconstruction, la recherche locale, les signatures et l'audit.
- Plugin officiel: integration maintenue, optionnelle, signable, revocable, testee.
- Export: format utile pour consultation ou partage, jamais source de verite.
- Transport externe: dossier synchronise par un outil tiers, sans confiance metier.
- Veille: piste interessante mais pas encore adoptee.

## Radar synthetique

| Outil | Role potentiel | Licence verifiee | Mode conseille | Risque principal |
|---|---|---|---|---|
| PDF.js | Visionneuse PDF web locale | Apache-2.0 | Plugin officiel de lecture | Confondre rendu PDF et modele d'annotation |
| Hypothesis | Inspiration annotation web | BSD-2-Clause | A surveiller | Architecture serveur trop large |
| Recogito Studio | Inspiration annotation collaborative | AGPL-3.0 | A surveiller | Copyleft/serveur lourd |
| Tesseract | OCR local | Apache-2.0 | Plugin officiel OCR | Qualite variable sur scans/tableaux |
| OCRmyPDF | Pipeline OCR PDF | MPL-2.0 | Plugin officiel OCR | Dependances et reecriture PDF sur copies |
| PyMuPDF | Extraction/rendu PDF avance | AGPL/commercial | A surveiller | Decision juridique obligatoire |
| RapidOCR | OCR alternatif | Apache-2.0 | Banc d'essai plugin | Poids modeles/runtimes |
| SQLite FTS5 | Recherche locale | SQLite public domain | Noyau | Tokenisation FR a soigner |
| DuckDB | Analytics local | MIT | Plugin officiel analytics | Ne pas devenir base transactionnelle |
| Grist | Interface tableur/base | Apache-2.0 community | Export/interface | Ne pas devenir source de verite |
| Syncthing | Sync peer-to-peer | MPL-2.0 | Transport externe documente | Suppressions et conflits propages |
| Nextcloud Desktop | Sync dossier | GPL-2.0-or-later client | Transport externe | Dependances serveur/admin |
| Google Drive Desktop | Sync dossier courant | proprietaire | Transport tolere | placeholders/conflits/compte Google |
| OneDrive | Sync dossier Windows | proprietaire | Transport tolere | Files On-Demand/chemins Windows |
| Dropbox Desktop | Sync dossier | proprietaire | Transport tolere | conflicted copies/online-only |
| Casbin | RBAC/ABAC | Apache-2.0 | A surveiller/plugin | Complexite des politiques |
| PyInstaller | Packaging Python | GPL avec exception bootloader | A evaluer | Antivirus/hooks natifs |
| Briefcase | Packaging Python apps | BSD-3-Clause | A surveiller | Compatibilite dependances |
| Tauri | Shell desktop WebView/Rust | MIT/Apache-2.0 | A evaluer | Toolchain et pont backend |

## Gates de decision

- Gate 0, veille: sources officielles, licence, risque, besoin produit.
- Gate 1, prototype jetable: travaille sur copies ou exports, jamais sur donnees canoniques.
- Gate 2, plugin officiel: optionnel, journalise, desinstallable, versionne, avec tests.
- Gate 3, noyau: exceptionnel, seulement si indispensable a l'ouverture ou a l'audit du coffre.

## Protocoles minimaux

| Domaine | Corpus minimal | Echec bloquant |
|---|---|---|
| PDF | 50 PDF reels: scans, PDF texte, gros contrats, factures, PV AG | modification du RAW ou ancre non reconstruisible |
| OCR | 100 pages FR variees | absence de provenance ou dependance non packagable |
| Recherche | 10k documents + 100k lignes metier synthetiques | index non reconstructible |
| Analytics | snapshots budget/contrats/sinistres/fournisseurs | mutation de la base noyau |
| Tableur | 5 vues metier + reimport controle | reimport implicite ou perte d'identifiants |
| Sync | 2 machines, offline/online, conflits, suppressions | perte silencieuse |
| Autorisations | 5 roles, 20 ressources, 20 actions | refus/autorisation impossible a expliquer |
| Packaging | Windows propre sans environnement dev | installation instable ou alerte antivirus non maitrisee |

## Decisions provisoires

- FTS5 est le candidat noyau le plus defensable pour la recherche locale.
- PDF.js est une bonne piste de lecteur, mais les annotations doivent rester CoproScope.
- Tesseract/OCRmyPDF forment le premier banc d'essai OCR; RapidOCR reste comparatif.
- DuckDB est excellent pour les audits, mais comme plugin analytics sur snapshots.
- Grist sert d'export/interface, pas de registre officiel.
- Syncthing, Nextcloud, Drive, OneDrive et Dropbox sont des transports de dossier.
- Casbin devient pertinent quand les roles et decisions d'acces depassent un modele simple.
- Le packaging desktop sera tranche apres un prototype vertical: coffre, PDF, recherche, OCR, indicateurs.

## Sources principales

- PDF.js: <https://github.com/mozilla/pdf.js>
- Hypothesis client: <https://github.com/hypothesis/client>
- Recogito Studio: <https://github.com/recogito/recogito-studio>
- Tesseract: <https://tesseract-ocr.github.io/tessdoc/Installation.html>
- OCRmyPDF: <https://github.com/ocrmypdf/OCRmyPDF/blob/main/LICENSE>
- PyMuPDF: <https://pymupdf.io/pymupdf>
- RapidOCR: <https://github.com/RapidAI/RapidOCR>
- SQLite FTS5: <https://www.sqlite.org/fts5.html>
- SQLite public domain: <https://www.sqlite.org/copyright.html>
- DuckDB: <https://duckdb.org/faq>
- Grist self-managed: <https://support.getgrist.com/self-managed/>
- Syncthing: <https://github.com/syncthing/syncthing>
- Nextcloud Desktop: <https://github.com/nextcloud/desktop>
- Google Drive Desktop: <https://support.google.com/drive/answer/10838124>
- OneDrive: <https://support.microsoft.com/en-us/office/sync-files-with-onedrive-in-windows-615391c4-2bd3-4aae-a42a-858262e42a49>
- Dropbox Desktop: <https://help.dropbox.com/installs/download-dropbox>
- Apache Casbin: <https://github.com/apache/casbin>
- PyInstaller: <https://pyinstaller.org/en/stable/license.html>
- Briefcase: <https://github.com/beeware/briefcase>
- Tauri: <https://github.com/tauri-apps/tauri>
