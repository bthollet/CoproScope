# Commande cycle N+2 - Detail evenement memoire

> Statut gouvernail: `SPEC_DERIVEE`.
> La source de verite roadmap est `docs/roadmap_backlog_central.md`.
> Executer seulement via un `RM-*` et un `CH-*` actifs.

Date: 2026-05-21.

Role cible: dev CoproScope cycle N+2.

Perimetre: livrer le detail d'un evenement memoire depuis la cible UX
enquete, pas depuis l'ancien produit. Ne pas modifier l'intention de
`Memoire de copropriete`: timeline centrale, passation CS, documents a
transmettre et restrictions lisibles.

Image cible designer:

- `C:\Users\brice\CoproScope\coproscope\docs\assets\ux-visuels-fictifs-2026-05-21\05_detail_evenement_memoire_n2.png`
- Source HTML rendable:
  `C:\Users\brice\CoproScope\coproscope\docs\assets\ux-visuels-fictifs-2026-05-21\05_detail_evenement_memoire_n2.html`

Reference UX d'enquete:

- `C:\Users\brice\CoproScope\coproscope\docs\assets\etude-utilisateurs\memoire-copropriete.png`

## Objectif utilisateur

Un nouveau membre de conseil syndical ouvre un evenement sensible depuis la
timeline de memoire et doit comprendre, sans aide:

- ce qui s'est passe;
- quelles preuves existent;
- quelle preuve manque encore;
- ce qui doit etre repris par le nouveau CS;
- ce qui peut etre transmis, masque ou bloque.

Phrase de reussite novice:

> Je comprends l'infiltration C31, je vois l'assurance B12 a relancer, je sais
> que le PV AG est la source diffusable, et je ne transmets pas la note syndic
> ou les photos brutes sans verification.

## Route cible

Route recommandee:

- `/chantiers/{event_id}`

Route equivalente acceptee si le routeur impose un detail query-param:

- `/chantiers?selected={event_id}`

Identifiant demo:

- `EVT-FICTIF-C31-INFILT-ASSURANCE`

Tous les liens internes doivent conserver le token UI existant quand la route
est protegee.

## Structure visuelle

Reprendre la grammaire de l'image enquete `Memoire de copropriete`:

- sidebar sombre avec `Memoire copro` active;
- topbar compacte avec recherche et badge `Donnees fictives privees`;
- barre d'actions: `Retour a la memoire`, `Preparer version diffusable`,
  `Creer action de relance`;
- grande fiche evenement a gauche;
- colonne droite `Passation CS`, `Documents lies`, `Version transmissible`;
- fil vertical de l'evenement avec dates, statuts, badges, documents et actions.

Le detail ne doit pas redevenir une page technique de chantier ou un tableau
documentaire. Il doit rester une fiche de memoire transmissible.

## Composants attendus

- `memory-event-detail-shell`
- `memory-event-header`
- `memory-event-status-strip`
- `memory-event-timeline`
- `memory-event-timeline-row`
- `memory-event-handover-note`
- `memory-event-restriction-note`
- `memory-event-passation-card`
- `memory-event-linked-documents`
- `memory-event-transmission-review`
- `memory-event-actions`

Noms CSS libres, mais les tests doivent pouvoir cibler des regions stables par
`data-testid` ou roles accessibles.

## Donnees fictives privees

Utiliser uniquement des donnees de copro fictive:

