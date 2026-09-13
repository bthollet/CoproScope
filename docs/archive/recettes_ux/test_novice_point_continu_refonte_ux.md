# Point testeur novice continu - Comptes / Memoire / vues manquantes

Date de reference: 2026-05-21.

Role: Agent novice continu. Je teste comme membre de conseil syndical non
technicien: je veux savoir quoi cliquer, ce que le clic promet, ce qui me
bloque, et quel est le prochain bouton utile.

Perimetre de modification: ce fichier et
`docs/test_novice_cycle5_vues_manquantes.md` uniquement. Aucun code applicatif
modifie.

## Preuves d'execution

Commandes lancees depuis `server/`:

- `.\.venv\Scripts\python.exe -m unittest tests.test_ui_cockpit -v`
  -> 5 tests OK.
- `.\.venv\Scripts\python.exe -m unittest tests.test_ui_comptes_guide -v`
  -> 7 tests lances, 4 OK, 3 skips car le layout cible Cycle 3 et
  `model.ux.comptes` ne sont pas encore livres.
- `.\.venv\Scripts\python.exe -m unittest tests.test_ui_memoire -v`
  -> 3 tests OK.
- `.\.venv\Scripts\python.exe -m unittest tests.test_ui_atelier_piece -v`
  -> 2 tests OK.
- `.\.venv\Scripts\python.exe -m unittest tests.test_ui_registre_actions -v`
  -> 6 tests OK.
- `.\.venv\Scripts\python.exe -m unittest tests.test_ui_smoke_routes_expanded -v`
  -> ECHEC: 2 erreurs sur `/actions`.
- `.\.venv\Scripts\python.exe -m unittest tests.test_ui_requests tests.test_ui_requests_route -v`
  -> ECHEC: `test_requests_route_requires_token_and_renders_novice_view`.
- `.\.venv\Scripts\python.exe -m unittest tests.test_ui_pilotage tests.test_ui_pilotage_route -v`
  -> ECHEC: 1 erreur template isolee, 1 assertion route.

Verification TestClient simple sur l'instance synthetique:

| Route cliquee | Resultat | Lecture novice |
|---|---:|---|
| `/` | 200 | Cockpit avec `Actions en retard`, `Pieces manquantes`, `Demandes syndic`. |
| `/comptes` | 200 | Lecture P1/P2/OK disponible. |
| `/chantiers` | 200 | Memoire/passation disponible en amont. |
| `/pieces?proof=missing` | 200 | Atelier pieces lisible, etat vide correct. |
| `/actions` | erreur | `jinja2.exceptions.UndefinedError: 'dict object' has no attribute 'action'`. |
| `/actions?priority=P1` | erreur | Bloque la vue `Actions en retard`. |
| `/actions?status=a_demander` | erreur | Bloque la vue preuves/relances a demander. |
| `/actions?scope=syndic` | erreur | Bloque la vue `Demandes syndic` / relance syndic. |

## Synthese go / no-go

| Surface | Clic utilisateur | Decision |
|---|---|---|
| Controle comptes | `/comptes` | GO lecture guidee, NO-GO parcours final. |
| Memoire copropriete | `/chantiers` | GO passation amont, NO-GO vraie memoire timeline. |
| Retards | `Actions en retard` -> `/actions?priority=P1` | NO-GO utilisateur. |
| Pieces manquantes | `Pieces manquantes` -> `/pieces?proof=missing` | GO amont, NO-GO boucle complete. |
| Relance syndic | `Demandes syndic` ou `Preparer une relance syndic` -> `/actions...` | NO-GO utilisateur. |

## Controle des comptes `/comptes`

Question utilisateur: "Puis-je comprendre quoi demander au syndic avant l'AG
sans etre comptable ?"

### Ce que je clique

- J'ouvre `/comptes`.
- Je lis les compteurs `P1 a traiter`, `P2 a confirmer`, `OK avec preuve`.
- Je regarde `Prochain geste humain`.
- Je descends vers `P1 a traiter`, `P2 a confirmer`, `OK avec preuve rattachee`.
- Je regarde `Questions syndic`.
- Je clique les liens actuels `traiter les P1`, `confirmer les P2`,
  `preparer l'envoi syndic` si je veux passer a l'action.

### Ce que j'attends

- Chaque P1 doit dire pourquoi c'est bloquant, quelle preuve manque, et quelle
  demande poser.
