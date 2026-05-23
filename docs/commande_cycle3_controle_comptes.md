# Commande Cycle 3 - Controle des comptes guide

Date de reference: 2026-05-21.

Source visuelle: `docs/assets/etude-utilisateurs/controle-comptes-guide.png`.

Statut: commande dev prete pour Cycle 3, sous reserve de ne pas demarrer le
developpement avant arbitrage d'ownership front/back par l'integrateur-scribe.

## Intention utilisateur confirmee

Un membre de conseil syndical novice ouvre `/comptes` avant l'assemblee generale
pour comprendre les comptes sans etre comptable.

Il ne cherche pas a produire une comptabilite officielle. Il veut:

- voir les postes ou factures qui demandent attention;
- comprendre pourquoi un point est `OK`, `P2 a confirmer` ou `P1 a traiter`;
- transformer chaque anomalie en question claire au syndic;
- savoir quelle piece ou preuve manque;
- garder les points importants pour le rapport AG;
- eviter de diffuser des chemins prives, des bruts comptables ou des conclusions
  trop affirmatives.

La page ne doit donc pas etre une table d'audit comptable. Elle doit etre un
guide de controle CS: alerte -> explication -> preuve attendue -> question
syndic -> note AG.

## Enquete sur image

### Cadre mental novice

Questions a poser au membre CS novice:

- Quand vous lisez `Controle des comptes`, pensez-vous controler les charges,
  les factures, le budget, ou tout cela?
- Comprenez-vous que CoproScope propose des indices de controle, pas une
  validation comptable officielle?
- `P1 Prioritaire` et `P2 A confirmer` disent-ils quoi faire sans autre aide?
- Une anomalie doit-elle devenir une question syndic, une action CS, ou une
  reserve a noter pour l'AG?
- Quels mots vous rassurent: `preuve`, `justificatif`, `facture rapprochee`,
  `piece manquante`, `a confirmer`?

Attentes retenues:

- La page parle d'abord en actions humaines: `A traiter`, `A confirmer`,
  `Preuve rattachee`, `Piece a demander`.
- Les codes `P1` et `P2` ne portent jamais seuls la comprehension.
- Chaque point ouvert doit exposer une question syndic prete a relire/copier ou
  une preuve attendue.
- Les montants et rapprochements restent presentes comme hypotheses de controle,
  avec source et niveau de confiance.
- L'AG est une sortie de synthese, pas le seul usage de la page.

### Navigation laterale

Elements visibles:

- titre shell `Cockpit Conseil Syndical`;
- entrees principales `Tableau de bord`, `Documents`, `Comptes & budgets`,
  `Controle des comptes`, `AG`, `Demandes syndic`, `Incidents`;
- sous-navigation active sous `Controle des comptes`: `Vue d'ensemble`,
  `Depenses`, `Factures & pieces`, `Questions au syndic`, `Rapports`;
- bloc bas `Mode de partage - Prive (local)`.

Questions a poser:

- Comprenez-vous que `Controle des comptes` est une sous-partie de
  `Comptes & budgets`?
- Au clic sur `Vue d'ensemble`, attendez-vous revenir aux KPI et categories?
- Au clic sur `Depenses`, attendez-vous voir les postes de charges ou les lignes
  comptables detaillees?
- Au clic sur `Factures & pieces`, voulez-vous ouvrir les justificatifs ou voir
  les factures sans preuve?
- Au clic sur `Questions au syndic`, attendez-vous des brouillons de demandes ou
  un historique de demandes envoyees?
- Au clic sur `Rapports`, attendez-vous un rapport AG, un export interne CS, ou
  les deux?
- Le bloc `Prive (local)` vous rappelle-t-il que rien n'est envoye au syndic?

Attentes retenues:

- Tous les items de sous-navigation doivent ouvrir la meme route `/comptes` avec
  filtre, ancre ou onglet explicite.
- `Vue d'ensemble` affiche KPI + tableau categorie + inspecteur droit.
- `Depenses` filtre sur les postes/categories de charges.
- `Factures & pieces` ouvre la liste des pieces rattachees, manquantes ou
  candidates.
- `Questions au syndic` ouvre les brouillons et questions a relire, sans
  pretendre envoyer un mail.
- `Rapports` ouvre la vue `Rapport AG` et les exports prudents.
- Le mode local reste visible avant tout export ou copie.

### Haut de page

Elements visibles:

- titre `Controle des comptes`;
- selecteur d'exercice `Exercice 2024 (01/01/2024 - 31/12/2024)`;
- bouton `Exporter le rapport`;
- croix de fermeture dans le panneau droit.

Questions a poser:

- Le selecteur d'exercice doit-il changer seulement l'annee ou aussi la periode
  d'analyse?
- Au clic sur l'exercice, attendez-vous un menu avec plusieurs exercices,
  periodes partielles, ou rapports importes?
- `Exporter le rapport` exporte-t-il tout, seulement les filtres actifs, ou la
  version AG?
- Avant export, faut-il verifier les pieces sensibles et les notes internes?
- Que signifie la croix en haut a droite: fermer le detail, quitter la page, ou
  revenir au tableau?

