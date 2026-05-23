# Visuels fictifs - cycle suivant - 2026-05-21

Role: designer de service visuel.
Perimetre: vues manquantes a tester avec donnees privees fictives, sans donnee reelle.
Reference UX: captures Canva / enquete utilisateur, densite cockpit conseil syndical, cartes d'action utiles, langage novice.

Tous les visuels sont des PNG 1672 x 941 dans `docs/assets/ux-visuels-fictifs-2026-05-21/`.

## 1. Toutes les actions en retard

PNG: `docs/assets/ux-visuels-fictifs-2026-05-21/01_toutes_actions_en_retard.png`

Intention de test: le membre CS clique sur `Actions en retard` et doit voir une liste priorisee, puis comprendre quoi faire sur chaque ligne: relancer, demander une piece, ajouter une preuve, ouvrir le detail.

Commande dev associee: livrer `/actions?priority=P1` comme vue stable avec compteurs, liste triee, panneau de detail selectionne, actions `Preparer relance syndic`, `Ajouter une preuve`, `Ouvrir detail action`, export liste tokenise.

## 2. Pieces manquantes

PNG: `docs/assets/ux-visuels-fictifs-2026-05-21/02_pieces_manquantes.png`

PNG N+2 corrige: `docs/assets/ux-visuels-fictifs-2026-05-21/07_pieces_manquantes_n2.png`

PNG N+2 prioritaire apres retour novice: `docs/assets/ux-visuels-fictifs-2026-05-21/09_pieces_manquantes_n2_liste_coherente.png`

Intention de test: le membre CS doit comprendre quelle piece manque, pourquoi elle compte, et transformer la piece manquante en demande syndic ou preuve rattachee.

Commande dev associee: livrer `/pieces?proof=missing` avec rubriques, pieces attendues, motif novice, rattachement a demande/action, filtre `prive fictif`, boutons `Demander`, `Relancer`, `Ajouter`, `Question`.

Retour novice: la relance est validee, mais `Pieces manquantes` est refusee si
la liste semble vide ou incoherente. La page doit donc afficher des cartes
remplies avec `Pourquoi`, `Detenteur`, `Lien action/compte`, `Relancer syndic`
et `Ajouter reponse recue`.

Attentes bouton par bouton N+2:

- `Creer demandes syndic`: prepare un recapitulatif de demandes, sans envoi automatique.
- `Voir pieces privees`: filtre les pieces restreintes avec raison lisible.
- `Demander`: ouvre une demande syndic pre-remplie pour la piece absente.
- `Relancer`: ouvre une relance copiable avec historique et canal.
- `Ajouter`: ouvre le depot/rattachement sur la piece attendue.
- `Ajouter reponse recue`: rattache une reponse syndic recue hors outil, en preuve candidate a verifier.
- `Ouvrir action` / `Ouvrir compte`: garde le contexte et ouvre le lien metier correspondant.
- `Question`: prepare une question syndic neutre rattachee au point concerne.

## 3. Relance syndic

PNG: `docs/assets/ux-visuels-fictifs-2026-05-21/03_relance_syndic.png`

Intention de test: le membre CS choisit une demande, lit un brouillon prudent, le copie hors CoproScope, puis trace date/canal sans envoi automatique.

Commande dev associee: livrer `/actions?scope=syndic` ou `/demandes?status=waiting` avec selection de demande, brouillon copiable, garde-fou aucun envoi automatique, champs `date`, `canal`, `piece attendue`, historique et validation confidentialite.

## 4. Detail action

PNG: `docs/assets/ux-visuels-fictifs-2026-05-21/04_detail_action.png`

PNG N+2 corrige: `docs/assets/ux-visuels-fictifs-2026-05-21/08_detail_action_n2.png`

Intention de test: depuis une ligne en retard, le membre CS ouvre une fiche unique qui explique le contexte, l'etat, les preuves, les pieces liees, la relance et la note de passation.

Commande dev associee: livrer `/actions/{id}` ou une route detail equivalente avec onglets `Action`, `Preuves`, `Pieces liees`, `Relance syndic`, `Historique`, `Passation`; chaque onglet doit avoir un etat vide utile et une action possible.

Attentes bouton par bouton N+2:

- `Retour aux retards`: revient a `/actions?priority=P1` sans perdre token ni filtre.
- `Exporter fiche`: ouvre un apercu derive avec inclus/exclus et biffage avant telechargement.
- `Cloturer si preuve OK`: reste bloque tant que la preuve finale manque.
- `Preparer relance`: prepare un brouillon copiable, sans envoi automatique.
- `Ajouter preuve` / `Deposer preuve`: ouvre le depot avec l'action deja selectionnee.
- `Changer statut` / `Marquer attente`: journalise le changement avec date, canal ou responsable.
- `Copier brouillon`: copie le texte et rappelle de tracer l'envoi externe.
- `Tracer envoi`: enregistre date, canal, destinataire et prochaine verification.

