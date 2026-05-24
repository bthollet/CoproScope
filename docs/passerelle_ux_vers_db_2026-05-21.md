# Passerelle UX vers DB - Besoins au 2026-05-21

## Synthese pour le fil DB

La refonte UX repart des visuels d'enquete utilisateur. L'utilisateur cible est un membre de conseil syndical novice: il ne pense pas en tables, modules ou pipelines. Il veut savoir quoi faire maintenant, pourquoi, avec quelle preuve, et ce qu'il peut transmettre sans risque.

Le fil UX livre des ecrans reels en cycles decales:
- Cycle N-1: QA et membre CS testent une route livree.
- Cycle N: front/back developpent la commande validee.
- Cycle N+1/N+2: designer prepare ou teste le prochain visuel image.

La DB doit soutenir ce cycle avec des donnees stables, reliees et filtrables, sans exposer les chemins ou sources privees.

## Source de verite cote UI

Les templates ne doivent pas parler directement aux tables. Ils consomment:

- `model.ux.registre`
- `model.ux.pieces`
- `model.ux.comptes`
- `model.ux.memoire`
- `model.ux.priority_views`
- `model.kpis`
- `model.action_items`

Le schema DB doit donc etre pense comme un socle evenementiel/metier qui alimente ces projections.

## Entites metier attendues

### Copro / instance

- Identifiant instance/coffre.
- Nom affichable.
- Annee de travail.
- Regles locales de confidentialite.
- Aucune route UI ne doit exposer de chemin local brut.

### Document / piece

Champs publics utiles:
- `doc_id`
- `display_name`
- `document_type`
- `domain`
- `period`
- `classification_status`
- `privacy_status`
- `diffusion_label`
- `proof_role`
- `expected_from`
- `holder_label`
- `received_on`
- `href_public`

Champs prives a isoler:
- chemin raw;
- chemin restricted;
- logs OCR;
- contenu integral non biffe;
- mapping local absolu.

### Decision / resolution

Champs publics utiles:
- `decision_id`
- `resolution_ref`
- `title`
- `decision_summary`
- `ag_date`
- `source_doc_id`
- `status`
- `diffusion_status`
- `open_action_count`

Relations attendues:
- decision -> actions;
- decision -> documents sources;
- decision -> preuves;
- decision -> evenements memoire.

### Action

Champs publics utiles:
- `action_id`
- `title`
- `source_module`
- `source_ref`
- `domain`
- `owner_label`
- `status`
- `priority`
- `due_on`
- `next_step`
- `proof_expected`
- `diffusion_label`
- `is_late`
- `href_public`

Relations attendues:
- action -> decision;
- action -> piece attendue;
- action -> preuve recue;
- action -> demande syndic;
- action -> relance;
- action -> evenement memoire.

### Demande / relance syndic

Champs publics utiles:
- `request_id`
- `subject`
- `recipient_label`
- `channel_label`
- `status`
- `created_on`
- `due_on`
- `last_followup_on`
- `message_draft`
- `linked_action_id`
- `linked_piece_id`

Important UX:
- le bouton visible doit faire comprendre que la relance est enregistree fictivement/localement;
- aucun envoi reel ne doit etre implique sans action explicite future.

### Controle comptes / anomalie

Champs publics utiles:
- `control_id`
- `severity`
- `vendor_label`
- `amount_label`
- `period`
- `question_label`
- `expected_piece_label`
- `linked_action_id`
- `linked_request_id`
- `status`

Relations attendues:
- anomalie -> action comptable;
- anomalie -> piece attendue;
- anomalie -> demande syndic;
- anomalie -> preuve recue.

### Memoire copropriete / passation

Champs publics utiles:
- `event_id`
- `date_label`
- `title`
- `summary`
- `status`
- `open_topic_count`
- `linked_doc_ids`
- `linked_action_ids`
- `handover_note`

Relations attendues:
- evenement -> documents;
- evenement -> actions;
- evenement -> preuves;
- evenement -> export passation derive.

## Questions UX ouvertes pour le fil DB

### UXDB-20260521-01 - Identite stable des actions

- Bloc UX: detail action.
- Route/ecran: `/actions/{action_id}` puis `/actions?selected=...`.
- Besoin utilisateur: cliquer une carte et retrouver toujours la meme fiche.
- Projection attendue: `model.action_items[*].id` et `model.ux.registre.items[*].id` doivent etre stables.
- Donnees minimales: ID public stable, source interne, statut, titre, preuve attendue.
- Donnees privees a ne jamais exposer: chemin source brut, chemin OCR, chemin local absolu.
- Reponse attendue du fil DB: choisir la strategie d'ID public stable entre hash metier, UUID, ou cle composite versionnee.

### UXDB-20260521-02 - Piece manquante comme objet de travail

- Bloc UX: pieces manquantes.
- Route/ecran: `/pieces?proof=missing`.
- Besoin utilisateur: voir quoi demander, a qui, pourquoi, depuis quel controle, et quoi faire si la piece arrive.
- Projection attendue: `model.ux.pieces.missing_items`.
- Donnees minimales: piece attendue, detenteur, raison, priorite, action liee, demande liee, depot possible.
- Donnees privees a ne jamais exposer: emplacement local, contenu non biffe, source raw.
- Reponse attendue du fil DB: faut-il une table `expected_pieces` separee de `documents`, ou un statut document attendu dans une table unique?

### UXDB-20260521-03 - Journal local des relances

- Bloc UX: relance syndic.
- Route/ecran: `/demandes/relance`.
- Besoin utilisateur: preparer/copier une relance puis enregistrer localement ce qui a ete fait.
- Projection attendue: `model.ux.priority_views.syndic_followups` et vue demandes.
- Donnees minimales: brouillon, canal, destinataire, action/piece liee, horodatage, statut fictif/local.
- Donnees privees a ne jamais exposer: email personnel, piece jointe brute, chemin local.
- Reponse attendue du fil DB: schema de journal d'evenements compatible avec un futur envoi reel, sans le promettre maintenant.

### UXDB-20260521-04 - Export passation derive

- Bloc UX: export passation.
- Route/ecran: `/exports/passation.*`.
- Besoin utilisateur: transmettre une synthese exploitable sans livrer les sources privees.
- Projection attendue: contrat derive filtrant raw/restricted/logs/private.
- Donnees minimales: dossiers, sujets ouverts, preuves diffusable, limites, date de generation.
- Donnees privees a ne jamais exposer: raw, restricted, logs, chemins absolus, notes privees non biffees.
- Reponse attendue du fil DB: separation nette entre source, derive diffusable, et audit interne.

## Donnees fictives privees a maintenir

Le designer peut creer de fausses donnees privees pour tester:
- facture fictive ascenseur;
- attestation assurance fictive B12;
- PV AG fictif;
- relance syndic fictive;
- note infiltration C31 fictive;
- anomalie comptable fictive;
- piece administrative fictive a demander.

Ces donnees doivent etre marquees demo/fictives et ne jamais devenir des exemples ambigus.

## Tests UI qui doivent rester verts apres choix DB

- `server.tests.test_ui_action_detail_route`
- `server.tests.test_ui_pieces_viewmodel`
- `server.tests.test_ui_requests_route`
- `server.tests.test_ui_registre_actions`
- `server.tests.test_ui_comptes_guide`
- `server.tests.test_ui_live_ux_contract`
- Suite UI complete: `server/tests/test_ui_*.py`

Dernier resultat connu: `150 tests OK`.
