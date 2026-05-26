# Concept et philosophie

## Idee centrale

CoproScope est un outil local-first pour rendre la copropriete lisible et actionnable par des coproprietaires non experts, des collectifs d'habitants et les acteurs qui les accompagnent.

Il part d'un constat simple : dans beaucoup de coproprietes, l'information existe deja, mais elle est dispersee, fragile, peu tracable, peu actionnable et parfois trop sensible pour etre partagee telle quelle.

Le projet reconstruit une chaine :

1. identifier les pieces ;
2. proteger les originaux ;
3. qualifier la confidentialite ;
4. biffer ou agreger avant diffusion si necessaire ;
5. relier documents, demandes, decisions, factures, comptes et constats ;
6. produire des sorties relisibles ;
7. ne publier que le genericisable.

## Ce que l'etude utilisateurs a clarifie

L'etude documentaire UX/SHS montre que le besoin n'est pas seulement documentaire.

L'enquete partait beaucoup des conseils syndicaux, parce qu'ils portent souvent les demandes, les controles et la passation. Mais le besoin produit depasse ce seul relais: il faut rendre les chaines de preuve comprehensibles pour des coproprietaires novices et pour les institutions qui les accompagnent.

Les utilisateurs ont besoin de :

- preuve : savoir d'ou vient l'information ;
- action : savoir quoi faire maintenant ;
- memoire : ne pas perdre l'historique ;
- limite : savoir ce qui releve ou non de leur role, de leur mandat ou de leur droit d'acces ;
- diffusion : expliquer sans exposer de donnees sensibles.

CoproScope doit donc eviter deux ecueils :

- devenir une simple arborescence de fichiers ;
- devenir un outil d'audit si expert qu'il surcharge les benevoles.

## La promesse en termes simples

Quand CoproScope fonctionne bien, un coproprietaire ou un collectif peut dire :

- on sait ce qu'on a ;
- on sait ce qu'il manque ;
- on sait ce qui est sensible ;
- on sait ce qu'on peut diffuser ;
- on sait quelle demande ou decision rattacher a quelle preuve ;
- on sait quels points traiter avant l'AG ;
- on peut transmettre le dossier au prochain relais sans repartir de zero.

## Ce que CoproScope est

- un outil local-first ;
- un cockpit documentaire et operationnel ;
- un assistant de controle et de comprehension pour coproprietaires et collectifs ;
- un systeme de registres et preuves ;
- une aide a la restitution propre ;
- une base open source genericisable.

## Ce que CoproScope n'est pas

- pas un syndic ;
- pas une comptabilite officielle ;
- pas un SaaS multi-tenant ;
- pas un extranet de plus ;
- pas un reseau social de copropriete ;
- pas un chatbot qui decide sans sources ;
- pas un outil qui publie des documents reels dans GitHub.

## Principes de conception

### 1. Les originaux ne se touchent pas

Les documents bruts restent en lecture seule. Toute transformation passe par les registres, sorties, journaux, versions biffees ou artefacts locaux.

### 2. La traçabilité des traitements faits par l'appli prime

Chaque automatisation utile doit laisser une trace : hash, registre, source, methode, statut, rapport, action attendue.

### 3. Le prive reste prive

Les instances reelles restent hors github. Le github recoit le code, les schemas, les exemples synthetiques, les methodes et les formes genericisees.

### 4. La confidentialite est une fonction produit

PrivacyOps et BiffageOps ne sont pas des details techniques. Ils rendent possible la diffusion prudente : screening, college d'acces, biffage, pseudonymisation, version diffusable à tous les copropriétaires.

### 5. Le conseil syndical est un relais, pas le centre unique

Un CS peut etre vigie, pompier, batisseur, expert, fatigue ou captif du syndic. Mais une copropriete peut aussi avoir peu ou pas de relais actif. CoproScope doit donc rester lisible pour des coproprietaires novices et pour les institutions qui veulent les accompagner.

### 6. IA et Cloud: maximiser les traitements locaux, faciliter le traitement humain, sécuriser le recours au cloud

Les aides IA peuvent accelerer l'extraction, la synthese ou la revue. Elles ne doivent pas effacer la source, le doute, la validation humaine ou la politique de confidentialite. CoproScope cherche à maximiser les traitements sans IA :
 - CoproScope est conçu pour fonctionner totalement hors ligne, en offrant la possibilité de recourir à des services tiers Cloud ou IA
 - Tous les traitements (extraction des données des documents, etc.) sont faits localement

#### 6.1 IA: aucun envoi de données par CoproScope, et fiabiliser le recours volontaire à l'IA pour les utilisateurs qui souhaitent y recourir
 - En cas d'échec des outils automatiques, des outils IA locale peuvent être déclencher (ex: si la reconnaissance de texte classique n'a pas marché, ou pour reconnaitre les différentes parties d'une facture)
 - CoproScope crée une version anonymisée de toutes les données, dans un format texte brut, qui permet d'éviter les fuites de données par des copropriétaires qui auraient recours à l'IA pour comprendre ce qu'il se passe
 - Il propose également des trames pour guider l'IA dans la production d'analyses pertinentes

#### 6.2 Cloud: faciliter le travail à plusieurs, tout en évitant à la fois les fuites externe et l'accaparement interne des données
L'enquête utilisateur met en évidence la nécessité de collaborer de manière efficace sans occulter le risque de captation de l'information par une partie de la gouvernance, parfois volontaire, parfois involontaire. CoprosCope veut permettre la décentralisation de l'information et la collaboration sur les dossiers en permettant de synchroniser en temps réél toute l'information dans un dossier crypté.

### 7. L'interface vient apres les objets metier

Pas d'application web decorative. L'interface locale est le produit pour les non-techniciens; les registres, statuts et rapports ne valent que s'ils nourrissent une experience comprehensible.

## Pourquoi c'est mobilisateur

Chaque couche utile rend le travail collectif un peu moins solitaire :

- une piece retrouvee evite une relance floue ;
- un biffage evite une diffusion risquee ;
- un rapprochement comptable produit une vraie question ;
- une resolution suivie evite l'oubli post-AG ;
- une memoire de copropriete evite de repartir de zero.
