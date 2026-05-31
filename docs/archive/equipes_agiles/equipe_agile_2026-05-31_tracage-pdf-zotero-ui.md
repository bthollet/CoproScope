# Equipe agile - Tracage PDF UI

Date: 2026-05-31
Roadmap: `RM-2026-0045`
Ordre: `ORD-P1-043`
Chantier: `CH-20260531-015700-RM-2026-0045-pdf-trace-ui`
Conversation: `CONV-2026-1915`

Statut courant: iteration UI en cadrage. Aucun dev UI ne demarre avant visuel
IA bitmap, blueprint UI, qualification novice et commande dev stabilisee.

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

- bouton novice `Tracer une preuve dans ce PDF`;
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

- bouton principal `Tracer une preuve dans ce PDF`;
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