Attentes retenues:

- L'exercice est un filtre global, persiste dans l'URL et garde le token local.
- Le libelle d'exercice affiche periode, date de derniere mise a jour et source
  si possible.
- `Exporter le rapport` ouvre d'abord une confirmation de perimetre:
  `Interne CS`, `Rapport AG`, `Questions syndic`, `Pieces a demander`.
- L'export est bloque ou averti si des notes internes, chemins prives ou pieces
  non diffusables sont inclus.
- La croix ferme seulement l'inspecteur droit sur desktop; sur mobile, elle
  revient a la liste.

### Cartes KPI

Cartes visibles:

- `Total depenses (charges)` avec valeur principale vide dans l'image et
  `Postes analyses 128`;
- `Factures rapprochees` avec `86%` et `110 / 128`;
- `P2 A confirmer` avec `18` et `14%`;
- `P1 Prioritaire` avec `6` et `5%`;
- `Pieces manquantes` avec `22` et `17%`.

Questions a poser carte par carte:

- `Total depenses (charges)`: voulez-vous voir un montant total, un nombre de
  postes, ou les deux? Une valeur vide est-elle inquietante?
- `Factures rapprochees`: comprenez-vous que `86%` signifie factures reliees a
  une ligne de depense ou preuve suffisante?
- `P2 A confirmer`: savez-vous que ce n'est pas une erreur certaine, mais une
  verification humaine?
- `P1 Prioritaire`: comprenez-vous que c'est a traiter avant AG ou avant
  validation CS?
- `Pieces manquantes`: attendez-vous voir les pieces a demander ou les factures
  concernees?
- Au clic sur une carte, attendez-vous filtrer le tableau, ouvrir les questions,
  ou afficher une liste dediee?

Attentes retenues:

- Les KPI sont cliquables et filtrent la page en conservant l'inspecteur.
- Une valeur manquante est remplacee par `Montant non charge` ou `A calculer`,
  jamais par un tiret muet.
- `Factures rapprochees` affiche ratio, numerateur, denominateur et aide courte.
- `P2` se lit `A confirmer avec le syndic ou une piece`.
- `P1` se lit `A traiter avant AG`.
- `Pieces manquantes` ouvre la liste des justificatifs attendus et propose une
  question syndic.
- Chaque carte a un `href` local token-safe ou un bouton filtre accessible.

### Bloc `Depenses par categorie`

Elements visibles:

- titre `Depenses par categorie`;
- filtre `Toutes categories`;
- filtre `Statut : Tous`;
- filtre `Fournisseur : Tous`;
- interrupteur `Afficher les lignes soldees`;
- tableau avec colonnes `Categorie`, `Montant charges`, `Factures
  rapprochees`, `Ecart`, `Statut`, `Alertes`;
- pagination `Afficher 1 a 7 sur 7 categories`, fleches precedent/suivant,
  page `1`;
- legende basse `OK`, `P2 A confirmer`, `P1 Prioritaire`, `Pieces manquantes`.

Questions a poser:

- `Depenses par categorie` vous fait-il chercher les familles comptables
  classiques: entretien, energie, assurances, taxes, honoraires?
- Le filtre `Toutes categories` doit-il proposer seulement les categories
  visibles ou aussi les sous-categories comptables?
- Le filtre `Statut : Tous` doit-il inclure `OK`, `P2`, `P1`, `Pieces
  manquantes`, `Hors exercice`, `A verifier`?
- Le filtre `Fournisseur : Tous` doit-il filtrer les categories qui contiennent
  au moins une facture de ce fournisseur?
- L'interrupteur `Afficher les lignes soldees` veut-il dire afficher les lignes
  deja OK, les postes sans alerte, ou les comptes a zero?
- Au clic sur une ligne, attendez-vous ouvrir le detail categorie a droite?
- Le chevron de fin de ligne ouvre-t-il le meme detail ou une page complete?
- La pagination est-elle utile si seulement 7 categories existent?
- La legende explique-t-elle suffisamment les couleurs et les pastilles?

Attentes retenues:

- Les filtres modifient tableau, KPI, questions et rapport AG en meme temps.
- `Afficher les lignes soldees` doit etre renomme ou aide:
  `Afficher aussi les categories sans alerte`.
- Les categories OK peuvent rester visibles mais moins dominantes.
- Le clic ligne et le chevron selectionnent la categorie dans l'inspecteur droit.
- La pagination reste stable mais ne masque pas des alertes P1 hors page sans
  signal.
- La legende associe couleur + texte + consequence, jamais couleur seule.

### Lignes de categories

Lignes visibles:

- `Entretien & maintenance`: rapprochement `92%`, statut `P2 A confirmer`,
  `4` alertes;
- `Energie & fluides`: rapprochement `78%`, statut `P1 Prioritaire`, `3`
  alertes;
- `Prestations de service`: rapprochement `88%`, statut `P2 A confirmer`, `5`
  alertes;
- `Assurances`: rapprochement `100%`, statut `OK`, `0` alerte;
- `Taxes & impots`: rapprochement `95%`, statut `OK`, `1` alerte;
- `Honoraires & honoraires tiers`: rapprochement `70%`, statut
  `P1 Prioritaire`, `2` alertes;
