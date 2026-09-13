# Equipe backend - Tracage PDF texte depuis zone

Date: 2026-05-31
Roadmap: `RM-2026-0045`
Ordre: `ORD-P1-043`
Chantier: `CH-20260531-041700-RM-2026-0045-pdf-trace-zone-text`
Conversation: `CONV-2026-1928`

Statut courant: pret a integrer.

## BOT-START

BOT-START - coordinateur-scribe - 2026-05-31 04:17 +02:00

Mission: livrer la prochaine brique probatoire de la feature PDF/Zotero:
quand l'utilisateur encadre une zone dans un PDF texte, CoproScope essaie de
recuperer le texte qui tombe dans cette zone, puis le garde comme information
candidate. Le rectangle reste la preuve rejouable; le texte reste a relire.

Ownership modifiable:

- `server/src/coproscope/modules/pdftrace_registry.py`
- `server/src/coproscope/modules/pdftrace_zone_text.py`
- `server/tests/test_pdftrace_registry_text_recovery.py`
- cette note, `docs/presence_agents.md`, `docs/roadmap_backlog_central.md`

Fichiers evites:

- fichiers ComptaScope de `CONV-2026-1926`;
- templates/CSS et lecteur UI hors besoin strict;
- instances privees, documents bruts, OCR/logs, exports bruts et secrets;
- serveurs non reserves, scans/kills et push GitHub;
- copie directe de code Zotero.

Dernier point lu: `AGENTS.md`, `docs/strategie_equipes_multi_agents.md`,
`docs/protocole_roadmap_presence_agents.md`, `docs/presence_agents.md`,
`docs/roadmap_backlog_central.md`, cadrage PDF/Zotero et tranches
`CONV-2026-1912`, `1918`, `1921`, `1924`, `1927`.

Risque de collision: le worktree contient des changements ComptaScope
`PRET_A_INTEGRER`; cette tranche ne les touche pas. Les fichiers PDF deja
touches par `CONV-2026-1927` sont repris uniquement pour continuer le meme
objectif PDF/Zotero.

Tests/preuves attendus:

- zone sur PDF texte fictif -> texte candidat recupere, hash texte garde;
- zone sans mots ou extraction indisponible -> comportement actuel
  `non_confirme`;
- texte sensible dans la zone -> extrait masque, pas de fuite dans le resume;
- PDF source non modifie;
- page, hash et diffusion restent prudents;
- tests PDF/UI/annotations cibles verts, line-limit et diff-check.

## ROUTAGE_EQUIPE

Preflight: OK. Les lots Compta et PDF precedents sont `PRET_A_INTEGRER`, aucun
owner vivant `EN_COURS` ne bloque cette tranche. On poursuit l'objectif actif
`RM-2026-0045` / `ORD-P1-043`; aucun nouveau `ORD-*` n'est choisi.

Equipe-type: `BACKEND_DOMAINE`.

Orchestration: hub-and-spoke. Un owner code unique modifie les fichiers
backend/tests; expert DocOps/preuve, QA privacy/regression et novice usage
rendent en lecture.

Owner code unique: coordinateur-scribe du fil pilote.

Roles a lancer:

- expert DocOps/preuve;
- QA privacy/regression;
- utilisateur novice/usage.

Roles explicitement non lances: designer UI. `VISUEL_IA_WAIVED` et
`BLUEPRINT_WAIVED`: tranche backend sans nouveau parcours ni nouveau layout.

Gates avant dev:

- expert valide que le texte recupere reste une aide de relecture, pas une
  preuve confirmee;
- QA valide les tests anti-fuite et la non-mutation du PDF;
- novice valide les mots visibles attendus: texte repere, a relire, pas
  preuve validee.

Livrable attendu: extraction texte candidate depuis zone PDF quand disponible,
avec fallback zone seule.

Condition d'arret: `PRET_A_INTEGRER` si les roles et tests passent, sinon
`BLOQUE` ou `EN_ATTENTE_USER`.

## Contrat donnees

Entrees:

- document PDF source si disponible dans l'instance et non brut/restreint;
- `page`, `zone_x`, `zone_y`, `zone_width`, `zone_height`;
- hash document attendu.

Sorties sidecar candidates:

- `text_status = texte_reconnu` quand des mots sont trouves dans la zone;
- `text_status = non_confirme` quand aucune lecture fiable n'est possible;
- `selected_text_hash` pour reconnaitre le passage sans dependre du texte brut;
- `selected_text_excerpt` court et filtre, masque si sensible;
- `confidence = text_from_selected_zone` ou `zone_only`;
- `source_engine` interne, jamais affiche comme jargon novice.

