# Test novice cycles refonte UX

Date de reference: 2026-05-21.

Role: membre de conseil syndical novice, testeur double flux.

Route testee pour le produit livre: `/`.

## Verdict court

Cockpit `/`: GO utilisateur provisoire. La route est disponible dans le controle
local et les libelles principaux du Cockpit sont presents. Le test manuel doit
encore etre rejoue en navigateur avec une personne novice, carte par carte.

Registre `/actions`: GO d'intention, mais GO conditionnel de langage. La
commande raconte bien le parcours decision -> action -> preuve -> relance ->
historique. Elle doit encore parler moins comme une commande produit et plus
comme une page de travail pour benevole.

Controle comptes `/comptes`: a challenger apres le Registre. Le risque principal
est de faire lire des codes et des categories au lieu d'aider la personne a
preparer une question claire au syndic avant l'assemblee generale.

## Regle de test think-aloud

Le testeur parle avant chaque clic:

- "Je vois..."
- "Je crois que ca sert a..."
- "Si je clique, je m'attends a..."
- "Apres le clic, je sais / je ne sais pas quoi faire."
- "Je sais / je ne sais pas si je peux partager."

Le facilitateur ne traduit pas les mots. Si le testeur demande ce que veut dire
un mot, le mot est note comme doute utilisateur.

## Script Cockpit `/`

### Arrivee sur la page

Question de depart:

- "En arrivant ici, que pensez-vous devoir faire en premier ?"

Attendu utilisateur:

- Je comprends que cette page me montre les sujets a traiter maintenant.
- Je vois les preuves ou pieces qui manquent.
- Je vois les demandes au syndic et les points a surveiller.
- Je peux aller vers le bon endroit sans connaitre tout CoproScope.

Phrase d'acceptation:

- "En moins d'une minute, je sais quel sujet ouvrir en premier et pourquoi."

### Lien "A faire maintenant"

Avant clic:

- "Je m'attends a voir toutes les actions ouvertes, triees par urgence."

Apres clic attendu:

- Une liste de choses a faire apparait.
- Chaque ligne dit pourquoi c'est la, quelle preuve manque ou existe, et quoi
  faire maintenant.
- Je peux revenir au Cockpit.

Phrase d'acceptation:

- "Je ne tombe pas sur un tableau brut: je vois les actions utiles."

### Carte "Actions en retard" ou action prioritaire

Avant clic:

- "Je m'attends a voir ce qui bloque ou ce qui est en retard."

Apres clic attendu:

- La page montre uniquement les actions urgentes ou bloquees.
- Chaque ligne explique le risque simple: retard, preuve manquante, arbitrage,
  reponse attendue.
- Une prochaine action est visible.

Phrase d'acceptation:

- "Je peux dire au conseil syndical ce qui doit etre traite en premier."

### Carte "Pieces manquantes"

Avant clic:

- "Je m'attends a voir les documents a demander ou a rattacher."

Apres clic attendu:

- Je vois le nom lisible de chaque piece attendue.
- Je comprends pourquoi cette piece est utile.
- Je vois a qui la demander ou ou la rattacher.
- Une ligne ne doit pas seulement ouvrir un fichier: elle doit expliquer le
  geste attendu.

Phrase d'acceptation:

- "Je sais quelle piece manque et pourquoi elle compte."

### Carte "Demandes syndic"

Avant clic:

- "Je m'attends a voir les questions ou relances au syndic."

Apres clic attendu:

- Je vois les demandes en attente, en cours ou resolues.
- Une demande ouverte montre la derniere relance, la reponse attendue et la
  prochaine action.
- Si le message n'a pas ete envoye par CoproScope, la page ne pretend pas qu'il
  est envoye.

Phrase d'acceptation:

- "Je sais quoi demander au syndic et ce qui est deja en attente."

### Carte "Echeances AG"

Avant clic:

- "Je m'attends a voir les dates importantes avant l'assemblee generale."

Apres clic attendu:

- Je vois les decisions, preuves et documents a preparer avant la date.
- Une echeance depassee dit clairement ce qu'il faut relancer.
- Les mots AG ou assemblee generale sont comprenables dans le contexte.

Phrase d'acceptation:

- "Je sais ce qui doit etre pret avant l'assemblee generale."

### Carte "Controle comptes"

Avant clic:

- "Je m'attends a voir les points comptables a expliquer avant l'AG."

Apres clic attendu:

- La route `/comptes` montre les points a traiter, a confirmer et ceux qui sont
  OK avec preuve.
- Une ligne comptable ouverte transforme le point en question simple pour le
  syndic.