- `Autres charges`: rapprochement `60%`, statut `P1 Prioritaire`, `2` alertes.

Questions a poser ligne par ligne:

- Entretien: avec `92%` et `P2`, comprenez-vous qu'il reste des justificatifs ou
  confirmations malgre un bon taux?
- Energie: avec `78%` et `P1`, voulez-vous voir les factures non rapprochees en
  premier?
- Prestations: `5` alertes en P2 vous parait-il moins urgent que `3` alertes en
  P1?
- Assurances: `OK 100%` suffit-il ou faut-il montrer la preuve rattachee?
- Taxes: `OK` avec `1` alerte est-il contradictoire? L'alerte est-elle mineure?
- Honoraires: faut-il distinguer syndic, avocat, expert, comptable?
- Autres charges: une categorie fourre-tout doit-elle etre decomposee avant AG?

Attentes retenues:

- La priorite depend de la nature du controle, pas seulement du nombre
  d'alertes.
- Une ligne `OK` avec alerte doit expliquer si l'alerte est informative,
  deja justifiee ou non bloquante.
- Les categories P1 affichent une prochaine action courte dans le detail:
  `Demander la piece`, `Verifier la ligne`, `Confirmer l'imputation`.
- Chaque ligne expose un chemin vers les pieces et questions associees.
- Les categories trop larges doivent proposer `Voir les sous-categories`.

### Panneau detail droit - en-tete

Elements visibles:

- titre `Entretien & maintenance`;
- badge `P2 A confirmer`;
- compteur `4 alertes`;
- onglets `Detail`, `Pieces`, `Questions au syndic`.

Questions a poser:

- Le titre vous dit-il clairement quel poste de charges est selectionne?
- Le badge `P2 A confirmer` suffit-il avec `4 alertes`, ou faut-il une phrase
  `A confirmer avant AG`?
- Voulez-vous savoir si cette categorie sera incluse dans le rapport AG?
- Les onglets vous font-ils comprendre la progression:
  comprendre -> ouvrir les pieces -> poser les questions?
- Les compteurs doivent-ils apparaitre sur chaque onglet?

Attentes retenues:

- L'en-tete affiche categorie, statut humain, nombre d'alertes, prochaine action
  et inclusion AG.
- Les onglets gardent la meme categorie selectionnee.
- Les onglets ont des compteurs: `Detail`, `Pieces (25)`,
  `Questions au syndic (3)`.
- Le statut est accompagne d'une micro-explication:
  `Rapprochement presque complet, pieces ou confirmations encore attendues`.

### Onglet `Detail`

Elements visibles:

- lignes `Montant charges`, `Factures rapprochees 92% (23 / 25)`,
  `Ecart constate`, `Derniere facture`;
- carte `Alertes`;
- carte `Questions au syndic (3)`;
- carte `Rapport AG`.

Questions a poser:

- Un tiret pour `Montant charges`, `Ecart constate` et `Derniere facture`
  signifie-t-il absence de donnee, non calcule, ou sans ecart?
- `Factures rapprochees 92% (23 / 25)` vous suffit-il pour comprendre le reste a
  verifier?
- Voulez-vous voir les 2 factures non rapprochees directement ici?
- `Ecart constate` doit-il afficher montant, pourcentage, sens de l'ecart, et
  source?
- `Derniere facture` sert-elle a detecter une periodicite manquante?

Attentes retenues:

- Aucun tiret muet: remplacer par `Non charge`, `Aucun ecart detecte`,
  `Date non lue`, ou `Non applicable`.
- Le detail doit afficher les chiffres qui aident l'action: total charges,
  nombre de factures, rapprochees, non rapprochees, pieces manquantes, ecart.
- Les valeurs importantes ont un lien vers les factures ou lignes source.
- La categorie selectionnee doit avoir une phrase novice:
  `Ce poste est presque complet, mais 2 factures et 3 confirmations restent a
  demander.`

### Carte `Alertes`

Elements visibles:

- `2 factures sans bon de commande` avec pastille `2`;
- `1 facture sans piece jointe` avec pastille `1`;
- `1 ecart de periodicite` avec pastille `1`.

Questions a poser:

- Comprenez-vous la difference entre bon de commande manquant, piece jointe
  manquante et periodicite?
- Au clic sur une alerte, voulez-vous voir les factures concernees ou la question
  syndic correspondante?
- La pastille orange indique-t-elle nombre de factures, gravite ou priorite?
- Une alerte peut-elle etre incluse dans le rapport AG sans question syndic?

Attentes retenues:

- Chaque alerte est cliquable et ouvre les pieces concernees.
- Chaque alerte expose: cause, niveau, preuve attendue, question proposee,
  statut de traitement.
- La pastille indique le nombre d'elements touches; la gravite reste lisible par
  texte.
- Une alerte P1 doit toujours avoir une suite: question syndic, piece a demander
  ou note AG.

### Carte `Questions au syndic`

Elements visibles:

- `Merci de nous transmettre les bons de commande manquants.`
- `Merci de nous fournir les justificatifs manquants pour la facture du 12/03.`
- `Pouvez-vous confirmer le detail des prestations facturees ?`
- bouton `Voir toutes les questions`.

