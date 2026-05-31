# Equipe agile - Tracage PDF lecteur multi-page

Date: 2026-05-31
Roadmap: `RM-2026-0045`
Ordre: `ORD-P1-043`
Chantier: `CH-20260531-040800-RM-2026-0045-pdf-trace-multipage-reader`
Conversation: `CONV-2026-1927`

Statut courant: pret a integrer.

## BOT-START

BOT-START - coordinateur-scribe - 2026-05-31 04:08 +02:00

Mission: livrer la prochaine brique visible de la feature PDF/Zotero:
permettre de choisir la page exacte dans l'atelier PDF avant de dessiner une
zone, afin que la trace candidate garde une ancre `page + rectangle` fiable.

Ownership modifiable:

- `server/src/coproscope/web/templates/document_detail.html`
- `server/src/coproscope/web/_document_viewer_parts/01_detail_sections.py`
- `server/src/coproscope/web/static/pdf_trace_selection.js`
- `server/src/coproscope/web/static/styles_part_31.css`
- `server/src/coproscope/modules/pdftrace_registry.py`
- `server/src/coproscope/modules/annotationops.py`
- `server/tests/test_annotationops.py`
- `server/tests/test_ui_document_viewer_multipage.py`
- cette note, `docs/presence_agents.md`, `docs/roadmap_backlog_central.md`
- `docs/assets/pdf-trace-ui-2026-05-31/pdf-trace-multipage-target.png`

Fichiers evites:

- fichiers ComptaScope de `CONV-2026-1926`;
- modules PDF backend hors validation page/hash directe;
- instances privees, documents bruts, OCR/logs, exports bruts et secrets;
- serveurs non reserves, scans/kills et push GitHub;
- copie directe de code Zotero.

Dernier point lu: `AGENTS.md`, `docs/strategie_equipes_multi_agents.md`,
`docs/protocole_equipe_agile_agents.md`, `docs/presence_agents.md`,
`docs/roadmap_backlog_central.md`, cadrage PDF/Zotero et tranches
`CONV-2026-1921` / `CONV-2026-1924`.

Risque de collision: `CONV-2026-1926` travaille Compta dans le meme worktree et
possede des fichiers Compta + traces de coordination. Cette tranche ne touche
pas les fichiers Compta et limite les changements de coordination a ses lignes
propres.

Tests/preuves attendus:

- l'atelier affiche un controle page precedente / page suivante / numero page;
- la page courante alimente le champ POST `page`;
- changer de page remet la selection a zero et desactive l'enregistrement;
- la trace enregistree affiche la page choisie;
- aucun chemin local ni champ technique Zotero dans l'HTML;
- tests UI/PDF/annotations verts, line-limit et diff-check.

## ROUTAGE_EQUIPE

Preflight: reprise de l'objectif actif `RM-2026-0045`. Le lot Compta
`CONV-2026-1926` reste actif mais disjoint. Aucun nouveau `ORD-*` n'est choisi:
on continue `ORD-P1-043`.

Equipe-type: `AGILE_UI_PRODUIT`.

Orchestration: pipeline UI court. Designer/facilitateur + novice + QA/privacy
+ expert DocOps rendent avant dev; owner code dans le fil pilote.

Roles a lancer:

- designer/facilitateur UI;
- utilisateur novice/usage;
- QA privacy/regression;
- expert DocOps/preuve.

Roles non lances: aucun role requis volontairement ignore.

Gates avant dev:

- visuel IA bitmap produit;
- blueprint cible ci-dessous;
- GO/NO-GO novice sur la comprehension "page exacte + zone";
- GO/NO-GO QA sur anti-fuite et non-regression;
- GO/NO-GO expert sur preuve candidate non destructive.

Livrable attendu: lecteur PDF V2 minimal avec choix de page, sans PDF modifie,
sans promesse de preuve validee.

Condition d'arret: `PRET_A_INTEGRER` si les gates roles + tests passent, sinon
`BLOQUE` ou `EN_ATTENTE_USER`.

## Visuel IA cible

Image cible:
`docs/assets/pdf-trace-ui-2026-05-31/pdf-trace-multipage-target.png`