- Chaque P2 doit rester prudent: plausible, a confirmer, pas une accusation.
- Chaque OK doit citer une preuve ou expliquer qu'aucune question n'est utile.
- La question syndic doit etre copiable, neutre, et rattachee au point regarde.
- La sortie AG doit etre diffusable sans chemin prive ni conclusion comptable
  definitive.

### Ce qui marche

- La route `/comptes` rend en 200.
- Les tests dedies valident P1, P2, OK avec preuve, prochain geste humain,
  questions syndic, mode prive local et token local.
- L'etat sans sorties comptables reste lisible:
  `Generer ou importer les sorties ComptaScope`.

### Ce qui me bloque

- Le layout cible n'est pas livre: les tests skip encore
  `Exporter le rapport`, `Factures rapprochees`, `Depenses par categorie`,
  `Afficher aussi les categories sans alerte`, `Questions au syndic`,
  `Detail`, `Rapport AG`.
- Le contrat `model.ux.comptes` cible n'est pas livre.
- Les liens d'action de `/comptes` basculent vers `/actions?...`, et `/actions`
  casse dans le smoke simple.
- Je peux lire les anomalies, mais pas encore faire le parcours complet:
  anomalie -> question syndic -> preuve attendue -> relance ou rapport AG.

### Prochain bouton utile

Bouton existant utile: rester dans `/comptes` et lire `Questions syndic`.

Bouton a rendre fiable avant GO: `preparer l'envoi syndic`, car il doit ouvrir
une vue `/actions?scope=syndic` ou equivalente sans erreur serveur.

### Go / no-go

Decision: GO pour test dev et lecture guidee. NO-GO livraison utilisateur finale.

## Memoire de copropriete `/chantiers`

Question utilisateur: "Si je quitte le conseil syndical demain, une autre
personne peut-elle reprendre le fil ?"

### Ce que je clique

- J'ouvre `/chantiers`.
- Je lis l'accroche `Memoire de copropriete`.
- Je lis `Sujets ouverts`.
- Je clique `Liste d'actions`.
- Je regarde `Prochaine passation`.
- Je clique `preuves de decisions a obtenir`, `pieces essentielles a demander`
  ou `incidents a completer`.
- Je descends vers `Decisions non cloturees`, `Incidents a transmettre`,
  `Contrats et travaux`, `Preuves essentielles`, `Diffusion et restreint`.
- Je clique `Atelier pieces` si je veux reprendre les preuves.

### Ce que j'attends

- Une ligne de vie: date, evenement, document, statut, preuve, prochaine action.
- Une passation claire: sujets chauds, pieces indispensables, restrictions,
  et prochains gestes.
- Un panneau `A transmettre` ou pack passation: ce qui est inclus, exclu,
  restreint.
- Des liens qui ne renvoient pas vers une page cassee.

### Ce qui marche

- `/chantiers` rend en 200.
- Les tests Memoire passent, y compris l'instance vide.
- La page expose deja: `Sujets ouverts`, `Prochaine passation`,
  `Decisions non cloturees`, `Contrats et travaux`, `Preuves essentielles`,
  `Diffusion et restreint`.
- Les exports passation avaient deja ete couverts par les tests precedents.

### Ce qui me bloque

- La navigation visible garde `Chantiers`; le viewmodel sait dire
  `Memoire copropriete`, mais le shell n'est pas aligne.
- Le titre principal reste `Passation conseil syndical`, pas
  `Memoire de copropriete`.
- Les liens de reprise principaux pointent vers `/actions?...`, qui casse dans
  le smoke simple.
- La page est une bonne passation amont, pas encore une timeline centrale avec
  detail evenement et pack `A transmettre`.

### Prochain bouton utile

Bouton existant utile: `Atelier pieces`, car `/pieces` rend et permet de
reprendre les preuves.

Bouton a rendre fiable avant GO: `Liste d'actions`, car la memoire doit pouvoir
ouvrir le sujet sans erreur.

### Go / no-go

Decision: GO passation amont. NO-GO vraie memoire utilisateur.

## Retards

Question utilisateur: "Qu'est-ce qui est en retard et que dois-je relancer ?"

### Ce que je clique

- Depuis le cockpit, je clique `Actions en retard`.
- Le href actuel est `/actions?priority=P1`.

### Ce que j'attends

- Une liste limitee aux retards ou urgences.
- Pour chaque ligne: pourquoi c'est en retard, echeance, preuve attendue,
  responsable, derniere relance, prochain geste.
- Un bouton direct `Preparer une relance syndic` quand la suite est une relance.

