# Equipe agile - Tracage PDF UI

Date: 2026-05-31
Roadmap: `RM-2026-0045`
Ordre: `ORD-P1-043`
Chantier: `CH-20260531-015700-RM-2026-0045-pdf-trace-ui`
Conversation: `CONV-2026-1915`

Statut courant: `PRET_A_INTEGRER` pour l'UI V1 corrigee. Le visuel IA bitmap,
le blueprint UI, la qualification novice avant dev et la commande dev ont ete
produits. Le premier dev prudent a recu un NO-GO novice, puis la correction a
ete reprise et verifiee. La feature globale reste active pour le vrai pointage
et l'enregistrement interactif d'une trace.

Rectification Brice du 2026-05-31 02:14: la doctrine d'equipe agile etait deja
claire et doit etre suivie. La correction documentaire porte seulement sur le
cas pratique d'indisponibilite d'un outil de sous-agents: cela ne vaut pas
waiver, les roles doivent etre joues sequentiellement et traces.

## Routage equipe

ROUTAGE_EQUIPE

Preflight: reprise de l'objectif actif PDF/Zotero. Les changements Compta
visibles dans le worktree restent hors perimetre et ne doivent pas etre touches.

Equipe-type: `AGILE_UI_PRODUIT`.

Raison: la prochaine tranche concerne une route et une interaction utilisateur:
fiche document -> tracer une preuve dans un PDF.

UI cible reelle:

```text
/documents/{doc_id}
```

Owner code unique apres GO novice:

- `server/src/coproscope/web/_document_viewer_parts/01_detail_sections.py`
- `server/src/coproscope/web/templates/document_detail.html`
- `server/tests/test_ui_document_viewer.py`

Fichiers evites:

- fichiers ComptaScope modifies par `CONV-2026-1914`;
- instances privees;
- documents bruts;
- OCR/logs;
- exports bruts;
- secrets;
- serveurs non reserves;
- scans/kills;
- push GitHub.

## Commande produit attendue

Ajouter dans la fiche document un atelier de trace PDF qui reste prudent:

- action novice `Preparer une trace dans ce PDF`;
- avertissement visible: `Cette version ne selectionne pas encore une zone dans le PDF.`;
- message visible `Le PDF original n'est pas modifie`;
- statut `Preuve candidate a verifier`;
- explication: CoproScope garde un repere dans le PDF, mais ne valide pas la
  preuve;
- etat scan/zone: `Texte non confirme : seule la zone encadree est gardee`;
- etat hash different: `Le fichier a change depuis la trace. Verifiez avant
  usage`;
- pas d'affichage brut du payload technique `zotero_position`, `rects`,
  `source_engine`.

## Gates avant dev

- visuel IA bitmap de l'ecran complet attendu;
- blueprint UI separe;
- qualification novice GO/NO-GO;
- commande dev stabilisee avec donnees fictives et tests attendus;
- aucun chemin local, document brut, email, telephone ou extrait sensible dans
  l'UI ou les traces.

## Visuel IA cible

Chemin retenu:

`docs/assets/pdf-trace-ui-2026-05-31/pdf-trace-document-detail-target.png`

Mode: image bitmap generee, ecran complet, utilisee comme intention UI amont.

Verdict designer/facilitateur: GO comme direction UI pour `/documents/{doc_id}`.

Reserves designer avant dev:

- ajouter explicitement les etats `Texte non confirme` et `Fichier change
  depuis la trace`;
- ne pas afficher les champs techniques `zotero_position`, `rects` ou
  `source_engine`;
- ne pas copier une interface externe: reprendre seulement les principes utiles.

## Blueprint UI

Premier viewport:

- haut: nom du document, badges simples, statut de diffusion;
- gauche: apercu PDF ou texte autorise;
- droite: panneau `Tracer une preuve`;
- bas visible: annotations et historique.

Panneau `Tracer une preuve`:

- action principale prudente `Preparer une trace dans ce PDF`;
- limite visible `Cette version ne selectionne pas encore une zone dans le PDF.`;
- statut `Preuve candidate a verifier`;
- garantie `Le PDF original n'est pas modifie`;
- garantie `CoproScope garde un repere dans le PDF, mais ne valide pas la
  preuve`;
- statut texte `Texte reconnu automatiquement : relisez avant de vous en
  servir`;
- statut scan `Texte non confirme : seule la zone encadree est gardee`;
- statut hash `Le fichier a change depuis la trace. Verifiez avant usage`;
- statut diffusion `Non diffusable par defaut`.

