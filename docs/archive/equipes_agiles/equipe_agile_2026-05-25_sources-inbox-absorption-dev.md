# Equipe agile - Sources inbox absorption

Rattachement: `RM-2026-0003` / `RM-2026-0029` / `ORD-P0-001`.
Chantier: `CH-20260525-233914-RM-2026-0003-sources-inbox-absorption`.
Conversation corrigee: `CONV-2026-1783`.

## BOT-START - Owner sources inbox absorption - 2026-05-25 23:39 +02:00

Mission: transformer `/documents/ajouter` en hub local de depots et sources,
avec validation humaine avant type, confidentialite, rattachement ou diffusion.

Note de coordination: le demarrage automatique a laisse une trace append-only
avec `CONV-2026-1782`, deja utilise par le lot `Messages entrants`. La cloture
et les preuves de ce lot sont donc portees par `CONV-2026-1783`.

Ownership modifiable:

- `server/src/coproscope/web/document_intake_view.py`
- `server/src/coproscope/web/document_intake_sources.py`
- `server/src/coproscope/web/document_intake_route.py`
- `server/src/coproscope/web/templates/document_intake.html`
- `server/src/coproscope/web/static/styles.css`
- `server/src/coproscope/web/static/styles_part_13.css`
- `server/tests/test_ui_document_intake.py`
- `server/tests/test_ui_document_intake_route.py`
- tests security/no-private cibles
- registres de presence et gouvernail

Fichiers evites: instances privees, documents bruts, OCR/logs, exports bruts,
secrets, connecteurs OAuth/IMAP reels, publication automatique, serveur live,
`RM-2026-0017` et `ORD-P0-990`.

## BOT-END - Owner sources inbox absorption - 2026-05-25 23:47 +02:00

Statut: `INTEGRE`.

Livraison:

- `/documents/ajouter` ouvre par defaut le glisser-deposer local;
- le filtre `source=all` reste explicite pour toutes les sources;
- le hub affiche inbox locale, dossier local, Drive Desktop local et mailbox
  future sans activer de connecteur;
- le retour upload `/depot` revient vers `/documents/ajouter`;
- qualification type/confidentialite et rattachement piece -> point -> action
  -> preuve sont enregistrables localement;
- noms de fichiers, chemins prives et marqueurs bruts restent masques.

Tests/preuves:

```powershell
.\.venv\Scripts\python.exe -B -m unittest tests.test_ui_document_intake tests.test_ui_document_intake_route tests.test_ui_security_routes tests.test_security_no_private_sync_leaks -v
.\server\.venv\Scripts\python.exe .\tools\check_code_line_limit.py
git diff --check -- <perimetre sources inbox>
```

Resultat: document-intake/security/no-private `24 OK`, line-limit OK,
diff-check OK avec warning CRLF preexistant sur `styles.css`. Le test upload
affiche un avertissement parseur PDF `EOF marker not found` sur un mini-PDF
synthetique volontairement minimal, mais le test passe.

Limites: pas de GO navigateur desktop/mobile; aucune source externe reelle,
OAuth, IMAP, cloud ou publication automatique n'est activee.

AGILE-DONE - equipe agile a fini son job.