Questions a poser:

- Ces phrases sont-elles assez precises pour etre envoyees au syndic?
- Faut-il citer la facture, le fournisseur, le montant, la periode et la piece
  attendue?
- Au clic sur une question, attendez-vous l'editer, la copier, ou la rattacher a
  une demande syndic?
- `Voir toutes les questions` ouvre-t-il l'onglet, une page, ou un tiroir?
- Une question doit-elle garder son statut: brouillon, copiee, envoyee hors
  CoproScope, reponse recue, a verifier?

Attentes retenues:

- Les questions visibles en carte sont des resumes; la version complete est
  accessible et copiable.
- La question complete cite le contexte minimal: categorie, fournisseur, facture,
  montant si connu, piece ou justification attendue, date limite si utile.
- `Voir toutes les questions` ouvre l'onglet `Questions au syndic` filtre sur la
  categorie.
- Le produit ne pretend pas envoyer l'email. Il prepare, copie et trace.

### Carte `Rapport AG`

Elements visibles:

- texte `Inclure cette categorie dans le rapport`;
- interrupteur actif;
- bouton `Ajouter une note`.

Questions a poser:

- Souhaitez-vous inclure seulement les categories P1/P2 ou aussi les OK
  importants?
- Que doit contenir la note: reserve CS, question non repondue, explication pour
  l'AG, decision demandee?
- L'interrupteur doit-il inclure toute la categorie ou seulement les alertes
  ouvertes?
- Au clic sur `Ajouter une note`, faut-il proposer un modele de phrase?
- La note AG est-elle interne CS ou diffusable aux coproprietaires?

Attentes retenues:

- L'interrupteur indique clairement le perimetre:
  `Inclure les points ouverts de cette categorie dans le rapport AG`.
- `Ajouter une note` ouvre un champ avec aide:
  `Note prudente, sans accusation, reliee aux preuves disponibles`.
- Chaque note porte un niveau de diffusion: interne CS, AG diffusable,
  a relire, bloque.
- Le rapport AG ne copie pas automatiquement les chemins ou commentaires
  internes.

### Onglet `Pieces`

Vue manquante a formaliser a partir de l'image.

Questions a poser:

- Voulez-vous voir toutes les pieces de la categorie ou seulement celles avec
  alerte?
- Une ligne piece doit-elle afficher fournisseur, facture, date, montant,
  statut de rapprochement et preuve attendue?
- Comment distinguer `piece presente`, `piece manquante`, `preuve candidate`,
  `preuve validee`?
- Au clic sur une piece, attendez-vous ouvrir le document, la fiche facture, ou
  le detail de rapprochement?
- Que doit faire une action `Demander cette piece au syndic`?

Attentes retenues:

- L'onglet `Pieces` liste les factures, justificatifs, bons de commande, lignes
  d'etat des depenses et documents rattaches.
- Chaque piece affiche son role: facture, bon de commande, contrat, devis,
  ligne comptable, preuve candidate, preuve OK.
- Une piece presente ne vaut pas preuve validee tant que son lien avec l'alerte
  n'est pas explicite.
- Les actions minimum sont: ouvrir, voir la fiche document, rattacher comme
  preuve, demander la piece, ajouter au rapport AG.
- Les chemins prives ne sont jamais visibles; utiliser des labels et `doc_id`.

### Onglet `Questions au syndic`

Vue manquante a formaliser a partir de l'image.

Questions a poser:

- Les questions doivent-elles etre groupees par alerte, fournisseur, facture ou
  priorite?
- Voulez-vous modifier le texte avant copie?
- Faut-il une case `inclure dans le prochain mail au syndic`?
- Comment indiquer qu'une question a deja ete posee hors CoproScope?
- Une reponse du syndic doit-elle pouvoir etre rattachee comme preuve?

Attentes retenues:

- L'onglet affiche les questions avec statut et version copiable.
- Chaque question expose l'alerte source, la preuve attendue et la consequence
  si la reponse manque avant AG.
- L'utilisateur peut: editer le brouillon, copier le texte, marquer comme
  envoyee hors CoproScope, rattacher une reponse, convertir en action dans
  `/actions` ou demande dans `/demandes`.
- Une question repondue reste `a verifier` tant qu'une preuve ou note n'est pas
  rattachee.

### Vue detail categorie comptable

Vue manquante obligatoire.

Route cible possible: `/comptes?categorie=<id>&tab=detail` ou
`/comptes/categories/<id>` selon arbitrage dev.

Contenu obligatoire:

- categorie selectionnee, exercice, statut, prochaine action;
- resume novice: ce qui est conforme, ce qui reste a confirmer, ce qui bloque;
- total charges et source, si disponible;
- factures rapprochees, non rapprochees, pieces manquantes;
- ecarts constates avec methode de calcul;
- sous-categories ou comptes si la categorie est trop large;
- alertes detaillees avec preuve attendue;
- pieces liees et factures concernees;
- questions syndic proposees;
- inclusion rapport AG et notes;
- historique court des confirmations humaines.

