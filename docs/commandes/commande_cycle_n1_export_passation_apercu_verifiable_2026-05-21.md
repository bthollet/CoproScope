# Commande cycle N+1 - Export passation apercu verifiable

> Statut gouvernail: `SPEC_DERIVEE`.
> La source de verite roadmap est `docs/roadmap_backlog_central.md`.
> Executer seulement via un `RM-*` et un `CH-*` actifs.

Date: 2026-05-21.

Role cible: dev CoproScope cycle N+1.

Perimetre: livrer `/exports/passation` comme apercu HTML verifiable avant
telechargement, depuis l'intention enquete utilisateur/Canva. Le membre du
conseil syndical novice doit savoir ce qui sera transmis, ce qui restera local,
ce qui est bloque, et pourquoi l'export derive ne remplace jamais le coffre.

Image cible designer:

- `C:\Users\brice\CoproScope\coproscope\docs\assets\ux-visuels-fictifs-2026-05-21\10_export_passation_n2_apercu_verifiable.png`
- Source HTML de reference visuelle:
  `C:\Users\brice\CoproScope\coproscope\docs\assets\ux-visuels-fictifs-2026-05-21\10_export_passation_n2_apercu_verifiable.html`

Reference UX amont:

- `C:\Users\brice\CoproScope\coproscope\docs\assets\etude-utilisateurs\memoire-copropriete.png`
- Intention: la memoire se transmet, mais seulement sous forme derivee,
  verifiee, tokenisee et sans fuite de donnees privees.

## Objectif utilisateur

Un membre CS prepare une passation et veut repondre en moins d'une minute:

- qu'est-ce qui est inclus dans l'export;
- qu'est-ce qui est exclu ou bloque;
- quelles restrictions empechent le telechargement final;
- quels formats sont disponibles: TXT, JSON audit, Markdown;
- comment revenir a la memoire ou aux actions ouvertes;
- pourquoi le fichier telecharge n'est pas la source de verite.

Phrase de reussite novice:

> Je vois ce qui part, ce qui reste dans le coffre, pourquoi le telechargement
> est bloque, et je comprends que TXT/JSON/Markdown sont des exports derives.

## Route cible

Route principale:

- `GET /exports/passation`

Routes formats conservees:

- `GET /exports/passation.txt`
- `GET /exports/passation.json`
- `GET /exports/passation.md` si Markdown est ajoute, sinon `Markdown` ouvre un
  apercu rendu depuis la meme structure derivee.

Tous les liens doivent conserver le token UI existant:

- `/exports/passation?token=...`
- `/exports/passation.txt?token=...`
- `/exports/passation.json?token=...`
- `/chantiers?token=...`
- `/actions?priority=P1&token=...`

## Structure visuelle

Reprendre le visuel cible:

- sidebar sombre avec `Exports` actif;
- topbar compacte avec titre `Apercu de passation`, recherche et badge donnees
  fictives;
- rangee de cinq compteurs: inclus, a verifier, bloques, formats, watermark;
- colonne principale `Apercu avant telechargement`;
- colonne centrale `Controle confidentialite` puis `Restrictions et blocages`;
- colonne droite `Decision avant export`.

La page ne doit pas etre une redirection texte. Elle doit etre une revue avant
telechargement.

## Composants attendus

- `passation-export-shell`
- `passation-export-metrics`
- `passation-export-preview`
- `passation-export-scope-tabs`
- `passation-export-section-row`
- `passation-export-confidentiality-checks`
- `passation-export-blockers`
- `passation-export-private-references`
- `passation-export-decision`
- `passation-export-format-actions`
- `passation-export-return-actions`

Les noms exacts peuvent suivre le style existant, mais les regions doivent
avoir des titres accessibles et/ou `data-testid` stables.

## Donnees necessaires

Projection recommandee:

```python
model.ux.passation_export_preview = {
    "context": {
        "route": "/exports/passation",
        "title": "Apercu de passation",
        "source_of_truth": False,
        "watermark": "export derive, non source collaborative",
        "token_required": True,
    },
    "summary": {
        "included_count": 9,
        "review_count": 4,
        "blocked_count": 6,
        "formats_count": 3,
        "watermark_visible": True,
    },
    "scope": {
        "label": "Passation CS - mai 2026",
        "audience": "Conseil syndical restreint",
        "period": "Mai 2026",
        "tabs": ["Conseil syndical", "Diffusable", "Archive interne"],
        "chips": ["Sujets ouverts", "Actions P1/P2", "Mai 2026", "Sans bruts"],
    },
    "sections": [
        {
            "label": "Inclus - synthese reprise",
            "content": "4 sujets chauds + 2 echeances AG",
            "status": "OK",
            "action_label": "Voir",
        },
        {
            "label": "Inclus - actions ouvertes",
            "content": "3 retards, 2 relances a tracer",
            "status": "A verifier",
            "action_label": "Corriger",
        },
        {
            "label": "Inclus - pieces attendues",
            "content": "6 pieces listees, aucune brute jointe",
            "status": "Liste seule",
            "action_label": "Filtrer",
        },
        {
            "label": "Restriction - memoire",
            "content": "2 evenements sensibles avec restrictions",
            "status": "Limite",
            "action_label": "Limiter",
        },
        {
            "label": "Inclus - comptes",
            "content": "3 anomalies documentees, montants arrondis",
            "status": "OK",
            "action_label": "Voir",
        },
        {
            "label": "Bloques - bruts prives",
            "content": "Noms, emails, chemins locaux, PDF originaux",
            "status": "Bloque",
            "action_label": "Journal",
        },
    ],
    "confidentiality_checks": [
        {"status": "OK", "label": "Aucun chemin local dans l'apercu"},
        {"status": "OK", "label": "Aucun email reel exporte"},
        {"status": "OK", "label": "Lots et contacts marques fictifs"},
        {"status": "OK", "label": "Documents bruts remplaces par references"},
        {"status": "WARN", "label": "2 relances doivent etre tracees avant telechargement"},
    ],
    "blockers": [
        {
            "title": "Relance ascenseur non tracee",
            "body": "Date et canal d'envoi externe manquent: export final verrouille.",
            "href": "/actions?priority=P1",
        },
        {
            "title": "Note infiltration C31 a valider",
            "body": "La synthese diffusable doit confirmer ce qui reste masque.",
            "href": "/chantiers?selected=EVT-FICTIF-INFIL-C31",
        },
    ],
    "private_references": [
        "DOC-FICTIF-B12-ASSUR",
        "DOC-FICTIF-C31-INFIL",
        "ACTION-FICTIF-ASC-2025",
        "EVT-FICTIF-INFIL-C31",
    ],
    "formats": [
        {"id": "txt", "label": "TXT lisible", "href": "/exports/passation.txt"},
        {"id": "json", "label": "JSON audit", "href": "/exports/passation.json"},
        {"id": "markdown", "label": "Markdown", "href": "/exports/passation.md"},
    ],
    "actions": {
        "download": {
            "label": "Telecharger export derive",
            "enabled": False,
            "disabled_reason": "2 points a verifier",
        },
        "fix_blockers": {"label": "Corriger les blocages", "href": "/actions?priority=P1"},
        "back_memory": {"label": "Retour memoire", "href": "/chantiers"},
        "back_actions": {"label": "Retour actions ouvertes", "href": "/actions?priority=P1"},
    },
}
```

## Interactions

| Interaction | Attente utilisateur | Resultat attendu | No-go |
| --- | --- | --- | --- |
| `Telecharger TXT derive` | Telecharger une version lisible si rien ne bloque. | Lance `/exports/passation.txt` token-safe, avec watermark et `source_of_truth: false`. | Telechargement direct si blocages actifs. |
| `Voir JSON audit` | Verifier le contenu structure. | Ouvre `/exports/passation.json` token-safe, sans chemin prive. | JSON avec `raw`, `payload`, `logs`, chemin local ou source brute. |
| `Voir Markdown` | Lire une version partageable. | Ouvre apercu Markdown derive ou route `.md` token-safe. | Markdown qui omet restrictions ou watermark. |
| `Corriger les blocages` | Traiter ce qui empeche l'export. | Ouvre la premiere action ou liste filtree des blocages. | Bouton generique sans cible. |
| `Retour memoire` | Revenir a la memoire de copro. | Retourne a `/chantiers` avec token et contexte si possible. | Retour dashboard sans explication. |
| `Retour actions ouvertes` | Revenir aux actions P1/P2. | Ouvre `/actions?priority=P1` token-safe. | Perte du filtre ou rupture token. |
| `Conseil syndical / Diffusable / Archive interne` | Comparer les publics de sortie. | Met a jour inclusions, exclusions et blocages visibles. | Changement silencieux sans impact visible. |
| `Limiter` sur memoire | Regler une restriction. | Ouvre le detail evenement ou revue diffusion. | Laisse croire que tout est diffusable. |

