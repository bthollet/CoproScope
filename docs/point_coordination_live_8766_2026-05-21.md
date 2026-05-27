# Point de coordination live 8766 - 2026-05-21

> Statut gouvernail: `JOURNAL_TRACE`.
> La source de verite roadmap est `docs/roadmap_backlog_central.md`
> (`RM-2026-0006`). Ce point live sert de preuve, pas de roadmap active.

## Point 07:31 CET - cycle double flux

### A tester maintenant

- Serveur live attendu: `http://127.0.0.1:8766/?token=local-secret`.
- Navigateur utilisateur observe sur: `/actions?token=local-secret`.
- Routes prioritaires a retester sur livraison reelle: `/demandes`, `/documents/ajouter`, `/depot`, `/actions?priority=P1`.
- Donnees fictives privees injectees dans la copro fictive pour tests novice:
  - demandes: `REQ-FICTIF-ASSURANCE-B12`, `REQ-FICTIF-ASSURANCE-SYNDIC`, `REQ-FICTIF-INFILTRATION-C31`;
  - documents: `DOC-FICTIF-B12-ASSUR`, `DOC-FICTIF-SYNDIC-ASSUR`, `DOC-FICTIF-C31-INFILT`;
  - registres touches par le flux data: `registre_demandes.csv`, `registre_documents.csv`, `journal_demandes_coproprietaires.csv`, `manifest_sha256.csv`, screening confidentialite et biffage.
- Le dernier vert global connu reste `138` tests UI OK, mais il date d'avant les derniers ajustements P0 demandes/depot et l'injection de donnees fictives. Il ne vaut donc plus acceptation courante.

### En dev maintenant

- P0 `/demandes`: finaliser le parcours novice de creation/suivi de demande, avec route POST reelle, token conserve, validation simple et retour visible en liste.
- P0 `/documents/ajouter`: rendre le depot utile depuis l'ecran ajoute document: depot local, rattachement, confidentialite, prochaine action comprehensible.
- P0 `/depot`: verifier que les exports et liens action/document gardent le token et ne cassent pas la session locale.
- Risque principal: un formulaire visible sans route back stable bloque le test novice. Le flux back doit donc etre stabilise avant declaration GO.

### En enquete maintenant

- Designer de service: guider le membre CS novice sur les ecrans reels P0, bouton par bouton, en partant de l'attente issue des visuels Canva.
- Designer visuel/data: produire ou completer les visuels image manquants pour le flux suivant, avec donnees fictives privees mais clairement marquees `FICTIF`.
- Membre CS novice: scenario attendu sur route reelle: creer une demande, rattacher ou attendre une preuve, verifier ce qui est a faire ensuite, puis retrouver l'action.

### Commande prete

- Commande de reprise deja disponible: `docs/commandes_reprise_live_8766.md`.
- Prochaine commande dev a stabiliser: `P0 demandes/depot`, avant de repartir sur l'alignement profond `actions -> comptes -> memoire`.
- Format exige pour la commande suivante: objectif utilisateur, structure visuelle, composants, donnees, interactions, etats vides, criteres d'acceptation, tests attendus.

### Decision requise

- Pas d'arbitrage produit supplementaire requis avant reprise dev: priorite au NO-GO novice `/demandes` et `/documents/ajouter`.
- Decision de coordination: aucun bloc P1 ne doit etre accepte tant que les deux P0 ne sont pas testes en navigateur sur le serveur 8766.

### Prochain mouvement

- Dev back: terminer la route POST `/demandes` et le raccord registre.
- Dev front: verifier les CTA depot/document et les libelles novice.
- QA: relancer les tests cibles `requests`, `document_intake`, `depot`, `actions`, puis la suite UI complete.
- Coordinateur-scribe: consigner le resultat du prochain point dans `docs/journal_cycles_ux_2026-05-21.md`.

## Etat des agents

- Coordinateur-scribe: actif, ownership limite a ce fichier et au journal des cycles.
- Designer de service: pret a lancer le test image/reel du bloc P0, puis a formaliser l'intention du bloc suivant.
- Designer visuel/data: donnees fictives privees creees; prochaine tache, visuels images manquants et variantes avec pieces administratives fictives.
- Membre CS novice: en attente d'un ecran livre testable; scenario de test P0 a executer sur `/demandes` et `/documents/ajouter`.
- Dev front: a reprendre sur CTA, lisibilite novice, structure proche Canva, responsive.
- Dev back/viewmodel: a reprendre sur POST demandes, projections utiles, liens tokenises.
- QA securite/live: en attente de build redemarre; tests a relancer avant GO.

## Pipeline courant

- Cycle N-1 - Test produit livre: cockpit/actions/comptes/memoire deja captures, mais NO-GO novice restant sur demandes/depot.
- Cycle N - Dev: P0 demandes/depot en cours de stabilisation.
- Cycle N+1 - Enquete/visuel: preparation des vues suivantes avec images et donnees fictives privees: toutes actions en retard, pieces manquantes, relance syndic, detail action, detail evenement memoire, export passation.

## Rappel des preuves visuelles existantes

- Capture de reference apres reprise: `docs/assets/ux-livraison-reelle-2026-05-21-8766-apres-reprise/`.
- Planche de preuve visuelle: `docs/planche_preuve_visuelle_live_8766.md`.
- Diagnostic visuel: `docs/ecarts_visuels_live_vs_canva_2026-05-21.md`.

## Historique avant ce point

- Coque front realignee: navigation metier, contexte compact, bouton `Nouvelle demande` visible, contenu metier remonte dans le premier ecran.
- Viewmodel comptes renforce: KPI non vides quand les sorties existent, categories, statuts P1/P2/OK, pieces manquantes et questions syndic exposes.
- Tests live ajoutes: routes 200, pas de 404, contenu utile, token, libelles novices, racines privees non servies.
- Verdict precedent: GO partiel, NO-GO sur `/demandes` et `/documents/ajouter`.

## Point 08:00 CET - GO cycle P0 relance/depot/demandes

### A tester maintenant

- Navigateur live laisse sur `/demandes/relance?token=local-secret&request_id=REQ-FICTIF-ASSURANCE-B12`.
- Captures finales disponibles: `docs/assets/ux-livraison-reelle-2026-05-21-8766-final/`.
- Visuels images amont disponibles: `docs/assets/ux-visuels-fictifs-2026-05-21/`.

### En dev maintenant

- Bloc P0 relance/demandes/depot livre et teste.
- Prochain bloc recommande: pieces manquantes puis detail action, en partant
  des PNG designer N+2 et de
  `docs/coordination_cycle_n2_pieces_detail_2026-05-21.md`.
- Retour novice ajoute: relance validee; `Pieces manquantes` refusee tant que
  la liste n'est pas remplie/coherente. Image prioritaire:
  `docs/assets/ux-visuels-fictifs-2026-05-21/09_pieces_manquantes_n2_liste_coherente.png`.

### En enquete maintenant

- Membre CS novice doit tester la route reelle: comprendre pourquoi on relance, verifier la piece attendue, copier le message, valider la relance fictive, rattacher une reponse.
- Designer de service doit convertir les retours en corrections mineures ou commande detail action.

### Commande prete

- `Relance syndic` est livre en route reelle `/demandes/relance`.
- Commande suivante: detail action, puis pieces manquantes.

### Decision requise

- Decision UX retenue pour la demo: `Valider la relance` signifie enregistrer une relance fictive dans le journal local et proposer copie du message; aucun envoi reel.

### Prochain mouvement

- Passer au test novice live.
- Si accepte: cycle suivant `/pieces?proof=missing` avec cartes remplies
  pourquoi/detenteur/lien comptes-action, puis `/actions/{id}` ou detail
  integre action.
- Si confusion: renommer `Valider la relance` en `Enregistrer la relance fictive`.

### Verification

- Serveur live `8766` redemarre, health OK.
- Suite UI complete apres dernier redemarrage live: `141 tests OK`.
- Securite: zip local filtre contenu et chemins prives; `/depot` masque les chemins raw; formulaires `/demandes` masquent les chemins soumis.

## Point 08:33 CET - GO bloc Pieces manquantes N+2

### A tester maintenant

- Serveur live actif: `http://127.0.0.1:8766/?token=local-secret`, listener `8766` PID `36804`.
- Route prioritaire livree: `/pieces?proof=missing&token=local-secret`.
- Captures reelles: `docs/assets/ux-livraison-reelle-2026-05-21-8766-pieces-n2/`.

### En dev maintenant

- Bloc `Pieces manquantes` livre avec cartes remplies depuis les manques comptes.
- `/actions?scope=comptes` n'affiche plus l'etat vide: les actions comptables P1/P2 sont exposees.
- Prochain bloc dev: detail action et libelles novice restants (`Registre des decisions` vers `Actions a traiter`).

### En enquete maintenant

- Designer image N+2 livre: `docs/assets/ux-visuels-fictifs-2026-05-21/09_pieces_manquantes_n2_liste_coherente.png`.
- Test novice suivant: verifier que le membre CS trouve la piece, le detenteur, `Relancer syndic`, `Ajouter une piece recue`, puis `Voir action`/compte.

### Commande prete

- Commande pieces/detail action: `docs/coordination_cycle_n2_pieces_detail_2026-05-21.md`.
- Detail action `/actions/{id}` existe et redirige vers la fiche selectionnee avec token.

### Agents idle a relancer

- QA, designer, novice, front et back ont rendu leurs sorties sur ce cycle.
- Les prochains cycles doivent les relancer sur `detail action` puis `export passation`.

### Decision requise

- Aucune decision bloquante. Les libelles peuvent encore etre adoucis en correction mineure.

### Prochain mouvement

- Capturer/tester detail action apres correction des libelles novice.
- Basculer QA sur responsive mobile et etat action introuvable.

### Verification

