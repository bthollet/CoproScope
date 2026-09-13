# Equipe agile - Tracage PDF sauvegarde candidate

Date: 2026-05-31
Roadmap: `RM-2026-0045`
Ordre: `ORD-P1-043`
Chantier: `CH-20260531-023500-RM-2026-0045-pdf-trace-save`
Conversation: `CONV-2026-1918`

Statut courant: `PRET_A_INTEGRER` - sauvegarde sidecar courte livree et testee.

Rectification Brice: la doctrine d'equipe agile est claire et obligatoire. La
seule clarification utile est le cas d'outil de sous-agents indisponible: cela
ne vaut pas waiver; les memes roles sont alors joues sequentiellement et traces.

## Routage equipe

ROUTAGE_EQUIPE

Equipe-type: `AGILE_UI_PRODUIT`.

Raison: la tranche ajoute une action utilisateur sur `/documents/{doc_id}`:
enregistrer une trace candidate visible dans la fiche document, sans modifier
le PDF.

Preflight:

- backend V1 et UI V1 precedents: `PRET_A_INTEGRER` pour leurs perimetres;
- feature globale `RM-2026-0045`: toujours `ACTIF`;
- changements ComptaScope `CONV-2026-1914` / `CONV-2026-1916`: hors perimetre;
- instances privees, documents bruts, OCR/logs, secrets et exports bruts:
  evites;
- serveur live: aucun nouveau port reserve tant que le dev n'est pas pret a
  tester.

UI cible reelle:

```text
/documents/{doc_id}
POST /documents/{doc_id}/traces
```

Owner code unique apres GO equipe:

- `server/src/coproscope/modules/pdftrace_registry.py`
- `server/src/coproscope/web/_document_viewer_parts/01_detail_sections.py`
- `server/src/coproscope/web/templates/document_detail.html`
- `server/src/coproscope/web/_app_fragments/part_003.pyfrag`
- `server/tests/test_ui_document_viewer.py`

Fichiers evites:

- fichiers ComptaScope modifies par les lots comptes;
- instances privees;
- documents bruts;
- OCR/logs;
- exports bruts;
- secrets;
- serveurs non reserves;
- scans/kills;
- push GitHub.

## Visuel IA cible

Chemin retenu:

`docs/assets/pdf-trace-ui-2026-05-31/pdf-trace-save-target.png`

Intentions visibles:

- bouton principal `Enregistrer la trace candidate`;
- garantie `Le PDF original n'est pas modifie`;
- statut `Texte non confirme : seule la zone encadree est gardee`;
- statut `Non diffusable par defaut`;
- encart apres action `Trace candidate enregistree`;
- tableau de traces candidates en bas de page.

## Blueprint UI

Premier viewport:

- gauche: lecteur/apercu PDF ou texte autorise;
- droite: panneau `Tracer une preuve`;
- action principale: enregistrer une trace candidate;
- garde-fous visibles sous l'action;
- si une trace existe, bloc de confirmation et resume lisible.

Zone basse:

- liste `Traces candidates enregistrees`;
- colonnes lisibles: date, ancre courte, page, statut, note;
- pas d'affichage brut de `zotero_position`, `rects`, `source_engine`, chemin
  local, OCR brut ou extrait sensible long.

## Parcours-evenements

1. Un membre CS ouvre la fiche document.
2. Il selectionne ou confirme une zone de preuve.
3. Il clique `Enregistrer la trace candidate`.
4. CoproScope calcule une ancre et ecrit un registre sidecar local.
5. Le PDF original reste inchange.
6. La fiche document affiche une confirmation et la trace enregistree.
7. La trace reste candidate, non diffusable par defaut, jusqu'a validation
   humaine future.

Hors perimetre de cette tranche:

- vrai dessin a la souris dans un lecteur PDF complet;
- copie de code lecteur Zotero;
- validation juridique ou comptable de la preuve;
- diffusion aux coproprietaires;
- modification du PDF source.

## Contrat de donnees

Entree formulaire:

- `page`;
- `zone_x`, `zone_y`, `zone_width`, `zone_height` en coordonnees normalisees;
- `comment` court, optionnel, sans chemin local ni donnee personnelle inutile.

Donnees calculees:

- `trace_id`;
- `document_ref`;
- `document_hash`;
- `anchor_hash`;
- `fragment_ref`;
- `page`;
- `proof_status = preuve_candidate`;
- `text_status = non_confirme` si la zone seule est enregistree;
- `diffusion = non_diffusable`;
- `write_policy = source_pdf_is_never_modified`.

Stockage:

- registre sidecar dans l'instance de test, pas dans le PDF;
- aucune ecriture dans le document source;
- resume public sans payload technique.

## Risques

Privacy: ne jamais exposer chemin local, nom de fichier brut sensible, OCR brut
ou commentaire contenant donnees personnelles inutiles.

Licence: CoproScope est `AGPL-3.0-only`; Zotero sert de reference
d'inspiration et de compatibilite de position, sans copie de code dans cette
tranche.

Qualite preuve: la trace est candidate. Elle dit ou regarder, mais ne remplace
pas la relecture humaine.

