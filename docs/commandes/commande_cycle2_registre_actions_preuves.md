# Commande Cycle 2 - Registre decisions, actions, preuves

Date de reference: 2026-05-21.

Source visuelle: `docs/assets/etude-utilisateurs/registre-decisions-actions-preuves.png`.

Statut: commande dev prete pour Cycle 2, sous reserve de ne pas demarrer le
developpement avant arbitrage d'ownership front/back par l'integrateur-scribe.

## Intention utilisateur confirmee

Un membre de conseil syndical novice ouvre `/actions` pour transformer une
resolution d'assemblee generale en suivi concret:

- quelle decision a ete votee;
- quelle action est attendue;
- qui s'en occupe;
- avant quand;
- quelle preuve manque ou existe;
- quelle relance syndic est a faire;
- ce qui doit rester dans la memoire de copropriete.

La page ne doit pas etre un simple tableau. Elle doit etre un registre de
travail: decision -> action -> preuve -> relance -> historique.

## Enquete sur image

### Haut de page

Questions a poser au membre CS novice:

- Quand vous lisez `Registre des decisions`, que pensez-vous pouvoir suivre ici?
- Le sous-titre `Tracez, suivez et prouvez l'execution des resolutions
  d'Assemblee Generale` est-il comprehensible sans connaitre CoproScope?
- La recherche `Rechercher (decisions, actions, preuves...)` sert-elle a trouver
  une resolution, une piece, une relance, ou tout cela?
- Au clic sur `Exporter le registre`, attendez-vous un fichier complet, un
  extrait filtre, ou une version diffusable?
- Au clic sur `Nouvelle action`, attendez-vous a creer une action libre, une
  action rattachee a une resolution, ou une relance?
- Que doit faire l'icone d'aide?
- Que doit ouvrir la cloche de notification?

Attentes retenues:

- La recherche porte sur decisions, actions, preuves et pieces liees.
- `Exporter le registre` doit annoncer son perimetre et sa prudence de diffusion
  avant telechargement si des pieces sensibles existent.
- `Nouvelle action` doit proposer en premier `Rattacher a une decision AG`, puis
  `Action libre du conseil syndical`.
- L'aide explique les mots `preuve`, `piece liee`, `relance`, `historique`.
- La notification liste les actions en retard et relances sans reponse.

### Navigation laterale

Questions a poser:

- Les compteurs `A traiter`, `Pieces manquantes`, `Demandes syndic` vous disent
  quoi faire ou seulement combien il y a d'elements?
- Au clic sur `A traiter`, attendez-vous rester dans `/actions` avec un filtre?
- Au clic sur `Pieces manquantes`, attendez-vous voir les pieces attendues ou les
  documents deja presents?
- Au clic sur `Demandes syndic`, attendez-vous une liste de relances envoyees,
  a envoyer, ou les deux?
- Le bloc `Mode de partage - Prive (local)` vous rassure-t-il avant export?

Attentes retenues:

- Tous les compteurs de navigation doivent etre cliquables.
- Les compteurs ouvrent une vue filtree avec un titre explicite.
- `Mode de partage - Prive (local)` reste visible: la page ne publie rien et ne
  lance aucune synchronisation externe.

### Colonne gauche - Toutes les AG

Questions a poser:

- Comprenez-vous que la colonne de gauche est une liste de resolutions classees
  par AG?
- Au clic sur `Filtrer`, quels filtres attendez-vous: AG, statut, retard,
  responsable, preuve manquante?
- Que signifie une resolution `Terminee`, `Action en cours`, `En retard`?
- Au clic sur la fleche d'une resolution, attendez-vous ouvrir le detail a
  droite ou changer de page?
- `Voir toutes les resolutions` doit-il deplier toute la liste ou ouvrir une
  page/table dediee?

Attentes retenues:

- La colonne gauche est le sommaire permanent des decisions.
- Le clic sur une resolution selectionne la fiche detaillee dans la zone droite.
- Les statuts sont en langage naturel; les codes techniques restent masques ou
  replies.
- Les filtres minimum sont: AG, statut, responsable, preuve manquante, retard,
  priorite.
- `Voir toutes les resolutions` ouvre une liste complete filtree, pas seulement
  une table brute.

### Fiche decision - En-tete

Questions a poser:

- Le libelle `Resolution AG 3` suffit-il pour identifier le vote?
- Le titre `Travaux etancheite toiture` est-il assez concret?
- Le badge `Action en cours` vous dit-il ce qui reste a faire?
- La ligne `AG du 15/06/2024 - Majorite simple` est-elle utile?
- Le paragraphe de decision doit-il etre le texte exact du PV ou une synthese?
- Au clic sur `Actions`, quelles commandes attendez-vous?

Attentes retenues:

- L'en-tete doit afficher le numero de resolution, la date AG, le titre court, le
  statut humain et une synthese novice.
- Le texte exact du PV doit etre accessible via `Voir le texte source`, mais la
  premiere lecture reste une synthese.
- Le menu `Actions` contient: mettre a jour l'avancement, ajouter une preuve,
  ajouter une piece liee, preparer une relance syndic, exporter cette fiche.

### Cartes resume

Questions a poser carte par carte:

- `Responsable`: qui est responsable, et qui est referent dans le CS?
- `Echeance`: la date est-elle la date legale, la date de relance, ou la date
  cible interne?
- `Statut`: que signifie `Suivi en cours` par rapport a `Action en cours`?
- `Priorite`: `Moyenne` suffit-il ou faut-il expliquer l'impact?

Attentes retenues:

- Les cartes doivent repondre a quatre questions: qui, quand, ou en est-on,
  pourquoi prioritaire.
- Si une date est depassee, la carte `Echeance` devient `En retard depuis X
  jours` et propose `Preparer une relance`.
- `Statut` affiche un libelle unique et une micro-phrase de consequence.
- `Priorite` affiche aussi la raison: budget, travaux, securite, juridique,
  preuve manquante, diffusion.

### Onglets

Questions generales:

- Comprenez-vous la difference entre `Preuves` et `Pieces liees`?
- Quand vous changez d'onglet, voulez-vous rester sur la meme resolution?
- Les onglets doivent-ils montrer un compteur?

Attentes retenues:

- Les onglets gardent la resolution selectionnee.
- Chaque onglet a un compteur si possible.
- Les onglets ne doivent jamais etre vides sans expliquer la prochaine action.

#### Onglet Action en cours

Questions a poser:

- La carte `Suivi de l'action` vous dit-elle quoi faire ensuite?
- L'avancement `60%` vous parait-il fiable sans preuve?
- Au clic sur `Mettre a jour l'avancement`, quels champs faut-il demander?

Attentes retenues:

- L'avancement ne suffit pas: il doit etre associe a une trace ou un commentaire.
- La prochaine etape est le point le plus important de l'onglet.
- La mise a jour demande: nouvel etat, pourcentage optionnel, commentaire,
  preuve ou piece liee, date de prochaine relance.

#### Onglet Preuves

Questions a poser:

- `Aucune preuve ajoutee pour le moment` vous inquiete-t-il ou vous guide-t-il?
- Au clic sur `Ajouter une preuve`, choisissez-vous un document existant, un
  fichier local, ou une note de verification?
- Qu'est-ce qui rend une preuve valide?

Attentes retenues:

- Une preuve confirme une date, un montant, une decision, une execution ou une
  reponse.
- `Ajouter une preuve` propose: choisir une piece existante, ajouter un fichier,
  saisir une preuve de relance/reponse, marquer comme preuve a demander.
- Une preuve affiche: type, source, date, statut de verification, diffusion
  possible ou restriction.

#### Onglet Pieces liees

Questions a poser:

- Les icones PDF/XLS/DOC aident-elles a comprendre le contenu?
- Au clic sur telechargement, attendez-vous ouvrir, telecharger ou exporter une
  copie diffusable?
- Le menu `...` doit-il proposer renommer, rattacher, detacher, verifier,
  masquer?
- Que manque-t-il pour savoir si une piece prouve vraiment l'action?

Attentes retenues:

- Une piece liee n'est pas toujours une preuve; la page doit dire son role.
- Chaque piece affiche: titre, type, date d'ajout, role (`source du vote`,
  `devis`, `preuve candidate`, `preuve validee`, `annexe utile`), statut de
  diffusion.
- Le menu de piece contient: ouvrir, rattacher comme preuve, detacher de la
  resolution, voir la fiche document, preparer une version diffusable.

#### Onglet Relance syndic