- Suite UI complete: `147 tests OK`.
- Health live: OK.
- Signaux live `/pieces?proof=missing`: `2 pieces concretes`, `SERVICES ASCENSEUR FICTIF`, `JUSTIFICATIF_INTERVENTION_ASCENSEUR`, `Preparer la demande syndic`, `Ajouter depuis le depot`.

### Mise a jour 08:39 CET

- Serveur live redemarre apres correction libelles actions: PID `11408`.
- `/actions` affiche maintenant `Actions a traiter` tout en conservant l'ancre testee `Registre des decisions`.
- Libelles techniques traduits dans les fiches: `Document a verifier`, `Diffusion a arbitrer`, `Controle comptes`.
- Suite UI complete relancee apres ce changement: `147 tests OK`.

## Point 09:10 CET - Passerelle UX / DB

### A tester maintenant

- Serveur local: `http://127.0.0.1:8766/?token=local-secret`.
- Suite UI complete cote TestClient: `150 tests OK`.
- Ecrans a garder sous test: `/pieces?proof=missing`, `/actions?scope=comptes`, `/demandes/relance`, `/actions/{id}`.

### En dev maintenant

- Cycle `detail action`: validation source/test OK pour action connue, action inconnue et ID prive masque.
- Reste a revalider le serveur live 8766 apres reload complet: le cas action inconnue a montre un ecart live temporaire (`selected` au lieu de `action_missing`).

### En enquete maintenant

- Designer/service continue les vues suivantes: detail evenement memoire et export passation.
- Le futur fil DB peut travailler en parallele sur la structure sans bloquer les tests UX.

### Commande prete

- Passerelle creee:
  - `coproscope/docs/passerelle_ux_db_2026-05-21.md`
  - `coproscope/docs/passerelle_ux_vers_db_2026-05-21.md`
  - `coproscope/docs/passerelle_db_vers_ux_2026-05-21.md`
- Convention: le fil UX ecrit `ux_vers_db`; le fil DB repond `db_vers_ux`.

### Agents idle a relancer

- Aucun agent ne doit rester idle: s'il termine, le basculer sur QA/doc ou sur le prochain bloc.
- Roles actifs attendus: dev front cycle N, dev back cycle N, QA/test N-1, designer N+2, membre CS novice transversal, coordinateur-scribe.

### Decision requise

- Aucune decision utilisateur requise.
- Decision de coordination: le fil DB ne doit pas prendre le comportement live temporaire de `/actions/{id inconnu}` comme contrat; source/tests font foi jusqu'au point "live aligne".

### Prochain mouvement

- Revalider 8766 sur action inconnue apres reload complet.
- Capturer detail action desktop/mobile.
- Lire les reponses du futur fil DB dans `coproscope/docs/passerelle_db_vers_ux_2026-05-21.md` et ajuster les projections `model.ux.*` si necessaire.

## Point 20:40 CET - Live detail action aligne

### A tester maintenant

- Serveur live actif: `http://127.0.0.1:8766/?token=local-secret`, listener `8766` PID `12268`.
- Ecran livre: `/actions/__COPROSCOPE_TEST_ACTION_MISSING_999__?token=local-secret` redirige vers `/actions?action_missing=__COPROSCOPE_TEST_ACTION_MISSING_999__&token=local-secret`.
- Captures reelles:
  - `docs/assets/ux-livraison-reelle-2026-05-21-8766-action-detail-live/action-inconnue-desktop-final.png`
  - `docs/assets/ux-livraison-reelle-2026-05-21-8766-action-detail-live/action-inconnue-mobile-final.png`
  - `docs/assets/ux-livraison-reelle-2026-05-21-8766-action-detail-live/pieces-manquantes-desktop.png`

### En dev maintenant

- Correction livree: bannière `Action introuvable` novice-safe, sans echo d'identifiant prive, avec actions de repli.
- Correction responsive: la notice mobile n'herite plus du vieux flex horizontal; texte et CTA passent en blocs lisibles.
- Prochain bloc dev: `Detail evenement memoire` puis `Export passation`.

### En enquete maintenant

- Designer relance sur image `Detail evenement memoire`.
- Membre CS novice teste les parcours action introuvable, pieces manquantes, relance syndic et memoire.

### Commande prete

- Passerelle UX/DB prete:
  - `docs/passerelle_ux_db_2026-05-21.md`
  - `docs/passerelle_ux_vers_db_2026-05-21.md`
  - `docs/passerelle_db_vers_ux_2026-05-21.md`
- Commande dev suivante attendue du designer: detail evenement memoire en image + criteres.

### Agents idle a relancer

- Ancienne vague bloquee fermee.
- Nouvelle vague active:
  - designer service: visuel image detail evenement memoire;
  - dev back: projections memoire/passation;
  - dev front: vue memoire/passation;
  - QA: routes live et non-fuites;
  - membre CS novice: scenarios et langage.

### Decision requise

- Aucune decision utilisateur requise.
- Pour l'autre fil DB: demarrer par modele conceptuel + contrats de projection `model.ux.*`, puis seulement tables/index/migrations.

### Prochain mouvement

- Integrer les retours agents.
- Si le designer rend l'image, transformer en commande dev et demarrer bloc memoire.
- Maintenir `150 tests OK` apres toute correction.

### Verification

- Tests cibles action/relance/live: `13 tests OK`.
- Suite UI complete: `150 tests OK`.
- Verifications live: `/pieces?proof=missing` expose `2 pieces concretes`, `SERVICES ASCENSEUR FICTIF`, `Preparer la demande syndic`.

## Point 20:56 CET - Coordination interconversations

### Veille passerelles

- Coordinateur interconversations actif.
- Note de coordination creee: `docs/coordination_interconversations_2026-05-21.md`.
- Dernier signal DB: `docs/passerelle_db_vers_ux_2026-05-21.md` modifie a 20:56 avec reponses UXDB et question `DBUX-20260521-01`.
- Dernier signal UX/live: ce point live et `docs/journal_cycles_ux_2026-05-21.md` modifies a 20:48 avec `150 tests OK`.

### Regles appliquees

- UX garde `passerelle_ux_vers_db_2026-05-21.md`.
- DB garde `passerelle_db_vers_ux_2026-05-21.md`.
- Le coordinateur n'ecrit pas dans les passerelles metier sauf demande explicite; il consolide l'etat et les collisions dans la note de coordination.
- Toute prochaine vague doit declarer son ownership avant de toucher `model.ux.*`, `viewmodel.py`, routes web ou schema vault.

### Prochain mouvement

- Repondre cote UX a `DBUX-20260521-01`: quels ecrans ont besoin d'un extrait de preuve lisible, et lesquels peuvent se contenter d'un libelle.
- Lancer la vague memoire/passation seulement avec owner unique des projections partagees.

## Point 21:13 CET - Final cycle memoire livre, export passation a preparer

### A tester maintenant

- Serveur live actif: `http://127.0.0.1:8766/?token=local-secret`, listener `8766` PID `7352`, health OK.
- Tests cibles: `34 tests OK`.
- Suite UI complete: `155 tests OK`.
- Captures reelles finales: `docs/assets/ux-livraison-reelle-2026-05-21-8766-final-cycle-memoire/`.
- Parcours livre a valider en QA/novice N-1:
  - action introuvable: `/actions/__COPROSCOPE_TEST_ACTION_MISSING_999__?token=local-secret` redirige vers `action_missing` et n'affiche plus une autre fiche;
  - actions comptes: `/actions?scope=comptes&token=local-secret` affiche le titre `Points comptes a traiter avant AG`;
  - relance action: plus de lien GET `sent=1`; l'action indique `Noter l'envoi hors CoproScope`;
  - pieces manquantes: `/pieces?proof=missing&token=local-secret` affiche `Voir le point dans les comptes`;
  - memoire detail: `/chantiers/{event_id}?token=local-secret` redirige token-safe vers `/chantiers?selected={event_id}&token=local-secret`;
  - memoire introuvable: `/chantiers/MEM-UNKNOWN-404?token=local-secret` redirige vers `/chantiers?event_missing=MEM-UNKNOWN-404&token=local-secret`;
  - export passation historique: `/exports/passation?token=local-secret&scope=event&selected=MEM-DOC-7D412766` redirige token-safe vers `/exports/passation.txt?scope=event&selected=MEM-DOC-7D412766&token=local-secret`.

### Corrections livrees

- `Action introuvable` ne selectionne plus une fiche sans rapport.
- Les actions comptes parlent en termes conseil syndical: `Points comptes a traiter avant AG`.
- La relance depuis une action ne simule plus un envoi par lien GET `sent=1`; elle demande de `Noter l'envoi hors CoproScope`.
- `Pieces manquantes` relie la preuve attendue au controle comptes avec `Voir le point dans les comptes`.
- Les routes detail/introuvable de la memoire sont OK et masquent les references privees.
- `/exports/passation` reste protege et redirige vers le texte avec token conserve.

### Cycle suivant - Export passation apercu verifiable en double flux

| Flux | Role | Objet | Sortie attendue |
| --- | --- | --- | --- |
| N-1 test | QA + membre CS novice | Fermer le cycle memoire/actions/pieces/relance livre | GO/NO-GO sur routes reelles ci-dessus, captures comparees au dossier final |
| N dev | Front + back | `/exports/passation` devient un apercu HTML verifiable avant telechargement | Sections incluses/exclues, restrictions, watermark derive, liens TXT/JSON token-safe, aucune source brute |
| N+1 image | Designer service + designer visuel/data | Preparer l'image export passation | Cible `docs/assets/ux-visuels-fictifs-2026-05-21/10_export_passation_n2_apercu_verifiable.png` et rappel `06_export_passation.png` |

### Points exacts a tester

