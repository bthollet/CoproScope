# Equipe agile - Tracage PDF selection manuelle de zone

Date: 2026-05-31
Roadmap: `RM-2026-0045`
Ordre: `ORD-P1-043`
Chantier: `CH-20260531-030600-RM-2026-0045-pdf-trace-interactive-zone`
Conversation: `CONV-2026-1921`

Statut courant: pret a integrer.

## BOT-START

BOT-START - coordinateur-scribe - 2026-05-31 03:06 +02:00

Mission: livrer la prochaine tranche utile de la feature PDF/Zotero: permettre
a l'utilisateur de choisir lui-meme une zone de page dans la fiche document,
puis d'enregistrer cette zone comme trace candidate sidecar.

Ownership modifiable:

- `server/src/coproscope/web/templates/document_detail.html`
- `server/src/coproscope/web/_document_viewer_parts/01_detail_sections.py`
- `server/src/coproscope/web/static/pdf_trace_selection.js`
- `server/tests/test_ui_document_viewer.py`
- cette note, le visuel cible et les traces presence/roadmap.

Fichiers evites:

- fichiers ComptaScope et coque responsive modifies par `CONV-2026-1919`;
- instances privees;
- documents bruts;
- OCR/logs;
- exports bruts;
- secrets;
- serveur non reserve, scan/kill et push GitHub;
- copie de code Zotero.

Dernier point lu: `AGENTS.md`, `docs/consignes_bots_interconversations.md`,
`docs/protocole_roadmap_presence_agents.md`, `docs/strategie_equipes_multi_agents.md`,
`docs/protocole_equipe_agile_agents.md`, `docs/tableau_execution_courant.md`,
`docs/presence_agents.md`, `docs/roadmap_backlog_central.md`.

Risque de collision: changements Compta vivants sur CSS responsive et tests
associes; perimetre PDF disjoint.

Tests/preuves attendus: tests UI document, tests PDF trace, garde-fou 600
lignes, `git diff --check`, recette route reelle ou waiver trace.

## Routage equipe

ROUTAGE_EQUIPE

Preflight: reprise explicite de `RM-2026-0045`, deja actif et demande par
Brice. Ce n'est pas un nouveau dispatch libre depuis le backlog long.

Equipe-type: `AGILE_UI_PRODUIT`.

Orchestration: designer + novice + QA/privacy + expert DocOps/preuve avant
dev; owner code unique ensuite.

UI cible reelle:

```text
GET /documents/{doc_id}
POST /documents/{doc_id}/traces
```

Gates avant dev:

- visuel IA bitmap plein ecran;
- blueprint UI;
- qualification novice;
- GO QA privacy/regression;
- GO expert DocOps/preuve.

## Visuel IA cible

Chemin retenu:

`docs/assets/pdf-trace-ui-2026-05-31/pdf-trace-interactive-zone-target.png`

Intention:

- la fiche document montre un lecteur/apercu PDF;
- l'utilisateur dessine ou ajuste une zone rectangulaire sur la page;
- le panneau de droite affiche `Zone selectionnee page 1`;
- le bouton `Enregistrer comme trace candidate` reste l'action principale;
- les garde-fous `Le PDF original n'est pas modifie` et
  `Non diffusable par defaut` restent visibles;
- les traces deja enregistrees sont listees sans afficher de coordonnees
  techniques.

## Blueprint UI

Premier viewport:

- zone principale gauche: page PDF ou apercu autorise dans un cadre stable;
- couche de selection au-dessus de l'apercu, avec rectangle visible pendant et
  apres le geste;
- aide courte: `Dessinez une zone sur la page`;
- statut proche du lecteur: `Zone selectionnee page 1` apres selection;
- panneau droit: note courte, bouton d'enregistrement, garde-fous.

Interaction:

1. l'utilisateur presse dans l'apercu PDF;
2. il glisse pour dessiner un rectangle;
3. CoproScope convertit le rectangle en coordonnees normalisees entre 0 et 1;
4. les champs caches du formulaire sont mis a jour;
5. le bouton devient actif seulement quand une zone existe;
6. le POST existant enregistre la trace candidate dans le sidecar.

Etats:

- aucune zone: bouton desactive, texte `Zone a selectionner`;
- selection en cours: rectangle visible, pas d'enregistrement;
- zone valide: `Zone selectionnee page 1`, bouton actif;
- apercu non interactif: message clair, formulaire prudent ou desactive.

## Parcours-evenements

1. Un membre du conseil syndical ouvre un PDF.
2. Il identifie le passage utile.
3. Il encadre la zone sur la page.
4. CoproScope garde uniquement un repere de page et zone.
5. Il ajoute une note courte, sans donnee personnelle inutile.
6. Il enregistre la trace candidate.
7. Le PDF original reste inchange.
8. La trace reste `preuve_candidate`, `non_confirme` et `non_diffusable`.

