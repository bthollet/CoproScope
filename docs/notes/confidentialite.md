# Confidentialité : ce qui reste chez vous

Un dossier de copropriété contient des noms, des adresses, des montants, des
litiges. CoproScope est conçu pour que ces données **restent sur l'ordinateur
de la personne qui les lit**.

## Ce qui est vrai aujourd'hui

- **L'interface travaille sur votre poste.** Elle ne crée pas de compte et ne
  lance aucune synchronisation. Des commandes expérimentales d'envoi vers Google
  Drive existent en ligne de commande (`coprocs drive …`) : elles demandent un
  module que l'installation proposée n'inclut pas, et une connexion à un compte
  Google. Installées et lancées, elles envoient réellement.
- **La chaîne n'écrit pas dans les documents d'origine.** Ce que CoproScope
  calcule vit à côté, dans des dossiers de travail que l'on peut effacer et
  reconstruire. C'est une règle du code, pas un verrou : rien, dans le système,
  n'interdit l'écriture dans le dossier source.
- **Une copropriété, un dossier.** Chaque copropriété a son propre dossier
  d'instance, en dehors du code. Aucun dossier de copropriété réelle n'entre dans
  le dépôt ; le seul dossier d'instance versionné est l'exemple fictif des tests.
- **La démonstration est inventée.** La démo en ligne et les captures du dépôt
  viennent d'une copropriété entièrement fictive, fabriquée par un
  générateur ([Démo](demo.md)). Les tests automatiques utilisent un autre jeu
  fictif, dans `examples/synthetic_copro`.
- **Un contrôle avant chaque envoi vers GitHub, pour qui l'active.** Un crochet
  `pre-push`, à activer ([développer](developper.md)), lance
  [`tools/verifier_avant_push.py`](../../tools/verifier_avant_push.py). Il lit
  les objets que le push enverrait réellement (pas seulement l'arbre courant) et
  refuse le push si un fichier texte, ou le nom d'un fichier, porte un terme de la
  liste interdite, qui vit hors du dépôt. Lancé sur l'arbre suivi, il cherche aussi
  les adresses postales plausibles. **Il ne lit ni les images ni les PDF, et ne
  cherche pas les chemins locaux.**

## Ce qui n'est pas promis

- **Le masquage automatique n'est pas une garantie.** Des modules de repérage
  des noms et de préparation au masquage existent, mais ils ne sont pas
  présentés comme fiables : un document partagé doit être relu par un humain.
- **La synchronisation Drive n'a pas d'écran.** Le transport chiffré vers Drive
  reste un concept ([synchronisation chiffrée](concept-synchro-drive.md)) ; seules
  les commandes expérimentales citées plus haut existent.
- **Le partage à plusieurs n'existe pas encore.** Voir
  [multi-utilisateur et coffre partagé](concept-multi-utilisateur-coffre-partage.md).

## Ce qu'il reste à surveiller

Le contrôle avant push cherche des termes et des **formes** connues. Une donnée
personnelle qui n'est pas dans la liste et n'a pas la forme d'une adresse peut
passer, comme tout ce que porte une image ou un PDF. Le dépôt a d'abord été un outil
de travail privé, développé sur de vrais dossiers. Avant sa publication, les noms
qu'il citait ont été remplacés par des noms d'emprunt. La version sur GitHub est un
instantané publié sans son historique : les versions de travail précédentes,
conservées sur le poste de l'auteur, n'y figurent pas.

Restent visibles, et c'est un choix connu : le prénom de l'auteur, dans de nombreux
fichiers (code, tests, documents de travail), et des chemins de son poste de
développement dans une cinquantaine de documents et de tests. Le contrôle avant push
saute aussi, sans le signaler, un fichier texte qui n'est pas encodé en UTF-8.

## Notes liées

- [Carte des notes](carte.md)
- [Démo](demo.md)
- [Diffusion et masquage (concept)](concept-diffusion-masquage.md)
- [Synchronisation chiffrée (concept)](concept-synchro-drive.md)
- [Architecture](architecture.md)