Commande dev candidate apres GO novice:

- fournir ces donnees dans le viewmodel document;
- afficher l'atelier dans `document_detail.html`;
- ne pas brancher de lecteur PDF interactif complet dans cette tranche;
- ne pas enregistrer de trace reelle encore;
- verrouiller par tests: libelles de prudence, absence de champs techniques,
  absence de chemin local, etats hash/texte/diffusion.

## Retours agents de l'iteration

Designer/facilitateur: GO sur le visuel IA cible et le blueprint, avec reserve
de ne pas afficher les champs techniques et de garder les libelles prudents.

Utilisateur novice avant dev: GO pour une commande bornee si les libelles
restent simples et si l'UI ne montre pas les champs internes.

QA privacy/regression apres premier dev: GO UI V1 seul pour les libelles
prudence et l'absence de fuite technique visible. Reserve: cette note devait
etre mise a jour car elle etait restee au statut cadrage.

Utilisateur novice apres premier dev: NO-GO UI. Le premier viewport restait
trop proche de l'ancienne fiche document: pas de lecteur PDF lisible, pas de
panneau lateral stable de tracage, pas de zones `Annotations` / `Historique`
en bas de l'atelier, et trop d'elements techniques visibles trop haut.

Commande corrective: restructurer `/documents/{doc_id}` en trois zones
visibles des l'arrivee: apercu/lecteur PDF, panneau `Tracer une preuve`, puis
`Annotations` / `Historique`; repousser les informations techniques plus bas et
renforcer les tests sur l'ordre visuel.

## Correction UI livree pour revue

Changements:

- `Lecteur PDF`, `Apercu PDF textuel` ou `Apercu autorise` passent en premier
  bloc apres l'en-tete selon le document;
- le panneau `Tracer une preuve` explique que la selection de zone n'est pas
  encore active et parle de `Preparer une trace dans ce PDF`;
- les resumes `Annotations` / `Historique` sont visibles dans le panneau de
  trace, avec sections detaillees juste apres l'atelier;
- `Parcours novice`, `Metadonnees`, `Traitement local`, `OCR`, `Moteur OCR` et
  empreintes techniques sont repousses dans des details repliables;
- le titre long de document est tronque visuellement pour eviter le
  chevauchement;
- un `file_name` contenant un chemin local est reduit a son nom court avant
  affichage.

Preuves coordinateur:

- `.\.venv\Scripts\python.exe -m unittest tests.test_ui_document_viewer tests.test_code_line_limit -v`:
  9 OK;
- `.\.venv\Scripts\python.exe -m unittest tests.test_ui_document_viewer tests.test_pdftraceops tests.test_annotationops tests.test_ui_smoke_routes_expanded tests.test_code_line_limit -v`:
  33 OK;
- `.\.venv\Scripts\python.exe ..\tools\check_code_line_limit.py`: OK;
- `git diff --check` cible: OK.

Reserve: les tests synthetiques prouvent la structure de l'atelier et les
libelles prudents, pas encore un lecteur PDF interactif complet sur une piece
PDF reelle.
Le serveur `8799` garde l'ancien gabarit en memoire et ne sert plus de preuve
finale apres correction du libelle prudent; la preuve finale est donc le panier
de regression ci-dessus.

## Revue finale

QA privacy/regression: NO-GO initial puis GO apres correction. Points corriges:
libelle unique `Preparer une trace dans ce PDF`, test rouge aligne, affichage
du nom de fichier durci pour ne jamais rendre `C:\...`, `/home/...` ou `raw/`.
Points verifies: pas de `zotero_position`, `rects`, `source_engine`, chemins
locaux ou chemins `raw/`; libelles prudents presents; infos techniques
repoussees; fichiers sous 600 lignes.

Novice final: le lancement d'un nouveau sous-agent a echoue par limite de
threads. Role joue sequentiellement par le coordinateur, selon la regle
documentee: GO UI V1 corrigee. Les deux blocages du NO-GO precedent sont leves:
`Cette version ne selectionne pas encore une zone dans le PDF.`,
`Le PDF original n'est pas modifie.` et `Texte non confirme : seule la zone
encadree est gardee.` sont maintenant visibles dans le premier ecran.

Verdict: UI V1 prete a integrer, sans promettre encore un lecteur PDF final
interactif ni l'enregistrement reel d'une trace.
