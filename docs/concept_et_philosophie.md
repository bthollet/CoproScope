# Concept et philosophie

## Idee centrale

CoproScope est un cockpit documentaire et operationnel pour conseil syndical. Il part d'un constat simple: dans beaucoup de coproprietes, l'information existe, mais elle est dispersee, inverifiable, difficile a relier et encore plus difficile a transformer en action propre.

Le produit n'essaie pas de remplacer d'un coup tous les outils. Il construit plutot une colonne vertebrale:

1. des documents bruts identifies et hashes ;
2. des registres explicites ;
3. des diligences rattachees a des preuves ;
4. des sorties diffusables qui restent propres et partageables ;
5. un noyau logiciel generique separe des cas reels.

## A qui cela s'adresse

- conseils syndicaux qui veulent une lecture plus nette de leur fonds documentaire ;
- coproprietaires tres impliques qui ont besoin de relier pieces, demandes, AG et travaux ;
- equipes qui veulent un outillage sobre, local-first, et audit-able.

## Ce que CoproScope n'est pas

- pas un SaaS de gestion locative ;
- pas un coffre-fort magique qui "comprend tout" sans trace ;
- pas une simple arborescence de dossiers ;
- pas une usine a gaz RAG imposee des le depart.

## Principes de conception

### 1. Les originaux ne se touchent pas

Les racines brutes restent en lecture seule. Toute transformation passe par des espaces de staging, de registres ou de sorties.

### 2. La preuve prime

Chaque automatisation doit produire ou enrichir une trace: manifeste, registre, journal d'action, rapport, constat.

### 3. Le prive reste prive

Une instance reelle sert a apprendre et a valider. Le depot public ne recoit que des briques genericisees, propres, documentees et testees.

### 4. La francophonie est une preference structurelle

Quand c'est pertinent, CoproScope privilegie:

- les noms fonctionnels en francais ;
- les documents publics en francais ;
- les sorties diffusables en francais ;
- l'anglais seulement lorsqu'il sert une compatibilite technique, un identifiant ou une integration externe.

### 5. L'outil doit rester operable

Un socle utile vaut mieux qu'une vision totale mais abstraite. CoproScope avance par couches utiles: DocOps, puis SyndicOps, puis AGOps.
