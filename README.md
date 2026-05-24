# CoproScope

> Rendre la copropriete lisible pour celles et ceux qui la subissent, la financent et doivent parfois la defendre.

CoproScope est un projet local-first pour outiller des coproprietaires novices, des collectifs d'habitants et les institutions qui ont interet a ce qu'ils soient mieux armes. L'objectif n'est pas de leur demander de devenir experts, ni de leur faire ouvrir un terminal. L'objectif est de transformer un dossier opaque en parcours clair: quoi regarder, quelle preuve existe, quelle action est possible, que peut-on partager sans risque.

Ce n'est pas un extranet de syndic. Ce n'est pas une comptabilite officielle. Ce n'est pas un chatbot qui decide. C'est une couche **preuve + action + memoire** qui doit aider a comprendre, verifier, relancer, transmettre et expliquer.

![Concept cockpit coproprietaires](./docs/assets/etude-utilisateurs/cockpit-conseil-syndical.png)

## Le Public

### Coproprietaires Novices

Le produit doit d'abord parler a quelqu'un qui ne sait pas encore lire une convocation d'assemblee generale, un etat de depenses, un contrat de syndic ou une relance technique.

Il doit repondre sans jargon a quatre questions:

1. Qu'est-ce qui demande mon attention ?
2. Quelle preuve avons-nous ?
3. Quelle action est possible maintenant ?
4. Que peut-on partager, avec qui, et sous quelle forme ?

### Institutions Et Acteurs D'Accompagnement

CoproScope doit aussi etre lisible par les acteurs qui ont interet a ce que les coproprietaires soient mieux outilles: collectivites, associations, observatoires, dispositifs d'accompagnement, acteurs de l'habitat, mediation, prevention des coproprietes fragiles.

Pour eux, l'interet n'est pas le code. L'interet est de disposer d'un cadre reproductible pour rendre une situation plus comprehensible, mieux prouvee, moins dependante d'une seule personne et plus facile a transmettre.

### Conseil Syndical

Le conseil syndical reste un relais d'usage naturel, surtout quand il existe et qu'il porte les demandes, les controles et la passation. Mais il n'est pas la cible unique. Le produit doit rester comprehensible par un coproprietaire qui n'a jamais ete elu.

## Ce Que L'UX Doit Faire

L'enquete utilisateur a clarifie un point simple: le probleme n'est pas seulement de stocker des documents. Le probleme est de relier une piece, une demande, une decision, une depense, une preuve, une action et une restitution diffusable.

L'interface doit donc rendre visibles:

| Moment | Ce que l'utilisateur doit comprendre |
|---|---|
| Arrivee | Les sujets prioritaires, sans devoir fouiller le dossier. |
| Piece ou document | Pourquoi c'est utile, ce que cela prouve, ce qui manque. |
| Demande au syndic | Ce qui a ete demande, depuis quand, avec quelle suite attendue. |
| Comptes | Les questions a poser, sans pretendre remplacer la comptabilite officielle. |
| AG | Les decisions, actions et preuves a suivre apres le vote. |
| Diffusion | Ce qui est partageable, restreint, biffe ou a garder local. |
| Passation | Ce que le prochain collectif doit pouvoir reprendre sans repartir de zero. |

## Concepts D'Interface

Les visuels suivants sont des directions UX issues de l'enquete et des cycles de conception. Ils servent a guider le produit; ils ne doivent pas masquer la maturite reelle.

### Cockpit D'Attention

Une vue qui montre les retards, pieces manquantes, echeances, risques et prochaines actions.

![Cockpit d'attention coproprietaire](./docs/assets/etude-utilisateurs/cockpit-conseil-syndical.png)

### Decisions, Actions, Preuves

Une decision d'assemblee generale ne doit pas rester un texte archive: elle doit devenir une action suivie, reliee aux preuves.

![Registre decisions actions preuves](./docs/assets/etude-utilisateurs/registre-decisions-actions-preuves.png)

### Controle Des Comptes Guide

Le controle comptable doit produire des questions comprehensibles, pas seulement des tableaux.

![Controle des comptes guide](./docs/assets/etude-utilisateurs/controle-comptes-guide.png)

### Memoire De Copropriete

La memoire de l'immeuble doit survivre aux changements de personnes, de comptes et de mandats.

![Memoire de copropriete](./docs/assets/etude-utilisateurs/memoire-copropriete.png)

## Maturite Reelle

| Bloc | Etat | Ce que cela veut dire |
|---|---|---|
| Interface locale | V0 utile | Des vues existent deja pour cockpit, actions, comptes, demandes, pieces, passation et documents. |
| Donnees de demo | Stable | L'instance `examples/synthetic_copro` est fictive et sert aux tests publics. |
| Documents | Exploitable | Inventaire, hash, extraction, classement, completude et preuves documentaires. |
| Confidentialite | Socle present | Detection de signaux sensibles, file de revue, biffage ou separation des sorties. |
| Demandes | En consolidation | Suivi des demandes, relances, pieces attendues et traces d'action. |
| Comptes | Amorce forte | Rapprochements et controles candidats, a rendre toujours plus pedagogiques. |
| AG et decisions | Amorce utile | Decisions, actions et preuves commencent a etre reliees. |
| Passation et memoire | En structuration | Le cap est clair; l'experience complete reste a construire. |
| Travaux, contrats, syntheses diffusables | A epaissir | Besoins identifies, modules encore incomplets. |

## Transparence

- CoproScope travaille d'abord en local; rien n'est publie automatiquement.
- Ce depot public ne contient pas de documents reels de copropriete.
- Les exemples sont fictifs ou synthetiques.
- Un export est une copie derivee, pas la source de verite.
- Le masquage reduit le risque, mais ne remplace pas une validation humaine.
- Les analyses doivent citer leurs sources et rester verifiables.
- Si le doute subsiste, on garde hors diffusion publique.

## Lire Ensuite

| Besoin | Lire |
|---|---|
| Comprendre le besoin | [Etude utilisateurs](./docs/etude_utilisateurs.md) |
| Comprendre la promesse | [Concept et philosophie](./docs/concept_et_philosophie.md) |
| Voir ce qui est livre | [Etat du developpement](./docs/etat_du_developpement.md) |
| Naviguer la doc | [Documentation CoproScope](./docs/README.md) |
| Comprendre la frontiere public/prive | [Documentation noyau vs instance](./docs/documentation_noyau_vs_instance.md) |
| Publier sans fuite | [Politique de partage GitHub](./docs/github_sharing.md) |

## Public Averti

Le CLI, les tests et les commandes de reconstruction sont utiles pour developper, auditer, integrer ou lancer une demo locale. Ils ne sont pas le parcours attendu d'un coproprietaire novice.

Pour installer et lancer techniquement CoproScope, lire [server/README.md](./server/README.md).

## Structure Du Depot

- [server/](./server): code produit, interface locale, CLI, configs, templates et tests.
- [docs/](./docs): vision produit, UX, architecture, confidentialite et references.
- [examples/synthetic_copro/](./examples/synthetic_copro): instance publique fictive pour tests et demonstration.

Les donnees reelles de copropriete, secrets, exports OCR prives, journaux locaux, cartes de biffage et sorties generees n'ont pas leur place dans ce depot public.
