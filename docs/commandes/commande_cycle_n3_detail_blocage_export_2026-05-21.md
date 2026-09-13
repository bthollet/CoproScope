# Commande cycle N+3 - Detail blocage export passation

> Statut gouvernail: `SPEC_DERIVEE`.
> Source de verite roadmap: `docs/roadmap_backlog_central.md`.
> Executer seulement via `RM-2026-0003` / `CH-2026-0003` et ownership code
> explicite.

Date: 2026-05-21.

Role cible: dev CoproScope cycle N+3.

Perimetre: livrer un detail de blocage depuis l'apercu export passation. Le
membre du conseil syndical novice doit comprendre pourquoi une ligne est
bloquee, ce qui ne sera pas exporte, quelle preuve manque et quelle action faire
sans exposer de donnees brutes.

Image cible designer:

- `C:\Users\brice\CoproScope\coproscope\docs\assets\ux-visuels-fictifs-2026-05-21\11_detail_blocage_export_n2.png`
- Source HTML de reference:
  `C:\Users\brice\CoproScope\coproscope\docs\assets\ux-visuels-fictifs-2026-05-21\11_detail_blocage_export_n2.html`

References UX d'enquete:

- `C:\Users\brice\CoproScope\coproscope\docs\assets\etude-utilisateurs\memoire-copropriete.png`
- `C:\Users\brice\CoproScope\coproscope\docs\assets\ux-visuels-fictifs-2026-05-21\06_export_passation.png`
- `C:\Users\brice\CoproScope\coproscope\docs\assets\ux-visuels-fictifs-2026-05-21\10_export_passation_n2_apercu_verifiable.png`

## Choix du prochain bloc

Bloc retenu: `detail blocage export`.

Raison: `detail memoire`, `export passation` et `relance confirmation` ont deja
ete livres ou commandes. Le point utile suivant est de transformer la liste
`Elements exclus ou bloques` en explication actionnable: pourquoi c'est bloque,
ce qui reste local, et comment corriger ou exclure sans fuite.

## Objectif utilisateur

Un membre CS clique sur un blocage de l'apercu passation et doit repondre en
moins d'une minute:

- pourquoi cet element bloque le telechargement final;
- ce qui sera exclu ou masque dans le pack;
- quelle preuve ou trace manque;
- quelle action est la plus sure: corriger, exclure, revenir a l'apercu;
- pourquoi l'export reste derive et n'est pas la source de verite.

Phrase de reussite novice:

> Je comprends que la relance ascenseur n'est pas prouvee comme envoyee. Je
> peux noter l'envoi hors CoproScope ou exclure la relance du pack, sans exporter
> de piece brute ni de chemin prive.

## Route cible

Route recommandee:

- `GET /exports/passation/blocages/{blocker_id}`

Route equivalente acceptee si plus simple a integrer:

- `GET /exports/passation?blocker={blocker_id}`

Identifiant demo:

- `BLOCK-FICTIF-RELANCE-ASCENSEUR`

Tous les liens internes conservent le token et le contexte:

- `scope=event`
- `selected=MEM-DOC-7D412766` si le blocage vient d'un export filtre
- `token=...`

## Structure visuelle

Reprendre la grammaire des visuels d'enquete:

- sidebar sombre avec `Exports` actif;
- topbar compacte `Detail blocage export`;
- rangee de compteurs identique a l'apercu passation: inclus, a verifier,
  bloques, formats, watermark;
- colonne principale: fil d'Ariane, carte blocage, statut, exclusions et fil de
  decision;
- colonne centrale: controle confidentialite et preuves attendues;
- colonne droite: decision avant export, formats impactes et CTA.

La page doit etre une explication de blocage, pas une page d'erreur et pas une
redirection vers un fichier texte.

## Composants

Noms libres si le style existant impose une convention, mais les regions doivent
etre ciblables par role accessible ou `data-testid`.

- `passation-blocker-detail-shell`
- `passation-blocker-breadcrumb`
- `passation-blocker-summary`
- `passation-blocker-status-grid`
- `passation-blocker-excluded-items`
- `passation-blocker-decision-timeline`
- `passation-blocker-confidentiality-checks`
- `passation-blocker-required-proof`
- `passation-blocker-decision-panel`
- `passation-blocker-format-impact`
- `passation-blocker-actions`

## Donnees necessaires

Projection recommandee:

