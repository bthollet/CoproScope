# Equipe agile - tracage PDF/Zotero - extrait visible

Date: 2026-05-31.
Rattachement: `RM-2026-0045` / `ORD-P1-043`.
Chantier: `CH-20260531-044800-RM-2026-0045-pdf-trace-extrait-visible`.
Conversation: `CONV-2026-1931`.
Equipe-type: `AGILE_UI_PRODUIT`.
Route cible: `/documents/{doc_id}`.
Visuel IA cible: `docs/assets/pdf-trace-ui-2026-05-31/pdf-trace-text-excerpt-target.png`.

## Probleme utilisateur

La zone PDF peut maintenant recuperer un texte candidat quand le PDF contient
du texte. Mais ce texte reste peu visible dans la fiche document: la trace
affiche surtout la zone, le statut et le commentaire. Pour un membre de conseil
syndical non technique, la valeur attendue est de revoir rapidement le passage
repere sans croire que CoproScope a valide la preuve.

## Perimetre

- afficher l'extrait court filtre deja produit par le registre PDF;
- garder le vocabulaire prudent: texte repere, a relire, preuve non validee;
- separer l'information reperee, le commentaire humain, la zone et le statut;
- ne pas afficher de champ technique Zotero/PyMuPDF/interne;
- ne pas changer le PDF original;
- ne pas valider automatiquement la preuve.

Hors perimetre:

- lecteur PDF.js complet;
- poignees de redimensionnement;
- extraction vision depuis image ou scan;
- reprise directe de code Zotero;
- export public ou partage de preuve.

## Blueprint UI

La fiche document garde trois zones:

1. lecteur/apercu PDF a gauche avec rectangle de selection;
2. panneau de droite `Tracer une preuve candidate` avec statut prudent;
3. tableau bas `Traces candidates enregistrees`.

Changement demande dans cette iteration:

- dans le panneau de droite, si une trace existe, afficher sous le statut:
  `Texte repere automatiquement, a relire` puis l'extrait court;
- dans le tableau des traces, ajouter une information lisible `Extrait repere`
  dans la colonne statut ou dans une colonne dediee si le template le permet
  sans refonte large;
- afficher le commentaire humain separement de l'extrait;
- fallback sans extrait: conserver `Texte non confirme : seule la zone encadree
  est gardee.`;
- contenu sensible masque: afficher seulement le message de masquage, jamais le
  texte brut ni le hash direct du texte.

## Parcours-evenements

1. L'utilisateur ouvre un PDF.
2. Il choisit une page et encadre une zone.
3. CoproScope enregistre une trace candidate sidecar.
4. Si le PDF texte le permet, CoproScope rattache un extrait court filtre.
5. L'utilisateur voit la trace dans la fiche document.
6. L'utilisateur relit le passage: il comprend que c'est une aide de reperage,
   pas une preuve validee.

Evenements limites:

- extraction impossible: zone conservee, texte non confirme;
- document modifie depuis la trace: texte a verifier;
- contenu sensible: extrait masque;
- commentaire absent: ne pas inventer une validation.

## Contrat de donnees

Entree UI existante:

- `document_detail.pdf_trace.saved_traces[]`
- champs publics par trace: `status`, `created_at`, `zone`, `anchor`,
  `diffusion`, `text`, `excerpt`, `comment`.

Interdit en UI:

- `source_engine`;
- `zotero_position`;
- `rects`;
- chemins locaux;
- OCR brut;
- emails, tokens, secrets;
- hash direct du texte sensible.

## Risques privacy/licence

- L'extrait peut contenir une donnee personnelle: le registre doit deja le
  masquer et l'UI ne doit pas contourner ce masque.
- L'ancre inspiree Zotero reste un sidecar CoproScope: pas de mutation PDF, pas
  de promesse de compatibilite totale avec Zotero.
- Licence: CoproScope AGPL et briques Zotero AGPL compatibles seulement avec
  notices/source/modifications tracees; cette iteration n'importe pas de code
  Zotero.

## Criteres d'acceptation

- Une trace PDF avec extrait affiche cet extrait sur la fiche document.
- Une trace sans extrait garde un message prudent et comprehensible.
- Une trace sensible n'affiche pas le texte sensible.
- Une trace dont le document a change affiche une reserve de verification.
- Aucun champ technique n'est visible dans le HTML.
- Les tests cibles passent et le garde-fou 600 lignes reste vert.