Critere: une personne non-comptable doit pouvoir expliquer en reunion CS:
`Ce poste est vert/orange/rouge pour telle raison, il manque telle preuve, et la
question syndic est celle-ci.`

### Vue question syndic

Vue manquante obligatoire.

Route cible possible: `/comptes/questions/<id>`, tiroir lateral, ou
`/comptes?tab=questions&question=<id>`.

Contenu obligatoire:

- question prete a relire/copier;
- categorie, alerte, fournisseur, facture, montant, periode;
- preuve ou reponse attendue;
- phrase de contexte neutre et non accusatoire;
- piece(s) concernees;
- statut: brouillon, copiee, envoyee hors CoproScope, reponse recue,
  reponse a verifier, cloturee;
- action `Copier la question`;
- action `Marquer envoyee hors CoproScope`;
- action `Rattacher une reponse`;
- action `Ajouter au rapport AG`;
- historique des changements de statut.

No-go:

- afficher `Envoyee` sans confirmation humaine du canal;
- produire une accusation ou conclusion juridique;
- inclure un chemin local, un brut sensible ou une note interne dans le texte
  copiable.

### Vue rapport AG

Vue manquante obligatoire.

Route cible possible: `/comptes/rapport-ag` ou `/comptes?tab=rapport-ag`.

Contenu obligatoire:

- synthese des comptes a porter en AG;
- categories incluses, exclues et motif;
- P1 a traiter avant AG;
- P2 a confirmer et questions en attente;
- OK avec preuves utiles a citer;
- pieces manquantes;
- questions syndic encore ouvertes;
- notes CS et niveau de diffusion;
- apercu du rapport exportable;
- avertissements de diffusion et blocages;
- date d'exercice et date de generation.

Critere: le rapport AG doit aider a parler clairement aux coproprietaires sans
transformer un indice local en accusation ni exposer les donnees internes.

## Structure visuelle attendue pour `/comptes`

La route `/comptes` doit reprendre la densite et la hierarchie de l'image:

- shell `cs-*` avec sidebar sombre fixe, zone de travail claire, inspecteur droit
  optionnel;
- header page avec titre `Controle des comptes`, exercice, export;
- rang de KPI cliquables;
- bloc central `Depenses par categorie` avec filtres et table de categories;
- inspecteur droit ouvert par defaut sur la categorie selectionnee;
- onglets d'inspecteur: `Detail`, `Pieces`, `Questions au syndic`;
- carte `Rapport AG` visible dans l'inspecteur;
- legende de statuts en bas du tableau;
- sur mobile: les KPI restent en haut, le tableau devient liste de categories,
  l'inspecteur devient une page/tiroir, et la croix revient a la liste.

Hierarchie d'usage:

1. voir combien de points sont OK/P2/P1/manquants;
2. filtrer ou selectionner une categorie;
3. comprendre les alertes;
4. ouvrir les pieces concernees;
5. preparer les questions syndic;
6. inclure les points utiles dans le rapport AG.

## Composants

Composants front attendus:

- `cs-shell`, `cs-sidebar`, `cs-nav-group`, `cs-nav-subitem`;
- `cs-page-header`, `cs-exercise-select`, `cs-export-button`;
- `cs-kpi-row`, `cs-kpi-card`;
- `cs-accounting-layout`, `cs-category-table`, `cs-category-row`;
- `cs-filter-bar`, `cs-filter-select`, `cs-switch`;
- `cs-progress-meter`, `cs-status-badge`, `cs-alert-count`;
- `cs-detail-drawer`, `cs-detail-header`;
- `cs-tabs`, `cs-tab`, `cs-tab-panel`;
- `cs-detail-metrics`, `cs-alert-card`, `cs-alert-row`;
- `cs-piece-list`, `cs-piece-row`, `cs-proof-state`;
- `cs-question-list`, `cs-question-card`, `cs-copy-question`;
- `cs-ag-report-card`, `cs-ag-report-preview`, `cs-note-editor`;
- `cs-empty-state`, `cs-safe-export-notice`, `cs-pagination`;
- `cs-local-sharing-badge`.

Regles UI:

- Les cartes gardent un rayon sobre, 8px maximum sauf convention existante.
- Les icones aident mais ne remplacent pas les libelles d'action.
- Aucun compteur non cliquable.
- Aucun statut porte par la couleur seule.
- Les libelles de boutons nomment leur consequence:
  `Exporter le rapport`, `Voir les pieces`, `Copier la question`,
  `Rattacher une reponse`, `Ajouter une note AG`.
- Les codes `P1` et `P2` sont toujours accompagnes de texte humain.
- Pas de promesse d'envoi email automatique.
- Pas de tableau brut en premier niveau si une lecture guidee est possible.

## Contrat donnees `model.ux.comptes`

Le dev back/viewmodel doit stabiliser `model.ux.comptes` tout en conservant les
cles existantes necessaires aux routes et tests en cours (`model.accounting`,
`model.accounting.guide`, `model.accounting.before_ag`,
`model.accounting.syndic_questions`).

Structure cible:

```text
model.ux.comptes = {
  context,
  summary,
  facets,
  filters,
  categories,
  selected,
  questions_syndic,
  ag_report,
  tabs,
  empty_states,
  export,
}
```

### `context`

Champs attendus:

- `coffre_label`;
- `sharing_mode_label`: exemple `Prive local`;
- `sharing_mode_detail`: aucune synchronisation externe lancee;
- `role_label`: exemple `Conseil syndical`;
- `exercise_label`: exemple `Exercice 2024`;
- `period_label`: exemple `01/01/2024 - 31/12/2024`;
- `year`;
- `source_label`: exemple `Sorties ComptaScope`;
- `last_updated_label`;
- `token_query` ou equivalent token-safe deja utilise par le shell.

### `summary`

Champs attendus:

- `total_charges_amount`;
- `total_charges_label`;
- `analyzed_posts_count`;
- `invoice_total_count`;
- `invoice_matched_count`;
- `invoice_matched_ratio`;
- `invoice_matched_label`;
- `p1_count`;
- `p1_ratio_label`;
- `p2_count`;
- `p2_ratio_label`;
- `missing_pieces_count`;
- `missing_pieces_ratio_label`;
- `questions_count`;
- `ag_included_count`;
- `export_blockers_count`;
- `last_control_label`.

Chaque compteur expose:

- `href`;
- `filter_key`;
- `help_label`;
- `status_tone`.

### `facets` et `filters`

Facettes minimum:

- `exercise`;
- `category`;
- `status`;
- `supplier`;
- `proof_state`;
- `piece_state`;
- `alert_type`;
- `ag_inclusion`;
- `match_state`.

Filtre actif:

- `selected_exercise`;
- `selected_category`;
- `selected_status`;
- `selected_supplier`;
- `selected_proof_state`;
- `selected_piece_state`;
- `selected_alert_type`;
- `show_solded_lines`;
- `query`;
- `selected_category_id`;
- `selected_tab`.

### `categories`

Chaque categorie:

- `category_id`;
- `label`;
- `icon`;
- `account_family_label`;
- `amount_charges`;
- `amount_charges_label`;
- `amount_state`: loaded, missing, not_applicable;
- `invoice_count`;
- `matched_invoice_count`;
- `matched_ratio`;
- `matched_ratio_label`;
- `unmatched_invoice_count`;
- `missing_pieces_count`;
- `ecart_amount`;
- `ecart_label`;
- `ecart_state`: none, detected, unknown, not_applicable;
- `last_invoice_label`;
- `last_invoice_href`;
- `status`: ok, p2, p1, missing, unknown;
- `status_label`;
- `status_detail`;
- `status_tone`;
- `alert_count`;
- `p1_count`;
- `p2_count`;
- `ok_count`;
- `question_count`;
- `ag_included`;
- `next_action_label`;
- `href`;
- `is_selected`.

### `selected`

`selected` est l'objet complet correspondant a `selected_category_id`.
S'il n'y a aucune selection, prendre la premiere categorie non OK, puis la
premiere categorie disponible. S'il n'y a aucune categorie, fournir un objet vide
exploitable par les etats vides.

Champs attendus:

- tous les champs de `categories`;
- `novice_summary`;
- `controls_summary`;
- `alerts`;
- `pieces`;
- `questions`;
- `ag_section`;
- `history`;
- `subcategories`;
- `source_rows`;
- `diffusion`;
- `memory_note`.

### Alertes

Chaque alerte:

- `alert_id`;
- `category_id`;
- `priority`: P1, P2, OK, info;
- `priority_label`;
- `tone`;
- `type`: missing_order, missing_attachment, period_gap, non_match,
  ambiguous_match, amount_gap, supplier_gap, unknown;
- `label`;
- `count`;
- `explanation`;
- `affected_piece_ids`;
- `affected_invoice_refs`;
- `expected_proof`;
- `suggested_question_id`;
- `next_action_label`;
- `status`: open, question_ready, waiting_syndic, answered_to_check, closed;
- `href`.

### Pieces

Chaque piece:

- `piece_id`;
- `doc_id`;
- `category_id`;
- `label`;
- `type_label`: facture, bon de commande, contrat, devis, ligne depense,
  justificatif, reponse syndic, autre;
- `supplier_label`;
- `invoice_ref`;
- `invoice_date_label`;
- `amount_label`;
- `period_label`;
- `match_status`;
- `match_status_label`;
- `proof_state`: missing, candidate, verified, rejected, not_needed;
- `proof_state_label`;
- `role_label`;
- `related_alert_ids`;
- `question_ids`;
- `diffusion_label`;
- `restriction_reason`;
- `href`;
- `actions`: ouvrir, fiche document, rattacher comme preuve, demander au syndic,
  ajouter au rapport AG.

### Questions syndic

Chaque question:

- `question_id`;
- `category_id`;
- `alert_ids`;
- `piece_ids`;
- `priority`;
- `priority_label`;
- `status`: draft, copied, sent_outside, answered_to_check, closed;
- `status_label`;
- `subject`;
- `short_label`;
- `question_text`;
- `copy_text`;
- `context_label`;
- `expected_answer`;
- `expected_proof`;
- `recipient_label`;
- `channel_label`;
- `last_sent_label`;
- `answer_summary`;
- `related_request_id`;
- `include_in_ag_report`;
- `diffusion_label`;
- `href`;