### Ce qui me bloque

- `/actions?priority=P1` leve une erreur Jinja.
- Le blocage est le meme que le smoke `/actions`:
  `selected.action` manquant dans `actions.html`.
- Je ne peux donc pas valider la vue retards comme utilisateur.

### Prochain bouton utile

Bouton produit attendu: `Actions en retard` doit ouvrir une liste stable, meme
vide, puis proposer `Preparer une relance syndic` ou `Ajouter une preuve`.

### Go / no-go

Decision: NO-GO utilisateur.

## Pieces manquantes

Question utilisateur: "Quelles pieces dois-je demander ou rattacher maintenant ?"

### Ce que je clique

- Depuis le cockpit ou la navigation, je clique `Pieces manquantes`.
- Le href actuel est `/pieces?proof=missing`.
- Dans l'atelier, je regarde `Pieces a demander`, `Preuves locales a verifier`
  et `File atelier`.
- Sur une ligne disponible, je clique `Ouvrir`.

### Ce que j'attends

- Une liste de pieces a demander avec priorite, raison, point rattache et action
  primaire.
- Une distinction simple entre piece manquante, preuve locale candidate et
  preuve validee.
- Un chemin pour transformer la piece manquante en demande ou relance.

### Ce qui marche

- `/pieces?proof=missing` rend en 200.
- Les tests Atelier pieces passent.
- L'etat vide est comprehensible: aucune piece a demander / aucune piece
  exploitable.
- Le test seed prouve que l'atelier sait relier DocOps, DecisionOps, incidents,
  actions et preuves.

### Ce qui me bloque

- La query `proof=missing` rend l'atelier, mais je ne vois pas encore une vue
  dediee "pieces manquantes" avec filtre lisible et prochaine relance.
- La boucle complete finit souvent par `/actions`, qui casse hors scenario seed.
- Je peux lire l'atelier, mais je ne peux pas encore garantir:
  piece manquante -> demande syndic -> relance -> preuve rattachee.

### Prochain bouton utile

Bouton existant utile: `Ouvrir` sur une ligne de l'atelier.

Bouton a rendre fiable avant GO: `Demander au syndic` ou `Preparer une relance`
depuis une piece manquante.

### Go / no-go

Decision: GO amont atelier. NO-GO boucle utilisateur complete.

## Relance syndic

Question utilisateur: "Puis-je preparer une relance sans croire que CoproScope a
envoye un email ?"

### Ce que je clique

- Depuis le cockpit, je clique `Demandes syndic`.
- Le href actuel est `/actions?scope=syndic`.
- Depuis `/comptes`, je clique `preparer l'envoi syndic`.
- Depuis une fiche action, je voudrais cliquer `Relance syndic` puis
  `Preparer une relance syndic`.

### Ce que j'attends

- Un brouillon copiable, pas un envoi automatique.
- La decision ou piece citee, la preuve demandee, le destinataire, le canal et
  l'echeance.
- Une trace apres envoi externe: date, canal, personne, prochaine verification.

### Ce qui marche

- Les tests dedies `tests.test_ui_registre_actions` passent et valident les
  libelles `Relance syndic` et `Preparer une relance syndic` dans le scenario
  seed.
- Le template contient bien une zone de brouillon prudent.

### Ce qui me bloque

- `/actions?scope=syndic` casse en TestClient simple.
- `/actions?status=a_demander` casse aussi.
- Le smoke elargi echoue sur `/actions`, donc je ne peux pas garantir l'arrivee
  utilisateur depuis le cockpit, les comptes ou la memoire.

### Prochain bouton utile

Bouton a rendre fiable: `Preparer une relance syndic` doit ouvrir une fiche
stable avec etat vide si aucune action n'est selectionnee.

### Go / no-go

Decision: NO-GO utilisateur.

## Prochaine attente utilisateur

Ordre conseille avant un nouveau GO utilisateur:

1. Stabiliser `/actions` pour toutes les arrivees simples:
   `/actions`, `/actions?priority=P1`, `/actions?status=a_demander`,
   `/actions?scope=syndic`.
2. Rejouer `tests.test_ui_smoke_routes_expanded`.
3. Rejouer le parcours novice:
   retards -> relance syndic -> preuve attendue -> historique.
4. Reprendre `/comptes` pour livrer le layout cible:
   categories, detail, questions au syndic, rapport AG.
5. Renommer visuellement `/chantiers` en Memoire et livrer timeline + pack de
   passation.