- `GET /actions/__COPROSCOPE_TEST_ACTION_MISSING_999__?token=local-secret` puis destination `GET /actions?action_missing=__COPROSCOPE_TEST_ACTION_MISSING_999__&token=local-secret`.
- `GET /actions?scope=comptes&token=local-secret`: titre `Points comptes a traiter avant AG`, cartes comptes, aucun etat vide.
- `GET /demandes/relance?token=local-secret&request_id=REQ-FICTIF-ASSURANCE-B12`: absence de `sent=1`, libelle `Noter l'envoi hors CoproScope`, token conserve.
- `GET /pieces?proof=missing&token=local-secret`: CTA `Voir le point dans les comptes`, lien retour comptes/action lisible.
- `GET /chantiers?token=local-secret`: au moins un lien detail `/chantiers/{event_id}?token=local-secret`.
- `GET /chantiers/{event_id}?token=local-secret`: redirection `303` vers `/chantiers?selected={event_id}&token=local-secret`, detail lisible `Pourquoi c'est garde` et `Documents et preuves`.
- `GET /chantiers/MEM-UNKNOWN-404?token=local-secret`: redirection `303` vers `/chantiers?event_missing=MEM-UNKNOWN-404&token=local-secret`, notice `Evenement introuvable`.
- `GET /chantiers/C:%5CUsers%5Cbrice%5Craw%5Cmemoire-privee.pdf?token=local-secret`: redirection vers `event_missing=reference-locale-masquee`, sans echo `Users`, `raw` ou nom de fichier.
- `GET /exports/passation?token=local-secret&scope=event&selected=MEM-DOC-7D412766`: redirection `303` vers `/exports/passation.txt?scope=event&selected=MEM-DOC-7D412766&token=local-secret`.
- `GET /exports/passation.json?token=local-secret` et `GET /exports/passation.txt?token=local-secret`: watermark derive, `source_of_truth: false`, aucune fuite `raw`, `restricted`, `logs`, `C:\Users` ou chemin local.

### Decisions requises

- Decider si le cycle memoire/actions/pieces/relance peut passer `GO` avec `34 tests cibles OK`, `155 suite UI OK` et les captures finales, ou s'il faut un dernier test novice verbalise.
- Decider si `/exports/passation` doit devenir l'apercu HTML principal du cycle N ou rester une redirection temporaire vers `.txt`.
- Decider le scope par defaut de l'apercu: passation globale conseil syndical ou passation filtree par evenement `selected`.
- Decider les formats exposes dans l'apercu: TXT + JSON minimum, Markdown seulement si le controle anti-fuite est teste.
- Decider la regle d'affichage des elements exclus: visibles comme exclusions motivees, jamais exportes comme sources brutes.

## Point 21:30 CET - Export passation apercu livre

### A tester maintenant

- Serveur live actif: `http://127.0.0.1:8766/?token=local-secret`, listener relance PID `23944`, health OK.
- Ecran livre principal: `/exports/passation?scope=event&selected=MEM-DOC-7D412766&token=local-secret`.
- Ecran relance corrige: `/demandes/relance?request_id=REQ-FICTIF-ASSURANCE-B12&token=local-secret`.
- Captures reelles:
  - `docs/assets/ux-livraison-reelle-2026-05-21-8766-export-passation-live/export-passation-desktop.png`
  - `docs/assets/ux-livraison-reelle-2026-05-21-8766-export-passation-live/export-passation-mobile.png`
  - `docs/assets/ux-livraison-reelle-2026-05-21-8766-export-passation-live/relance-trace-envoi-desktop.png`
  - `docs/assets/ux-livraison-reelle-2026-05-21-8766-export-passation-live/relance-trace-envoi-mobile.png`

### En dev maintenant

- Cycle Export passation: GO livre.
- `/exports/passation` sert maintenant un apercu HTML complet avec template `passation_export.html`, styles `cs-passation-*`, watermark, `source_of_truth false`, sections incluses, exclusions/blocages, restrictions, checklist et formats TXT/JSON tokenises.
- Les liens TXT/JSON conservent le contexte `scope=event&selected=MEM-DOC-7D412766` sans doubler le token.
- La relance syndic a ete renforcee: `Noter un envoi fait hors CoproScope` demande date, canal, destinataire et copie/preuve d'envoi avant journal fictif.

### En enquete maintenant

- Le membre CS novice a accepte les corrections action introuvable, pieces, memoire et a demande une page d'apercu avant tout export direct.
- Le visuel cible designer existe:
  - `docs/assets/ux-visuels-fictifs-2026-05-21/10_export_passation_n2_apercu_verifiable.png`
  - `docs/commandes/commande_cycle_n1_export_passation_apercu_verifiable_2026-05-21.md`

### Commande prete

- Prochain bloc candidat: durcir le parcours `Noter un envoi fait hors CoproScope` apres POST avec retour de confirmation date/canal/destinataire, puis test novice.
- Bloc suivant possible: page detail export par element bloque depuis `Elements exclus ou bloques`.

### Agents idle a relancer

- Designer: disponible pour visuel detail blocage export ou confirmation relance.
- Dev back/front: a relancer sur confirmation relance ou blocages export, en gardant ownership disjoint.
- QA: relancer sur tests live navigateur desktop/mobile de `/exports/passation`, `/demandes/relance`, `/chantiers`, `/pieces`.
- Membre CS novice: refaire scenario export: lire l'apercu, comprendre inclus/exclus, choisir TXT/JSON ou retour memoire.

### Decision requise

- Aucune decision bloquante.
- Arbitrage produit non bloquant: Markdown reste absent de la livraison tant qu'un test anti-fuite dedie n'est pas ajoute.

### Prochain mouvement

- Recharger le navigateur sur `/exports/passation?scope=event&selected=MEM-DOC-7D412766&token=local-secret` pour test humain.
- Continuer le double flux: QA/novice testent l'export livre, designer prepare confirmation relance ou detail blocage, dev corrige les retours.

### Verification

- Tests cibles relance/actions/pieces/live: `17 tests OK`.
- Tests export/memoire/securite: `23 tests OK`.
- Suite UI complete: `155 tests OK`.
- Verification live HTTP: template export, sections, exclusions, liens TXT/JSON, non-fuite privee et champs relance OK.

## Point 21:38 CET - Relance confirmation livree

### A tester maintenant

- Ecran live: `/demandes/relance?request_id=REQ-FICTIF-ASSURANCE-B12&sent=1&token=local-secret`.
- Donnee fictive injectee pour test live: relance `REQ-FICTIF-ASSURANCE-B12`, date `2026-05-21`, canal `email`, note `test live confirmation fictive`.
- Captures reelles:
  - `docs/assets/ux-livraison-reelle-2026-05-21-8766-relance-confirmation-live/relance-confirmation-desktop.png`
  - `docs/assets/ux-livraison-reelle-2026-05-21-8766-relance-confirmation-live/relance-confirmation-mobile.png`

### En dev maintenant

- Micro-cycle relance confirmation: GO livre.
- Apres POST fictif, la page affiche la trace enregistree avec date/canal/note au lieu d'un simple message generique.

### Verification

- Suite UI complete apres ce correctif: `155 tests OK`.
- Verification live HTTP + navigateur: bandeau `Relance enregistree fictivement`, `date 2026-05-21, canal email`, note fictive et rappel aucun envoi reel visibles.

## Point 21:46 CET - P1 QA export/relance fermes

### Corrections QA

- `GET /demandes/relance?sent=1&token=local-secret` n'affiche plus de confirmation si aucune demande explicite et aucun journal de relance ne correspondent.
- Le POST relance redirige avec `sent_id=JRN-UI-RELANCE-*`, ce qui garantit que la page de confirmation relit l'action de journal creee, pas une ancienne trace du meme jour.
- `/exports/passation.json?scope=event&selected=MEM-DOC-7D412766&token=local-secret` produit un export derive `scope.kind=passation_event`, `selected=MEM-DOC-7D412766`, avec une seule entree chronologie.
- `/exports/passation.txt?scope=event&selected=MEM-DOC-7D412766&token=local-secret` contient l'evenement selectionne et n'inclut pas l'autre evenement `MEM-DOC-816608C5`.

### Verification

- Tests export routes: `6 tests OK`.
- Tests securite/smoke/relance: `16 tests OK`.
- Suite UI complete: `156 tests OK`.
- Serveur live redemarre: `8766`, PID `38040`, health OK.
- Verification navigateur: apercu export visible, liens TXT/JSON event-scope presents, pas de double token.

## Point 22:05 CET - Reprise sous regle zero agents

### A tester maintenant

- Serveur live a reverifier avant tout nouveau correctif.
- Dernier ecran livre connu: `/exports/passation?scope=event&selected=MEM-DOC-7D412766&token=local-secret`.
- Dernier cockpit utilisateur ouvert: `/?token=local-secret`.

### En dev maintenant

- Aucun fichier applicatif nouveau n'est modifie tant que les roles front/back/QA/design ne sont pas rattaches au chantier `CH-2026-0002`.
- Le coordinateur-scribe ouvre d'abord une reprise, puis corrige le rattachement vers `RM-2026-0003` / `CH-2026-0003` / `CONV-2026-0003`, car `RM-2026-0002` / `CONV-2026-0002` sont deja utilises par le gouvernail roadmap.

### En enquete maintenant

- Reprise du flux decale Image -> Dev -> Test produit.
- Roles attendus: designer/facilitateur, membre CS novice, dev front, dev back/viewmodel, QA/securite, coordinateur-scribe.

### Commande prete

- Premiere commande de reprise: verifier le live 8766, relancer la baseline de tests, puis choisir le prochain bloc entre detail memoire, detail blocage export ou confirmation relance.

### Agents idle a relancer

- Tous les roles doivent recevoir un lot explicite apres verification live.

### Decision requise

- Aucune decision utilisateur bloquante: carte blanche confirmee. Les arbitrages impossibles seront notes comme questions, pas comme arret.

### Prochain mouvement

- Executer health live + tests cibles existants, puis ouvrir les lots agents avec ownership disjoint.

### Verification 22:10