### Rapport AG

`ag_report`:

- `title`;
- `scope_label`;
- `generated_on_label`;
- `included_categories`;
- `excluded_categories`;
- `p1_points`;
- `p2_points`;
- `ok_with_proof_points`;
- `missing_pieces`;
- `open_questions`;
- `notes`;
- `preview_markdown`;
- `diffusion_status`: ok, warning, blocked;
- `diffusion_label`;
- `blocked_by`;
- `export_href`;
- `edit_href`.

Chaque note AG:

- `note_id`;
- `category_id`;
- `author_label`;
- `created_on_label`;
- `text`;
- `diffusion_level`: internal_cs, ag_public, to_review, blocked;
- `related_alert_ids`;
- `related_question_ids`;
- `href`.

### Historique

Chaque evenement:

- `event_id`;
- `occurred_on`;
- `type`: control_loaded, category_selected, question_created,
  question_copied, sent_outside_confirmed, answer_linked, proof_linked,
  status_changed, ag_note_added, export_created;
- `type_label`;
- `actor_label`;
- `summary`;
- `category_id`;
- `piece_ids`;
- `question_ids`;
- `is_evidence`;
- `memory_note`.

### Diffusion

`diffusion`:

- `status`: local_only, cs_only, ag_ok, after_review, blocked;
- `label`;
- `reason`;
- `allowed_audience`;
- `blocked_by`;

## Interactions attendues

- Exercice: change l'exercice, recharge les KPI et conserve les filtres
  compatibles.
- KPI: filtre la page et met a jour tableau + inspecteur + rapport.
- Filtres: modifient la liste de categories, les compteurs et l'URL.
- `Afficher les lignes soldees`: affiche ou masque les categories sans alerte
  ouverte.
- Selection categorie: met a jour l'inspecteur avec `selected_category_id` dans
  l'URL.
- Onglet inspecteur: conserve la categorie et utilise `tab=detail`, `tab=pieces`
  ou `tab=questions`.
- Alerte: ouvre les pieces concernees ou la question associee.
- Piece: ouvre la fiche document ou le detail de rapprochement sans exposer de
  chemin prive.
- Question: permet edition, copie, confirmation d'envoi hors CoproScope,
  rattachement de reponse, conversion en demande/action si la route existe.
- `Voir toutes les questions`: bascule vers l'onglet questions filtre sur la
  categorie ou vers `/comptes?tab=questions`.
- `Inclure dans le rapport AG`: ajoute seulement les points ouverts ou notes
  explicitement selectionnes.
- `Ajouter une note`: cree une note avec niveau de diffusion obligatoire.
- `Exporter le rapport`: demande le perimetre, signale les blocages, puis exporte
  une version derivee.
- Fermer le panneau: masque l'inspecteur sur desktop; revient a la liste sur
  mobile.

## Etats vides

Tous les etats vides doivent expliquer le probleme et proposer une suite.

- Aucune sortie comptes: `Aucun controle comptes charge. Generer ou importer les
  sorties ComptaScope pour cet exercice.`
- Aucun exercice: `Aucun exercice comptable disponible. Selectionner ou importer
  un exercice.`
- Aucune categorie: `Aucune categorie de charges exploitable pour cet exercice.`
- Aucun resultat filtre: `Aucune categorie ne correspond a ces filtres. Retirer
  un filtre ou afficher toutes les categories.`
- Aucun montant: `Montant non charge pour ce poste. Le controle reste possible a
  partir des factures et pieces.`
- Aucune alerte: `Aucune alerte ouverte pour cette categorie. Verifier les
  preuves OK avant de l'indiquer en AG.`
- Aucune piece: `Aucune piece rattachee a cette categorie. Importer une facture,
  une ligne de depense ou demander le justificatif au syndic.`
- Aucune question: `Aucune question preparee. Creer une question depuis une
  alerte ou une piece manquante.`
- Aucune note AG: `Aucune note AG pour cette categorie. Ajouter une note si ce
  point doit etre explique aux coproprietaires.`
- Rapport AG vide: `Aucun point inclus dans le rapport AG. Inclure une categorie
  ou une question ouverte.`
- Export bloque: `Export non prepare car au moins un element demande une revue
  de diffusion.`

## Criteres d'acceptation

- `/comptes` ressemble a la source visuelle par structure: sidebar, header,
  cartes KPI, filtres, tableau de categories, inspecteur droit, onglets, rapport
  AG.
- Un membre CS novice comprend la difference entre `OK`, `P2 a confirmer` et
  `P1 a traiter`.
- Les codes `P1` et `P2` ne sont jamais affiches seuls.
- Chaque P1 expose une action ou question syndic et une preuve attendue.
- Chaque P2 expose ce qui doit etre confirme et pourquoi ce n'est pas une erreur
  definitive.
- Chaque OK cite une preuve locale ou explique pourquoi aucune question n'est
  necessaire.
