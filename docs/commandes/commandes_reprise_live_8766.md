# Commandes de reprise live 8766

> Statut gouvernail: `SPEC_DERIVEE`.
> La source de verite roadmap est `docs/roadmap_backlog_central.md`.
> Toute commande de reprise doit etre rattachee a un `RM-*` et un `CH-*` avant dev.

Date de reference: 2026-05-21.

Perimetre: ecarts visibles entre les images cible Canva
`docs/assets/etude-utilisateurs/` et les captures live 8766
`docs/assets/ux-livraison-reelle-2026-05-21-8766/`.

Serveur live observe: `http://127.0.0.1:8766/?token=local-secret`.

Mission de ce document: donner aux devs front/back des tickets directement
exploitables, sans modifier le code et sans inventer de visuel.

## Ordre de reprise

1. P0 - Coque, navigation et premier viewport.
2. P0 - Cockpit Conseil Syndical.
3. P0 - Registre decisions, actions, preuves.
4. P1 - Controle des comptes.
5. P1 - Memoire de copropriete.
6. P1 - Vues de reprise: retards, relance syndic, pieces manquantes.
7. P2 - Demandes coproprietaires.
8. P2 - Pilotage indicateurs.
9. P2 - Ajout document et depot local.
10. P2 - AG, contentieux, passation.

## Garde-fous transverses

- Ne pas retirer les informations de coffre, role, sync et partage prive: les
  rendre compactes et actionnables.
- Ne pas afficher `novice` dans les libelles de navigation utilisateur.
- Ne pas laisser un bloc technique occuper le premier viewport au detriment de
  la tache metier.
- Tous les liens internes doivent conserver le token local ou fonctionner par le
  cookie local deja pose.
- Aucune route ne doit afficher chemin local, secret, `raw`, `vault` comme mot
  primaire, stacktrace ou message Jinja.
- Les etats vides doivent proposer un prochain geste clair.

---

## P0-01 - Recaler la coque, la navigation et le premier viewport

### Objectif utilisateur

A l'ouverture d'une route, un membre du conseil syndical doit comprendre en
moins de 5 secondes: ou il est, dans quel coffre il travaille, quel est son role
et quelle action metier faire maintenant, sans scroller.

### Image cible / capture live concernee

- Images cible: les quatre Canva de `docs/assets/etude-utilisateurs/`.
- Captures live concernees: `01_cockpit.png` a `12_depot.png`.
- Ecart visible: le live affiche un grand bloc `Contexte actif / Coffre courant
  / Role / Coffre signe / Sync / Prochaine action` sur presque tout le premier
  viewport. Les contenus metier commencent trop bas. La navigation live contient
  des numeros et des libelles de travail comme `Demandes novice` et
  `AG contentieux novice`. Le bouton `Nouvelle demande` est coupe a droite dans
  plusieurs captures.

### Structure visuelle attendue

- Sidebar sombre fixe, proche des Canva: marque en haut, sections lisibles,
  entree active nette, badges de compteurs alignes a droite.
- Navigation sans numeros visibles `01`, `02`, etc. Les numeros peuvent rester
  dans le code ou l'ordre, pas comme libelle principal.
- Topbar compacte: titre de page, recherche ou contexte minimal, actions
  globales. Aucun bouton ne doit etre tronque.
- Contexte coffre/role/sync sous forme de bandeau compact ou de chips de
  statut, hauteur cible desktop: 48 a 72 px, extensible au clic seulement.
- Le premier viewport doit afficher le titre, l'action principale et le debut
  du bloc metier prioritaire.
- Le bloc `Aide rapide` reste disponible mais replie par defaut, hors cas de
  risque ou onboarding explicite.

### Composants

- `AppShell` ou equivalent: sidebar, topbar, conteneur principal.
- `SidebarNav`: sections, items, compteurs, etat actif.
- `CompactContextBanner`: coffre courant, role, sync, coffre signe, prochaine
  action.
- `GlobalActionButton`: `Nouvelle demande` ou action specifique de page, avec
  menu responsive.
- `QuickHelpDisclosure`: aide repliee, accessible au clavier.
- Breakpoints desktop, compact desktop, tablette et mobile.

### Donnees necessaires

- `context_banner`: nom de coffre, role, niveau d'acces, etat coffre signe,
  etat sync, derniere verification, prochaine action et lien token-safe.
- `navigation`: libelles utilisateur, href token-safe, compteur, actif, section.
- `page_header`: titre, sous-titre optionnel, action primaire, action secondaire.
- `security_flags`: etat local prive, export autorise/interdit, sync non
  branchee, role a confirmer.

### Interactions

- Clic sur un item de sidebar: change de route ou de filtre sans perdre le
  token.
- Clic sur un compteur de sidebar: ouvre la vue filtree correspondante.
- Clic sur `details` du contexte: deploie les informations longues, puis peut
  se replier.
- Clic sur `prochaine action`: ouvre la route utile, par exemple gouvernance ou
  depot local, sans occuper le premier viewport par defaut.