- Health live `/?token=local-secret`: HTTP 200, contenu CoproScope present.
- Baseline complete serveur: 433 tests lances, 431 OK, 2 echecs.
- Echecs a isoler:
  - `test_docops_completeness.DocOpsCompletenessTests.test_actionable_matrix_distinguishes_present_missing_stale_and_classification_doubt`: statut attendu `A_CLASSER`, obtenu `PRESENT`.
  - `test_incidentops.IncidentOpsTests.test_build_register_detects_incident_and_exports_open_items`: `incident_count` attendu 1, obtenu 3.
- Decision coordination: ne pas masquer ces echecs; QA les prend en analyse pendant que designer/utilisateur/front/back avancent sur les flux non bloquants.

## Point 22:32 CET - P0 export passation filtre corrige

### A tester maintenant

- Route live: `/exports/passation?scope=event&selected=MEM-DOC-7D412766&token=local-secret`.
- L'ecran affiche maintenant `Apercu de passation - extrait evenement`.
- Les compteurs visibles sont filtres: 1 evenement inclus, 3 sujets ouverts, 2 documents cites, 1 restriction a relire.
- Les liens `Telecharger TXT` et `Telecharger JSON` conservent `scope=event&selected=MEM-DOC-7D412766`.

### En dev maintenant

- Lot `CONV-2026-0010` livre: template passation et route HTML alignes sur le document export derive filtre.
- Le serveur live 8766 a ete relance, health OK.

### En enquete maintenant

- Retours novice/front/back convergent vers le prochain bloc: detail memoire plus haut dans la page et clarifications titres/contexte.

### Commande prete

- P0 technique QA suivant: durcir les matchs lexicaux DocOps/IncidentOps reveles par les donnees fictives.

### Tests/preuves

- `tests.test_ui_passation_export_route tests.test_ui_security_routes tests.test_ui_smoke_routes_expanded -v`: 15 tests OK.
- Verification live HTTP: titre filtre OK, lien TXT scope OK, pas de lien TXT global, 1 evenement visible, export TXT contient `MEM-DOC-7D412766` et pas `MEM-DOC-816608C5`.
- Verification navigateur: page rechargee sur 8766, captures visuelles observees dans le navigateur integre.

## Point 22:40 CET - Baseline verte et prochain visuel pret

### A tester maintenant

- Export passation filtre livre et teste sur route reelle.
- Prochain visuel designer a tester/preparer: `docs/assets/ux-visuels-fictifs-2026-05-21/11_detail_blocage_export_n2.png`.

### En dev maintenant

- Aucun dev applicatif actif apres cloture des P0.
- `CONV-2026-0010` integre: HTML passation filtre.
- `CONV-2026-0011` integre: matching lexical DocOps/IncidentOps durci.

### En enquete maintenant

- Bloc suivant retenu par designer: `detail blocage export`, pour rendre les exclusions/masquages actionnables pour un membre CS novice.

### Commande prete

- `docs/commandes/commande_cycle_n3_detail_blocage_export_2026-05-21.md`.
- Visuel PNG: `docs/assets/ux-visuels-fictifs-2026-05-21/11_detail_blocage_export_n2.png`.

### Agents idle a relancer

- Designer: pret a passer sur le visuel suivant apres integration du detail blocage.
- Front/back: a relancer avec ownership explicite sur le bloc detail blocage export.
- QA/novice: a relancer apres route livree.

### Decision requise

- Aucune decision bloquante: continuer le flux decale.

### Prochain mouvement

- Declarer le lot dev detail blocage export, reserver les fichiers front/back minimaux, puis livrer une route ou un etat actionnable depuis les elements exclus de l'export.

### Tests/preuves

- Tests DocOps ciblés: OK.
- Tests IncidentOps ciblés: OK.
- Suite complete: 433 tests OK.

## Point 22:48 CET - Base test par defaut basculee

### Decision

- L'environnement de test local par defaut des agents devient `C:\Users\brice\CoproScope\instances\beauvallon_test`.
- Identifiant de l'instance: `beauvallon-test`.
- Platanes (`examples/synthetic_copro`) n'est plus la cible live/recette par defaut; il reste reserve aux tests publics/CI et aux exemples partageables.

### Commande de reprise agents

```powershell
cd C:\Users\brice\CoproScope\coproscope
.\server\.venv\Scripts\python.exe -m coproscope.cli ui open-test --instance-root C:\Users\brice\CoproScope\instances\beauvallon_test --year 2025 --host 127.0.0.1 --port 8766 --token beauvallon-test-local
```

### Signal aux agents

- Lire `AGENTS.md` et `docs/orchestration_agents.md` avant toute nouvelle recette.
- Ne pas commiter la base `beauvallon_test` ni ses dossiers `raw`, `restricted`, logs, exports prives ou tables de correspondance.
- Toute comparaison avec Platanes doit etre annoncee comme test public/CI, pas comme recette locale par defaut.

### Verification

- `doctor` sur `beauvallon-test`: OK.
- `vault verify` sur le coffre copie: OK.

## Point 22:54 CET - Detail blocage export consolide

### A tester maintenant

- Route prioritaire: `/exports/passation/blocages/BLOCK-FICTIF-RELANCE-ASCENSEUR?scope=event&selected=MEM-DOC-7D412766&token=local-secret`.
- L'ecran doit afficher `Detail blocage export`, `Relance ascenseur non tracee`, les preuves attendues, le telechargement verrouille et les compteurs non nuls.

### En dev maintenant

- Lot `CONV-2026-0015` integre: route detail blocage unique, ancien fallback doublonne retire, compteurs de detail alimentes par `passation_blocker_view`.
- Relance horaire Codex active: `relance-equipe-agile-coproscope`.

### En enquete maintenant

- Prochain choix utile: CI minimale / hygiene tests ou extraction progressive des gros centres UI (`app.py`, `viewmodel.py`) sans changer les contrats.

### Tests/preuves

- Grappe de sortie: `34 tests OK`.
- Suite complete: `444 tests OK`.
- Commande: `.\.venv\Scripts\python.exe -m unittest tests.test_ui_passation_export_route tests.test_ui_security_routes tests.test_ui_action_detail_route tests.test_ui_requests_route tests.test_ui_smoke_routes_expanded -v`.

## Point 22:57 CET - Detail blocage export livre sur navigateur

### A tester maintenant

- Route live disponible: `/exports/passation/blocages/BLOCK-FICTIF-RELANCE-ASCENSEUR?scope=event&selected=MEM-DOC-7D412766&token=local-secret`.
- Parcours reel teste depuis `/exports/passation?scope=event&selected=MEM-DOC-7D412766&token=local-secret`: clic sur `Relance ascenseur non tracee` puis arrivee sur le detail.
- Captures reelles sauvegardees:
  - `docs/assets/ux-livraison-reelle-2026-05-21-8766-detail-blocage-export/detail-blocage-export-visible.png`
  - `docs/assets/ux-livraison-reelle-2026-05-21-8766-detail-blocage-export/detail-blocage-export-full.png`

### En dev maintenant

- Lot detail blocage export integre: source unique `passation_blocker_view`, route unique dans `app.py`, template detail, styles et tests passation.
- Serveur live relance: `http://127.0.0.1:8766/?token=local-secret`, health OK, PID `5920`.

### En enquete maintenant

- Aucun nouveau dev ne doit demarrer sans commande validee.
- Prochain bloc UX recommande: `detail piece/preuve`, car le backlog produit demande qu'une piece ouverte explique pourquoi elle compte, quelle preuve elle porte et quoi faire.

### Commande prete

- Commande cloturee: `docs/commandes/commande_cycle_n3_detail_blocage_export_2026-05-21.md`.
- Commande suivante a produire par designer/service avant dev: detail piece/preuve ou premier succes onboarding si le coordinateur active `RM-2026-0009`.

### Agents idle a relancer

- QA/novice: relancer sur recette navigateur du detail blocage export si un second avis est demande.
- Designer/service: basculer sur image detail piece/preuve.
- Dev front/back: attente de commande validee; pas de dev direct sur intention abstraite.

### Decision requise

- Aucune pour le lot livre.

### Prochain mouvement

- Formaliser la prochaine commande image -> dev -> test, probablement `detail piece/preuve`, puis ouvrir un nouveau `CONV-*` avec ownership disjoint.

### Tests/preuves

- `.\.venv\Scripts\python.exe -m unittest tests.test_ui_passation_export_route tests.test_ui_security_routes tests.test_ui_action_detail_route tests.test_ui_requests_route tests.test_ui_smoke_routes_expanded -v`: `34 tests OK`.
- Verification navigateur integre: titre, raison du blocage, `TXT verrouille`, `source_of_truth false`, lien retour scope/token, lien action token-safe, aucune fuite `C:\Users` ou `file://`.

## Point 23:08 CET - CI minimale ajoutee

### En dev maintenant

- Lot `CONV-2026-0023` integre: workflow `.github/workflows/ci.yml` ajoute.
- Le workflow GitHub Actions lance deux jobs publics: suite `unittest` et controles securite.
- Les controles securite sont calibres pour une premiere CI exploitable: Bandit bloque les severites hautes; `pip-audit` audite le projet avec `--skip-editable`.

### Tests/preuves

- YAML workflow: OK.
- Suite complete locale: `450 tests OK`.
- `python -m bandit -r src -q --severity-level high`: OK.
- `python -m pip_audit . --skip-editable --progress-spinner off`: OK.

### Prochain mouvement

- Integrer progressivement les tests non suivis par familles (`ui`, `vault`, `security`, `docs/contracts`) afin que la CI voie la meme couverture que la recette locale.
- Traiter ensuite les signaux Bandit bas/moyens par petits lots dedies.

## Point 23:04 CET - Relance horaire consolidee

### Automation

- Relance active unique: `relance-equipe-agile-coproscope`.
- Type retenu: heartbeat attache a ce fil, cadence `FREQ=HOURLY;INTERVAL=1`.
- Prompt aligne sur le protocole agile: lecture des registres, declaration RM/CH/CONV, ownership explicite, tests cibles et BOT-END.
- Doublon supprime: cron `relance-equipe-agile-coproscope-2`, pour eviter deux relances concurrentes toutes les heures.

### Prochain mouvement

