# Equipe agile IncidentOps - protocole strict

Date: 2026-06-02 09:21 +02:00

Roadmap: `RM-2026-0034` / `RM-2026-0031` / `ORD-P1-070`

Chantier: `CH-20260602-090652-RM-2026-0034-incidentops-tests-utilisateur`

Coordinateur: `CONV-2026-2052`

Worktree: `dev/worktrees/coproscope-incidentops-tests-utilisateur-20260602`

Branche: `codex/20260602-incidentops-tests-utilisateur`

## Preflight

Consigne superviseur respectee:

- ne pas prendre cockpit ni son worktree;
- ne pas toucher `/comptes`;
- ne pas toucher la reconstruction;
- ne pas toucher les donnees privees;
- ne pas toucher Zotero;
- ne pas modifier `main`.

Rollback effectue:

- modifications produit/test/backlog annulees;
- captures et note de regularisation supprimees;
- seul `docs/presence_agents.md` garde la trace anti-collision et le rollback.

## Routage Equipe

Preflight: OK hors cockpit, hors `/comptes`, hors reconstruction.

Equipe-type: `AGILE_UI_PRODUIT`.

Orchestration: sous-agents lances apres objectif utilisateur explicite de travail multi-agents.

Sous-agents recus: organisateur/test, utilisateur expert audit, designer/facilitateur, dev front et dev back/viewmodel. Aucun sous-agent n'a modifie de fichier.

Roles:

- coordinateur-scribe: `CONV-2026-2052`;
- designer/facilitateur: `CONV-2026-2053`;
- utilisateur novice: `CONV-2026-2054`;
- expert syndic/process: `CONV-2026-2055`;
- dev front: `CONV-2026-2056`, lecture seule jusqu'au GO;
- dev back/viewmodel: `CONV-2026-2057`, lecture seule jusqu'au GO;
- QA: `CONV-2026-2058`.

## UI Cible

Route reelle visee: `/incidents`.

Donnees de recette: uniquement donnees fictives ou instance synthetique.

Objectif utilisateur: un membre du conseil syndical doit comprendre quoi faire apres un signalement, sans croire que CoproScope envoie une declaration, partage une piece ou cloture le dossier automatiquement.

## References Visuelles

Reference proche:

- `docs/assets/etude-utilisateurs/registre-decisions-actions-preuves.png` pour la logique decision -> action -> preuve;
- `docs/assets/etude-utilisateurs/cockpit-conseil-syndical.png` pour la densite et la hierarchie du shell.

Reference specifique IncidentOps: aucune image d'enquete dediee trouvee dans ce passage. Le visuel IA cible doit donc servir de reference designer derivee.

## Blueprint Cible

Premier ecran:

- titre `Incidents et sinistres`;
- phrase courte: CoproScope prepare la suite, mais n'envoie rien;
- statut de page: suivi local / aucune declaration;
- indicateurs compacts orientes action: urgence, infos a completer, preuve attendue, preuve recue;
- CTA principal: completer un signalement, pas declarer;
- CTA secondaire: voir les actions a faire.

Corps de page:

- liste des signalements avec lieu, statut, urgence, assurance, preuve attendue, prochaine action et diffusion;
- actions autorisees: consulter les actions, joindre une photo ou un document masque, voir preuves attendues;
- actions bloquees: declaration assurance, partage large, cloture;
- limites visibles: pas de piece brute, pas de chemin local, pas de transmission automatique.

## Visuel IA

Statut: produit avant commande dev.

Chemin: `docs/assets/ux-cibles-2026-06-02-incidentops/incidentops-cible.png`.

Verdict designer:

- GO comme reference cible: ecran complet, structure app, donnees fictives, action/preuve/diffusion visibles;
- reserve: le visuel emploie parfois `photo`, a traduire dans le produit en `photo ou document masque`;
- ne pas copier les chiffres du visuel IA, ils servent seulement a la hierarchie.

UI actuelle capturee avant dev:

- desktop: `docs/assets/ux-cibles-2026-06-02-incidentops/incidentops-ui-actuelle-desktop.png`;
- mobile: `docs/assets/ux-cibles-2026-06-02-incidentops/incidentops-ui-actuelle-mobile.png`;
- HTML rendu depuis `/incidents` sur instance synthetique: artefact local non commite, car il contient des liens tokenises de test.

Ecarts constates:

- `Qualifier un signalement` peut faire croire a un workflow complet;
- `Ajouter preuve locale` peut faire croire au depot d'une piece brute;
- `Voir actions incidents` reste jargon;
- `Journal de versions` est une trace technique trop visible;
- le glossaire prend trop de place avant la file;
- sur mobile, `Nouvelle demande` deborde dans l'en-tete.

## Qualification Novice

Statut: rendu avant dev.

Questions:

- Est-ce que je comprends qu'aucune declaration ne part depuis la page ?
- Est-ce que je sais quoi faire maintenant ?
- Est-ce que les actions disponibles paraissent vraiment disponibles ?
- Est-ce que les actions bloquees sont assez claires ?

Verdict novice:

- GO sur le principe: la page dit deja qu'il n'y a pas de declaration depuis CoproScope;
- NO-GO sur les libelles actuels: `Qualifier un signalement`, `Ajouter preuve locale` et `Voir actions incidents` promettent trop ou parlent trop technique;
- NO-GO mobile: bouton `Nouvelle demande` deborde et parasite la lecture;
- GO pour une correction courte si elle remplace ces mots et garde les actions sensibles bloquees.

## Avis Expert Syndic/Process

Statut: rendu avant dev.

Contraintes:

- declaration assurance externe et humaine;
- partage coproprietaires bloque tant que la diffusion n'est pas validee;
- cloture impossible sans preuve controlee;
- photos originales et pieces brutes non affichees dans une sortie diffusable.

Verdict expert:

- GO si l'outil reste un preparateur local;
- NO-GO si un bouton laisse croire a une declaration, un partage ou une cloture;
- la preuve peut etre jointe seulement comme preuve controlee ou derivee, pas comme original brut.

## Gate Avant Dev

Statut: GO pour correction courte uniquement.

Points fermes:

- visuel IA bitmap produit;
- blueprint ci-dessus qualifie;
- novice NO-GO explicite sur l'etat actuel et GO sur la correction courte;
- expert GO avec garde-fous;
- commande dev ci-dessous stabilisee.

## Commande Dev Bornee

Objectif:

Rendre `/incidents` moins trompeur pour un membre CS novice, sans creer de vrai formulaire, sans declaration assurance, sans partage et sans cloture automatique.

Fichiers modifiables:

- `server/src/coproscope/web/incidentops_view.py`;
- `server/src/coproscope/web/templates/incidents.html`;
- `server/src/coproscope/web/static/styles_part_22.css`;
- `server/tests/test_ui_incidentops.py`;
- `docs/presence_agents.md`;
- ce document.

Changements autorises:

- remplacer `Qualifier un signalement` par `Completer un signalement`;
- remplacer `Voir actions incidents` par `Voir les actions a faire`;
- remplacer `Ajouter preuve locale` par `Joindre photo ou document masque`;
- clarifier que la page prepare la suite et n'envoie pas de declaration assurance ou syndic;
- rendre les compteurs plus orientes action;
- replier le glossaire;
- renommer `Journal de versions` en limites/garde-fous de page;
- sur `/incidents`, remplacer le bouton d'en-tete `Nouvelle demande` par un raccourci court vers les suites.
- integrer la photo comme photo/document masque, jamais comme fichier brut affiche ou partage;
- corriger les libelles d'incidents clos pour ne plus afficher preuve a definir ou assurance a verifier;
- ajouter les libelles de colonne sur mobile.

Changements interdits:

- creer un formulaire de qualification;
- envoyer ou simuler une declaration;
- ajouter un partage large;
- creer une cloture automatique;
- toucher cockpit, `/comptes`, reconstruction, Zotero ou donnees privees.

Criteres d'acceptation:

- les anciens libelles trompeurs ne sont plus visibles;
- les actions sensibles restent bloquees;
- la route reste protegee par token;
- la page reste lisible mobile/desktop sur donnees fictives;
- aucun marqueur prive ou brut n'apparait.

## Demande Brice Photo

Instruction recue: `incidents: integre photo`.

Interpretation protocole:

- GO petite iteration: faire apparaitre la photo comme type de photo/document masque attendu ou joignable;
- NO-GO feature: ne pas creer ici de galerie, vision photo, biffage automatique ou workflow d'envoi;
- garde-fou: aucune photo originale, aucun chemin local, aucun contenu brut dans Git ou dans une sortie diffusable.
- backlog ajoute: `BACKLOG_INCIDENTOPS_PHOTO_WORKFLOW` dans `docs/roadmap_backlog_central.md`.

## Organisateur De Test

Retour `CONV-2026-2053` / organisateur de test, 2026-06-02:

Scenarios anonymises:

1. Signalement ouvert avec lieu ou sujet a completer.
   Preuve attendue a l'ecran: statut, urgence, assurance a verifier, preuve attendue, prochaine action et diffusion `Conseil syndical seulement`.
   Action de test: verifier qu'on comprend quoi demander sans croire qu'un envoi part depuis CoproScope.

2. Incident avec piece candidate mais cloture non prouvee.
   Preuve attendue a l'ecran: `piece candidate a verifier` ou equivalent, pas `dossier clos`.
   Action de test: confirmer que la preuve reste a valider humainement et qu'aucune piece brute n'est affichee.

3. Incident resolu ou classe.
   Preuve attendue a l'ecran: `preuve recue` seulement si une preuve de cloture existe.
   Action de test: verifier que CoproScope aide a decider mais ne cloture pas automatiquement.

Risques remontes:

- croire que completer un signalement lance une declaration assurance;
- croire que la photo/document masque autorise une photo originale ou piece brute;
- confondre piece candidate et preuve validee;
- confondre `Conseil syndical seulement` avec un partage coproprietaires deja autorise.

## QA Apres Dev

Observation intermediaire:

- desktop: les libelles corriges sont visibles et alignes avec le visuel cible;
- mobile: le raccourci d'en-tete `Voir suites` deborde partiellement. Correction autorisee: cacher ce raccourci sur mobile, car le CTA principal existe deja dans le hero.

Retours sous-agents:

- dev back/viewmodel: GO lecture seule, tests cibles IncidentOps 5 OK, aucun fichier modifie;
- dev front: GO lecture seule sur template/CSS, tests cibles IncidentOps 5 OK, aucun fichier modifie;
- designer/facilitateur: GO partiel desktop mais NO-GO mobile avant correction, car debordement et tableau encore trop large;
- utilisateur expert audit: NO-GO utilisateur avant correction, car les mots `qualification`, `IncidentOps`, `File incidents`, `preuve controlee`, `References opaques` et l'incident clos pouvaient tromper.

Correction finale appliquee dans ce lot borne:

- photo integree comme `photo ou document masque`;
- bouton d'en-tete masque sur mobile;
- tableau desktop compacte sans largeur minimale forcee;
- libelles de colonnes ajoutes aux lignes mobile;
- incident clos fictif sans assurance a verifier ni preuve a definir;
- recherche shell reformulee vers les documents rattaches.

## Preuves Attendues Si Dev

- `tests.test_ui_incidentops`;
- `tests.test_ui_security_routes`;
- `tests.test_ui_smoke_routes_expanded`;
- `tests.test_security_no_private_sync_leaks`;
- `tools/check_code_line_limit.py`;
- `git diff --check`;
- capture desktop/mobile sur donnees fictives ou waiver explicite.

## Recette Finale

Date: 2026-06-02 09:56 +02:00.

Resultat coordinateur: GO `PRET_A_INTEGRER`.

Preuves executees:

- `python -m unittest tests.test_ui_incidentops -v`: 5 tests OK;
- `python -m unittest tests.test_ui_incidentops tests.test_ui_security_routes tests.test_ui_smoke_routes_expanded tests.test_security_no_private_sync_leaks -v`: 23 tests OK;
- `python tools\check_code_line_limit.py`: OK, aucun fichier code suivi au-dessus de 600 lignes;
- `git diff --check`: OK;
- recherche anti-libelles trompeurs et anti-fuite sur la page finale: aucun ancien libelle visible dans le produit.

Captures fictives livrees:

- `docs/assets/ux-cibles-2026-06-02-incidentops/incidentops-apres-dev-desktop.png`;
- `docs/assets/ux-cibles-2026-06-02-incidentops/incidentops-apres-dev-mobile.png`;
- `docs/assets/ux-cibles-2026-06-02-incidentops/incidentops-apres-dev-mobile-long.png`;
- HTML autonome: artefact local non commite, car il contient des liens tokenises de test.

Garde-fous tenus:

- aucune donnee privee, photo brute, chemin local, OCR/log ou secret ajoute dans Git;
- aucune declaration assurance, relance, partage large ou cloture automatique creee;
- aucune modification de `main`, cockpit, `/comptes`, reconstruction ou Zotero;
- aucun serveur durable lance.

Limite explicite:

- le vrai parcours photo complet reste en backlog `BACKLOG_INCIDENTOPS_PHOTO_WORKFLOW`: vignettes, purge EXIF, masquage/biffage, rattachement incident, validation humaine et diffusion conseil syndical seulement.