```python
model.ux.memoire.selected_event = {
    "id": "EVT-FICTIF-C31-INFILT-ASSURANCE",
    "title": "Infiltration C31 - suivi assurance B12",
    "category": "Sinistre",
    "status_label": "Sinistre ouvert",
    "date_label": "03 mars 2025",
    "owner_label": "Nadia L. fictive",
    "next_action": "Relancer le syndic et demander le retour assureur avant le 24 mai 2026.",
    "proof_status": "Preuve finale manquante",
    "diffusion_label": "CS seulement en brut. Coproprietaires: version masquee et derivee.",
    "handover_note": "Transmettre le resume, le PV AG et l'etat assurance B12. Dire clairement que la preuve finale manque.",
    "restriction_note": "Masquer noms, photos de cave C31 et commentaire brut syndic. Export derive seulement.",
    "timeline": [
        {
            "date_label": "03 mars 2025",
            "title": "Infiltration C31 signalee",
            "body": "Photo et constat DOC-FICTIF-C31-INFILT ajoutes au coffre local.",
            "restriction": "Photos brutes privees",
            "document_id": "DOC-FICTIF-C31-INFILT",
        },
        {
            "date_label": "08 mars 2025",
            "title": "Assurance B12 demandee",
            "body": "REQ-FICTIF-ASSURANCE-B12 creee pour obtenir attestation, declaration et retour assureur.",
            "action_id": "REQ-FICTIF-ASSURANCE-B12",
        },
        {
            "date_label": "10 avril 2025",
            "title": "PV AG rattache au sinistre",
            "body": "PV AG 2024: mandat pour suivi assurance et devis de reprise.",
            "document_id": "DOC-FICTIF-PV-AG-2024-C31",
        },
        {
            "date_label": "21 mai 2026",
            "title": "Note syndic recue hors outil",
            "body": "Note syndic: visite technique annoncee, mais aucun justificatif final.",
            "document_id": "DOC-FICTIF-NOTE-SYNDIC-C31",
        },
    ],
    "linked_documents": [
        {
            "label": "Signalement infiltration C31",
            "type": "IMG",
            "diffusion": "brut bloque",
            "reason": "photos privees de cave C31",
        },
        {
            "label": "Assurance B12 attendue",
            "type": "REQ",
            "diffusion": "a relancer",
            "reason": "preuve finale manquante",
        },
        {
            "label": "PV AG du 10/04/2025",
            "type": "PDF",
            "diffusion": "diffusable apres masquage",
            "reason": "source de mandat",
        },
        {
            "label": "Note syndic 21/05/2026",
            "type": "TXT",
            "diffusion": "a verifier",
            "reason": "reponse hors outil non prouvee",
        },
    ],
}
```

Les libelles obligatoires visibles quelque part dans la route:

- `infiltration C31`
- `assurance B12`
- `PV AG`
- `note syndic`

## Interactions

| Interaction | Attente avant clic | Resultat attendu | No-go |
| --- | --- | --- | --- |
| `Retour a la memoire` | Revenir a la timeline source. | Retourne a `/chantiers` avec filtres, periode et token conserves. | Retour dashboard ou perte du filtre. |
| `Preparer version diffusable` | Voir ce qui sera masque avant partage. | Ouvre une revue: inclus, exclus, masquages, public cible. | Telechargement direct sans revue. |
| `Creer action de relance` | Transformer l'evenement ouvert en action concrete. | Cree ou ouvre une action pre-remplie: relance syndic, assurance B12, echeance, preuve attendue. | Action generique sans lien evenement. |
| `Ajouter document` | Ajouter une preuve candidate au bon evenement. | Ouvre depot/rattachement avec evenement selectionne et diffusion a choisir. | Depot generique sans contexte. |
| `Exporter cet evenement` | Produire un extrait de passation. | Ouvre apercu derive avec source_of_truth false, omissions et restrictions. | Export brut ou source collaborative. |
| `Voir document` | Inspecter une piece rattachee. | Ouvre le detail document token-safe, sans chemin local brut. | Fuite de chemin `raw`, `restricted`, `file://` ou absolu local. |
| `Demander assurance B12` | Relancer la preuve manquante. | Ouvre brouillon copiable ou demande syndic, sans envoi automatique. | Envoi implicite ou statut marque envoye. |
| `Verifier note syndic` | Controler une note recue hors outil. | Ouvre fiche de verification avec date, canal, auteur declare et preuve attendue. | Note consideree comme preuve finale. |

## Etats vides

- Evenement introuvable: afficher `Evenement introuvable`, retour
  `Retour a la memoire`, lien `Voir les sujets ouverts`, pas de 500.
- Aucun document lie: afficher `Aucun document rattache a cet evenement`, CTA
  `Ajouter document`, rappel que l'evenement reste dans la memoire.
- Aucune restriction: afficher un etat positif `Aucune restriction identifiee`
  et garder la revue de diffusion accessible.
- Aucune action ouverte: afficher `Aucune action ouverte`, CTA
  `Creer action de relance` si l'evenement n'est pas clos.
- Export bloque: afficher la raison, les pieces bloquantes et le lien vers la
  revue de diffusion; aucun telechargement direct.