- Laisser `CONV-2026-0023` avancer sur CI minimale si actif.
- Pour le flux produit `CH-2026-0006`, prochaine relance: produire ou valider la commande `detail piece/preuve`, puis ouvrir un nouveau lot avec ownership disjoint.

## Point 23:11 CET - Nouvelle equipe agile CH-2026-0007

### A tester maintenant

- Livraisons recentes a surveiller: detail blocage export, detail evenement memoire, CI minimale.
- Route candidate pour le prochain produit: `/pieces?proof=missing&token=local-secret`.

### En dev maintenant

- Un autre coordinateur a deja reserve le code pieces sous `CONV-2026-0025`.
- La relance parallele `CONV-2026-0029` reste en coordination lecture seule et ne prend pas d'ownership applicatif.

### En enquete maintenant

- `CONV-2026-0031`: verifier si `detail piece/preuve` est bien le meilleur prochain pas pour un membre CS novice, en second avis.
- `CONV-2026-0032`: cartographier le plus petit ownership front/back sans toucher au code reserve par `CONV-2026-0025`.
- `CONV-2026-0030`: verifier les risques de regression apres les lots passation, memoire et CI, en second avis QA.

### Commande prete

- Hypothese de depart: commande `detail piece/preuve`, a confirmer par les agents avant dev.

## Point 23:15 CET - Relance agile et hygiene Git

### Avis des roles

- QA/CI: priorite qualite = rendre la CI et les tests suivis aussi proches que possible des preuves locales `450 tests OK`.
- Produit novice: prochain succes utilisateur = traiter une piece/preuve manquante depuis `/pieces?proof=missing`.
- Architecture: micro-lot immediat recommande = reduire le bruit des artefacts locaux avant tout refactor `app.py` / `viewmodel.py`.

### Integre maintenant

- Lot `CONV-2026-0033` integre sur `.gitignore`.
- Exclusions ajoutees: `.codex-edge-profile-*/`, `.codex-tmp/`, `server/.tmp-test/`, `*.egg-info/`.
- Verification: `git check-ignore -v` confirme les quatre familles; `git status --short` ne remonte plus d'avertissement `Permission denied` sur `server/.tmp-test`.

### Prochain mouvement

- Ne pas lancer de gros onboarding abstrait.
- Continuer le produit via un petit lot `detail piece/preuve` sur `/pieces?proof=missing`, avec ownership explicite et tests token-safe/anti-fuite.
- Continuer la qualite via l'integration progressive des tests non suivis dans Git, par familles.

### Agents idle a relancer

- Nouvelle equipe lancee: QA, designer/novice, cartographie dev.
- Collision detectee et contenue: `CONV-2026-0025`..`0028` existaient deja; la relance courante utilise `CONV-2026-0029`..`0032`.

### Decision requise

- Aucune decision Brice bloquante a ce stade; la vague reste en cadrage lecture seule.

### Prochain mouvement

- Attendre les trois diagnostics courts, puis les consolider avec le lot code `CONV-2026-0025` au lieu d'ouvrir un deuxieme dev concurrent.

### Tests/preuves

- `CONV-2026-0030`: panier QA cible `42 tests OK` sur atelier pieces, viewmodel pieces, passation, memoire, securite et smoke.
- `CONV-2026-0031`: GO conditionnel novice pour un micro-detail piece/preuve dans `/pieces?proof=missing`.
- `CONV-2026-0032`: patch minimal recommande dans `pieces.html` + `test_ui_atelier_piece.py`; `viewmodel.py` a eviter.

## Point 23:18 CET - Second avis CH-2026-0007 cloture

### A tester maintenant

- Route prioritaire du lot code deja reserve: `/pieces?proof=missing&token=local-secret`.
- Verifier que la page distingue piece candidate, preuve validee, reponse recue et diffusion avant partage.

### En dev maintenant

- `CONV-2026-0025` reste owner du patch applicatif pieces.
- `CONV-2026-0029`..`0032` sont clotures en second avis lecture seule.

### En enquete maintenant

- Consensus: `detail piece/preuve` doit rester compact dans le flux pieces manquantes, pas devenir une fiche document globale.

### Prochain mouvement

- Consolider la sortie de `CONV-2026-0025`, relancer son panier de tests, puis seulement ensuite envisager une recette navigateur.

## Point 23:31 CET - Detail piece/preuve livre sur instance fraiche 8769

### A tester maintenant

- Instance de recette fraiche: `http://127.0.0.1:8769/?token=local-secret`.
- Parcours reel navigateur valide: `/pieces?proof=missing&token=local-secret` -> lien `Detail piece/preuve` -> `/pieces/UX-PIECE-COMP-C2B3F479?token=local-secret`.
- Ecran livre: fiche `Detail piece/preuve` avec pourquoi, preuve attendue, detenteur, piece candidate/preuve finale, diffusion et actions.

### En dev maintenant

- Lot `CONV-2026-0034` integre dans le repo principal:
  - `server/src/coproscope/web/piece_detail_view.py`;
  - `server/src/coproscope/web/templates/piece_detail.html`;
  - route additive `/pieces/{piece_id}` dans `server/src/coproscope/web/app.py`;
  - raccord minimal `Detail piece/preuve` dans `server/src/coproscope/web/templates/pieces.html`;
  - tests `server/tests/test_ui_piece_detail_route.py`.
- `viewmodel.py` evite.
- Serveur historique `8766` laisse intact; il servait l'ancienne version. Recette faite sur `8769` pour tester le code livre sans casser l'autre session.

### En enquete maintenant

- `CONV-2026-0036` relance designer/service + novice en lecture seule sur le prochain bloc: `Ajouter reponse recue` ou `Relancer syndic` contextualise depuis la fiche.
- Le designer doit produire la prochaine commande et indiquer le visuel image attendu.

### Commande prete

- Commande livree: detail piece/preuve depuis liste des pieces manquantes.
- Prochaine commande candidate: depot pre-rempli avec statut `reponse recue`, piece detail conservee, preuve candidate a verifier, aucune validation automatique.

### Agents idle a relancer

- QA `CONV-2026-0035` actif en lecture seule sur la livraison detail piece/preuve.
- Designer/novice `CONV-2026-0036` actif en lecture seule sur le prochain bloc.
- Cartographie dev `CONV-2026-0037` actif en lecture seule sur le prochain petit lot.
- Coordinateur garde l'integration et les arbitrages d'ownership.

### Decision requise

- Aucune decision Brice bloquante.
- Point a surveiller: capture image via in-app browser indisponible par timeout CDP; la recette DOM et les tests live sont verts.

### Prochain mouvement

- Attendre QA/design/cartographie.
- Si GO: implementer le plus petit lot `Ajouter reponse recue` pre-rempli depuis `/pieces/{piece_id}`.
- Si NO-GO QA: corriger le meme lot avant tout nouveau dev.

### Tests/preuves

- `.\.venv\Scripts\python.exe -B -m unittest tests.test_ui_piece_detail_route tests.test_ui_atelier_piece tests.test_ui_pieces_viewmodel tests.test_ui_document_viewer tests.test_ui_security_routes tests.test_ui_smoke_routes_expanded -v`: `29 tests OK`.
- Live `8769`: `tests.test_ui_live_ux_contract -v`: `5 tests OK`.
- HTTP live detail: `Detail piece/preuve`, `Pourquoi cette piece compte`, `Aucun envoi automatique`, no leak OK.
- Navigateur in-app: lien depuis liste compte `2`, clic vers detail OK, token conserve, no leak OK.

## Point 23:46 CET - Depot reponse recue pre-rempli livre sur 8770

### A tester maintenant

- Instance fraiche: `http://127.0.0.1:8770/?token=local-secret`.
- Parcours reel navigateur valide: `/pieces/UX-PIECE-COMP-C2B3F479?token=local-secret` -> `Ajouter reponse recue` -> `/depot?...&piece_detail=UX-PIECE-COMP-C2B3F479&token=local-secret`.
- Ecran livre: panneau `Reponse recue pour cette piece`, statut `Piece candidate a verifier`, preuve attendue, detenteur, diffusion, retour detail.

### En dev maintenant

- Lot `CONV-2026-0038` integre:
  - contexte depot allowliste dans `app.py`;
  - persistance `manifest["context"]` sans query brute dans `depot.py`;
  - panneau de pre-remplissage et champs caches dans `depot.html`;
  - harmonisation CTA `Ajouter reponse recue` depuis `piece_detail_view.py`;
  - tests depot + detail.
- `viewmodel.py` evite.

### En enquete maintenant

- Designer/novice recommande ensuite `Relancer syndic contextualise piece/preuve`.
- Commande UX disponible: brouillon non envoye, preuve attendue, garde-fou diffusion, suivi d'envoi hors CoproScope.

### Commande prete

- Prochain lot candidat: `/demandes/relance?piece_id=<piece_id>` enrichi depuis la fiche piece, sans envoi automatique.

### Agents idle a relancer

- QA `CONV-2026-0035` cloture GO.
- Designer `CONV-2026-0036` cloture avec commande relance contextualisee.
- Cartographie `CONV-2026-0037` cloture avec recommandation depot pre-rempli, maintenant livree.

### Decision requise

- Aucune.
- Note: le serveur historique `8766` et le serveur intermediaire `8769` restent ouverts; la recette du dernier code est sur `8770`.

### Prochain mouvement

- Lancer le lot `Relancer syndic contextualise piece/preuve`.
- Garder le meme pattern: commande novice -> petit dev -> tests produit live -> QA.

### Tests/preuves

- `.\.venv\Scripts\python.exe -B -m unittest tests.test_ui_depot_flow tests.test_ui_piece_detail_route tests.test_ui_atelier_piece tests.test_ui_pieces_viewmodel tests.test_ui_document_viewer tests.test_ui_requests_route tests.test_ui_security_routes tests.test_ui_smoke_routes_expanded -v`: `37 tests OK`.
- Live `8770`: `tests.test_ui_live_ux_contract -v`: `5 tests OK`.
- HTTP live depot prefill: `200`, prefill OK, hidden context OK, no leak OK.
- Navigateur in-app: clic depuis fiche piece vers depot pre-rempli OK; DOM confirme prefill, statut candidate, notice candidate, no leak.

