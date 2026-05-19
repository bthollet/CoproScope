# Outillage open source

Ce journal documente les outils retenus pour CoproScope. Il est public et generique: aucune donnee d'instance privee, aucun secret et aucun chemin prive ne doit y etre ajoute.

## Installe ou verifie

| Outil | Version verifiee | Source | Licence | Objet CoproScope | Statut | Vigilance |
|---|---:|---|---|---|---|---|
| Python | 3.14.5 | python.org / winget `Python.Python.3.14` | PSF | Runtime systeme stable, hors venv existants | installe | garder les venv projet isoles |
| GitHub CLI | 2.92.0 | winget `GitHub.cli` | MIT | publication PR brouillon | installe | authentification requise |
| Git | 2.54.0 | winget `Git.Git` | GPLv2 | operations Git locales | installe | ne pas pousser de donnees privees |
| uv | 0.11.14 | winget `astral-sh.uv` | MIT/Apache | environnements Python rapides | installe | PATH a recharger apres winget |
| ripgrep | 15.1.0 | winget | MIT/Unlicense | recherche rapide | installe | aucun |
| fd | 10.4.2 | winget | MIT/Apache | recherche de fichiers | installe | aucun |
| jq | 1.8.1 | winget | MIT | inspection JSON | installe | aucun |
| DuckDB CLI | 1.5.2 | winget | MIT | analyses locales et exports | installe | fichiers DuckDB prives hors Git |
| QPDF | 12.3.2 | winget | Apache-2.0 | outils PDF | installe | PATH utilisateur complete |
| Poppler | 25.07.0 | winget | GPL/utilitaires | `pdftotext`, PDF tabulaires | installe | sorties OCR privees hors Git |
| Tesseract | 5.4.0 | winget | Apache-2.0 | OCR local | installe | qualite a tracer |
| ImageMagick | 7.1.2-23 | winget | ImageMagick License | conversion images/PDF | installe | prudence sur fichiers non fiables |
| Node LTS | 24.15.0 | winget | MIT | Evidence et outils JS | installe | utiliser `npm.cmd` sous PowerShell |
| Evidence | 40.1.8 | npm `@evidence-dev/evidence` | MIT | rapports SQL/Markdown | installe | `evidence.cmd`, pas shim `.ps1` |
| Grist Desktop | 0.3.10 | winget `GristLabs.GristDesktop` | Apache-2.0 cote grist-core | cockpit tableur local | installe | rester local par defaut |
| grist-api | 0.1.1 | PyPI / Grist Labs | Apache-2.0 | client API Grist Python | installe | cle API via env prive uniquement |

## Python dans le venv CoproScope

Modules presents: `duckdb`, `pandas`, `openpyxl`, `pypdf`, `PyMuPDF`, `pdfplumber`, `factur-x`, `rapidocr`, `grist_api`.

`docling` reste optionnel et reporte: l'installation a depasse la fenetre de 15 minutes. Le code conserve `docling` comme backend optionnel, jamais comme dependance obligatoire.

## Grist CLI

`grist-ctl` etait explicitement demande, mais le telechargement de l'archive de release a declenche Bitdefender. L'archive a ete supprimee et aucun binaire n'a ete lance.

Decision de securite:

- ne pas contourner l'antivirus ;
- consigner `grist-ctl` comme bloque securite ;
- utiliser `grist_api` et les exports CSV locaux comme chemin Grist v1 ;
- ne reessayer `grist-ctl` qu'apres validation manuelle de l'artefact.

## Outils exclus ou references seulement

- Odoo/OCA: reference Factur-X et comptable, pas socle CoproScope.
- Diacamma: reference metier copro, pas dependance produit.
- invoice2data: inspiration templates, pas moteur principal.
- Paperless-ngx, Superset, Metabase: trop lourds pour la v1 locale.