## Criteres d'acceptation

- un POST cree une trace candidate dans un registre sidecar;
- le PDF d'origine n'est pas modifie;
- la page rechargee affiche `Trace candidate enregistree`;
- l'UI affiche `Non diffusable par defaut`;
- l'UI n'affiche pas `zotero_position`, `rects` ou `source_engine`;
- une note contenant chemin local ou donnee privee evidente est refusee;
- tests UI et backend verts;
- recette live sur instance synthetique apres dev.

## Roles equipe avant dev

Designer/facilitateur attendu: verifier que le visuel cible et le blueprint
gardent une action claire, non spectaculaire et prudente.

Utilisateur novice attendu: dire s'il comprend que le bouton enregistre une
trace candidate, pas une preuve validee ni une modification du PDF.

QA privacy/regression attendu: verifier le contrat sidecar, la non-mutation du
PDF, le refus de donnees privees evidentes et l'absence de champs techniques
dans l'UI.

Expert DocOps/preuve attendu: verifier que le statut `preuve_candidate` et
`non_diffusable` restent coherents avec DocOps.

## Retours equipe avant dev

Designer/facilitateur: GO avant dev. Reserve de wording: remplacer le titre
`Tracer une preuve` par `Tracer une preuve candidate` ou
`Preparer une trace candidate`, et ne jamais afficher `Rect (...)` en UI.

Utilisateur novice: GO avant dev. Il comprend quoi cliquer, que la trace est
candidate, que le PDF original n'est pas modifie et que rien n'est diffuse par
defaut. Reserve identique: afficher `Zone encadree page 1`, pas les
coordonnees.

Expert DocOps/preuve: GO sous conditions. Ecriture uniquement sidecar, statut
`preuve_candidate`, diffusion `non_diffusable`, refus des notes avec chemin
prive, email, telephone ou donnee personnelle inutile, et pas de promesse de
preuve juridique validee.

QA privacy/regression: GO avant dev avec garde-fou strict. Le template ne doit
jamais utiliser directement `candidate_to_public_dict`, car ce dictionnaire
contient des champs techniques. L'UI doit passer par un resume filtre et une
liste blanche.

Decision equipe: GO dev pour une V2 courte de sauvegarde sidecar. Le GO
d'integration reste conditionne aux tests et a la recette reelle apres dev.

## Commande dev conditionnelle

Commande active apres retours GO:

- ajouter un petit registre sidecar de traces candidates;
- ajouter `POST /documents/{doc_id}/traces`;
- brancher le panneau de droite sur cette action;
- afficher les traces enregistrees dans la fiche document;
- couvrir par tests: creation, non-mutation PDF, anti-fuite, libelles novice.

## Livraison

BOT-END - coordinateur-scribe - 2026-05-31 02:55 +02:00

Statut: `PRET_A_INTEGRER`.

Livre:

- registre sidecar `registre_pdf_traces.csv` dans l'instance;
- route `POST /documents/{doc_id}/traces`;
- bouton `Enregistrer la trace candidate`;
- confirmation `Trace candidate enregistree`;
- resume filtre des traces candidates, sans payload technique;
- refus d'une note contenant chemin local ou marqueur prive.
- libelle novice `Zone encadree page 1` au lieu de coordonnees techniques.

Preuves:

- `tests.test_ui_document_viewer -v`: 10 OK;
- `tests.test_ui_document_viewer tests.test_pdftraceops tests.test_annotationops tests.test_ui_smoke_routes_expanded -v`:
  34 OK;
- `..\tools\check_code_line_limit.py`: OK;
- `git diff --check`: OK.

Recette live:

- `8797` sur `examples/synthetic_copro`: route vivante, mais aucun PDF dans
  cette instance;
- `8791`: port ambigu, refus du jeton attendu, non utilise;
- `8790` sur copie temporaire hors depot:
  `http://127.0.0.1:8790/documents/DOC-PDF-TRACE-LIVE?token=pdf-trace-save-temp-8790`;
- GET fiche PDF: 200;
- POST `/documents/DOC-PDF-TRACE-LIVE/traces`: 303;
- page rechargee: `Trace candidate enregistree`,
  `Non diffusable par defaut`, `Zone encadree page 1`,
  `Le PDF original n'est pas modifie.`;
- page rechargee: pas de `zotero_position`, `source_engine`, `rects`;
- registre temporaire: une ligne `preuve_candidate`, `non_confirme`,
  `non_diffusable`, `source_pdf_is_never_modified`.

In-app Browser: action refusee par politique interne sur cette page locale.
Pas de contournement par un autre navigateur; preuve visuelle limitee au HTTP
live et aux tests HTML.

Revue post-dev:

- novice: GO;
- QA privacy/regression: GO integration.

Reserves:

- `source_engine` reste dans le registre interne local; ne pas l'exporter tel
  quel en public;
- la route ne recalcule pas le hash du PDF au POST, donc ne pas presenter cette
  V2 comme verification forte du fichier;
- le vrai lecteur PDF interactif et le pointage souris/vision restent a livrer.