Questions a poser:

- Voulez-vous voir les relances envoyees, les relances a envoyer, ou le brouillon
  de prochaine relance?
- `En attente` signifie quoi: envoyee sans reponse, non envoyee, ou reponse a
  verifier?
- Au clic sur `Voir tout`, attendez-vous une chronologie ou une liste de
  demandes?
- Que doit produire un bouton `Preparer une relance`?

Attentes retenues:

- L'onglet montre trois etats: a preparer, envoyee sans reponse, repondue a
  verifier.
- Le produit ne pretend pas envoyer un email si l'envoi reel n'existe pas.
- `Preparer une relance` produit un message copiable, trace le brouillon, et
  demande a l'utilisateur de noter le canal d'envoi.
- Une relance doit citer la decision, la preuve attendue, l'echeance et la
  derniere demande.

#### Onglet Historique

Questions a poser:

- La timeline en bas vous aide-t-elle a comprendre ce qui s'est passe?
- Voulez-vous cliquer sur un evenement pour voir sa preuve?
- Faut-il distinguer creation, piece ajoutee, relance envoyee, reponse syndic,
  avancement?
- Que doit rester en memoire pour une passation de CS?

Attentes retenues:

- L'historique est la memoire probatoire de l'action.
- Chaque evenement affiche date, type, auteur/role, note courte, preuve ou piece
  liee.
- Un evenement sans preuve doit etre signale comme trace de travail, pas comme
  preuve validee.
- La passation reprend: decision, action ouverte, derniere relance, preuve
  manquante, risque et personne referente.

## Structure visuelle attendue pour `/actions`

La route `/actions` doit reprendre la densite et la hierarchie de l'image:

- shell `cs-*` avec sidebar sombre fixe, topbar compacte, zone de travail claire;
- header page avec titre, sous-titre, recherche, aide, notification, export,
  creation;
- layout principal en deux colonnes:
  - colonne gauche `Registre des AG`, largeur stable, liste groupee par AG;
  - colonne droite `Fiche decision`, largeur fluide;
- en-tete de fiche avec badge de resolution, titre, statut, date AG, majorite,
  synthese;
- quatre cartes resume: responsable, echeance, statut, priorite;
- barre d'onglets: Action, Preuves, Pieces liees, Relance syndic, Historique;
- zone contenu de l'onglet actif;
- timeline horizontale ou verticale visible en bas de fiche sur desktop;
- sur mobile: la liste AG devient un tiroir ou une section repliee, la fiche
  reste prioritaire.

## Composants

Composants front attendus:

- `cs-shell`, `cs-sidebar`, `cs-topbar`, `cs-canvas`;
- `cs-page-header`, `cs-search`, `cs-icon-button`, `cs-primary-action`;
- `cs-registry-layout`, `cs-ag-list`, `cs-ag-group`, `cs-resolution-card`;
- `cs-decision-panel`, `cs-decision-header`, `cs-status-badge`;
- `cs-summary-card`;
- `cs-tabs`, `cs-tab`, `cs-tab-panel`;
- `cs-action-progress`, `cs-progress-bar`;
- `cs-proof-card`, `cs-piece-card`, `cs-followup-card`;
- `cs-history-timeline`, `cs-history-event`;
- `cs-empty-state`, `cs-filter-menu`, `cs-action-menu`;
- `cs-safe-export-notice`.

Regles UI:

- Les cartes gardent un rayon sobre, 8px maximum sauf convention existante.
- Les icones peuvent aider les boutons, mais un libelle textuel clair reste
  present pour les actions principales.
- Aucun compteur non cliquable.
- Aucun statut porte par la couleur seule.
- Chaque bouton nomme sa consequence: `Ajouter une preuve`, `Preparer une
  relance`, `Rattacher comme preuve`, `Exporter cette fiche`.
- Pas de promesse d'envoi email automatique sans backend d'envoi.

## Contrat donnees `model.ux.registre`

Le dev back/viewmodel doit stabiliser `model.ux.registre` tout en gardant les
cles existantes necessaires aux routes en cours (`model.action_items`,
`model.action_summary`, exports existants).

Structure cible:

```text
model.ux.registre = {
  context,
  summary,
  facets,
  filters,
  ag_groups,
  items,
  selected,
  tabs,
  empty_states,
  export,
}
```