```python
model.ux.passation_export_blocker_detail = {
    "context": {
        "route": "/exports/passation/blocages/BLOCK-FICTIF-RELANCE-ASCENSEUR",
        "title": "Detail blocage export",
        "source_of_truth": False,
        "watermark": "export derive, non source de verite",
        "token_required": True,
        "scope": {"kind": "event", "selected": "MEM-DOC-7D412766"},
    },
    "summary": {
        "included_count": 9,
        "review_count": 4,
        "blocked_count": 6,
        "formats_count": 3,
        "watermark_visible": True,
    },
    "blocker": {
        "id": "BLOCK-FICTIF-RELANCE-ASCENSEUR",
        "title": "Relance ascenseur non tracee",
        "status": "blocked",
        "status_label": "Bloque export",
        "user_reason": "Date et canal d'envoi externe manquent.",
        "risk_label": "Brouillon pris pour envoi reel",
        "safe_action": "Noter l'envoi hors CoproScope",
        "linked_action_id": "ACTION-FICTIF-ASC-2025",
        "linked_request_id": "REQ-FICTIF-ASCENSEUR-SYNDIC",
        "audience": "Conseil syndical restreint",
    },
    "excluded_items": [
        {
            "label": "Brouillon de relance non envoye",
            "reason": "Le texte copiable reste local tant qu'aucun envoi externe n'est note.",
            "status_label": "Exclu",
        },
        {
            "label": "Chemin et piece brute ascenseur",
            "reason": "Les references privees sont remplacees par un libelle fictif sans chemin local.",
            "status_label": "Masque",
        },
        {
            "label": "Synthese action ascenseur",
            "reason": "Peut sortir si elle garde le watermark et mentionne la preuve manquante.",
            "status_label": "A verifier",
        },
    ],
    "required_proofs": [
        {"label": "Date d'envoi", "status": "missing"},
        {"label": "Canal et destinataire", "status": "missing"},
        {"label": "Note de suivi", "status": "to_fill"},
    ],
    "confidentiality_checks": [
        {"status": "OK", "label": "Aucun chemin local affiche"},
        {"status": "OK", "label": "Export derive seulement"},
        {"status": "WARN", "label": "Preuve d'envoi absente"},
        {"status": "BLOCKED", "label": "Brut ascenseur bloque"},
    ],
    "format_impact": [
        {"id": "txt", "label": "TXT verrouille", "enabled": False},
        {"id": "json", "label": "JSON audit", "enabled": True},
        {"id": "markdown", "label": "Markdown", "enabled": False},
        {"id": "clipboard", "label": "Presse-papier", "enabled": False},
    ],
    "actions": {
        "download": {
            "label": "Telecharger export derive",
            "enabled": False,
            "disabled_reason": "Relance ascenseur non tracee",
        },
        "record_external_send": {
            "label": "Noter l'envoi hors CoproScope",
            "href": "/demandes/relance?request_id=REQ-FICTIF-ASCENSEUR-SYNDIC",
        },
        "exclude_from_pack": {
            "label": "Exclure cette relance du pack",
            "href": "/exports/passation?exclude=BLOCK-FICTIF-RELANCE-ASCENSEUR",
        },
        "back_preview": {"label": "Retour apercu", "href": "/exports/passation"},
        "view_action": {"label": "Voir action", "href": "/actions/ACTION-FICTIF-ASC-2025"},
    },
}
```

## Interactions

| Interaction | Attente utilisateur | Resultat attendu | No-go |
| --- | --- | --- | --- |
| Ouvrir un blocage depuis l'apercu | Comprendre la raison precise. | Page detail avec raison, risque et action sure. | Notice generique `export bloque`. |
| Noter l'envoi hors CoproScope | Tracer une relance deja faite ailleurs. | Ouvre la relance avec demande/action preselectionnee, date, canal, destinataire et note. | Envoi automatique ou confirmation sans journal. |
| Exclure cette relance du pack | Continuer la passation sans ambiguite. | Retour apercu avec l'element marque exclu et motif visible. | Disparition silencieuse du blocage. |
| Retour apercu | Revenir a la revue avant telechargement. | Conserve token, scope, selected et position si possible. | Perte du contexte export. |
| Voir action | Inspecter le point de travail lie. | Ouvre la fiche action token-safe. | Affichage d'un ID prive ou d'un chemin local. |
| Telecharger export derive verrouille | Comprendre pourquoi le bouton est inactif. | Bouton desactive avec raison lisible. | Telechargement direct malgre blocage. |

## Etats vides

