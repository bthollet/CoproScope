# Concept et philosophie

## Idee centrale

CoproScope est un cockpit local-first pour conseil syndical.

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

L'etude UX/SHS montre que le besoin n'est pas seulement documentaire.

Le conseil syndical a besoin de :

- preuve : savoir d'ou vient l'information ;
- action : savoir quoi faire maintenant ;
- memoire : ne pas perdre l'historique ;
- limite : savoir ce qui releve ou non du role CS ;
- diffusion : expliquer sans exposer de donnees sensibles.

CoproScope doit donc eviter deux ecueils :

- devenir une simple arborescence de fichiers ;
- devenir un outil d'audit si expert qu'il surcharge les benevoles.

## La promesse en termes simples

Quand CoproScope fonctionne bien, une equipe peut dire :

- on sait ce qu'on a ;
- on sait ce qu'il manque ;
- on sait ce qui est sensible ;
- on sait ce qu'on peut diffuser ;
- on sait quelle demande ou decision rattacher a quelle preuve ;
- on sait quels points traiter avant l'AG ;
- on peut transmettre le dossier au prochain conseil syndical.

## Ce que CoproScope est

- un outil local-first ;
- un cockpit documentaire et operationnel ;
- un assistant de controle pour conseil syndical ;
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

Les racines brutes restent en lecture seule. Toute transformation passe par les registres, sorties, journaux, versions biffees ou artefacts locaux.

### 2. La preuve prime

Chaque automatisation utile doit laisser une trace : hash, registre, source, methode, statut, rapport, action attendue.

### 3. Le prive reste prive

Les instances reelles restent hors depot. Le depot public recoit le code, les schemas, les exemples synthetiques, les methodes et les formes genericisees.

### 4. La confidentialite est une fonction produit

PrivacyOps et BiffageOps ne sont pas des details techniques. Ils rendent possible la diffusion prudente : screening, college d'acces, biffage, pseudonymisation, version diffusable.

### 5. Le conseil syndical n'est pas un persona unique

Un CS peut etre vigie, pompier, batisseur, expert, fatigue ou captif du syndic. CoproScope doit accepter ces niveaux de maturite.

### 6. L'IA doit rester sous preuve

Les aides IA peuvent accelerer l'extraction, la synthese ou la revue. Elles ne doivent pas effacer la source, le doute, la validation humaine ou la politique de confidentialite.

### 7. L'interface vient apres les objets metier

Pas d'application web prematuree. L'interface locale devient pertinente quand les registres, statuts et rapports sont assez stables.

## Pourquoi c'est mobilisateur

Chaque couche utile rend le travail du conseil syndical un peu moins solitaire :

- une piece retrouvee evite une relance floue ;
- un biffage evite une diffusion risquee ;
- un rapprochement comptable produit une vraie question ;
- une resolution suivie evite l'oubli post-AG ;
- une memoire de copropriete evite de repartir de zero.