- Sur mobile: sidebar en tiroir, contexte en resume une ligne, actions dans un
  menu.

### Etats vides

- Pas de coffre signe: afficher `Coffre signe a initialiser` en chip d'alerte
  avec lien `Preparer le coffre`, pas une grande carte.
- Role non confirme: afficher `Role a confirmer` avec action `Confirmer le
  role`, sans bloquer la lecture metier si la page est consultable.
- Sync non branchee: afficher `Sync non branchee` et `Prive local`, sans laisser
  croire a une publication automatique.
- Aucun compteur: afficher `0` ou masquer le badge, mais garder le lien stable.

### Criteres d'acceptation

- Sur toutes les captures live 8766, le contenu metier commence dans le premier
  viewport apres reprise.
- Aucune page ne consacre plus de 25% du premier viewport desktop a des cartes
  de contexte local.
- Le bouton global en haut a droite n'est jamais coupe a 999 px de largeur.
- Les libelles `novice`, `sync_root`, `local_root`, `vault`, `raw` ne sont pas
  visibles comme libelles primaires utilisateur.
- Chaque entree active de navigation correspond a la route affichee.
- Les compteurs de navigation qui annoncent une file de travail ouvrent une vue
  filtree ou un etat vide dedie.

### Tests attendus

- Captures navigateur: `999x693`, `1366x768`, `1440x900`, `390x844`.
- Smoke routes avec token sur `/`, `/actions`, `/comptes`, `/chantiers`,
  `/pieces`, `/demandes`, `/pilotage`, `/depot`.
- Test HTML statique: absence des libelles interdits en navigation primaire.
- Test responsive: pas de scroll horizontal global, pas de bouton tronque, focus
  visible sur navigation et actions.

---

## P0-02 - Reprendre le cockpit comme table de travail prioritaire

### Objectif utilisateur

Un membre CS ouvre le cockpit pour savoir quoi traiter maintenant: retards,
pieces manquantes, demandes syndic, echeances AG, risques et controles comptes.
Il doit pouvoir partir de chaque carte vers la bonne file de travail.

### Image cible / capture live concernee

- Image cible: `docs/assets/etude-utilisateurs/cockpit-conseil-syndical.png`.
- Capture live: `docs/assets/ux-livraison-reelle-2026-05-21-8766/01_cockpit.png`.
- Ecart visible: la capture live montre surtout le contexte local. Le bloc
  cockpit reel n'apparait qu'en bas du viewport et le rang `A traiter` n'est pas
  lisible au premier regard.

### Structure visuelle attendue

- En-tete: `Cockpit Conseil Syndical`, phrase courte de situation, recherche
  globale, action `Nouvelle demande`.
- Rang `A traiter`: cinq cartes horizontales desktop, avec icone, compteur,
  libelle et micro-consequence:
  `Actions en retard`, `Pieces manquantes`, `Demandes syndic`,
  `Echeances AG`, `Alertes et risques`.
- Deuxieme zone: quatre panneaux de travail en grille:
  `Pieces manquantes`, `Demandes syndic`, `AG`, `Controle comptes`.
- Bas de page visible apres le premier rang: tableau/liste `Alertes et risques`
  avec niveaux, sujet, detail, impact, echeance, statut.
- La page doit etre dense et operable, pas un hero ni une page de diagnostic.

### Composants

- `PriorityCard` avec href et statut.
- `MissingPiecesPanel` avec taux de completude et rubriques.
- `SyndicRequestsPanel` avec onglets ou etats `En attente`, `En cours`,
  `Resolues`.
- `AGPanel` avec dates et prochaines echeances.
- `AccountingSummaryPanel` avec score, P1/P2/OK et lien detail.
- `RiskTable` ou liste compacte d'alertes.
- `GlobalSearch` et `NewRequestSplitButton`.

### Donnees necessaires

- Compteurs: actions en retard, pieces manquantes, demandes syndic, echeances
  AG, alertes.
- Pour chaque carte: href token-safe, severite, raison courte, nombre critique.
- Completeness documentaire par rubrique.
- Demandes syndic: titre, domaine, date de relance, statut, criticite.
- AG: date, type d'echeance, nombre de jours restants ou retard.
- Comptes: score ou synthese, P1/P2/OK, points a surveiller.
- Alertes: niveau, sujet, detail, impact, detection/echeance, statut.

### Interactions

- Carte `Actions en retard`: ouvre `/actions?priority=P1` ou vue retards
  dediee.
- Carte `Pieces manquantes`: ouvre `/pieces?proof=missing`.
- Carte `Demandes syndic`: ouvre `/actions?scope=syndic` ou vue relance.
- Carte `Echeances AG`: ouvre une vue AG/echeances filtree.
- Carte `Alertes et risques`: ouvre la liste des risques a traiter.
- Boutons `Voir tout`: ouvrent la vue filtree du panneau.
- `Nouvelle demande`: propose creer demande coproprietaire, action CS, relance
  syndic, piece a demander.

### Etats vides

- Aucun retard: carte verte `Aucun retard detecte` avec lien vers actions en
  cours.