- Je vois la preuve attendue ou la piece deja retrouvee.

Phrase d'acceptation:

- "Je peux preparer une question au syndic sans etre comptable."

### Carte "Alertes et risques"

Avant clic:

- "Je m'attends a voir ce qui demande prudence."

Apres clic attendu:

- Les alertes sont formulees sans dramatiser.
- Chaque alerte dit le sujet, l'impact, l'echeance ou la date de detection, et
  le statut.
- Le clic mene a une action ou une decision, pas seulement a une couleur rouge.

Phrase d'acceptation:

- "Je comprends le risque et je sais quoi faire avant de partager ou clore."

## Panneaux du Cockpit

### Panneau "Pieces manquantes"

Attendu au clic sur "Voir tout":

- J'arrive sur la liste complete des pieces a demander ou rattacher.
- Le pourcentage de completude ne suffit pas: je dois voir les pieces concretes.

Attendu au clic sur une ligne:

- J'ouvre le detail de la piece attendue ou l'action pour la demander.
- Je vois la raison, la source attendue et la prochaine etape.

Phrase d'acceptation:

- "La ligne me dit quoi faire, pas seulement ce qui manque."

### Panneau "Demandes syndic"

Attendu au clic sur "Voir tout":

- J'arrive sur les demandes au syndic.
- Les statuts sont en mots simples: a preparer, envoyee sans reponse, reponse a
  verifier, resolue.

Attendu au clic sur une ligne:

- J'ouvre la demande.
- Je vois le message ou la question, la preuve attendue, la derniere relance et
  le canal utilise ou a utiliser.

Phrase d'acceptation:

- "Je peux reprendre une relance sans rechercher l'historique ailleurs."

### Panneau "AG"

Attendu au clic sur "Voir tout":

- J'arrive sur la preparation de l'assemblee generale.
- Je vois les decisions ouvertes et les pieces qui doivent etre pretes.

Attendu au clic sur une echeance:

- J'ouvre le sujet lie a cette date.
- La page me dit si c'est a preparer, a relancer ou deja couvert.

Phrase d'acceptation:

- "Je comprends pourquoi cette date compte."

### Panneau "Controle comptes"

Attendu au clic sur "Voir tout":

- J'arrive sur `/comptes`.
- Je vois les controles classes en mots humains.

Attendu au clic sur une ligne a surveiller:

- J'ouvre le point comptable concerne.
- Je vois la question syndic prete ou la preuve attendue.
- Je vois si le point peut etre explique en AG ou s'il manque encore quelque
  chose.

Phrase d'acceptation:

- "Je peux transformer un point comptable en demande claire."

### Tableau "Alertes et risques"

Attendu au clic sur le niveau d'une ligne:

- J'ouvre l'action ou le sujet qui explique l'alerte.
- Le niveau ne doit pas etre le seul indice: le texte doit expliquer l'impact.

Attendu au clic mental sur chaque colonne:

- Sujet: je comprends de quoi on parle.
- Detail: je comprends ce qui est observe.
- Impact: je comprends pourquoi ca compte.
- Echeance / detection: je sais si c'est urgent.
- Statut: je sais si c'est ouvert, bloque, a verifier ou OK.

Phrase d'acceptation:

- "Je peux expliquer l'alerte a un autre membre du conseil syndical."

### Bandeau de confiance

Attendu au clic sur "Decisions, actions, preuves":

- J'arrive dans l'espace ou les decisions, actions et preuves sont suivies.
- Je comprends que rien n'est partage automatiquement.
- Si le libelle ouvre une memoire ou un chantier, le mot doit le dire plus
  clairement.

Phrase d'acceptation:

- "Je sais que je suis encore dans un espace local de travail."

## Lignes et listes: regle commune

Pour toute ligne cliquable du Cockpit:

- avant clic, je dois comprendre l'objet de la ligne;
- apres clic, je dois voir le detail utile ou la liste filtree attendue;
- la ligne ne doit pas modifier, envoyer, exporter ou partager sans demande
  explicite;
- la ligne doit garder une voie de retour vers le Cockpit ou la liste.

Phrase d'acceptation:

- "Chaque ligne que j'ouvre me rapproche d'une action concrete."

## Challenge Cycle 2 Registre `/actions`

### Ce qui parle deja comme un membre CS novice

- Le parcours decision -> action -> preuve -> relance -> historique est bon.
- La commande refuse le simple tableau brut.
- La difference entre piece utile et preuve verifiee est bien posee.
- La relance syndic est decrite comme un brouillon copiable si aucun envoi reel
  n'existe.
