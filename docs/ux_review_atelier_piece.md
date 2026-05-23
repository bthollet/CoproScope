# Audit UX/UI - bascule locale/vault et Atelier pieces

Date d'audit : 2026-05-20
Agent : G2 - testeur expert UX/UI
Perimetre inspecte : UI FastAPI/Jinja sous `server/src/coproscope/web/`, templates `base`, `overview`, `actions`, `documents`, `pieces`, `privacy`, `workstreams`, `depot`, viewmodel associe, tests UI/vault et docs vault/confidentialite.

## Synthese executive

L'UI locale est sobre, coherente et deja utile pour relier documents, actions, decisions et incidents. L'Atelier pieces formalise bien la chaine `piece -> point -> action -> preuve` en tableau, avec une densite adaptee a un conseil syndical moteur.

Le point faible majeur est la promesse "bascule locale/vault" : le vault existe dans la CLI, les tests et les specs, mais pas dans l'experience web. L'utilisateur ne voit ni statut de vault, ni verification, ni signatures, ni historique d'evenements, ni conflit. Pour une transition vers un coffre signe et synchronisable, l'UI actuelle ressemble encore a un cockpit local avec depot de fichiers et exports.

## Tests et inspection

- Commandes initiales faites dans le worktree demande : `Get-Location`, puis `git status --short --branch`; branche propre `codex/vault-ui-ux-review`.
- Tests tentes depuis `server/` avec `PYTHONPATH=src` :
  - `python -m unittest tests.test_ui_atelier_piece tests.test_ui_demo tests.test_vault -v`
  - `py -3.14 -m unittest tests.test_ui_atelier_piece tests.test_ui_demo tests.test_vault -v`
- Resultat :
  - 3 tests `CoproScopeVaultReconstructionTests` passent.
  - 9 tests vault crypto sont sautes car `cryptography` est absent.
  - les tests UI ne s'importent pas car `defusedxml` est absent.
- App locale non demarree et aucune capture navigateur produite, pour la meme raison de dependances manquantes. Aucune installation effectuee, aucun fichier UI modifie.

## Constats P0

### P0-1 - La bascule locale/vault n'existe pas dans l'UI web

La CLI expose `vault init/import/status/verify/snapshot` et les docs decrivent un vault chiffre, signe, append-only et synchronisable. Dans l'UI, le seul point proche est `Depot & exports`, qui gere un depot local et un pack local prive. Il n'y a pas d'etat "local seulement / vault initialise / vault verifie / sync degradee", pas de `vault verify`, pas de `local_root` vs `sync_root`, pas de compteur d'evenements/blobs/snapshots, pas de diagnostic d'integrite.

Risque UX : un membre du CS peut croire que deposer un fichier ou exporter un pack equivaut a l'avoir place dans le vault verifiable. C'est dangereux pour la comprehension de la source de verite.

Recommandation : ajouter une zone de confiance globale persistante, par exemple dans l'en-tete ou `Depot & exports`, avec mode courant, derniere verification, erreurs bloquantes, warnings, nombre d'evenements, blobs, snapshots et bouton de verification locale. Employer des libelles utilisateur : "Travail local", "Coffre chiffre", "Verification OK", "Historique incomplet", plutot que seulement `vault`.

### P0-2 - Historique et signatures invisibles sur les objets metier

Les specs demandent que l'UI affiche l'historique d'un document, d'un point, d'une action et d'un export, ainsi que validite des signatures, auteur logique, appareil et date UTC. L'Atelier pieces n'affiche aucun de ces elements : les lignes montrent priorite, piece, point, action, prochaine etape et parfois une preuve locale, mais pas l'origine evenementielle ni la confiance cryptographique.

Risque UX : l'Atelier peut donner un etat courant propre alors que l'historique signe, les conflits ou un evenement invalide devraient etre visibles.

Recommandation : pour chaque ligne de l'Atelier, ajouter un etat de confiance discret mais lisible : source de l'etat, dernier evenement, signature `valide / a verifier / invalide`, auteur/appareil si disponible, et lien "Historique". Les erreurs d'integrite doivent remonter avant les actions ordinaires.

## Constats P1

### P1-1 - La chaine piece -> point -> action -> preuve est visible, mais pas actionnable

`pieces.html` affiche les bons axes : "Pieces a demander", "Preuves locales a verifier" et "File atelier". Le viewmodel calcule pourtant un `href` par item, mais le template ne l'utilise pas sur les lignes. La file devient donc une lecture, pas un poste de travail.

Recommandation : rendre chaque ligne ouvrable vers le bon contexte (`Documents`, `Actions`, `Chantiers`, preuve locale), avec un detail qui garde les quatre elements ensemble : piece, point, action, preuve. Ajouter aussi une action primaire par ligne : "Demander", "Verifier", "Rattacher", "Cloturer".

### P1-2 - La confidentialite n'est pas visible au moment de manipuler une piece

La vue `Confidentialite` est utile et explicite les statuts de diffusion, biffage et arbitrage. Mais l'Atelier pieces ne signale pas si une preuve locale est brute, biffable, agregee, bloquee ou a arbitrer.

Risque UX : un utilisateur peut passer de l'Atelier a une demande ou un export sans voir que la piece liee ne doit pas sortir telle quelle.