- Aucune piece manquante: afficher les rubriques completes et le prochain
  controle documentaire.
- Aucune demande syndic: proposer `Preparer une question` ou `Voir l'historique`.
- Aucun risque: garder la table avec message `Aucune alerte active`.
- Donnee de compte indisponible: afficher `Controle a calculer`, pas un tiret
  muet.

### Criteres d'acceptation

- En `1366x768`, le titre cockpit et les cinq cartes `A traiter` sont visibles
  sans scroll.
- Chaque carte prioritaire est cliquable et son lien rend une route 200 ou un
  etat vide dedie.
- Le cockpit ne montre pas les cartes de contexte comme contenu principal.
- Les compteurs de la sidebar et des cartes cockpit restent coherents.
- Aucun panneau n'affiche seulement un chiffre sans expliquer le prochain geste.

### Tests attendus

- Test route `/` avec token: statut 200, titre, cinq cartes et liens presents.
- Test clic href des cinq cartes en TestClient ou navigateur.
- Screenshot desktop `1366x768` compare a `cockpit-conseil-syndical.png`.
- Screenshot mobile `390x844`: cartes empilees avant les panneaux secondaires.
- Test accessibilite: cartes focusables avec nom accessible et consequence.

---

## P0-03 - Reprendre le registre decisions/actions/preuves

### Objectif utilisateur

Depuis une decision d'AG, un membre CS doit suivre l'action concrete, les
preuves, les pieces liees, les relances syndic et l'historique, sans chercher
dans un tableau ou une route fragile.

### Image cible / capture live concernee

- Image cible: `docs/assets/etude-utilisateurs/registre-decisions-actions-preuves.png`.
- Capture live: `docs/assets/ux-livraison-reelle-2026-05-21-8766/02_actions.png`.
- Ecart visible: le live garde le grand contexte local au-dessus du registre.
  La structure cible en deux colonnes, avec liste d'AG a gauche et fiche
  decision a droite, n'est pas visible dans le premier viewport.

### Structure visuelle attendue

- En-tete: `Registre des decisions`, sous-titre court, recherche, `Exporter le
  registre`, `Nouvelle action`.
- Colonne gauche desktop: `Toutes les AG`, filtre, resolutions groupees par date
  d'AG, badges `Terminee`, `Action en cours`, `En retard`.
- Zone droite: fiche decision selectionnee avec numero de resolution, titre,
  statut, date AG, synthese novice.
- Cartes resume: responsable, echeance, statut, priorite.
- Onglets: `Action en cours`, `Preuves`, `Pieces liees`, `Relance syndic`,
  `Historique`.
- Contenu onglet visible au premier viewport: suivi action, documents, preuves
  d'execution, relances et timeline.

### Composants

- `DecisionRegisterHeader`.
- `AGResolutionList` avec filtre.
- `ResolutionDetailHeader`.
- `ActionSummaryCards`.
- `DecisionTabs`.
- `ActionFollowupCard`.
- `LinkedDocumentsCard`.
- `EvidenceCard`.
- `SyndicReminderCard`.
- `ActionHistoryTimeline`.

### Donnees necessaires

- AG: id, date, libelle, resolutions.
- Resolution: numero, titre, texte synthetique, texte source optionnel, statut,
  majorite, date vote.
- Action: responsable, referent CS, echeance, priorite, avancement, prochaine
  etape.
- Preuves: id, type, titre, source, date, statut de verification, diffusion.
- Pieces liees: role de piece, type fichier, date ajout, statut preuve ou piece
  candidate.
- Relances: brouillon, date envoyee, canal note, statut reponse, prochaine
  relance.
- Historique: date, evenement, auteur, piece ou preuve associee.
- Filtres: AG, statut, responsable, retard, preuve manquante, priorite.

### Interactions

- Clic resolution: selectionne la fiche a droite sans perdre la liste.
- Filtres: reduisent la colonne gauche et gardent la selection si possible.
- `Nouvelle action`: propose `Rattacher a une decision AG` puis `Action libre`.
- `Mettre a jour l'avancement`: demande etat, commentaire, preuve optionnelle,
  date de prochaine relance.
- `Ajouter une preuve`: choisir document existant, ajouter fichier, saisir note
  de verification ou marquer preuve a demander.
- `Preparer une relance syndic`: ouvre brouillon copiable, sans envoi
  automatique.
- `Exporter le registre`: demande perimetre et diffusion avant export.

### Etats vides

- Aucune resolution: afficher `Aucune decision AG chargee` avec action
  `Importer un PV d'AG` ou `Ajouter une action libre`.
- Aucune selection: selectionner par defaut la premiere action ouverte ou
  afficher un panneau `Choisissez une decision`.
- Aucune preuve: expliquer ce qui rendrait l'action prouvable et proposer
  `Ajouter une preuve` ou `Demander une piece`.
- Aucune relance: proposer un brouillon si une piece ou reponse manque.
- Aucun historique: afficher `Aucun evenement de suivi pour cette decision`.

### Criteres d'acceptation

