# Mode recette annotable - cadrage 2026-05-31

## BOT-START

- Roadmap: `RM-2026-0006` avec appui `RM-2026-0007` et `RM-2026-0003`.
- Backlog: `ORD-P0-037 RECETTE-ANNOTATIONS-EXECUTABLE`.
- Chantier: `CH-20260531-005600-RM-2026-0006-mode-recette-annotations`.
- Conversation: `CONV-2026-1910`.
- Role: coordinateur-scribe, puis equipe agile produit jouee par roles successifs.
- Mission: livrer un mode test/recettage dans l'executable, qui permet de pointer un objet ou une zone et de noter un probleme comme dans Codex.
- Fichiers modifiables: modules/routes/templates/static/tests de recette, branchement UI/CLI/executable, traces roadmap/presence/doc.
- Fichiers evites: instances privees, documents bruts, OCR/logs, exports reels, secrets, Drive hors raccord existant, annotations PDF metier sauf lecture.
- Preuves attendues: tests unitaires, routes token-safe, export sans jeton ni chemin local, config executable, garde-fou 600 lignes.

## Conclusion courte

C'est faisable dans CoproScope sans changer de technologie.

Le bon format est un **mode Recette** desactive par defaut. Quand il est actif, une petite barre de test apparait dans l'interface locale. Le testeur peut:

- selectionner un objet visible: bouton, lien, carte, ligne de tableau, champ;
- dessiner une zone libre sur l'ecran;
- ecrire une remarque courte;
- qualifier la gravite: bloquant, important, detail;
- exporter la liste en Markdown ou JSON.

Ce mode ne doit pas etre confondu avec les annotations metier sur PDF. Ici, on parle de remarques de test sur l'interface elle-meme.

## Bonnes pratiques retenues

Les tests doivent parler comme un utilisateur. Playwright recommande de tester le comportement visible et de preferer les reperes stables comme role, texte, label ou identifiant de test, plutot que des chemins CSS fragiles. Source: [Playwright Best Practices](https://playwright.dev/docs/best-practices) et [Playwright Locators](https://playwright.dev/docs/locators).

Les captures et traces servent surtout a comprendre une erreur, pas a remplacer une note structuree. Playwright documente les traces avec captures, et indique que les traces aident a revoir le deroule d'un test. Source: [Playwright Trace Viewer](https://playwright.dev/docs/trace-viewer) et [Tracing](https://playwright.dev/docs/api/class-tracing).

Le mode doit rester utilisable au clavier et a la souris. Le W3C recommande un focus visible et des zones cliquables assez grandes, avec un minimum de 24 px pour les cibles pointer dans WCAG 2.2 niveau AA. Sources: [WCAG 2.2 Focus Visible](https://www.w3.org/TR/WCAG22/#focus-visible) et [Target Size Minimum](https://www.w3.org/WAI/WCAG22/Understanding/target-size-minimum.html).

La recette exploratoire est normale: on apprend en testant, puis on note ce qui manque. L'ISTQB decrit l'exploratory testing comme des tests concus et executes pendant l'exploration du produit. Source: [ISTQB Glossary](https://glossary.istqb.org/).

Dans l'executable pywebview, il faut garder une protection locale. pywebview documente le lien entre JavaScript et Python, et rappelle le risque CSRF si une API locale n'est pas protegee. Source: [pywebview API](https://pywebview.flowrl.com/api/) et [pywebview Security](https://pywebview.flowrl.com/guide/security).

## Regles produit

- Desactive par defaut: aucune barre de recette en usage normal.
- Active par option explicite: `--recette` ou variable d'environnement.
- Token obligatoire si l'interface a un token.
- Export nettoye: pas de `token`, pas de chemin local, pas de `file://`, pas de dossier `raw`, `restricted`, `logs` ou `private`.
- Annotation objet: enregistrer un libelle stable et lisible, pas seulement une position d'ecran.
- Annotation zone: enregistrer le rectangle visible, la taille de fenetre et le scroll.
- Donnee append-only: on ajoute une ligne de recette, on ne modifie pas l'historique.
- Sortie diffusable: Markdown pour relire humainement, JSON pour automatiser plus tard.

## Forme V1

La V1 vise volontairement petit:

1. Backend: un registre local `registre_recette_annotations.csv` dans le dossier de registres de l'instance.
2. Routes: sauvegarde d'une annotation et exports Markdown/JSON.
3. UI: barre flottante "Recette", mode objet, mode zone, formulaire simple.
4. Executable: option `--recette` transmise au serveur local.
5. Tests: sauvegarde, nettoyage anti-fuite, routes protegees, presence/absence du mode.

## Roles agile de cette tranche

- Designer/facilitateur: interface legere, sans transformer CoproScope en outil de debug pour developpeur.
- Utilisateur novice: peut dire "ce bouton est confus" ou "ce bloc deborde" sans connaitre le HTML.
- Dev front: selection visuelle et dessin de zone.
- Dev back/viewmodel: registre, nettoyage, exports.
- QA: preuve token-safe, anti-fuite, test executable.

`VISUEL_IA_WAIVED` et `BLUEPRINT_WAIVED` pour cette tranche: il s'agit d'un outillage transverse de recette, pas d'un ecran metier final. La cible UI tient en une barre flottante et un panneau court; la preuve utile est le test reel sur l'interface.

## Iteration V1 livree

Fait:

- module registre/export: `server/src/coproscope/modules/recetteops.py`;
- routes: `/recette`, `/recette/annotations`, `/exports/recette-annotations.md`, `/exports/recette-annotations.json`;
- barre UI: `server/src/coproscope/web/static/recette_mode.js` et `styles_part_29.css`;
- activation serveur: option `--recette` et variable `COPROSCOPE_RECETTE_MODE`;
- activation executable: option `--recette` et variable `COPROSCOPE_RECETTE_MODE`;
- tests dedies: `tests/test_recetteops.py`, `tests/test_ui_recette_mode.py`, plus tests executable/securite ajustes.

Preuves lancees:

- `python -m unittest tests.test_recetteops tests.test_ui_recette_mode tests.test_executable_app tests.test_ui_security_routes tests.test_security_no_private_sync_leaks tests.test_ui_smoke_routes_expanded tests.test_code_line_limit -v`: 38 tests OK.
- `git diff --check`: OK.
- Smoke HTTP transitoire sur port `8792`: accueil `200`, config recette presente, JS present, sauvegarde annotation `200`, export Markdown `200`, note presente, jeton absent de l'export.

Limites:

- Le navigateur integre Codex a bloque l'ouverture locale `127.0.0.1` et `localhost` avec `ERR_BLOCKED_BY_CLIENT` pendant cette session. La preuve navigateur visuelle reste donc a refaire depuis une session ou l'in-app browser accepte le loopback.
- Le mode V1 ne joint pas encore de capture d'ecran image a chaque remarque. Il enregistre l'objet, le rectangle, la fenetre et le scroll.
- Le registre est local a l'instance et reste une aide de test, pas un registre metier officiel.