## Etats vides et erreurs

- Aucun element exportable: afficher `Aucun sujet transmissible pour ce
  perimetre`, puis `Retour memoire` et `Voir actions ouvertes`.
- Tous les blocages corriges: le CTA devient `Telecharger export derive` actif,
  mais garde le rappel `export derive, non source collaborative`.
- Token absent ou invalide: 403 existant, pas d'apercu partiel.
- Format indisponible: bouton desactive avec raison lisible.
- Export bloque: lister les blocages et ne servir aucun fichier.

## Criteres d'acceptation

- `/exports/passation` rend un apercu HTML, pas une simple redirection texte.
- Le premier ecran montre: inclus, a verifier, bloques, formats, watermark.
- Les sections incluses/exclues/restrictions sont visibles dans l'apercu.
- Les formats TXT, JSON audit et Markdown sont exposes.
- Le watermark `export derive, non source collaborative` est visible dans
  l'apercu et present dans les payloads TXT/JSON/Markdown.
- `source_of_truth` reste `false` partout.
- Les chemins locaux, chemins absolus, `raw`, `restricted`, `logs`, emails
  reels, PDF bruts et payloads sources ne sont jamais rendus.
- Les documents bruts sont remplaces par references ou omissions lisibles.
- Les blocages verrouillent le telechargement final et disent comment corriger.
- Les CTA `Retour memoire` et `Retour actions ouvertes` conservent le token.
- La page reste lisible au clavier et les boutons ont des noms d'action reels.
- L'interface mobile empile les trois colonnes sans couper les boutons de
  format ni masquer la raison du verrouillage.

## Tests a prevoir par le dev

Depuis `C:\Users\brice\CoproScope\coproscope\server`:

```powershell
.\.venv\Scripts\python.exe -m unittest tests.test_ui_passation_export_route tests.test_ui_security_routes tests.test_ui_smoke_routes_expanded -v
```

Ajouter ou completer:

- `test_passation_default_route_returns_html_preview`
- `test_passation_preview_lists_included_excluded_and_blocked_sections`
- `test_passation_preview_exposes_txt_json_markdown_formats`
- `test_passation_preview_download_locked_when_blockers_exist`
- `test_passation_preview_links_are_token_safe`
- `test_passation_preview_has_watermark_and_source_of_truth_false`
- `test_passation_preview_does_not_leak_private_paths_or_raw_payloads`

## Commande dev prete

```text
Role: dev CoproScope cycle N+1.
Objectif: transformer /exports/passation en apercu HTML verifiable avant
telechargement, conforme au PNG:
C:\Users\brice\CoproScope\coproscope\docs\assets\ux-visuels-fictifs-2026-05-21\10_export_passation_n2_apercu_verifiable.png

Structure: sidebar Exports active, topbar Apercu de passation, compteurs
Inclus/A verifier/Bloques/Formats/Watermark, colonne Apercu avant
telechargement, colonne Controle confidentialite + Restrictions et blocages,
colonne Decision avant export.

Donnees: model.ux.passation_export_preview avec context/source_of_truth false,
watermark, scope, sections incluses/exclues/restrictions, checks
confidentialite, blockers, private_references, formats TXT/JSON/Markdown,
actions retour memoire/actions.

Interactions: Telecharger TXT derive, Voir JSON audit, Voir Markdown, Corriger
les blocages, Retour memoire, Retour actions ouvertes, changement de public et
limitation des restrictions.

Garde-fous: aucun chemin local, raw, restricted, logs, email reel, PDF brut ou
payload source dans HTML ou exports; token conserve; export final bloque tant
qu'un blocker existe; source_of_truth false; watermark visible.

Acceptation novice: je vois ce qui part, ce qui reste local, ce qui bloque le
telechargement, et je comprends que TXT/JSON/Markdown sont des exports derives,
pas la source de verite du coffre.
```

## Risques a surveiller

- L'apercu devient un simple bouton de telechargement et perd sa valeur de
  verification.
- Markdown est expose sans route ou sans watermark.
- Les exclusions sont seulement dans JSON mais invisibles pour le novice.
- Un lien de retour perd le token ou le filtre.
- Le bouton final est actif alors que les blocages sont encore presents.