- Blocage introuvable: afficher `Blocage introuvable`, ne pas echo l'ID brut si
  l'ID ressemble a un chemin local, proposer `Retour apercu` et `Voir actions
  ouvertes`.
- Blocage deja corrige: afficher `Blocage corrige`, montrer la trace de
  correction, proposer `Retour apercu` et formats redevenus disponibles.
- Aucune preuve attendue: afficher `Aucune preuve supplementaire requise`,
  garder la revue confidentialite visible.
- Action liee absente: afficher `Action liee introuvable`, proposer la liste
  des actions ouvertes sans 500.
- Token absent ou invalide: refuser l'acces via le comportement securise
  existant, sans apercu partiel.

## Criteres d'acceptation

- La page affiche `Detail blocage export` et le titre du blocage.
- Le premier fold montre la raison du blocage, le risque et l'action sure.
- Le blocage distingue clairement: exclu, masque, a verifier.
- La page explique qu'aucun envoi automatique n'est fait par CoproScope.
- `Telecharger export derive` reste verrouille tant que le blocage est actif.
- `Noter l'envoi hors CoproScope` conserve demande/action/evenement et token.
- `Exclure cette relance du pack` rend l'exclusion motivee, pas silencieuse.
- `Retour apercu` conserve token, scope et selected.
- Le watermark derive et `source_of_truth: false` restent visibles ou testables.
- Aucun chemin local, `raw`, `restricted`, `logs`, `file://`, email reel, PDF
  brut ou payload source n'apparait dans HTML, attributs ou exports.
- Les references fictives restent marquees `FICTIF`.
- Mobile: la colonne decision passe sous la preuve attendue; aucun bouton n'est
  tronque.
- Clavier: tous les CTA sont focusables avec noms accessibles.

## Tests attendus

Depuis `C:\Users\brice\CoproScope\coproscope\server`:

```powershell
.\.venv\Scripts\python.exe -m unittest tests.test_ui_passation_export_route tests.test_ui_security_routes tests.test_ui_action_detail_route tests.test_ui_requests_route tests.test_ui_smoke_routes_expanded -v
```

Ajouter ou completer:

- `test_passation_blocker_detail_route_200`
- `test_passation_blocker_detail_lists_reason_exclusions_and_required_proofs`
- `test_passation_blocker_detail_download_is_locked`
- `test_passation_blocker_detail_links_are_token_safe`
- `test_passation_blocker_detail_preserves_scope_and_selected`
- `test_passation_blocker_detail_unknown_id_has_safe_empty_state`
- `test_passation_blocker_detail_masks_private_path_like_ids`
- `test_passation_blocker_detail_no_private_path_or_raw_leak`
- `test_passation_blocker_detail_source_of_truth_false`

## Commande dev prete

```text
Role: dev CoproScope cycle N+3.
Objectif: livrer le detail d'un blocage d'export passation, conforme au PNG:
C:\Users\brice\CoproScope\coproscope\docs\assets\ux-visuels-fictifs-2026-05-21\11_detail_blocage_export_n2.png

Route: /exports/passation/blocages/{blocker_id} ou /exports/passation?blocker={blocker_id}.
ID demo: BLOCK-FICTIF-RELANCE-ASCENSEUR.

Structure: sidebar Exports active, topbar Detail blocage export, compteurs
Inclus/A verifier/Bloques/Formats/Watermark, colonne raison du blocage et
exclusions, colonne controle confidentialite + preuves attendues, colonne
decision avant export.

Composants: blocker breadcrumb, blocker summary, status grid, excluded items,
decision timeline, confidentiality checks, required proof, decision panel,
format impact, actions.

Donnees necessaires: model.ux.passation_export_blocker_detail avec context,
summary, blocker, excluded_items, required_proofs, confidentiality_checks,
format_impact et actions token-safe.

Interactions: ouvrir blocage depuis apercu, noter l'envoi hors CoproScope,
exclure du pack, retour apercu, voir action, telechargement verrouille avec
raison.

Etats vides: blocage introuvable, blocage deja corrige, aucune preuve attendue,
action liee absente, token absent/invalide.

Criteres d'acceptation: raison visible, risque visible, action sure visible,
exclusions motivees, download verrouille, token/scope/selected conserves,
source_of_truth false, watermark derive, aucune fuite raw/restricted/logs/file
ou chemin local, mobile lisible, clavier OK.

Tests attendus:
.\.venv\Scripts\python.exe -m unittest tests.test_ui_passation_export_route tests.test_ui_security_routes tests.test_ui_action_detail_route tests.test_ui_requests_route tests.test_ui_smoke_routes_expanded -v
```

## Limites designer

- Cette commande ne modifie pas l'application.
- Le wording exact peut etre aligne par le dev front avec le registre de langage
  novice si un owner front est declare.
- Les noms de routes peuvent etre adaptes si le routeur prefere un query-param,
  mais le comportement utilisateur et les tests anti-fuite doivent rester
  equivalents.
