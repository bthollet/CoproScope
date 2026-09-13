# Test novice Cycle 5 - vues manquantes

Date de reference: 2026-05-21.

Objectif: verifier les vues manquantes demandees par un utilisateur novice:
`retards`, `pieces manquantes`, `relance syndic`. Pour chaque vue, je note ce
que je clique, ce que j'attends, ce qui me bloque et le prochain bouton utile.

Perimetre de modification: ce fichier et
`docs/test_novice_point_continu_refonte_ux.md` uniquement. Aucun code applicatif
modifie.

## Signal d'entree

Le cockpit expose deja les cartes suivantes dans `model.ux.cockpit.summary_cards`
sur l'instance synthetique:

| Carte | Compteur observe | Href observe | Verdict |
|---|---:|---|---|
| Actions en retard | 3 | `/actions?priority=P1` | NO-GO: route cassee. |
| Pieces manquantes | 0 | `/pieces?proof=missing` | GO amont: route lisible. |
| Demandes syndic | 2 | `/actions?scope=syndic` | NO-GO: route cassee. |
| Echeances AG | 0 | `/chantiers?section=ag` | GO amont: Memoire/passation rend. |
| Alertes et risques | 1 | `/actions?status=a_revoir` | NO-GO probable: depend de `/actions`. |

Routes testees en TestClient simple:

| Route | Resultat |
|---|---|
| `/pieces?proof=missing` | 200, etat vide lisible. |
| `/chantiers?section=ag` | 200, passation rend. |
| `/actions?priority=P1` | erreur Jinja. |
| `/actions?status=a_demander` | erreur Jinja. |
| `/actions?scope=syndic` | erreur Jinja. |

## Vue retards

Question novice: "Qu'est-ce qui est en retard, et qu'est-ce que je dois faire
maintenant ?"

### Ce que je clique

- J'ouvre le cockpit `/`.
- Je clique la carte `Actions en retard`.
- Le lien actuel ouvre `/actions?priority=P1`.

### Ce que j'attends

- Une liste de sujets en retard ou prioritaires.
- Pour chaque sujet: raison du retard, echeance, responsable, preuve attendue,
  derniere relance, prochaine action.
- Une entree vide comprehensible si aucun retard n'existe.
- Un bouton de suite: `Preparer une relance syndic`, `Ajouter une preuve`, ou
  `Mettre a jour l'avancement`.

### Ce qui me bloque

- `/actions?priority=P1` casse avec:
  `jinja2.exceptions.UndefinedError: 'dict object' has no attribute 'action'`.
- Le test smoke elargi echoue aussi sur `/actions`.
- Je ne peux pas confirmer que la carte `Actions en retard` est utilisable par
  un membre du conseil syndical.

### Prochain bouton utile

Bouton attendu: `Actions en retard` doit ouvrir une liste stable, puis chaque
ligne doit proposer `Preparer une relance syndic` ou `Ajouter une preuve`.

### Go / no-go

Decision: NO-GO utilisateur.

Condition de GO: `/actions?priority=P1` rend une vue stable avec etat vide,
filtre visible et au moins un prochain geste explicite.

## Vue pieces manquantes

Question novice: "Quelle piece manque, pourquoi, et comment je la demande ?"

### Ce que je clique

- J'ouvre le cockpit `/`.
- Je clique `Pieces manquantes`.
- Le lien actuel ouvre `/pieces?proof=missing`.
- Dans la page, je regarde `Pieces a demander`, `Preuves locales a verifier`,
  `File atelier`.
- Si une ligne existe, je clique `Ouvrir`.

### Ce que j'attends

- Une liste filtree sur les pieces manquantes.
- Pour chaque piece: priorite, piece attendue, raison, point rattache, preuve
  locale eventuelle, action primaire.
- Un bouton qui transforme la piece en demande syndic ou relance.
- Un retour vers l'action ou la decision concernee.

### Ce qui marche

- `/pieces?proof=missing` rend en 200.
- L'etat vide est lisible:
  `Aucune piece a demander dans les sorties disponibles` et
  `Aucune piece exploitable dans les artefacts charges`.
- `tests.test_ui_atelier_piece` passe: avec donnees seed, l'atelier relie
  pieces, points, actions et preuves.

### Ce qui me bloque

- La vue reste l'atelier general; le filtre `proof=missing` n'est pas encore une
  vue novice dediee avec son propre titre, ses compteurs et son prochain geste.
