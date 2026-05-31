# Equipe backend - Tracage PDF verification hash au POST

Date: 2026-05-31
Roadmap: `RM-2026-0045`
Ordre: `ORD-P1-043`
Chantier: `CH-20260531-033100-RM-2026-0045-pdf-trace-hash-post`
Conversation: `CONV-2026-1924`

Statut courant: pret a integrer.

## BOT-START

BOT-START - coordinateur-scribe - 2026-05-31 03:31 +02:00

Mission: livrer la prochaine brique probatoire de la feature PDF/Zotero:
au moment ou l'utilisateur enregistre une trace candidate, CoproScope doit
reverifier localement le hash du PDF source quand le fichier est disponible.
Si le PDF a change, la trace reste possible mais passe en `a_verifier`.

Ownership modifiable:

- `server/src/coproscope/modules/pdftrace_registry.py`
- `server/src/coproscope/modules/pdftraceops.py`
- `server/src/coproscope/web/templates/document_detail.html`
- `server/tests/test_ui_document_viewer.py`
- cette note, `docs/presence_agents.md`, `docs/roadmap_backlog_central.md`

Fichiers evites:

- fichiers ComptaScope et executable modifies par `CONV-2026-1922` et
  `CONV-2026-1923`;
- templates/CSS hors document viewer;
- instances privees;
- documents bruts;
- OCR/logs;
- exports bruts;
- secrets;
- serveur non reserve, scan/kill et push GitHub;
- copie de code Zotero.

Dernier point lu: `AGENTS.md`, `docs/consignes_bots_interconversations.md`,
`docs/protocole_roadmap_presence_agents.md`,
`docs/strategie_equipes_multi_agents.md`,
`docs/protocole_equipe_agile_agents.md`,
`docs/tableau_execution_courant.md`, `docs/presence_agents.md`,
`docs/roadmap_backlog_central.md`, `orchestration-watch --emit-prompt`.

Risque de collision: worktree sale avec lots Compta `PRET_A_INTEGRER` et
`EN_COURS`; le perimetre hash PDF reste disjoint.

Tests/preuves attendus:

- POST trace PDF valide avec hash conforme;
- POST trace PDF quand le fichier source local a change: sidecar cree mais
  `document_hash_status = hash_a_verifier`;
- aucun chemin local ni champ technique visible dans l'UI novice;
- PDF source non modifie;
- tests PDF/UI/annotations verts;
- garde-fou 600 lignes et `git diff --check`.

## ROUTAGE_EQUIPE

Preflight: OK pour reprise de l'objectif actif `RM-2026-0045`. Le watchdog
propose un lot P0 de coque, mais le present fil poursuit l'objectif persistant
fourni par Brice; aucun nouveau `ORD-*` libre n'est choisi. Collision detectee:
`CONV-2026-1923` est deja pris par Compta, donc cette tranche PDF utilise
`CONV-2026-1924`.

Equipe-type: `BACKEND_DOMAINE`.

Orchestration: hub-and-spoke. Un owner code unique modifie le backend et les
tests; expert DocOps/preuve, QA privacy/regression et novice usage challengent
en lecture.

Owner code unique: coordinateur-scribe du fil pilote.

Roles a lancer:

- expert DocOps/preuve;
- QA privacy/regression;
- utilisateur novice/usage.

Roles non lances: designer UI, car cette tranche ne change pas le parcours ni
la surface visuelle; `VISUEL_IA_WAIVED` et `BLUEPRINT_WAIVED` par non-UI.

Gates avant dev:

- accord expert sur le comportement hash conforme / hash a verifier;
- accord QA sur les tests de mismatch et anti-fuite;
- accord novice sur le libelle attendu si un fichier a change.

Livrable attendu: verification de hash au POST, statut sidecar prudent, tests
cibles et trace finale.

Condition d'arret: `PRET_A_INTEGRER` si les gates role + tests passent, sinon
`BLOQUE` ou `EN_ATTENTE_USER` selon la cause.

Tableau execution: pas de slot worker externe publie; les sous-agents sont
lances directement par le fil pilote avec ownership lecture seule.

## Contrat de donnees

Entrees:

- `document.sha256`: hash attendu depuis le registre document;
- `document.original_path`: chemin local relatif a l'instance, lu seulement
  pour calculer le hash si le fichier existe et reste dans l'instance;