Invariants:

- le PDF source n'est jamais modifie;
- le texte extrait reste a relire;
- les chemins locaux, OCR brut long, emails, telephones, secrets et marqueurs
  sensibles ne sortent pas dans l'interface publique;
- si le fichier a change, la trace reste candidate et a verifier.

## Retours equipe avant dev

Expert DocOps/preuve: GO dev limite, NO-GO integration sans tests et revue
privacy. Invariants rappeles: PDF source inchange, rectangle principal, texte
comme aide de relecture seulement, `preuve_candidate`, hash PDF conserve, trace
a verifier si le fichier a change, extrait court et filtre, aucun chemin local
ni donnees sensibles publiques. Manque principal identifie: le registre ne
stockait pas encore `selected_text_hash` ni extrait candidat.

Utilisateur novice/usage: GO dev avec garde-fou de wording. Mots attendus:
`Texte repere automatiquement, a relire`, `Preuve non validee par CoproScope`,
`Le PDF original n'est pas modifie`, et fallback `Texte non confirme : seule la
zone encadree est gardee`. Le mot `reconnu` est juge trop sur; il faut parler
de texte repere, pas de preuve validee.

QA privacy/regression: GO dev avec tests obligatoires. Garde-fou ajoute: pour
un texte sensible, meme le hash direct du texte peut devenir une fuite par
devinette; le registre doit alors utiliser l'ancre de zone ou rien pour la
surface publique/exportable. Tests requis: zone texte -> extrait/hash, zone
vide -> `non_confirme`, sensible -> masque, document modifie -> a verifier, UI
sans `source_engine`, `zotero_position`, `rects`, chemin local, `raw/` ou
`restricted`.

Decision coordinateur avant dev: GO backend borne. Pas de nouveau visuel IA ni
blueprint UI car la tranche ne cree ni nouveau parcours ni nouveau layout.

## BOT-END

BOT-END - coordinateur-scribe - 2026-05-31 04:25 +02:00

Roadmap: `RM-2026-0045`
Chantier: `CH-20260531-041700-RM-2026-0045-pdf-trace-zone-text`
Conversation: `CONV-2026-1928`
Statut: `PRET_A_INTEGRER`

Fichiers modifies:

- `server/src/coproscope/modules/pdftrace_registry.py`
- `server/src/coproscope/modules/pdftrace_zone_text.py`
- `server/tests/test_pdftrace_registry_text_recovery.py`
- cette note, `docs/presence_agents.md`,
  `docs/roadmap_backlog_central.md`

Resultat:

- quand le PDF texte est lisible et que la zone contient des mots, CoproScope
  cree une trace candidate avec `text_status = texte_reconnu`, `confidence =
  text_from_selected_zone`, un hash de passage et un court extrait filtre;
- quand l'extraction echoue ou que la zone ne contient pas de mots, le
  comportement reste `non_confirme` et zone seule;
- si le texte repere contient email, token, chemin ou marqueur sensible,
  l'extrait est masque et le hash direct du texte n'est pas expose: le champ
  public/exportable reprend l'ancre de zone;
- si le document a change, la trace passe `hash_a_verifier` et le texte reste
  a verifier;
- le PDF source n'est jamais modifie.

Tests/preuves:

- `.\.venv\Scripts\python.exe -m unittest tests.test_pdftrace_registry_text_recovery -v`: 4 OK;
- `.\.venv\Scripts\python.exe -m unittest tests.test_pdftrace_registry_text_recovery tests.test_ui_document_viewer tests.test_ui_document_viewer_multipage tests.test_pdftraceops tests.test_annotationops tests.test_ui_comptes_rapprochement tests.test_ui_smoke_routes_expanded tests.test_code_line_limit -v`: 57 OK;
- `.\.venv\Scripts\python.exe ..\tools\check_code_line_limit.py`: OK;
- `git diff --check` cible: OK.

Limites:

- `RECETTE_PAGE_REELLE_WAIVED`: tranche backend sans nouveau parcours; pas de
  nouveau serveur pendant le diagnostic CPU/RAM RECOVER;
- l'ordre de lecture reste simple: zones larges, tableaux complexes, colonnes,
  rotation ou scan exigent encore une reprise lecteur/OCR/vision;
- la recuperation par vision reste hors lot, mais le contrat rappelle qu'elle
  devra rendre information + position ensemble.
