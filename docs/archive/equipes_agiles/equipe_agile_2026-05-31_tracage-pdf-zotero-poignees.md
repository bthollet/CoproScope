# Equipe agile - tracage PDF/Zotero - poignees de selection

Date: 2026-05-31.
Rattachement: `RM-2026-0045` / `ORD-P1-043`.
Chantier: `CH-20260531-045900-RM-2026-0045-pdf-trace-poignees`.
Conversation: `CONV-2026-1935`.
Equipe-type: `AGILE_UI_PRODUIT`.
Route cible: `/documents/{doc_id}`.
Visuel IA cible: `docs/assets/pdf-trace-ui-2026-05-31/pdf-trace-resize-handles-target.png`.

## Probleme utilisateur

Le rectangle de trace PDF peut etre dessine, mais il reste difficile a ajuster.
Si l'utilisateur rate legerement le passage, il doit redessiner. Pour un
pointage utilisable comme preuve candidate, le geste doit permettre de corriger
la zone avant enregistrement.

## Perimetre

- afficher des poignees visibles autour de la zone selectionnee;
- permettre d'ajuster la zone en tirant les coins et les cotes;
- garder les champs serveur existants `page`, `zone_x`, `zone_y`,
  `zone_width`, `zone_height`;
- conserver le bouton desactive tant qu'aucune zone valide n'existe;
- garder le changement de page qui efface la zone;
- ne pas modifier le PDF original.

Hors perimetre:

- lecteur PDF.js complet;
- zoom reel;
- rotation;
- selection texte native;
- extraction vision;
- export ou validation finale de preuve.

## Blueprint UI

La zone selectionnee affiche:

- un rectangle bleu ou vert selon l'etat;
- quatre poignees de coin;
- quatre poignees de cote;
- le statut novice `Zone ajustable` ou `Zone selectionnee`;
- une aide courte: `Tirer les poignees pour ajuster`.

Sur mobile/tactile, les poignees doivent rester assez grandes pour etre
utilisables. Si l'ajustement par poignee n'est pas possible, le drag de dessin
reste disponible.

## Parcours-evenements

1. L'utilisateur ouvre un PDF.
2. Il dessine une zone.
3. CoproScope affiche la zone et ses poignees.
4. L'utilisateur tire une poignee pour agrandir, reduire ou deplacer un bord.
5. Les champs caches sont recalcules.
6. L'utilisateur enregistre la trace candidate.

Evenements limites:

- zone trop petite: bouton desactive et statut de selection a refaire;
- sortie de page: la zone reste bornee a la page;
- changement de page: zone effacee;
- touche `Escape`: zone effacee.

## Contrat de donnees

Inchange cote serveur:

- `page`;
- `zone_x`;
- `zone_y`;
- `zone_width`;
- `zone_height`.

Contrat front:

- le rectangle affiche correspond toujours aux champs caches;
- les valeurs restent normalisees entre 0 et 1;
- largeur et hauteur restent au-dessus du minimum serveur;
- aucune donnee technique n'est ajoutee au HTML public.

## Risques privacy/licence

- Cette iteration n'importe pas de code Zotero; elle s'inspire seulement du
  geste d'annotation ajustable.
- Aucun chemin local, hash, OCR brut ou champ technique ne doit devenir visible.
- L'ajustement de zone ne valide pas la preuve: la trace reste candidate.

## Criteres d'acceptation

- Une zone dessinee affiche des poignees visibles.
- Tirer une poignee met a jour la zone et les champs caches.
- Les poignees ne permettent pas une zone hors page.
- Une zone trop petite ne peut pas etre enregistree.
- Changer de page efface la zone et le bouton redevient desactive.
- Aucun jargon technique n'apparait dans l'UI.
- Tests JS/HTML et panier regression PDF passent.

## Tests attendus

- assertions statiques sur la presence des poignees dans le HTML;
- assertions JS sur les attributs de poignees, la logique de redimensionnement
  et l'absence de champs techniques;
- tests de non-regression document viewer / multipage;
- panier PDF/UI/annotations/ComptaScope;
- garde-fou 600 lignes;
- `git diff --check`.

## Gate avant dev

Dev bloque tant que les retours suivants ne sont pas rendus:

- designer/facilitateur: GO/NO-GO sur visuel et structure des poignees;
- utilisateur novice: GO/NO-GO sur comprehension du geste;
- QA privacy/regression: tests minimaux et risques anti-fuite;
- expert DocOps/preuve: invariants de trace candidate et non-mutation PDF.

Gate leve le 2026-05-31 05:11 +02:00:

- designer/facilitateur: GO pour huit poignees visibles autour de la zone;
- utilisateur novice: GO si le libelle reste `Zone ajustable` avec aide courte;
- QA privacy/regression: GO, aucun champ technique ni chemin local visible;
- expert DocOps/preuve: GO, la trace reste candidate et le PDF source n'est pas
  modifie.

Points imposes par les roles et repris dans le dev:

- ne pas garder la petite poignee decorative unique;
- ne pas cacher les poignees uniquement au survol;
- ne pas afficher un extrait repere avec un message contradictoire
  `Texte non confirme`;
- garder la preuve au statut de trace a verifier;
- ne pas afficher `source_engine`, `zotero_position`, `rects`,
  `selected_text_hash`, chemin local, OCR brut, token ou secret.

## BOT-END

Statut: `PRET_A_INTEGRER`.

Livraison: la zone PDF affiche huit poignees de redimensionnement. Les coins et
les cotes recalculent les champs caches bornes a la page, gardent le bouton
desactive si la zone est trop petite, et conservent le changement de page qui
efface la selection.

Preuves:

- tests cibles `tests.test_ui_document_viewer_trace_handles`
  `tests.test_ui_document_viewer` `tests.test_ui_document_viewer_multipage`:
  20 OK;
- panier PDF/UI/annotations/ComptaScope/smoke/line-limit: 63 OK;
- `tools/check_code_line_limit.py`: OK;
- `git diff --check`: OK.

Limite: pas de serveur local ni executable relance dans ce passage, pour ne pas
ajouter de processus pendant l'etat CPU/RAM RECOVER. Le banc navigateur local a
ete refuse par l'outil de navigateur et n'a pas ete contourne. Une recette
visuelle sur `/documents/{doc_id}` reste a reprendre avant validation produit
finale.
