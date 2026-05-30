# Equipe agile - Navigation responsive mobile

Date: 2026-05-25 10:16 +02:00.
Rattachement: `ORD-P0-000`, qualite live `RM-2026-0006`, travaux `RM-2026-0032`.
Chantier: `CH-20260525-101645-RM-2026-0006-responsive-nav-mobile`.

## BOT-START - Coordinateur-scribe - 2026-05-25 10:16 +02:00

Roadmap: `RM-2026-0006`, rattachement travaux `RM-2026-0032`.
Chantier: `CH-20260525-101645-RM-2026-0006-responsive-nav-mobile`.
Conversation: `CONV-2026-1738`.
Role: coordinateur-scribe agile.
Mission: lancer l'equipe agile demandee par Brice pour corriger le NO-GO
produit de la recette `/travaux`: navigation mobile/tablette horizontale ou
tronquee.
Ownership modifiable: cette trace, `docs/presence_agents.md`,
`docs/roadmap_backlog_central.md`, heartbeat agile du fil courant.
Fichiers a eviter: instances privees reelles, documents bruts, OCR/logs,
exports bruts, secrets, push GitHub, `RM-2026-0017`, `ORD-P0-990`, routes
metier hors navigation responsive, serveur non reserve.
Passerelle/registre de trace: ce fichier, `docs/presence_agents.md`,
`docs/roadmap_backlog_central.md`.
Dernier point lu: `AGENTS.md`, `docs/protocole_equipe_agile_agents.md`,
`docs/roadmap_backlog_central.md`, `docs/presence_agents.md`,
`docs/equipe_agile_2026-05-25_worksops-recette-navigateur.md`, watchdog
`.\tools\orchestration-watch.cmd --emit-prompt`.
Tests/preuves attendus: correction CSS/template bornee, route `/travaux`
tokenisee 200, sans/mauvais token 403, captures tablette 768x1024 et mobile
390x844 sans barre horizontale ni navigation tronquee, line-limit.
Risque de collision: le worktree principal reste sale; le correctif code est
porte uniquement dans le worktree dedie
`C:\Users\brice\CoproScope\dev\worktrees\coproscope-coque-nav-responsive-20260525`
sur la branche `codex/coque-nav-responsive-20260525`. Ce worktree propre ne
porte pas les fichiers WorksOps non suivis du principal; le patch reste donc
borne a la coque de navigation responsive et l'integration/capture live devra
etre faite ensuite par owner unique sur serveur visible reserve.
Lease ownership: 2026-05-25 12:16 +02:00.
Prochaine action: lancer roles lecture seule, corriger localement la coque
responsive, puis refaire captures.

## Roles ouverts

| Conversation | Role | Ownership |
|---|---|---|
| `CONV-2026-1738` | Coordinateur-scribe | Trace, presence, gouvernail, heartbeat |
| `CONV-2026-1739` | Designer comparaison responsive | Lecture seule, ecarts mobile/tablette |
| `CONV-2026-1740` | Utilisateur novice mobile | Lecture seule, comprehension premier ecran |
| `CONV-2026-1741` | Dev front owner responsive | Worktree dedie `coproscope-coque-nav-responsive-20260525`; `styles_part_05.css`, tests UI cibles; `base.html` / `styles_part_06.css` seulement si strictement necessaire |
| `CONV-2026-1742` | QA responsive / privacy | Lecture seule, token, anti-fuite, captures |

## Point initial

- A tester maintenant: `/travaux?token=worksops-live-local` sur le serveur
  visible deja ouvert `127.0.0.1:8773`.
- En dev maintenant: correctif navigation responsive mobile/tablette.
- En enquete maintenant: designer et novice verifient que la navigation ne
  donne plus une impression de page cassee.
- Commande prete: transformer la navigation mobile/tablette en pile compacte
  sans overflow horizontal, conserver les libelles et liens token-safe.
- Comparaison visuels enquete: reference = captures live
  `worksops-recette-20260525-0958` et verdict designer `CONV-2026-1737`.
- Agents idle a relancer: aucun role `/travaux` integration ou recette.
- Decision requise: aucune; la demande Brice `lance une equipe agile` vaut
  decision explicite pour ce correctif borne.
- Prochain mouvement: patch CSS/template, tests, captures.
- Tests/preuves: a produire apres patch.

## Retours roles - 2026-05-25 10:30 +02:00

`CONV-2026-1740` novice mobile:

- Attendu avant patch: mobile/tablette sans defilement horizontal ni onglet
  coupe.
- Le premier ecran doit montrer clairement `Travaux suivis`, le statut
  `3 sur 5` et l'action prioritaire.
- Les boutons doivent rester comprehensibles et ne doivent pas faire croire a
  un partage reel automatique.

`CONV-2026-1739` designer responsive:

- NO-GO avant patch: barre horizontale mobile et navigation tablette trop
  haute/profonde.
- Criteres GO: navigation compacte en grille/retour ligne, pas de libelle actif
  tronque, contenu metier proprement sous la navigation.
- Desktop conserve sans refonte.

`CONV-2026-1742` QA responsive/privacy:

- Premier passage NO-GO car le navigateur live servait encore l'ancien CSS.
- Apres cache-bust et recaptures: GO QA responsive et privacy.
- `/travaux` tokenise repond `200`; sans token et mauvais token repondent
  `403`.

## Patch livre

- `server/src/coproscope/web/templates/base.html`: cache-bust CSS
  `styles.css?v=20260525-responsive-nav` et correction du lien `A surveiller`
  pour garder le libelle dans un `span`.
- `server/src/coproscope/web/static/styles.css`: imports cache-bustes pour
  `styles_part_05.css` et `styles_part_06.css`.
- `server/src/coproscope/web/static/styles_part_05.css`: navigation
  mobile/tablette transformee en grille responsive sans overflow horizontal,
  headings visuellement masques, compteurs caches et liens compacts.
- `server/src/coproscope/web/static/styles_part_06.css`: topbar compacte sur
  petit mobile, navigation plus dense et icones cachees sous 720 px.

## Verification live

Serveur visible conserve sur `127.0.0.1:8773`, instance de test locale, token
`worksops-live-local`.

- Mobile `390x844`: document `375/375`, nav `355/355`, display `grid`,
  overflow visible, actif `04 Travaux suivis`, titre/statut/action presents.
- Tablette `768x1024`: document `753/753`, nav `729/729`, display `grid`,
  overflow visible, actif `04 Travaux suivis`, titre/statut/action presents.
- Captures post-patch:
  `C:\Users\brice\CoproScope\dev\captures\responsive-nav-20260525-1022\travaux-mobile.png`
  et
  `C:\Users\brice\CoproScope\dev\captures\responsive-nav-20260525-1022\travaux-tablet.png`.
- Inspection visuelle: pas de barre horizontale, pas de libelle actif tronque,
  contenu `/travaux` lisible sous la navigation.

## Tests

Depuis `server/`:

```powershell
$env:PYTHONPATH='src'; .\.venv\Scripts\python.exe -m unittest tests.test_ui_worksops_travaux tests.test_ui_security_routes tests.test_ui_demo -v
```

Resultat: `20 OK`.

```powershell
.\.venv\Scripts\python.exe ..\tools\check_code_line_limit.py
```

Resultat: `OK`, aucun fichier code suivi ne depasse 600 lignes.

Verification complementaire 2026-05-25 10:34 +02:00:

- Ajout du test de regression
  `server/tests/test_ui_responsive_shell_css.py` pour verrouiller l'absence de
  `overflow-x: auto`, la grille responsive `auto-fit`, les sections aplaties
  et les libelles qui peuvent passer a la ligne.
- Panier principal:
  `tests.test_ui_responsive_shell_css`,
  `tests.test_ui_accessibility_language`, `tests.test_ui_security_routes`,
  `tests.test_security_no_private_sync_leaks`,
  `tests.test_ui_smoke_routes_expanded`: `25 OK`.
- Panier worktree dedie identique: `25 OK`.
- `tools/check_code_line_limit.py`: `OK` dans le principal et le worktree.
- `git diff --check`: `OK` dans le principal et le worktree. Warnings CRLF
  seulement sur fichiers deja sales du principal, sans erreur diff-check.
- Captures et metriques confirmees par QA:
  `C:\Users\brice\CoproScope\dev\captures\worksops-responsive-nav-20260525-1016\mobile-390x844.png`,
  `tablet-768x1024.png`, `desktop-1280x720.png` et `metrics.json`.
- Metriques critiques: mobile document `375/375`, nav `355/355`; tablette
  document `753/753`, nav `729/729`; `hasHorizontalOverflow=false`; actif
  `04 Travaux suivis`.
- Le contrat live large `tests.test_ui_live_ux_contract` reste NO-GO sur des
  routes hors perimetre responsive (`/actions`, `/pieces`,
  `/documents/ajouter`) et n'est pas retenu comme verdict de ce lot.

## BOT-END - Coordinateur-scribe - 2026-05-25 10:30 +02:00

Statut: `CLOTURE`.
Verdict: GO produit sur le correctif borne navigation mobile/tablette de
`/travaux`.
Roles: `CONV-2026-1738`, `CONV-2026-1739`, `CONV-2026-1740`,
`CONV-2026-1741` et `CONV-2026-1742` clos.
Fichiers modifies par ce lot: cette trace, `docs/presence_agents.md`,
`docs/roadmap_backlog_central.md`,
`server/src/coproscope/web/templates/base.html`,
`server/src/coproscope/web/static/styles.css`,
`server/src/coproscope/web/static/styles_part_05.css`,
`server/src/coproscope/web/static/styles_part_06.css`,
`server/tests/test_ui_responsive_shell_css.py`.
Fichiers evites: instances privees reelles, documents bruts, OCR/logs,
exports bruts, secrets, push GitHub, `RM-2026-0017`, `ORD-P0-990`.
Serveur: reste ouvert volontairement dans le PowerShell visible sur `8773`
pour recette; arret uniquement par `Ctrl+C`.

AGILE-DONE - equipe agile a fini son job.
