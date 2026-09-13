# Journal cycles UX - 2026-05-21

> Statut gouvernail: `JOURNAL_TRACE`.
> La source de verite roadmap est `docs/roadmap_backlog_central.md`
> (`RM-2026-0006`). Ce journal garde la trace, il ne decide plus des priorites.

## Cadre

- Methode: cycle double flux `enquete sur image -> commande dev -> dev -> test produit livre -> corrections`.
- Decalage permanent:
  - Cycle N-1: test QA + membre CS novice sur route livree.
  - Cycle N: dev front/back sur commande validee.
  - Cycle N+1: designer de service + designer visuel/data preparent l'image, l'enquete et la commande suivante.
- Regle de coordination: aucun test d'intention abstraite, uniquement une route ou un ecran livre; aucun dev ne demarre sans commande; aucun visuel manquant n'est invente directement par les devs.

## Point 07:31 CET

### A tester maintenant

- Serveur cible: `http://127.0.0.1:8766/?token=local-secret`.
- Ecran observe cote utilisateur: `/actions?token=local-secret`.
- Tests live prioritaires: `/demandes`, `/documents/ajouter`, `/depot`, `/actions?priority=P1`.
- Donnees privees fictives disponibles pour scenario novice:
  - demande attestation assurance lot B12;
  - reponse syndic avec piece assurance fictive;
  - signalement infiltration cave C31;
  - documents et registres marques `FICTIF`, utilisables sans donnees personnelles reelles.

### En dev maintenant

- Bloc P0: demandes/depot.
- Front attendu: formulaire ou CTA utile, libelles novice, ecran sans cul-de-sac.
- Back attendu: creation demande persistante, token conserve, registre coherent, exports accessibles depuis la session locale.
- Risque: tests verts precedents non valables tant que les nouveaux changements P0 ne sont pas relances.

### En enquete maintenant

- Designer de service: conduire le membre CS novice sur l'attendu naturel: "je cree une demande", "je rattache une preuve", "je vois quoi faire ensuite".
- Designer visuel/data: preparer les images du prochain bloc avec faux documents administratifs exploitables par le test.
- Membre CS novice: tester uniquement la route livree, pas la maquette.

### Commande prete

- `docs/commandes_reprise_live_8766.md`.
- Prochaine commande a expliciter apres P0: master-detail `/actions` decision -> action -> preuve -> relance.

### Decision requise

- Priorite maintenue: corriger les deux NO-GO novice avant extension P1.
- Acceptation interdite sans relance de tests cibles puis suite UI complete.

### Prochain mouvement

- Relancer dev back/front P0 demandes/depot.
- Redemarrer le serveur 8766 apres changements back.
- Relancer tests cibles puis suite UI complete.
- Capturer les vues touchees comme preuves image.
- Consigner le prochain point dans ce journal.

## Tableau de flux

| Flux | Bloc | Etat | Sortie attendue |
| --- | --- | --- | --- |
| N-1 test | Cockpit/actions/comptes/memoire | GO partiel | garder les captures comme reference |
| N dev | Demandes/depot | en stabilisation P0 | routes utiles, token, creation demande, depot guide |
| N+1 enquete | Actions detail + pieces manquantes | a preparer | visuels images et commande dev |

## Agents

| Agent | Etat | Travail utile maintenant |
| --- | --- | --- |
| Designer de service | pret | guider le test novice P0 sur ecran livre |
| Designer visuel/data | actif amont | maintenir les fausses donnees privees et produire les visuels manquants |
| Membre CS novice | en attente testable | executer le scenario naturel sur `/demandes` et `/documents/ajouter` |
| Dev front | a relancer | CTA, formulaires, langage novice, responsive |
| Dev back/viewmodel | a relancer | POST demandes, registres, liens tokenises, modeles utiles |
| QA live/securite | a relancer | tests routes, token, absence fuite, captures navigateur |
| Coordinateur-scribe | actif | journaliser, signaler blocages, garder la cadence 10 minutes |