Decision visuelle: conserver l'atelier en deux zones, ajouter un bandeau de
navigation page au-dessus de la page PDF et une colonne de miniatures. La page
active est lisible, et le panneau de droite reprend la page choisie dans le
message `Zone selectionnee sur la page N`.

## Blueprint

Route reelle: `/documents/{doc_id}`.

Etat initial:

- bouton `Enregistrer comme trace candidate` desactive;
- champ cache `page = 1`;
- statut visible `Zone a selectionner`;
- controles `Page precedente`, `Page suivante`, `Page courante`, `Page totale`
  si le nombre de pages est connu.

Interaction:

1. l'utilisateur change de page;
2. CoproScope met a jour `page`;
3. CoproScope efface tout rectangle precedent;
4. l'utilisateur dessine une zone;
5. CoproScope active le bouton et affiche `Zone selectionnee sur la page N`;
6. le POST enregistre la trace candidate sur la page N.

Hors perimetre:

- rendu PDF.js/Zotero complet;
- zoom reel;
- selection multi-page en une seule trace;
- poignees redimensionnables avancees;
- OCR ou vision.

## Contrat donnees UI

- `data-pdf-trace-current-page`: page courante visible;
- `data-pdf-trace-page-count`: nombre de pages connu ou 1;
- `input[name=page]`: page envoyee au POST;
- `zone_x`, `zone_y`, `zone_width`, `zone_height`: coordonnees normalisees de
  la zone sur la page courante.

Invariants:

- changer de page invalide la zone precedente;
- l'UI ne publie jamais `zotero_position`, `rects`, `source_engine` ni chemin
  local;
- la trace reste `preuve_candidate`, `non_diffusable`, texte `non_confirme`.

## Retours equipe avant dev

Utilisateur novice/usage: GO avant dev, mais NO-GO de l'ecran actuel pour le
multi-page. Condition: l'ecran doit dire clairement quelle page est affichee et
sur quelle page la zone sera enregistree. Libelles requis: `Page precedente`,
`Page suivante`, `Page N sur M`, `Choisissez la page, puis encadrez la zone`,
`Zone a selectionner sur la page N`, `Zone selectionnee sur la page N` et
confirmation `Zone encadree page N`. Si le nombre de pages est inconnu, dire
`nombre total de pages non connu`. Quand la page change, l'ancienne zone doit
disparaitre. Le bouton conseille est `Enregistrer cette zone comme trace
candidate`. Garder visible: `Le PDF original n'est pas modifie`.

Designer/facilitateur UI: NO-GO avant dev en l'etat tant que le blueprint ne
verrouille pas le risque lecteur trompeur. Le visuel cible est bon, mais la
page affichee doit etre celle choisie et le rectangle doit etre mesure sur la
page courante. Point technique releve: le JS actuel remet `page = 1` au moment
du commit. Conditions UX: page precedente desactivee page 1, page suivante
desactivee derniere page, changement de page met a jour le POST, efface la zone
et desactive l'enregistrement, puis `Zone selectionnee sur la page N` doit apparaitre
apres dessin. Risque accepte pour cette tranche: pas de rendu PDF.js/Zotero
complet; l'UI doit rester honnete si l'apercu natif ne permet pas de garantir
un rendu page par page.

## BOT-END

BOT-END - coordinateur-scribe - 2026-05-31 04:13 +02:00

Statut: `PRET_A_INTEGRER`.

Livraison: lecteur multi-page minimal dans l'atelier PDF. L'utilisateur choisit
la page, la zone precedente est effacee si la page change, puis la trace
candidate garde `page + rectangle` sans modifier le PDF source.

Retours equipe: designer GO sur la navigation prudente, novice GO si les
libelles restent explicites, QA/privacy GO sur anti-fuite, expert DocOps GO sur
sidecar non destructif.

Preuves:

- panier complet 52 OK:
  `tests.test_ui_document_viewer tests.test_ui_document_viewer_multipage tests.test_pdftraceops tests.test_annotationops tests.test_ui_comptes_rapprochement tests.test_ui_smoke_routes_expanded tests.test_code_line_limit -v`;
- `git diff --check` OK;
- scan anti-fuite du diff OK.

Limite: recette navigateur live differee pour ne pas ouvrir un serveur
supplementaire pendant le diagnostic CPU/RAM `RECOVER`. Le lecteur PDF.js ou
Zotero complet, les poignees de redimensionnement et la vision restent hors
lot.