## 5. Detail evenement memoire

PNG: `docs/assets/ux-visuels-fictifs-2026-05-21/05_detail_evenement_memoire.png`

Intention de test: un nouveau membre CS comprend l'histoire d'un evenement sensible, voit les documents lies, sait ce qui reste ouvert et ce qui peut etre transmis.

Commande dev associee: livrer `/chantiers/{event_id}` ou equivalent memoire avec timeline detaillee, documents rattaches, restrictions, note de passation, actions `Creer action de relance`, `Ajouter document`, `Exporter cet evenement`.

## 6. Export passation

PNG: `docs/assets/ux-visuels-fictifs-2026-05-21/06_export_passation.png`

Intention de test: avant export, le membre CS voit ce qui est inclus, ce qui est exclu, les controles de confidentialite et le rappel que l'export est derive, non source de verite.

Commande dev associee: livrer `/exports/passation` comme apercu HTML avant telechargement, avec sections incluses/exclues, controle confidentialite, formats TXT/JSON/Markdown tokenises, watermark derive, absence de chemins locaux et de bruts prives.

PNG N+2 livre: `docs/assets/ux-visuels-fictifs-2026-05-21/10_export_passation_n2_apercu_verifiable.png`

Retour de cycle: l'apercu passation est livre. Le prochain besoin utile n'est
plus de repeter l'export global, mais de rendre chaque blocage explicable et
actionnable pour le membre CS novice.

## 7. Detail blocage export

PNG N+3: `docs/assets/ux-visuels-fictifs-2026-05-21/11_detail_blocage_export_n2.png`

HTML source: `docs/assets/ux-visuels-fictifs-2026-05-21/11_detail_blocage_export_n2.html`

Commande dev associee: `docs/commandes/commande_cycle_n3_detail_blocage_export_2026-05-21.md`

Intention de test: depuis `Elements exclus ou bloques`, le membre CS ouvre un
blocage et comprend pourquoi le telechargement est verrouille, ce qui reste
local, quelle preuve manque, et quelle action est sure: noter l'envoi hors
CoproScope, exclure l'element du pack, revenir a l'apercu ou voir l'action liee.

Attentes bouton par bouton:

- `Noter l'envoi hors CoproScope`: ouvre la relance avec demande/action
  preselectionnee, date, canal, destinataire et note obligatoire.
- `Exclure cette relance du pack`: revient a l'apercu avec exclusion motivee,
  jamais une disparition silencieuse.
- `Retour apercu`: conserve token, scope et selected.
- `Voir action`: ouvre la fiche action liee sans fuite d'identifiant prive.
- `Telecharger export derive - verrouille`: reste inactif tant que la preuve
  d'envoi manque et affiche la raison.

## Donnees fictives utilisees pour les tests

- `REQ-FICTIF-ASSURANCE-B12`: demande d'attestation assurance lot B12 fictif.
- `DOC-FICTIF-B12-ASSUR`: piece administrative fictive rattachee.
- `DOC-FICTIF-SYNDIC-ASSUR`: reponse syndic fictive attendue ou a biffer.
- `DOC-FICTIF-C31-INFILT`: signalement infiltration cave C31 fictif.
- `BLOCK-FICTIF-RELANCE-ASCENSEUR`: blocage fictif d'export lie a une relance
  ascenseur non tracee.
- `ACTION-FICTIF-ASC-2025`: action fictive reliee au blocage export.

## Prochaine commande globale

Demarrer le bloc N+2 par `/pieces?proof=missing`, avec le PNG prioritaire `09_pieces_manquantes_n2_liste_coherente.png`, puis raccorder le detail action `/actions/{id}` ou equivalent. La passation complete est documentee dans `docs/coordination_cycle_n2_pieces_detail_2026-05-21.md`.

Commande dev prete: livrer les cartes remplies `Pieces manquantes` a partir du PNG N+2 prioritaire, conserver le token local, ne jamais envoyer automatiquement de message, afficher pourquoi/detenteur/lien comptes-action, distinguer piece manquante / preuve candidate / preuve finale, et relancer depuis `server/`:

```powershell
.\.venv\Scripts\python.exe -m unittest tests.test_ui_pieces_viewmodel tests.test_ui_action_detail_route tests.test_ui_registre_actions tests.test_ui_smoke_routes_expanded -v
```