Recommandation : afficher sur chaque preuve/piece un badge de diffusion : `Brut`, `Apres biffage`, `Aggregation`, `Bloque`, `A arbitrer`, avec un lien vers la revue PrivacyOps si le statut n'est pas directement diffusable.

### P1-3 - La densite des tableaux risque de noyer les decisions du CS

L'Atelier juxtapose deux tableaux en colonnes puis une file globale a 5 colonnes. C'est efficace pour un utilisateur expert, mais fragile pour un CS non expert : "Action attendue" et "Prochaine etape" peuvent se ressembler, les statuts techniques prennent beaucoup de place, et les longues preuves/chemins peuvent transformer la ligne en bloc vertical.

Recommandation : conserver la table globale pour l'audit, mais ajouter au-dessus une vue de travail par priorite : "A demander au syndic", "A verifier localement", "A rattacher", "Bloque confidentialite". Chaque item devrait tenir en une fiche compacte non imbriquee, avec la prochaine action en premier.

### P1-4 - Les filtres et compteurs ne ferment pas la boucle de travail

Dans l'Atelier, les compteurs "Statuts" renvoient tous vers `/pieces` sans filtre. Dans `Actions`, les filtres existent, mais l'Atelier ne permet pas de filtrer par source, statut, priorite, presence de preuve ou confidentialite.

Recommandation : rendre les compteurs filtrants et conserver le filtre courant dans l'URL. Les filtres prioritaires pour le CS : priorite, source, statut, preuve locale oui/non, diffusion bloquee/a arbitrer.

### P1-5 - Parcours conseil syndical incomplet

Le parcours attendu est : comprendre ce qui manque, demander au syndic, recevoir/verser une preuve, verifier confidentialite, rattacher, exporter ou passer le relais. Aujourd'hui ces etapes sont dispersees entre `Documents`, `Actions`, `Atelier pieces`, `Confidentialite`, `Chantiers` et `Depot & exports`.

Recommandation : definir un parcours "Jour de CS" depuis le cockpit : liste priorisee, responsable, echeance, prochain message/demande, preuve attendue, statut diffusion. L'Atelier doit etre le lieu de rattachement et de verification, pas seulement un recapitulatif.

## Constats P2

### P2-1 - Vocabulaire interne visible

Les libelles "Sprint 2", "Sprint 4", `DocAI local-heavy`, `Tout hors DocAI`, `DecisionOps`, `IncidentOps` parlent a l'equipe produit plus qu'a un conseil syndical.

Recommandation : remplacer par des libelles utilisateur : "Actions", "Atelier pieces", "Analyse locale avancee", "Tout analyser sauf IA lourde", "Decisions AG", "Incidents".

### P2-2 - Accessibilite basique a renforcer

Points positifs : navigation avec `aria-label`, titres structurants, tableaux avec en-tetes, texte non uniquement colore pour les priorites. Points faibles : pas de style `:focus-visible`, tables sans `caption` ni `scope`, champ fichier sans label visible, pas de lien d'evitement, navigation horizontale sticky potentiellement difficile au clavier.

Recommandation : ajouter un focus visible fort, des captions ou descriptions de tableaux, un label de champ fichier, et verifier le parcours clavier complet.

### P2-3 - Lisibilite mobile et debordements a tester visuellement

Le CSS protege les textes longs avec `overflow-wrap: anywhere` et `table-layout: fixed`, ce qui evite souvent le debordement. En contrepartie, les tableaux a 4 ou 5 colonnes deviennent vite peu lisibles en largeur et peuvent casser les mots ou chemins. Les deux tableaux hauts de l'Atelier ne sont pas dans une zone scroll horizontale dediee comme la file globale.

Recommandation : tester visuellement mobile/tablette. Si les lignes deviennent trop hautes, passer les tableaux de travail en layout empile : priorite + piece en tete, puis point, preuve, action.

### P2-4 - Coherence visuelle solide mais peu hierarchisee

La palette est sobre, les panneaux sont coherents et la densite convient au domaine. Le systeme manque surtout de hierarchie d'urgence : P1/P2 sont visibles, mais l'oeil ne distingue pas assez "a faire maintenant" de "information utile".

Recommandation : introduire une hierarchie constante : bande d'alerte pour P0/P1, actions primaires plus visibles, compteurs secondaires plus calmes, et statuts techniques relegues en detail.

## Recommandations priorisees

1. Creer un indicateur de confiance vault dans l'UI : mode local/vault, derniere verification, erreurs, evenements, blobs, snapshots.
2. Ajouter historique et signature au niveau document, point, action, preuve et export.
3. Enrichir l'Atelier avec badges confidentialite et liens directs vers preuve, action, demande syndic et revue PrivacyOps.
4. Transformer les compteurs Atelier en filtres reels et rendre les lignes actionnables.
5. Repenser la vue CS autour de files de travail : demander, verifier, rattacher, arbitrer, cloturer.
6. Remplacer les libelles internes par du vocabulaire metier conseil syndical.
7. Ajouter les controles accessibilite de base et valider mobile/tablette avec captures.

## Conclusion

L'Atelier pieces est une bonne base de lisibilite metier : il relie deja pieces, points, actions et preuves. Pour devenir l'interface d'une bascule locale/vault, il doit maintenant porter la confiance : historique, signatures, conflits, confidentialite et statut de synchronisation. Sans cela, l'utilisateur voit une file de travail, mais pas encore un coffre probatoire.