## Point 01:28 CET - Relance piece/preuve contextualisee clarifiee

### A tester maintenant

- Parcours prioritaire: `/pieces/{piece_id}?token=local-secret` -> `Relancer syndic` -> `/demandes/relance?piece_detail=<piece_id>&token=local-secret`.
- Verifier en navigateur desktop/mobile que le premier viewport montre: brouillon non envoye, piece concernee, preuve attendue, detenteur, diffusion a verifier, retour detail piece/preuve et rattachement reponse.

### En dev maintenant

- Lot `CONV-2026-0040` integre comme micro-retouche du lot deja present:
  - libelles novice dans `server/src/coproscope/web/templates/relance_syndic.html`;
  - assertions relance dans `server/tests/test_ui_requests_route.py`;
  - contrat live dans `server/tests/test_ui_live_ux_contract.py`;
  - registres de coordination.
- Routes/helpers inchanges: `app.py`, `relance_syndic_view.py`, `piece_detail_view.py`, `viewmodel.py` evites.

### Decision produit

- GO technique: le couloir relance piece/preuve est token-safe, sans envoi automatique, et clair sur la piece concernee.
- GO produit complet en attente d'une vraie preuve navigateur multi-viewport, conformement au gate novice ajoute par l'audit UX/UI du 2026-05-22.

### Tests/preuves

- `.\.venv\Scripts\python.exe -B -m unittest tests.test_ui_requests_route tests.test_ui_piece_detail_route tests.test_ui_depot_flow tests.test_ui_atelier_piece tests.test_ui_security_routes tests.test_ui_smoke_routes_expanded -v`: `30 tests OK`.
- `.\.venv\Scripts\python.exe -B -m unittest tests.test_ui_live_ux_contract -v`: `5 tests OK`.
- `git diff --check -- server/src/coproscope/web/templates/relance_syndic.html server/tests/test_ui_requests_route.py server/tests/test_ui_live_ux_contract.py docs/presence_agents.md docs/point_coordination_live_8766_2026-05-21.md docs/roadmap_backlog_central.md`: OK.

## Point 09:42 CET - Module audit Cycle 9A livre

### A tester maintenant

- Commande locale: `vault import-audit360-rows`.
- Entree attendue: fichier Audit360 CSV/JSON/JSONL fictif ou public.
- Sortie attendue: resume derive sans racine locale, avec compteurs points/actions/pieces attendues et rappel que ce n'est pas une source de verite.

### En dev maintenant

- Lot audit `CONV-2026-0056` integre apres collision d'identifiant avec le chantier reconstruction.
- Ajout de `server/src/coproscope/modules/audit360.py`.
- Hook CLI ajoute dans `server/src/coproscope/cli.py`.
- Tests dedies ajoutes dans `server/tests/test_audit360_import.py`.
- Aucun ecran web audit cree; `viewmodel.py`, `app.py`, templates web et `vault/reconstruction.py` evites.

### Avis equipe

- Produit: prochain produit utile = reprise probatoire d'un seul constat, pas un gros tableau Audit360.
- Architecture: premier lot prudent = adaptateur import local + CLI, en reutilisant `import_audit360_rows`.
- QA: priorite suivante = durcir `share-audit`/`share-export` sur le scan de contenu avant publication large.

### Tests/preuves

- `tests.test_audit360_import -v`: `4 tests OK`.
- `tests.test_vault tests.test_pipeline tests.test_privacy tests.test_invoice_extractors -v`: `42 tests OK`.
- `tests.test_security_no_private_sync_leaks tests.test_ui_security_routes tests.test_ui_passation_export_route -v`: `28 tests OK`.
- `python -m bandit -r src -q --severity-level high`: OK.
- Suite complete: une passe `467 tests` a signale 4 echecs UI hors lot sur le couloir piece/detail/depot; relance ciblee ensuite `tests.test_ui_depot_flow tests.test_ui_piece_detail_route -v`: `10 tests OK`.

### Prochain mouvement

- Ne pas ouvrir encore d'UI audit.
- Traiter d'abord le risque QA: scanner le contenu des fichiers partageables et sanitiser/borner le manifeste `share-export`.

## Point 10:50 CET - Gate contenu share-audit/share-export

### A tester maintenant

- Commande publication: `share-audit` sur un depot candidat avant tout `share-export`.
- Cas a rejouer: un fichier en chemin autorise mais contenant un chemin local, `file://`, un token local ou une affectation de cle doit etre bloque sans afficher la valeur.

### En dev maintenant

- Lot `CONV-2026-0057` integre dans la frontiere publication:
  - `server/src/coproscope/core/share.py`: scan des fichiers texte publiables, ajout `content_violations`, retrait de `shareable`, blocage de la copie export;
  - `server/src/coproscope/cli.py`: `share-audit` retourne `1` si des violations de contenu existent;
  - `server/tests/test_pipeline.py`: tests audit/export/CLI avec valeurs sensibles construites dynamiquement pour ne pas polluer le depot.
- UI, templates, `viewmodel.py`, `vault/reconstruction.py` et modules Audit360 evites.

### Decision produit

- GO qualite pour la premiere garde publication: le coordinateur voit le chemin relatif, le statut `publication_blocked`, la raison `allowed_path_refused_content`, `value_masked` et l'effet `file_not_copied_to_public_export`.
- Tranche suivante a faire prudemment: email/IBAN/secret securite, avec tolerance explicite pour les fixtures demo/test afin de ne pas bloquer les exemples synthetiques utiles.

### Tests/preuves

- Panier cible hors sandbox Windows: `tests.test_pipeline` partage/CLI, `test_privacy` table de correspondance, `test_invoice_extractors` manifest extracteurs et `tests.test_audit360_import`: `9 tests OK`.
- `git diff --check` sur fichiers touches: OK.
- Limite: les tests creant des temporaires echouent dans le sandbox Windows (`AppData\\Local\\Temp` refuse), puis passent hors sandbox avec approbation.

## Point 09:39 CET - Gate live du couloir piece relance depot

### A tester maintenant

- Quand le backend in-app browser sera disponible: rejouer le parcours avec captures desktop/mobile:
  `/pieces/UX-PIECE-COMP-C2B3F479?token=local-secret` -> `Relancer syndic` -> `/demandes/relance?...piece_detail=UX-PIECE-COMP-C2B3F479` -> `Rattacher la reponse du syndic` -> `/depot?...piece_detail=UX-PIECE-COMP-C2B3F479`.
- Le gate automatisé couvre deja les marqueurs novice qui doivent rester dans la bande premier viewport: detail piece, relance, depot, preuve attendue, detenteur, diffusion, reponse candidate et retour detail.

### En dev maintenant

- Lot `CONV-2026-0052` integre comme gate de recette substitut, sans changement applicatif:
  - `server/tests/test_ui_live_ux_contract.py`: route stable `RELANCE_FLOW_ROUTES` et test `test_piece_relance_depot_flow_keeps_novice_markers_in_first_viewport_band`;
  - `server/tests/test_ui_piece_detail_route.py`: le CTA relance doit porter `piece_detail` et `token`;
  - `server/tests/test_ui_requests_route.py`: le CTA depot depuis la relance doit conserver `piece_detail`, `status=reponse-recue`, `return=pieces` et `token`;
  - `server/tests/test_ui_depot_flow.py`: la redirection post-upload depot reste tokenisee.
- Code applicatif evite: `app.py`, `viewmodel.py`, templates et helpers web.

### Decision produit

- GO regression/live automatisé: le couloir piece -> relance -> depot est couvert par serveur live local et TestClient.
- GO produit visuel encore conditionnel: Browser Use in-app browser a echoue avec aucun backend `iab` disponible; aucune capture desktop/mobile n'a donc ete produite.

### Tests/preuves

- Serveur frais `8782` lance depuis Node: `/health` OK sur `synthetic-copro`.
- `$env:COPROSCOPE_LIVE_URL='http://127.0.0.1:8782'; $env:COPROSCOPE_LIVE_REQUIRED='1'; .\.venv\Scripts\python.exe -B -m unittest tests.test_ui_live_ux_contract -v`: `6 tests OK`.
- Gate cible live: `test_piece_relance_depot_flow_keeps_novice_markers_in_first_viewport_band` + `test_p1_relance_and_missing_piece_routes_expose_useful_actions`: `2 tests OK`.
- TestClient chainage hors sandbox: `test_piece_detail_tokenizes_local_ctas_without_double_token`, `test_relance_syndic_route_prefills_from_piece_detail_without_fake_send`, `test_depot_upload_persists_received_answer_context_without_private_leaks`: `3 tests OK`.
- `git diff --check -- server/tests/test_ui_live_ux_contract.py server/tests/test_ui_piece_detail_route.py server/tests/test_ui_requests_route.py server/tests/test_ui_depot_flow.py docs/presence_agents.md docs/point_coordination_live_8766_2026-05-21.md docs/roadmap_backlog_central.md`: OK.

## Point 09:32 CET - Equipe reconstruction base/projections lancee

### A tester maintenant

- Instance cible: `C:\Users\brice\CoproScope\instances\beauvallon_test`.
- Symptôme utilisateur: depuis le site local, suspicion de base/projection a reconstruire.
- Aucun rebuild destructif avant diagnostic, sauvegarde et GO explicite.

### En dev maintenant

- `CONV-2026-0048`: coordination et preflight local.
- `CONV-2026-0049`: cartographie DB/projections et commandes de rebuild.
- `CONV-2026-0050`: QA sauvegarde, non-regression et criteres GO/NO-GO.
- `CONV-2026-0051`: generalisation du process en runbook reutilisable.

### Decision requise