- La boucle vers une demande ou relance finit encore par `/actions`, qui casse
  hors scenario seed.
- Le compteur observe est `0`; cela valide l'etat vide, pas un parcours complet
  de demande de piece.

### Prochain bouton utile

Bouton existant utile: `Ouvrir` dans l'atelier pieces.

Bouton attendu: `Demander cette piece au syndic`, avec brouillon ou action
tracee, puis retour vers la decision/action concernee.

### Go / no-go

Decision: GO amont pour l'etat vide et l'atelier. NO-GO boucle complete.

Condition de GO final: une piece manquante doit pouvoir devenir demande syndic,
relance, puis preuve rattachee sans passer par une route fragile.

## Vue relance syndic

Question novice: "Puis-je preparer une relance prudente, copiable, puis garder
la trace ?"

### Ce que je clique

- Depuis le cockpit, je clique `Demandes syndic`.
- Le lien actuel ouvre `/actions?scope=syndic`.
- Depuis le registre, je voudrais ouvrir l'onglet `Relance syndic`.
- Je clique ensuite `Preparer une relance syndic`.

### Ce que j'attends

- Une liste des demandes ou preuves attendues du syndic.
- Pour chaque demande: sujet, preuve attendue, derniere demande, destinataire,
  echeance, canal a noter.
- Un brouillon copiable.
- Un message clair: CoproScope ne l'envoie pas automatiquement.
- Une action de suivi apres envoi externe.

### Ce qui marche

- `tests.test_ui_registre_actions` passe.
- Le template contient les libelles `Relance syndic`,
  `Preparer une relance syndic` et une zone de brouillon prudent.

### Ce qui me bloque

- `/actions?scope=syndic` casse en TestClient simple.
- `/actions?status=a_demander` casse aussi.
- La fonctionnalite existe dans le scenario seed, mais l'arrivee depuis le
  cockpit ou les comptes n'est pas robuste.

### Prochain bouton utile

Bouton attendu: `Preparer une relance syndic`, ouvrant une fiche stable meme si
aucune action n'est preselectionnee.

### Go / no-go

Decision: NO-GO utilisateur.

Condition de GO: les routes `/actions?scope=syndic` et
`/actions?status=a_demander` rendent en 200, avec etat vide et brouillon
copiable.

## Vue AG / echeances

Question novice: "Ou reprendre les echeances AG si je ne passe pas par les
retards ?"

### Ce que je clique

- Je clique `Echeances AG`.
- Le lien actuel ouvre `/chantiers?section=ag`.

### Ce que j'attends

- Une vue des echeances ou decisions a reprendre.
- Les preuves attendues et la prochaine action.
- Un retour vers la memoire de copropriete.

### Ce qui marche

- `/chantiers?section=ag` rend en 200.
- La page affiche `Memoire de copropriete`, `Passation conseil syndical`,
  `Sujets ouverts`, `Prochaine passation`.

### Ce qui me bloque

- Le parametre `section=ag` n'isole pas visiblement une section AG.
- Les boutons de reprise `preuves de decisions a obtenir` et equivalents
  pointent vers `/actions?...`, qui casse.
- C'est une passation, pas encore une vue echeances dediee.

### Prochain bouton utile

Bouton existant utile: `Atelier pieces`.

Bouton attendu: `Voir les echeances en retard`, sans passer par une route
`/actions` fragile.

### Go / no-go

Decision: GO amont, NO-GO vue dediee.

## Decision Cycle 5

NO-GO utilisateur global pour les vues manquantes.

La seule surface suffisamment stable aujourd'hui est `Pieces manquantes` en
mode atelier/etat vide. Les vues `Retards` et `Relance syndic` dependent de
`/actions`, qui n'est pas robuste en arrivee simple.

## Prochaine verification

Apres correction applicative, relancer:

1. `.\.venv\Scripts\python.exe -m unittest tests.test_ui_smoke_routes_expanded -v`
2. `.\.venv\Scripts\python.exe -m unittest tests.test_ui_registre_actions -v`
3. `.\.venv\Scripts\python.exe -m unittest tests.test_ui_atelier_piece -v`
4. TestClient simple sur:
   `/actions?priority=P1`, `/actions?status=a_demander`,
   `/actions?scope=syndic`, `/pieces?proof=missing`,
   `/chantiers?section=ag`.