- `/actions` rend une fiche stable sans action preselectionnee par l'utilisateur.
- En desktop, la liste AG et la fiche detail sont visibles ensemble au premier
  viewport.
- Les onglets changent de contenu sans changer de resolution.
- Les preuves sont distinguees des pieces candidates.
- Les routes filtrees depuis le cockpit rendent en 200:
  `/actions?priority=P1`, `/actions?status=a_demander`,
  `/actions?scope=syndic`.
- Aucun message Jinja ou attribut manquant ne peut etre vu par l'utilisateur.

### Tests attendus

- Tests route `/actions` et routes filtrees avec token.
- Test selection d'une resolution puis changement d'onglet.
- Test etat vide sans action seed.
- Screenshot `1366x768` et `1440x900` compare a la cible registre.
- Test mobile: liste puis detail en tiroir ou page detail, sans scroll
  horizontal.

---

## P1-04 - Reprendre le controle des comptes comme guide avant AG

### Objectif utilisateur

Un membre CS non comptable doit identifier les postes a traiter, comprendre
pourquoi ils sont OK/P2/P1, formuler une question au syndic et garder une note
pour l'AG.

### Image cible / capture live concernee

- Image cible: `docs/assets/etude-utilisateurs/controle-comptes-guide.png`.
- Capture live: `docs/assets/ux-livraison-reelle-2026-05-21-8766/03_comptes.png`.
- Ecart visible: le live affiche le contenu comptes, mais encore trop bas. Les
  KPI sont a `0` ou `A calculer`, le tableau categorie et l'inspecteur droit ne
  sont pas visibles dans le premier viewport.

### Structure visuelle attendue

- En-tete: `Controle des comptes`, selecteur exercice, action `Exporter le
  rapport`.
- Rang KPI: total charges, factures rapprochees, P2 a confirmer, P1
  prioritaire, pieces manquantes.
- Bloc `Depenses par categorie`: filtres categorie, statut, fournisseur, toggle
  `Afficher aussi les categories sans alerte`.
- Tableau categories: categorie, montant charges, factures rapprochees, ecart,
  statut, alertes, chevron.
- Inspecteur droit desktop: detail de la categorie selectionnee, onglets
  `Detail`, `Pieces`, `Questions au syndic`, `Rapport AG`.
- Legende couleur + consequence en bas de tableau.

### Composants

- `AccountingHeader`.
- `ExerciseSelector`.
- `AccountingKpiCard`.
- `AccountingFilters`.
- `CategoryControlTable`.
- `CategoryInspector`.
- `SyndicQuestionList`.
- `ReportAGPanel`.
- `ExportReportDialog`.

### Donnees necessaires

- Exercice courant, periode, date de mise a jour, source d'import.
- KPI: total charges ou `Montant non charge`, postes analyses, ratio factures
  rapprochees, P1, P2, pieces manquantes.
- Categories: libelle, icone, montant, rapprochement, ecart, statut, nombre
  alertes, fournisseur principal optionnel.
- Detail categorie: alertes, pieces attendues, factures concernees, questions
  syndic, note AG, niveau de confiance.
- Exports: perimetre `Interne CS`, `Rapport AG`, `Questions syndic`,
  `Pieces a demander`, diffusion autorisee.

### Interactions

- Clic KPI: filtre le tableau et actualise l'inspecteur.
- Clic ligne categorie: ouvre le detail dans l'inspecteur droit.
- Toggle categories sans alerte: conserve les P1/P2 visibles en priorite.
- Filtre fournisseur: affiche les categories contenant ce fournisseur.
- `Ajouter une question syndic`: cree un brouillon relie a la categorie.
- `Ajouter une note AG`: ajoute une reserve ou un point de presentation.
- `Exporter le rapport`: ouvre confirmation de perimetre et avertit si donnees
  internes ou pieces sensibles.

### Etats vides

- Donnees non chargees: afficher `Controle a calculer` avec action `Importer ou
  rapprocher les factures`.
- Aucun P1/P2: afficher les categories OK et proposer `Voir le rapport AG`.
- Aucune piece manquante: afficher `Toutes les pieces attendues sont rattachees`
  avec derniere date de verification.
- Aucun detail categorie: afficher `Selectionnez une categorie`.

### Criteres d'acceptation

- En `1366x768`, le rang KPI et le debut du tableau sont visibles sans scroll.
- En `1440x900`, le tableau et l'inspecteur droit sont visibles ensemble.
- Aucun KPI ne se limite a `0` sans expliquer s'il s'agit d'une absence de
  donnee ou d'un resultat reel.
- Les statuts P1/P2/OK sont accompagnes d'une phrase humaine.
- Une categorie P1 ou P2 peut produire une question syndic ou une note AG.

### Tests attendus

- Test route `/comptes` avec donnees synthetiques et token.
- Test filtres KPI, categorie, statut, fournisseur.
- Test clic ligne -> inspecteur.
- Test export prudence avec choix de perimetre.
- Screenshots desktop et mobile compares a `controle-comptes-guide.png`.

---