## Tests attendus

- test UI dedie sur `/documents/{doc_id}` avec extrait visible;
- test UI dedie sur extrait sensible masque;
- panier regression PDF/document viewer/annotations/ComptaScope;
- `tools/check_code_line_limit.py`;
- `git diff --check`.

## Gate avant dev

Dev bloque tant que les retours suivants ne sont pas rendus:

- designer/facilitateur: GO/NO-GO sur visuel et blueprint;
- utilisateur novice: GO/NO-GO vocabulaire et comprehension;
- QA privacy/regression: risques anti-fuite et tests minimaux;
- expert DocOps/preuve: invariants preuve candidate / non-mutation PDF.

## Retours roles

Designer/facilitateur: GO conditionnel.

- Le visuel IA est adapte comme cible d'intention.
- Ecart accepte: UI actuelle moins riche que le visuel, si l'extrait reste
  lisible sans refonte large.
- Ecart refuse: cacher l'extrait dans le commentaire humain ou melanger extrait
  et preuve validee.
- Structure demandee: panneau droit enrichi avec statut prudent, texte repere
  et extrait; tableau avec information `Extrait repere` separee.

Utilisateur novice: GO conditionnel.

- Comprend que CoproScope garde une zone et montre un court extrait pour relire.
- Demande des mots simples: `Trace a verifier`, `Extrait repere`, `Non valide`,
  `Le PDF original n'est pas modifie`.
- Risque signale: `preuve candidate` et `trace candidate` restent techniques.
- Condition: separer extrait automatique et commentaire humain.

Expert DocOps/preuve: GO conditionnel.

- Utiliser seulement `trace.excerpt`, deja prepare par le resume public.
- L'extrait est une aide de relecture, jamais une preuve validee.
- Si le document a change, afficher une reserve de verification.
- Si le contenu est sensible, afficher seulement le message de masquage.
- No-go: champs internes, chemins locaux, hash direct, OCR brut ou promesse de
  validation juridique/comptable.

QA privacy/regression: GO dev, NO-GO `PRET_A_INTEGRER` avant patch et tests.

- Risque principal: fuite de texte sensible au lieu du message masque.
- Tests exiges: cas extrait normal, sensible masque, document modifie, champs
  techniques absents.
- Panier regression exige: PDF registry, UI document viewer, multipage,
  pdftraceops, annotationops, ComptaScope, smokes UI et line-limit.

## Commande dev retenue

Modifier uniquement `document_detail.html` pour afficher l'extrait public:

- panneau droit: premiere trace avec statut prudent, texte repere, extrait si
  present, zone et diffusion;
- tableau: colonne `Extrait repere`, avec commentaire humain separe;
- fallback sans extrait: ne pas inventer de contenu;
- ne jamais afficher de champ interne.

Ajouter un test UI dedie, sans allonger `test_ui_document_viewer.py` deja proche
de la limite.

## Livraison

Statut: `PRET_A_INTEGRER`.

Fichiers modifies pour cette iteration:

- `server/src/coproscope/web/templates/document_detail.html`;
- `server/tests/test_ui_document_viewer_trace_excerpt.py`;
- ce document;
- `docs/presence_agents.md`;
- `docs/roadmap_backlog_central.md`;
- `docs/assets/pdf-trace-ui-2026-05-31/pdf-trace-text-excerpt-target.png`.

Preuves:

- `python -m unittest tests.test_ui_document_viewer_trace_excerpt -v`: 3 OK;
- panier QA:
  `tests.test_pdftrace_registry_text_recovery tests.test_ui_document_viewer_trace_excerpt tests.test_ui_document_viewer tests.test_ui_document_viewer_multipage tests.test_pdftraceops tests.test_annotationops tests.test_ui_comptes_rapprochement tests.test_ui_smoke_routes_expanded tests.test_code_line_limit -v`: 60 OK;
- `python ..\tools\check_code_line_limit.py`: OK;
- `git diff --check`: OK.

Limites:

- `RECETTE_PAGE_REELLE_WAIVED`: aucun serveur local n'a ete ouvert dans ce
  passage, pour eviter une recette live ambigue depuis un worktree contenant
  aussi des changements ComptaScope non lies. La verification live PDF reste a
  reprendre sur une instance synthetique propre avant validation produit finale.
- Le lecteur PDF.js complet, les poignees et l'extraction vision restent hors
  lot.