- Trancher apres diagnostics: rebuild complet `pipeline run`, rebuild cible compta/decisions/incidents, ou simple regeneration des projections UI.

### Prochain mouvement

- Lancer `doctor` et inventaire des sorties derivees sur `beauvallon_test`.
- Ne pas supprimer les dossiers runtime; si rebuild requis, sauvegarder d'abord les outputs/projections reconstructibles.

### Diagnostic initial

- `doctor --instance-root beauvallon_test`: OK, chemins et dependances OK.
- `vault status`: OK, 1 evenement, 0 blob, 0 snapshot.
- `vault verify`: valide, 0 erreur.
- Registre documents: 1137 lignes.
- `outputs/accounting`: 0 fichier.
- `system/matrices`: 0 fichier.
- `outputs/reports/matrice_completude_documentaire.csv`: 0 ligne.
- `outputs/reports/pieces_a_demander.csv`: 0 ligne.

### Decision

- Il ne faut pas supprimer une "base" unique: CoproScope combine sources, registres, projections et vault.
- Le besoin probable est un rebuild cible des projections derivees, apres sauvegarde verifiee.

### Process generalise

- Runbook cree: `docs/runbook_reconstruction_base_projections.md`.
- Sequence recommandee: manifeste avant -> vault status/verify -> sauvegarde complete -> rebuild cible -> postchecks -> recette UI.

### Prochain mouvement

- Demander GO avant execution reelle du rebuild.
- Si GO: sauvegarde complete de `beauvallon_test`, puis `pipeline run --no-copy --docai off`, `accounting reconstruct --year 2025`, puis `decisions build` et `incidents build` seulement si leurs registres doivent etre regeneres.

## Point 12:52 CET - Rebuild cible Beauvallon execute

### A tester maintenant

- Site Beauvallon local: `http://127.0.0.1:8772/comptes?token=beauvallon-test-local`.
- Verifier aussi `actions` et `pieces?proof=missing` sur `8772`; la route passation/export reste a diagnostiquer car elle a depasse 60 secondes sur ce jeu reconstruit.

### En dev maintenant

- `CONV-2026-0063` a execute le runbook sur `C:\Users\brice\CoproScope\instances\beauvallon_test`.
- Preflight: `doctor` OK, `vault status/verify` OK.
- Sauvegardes verifiees:
  - `C:\Users\brice\CoproScope\dev\instance_support\sauvegardes\beauvallon_test\20260522-122035` avant pipeline, 2188 fichiers, 0 ecart;
  - `C:\Users\brice\CoproScope\dev\instance_support\sauvegardes\beauvallon_test\20260522-122854-post-pipeline` apres pipeline, 2195 fichiers, 0 ecart;
  - `C:\Users\brice\CoproScope\dev\instance_support\sauvegardes\beauvallon_test\20260522-123739-post-accounting` apres compta, 2210 fichiers, 0 ecart.
- Commandes lancees:
  - `pipeline run --no-copy --docai off`: OK;
  - `accounting reconstruct --year 2025`: OK, 827 factures, 601 ecritures, 827 controles, 1522 anomalies factures;
  - `accounting controls --year 2025`: OK, 827 controles, 0 P0;
  - copie controlee des matrices deja presentes dans l'instance vers `900_Systeme_Audit\coproscope_runtime\system\matrices`;
  - `missing-docs` et `kpi`: OK.

### Decision produit

- Verdict: `GO_TECHNIQUE_RECETTE_UI_RESTANTE`.
- On n'a pas supprime ni reconstruit une base unique: les sources ont ete conservees, sauvegardees et verifiees; seules les projections ciblees ont ete regenerees ou reconnectees.
- Decisions/incidents sont differes: pas de rebuild supplementaire sans besoin metier explicite.

### Tests/preuves

- `vault verify`: valide, 1 evenement, 0 erreur.
- Deltas finaux apres correction matrice: 2 fichiers matrices ajoutes, 7 fichiers logs/rapports/registres modifies, 0 suppression.
- Comptes UI: `8772/comptes` 200, marqueur Beauvallon present.
- Actions UI: `8772/actions` 200 apres timeout etendu, marqueur Beauvallon present.
- Pieces UI: `8772/pieces?proof=missing` 200, marqueur Beauvallon present.
- Tests serveur:
  - `tests.test_pipeline tests.test_comptascope tests.test_security_no_private_sync_leaks`: 27 OK;
  - `tests.test_vault tests.test_vault_core_hardening tests.test_vault_reconstruction_local tests.test_vault_reconstruction_archive`: 31 OK;
  - `tests.test_ui_security_routes tests.test_ui_smoke_routes_expanded tests.test_ui_passation_export_route tests.test_ui_comptes_guide`: 36 OK.

### Prochain mouvement

- Basculer le navigateur de `8771` vers `8772` pour voir la vraie instance Beauvallon.
- Diagnostiquer la lenteur passation/export sur donnees Beauvallon avant de declarer un GO produit complet.

## Point 12:25 CET - Plan de reprise avant AG

### A tester maintenant

- Utiliser des constats Audit360 anonymises ou fictifs uniquement.
- Verifier que seules les priorites `P0`/`P1` alimentent le plan et que chaque action garde une source et, si disponible, une preuve rattachee.

### En dev maintenant