## P1-05 - Reprendre la memoire de copropriete en timeline de passation

### Objectif utilisateur

Un nouveau membre CS doit comprendre l'historique utile de l'immeuble, les
sujets ouverts, les preuves disponibles et les elements a transmettre, sans
fouiller dans des chantiers ou des compteurs abstraits.

### Image cible / capture live concernee

- Image cible: `docs/assets/etude-utilisateurs/memoire-copropriete.png`.
- Capture live: `docs/assets/ux-livraison-reelle-2026-05-21-8766/04_memoire.png`.
- Ecart visible: le live affiche le bon titre, mais la timeline cible et la
  colonne droite de passation ne sont pas visibles au premier viewport. Des
  cartes KPI occupent l'espace principal.

### Structure visuelle attendue

- En-tete: `Memoire de copropriete`, sous-titre, `Exporter`, bouton split
  `Ajouter un evenement`.
- Barre de recherche: `Rechercher un evenement, un contrat, un document...`,
  bouton `Filtres`, controle segmente `5 ans`, `10 ans`, `Tout`.
- Zone centrale: grande timeline datee, du plus recent au plus ancien, avec
  point couleur, icone, titre, sous-titre, badge categorie, chevron.
- Colonne droite: `Passation CS` avec progression, checklist `Sujets ouverts`,
  puis panneau `A transmettre`.
- Les KPI peuvent exister, mais pas avant la timeline cible.

### Composants

- `MemoryHeader`.
- `MemorySearchFilters`.
- `PeriodSegmentedControl`.
- `TimelineEventList`.
- `TimelineEventRow`.
- `PassationPanel`.
- `OpenTopicsChecklist`.
- `DocumentsToTransmitPanel`.
- `AddEventSplitButton`.
- `MemoryExportDialog`.

### Donnees necessaires

- Evenements: date, titre, description, categorie, couleur, icone, statut,
  diffusion, preuve liee, source.
- Filtres: periode, categorie, statut, diffusion, preuve.
- Passation: total elements, elements completes, progression, sujets ouverts,
  restrictions, prochain geste.
- Documents a transmettre: titre, type, date mise a jour, diffusion,
  telechargement autorise ou a biffer.
- Exports derives: passation texte, passation JSON, apercu passation.

### Interactions

- Recherche: filtre timeline et panneaux de droite.
- `Filtres`: ouvre categorie, statut, diffusion, preuve.
- Periode `5 ans / 10 ans / Tout`: ajuste la timeline et persiste dans l'URL.
- Clic evenement: ouvre detail avec preuves et liens vers action, demande,
  compte ou document.
- `Ajouter un evenement`: ouvre une saisie locale, pas une ecriture brute
  immediate.
- `Exporter`: demande perimetre, restrictions et statut derive avant
  telechargement.

### Etats vides

- Aucun evenement: afficher `Aucun evenement dans cette periode` avec action
  `Elargir la periode` ou `Ajouter un evenement`.
- Aucun sujet ouvert: afficher une checklist complete et proposer `Preparer la
  passation`.
- Aucune piece a transmettre: afficher `Aucun document transmissible sans
  verification` si les documents sont restreints.
- Evenement sans date: regrouper sous `Date a confirmer`, pas en haut de
  timeline.

### Criteres d'acceptation

- En desktop, la timeline et la colonne `Passation CS` sont visibles ensemble.
- L'entree active de navigation dit `Memoire de copropriete`, pas `Chantiers`.
- Les cartes KPI ne precedent pas la timeline dans la lecture principale.
- Les documents a transmettre affichent leur restriction ou statut de diffusion.
- Le bouton d'export ne produit pas de source de verite brute sans confirmation.

### Tests attendus

- Test route `/chantiers` avec titre `Memoire de copropriete`.
- Test filtre periode et recherche.
- Test clic evenement -> detail.
- Test export passation avec restrictions.
- Screenshots desktop/mobile compares a `memoire-copropriete.png`.

---

## P1-06 - Finaliser les vues de reprise: retards, relance syndic, pieces manquantes

### Objectif utilisateur

Depuis le cockpit, un membre CS doit pouvoir ouvrir une file de travail dediee,
comprendre pourquoi chaque sujet existe et enchainer vers le bon geste:
relancer, demander une piece, rattacher une preuve ou mettre a jour l'action.

### Image cible / capture live concernee

- Images cible de derivation: `cockpit-conseil-syndical.png` et
  `registre-decisions-actions-preuves.png`.
- Captures live:
  - `05_retards.png`;
  - `06_relance_syndic.png`;
  - `07_pieces_manquantes.png`.
- Ecart visible: les trois vues ont la meme coque trop haute. Le titre de la
  file apparait, mais la liste de travail ou le detail actionnable n'est pas
  visible dans le premier viewport.

### Structure visuelle attendue

- En-tete de file: titre explicite, description courte, action primaire.
- Filtres rapides: statut, priorite, responsable, domaine, echeance, preuve.
- Layout desktop: liste a gauche ou centre, detail selectionne a droite.
- Chaque ligne de file contient: sujet, rattachement, echeance, raison, preuve
  attendue, derniere action, prochaine action.