- champs de zone deja fournis par l'UI interactive.

Sorties:

- `document_hash_status = hash_conforme` si le fichier local correspond;
- `document_hash_status = hash_a_verifier` si le fichier local existe mais a
  change;
- `document_hash_status = hash_non_verifie` si le fichier local n'est pas
  disponible, n'est pas dans l'instance ou se trouve dans une zone
  brute/restreinte/privee;
- aucune mutation du PDF source;
- aucune exposition de chemin local.

## Criteres d'acceptation

- le POST ne se contente plus du hash stocke quand le fichier local est
  disponible;
- une trace candidate peut encore etre creee en cas de mismatch, mais elle est
  marquee a verifier;
- le resume public parle de verification, pas de certitude;
- les tests prouvent que le PDF n'est pas modifie;
- aucune donnee privee ou chemin local ne sort dans le HTML.

## Retours equipe avant dev

Expert DocOps/preuve: GO dev, NO-GO integration tant que les tests ne prouvent
pas les trois cas. Invariants: PDF source jamais modifie, trace toujours
candidate, diffusion `non_diffusable`, texte `non_confirme` pour zone manuelle,
aucun chemin local dans HTML/erreurs/sidecar public, aucun code Zotero copie.
Le hash attendu du registre doit rester dans `document_hash`; il ne faut pas le
remplacer silencieusement par le nouveau hash.

QA privacy/regression: GO dev, NO-GO integration sans tests. Tests exiges:
hash conforme, hash change -> `hash_a_verifier`, source absente ou hors
instance -> `hash_non_verifie`, PDF inchange, anti-fuite HTML et erreurs, et
regressions commentaire prive / zone invalide.

Utilisateur novice/usage: GO dev avec condition forte de wording. Si le
document a change, l'ecran doit parler en mots simples: `Trace candidate
enregistree - a verifier`, puis expliquer que le document a change depuis son
ajout dans CoproScope. Eviter `hash`, `mismatch`, `POST`, `sidecar`, `registre`
et tout chemin local.

Decision equipe: GO dev backend borne. `VISUEL_IA_WAIVED` et
`BLUEPRINT_WAIVED`: tranche non-UI, aucun nouveau parcours visible avant dev.

## BOT-END

BOT-END - coordinateur-scribe - 2026-05-31 03:43 +02:00

Roadmap: `RM-2026-0045`
Chantier: `CH-20260531-033100-RM-2026-0045-pdf-trace-hash-post`
Conversation: `CONV-2026-1924`
Statut: `PRET_A_INTEGRER`

Fichiers modifies:

- `server/src/coproscope/modules/pdftrace_registry.py`
- `server/src/coproscope/modules/pdftraceops.py`
- `server/src/coproscope/web/templates/document_detail.html`
- `server/tests/test_ui_document_viewer.py`
- cette note, `docs/presence_agents.md`,
  `docs/roadmap_backlog_central.md`

Resultat:

- au POST, CoproScope recalcule le hash du PDF local si le fichier source est
  disponible dans l'instance;
- hash conforme: trace candidate enregistree avec `hash_conforme`;
- PDF change: trace candidate encore possible, mais visible comme
  `Trace candidate enregistree - a verifier`;
- source absente, hors instance ou brute/restreinte/privee: trace candidate marquee
  `hash_non_verifie`;
- le hash attendu du registre reste conserve;
- le PDF source n'est pas modifie;
- aucun chemin local, champ technique ou detail Zotero interne n'est affiche.

Tests/preuves:

- `.\.venv\Scripts\python.exe -m unittest tests.test_ui_document_viewer tests.test_pdftraceops tests.test_annotationops tests.test_ui_smoke_routes_expanded -v`: 37 OK;
- `.\.venv\Scripts\python.exe ..\tools\check_code_line_limit.py`: OK;
- `git diff --check` cible: OK.

Limites:

- `RECETTE_PAGE_REELLE_WAIVED`: cette tranche est backend et wording de
  confirmation, sans nouveau geste utilisateur; la recette navigateur live du
  geste complet reste a reprendre avec le lecteur PDF final;
- lecteur PDF plus complet, multi-page, poignees et recuperation d'information
  par vision restent hors lot.