- Les pieces manquantes ouvrent une liste et une question syndic possible.
- Les alertes sont cliquables et reliees aux pieces, questions et notes AG.
- Le detail categorie donne assez de contexte pour expliquer le poste sans etre
  comptable.
- La vue question syndic produit un texte copiable, prudent et sans promesse
  d'envoi automatique.
- La vue rapport AG inclut seulement les points selectionnes et signale les
  restrictions de diffusion.
- Tous les compteurs, cartes KPI, badges d'alerte et boutons critiques ont un
  lien ou une action utile.
- Les liens conservent le token local quand la route est protegee.
- Aucun chemin prive, `raw`, `restricted`, `logs`, `file://` ou chemin absolu
  utilisateur n'apparait dans l'UI ou les exports.
- Les etats vides guident vers une action concrete.
- La page reste utilisable au clavier: focus visible, onglets accessibles,
  boutons nommes, table avec caption ou liste equivalente.
- La page reste lisible sur mobile: pas de chevauchement, inspecteur transforme
  en vue detail.

## Tests attendus

Tests front/route:

- route `/comptes` retourne 200 avec token;
- route protegee retourne 403 sans token si un token est configure;
- presence du shell, du titre `Controle des comptes`, du selecteur d'exercice et
  du bouton `Exporter le rapport`;
- presence des KPI `Factures rapprochees`, `P2 a confirmer`, `P1 a traiter`,
  `Pieces manquantes`;
- presence du bloc `Depenses par categorie`, des filtres categorie/statut/
  fournisseur et du controle d'affichage des categories sans alerte;
- presence de l'inspecteur droit avec titre categorie, statut, onglets `Detail`,
  `Pieces`, `Questions au syndic`;
- presence de la carte `Rapport AG`;
- chaque KPI et compteur critique contient un `href` local ou une action
  accessible;
- aucun lien interne ne perd le token quand le token est present;
- les boutons principaux portent des libelles consequences.

Tests viewmodel:

- `model.ux.comptes.summary` contient compteurs, ratios, labels humains et hrefs
  attendus;
- `model.ux.comptes.categories` expose categories, statuts, ratios, alertes et
  prochaine action;
- `model.ux.comptes.selected` est stable avec ou sans `selected_category_id`;
- une instance vide produit des etats vides exploitables;
- P1, P2, OK et pieces manquantes sont distingues sans s'ecraser;
- chaque P1 a au moins une question syndic ou une action explicite;
- chaque P2 expose une confirmation attendue;
- chaque OK cite une preuve ou une raison de non-question;
- pieces et preuves ne sont pas confondues;
- questions syndic ont statut brouillon/copie/envoye hors CoproScope/reponse a
  verifier;
- rapport AG expose categories incluses, notes, blocages et export;
- les champs publics masquent chemins prives et dossiers sensibles.

Tests UX/langage/securite:

- absence de jargon primaire non traduit (`vault`, `hash`, `ACL`, `RBAC`,
  `P1/P2` seuls, `NON_RAPPROCHE` seul);
- `Mode prive local` ou equivalent visible;
- aucune promesse d'envoi email automatique;
- export bloque ou averti si diffusion incertaine;
- comparaison visuelle par blocs avec
  `docs/assets/etude-utilisateurs/controle-comptes-guide.png`;
- scenario novice: ouvrir `/comptes`, filtrer sur `P1`, selectionner une
  categorie, comprendre l'alerte, ouvrir les pieces, copier une question syndic,
  inclure une note dans le rapport AG;
- scenario OK: selectionner une categorie OK, identifier la preuve rattachee et
  comprendre pourquoi aucune question n'est necessaire;
- scenario vide: supprimer ou masquer les sorties comptes et verifier que la page
  propose de generer/importer les sorties ComptaScope.

Commande indicative depuis `server/` une fois le dev livre:

```powershell
.\.venv\Scripts\python.exe -m unittest tests.test_ui_comptes_guide -v
.\.venv\Scripts\python.exe -m unittest tests.test_ui_novice_language_static -v
```

Des tests dedies Cycle 3 devront etre ajoutes ou completes par les devs selon
leur ownership exact; ce document ne modifie ni templates ni tests.

## Commande dev prete

Developper Cycle 3 `/comptes` comme controle comptes guide a partir de la source
visuelle `controle-comptes-guide.png`.

Priorite de livraison:

1. Stabiliser `model.ux.comptes` avec `context`, `summary`, `facets`,
   `filters`, `categories`, `selected`, `questions_syndic`, `ag_report`,
   `empty_states`, `export`.
2. Refaire la structure front `/comptes`: KPI, filtres, tableau categories,
   inspecteur droit, onglets, carte rapport AG.
3. Implementer les vues manquantes: detail categorie comptable, question syndic,
   rapport AG.
4. Verrouiller tests route, DOM, viewmodel, langage novice, token, anti-fuite et
   scenario novice.

Definition de fini:

- une anomalie comptable ne reste plus une ligne technique;
- elle devient une explication lisible;
- l'explication dit quelle preuve manque ou existe;
- la question syndic est preparable, copiable et tracable;
- le rapport AG reprend les points utiles sans exposer les donnees internes ni
  pretendre remplacer la comptabilite officielle.