- Vue retards: prioriser echeance depassee et impact.
- Vue relance syndic: prioriser brouillons, relances envoyees sans reponse et
  reponses a verifier.
- Vue pieces manquantes: prioriser piece attendue, raison, action de demande ou
  rattachement.

### Composants

- `WorkQueueHeader`.
- `WorkQueueFilters`.
- `WorkQueueList`.
- `WorkQueueItem`.
- `WorkQueueDetail`.
- `ReminderDraftPanel`.
- `MissingPieceDetail`.
- `ProofAttachAction`.
- `QueueEmptyState`.

### Donnees necessaires

- Actions en retard: id, titre, decision ou source, responsable, echeance,
  jours de retard, impact, preuve attendue, relance proposee.
- Relances syndic: sujet, destinataire, preuve demandee, dernier envoi, canal,
  statut, brouillon, reponse a verifier.
- Pieces manquantes: libelle piece, rubrique, action ou decision rattachee,
  source attendue, criticite, pieces candidates locales.
- Liens token-safe vers action, piece, demande, compte ou memoire.
- Etats de diffusion: interne CS, transmissible, apres biffage, bloque.

### Interactions

- Clic depuis une carte cockpit: ouvre la file avec filtre visible.
- Clic ligne: ouvre detail sans perdre la file.
- `Preparer une relance`: genere un brouillon copiable et enregistre une action
  de suivi, sans envoi automatique.
- `Demander cette piece`: cree ou ouvre une demande syndic.
- `Rattacher une preuve`: propose piece existante, fichier local ou note de
  verification.
- `Exporter une liste de travail`: export interne apres apercu.

### Etats vides

- Aucun retard: afficher `Aucune action en retard` et proposer `Voir actions en
  cours`.
- Aucune relance: afficher `Aucune relance syndic a preparer` et proposer
  `Voir demandes resolues`.
- Aucune piece manquante: afficher `Aucune piece manquante detectee` et date de
  derniere verification.
- Aucune piece candidate: expliquer comment ajouter depuis le depot local.

### Criteres d'acceptation

- Les routes issues du cockpit rendent en 200 avec ou sans donnees.
- Le premier viewport montre au moins trois lignes de file ou l'etat vide
  dedie.
- Les vues ne sont pas de simples titres suivis d'un bloc contexte.
- Chaque ligne a une action primaire nommee.
- La relance syndic indique clairement que l'envoi se fait hors outil ou apres
  confirmation explicite.

### Tests attendus

- Test `/actions?priority=P1`, `/actions?scope=syndic`,
  `/actions?status=a_demander`, `/pieces?proof=missing`.
- Test etat vide pour chaque file.
- Test donnees seed: clic ligne -> detail -> action primaire.
- Screenshot `999x693` pour verifier que la file est visible dans le premier
  viewport.
- Test anti-regression: aucun message Jinja `dict object has no attribute`.

---

## P2-07 - Rendre la boite de demandes coproprietaires exploitable

### Objectif utilisateur

Un membre CS doit suivre les demandes coproprietaires multi-canaux, savoir qui
demande quoi, depuis quand, quel canal a ete utilise, quelle reponse ou piece
est attendue, et ce qui peut etre partage.

### Image cible / capture live concernee

- Pas de Canva dedie. Deriver la structure de travail du cockpit et du registre.
- Capture live: `docs/assets/ux-livraison-reelle-2026-05-21-8766/08_demandes.png`.
- Ecart visible: le contenu `Boite de demandes` commence sous le contexte local
  et est coupe dans le premier viewport. La navigation affiche `Demandes
  novice`.

### Structure visuelle attendue

- En-tete: `Boite de demandes`, description courte, action `Nouvelle demande`.
- Filtres: statut, canal, demandeur, domaine, urgence, preuve attendue.
- Colonnes ou liste: demande, coproprietaire ou source, canal, statut, derniere
  activite, prochaine action.
- Detail lateral: contexte, messages, pieces, decision de diffusion, action de
  reponse ou transfert.
- Vue liee au registre si une demande devient action, relance ou preuve.

### Composants

- `RequestsHeader`.
- `RequestFilters`.
- `RequestList`.
- `RequestStatusBadge`.
- `RequestDetailPanel`.
- `RequestTimeline`.
- `RequestReplyDraft`.
- `RequestEvidenceLinks`.

### Donnees necessaires

- Demande: id, titre, demandeur, lot optionnel, canal, date reception, statut,
  priorite, domaine.
- Messages: date, canal, contenu derive ou resume, auteur, pieces jointes.
- Liens: action, piece, preuve, AG, memoire, syndic.
- Diffusion: visible CS, reponse coproprietaire, a biffer, confidentiel.

### Interactions

- Clic demande: ouvre le detail.
- `Nouvelle demande`: saisie locale avec canal et source.
- `Preparer une reponse`: brouillon copiable, pas d'envoi automatique.
- `Transformer en action`: cree une action registre avec preuve attendue.
- `Rattacher une piece`: ouvre selection depot/documents.
- Filtres et recherche persistent dans l'URL.