## Definition de GO P0

- `/demandes` permet de creer ou suivre une demande sans impasse.
- `/documents/ajouter` donne une action concrete de depot/rattachement.
- `/depot` conserve le token sur les exports et ne fuit pas les racines privees.
- Le membre CS novice comprend quoi faire sans vocabulaire technique.
- Les tests cibles et la suite UI complete passent apres redemarrage serveur.

## Point 08:00 CET

### A tester maintenant

- Serveur live actif: `http://127.0.0.1:8766/?token=local-secret`.
- Ecran laisse dans le navigateur: `/demandes/relance?token=local-secret&request_id=REQ-FICTIF-ASSURANCE-B12`.
- Captures reelles finales: `docs/assets/ux-livraison-reelle-2026-05-21-8766-final/`.

### Livre

- Route reelle `/demandes/relance`: brouillon de relance syndic, validation POST journalisee, copie message, pieces liees, retour demandes/actions.
- `/demandes`: creation POST locale, token conserve, sanitation chemins prives.
- `/documents/ajouter`: depot local reel via `/depot`.
- `/depot`: depot fictif visible, chemins raw masques, erreurs techniques non affichees, export zip filtre contenu et chemins.
- `/comptes`: anomalies fictives P1/P2 et questions syndic exploitables pour test novice.
- Visuels images du designer: `docs/assets/ux-visuels-fictifs-2026-05-21/`.

### Verification

- Suite UI complete apres redemarrage live: `141 tests OK`.
- Dernier redemarrage live apres POST relance: health OK, listener 8766 actif.
- Signaux navigateur captures:
  - relance: `Valider la relance` et `Copier le message`;
  - depot: `DEPOT-20260521T060000Z` visible sans `raw/_depot_ui`;
  - comptes: anomalie `SERVICES ASCENSEUR FICTIF` visible;
  - routes capturees avec token conserve.

### Prochain mouvement

- Test novice live sur `/demandes/relance`, puis correction des libelles si le sens de `Valider la relance` reste ambigu.
- Cycle suivant: pieces manquantes puis detail action avec les PNG designer N+2
  comme cible:
  `docs/assets/ux-visuels-fictifs-2026-05-21/09_pieces_manquantes_n2_liste_coherente.png`
  puis
  `docs/assets/ux-visuels-fictifs-2026-05-21/08_detail_action_n2.png`.
  Commande de passation:
  `docs/coordination_cycle_n2_pieces_detail_2026-05-21.md`.
- Ajout designer: le test novice valide la relance mais refuse
  `Pieces manquantes` si la liste n'est pas remplie/coherente. La commande dev
  priorise donc cartes remplies, raison du manque, detenteur, relance syndic,
  ajout de reponse recue, et lien comptes/action.

## Point 08:33 CET - cycle N+2 Pieces manquantes livre

### Flux decale

| Flux | Bloc | Etat | Sortie |
| --- | --- | --- | --- |
| N-1 test | Relance/depot/comptes | GO | tests live + captures conservees |
| N dev | Pieces manquantes | GO | `/pieces?proof=missing` rempli avec manques comptes |
| N+1 enquete | Detail action | pret | visuel `08_detail_action_n2.png` + route `/actions/{id}` disponible |

### Corrections livrees

- `model.ux.pieces` remonte les pieces manquantes comptables quand DocOps est vide.
- La navigation affiche `Pieces manquantes 2` et `Controle comptes 3`.
- `/actions?scope=comptes` expose les actions comptables au lieu d'un etat vide.
- La page `/pieces?proof=missing` affiche les cartes avec pourquoi, qui relancer, preuve attendue, diffusion et lien.

### Verification

- Tests cibles pieces/comptes/live/action detail: OK.
- Suite UI complete: `147 tests OK`.
- Serveur live redemarre: `8766`, PID `36804`, health OK.
- Captures: `docs/assets/ux-livraison-reelle-2026-05-21-8766-pieces-n2/`.