- L'historique sert de memoire de passation, ce qui parle bien au conseil
  syndical.

### Ce qui parle encore trop produit

Libelles a simplifier avant livraison:

- "Registre decisions - actions - preuves" peut devenir "Suivre les decisions
  et les preuves".
- "Resolution AG" doit etre explique la premiere fois: "decision votee en
  assemblee generale".
- "Exporter le registre" doit dire le public: "Preparer un extrait pour le
  conseil syndical" ou "Preparer une version partageable".
- "Nouvelle action" peut devenir "Ajouter un suivi".
- "Action en cours" et "Suivi en cours" ne doivent pas cohabiter si le sens est
  le meme.
- "Preuve candidate" peut devenir "piece qui peut servir de preuve".
- "Diffusion" doit toujours repondre a "qui peut voir ?".
- "P1" et "P2" ne doivent jamais etre seuls: dire "a traiter avant l'AG" et "a
  confirmer".

### Questions a poser sur l'image Registre

- "Quand vous choisissez une decision a gauche, qu'attendez-vous a droite ?"
- "Voyez-vous la difference entre une piece liee et une preuve ?"
- "Que doit faire le bouton Ajouter une preuve ?"
- "Le bouton Preparer une relance doit-il envoyer un message ou seulement le
  preparer ?"
- "Que voulez-vous retrouver dans l'historique pour passer le dossier a un autre
  membre du conseil syndical ?"
- "Avant d'exporter, voulez-vous savoir qui peut lire l'extrait ?"

### Phrases d'acceptation utilisateur pour le Registre

- "Je peux choisir une decision votee et voir ce qui reste a faire."
- "Je vois qui suit l'action et avant quand."
- "Je vois la preuve attendue avant de preparer une relance."
- "Je distingue une piece utile d'une preuve verifiee."
- "Je sais si la fiche peut rester au conseil syndical ou etre partagee plus
  largement."
- "Je retrouve la derniere relance sans chercher ailleurs."
- "Je peux transmettre le sujet a un autre membre avec l'historique."

### No-go utilisateur Registre

- Une decision ouverte n'affiche pas la preuve attendue.
- Un bouton promet un envoi alors que seul un brouillon est prepare.
- Une piece liee est presentee comme preuve sans verification.
- Un export ne dit pas son public de lecture.
- Les codes P1/P2 ou les mots internes apparaissent seuls.
- Une ligne n'a ni prochaine action ni historique.

## Challenge Cycle suivant Controle comptes `/comptes`

Question utilisateur centrale:

- "Avant l'assemblee generale, qu'est-ce que je dois comprendre ou demander au
  syndic sur les comptes ?"

Attentes au clic:

- Clic sur "a traiter avant l'AG": voir les points qui bloquent vraiment la
  preparation.
- Clic sur "a confirmer": voir les points utiles mais moins bloquants.
- Clic sur "OK avec preuve": voir les lignes que je peux expliquer car une
  piece est rattachee.
- Clic sur une categorie: ouvrir un detail avec preuves, pieces manquantes et
  questions syndic.
- Clic sur "Questions au syndic": obtenir des questions pretes a copier, avec
  contexte et preuve attendue.
- Clic sur "Exporter rapport": preparer un support pour le conseil syndical ou
  l'AG, avec les prudences de partage.

Libelles a surveiller:

- "Postes analyses" peut devenir "lignes de comptes regardees".
- "Factures rapprochees" peut devenir "factures retrouvees".
- "Anomalie" peut devenir "point a expliquer" quand ce n'est pas prouve.
- "P1 prioritaire" peut devenir "a traiter avant l'AG".
- "P2 a confirmer" peut rester si la phrase explique "a confirmer".

Phrases d'acceptation utilisateur:

- "Je sais quels points comptables demander au syndic avant l'AG."
- "Je vois la difference entre a traiter, a confirmer et OK avec preuve."
- "Je peux ouvrir une ligne et comprendre la question a poser."
- "Je ne conclus pas trop vite: si la preuve manque, la page le dit."
- "Je peux expliquer les comptes sans me faire passer pour comptable."

## Go / no-go utilisateur

GO Cockpit `/` pour test utilisateur manuel: oui, a condition de verifier en
session que chaque carte et chaque ligne mene a une action comprehensible.

GO Registre `/actions`: conditionnel. L'intention est bonne, mais les libelles
doivent etre relus avec les phrases novice ci-dessus avant de figer la livraison.

GO Controle comptes `/comptes`: pas encore. L'image doit etre testee avec la
question "quelle demande au syndic puis-je preparer ?" avant developpement
complet.