### Etats vides

- Aucune demande: afficher `Aucune demande en cours` et proposer `Ajouter une
  demande recue hors outil`.
- Aucun message: afficher `Aucun echange trace`.
- Demande sans canal: afficher `Canal a confirmer`.
- Demande sensible: afficher restriction avant brouillon ou export.

### Criteres d'acceptation

- La navigation affiche `Demandes`, pas `Demandes novice`.
- Le premier viewport montre liste ou etat vide dedie.
- Une demande peut etre reliee a une action, une piece ou une preuve.
- Le statut ne repose pas seulement sur la couleur.
- Les brouillons n'annoncent pas un envoi automatique.

### Tests attendus

- Test route `/demandes` avec token.
- Test filtres statut/canal.
- Test creation brouillon reponse.
- Test transformation demande -> action ou lien action.
- Screenshot desktop/mobile sans contenu coupe.

---

## P2-08 - Rendre le pilotage indicateurs lisible et relie au cockpit

### Objectif utilisateur

Un membre CS doit voir les indicateurs a surveiller, comprendre leur tendance,
leur source et leur prochaine action, sans entrer dans un tableau technique.

### Image cible / capture live concernee

- Pas de Canva dedie. Deriver du cockpit pour la synthese et du controle des
  comptes pour les details filtrables.
- Capture live: `docs/assets/ux-livraison-reelle-2026-05-21-8766/09_pilotage.png`.
- Ecart visible: la page `Pilotage` est cachee sous la coque de contexte. Les
  indicateurs ne sont pas lisibles dans le premier viewport.

### Structure visuelle attendue

- En-tete: `Pilotage`, sous-titre court, periode, export interne.
- Rang KPI: risques, retards, charges, demandes, pieces, AG ou categories
  utiles.
- Bloc principal: indicateurs par domaine avec statut, tendance, source,
  prochaine action.
- Panneau detail: explication novice, dernier calcul, liens vers comptes,
  actions, demandes ou memoire.
- Zone basse: alertes recentes et decisions a reprendre.

### Composants

- `PilotageHeader`.
- `IndicatorKpiCard`.
- `IndicatorGrid`.
- `IndicatorTrend`.
- `IndicatorDetailPanel`.
- `IndicatorSourceLink`.
- `PilotageAlertsList`.

### Donnees necessaires

- Indicateur: id, nom, domaine, valeur, unite, tendance, seuil, statut,
  source, derniere mise a jour.
- Liens vers routes metier: action, compte, demande, piece, memoire.
- Periode ou exercice courant.
- Droits de diffusion et statut local.

### Interactions

- Clic KPI ou indicateur: ouvre detail et filtre les alertes.
- Clic source: ouvre la route metier correspondante.
- Export: apercu interne, pas diffusion externe directe.
- Filtre domaine/periode: conserve token et met a jour l'URL.

### Etats vides

- Aucun indicateur: afficher `Aucun indicateur calcule` avec action `Recalculer`
  ou `Importer des donnees`.
- Source manquante: afficher `Source a verifier`.
- Tendance indisponible: afficher `Pas assez d'historique`, pas une fleche
  muette.

### Criteres d'acceptation

- Le premier viewport montre au moins le rang KPI et le debut de la grille.
- Chaque indicateur expose une source et une prochaine action.
- Les indicateurs du cockpit renvoient vers cette page ou inversement avec
  coherence.
- Aucun chiffre n'est affiche sans unite ou signification.

### Tests attendus

- Test route `/pilotage` avec token.
- Test filtre domaine/periode.
- Test clic indicateur -> detail.
- Screenshot desktop/mobile.
- Test source links token-safe.

---

## P2-09 - Reprendre ajout document et depot local en parcours unique

### Objectif utilisateur

Un utilisateur ajoute un document local, comprend ou il va, quel statut il a,
ce qu'il peut prouver, et s'il est transmissible ou reserve au conseil
syndical.

### Image cible / capture live concernee

- Pas de Canva dedie. Deriver du cockpit pour le depot local et du registre pour
  le rattachement preuve/action.
- Captures live:
  - `10_ajout_document.png`;
  - `12_depot.png`.
- Ecart visible: les deux pages sont masquees par le contexte local. Le premier
  geste d'ajout ou de depot n'est pas visible immediatement.

### Structure visuelle attendue

- En-tete: `Ajout de document` ou `Depot local`, avec phrase `aucune publication
  automatique`.
- Zone principale: dropzone/fichier, ou liste de documents recemment deposes.
- Etapes: importer, classifier, rattacher, verifier diffusion.
- Panneau de droite ou bas: pieces candidates, actions/decisions liees,
  restrictions.
- File de traitement: document, type detecte, statut, prochain geste.

### Composants

- `DocumentIntakeHeader`.
- `LocalDropZone`.
- `DocumentIntakeSteps`.
- `CandidateDocumentList`.
- `DocumentClassificationCard`.
- `AttachToActionPanel`.
- `DiffusionReviewChip`.
- `DepotQueue`.