## Criteres d'acceptation

- La route affiche `Detail evenement memoire` et le titre evenement.
- La route ressemble a une extension directe de `Memoire de copropriete`:
  sidebar, topbar, fiche centrale, passation et transmission.
- Le detail relie preuves, actions, documents, restrictions et note de
  passation.
- Les donnees fictives obligatoires apparaissent: infiltration C31, assurance
  B12, PV AG, note syndic.
- La prochaine action est visible dans le premier fold.
- Le statut de diffusion distingue brut CS, version masquee et export derive.
- `Creer action de relance` conserve le lien vers l'evenement memoire.
- Les documents bruts sensibles sont marques bloques avant export.
- L'export de cet evenement est derive et `source_of_truth` reste false.
- Aucun chemin prive, email prive, payload brut, `raw`, `restricted`, `logs` ou
  chemin absolu local ne fuit dans HTML, data attributes ou exports.
- La page est utilisable au clavier: focus visible, titres regions, boutons
  accessibles et libelles non tronques.
- Mobile/tablette: la colonne droite passe sous la fiche sans masquer les CTA ni
  couper les libelles critiques.

## Tests attendus

Depuis `C:\Users\brice\CoproScope\coproscope\server`:

```powershell
.\.venv\Scripts\python.exe -m unittest tests.test_ui_memoire tests.test_ui_passation_export_route tests.test_ui_security_routes tests.test_ui_smoke_routes_expanded -v
```

Ajouter ou completer des tests si les noms ci-dessous n'existent pas encore:

- `test_memory_event_detail_route_200`
- `test_memory_event_detail_contains_required_private_fictive_labels`
- `test_memory_event_detail_links_are_token_safe`
- `test_memory_event_detail_no_private_path_leak`
- `test_memory_event_detail_export_is_derived_not_source_of_truth`
- `test_memory_event_detail_empty_state_not_found`
- `test_memory_event_detail_accessible_buttons`

## Commande dev prete

```text
Role: dev CoproScope cycle N+2.
Objectif: livrer le detail evenement memoire depuis la cible UX enquete, en
suivant le PNG:
C:\Users\brice\CoproScope\coproscope\docs\assets\ux-visuels-fictifs-2026-05-21\05_detail_evenement_memoire_n2.png

Route: /chantiers/{event_id} ou /chantiers?selected={event_id}.
ID demo: EVT-FICTIF-C31-INFILT-ASSURANCE.

Structure: sidebar Memoire active, topbar recherche + donnees fictives privees,
fiche centrale evenement, status strip action/diffusion/preuve, timeline de
l'evenement, colonne droite Passation CS, Documents lies, Version
transmissible.

Donnees fictives obligatoires: infiltration C31, assurance B12, PV AG, note
syndic. Ne jamais utiliser de donnees reelles.

Interactions obligatoires: Retour a la memoire, Preparer version diffusable,
Creer action de relance, Ajouter document, Exporter cet evenement, Voir
document, Demander assurance B12, Verifier note syndic.

Garde-fous: token conserve, aucun envoi automatique, export derive avec
source_of_truth false, bruts C31 bloques, note syndic a verifier, aucun chemin
raw/restricted/logs/file:// ou absolu local dans HTML/export.

Etats vides: evenement introuvable, aucun document lie, aucune restriction,
aucune action ouverte, export bloque.

Tests depuis server/:
.\.venv\Scripts\python.exe -m unittest tests.test_ui_memoire tests.test_ui_passation_export_route tests.test_ui_security_routes tests.test_ui_smoke_routes_expanded -v

Acceptation: un membre CS novice comprend l'histoire, la preuve disponible, la
preuve manquante, la prochaine relance, et ce qui est transmissible ou bloque
sans lire la documentation.
```

## Risques a surveiller

- Confusion entre memoire et stockage documentaire si la page devient une liste
  de fichiers.
- Confusion entre export derive et source de verite collaborative.
- Fuite de donnees privees si les photos C31, la note syndic brute ou les
  chemins locaux apparaissent.
- Bouton `Creer action de relance` trop generique s'il ne transporte pas
  evenement, piece attendue, echeance et preuve manquante.
- Retour utilisateur perdu si `/chantiers` ne conserve pas filtres et periode.