QA privacy/regression: GO dev seulement tests-first, NO-GO integration sans
controle serveur. Tests requis: rendu des controles sur PDF trois pages, POST
page 2 qui sauvegarde page 2, rejet page 4 sur document connu a trois pages,
changement de page qui remet la zone a zero, aucun chemin local ni champ
technique (`source_engine`, `zotero_position`, `rects`) dans l'HTML public.
Point de vigilance ajoute pendant test: une empreinte SHA-256 numerique ne doit
pas etre confondue avec un numero de telephone par le garde-fou anti-fuite.

Expert DocOps/preuve: GO dev borne, NO-GO livraison sans validation cote
serveur. Invariants: PDF source jamais modifie, trace toujours sidecar,
`preuve_candidate`, `non_diffusable`, texte `non_confirme`, hash de version
conserve, page de trace refusee si elle depasse le nombre de pages connu, aucun
chemin local ni detail Zotero technique expose dans l'interface. Le lecteur
multi-page minimal ne doit pas promettre une preuve validee ni un rendu PDF.js
complet.

Decision coordinateur avant dev: GO dev conditionnel apres ajustement de la
commande. La tranche livre un choix de page robuste cote formulaire et
sidecar, pas un lecteur PDF complet. Si l'apercu natif ne garantit pas une
page isolee, le libelle doit rester prudent: `Page choisie pour la trace` et
non promesse de rendu PDF final.

## BOT-END

BOT-END - coordinateur-scribe - 2026-05-31 04:32 +02:00

Roadmap: `RM-2026-0045`
Chantier: `CH-20260531-040800-RM-2026-0045-pdf-trace-multipage-reader`
Conversation: `CONV-2026-1927`
Statut: `PRET_A_INTEGRER`

Fichiers modifies:

- `server/src/coproscope/web/templates/document_detail.html`
- `server/src/coproscope/web/_document_viewer_parts/01_detail_sections.py`
- `server/src/coproscope/web/static/pdf_trace_selection.js`
- `server/src/coproscope/web/static/styles_part_31.css`
- `server/src/coproscope/modules/pdftrace_registry.py`
- `server/src/coproscope/modules/annotationops.py`
- `server/tests/test_annotationops.py`
- `server/tests/test_ui_document_viewer_multipage.py`
- cette note, `docs/presence_agents.md`,
  `docs/roadmap_backlog_central.md`

Resultat:

- l'atelier PDF affiche un choix de page quand le document PDF a plusieurs
  pages connues;
- `Page precedente`, `Page suivante`, `Page N sur M` et le champ page pilotent
  la page envoyee au POST;
- changer de page efface le rectangle, vide les coordonnees et desactive le
  bouton d'enregistrement;
- une selection faite sur la page N envoie `page = N`;
- le serveur refuse une page au-dela du `page_count` connu;
- le PDF source reste inchange et la trace reste candidate, sidecar,
  non diffusable et non confirmee;
- correction anti-fuite: les empreintes SHA-256 valides ne sont plus refusees
  comme faux positifs de telephone, tout en gardant le blocage des chemins,
  emails et vrais numeros dans les textes publics.

Tests/preuves:

- `.\.venv\Scripts\python.exe -m unittest tests.test_annotationops tests.test_ui_document_viewer_multipage -v`: 11 OK;
- `.\.venv\Scripts\python.exe -m unittest tests.test_ui_document_viewer tests.test_ui_document_viewer_multipage tests.test_pdftraceops tests.test_annotationops tests.test_ui_smoke_routes_expanded -v`: 42 OK;
- `.\.venv\Scripts\python.exe ..\tools\check_code_line_limit.py`: OK;
- `git diff --check` cible: OK.

Limites:

- `RECETTE_PAGE_REELLE_WAIVED`: pas de nouveau serveur lance dans cette
  reprise; la recette navigateur du lecteur multi-page complet reste a faire;
- l'apercu natif du navigateur est utilise en mode prudent, pas un lecteur
  PDF.js/Zotero complet;
- pas encore de poignees avancees, selection multi-page en une trace, ni
  recuperation automatique d'information par vision.
