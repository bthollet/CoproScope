# QA cycle N - Apercu HTML `/exports/passation`

Date: 2026-05-21
Produit live teste: `http://127.0.0.1:8766`
Token: `local-secret`
Capture temporaire: `C:\Users\brice\CoproScope\coproscope\.codex-tmp\qa-cycle-n-20260521-211912`

## Synthese live

La route `/exports/passation` repond maintenant en HTML sur le serveur live et garde
le token dans les liens TXT/JSON. Les exports TXT et JSON restent telechargeables,
watermarkes et sans fuite detectee de chemins prives.

Ecart UX observe: l'apercu HTML live est rendu sans shell visuel CoproScope dans
les captures Chrome headless (`exports-passation-preview-desktop.png`,
`exports-passation-preview-mobile.png`). Le contenu est lisible, mais la page
apparait comme du HTML par defaut, sans navigation, topbar ni styles produit.

## Matrice de recette

| Axe | Scenario | Attendu GO | Resultat live | Verdict |
| --- | --- | --- | --- | --- |
| Token | `GET /exports/passation` sans token | `403 Jeton local requis.` | `403` observe | GO |
| Token | `GET /exports/passation?token=local-secret` | `200 text/html`, cookie/token conserves | `200 text/html` | GO |
| Non-fuite | Scanner HTML preview | Aucun `raw/`, `restricted/`, `logs/`, `private/`, `file://`, chemin Windows/home | Aucune fuite detectee | GO |
| Watermark | Preview visible | Mention `export derive, non source collaborative` visible | Visible en haut de page | GO |
| Source | Preview visible | `source_of_truth false` visible | Visible | GO |
| Formats | Liens TXT/JSON | Liens tokenises vers `/exports/passation.txt` et `.json` | Liens presents avec `scope`, `selected`, `token` | GO |
| TXT | `GET /exports/passation.txt?...` | `200 text/plain`, attachment, watermark, pas de fuite | OK | GO |
| JSON | `GET /exports/passation.json?...` | `200 application/json`, attachment, `source_of_truth=false`, sections attendues | OK | GO |
| Scope preview | `scope=event&selected=MEM-DOC-7D412766` | Preview affiche le perimetre et propage scope/selected aux liens | OK | GO |
| Scope exports | TXT/JSON avec `scope=event&selected=MEM-DOC-7D412766` | Le contenu telecharge correspond au perimetre choisi ou signale clairement le fallback global | TXT/JSON identiques au pack global hors `generated_at`; `scope.kind` reste `passation_ag_contentieux` | NO-GO coherence |
| Redirect ancien | `GET /exports/passation?...` | Ne redirige plus vers TXT; affiche l'apercu HTML | `200 text/html` | GO |
| Responsive | Mobile 390px | Pas de fuite ni chevauchement bloquant; controles formats accessibles | Contenu accessible, mais page non stylisee | NO-GO UX |
| Shell produit | Desktop/mobile | Meme shell CoproScope que les autres routes, styles charges, navigation/retour visibles | Non visible dans capture live | NO-GO UX |

## Checks complementaires N-1

| Route | Resultat | Note |
| --- | --- | --- |
| `/actions/__COPROSCOPE_TEST_ACTION_MISSING_999__?token=local-secret` | `303` vers `action_missing`, puis `200` notice novice | OK |
| `/actions?scope=comptes` | `200`, libelles comptes/action/preuve presents | OK |
| `/pieces?proof=missing` | `200`, deux pieces manquantes, actions demande/depot visibles | OK |
| `/demandes/relance?token=local-secret` | `200`, pas de banniere de succes | OK |
| `/demandes/relance?token=local-secret&sent=1` | `200`, affiche `Relance enregistree fictivement` sans POST | NO-GO integrite UX |
| `/chantiers?selected=MEM-DOC-7D412766` | `200`, detail present sous la timeline | GO fonctionnel, P2 UX car detail loin sous le fold |
| `/chantiers/__COPROSCOPE_TEST_MEMOIRE_MISSING_999__?token=local-secret` | `303` vers `event_missing`, puis `200` fallback novice | OK |

## Points de vigilance ouverts

- P1: `GET /demandes/relance?sent=1` suffit a afficher une confirmation de relance fictive sans POST valide.
- P1: `/exports/passation` est fonctionnel mais le rendu live capture est hors shell/styling produit.
- P1: les liens TXT/JSON conservent `scope/selected`, mais le contenu exporte reste identique au pack global.
- P2: le detail memoire selectionne existe, mais il est tres bas sous la timeline et manque de libelles de retour/export visibles.

## Resolution 21:46 CET

Les trois P1 ci-dessus ont ete repris apres cette QA.

- `GET /demandes/relance?sent=1&token=local-secret` n'affiche plus de succes sans `request_id` et sans journal correspondant.
- Le POST relance ajoute maintenant `sent_id=JRN-UI-RELANCE-*` dans la redirection, afin de relire exactement la trace creee.
- `/exports/passation` est branche sur le template produit `passation_export.html` et les styles `cs-passation-*`.
- Les exports TXT/JSON avec `scope=event&selected=MEM-DOC-7D412766` produisent un extrait `passation_event` avec une seule entree de chronologie et sans l'autre evenement `MEM-DOC-816608C5`.

Verification de cloture:

- `server\.venv\Scripts\python.exe -m unittest server.tests.test_ui_passation_export_route -v` -> `6 tests OK`.
- `server\.venv\Scripts\python.exe -m unittest server.tests.test_security_no_private_sync_leaks server.tests.test_ui_smoke_routes_expanded server.tests.test_ui_requests_route -v` -> `16 tests OK`.
- `server\.venv\Scripts\python.exe -m unittest discover -s server/tests -p "test_ui_*.py" -v` -> `156 tests OK`.

## Commandes lancees

```powershell
$env:COPROSCOPE_LIVE_REQUIRED='1'; $env:COPROSCOPE_LIVE_URL='http://127.0.0.1:8766'; $env:COPROSCOPE_LIVE_TOKEN='local-secret'
server\.venv\Scripts\python.exe -m unittest server.tests.test_ui_live_ux_contract server.tests.test_ui_passation_export_route server.tests.test_ui_memoire server.tests.test_ui_action_detail_route server.tests.test_ui_requests_route server.tests.test_ui_smoke_routes_expanded server.tests.test_ui_security_routes -v
```

Resultat: `Ran 31 tests in 56.052s - OK`.

## Captures utiles

- `action-introuvable-desktop.png`
- `actions-comptes-desktop.png`
- `pieces-manquantes-desktop.png`
- `pieces-manquantes-mobile.png`
- `relance-sans-sent-desktop.png`
- `relance-get-sent-probe-desktop.png`
- `memoire-selected-desktop-extra-tall.png`
- `memoire-introuvable-desktop.png`
- `exports-passation-preview-desktop.png`
- `exports-passation-preview-mobile.png`