### `context`

Champs attendus:

- `coffre_label`: nom affichable du coffre local;
- `sharing_mode_label`: exemple `Prive local`;
- `sharing_mode_detail`: aucune synchronisation externe lancee;
- `role_label`: exemple `Conseil syndical`;
- `as_of_label`: date ou exercice de situation.

### `summary`

Champs attendus:

- `total_resolutions`;
- `open_actions`;
- `late_actions`;
- `missing_proofs`;
- `syndic_followups`;
- `verified_proofs`;
- `share_blockers`;
- `last_updated_label`.

Chaque compteur expose un `href` local et token-safe.

### `facets` et `filters`

Facettes minimum:

- `ag`;
- `status`;
- `owner`;
- `priority`;
- `proof_state`;
- `due_state`;
- `scope`.

Filtre actif:

- `selected_ag`;
- `selected_status`;
- `selected_owner`;
- `selected_priority`;
- `selected_proof_state`;
- `query`;
- `selected_item_id`.

### `ag_groups`

Chaque groupe:

- `ag_id`;
- `label`: exemple `AG du 15/06/2024`;
- `date`;
- `open_count`;
- `late_count`;
- `is_expanded`;
- `href`;
- `items`: liste de cartes resolution.

Chaque carte resolution:

- `id`;
- `resolution_ref`;
- `title`;
- `subtitle`;
- `status_label`;
- `status_tone`;
- `priority_label`;
- `proof_state_label`;
- `owner_label`;
- `due_label`;
- `is_selected`;
- `href`;

### `items`

Chaque action-registre est un objet detail compatible avec les cartes et la
fiche:

- `id`;
- `ag_id`;
- `resolution_ref`;
- `source_doc_id`;
- `source_file_label`;
- `title`;
- `decision_summary`;
- `decision_source_excerpt`;
- `majority_label`;
- `status`;
- `status_label`;
- `status_detail`;
- `status_tone`;
- `priority`;
- `priority_label`;
- `priority_reason`;
- `owner`;
- `referent`;
- `due_on`;
- `due_label`;
- `due_state`;
- `progress_pct`;
- `next_step`;
- `action_description`;
- `proof_expected`;
- `proof_state`;
- `proof_state_label`;
- `proofs`;
- `pieces`;
- `followups`;
- `history`;
- `diffusion`;
- `memory`;
- `href`;

### `selected`

`selected` est l'objet complet de `items` correspondant a `selected_item_id`.
S'il n'y a aucune selection, prendre la premiere action ouverte. S'il n'y a pas
d'action, fournir un objet vide exploitable par les etats vides.

### Preuves

Chaque preuve:

- `proof_id`;
- `label`;
- `type_label`;
- `source_doc_id`;
- `source_label`;
- `captured_on`;
- `verified_on`;
- `status`: `missing`, `candidate`, `verified`, `rejected`, `blocked`;
- `status_label`;
- `confirms`: date, montant, vote, execution, reponse, autre;
- `diffusion_label`;
- `restriction_reason`;
- `href`;

### Pieces liees

Chaque piece:

- `doc_id`;
- `label`;
- `type_label`;
- `added_on`;
- `role_label`: source du vote, devis, facture, PV, preuve candidate, annexe;
- `proof_relation`: none, candidate, verified, rejected;
- `diffusion_label`;
- `href`;
- `download_href`;
- `actions`: ouvrir, rattacher comme preuve, detacher, fiche document,
  preparer version diffusable.

### Relances syndic

Chaque relance:

- `followup_id`;
- `label`;
- `status`: `draft`, `to_send`, `sent_waiting`, `answered_to_check`, `closed`;
- `status_label`;
- `sent_on`;
- `channel_label`;
- `recipient_label`;
- `message_excerpt`;
- `expected_answer`;
- `answer_summary`;
- `related_request_id`;
- `copy_text`;
- `href`;

### Historique

Chaque evenement:

- `event_id`;
- `occurred_on`;
- `type`: creation, update, proof_added, piece_linked, followup_sent,
  syndic_answer, progress_update, closed, reopened;
- `type_label`;
- `actor_label`;
- `summary`;
- `proof_ids`;
- `piece_ids`;
- `followup_ids`;
- `is_evidence`;
- `memory_note`;

### Diffusion et memoire