### Prochain mouvement

- Tester le detail action avec le membre CS novice.
- Traiter les libelles restants: `Registre des decisions`, `DocOps`, `PrivacyOps`, `P1/P2`.
- QA mobile: verifier que les cartes utiles restent accessibles sans debordement horizontal.

### Mise a jour 08:39 CET

- Correction mineure livree sur `/actions`: titre visible `Actions a traiter`.
- Traductions visibles ajoutees: `Document a verifier`, `Diffusion a arbitrer`, `Controle comptes`.
- Serveur live redemarre PID `11408`.
- Suite UI complete apres correction: `147 tests OK`.
## Point 20:40 CET - Cycle detail action livre, flux relance

- Serveur 8766 realigne apres arret de l'ancien PID `11408`; listener courant PID `12268`.
- `/actions/{id inconnu}` redirige maintenant vers `action_missing` au lieu de selectionner une fausse fiche.
- Notice mobile corrigee: structure grid, texte novice lisible, CTA visibles.
- Captures reelles ajoutees dans `docs/assets/ux-livraison-reelle-2026-05-21-8766-action-detail-live/`.
- Tests:
  - cibles action/relance/live: `13 tests OK`;
  - suite UI complete: `150 tests OK`.
- Ancienne vague agents fermee car bloquee; nouvelle vague lancee sur:
  - image detail evenement memoire;
  - projections memoire/passation;
  - front memoire/passation;
  - QA live;
  - test membre CS novice.

## Point 21:13 CET - Final cycle memoire livre, double flux passation ouvert

### Flux decale

| Flux | Bloc | Etat | Sortie |
| --- | --- | --- | --- |
| N-1 test | Actions, comptes, relance, pieces, memoire detail | EN_QA finale | `34 tests cibles OK`, captures finales et test novice sur routes reelles |
| N dev | Export passation apercu verifiable | A_LANCER | `/exports/passation` comme apercu HTML, avec liens TXT/JSON token-safe |
| N+1 enquete | Image export passation | COMMANDE_PRETE | `10_export_passation_n2_apercu_verifiable.png` + criteres de verification |

### Verification connue

- Serveur live `8766` redemarre PID `7352`, health OK.
- Suite UI complete: `155 tests OK`.
- Captures reelles: `docs/assets/ux-livraison-reelle-2026-05-21-8766-final-cycle-memoire/`.
- Corrections livrees:
  - action introuvable ne montre plus une autre fiche;
  - `/actions?scope=comptes` affiche `Points comptes a traiter avant AG`;
  - relance action sans lien GET `sent=1`, avec libelle `Noter l'envoi hors CoproScope`;
  - pieces manquantes affiche `Voir le point dans les comptes`;
  - memoire detail et introuvable routes OK;
  - `/exports/passation` redirige token-safe vers le texte.

### Commande suivante

Objectif: livrer un apercu de passation verifiable avant telechargement, en gardant le pack comme derive et non comme source de verite.

- QA + novice testent N-1: fermer les routes actions/comptes/relance/pieces/memoire/export existantes sur le live 8766.
- Front/back dev N: transformer `/exports/passation` en apercu HTML controlable, sans perdre la redirection ou les liens vers `/exports/passation.txt` et `/exports/passation.json`.
- Designer image N+1: figer l'image cible depuis `docs/assets/ux-visuels-fictifs-2026-05-21/10_export_passation_n2_apercu_verifiable.png`.

### Points exacts a tester

- `/actions/__COPROSCOPE_TEST_ACTION_MISSING_999__?token=local-secret` puis `/actions?action_missing=__COPROSCOPE_TEST_ACTION_MISSING_999__&token=local-secret`.
- `/actions?scope=comptes&token=local-secret`.
- `/demandes/relance?token=local-secret&request_id=REQ-FICTIF-ASSURANCE-B12`.
- `/pieces?proof=missing&token=local-secret`.
- `/chantiers?token=local-secret`.
- `/chantiers/{event_id}?token=local-secret`, avec `{event_id}` pris depuis un lien reel de la timeline.
- `/chantiers/MEM-UNKNOWN-404?token=local-secret`.
- `/chantiers/C:%5CUsers%5Cbrice%5Craw%5Cmemoire-privee.pdf?token=local-secret`.
- `/exports/passation?token=local-secret&scope=event&selected=MEM-DOC-7D412766`.
- `/exports/passation.json?token=local-secret`.
- `/exports/passation.txt?token=local-secret`.