### Donnees necessaires

- Document: id, nom affiche, type, taille, date ajout, statut, hash court si
  utile mais non primaire, restriction.
- Classification: categorie proposee, confiance, preuve candidate, action ou
  decision rattachee.
- Depot local: emplacement logique, pas chemin Windows brut.
- Diffusion: prive CS, transmissible, apres biffage, bloque.
- Liens vers pieces, actions, demandes, memoire.

### Interactions

- Ajouter un fichier: selection ou glisser-deposer.
- Classifier: choisir type, rubrique, exercice, categorie.
- Rattacher: action, resolution, demande, evenement memoire ou compte.
- Marquer comme preuve: demande confirmation du role de preuve.
- Revoir diffusion: affiche ce qui peut sortir ou rester prive.
- Ouvrir document: apercu si possible, telechargement prudent sinon.

### Etats vides

- Aucun document depose: dropzone visible avec message local-first.
- Document non classifie: afficher `A classer` et action `Choisir une rubrique`.
- Aucune action liee: proposer `Rattacher plus tard`, sans bloquer le depot.
- Document restreint: afficher restriction et masquer export direct.

### Criteres d'acceptation

- Le premier viewport montre le geste d'ajout ou la file de depot.
- Aucun chemin local absolu n'est visible.
- Le statut local prive est visible sans prendre toute la page.
- Un document peut devenir piece candidate ou preuve rattachee.
- Les etapes restent comprehensibles sans vocabulaire technique.

### Tests attendus

- Test routes `/depot` et route ajout document existante avec token.
- Test etat vide depot.
- Test ajout synthetique ou fixture document -> classification -> rattachement.
- Test absence de chemins Windows dans HTML rendu.
- Screenshots desktop/mobile.

---

## P2-10 - Finaliser AG, contentieux, passation comme surface dediee

### Objectif utilisateur

Un membre CS prepare une AG, suit les points contentieux factuels et transmet la
passation sans perdre les preuves ni diffuser trop largement.

### Image cible / capture live concernee

- Pas de Canva dedie. Deriver de la memoire de copropriete pour la passation et
  du registre pour les actions/preuves.
- Capture live: `docs/assets/ux-livraison-reelle-2026-05-21-8766/11_ag_contentieux.png`.
- Ecart visible: le contenu `AG, contentieux, passation` apparait sous la coque.
  Les cartes de travail sont partiellement visibles et coupees horizontalement.

### Structure visuelle attendue

- En-tete: `AG, contentieux, passation`, description courte, action primaire
  selon contexte.
- Rang resume: questions AG, pieces de convocation, dossiers contentieux,
  preuves ou restrictions.
- Trois colonnes ou panneaux:
  `Question AG`, `Piece de convocation`, `Dossier contentieux`.
- Chaque panneau explique pourquoi le sujet existe, quelle preuve est attendue,
  qui peut voir et quel est le prochain geste.
- Zone passation: pack derive, exclusions, restrictions, liens memoire.

### Composants

- `AGContentieuxHeader`.
- `AGPreparationSummaryCards`.
- `AGQuestionCard`.
- `ConvocationPieceCard`.
- `ContentieuxDossierCard`.
- `PassationPackPreview`.
- `RestrictionBadge`.
- `ProofRequirementList`.

### Donnees necessaires

- Questions AG: titre, raison, statut, responsable, lien resolution ou demande.
- Pieces de convocation: type, statut, date attendue, preuve ou document lie.
- Dossiers contentieux: nom, phase, derniere action, restriction, preuve.
- Passation: elements inclus, exclus, a biffer, destinataires autorises.
- Liens token-safe vers registre, memoire, pieces, demandes.

### Interactions

- Clic carte: ouvre detail avec preuve attendue et historique.
- `Cadrer une question AG`: cree brouillon ou action registre.
- `Verifier une piece de convocation`: ouvre piece manquante ou depot.
- `Restreindre un dossier`: ouvre decision de diffusion.
- `Preparer passation`: affiche apercu derive avant export.

### Etats vides

- Aucune question AG: afficher `Aucune question AG a cadrer`.
- Aucune piece de convocation: afficher `Aucune piece attendue connue` et
  proposer ajout manuel.
- Aucun contentieux: afficher `Aucun dossier contentieux ouvert`.
- Passation impossible: expliquer quelle preuve ou restriction manque.

### Criteres d'acceptation

- Le premier viewport montre l'en-tete et les trois panneaux de travail sans
  coupe horizontale.
- Les cartes ne sont pas seulement des compteurs: elles expliquent pourquoi et
  quoi faire.
- La passation est presentee comme export derive, pas source de verite.
- Chaque sujet sensible affiche restriction/diffusion avant export.

### Tests attendus

- Test route AG/contentieux avec token.
- Test clic sur chaque type de carte.
- Test preview passation avec restrictions.
- Screenshot desktop `1366x768` et mobile `390x844`.
- Test absence de scroll horizontal global.