## Contrat de donnees

Champs UI:

- `page`: entier positif, V1 limitee a page 1 dans l'apercu actuel;
- `zone_x`, `zone_y`, `zone_width`, `zone_height`: nombres normalises entre 0
  et 1, calcules depuis le rectangle visible;
- `comment`: note courte existante, filtree cote route.

Contraintes:

- largeur et hauteur minimales non nulles;
- valeurs bornees dans la page;
- aucun affichage public de `zotero_position`, `rects`, `source_engine` ou
  chemin local;
- pas de modification du PDF source;
- pas de validation automatique de la preuve.

## Criteres d'acceptation

- la page contient une zone de selection PDF identifiable et testable;
- dessiner une zone met a jour les champs caches du formulaire;
- le bouton d'enregistrement est desactive tant qu'aucune zone n'est choisie;
- la sauvegarde sidecar existante continue de fonctionner;
- l'UI garde les libelles prudents et lisibles;
- les champs techniques restent absents du HTML visible;
- les tests de regression PDF/UI restent verts;
- aucun fichier code suivi ne depasse 600 lignes.

## Retours equipe avant dev

Designer/facilitateur: GO avant dev, sous reserve de qualification novice. Il
demande une consigne courte `Dessinez une zone sur la page`, un statut
`Zone a selectionner`, un rectangle visible, puis `Zone selectionnee page 1`.
Le bouton doit rester desactive tant qu'aucune zone n'est choisie.

Utilisateur novice: GO avant dev. Il comprend qu'il doit encadrer un passage,
puis enregistrer une trace candidate. Reserve: eviter `Enregistree` seul, qui
peut faire croire a une preuve acceptee. Preferer `Candidate enregistree`,
`A verifier` et `Enregistrer comme trace candidate`.

Expert DocOps/preuve: GO dev, NO-GO integration tant que le backend accepte une
zone par defaut quand les coordonnees manquent. Il exige le refus d'une trace
sans zone fournie, largeur/hauteur nulle ou zone invalide.

QA privacy/regression: GO dev conditionnel, NO-GO integration tant que les
tests ne prouvent pas le bouton desactive avant selection, le refus serveur des
coordonnees absentes/invalides, l'absence de fuite technique et la non-mutation
du PDF.

Decision equipe: GO dev pour une tranche interactive bornee, avec durcissement
serveur obligatoire. Pas de copie de code Zotero.

## Commande dev

- Ajouter une couche de selection sur l'apercu PDF/texte/image de
  `/documents/{doc_id}`.
- Afficher `Zone a selectionner` au chargement et desactiver le bouton.
- Dessiner un rectangle visible pendant le glissement souris/tactile.
- Convertir le rectangle en valeurs normalisees `zone_x`, `zone_y`,
  `zone_width`, `zone_height` dans les champs caches existants.
- Activer le bouton seulement quand une zone valide est selectionnee.
- Renommer l'action visible en `Enregistrer comme trace candidate`.
- Durcir `pdftrace_registry.save_zone_trace`: aucune valeur par defaut si les
  coordonnees manquent, sont non numeriques, hors page ou trop petites.
- Tester rendu HTML, validation serveur, non-mutation PDF et anti-fuite.

## BOT-END

BOT-END - coordinateur-scribe - 2026-05-31 03:23 +02:00

Statut: `PRET_A_INTEGRER` pour la tranche selection manuelle de zone.

Resultat livre:

- l'atelier affiche `Zone a selectionner` au chargement;
- le bouton `Enregistrer comme trace candidate` est desactive tant qu'aucune zone
  n'est dessinee;
- le glissement souris/tactile dessine un rectangle visible et remplit les
  champs caches de zone;
- le serveur refuse une sauvegarde si la zone manque, est non numerique, sort
  de la page ou est trop petite;
- la trace reste candidate, non confirmee et non diffusable;
- le PDF original n'est pas modifie.

Preuves:

- `tests.test_ui_document_viewer -v`: 11 OK;
- `tests.test_pdftraceops tests.test_annotationops tests.test_ui_smoke_routes_expanded -v`:
  24 OK;
- `check_code_line_limit.py`: OK;
- `git diff --check`: OK;
- visuel cible publie dans
  `docs/assets/pdf-trace-ui-2026-05-31/pdf-trace-interactive-zone-target.png`;
- designer, novice, QA/privacy et expert DocOps fermes apres verdict.

Limite tracee:

- `RECETTE_PAGE_REELLE_WAIVED`: aucun nouveau serveur lance dans ce passage.
  La verification navigateur reelle devra etre reprise sur serveur reserve si
  l'on veut une preuve visuelle finale.
- prochaine tranche utile: lecteur PDF plus complet, selection multi-page ou
  avec poignees, recalcul hash au POST et extraction de l'information par
  vision si une lecture vision est mobilisee.