### Decisions requises

- GO memoire/actions/pieces/relance: accepter maintenant ou demander un dernier passage novice verbalise.
- Route principale passation: `/exports/passation` devient-elle l'apercu HTML du cycle N, ou la redirection texte reste-t-elle le comportement accepte?
- Scope par defaut: passation globale ou passation filtree par evenement selectionne.
- Formats: TXT + JSON obligatoires; Markdown seulement si tests anti-fuite dedies.
- Exclusions: afficher les elements bloques avec raison, mais ne jamais exporter de brut ni chemin local.

## Point 21:30 CET - Cycle export passation livre

### Flux decale

| Flux | Bloc | Etat | Sortie |
| --- | --- | --- | --- |
| N-1 test | Action introuvable, pieces, memoire, relance | GO | P0 leves, relance renforcee avec date/canal/destinataire |
| N dev | Export passation apercu verifiable | GO | `/exports/passation` est une page HTML testable |
| N+1 enquete | Confirmation relance / blocages export | pret | retour novice + visuel export N2 disponibles |

### Corrections livrees

- `/exports/passation` ne telecharge plus directement: il affiche un apercu avec inclusions, exclusions, restrictions, checklist, watermark et formats TXT/JSON.
- `model.ux.passation_export_preview` reste source du contrat; le template front `passation_export.html` est branche sur la route live.
- Les liens `/exports/passation.txt` et `/exports/passation.json` conservent `scope` et `selected`, puis le token est ajoute une seule fois.
- `/demandes/relance` affiche maintenant `Noter un envoi fait hors CoproScope` avec date, canal, destinataire et copie/preuve d'envoi.

### Verification

- Tests cibles relance/actions/pieces/live: `17 tests OK`.
- Tests export/memoire/securite: `23 tests OK`.
- Suite UI complete: `155 tests OK`.
- Serveur live redemarre: `8766`, PID `23944`, health OK.
- Captures: `docs/assets/ux-livraison-reelle-2026-05-21-8766-export-passation-live/`.

### Prochain mouvement

- Test novice produit sur `/exports/passation`.
- Decider si le prochain bloc est `detail blocage export` ou `confirmation relance apres enregistrement`.
- Garder Markdown hors livraison tant qu'un test anti-fuite dedie n'existe pas.

## Point 21:38 CET - Micro-cycle relance confirmation

- `/demandes/relance` journalise maintenant la date, le canal, le destinataire et la note d'envoi fictif hors CoproScope.
- L'etat `sent=1` relit la derniere action de relance et affiche sa trace dans le bandeau de confirmation.
- Test live realise avec donnees fictives sur `REQ-FICTIF-ASSURANCE-B12`.
- Captures: `docs/assets/ux-livraison-reelle-2026-05-21-8766-relance-confirmation-live/`.
- Suite UI complete: `155 tests OK`.

## Point 21:46 CET - Fermeture P1 QA

- P1 `sent=1` nu ferme: la confirmation exige maintenant une demande explicite et une trace de journal associee.
- P1 export scope ferme: les exports TXT/JSON avec `scope=event&selected=...` deviennent de vrais extraits evenementiels.
- Tests:
  - export routes: `6 tests OK`;
  - securite/smoke/relance: `16 tests OK`;
  - suite UI complete: `156 tests OK`.
- Live final: `http://127.0.0.1:8766/exports/passation?scope=event&selected=MEM-DOC-7D412766&token=local-secret`, PID `38040`.