`diffusion`:

- `status`: local_only, cs_only, copro_ok, after_redaction, blocked;
- `label`;
- `reason`;
- `allowed_audience`;
- `blocked_by`;

`memory`:

- `handover_note`;
- `timeline_ref`;
- `open_risk`;
- `pack_section`;
- `next_review_label`;

## Interactions attendues

- Recherche: filtre instantane ou submit, mais conserve la selection si elle
  reste dans le resultat.
- Selection resolution: recharge ou met a jour la fiche avec `selected_item_id`
  dans l'URL.
- Filtre: met a jour la colonne gauche, les compteurs et l'URL.
- Onglet: conserve la resolution; peut etre represente par ancre ou parametre
  `tab=preuves`, `tab=pieces`, `tab=relance`, `tab=historique`.
- Export registre: exporte le perimetre courant et indique si l'export est
  interne CS, diffusable copro ou bloque par restriction.
- Nouvelle action: propose un formulaire de creation rattachee a une AG ou libre.
- Mettre a jour l'avancement: ajoute un evenement d'historique et demande une
  note; ne transforme pas automatiquement un pourcentage en preuve.
- Ajouter une preuve: selectionne une piece existante, ajoute un document local
  ou cree une preuve a demander.
- Ajouter une piece: rattache un document a la decision sans le declarer preuve
  tant que l'utilisateur ne le confirme pas.
- Preparer une relance syndic: genere un brouillon copiable, rattache la
  resolution, la preuve attendue et l'historique des demandes.
- Voir tout relances: ouvre la vue des relances filtree sur la resolution ou sur
  `/demandes` si cette route porte les demandes syndic.
- Timeline: chaque evenement ouvre son detail ou la piece/preuve associee.

## Vues manquantes liees

### Detail action

Route cible possible: `/actions?selected=<id>` ou `/actions/<id>` selon
arbitrage dev.

Contenu obligatoire:

- decision source;
- action attendue;
- responsable et referent;
- echeance;
- statut et priorite;
- preuve attendue et preuves disponibles;
- pieces liees;
- relances;
- historique;
- prudence de diffusion;
- note de passation.

Critere: une personne qui ne connait pas le dossier peut reprendre l'action sans
ouvrir un tableur brut.

### Relance syndic

Route cible possible: `/actions?selected=<id>&tab=relance` ou `/demandes`.

Contenu obligatoire:

- brouillon de message copiable;
- destinataire/canal;
- date de derniere demande;
- date de relance proposee;
- preuve demandee;
- phrase de contexte citant la resolution;
- statut d'envoi explicite: brouillon, copiee, envoyee hors CoproScope,
  reponse recue a verifier.

No-go: afficher `Envoyee` si CoproScope n'a pas la preuve d'envoi ou si
l'utilisateur n'a pas confirme le canal.

### Pieces et preuves liees

Route cible possible: onglets `Preuves` et `Pieces liees`, avec liens vers
`/pieces` et `/documents`.

Contenu obligatoire:

- separation claire entre piece utile et preuve validee;
- statut de verification;
- diffusion possible ou restriction;
- action `Rattacher comme preuve`;
- action `Demander la preuve manquante`;
- historique de rattachement.

Critere: une piece ne cloture pas une action tant qu'elle n'est pas marquee
comme preuve du point suivi.

## Etats vides

Tous les etats vides doivent expliquer le probleme et proposer une suite.

- Aucune resolution: `Aucune decision AG chargee. Ajouter ou importer un PV /
  registre AG pour commencer.`
- Aucun resultat filtre: `Aucune resolution ne correspond a ce filtre. Retirer
  un filtre ou afficher toutes les AG.`
- Aucune preuve: `Aucune preuve validee pour cette action. Ajouter une piece,
  choisir une preuve existante ou preparer une demande au syndic.`
- Aucune piece liee: `Aucune piece rattachee. Ajouter le PV, un devis, une
  facture, une reponse syndic ou une note de verification.`
- Aucune relance: `Aucune relance tracee. Preparer un message copiable et noter
  le canal d'envoi.`
- Aucun historique: `Aucune trace encore inscrite. La prochaine mise a jour
  creera le premier evenement.`
- Export bloque: `Export non prepare car au moins un element demande une
  verification de diffusion.`

## Criteres d'acceptation