- Lot `CONV-2026-0067` integre dans `server/src/coproscope/modules/agcontentieux.py`:
  - objets `PrecontentiousAction` et `PrecontentiousPlan` raccordes aux payloads evenementiels;
  - builder `build_precontentious_plan` pour demandes P1, reserves PV, pouvoirs/votes et corrections;
  - libelles produit: `A demander avant l'AG`, `A faire constater au PV si non leve`, `Pouvoirs et votes a tracer`, `Corrections a suivre apres AG`;
  - validation contre avis juridique automatique, donnees privees et marqueurs locaux (`C:\`, `file://`, token/secret, `raw`, `restricted`, `logs`).
- UI, CLI, Audit360, DecisionOps, vault/reconstruction et instance privee evites.
- Collision detectee puis repointee: le lot precontentieux utilise `CONV-2026-0067`..`0070`; `CONV-2026-0063`..`0066` restent au chantier `RM-2026-0004`.

### Decision produit

- GO technique pour un plan derive non-juridique et testable.
- Prochain mouvement: brancher ce plan sur une sortie prudente demandes P1/reserves PV, sans UI large avant gate privacy/novice.

### Tests/preuves

- `tests.test_agcontentieux -v`: `6 tests OK`.
- Audit360 sensible: `test_import_csv_creates_derived_objects_without_path_leak` et `test_rejects_private_hints_without_importing_or_echoing_values`: `2 tests OK`.
- DecisionOps AG/PV: `test_builds_decision_action_register_from_ag_resolutions` et `test_missing_proof_after_pv_is_marked_as_request_needed`: `2 tests OK`.

## Point 13:15 CET - Recette navigateur piece relance depot

### A tester maintenant

- Rejouer sur l'instance cible `8766`/Beauvallon avec un identifiant piece reel de cette instance: le test novice a signale que l'id synthetique `UX-PIECE-COMP-C2B3F479` y renvoie `404`.
- Garder le serveur frais `8784` comme preuve synthetique partageable du couloir.

### En dev maintenant

- Lot `CONV-2026-0075` integre:
  - `relance_syndic.html`: contexte piece/preuve/detenteur remonte dans le hero;
  - `depot.html`: contexte `Reponse recue pour cette piece` et `Piece candidate a verifier` remonte dans le premier bandeau quand `piece_detail` est present;
  - `styles.css`: pastilles/actions mobiles en colonne, largeur minimale flex corrigee, rupture des libelles longs.
- `app.py`, `viewmodel.py`, routes, modules et instances privees evites.
- Automation app: `relance-equipe-agile-coproscope` n'existait plus; heartbeat recree toutes les 30 minutes, statut `ACTIVE`, destination fil courant.

### Decision produit

- GO regression synthetique sur `8784`: le couloir piece -> relance -> depot est prouve desktop/mobile/tablette avec captures finales.
- GO utilisateur Beauvallon encore conditionnel: rejouer sur `8766` avec un identifiant piece existant dans l'instance cible.

### Tests/preuves

- Serveur frais `8784`: `/health` OK sur `synthetic-copro`.
- Browser Use: onglet in-app recharge sur `/depot?...piece_detail=UX-PIECE-COMP-C2B3F479&token=local-secret`.
- Captures finales: `docs/assets/ux-livraison-reelle-2026-05-22-piece-relance-depot/*-final2.png` (`1440x900`, `1366x768`, `390x844` x piece/relance/depot).
- Live gate: `tests.test_ui_live_ux_contract -v`: `6 tests OK`.
- Chainage token/securite: piece detail + relance + depot: `3 tests OK`.

## Point 13:17 CET - Perf passation Beauvallon

### A tester maintenant

- Si le serveur `8772` tourne encore depuis avant 13:17, le recharger avant de juger la route passation: le patch est applicatif.
- Rejouer `http://127.0.0.1:8772/actions?token=beauvallon-test-local` puis `http://127.0.0.1:8772/exports/passation?token=beauvallon-test-local`.
- Si `17s` reste trop long pour la recette, prochain lot = profiler `build_dashboard_model` lui-meme, pas relancer un rebuild de l'instance.

### En dev maintenant

- Lot `CONV-2026-0076` integre dans `server/src/coproscope/web/app.py`:
  - `context()` reutilise le `model` deja fourni par une route au lieu de recalculer le dashboard;
  - `_passation_export_document()` accepte un `dashboard_model` deja construit;
  - l'apercu passation et le detail blocage transmettent ce modele a la projection memoire et au template.
- `viewmodel.py`, templates, modules metier et instance privee evites hors mesures lecture.
- Automation: heartbeat actif `relance-equipe-agile-coproscope-2` remis a jour sur 30 minutes; l'app refuse un second heartbeat actif pour ce fil.

### Decision produit

- GO technique sur le timeout passation: le chemin HTML n'empile plus trois constructions dashboard.
- GO utilisateur Beauvallon encore conditionnel: recharger le live `8772`, finir la recette navigateur, puis seulement profiler plus profond si le dashboard unique reste trop lent.

### Tests/preuves

- Avant patch mesure locale: `build_dashboard_model` `21.2s`; document passation `32.5s`; ordre attendu route actions/passation environ `42s`/`75s`.
- Apres patch sur `beauvallon_test` via TestClient: `/actions` 200 en `17.2s`; `/exports/passation` 200 en `22.4s`.
- `tests.test_ui_passation_export_route -v`: `19 tests OK`.
- `tests.test_ui_security_routes tests.test_ui_smoke_routes_expanded -v`: `9 tests OK`.

## Point 13:59 CET - Gate piece relance depot avec id reel

### A tester maintenant

- Serveur Beauvallon frais laisse disponible: `http://127.0.0.1:8785/?token=beauvallon-test-local`.
- Le gate ne depend plus de l'id synthetique: `COPROSCOPE_LIVE_PIECE_ID=auto` decouvre un lien `/pieces/{id}` depuis `/pieces?proof=missing`.
- Verdict utilisateur Beauvallon: `NO-GO` tant que le couloir piece -> relance -> depot ne passe pas sans timeout.

### En dev maintenant

- Lot `CONV-2026-0077` integre dans `server/tests/test_ui_live_ux_contract.py`:
  - auto-decouverte d'un id piece public depuis la page live;
  - routes du couloir construites au moment du test;
  - libelles de sous-test masques pour ne pas recopier l'id reel dans les traces;
  - timeout live configurable via `COPROSCOPE_LIVE_TIMEOUT`.
- Code applicatif, templates, `viewmodel.py`, routes, modules et instance privee evites.

### Avis equipe

- QA: l'auto-decouverte est necessaire et prudente; Beauvallon expose des liens detail reels, mais piece/relance depassent les timeouts de recette et depot reste trop lent.
- Novice: garder visibles dans le premier viewport `Detail piece/preuve`, `Pourquoi cette piece compte`, `Brouillon a copier, non envoye`, `Piece concernee`, `Preuve attendue`, `A qui demander / qui doit l'avoir`, `Reponse recue pour cette piece` et `Piece candidate a verifier`.
- Cartographie: le prochain durcissement possible est de remplacer le parsing regex par `html.parser`, mais le verrou produit actuel est la performance.

### Tests/preuves

- Synthetique `8784`: `tests.test_ui_live_ux_contract -v` avec le defaut existant: `6 OK`.
- Synthetique `8784` avec `COPROSCOPE_LIVE_PIECE_ID=auto`: gate cible piece/relance/depot `1 OK`.
- TestClient chainage: `tests.test_ui_piece_detail_route tests.test_ui_requests_route tests.test_ui_depot_flow -v`: `16 OK`.
- Beauvallon `8785` avec `COPROSCOPE_LIVE_PIECE_ID=auto` et `COPROSCOPE_LIVE_TIMEOUT=35`: echec utile, pas 404; timeout sur relance contextualisee et lenteur constatee sur les routes du couloir.

### Prochain mouvement

- Profiler la construction de modele pour les routes piece/relance sur `beauvallon_test`.
- Rejouer ensuite le gate auto avec un timeout de recette normalise, puis seulement produire la preuve navigateur Beauvallon.

## Point 14:44 CET - Perf piece relance depot Beauvallon

### A tester maintenant

- Serveur synthetique partageable relance: `http://127.0.0.1:8784/?token=local-secret`, live contract `6 OK`.
- Serveur Beauvallon frais laisse disponible: `http://127.0.0.1:8786/?token=beauvallon-test-local`.
- Verdict utilisateur Beauvallon: toujours `NO-GO` tant que le gate auto ne passe pas avec `COPROSCOPE_LIVE_TIMEOUT=8` et tant que chaque ecran reste au-dessus de 5s.

### En dev maintenant

- Lot `CONV-2026-0086` integre:
  - `piece_detail_view.build_piece_detail` accepte un `dashboard_model` deja construit;
  - `relance_syndic_view.build_relance_syndic_view` et son contexte piece reutilisent ce modele;
  - `/pieces/{id}`, `/demandes/relance?piece_detail=...` et `/depot?...piece_detail=...` construisent le dashboard une seule fois puis le transmettent au template et au contexte piece;
  - tests de regression ajoutent un compteur pour verifier qu'une seule construction sert la page et le contexte.
- `viewmodel.py`, templates, modules metier et instance privee evites hors mesures lecture.

### Mesures avant / apres

- Avant patch TestClient Beauvallon:
  - `/pieces/{id}`: environ `38.4s`;
  - `/demandes/relance?piece_detail=...`: environ `35.8s`;
  - `/depot?...piece_detail=...`: environ `33.9s`.
- Apres patch TestClient Beauvallon:
  - `/pieces/{id}`: environ `16.0s`;
  - `/demandes/relance?piece_detail=...`: environ `18.3s`;
  - `/depot?...piece_detail=...`: environ `17.1s`.

### Avis equipe

- QA: panier minimal = tests piece/relance/depot, security/smoke, gate live auto; pas d'id reel dans les traces.
- Novice: GO produit seulement si chaque ecran repond sous `3s`, tolerance haute `5s`; `8s` reste un garde-fou technique, pas un confort utilisateur.
- Cartographie: prochain verrou = profiler `build_dashboard_model` lui-meme avec owner unique sur `viewmodel.py`.

### Tests/preuves

- `tests.test_ui_piece_detail_route tests.test_ui_requests_route tests.test_ui_depot_flow -v`: `19 OK`.
- `tests.test_ui_security_routes tests.test_ui_smoke_routes_expanded -v`: `9 OK`.
- Synthetique `8784`, `tests.test_ui_live_ux_contract -v`: `6 OK`.
- Beauvallon `8786`, gate auto avec `COPROSCOPE_LIVE_TIMEOUT=35`: `1 OK`.
- Beauvallon `8786`, gate auto avec `COPROSCOPE_LIVE_TIMEOUT=8`: echec attendu par timeout sur `/pieces?proof=missing`, donc NO-GO novice maintenu.

### Prochain mouvement

- Ouvrir un lot dedie `viewmodel.py` avec owner unique pour profiler `build_dashboard_model`.
- Cible: passer `/pieces?proof=missing`, detail piece, relance contextualisee et depot contextualise sous le timeout 8s, puis viser 3-5s avant GO utilisateur.

## Point 15:42 CET - Perf viewmodel Beauvallon

### A tester maintenant

- Serveur Beauvallon frais laisse disponible: `http://127.0.0.1:8787/?token=beauvallon-test-local`.
- Gate cible a conserver: `COPROSCOPE_LIVE_PIECE_ID=auto`, `COPROSCOPE_LIVE_TIMEOUT=8`, test `test_piece_relance_depot_flow_keeps_novice_markers_in_first_viewport_band`.
- Verdict utilisateur global: `NO-GO` tant que la suite live complete reste rouge ou que des ecrans critiques depassent durablement 5s.

### En dev maintenant

- Lot `CONV-2026-0091` integre dans `server/src/coproscope/web/viewmodel.py`:
  - fast-path sur la detection anti-fuite UX pour eviter de tokeniser les libelles sans marqueur suspect;
  - cache `lru_cache` sur les references interdites normalisees;
  - caches locaux texte/href dans `_sanitize_ux_public` pendant la sanitisation recursive du modele.
- Routes, templates, modules metier et instances privees evites hors mesures lecture.
- Automation verifiee: `relance-equipe-agile-coproscope` actif toutes les 30 minutes; doublon `relance-equipe-agile-coproscope-2` supprime.

### Mesures avant / apres

- Avant optimisation profonde: routes Beauvallon piece/relance/depot environ `16.0s` / `18.3s` / `17.1s` apres suppression des reconstructions redondantes.
- Apres patch viewmodel, mesures isolees TestClient Beauvallon:
  - `build_dashboard_model`: environ `3.8s` a `6.2s` selon passe;
  - `/pieces?proof=missing`: environ `4.2s`;
  - `/pieces/{id}`: environ `4.5s` a `5.6s`;
  - `/demandes/relance?...piece_detail=...`: environ `5.4s` a `5.7s`;
  - `/depot?...piece_detail=...`: environ `4.0s` a `6.4s`.

### Avis equipe

- QA: panier minimal vert requis = pieces/viewmodel/couloir + anti-fuite/smoke/passation + gate live cible.
- Novice: cible confort `3s`, tolerance haute `5s`; le gate `8s` est seulement un garde-fou technique.
- Cartographie: le verrou principal etait `_sanitize_ux_public`; prochain pas si besoin = reduire le volume du modele UX ou ajouter un cache route-scoped avec invalidation depot.

### Tests/preuves

- `tests.test_ui_pieces_viewmodel tests.test_ui_atelier_piece tests.test_ui_piece_detail_route tests.test_ui_requests_route tests.test_ui_depot_flow -v`: `27 OK`.
- `tests.test_ui_security_routes tests.test_ui_smoke_routes_expanded tests.test_ui_passation_export_route -v`: `28 OK`.
- `tests.test_ui_cockpit tests.test_ui_comptes_guide tests.test_ui_registre_actions -v`: `24 OK`.
- Beauvallon `8787`, gate cible piece -> relance -> depot avec `COPROSCOPE_LIVE_TIMEOUT=8`: `1 OK`.
- `git diff --check` sur fichiers touches: OK.
- Limite: la suite `tests.test_ui_live_ux_contract -v` complete a ete interrompue a 120s avec signaux hors-lot sur `/demandes`, `/ag-contentieux` et relance P1; le couloir cible etait vert avant interruption.

### Prochain mouvement

- Traiter les routes live hors-couloir qui restent lentes/rouges, puis rejouer la suite live complete.
- Produire ensuite la recette navigateur Beauvallon multi-viewport seulement si le gate complet est vert et si les ecrans critiques restent proches de 3-5s.
