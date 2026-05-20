# Documentation noyau vs documentation d'instance

Ce document fixe la frontiere entre le repo produit CoproScope et les contenus propres a une copropriete.

## Principe

CoproScope separe trois espaces:

- le noyau produit: code, schemas, formats, tests et documentation generique;
- les instances locales: configuration, documents, registres et sorties d'une copropriete donnee;
- le vault collaboratif: historique chiffre, signe et synchronisable d'une instance.

Le repo noyau doit rester publiable et reutilisable. Une instance peut etre sensible meme quand elle ne contient que des notes de travail.

## Autorise dans le noyau

- Specifications generiques de format, API, CLI, vault, plugins et securite.
- Documentation produit et technique sans faits reels identifiants.
- Exemples synthetiques sous `examples/synthetic_copro`.
- Tests unitaires et donnees de test fictives.
- Configurations par defaut, schemas JSON, templates generiques.
- Notes d'architecture sur la separation public/prive.

## Interdit dans le noyau

- Documents reels de copropriete.
- Noms, adresses, lots, coproprietaires, fournisseurs ou montants issus d'une instance reelle.
- Notes de conseil syndical, decisions, preuves, relances ou historiques propres a une instance.
- Cartes de pseudonymisation, correspondances, secrets, jetons, cles, exports prives.
- Caches OCR, indexes locaux, bases SQLite reconstruites, blobs dechiffres.
- Worktrees agents, `.venv`, `.git` de copies, exports temporaires.

## Autorise dans une instance ou un vault

- Documents et preuves de l'instance.
- Commentaires, points concrets, actions, statuts, decisions de diffusion.
- Historique signe et pieces justificatives chiffrees.
- Journaux locaux et diagnostics non publies.
- Exports derives, biffes ou diffusables selon politique d'acces.

## Regle de documentation

- Une documentation noyau decrit un comportement reutilisable.
- Une documentation d'instance decrit un cas reel, une decision locale ou une preuve.
- En cas de doute, placer le contenu hors repo noyau.

## Consequence pour les batchs

Les scripts de transition vivent dans le repo car ils sont generiques. Leurs rapports vivent hors repo dans `_transition_reports` car ils peuvent contenir des chemins prives et l'etat local de la machine.