- `/actions` ressemble a la source visuelle par structure: colonne AG, fiche
  decision, cartes resume, onglets, cartes action/preuve/piece/relance,
  historique.
- Une resolution ouverte montre toujours responsable, echeance, statut humain,
  priorite, prochaine action, preuve attendue et diffusion.
- Le membre CS novice distingue `preuve` et `piece liee`.
- Chaque compteur, carte et onglet a un lien ou une action utile.
- Les statuts sont lisibles sans connaitre les codes internes.
- Une preuve manquante propose soit `Ajouter une preuve`, soit `Preparer une
  relance syndic`.
- Une relance affiche clairement si elle est brouillon, copiee, envoyee hors
  CoproScope, repondue, ou a verifier.
- L'historique garde la memoire des mises a jour, pieces, preuves, relances et
  reponses.
- Les liens conservent le token local quand la route est protegee.
- Aucun chemin prive, `raw`, `restricted`, `logs`, `file://` ou chemin absolu
  utilisateur n'apparait dans l'UI ou les exports de la route.
- Les etats vides guident l'utilisateur vers une action concrete.
- La page reste utilisable au clavier: focus visible, onglets accessibles,
  boutons nommes, tables avec titres ou captions si elles restent presentes.

## Tests attendus

Tests front/route:

- route `/actions` retourne 200 avec token;
- route protegee retourne 403 sans token si un token est configure;
- presence du shell, du titre `Registre des decisions`, de la colonne AG et de
  la fiche decision;
- presence des onglets `Action`, `Preuves`, `Pieces liees`, `Relance syndic`,
  `Historique`;
- chaque compteur et carte critique contient un `href` local;
- aucun lien interne ne perd le token quand le token est present;
- les boutons principaux portent des libelles consequences.

Tests viewmodel:

- `model.ux.registre.summary` contient les compteurs et href attendus;
- `model.ux.registre.ag_groups` groupe les resolutions par AG;
- `model.ux.registre.selected` est stable avec ou sans `selected_item_id`;
- une instance vide produit des etats vides exploitables;
- preuve candidate, preuve manquante et preuve verifiee sont distinguees;
- pieces liees et preuves ne sont pas confondues;
- relances `draft`, `sent_waiting`, `answered_to_check` sont exposees avec
  libelles novices;
- historique trie chronologiquement les evenements;
- les champs publics masquent chemins prives et dossiers sensibles.

Tests UX/langage/securite:

- absence de jargon primaire non traduit (`vault`, `hash`, `ACL`, `RBAC`,
  `P1/P2` seuls);
- `Mode prive local` ou equivalent visible;
- aucune promesse d'envoi email automatique;
- export bloque ou averti si diffusion incertaine;
- comparaison visuelle par blocs avec
  `docs/assets/etude-utilisateurs/registre-decisions-actions-preuves.png`;
- scenario novice: selectionner une resolution en retard, identifier la preuve
  manquante, preparer une relance, retrouver l'historique.

Commande indicative depuis `server/` une fois le dev livre:

```powershell
.\.venv\Scripts\python.exe -m unittest tests.test_ui_registre_actions -v
.\.venv\Scripts\python.exe -m unittest tests.test_ui_novice_language_static -v
```

Des tests dedies Cycle 2 devront etre ajoutes ou completes par les devs selon
leur ownership exact; ce document ne modifie ni templates ni tests.

## Commande dev prete

Developper Cycle 2 `/actions` comme registre decision-action-preuve a partir de
la source visuelle `registre-decisions-actions-preuves.png`.

Priorite de livraison:

1. Stabiliser `model.ux.registre` avec `summary`, `ag_groups`, `items`,
   `selected`, `tabs`, `empty_states`, `export`.
2. Refaire la structure front `/actions` en deux colonnes avec fiche detaillee et
   onglets.
3. Implementer les vues de detail action, relance syndic, preuves et pieces
   liees dans la meme route ou via routes dediees arbitrees.
4. Verrouiller les tests route, DOM, viewmodel, langage novice, token et
   anti-fuite.

Definition de fini:

- une decision AG ne reste plus un texte archive;
- elle devient une action suivie;
- l'action dit quelle preuve manque ou existe;
- la relance syndic est preparable et tracee;
- l'historique peut servir de memoire de copropriete et de passation CS.
