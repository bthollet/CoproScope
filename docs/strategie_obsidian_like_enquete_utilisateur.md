# Strategie Obsidian-like centree enquete utilisateur

Date de reference : 2026-05-20

## Intention

Cette note relie deux constats deja presents dans la documentation :

- l'enquete utilisateur montre que les conseils syndicaux ont besoin d'un outil
  de **preuve + action + memoire**, pas seulement d'un stockage documentaire ;
- la transition vault montre qu'une strategie locale, signee et synchronisable
  peut donner a CoproScope une base de confiance durable, a la maniere
  d'Obsidian, sans copier Obsidian ni embarquer son moteur.

La priorite produit est donc de construire un compagnon de travail local-first
pour conseil syndical : un outil qui aide a voir ce qui demande attention, a
relier chaque sujet aux preuves disponibles, a proposer l'action legitime
suivante et a produire une restitution diffusable sans exposer de donnees
sensibles.

## Strategie en trois horizons

### Horizon 1 - Testable maintenant

Objectif : rendre la promesse CoproScope testable par un conseil syndical, meme
sur donnees synthetiques ou corpus limite.

Decisions :

- partir des parcours critiques de l'enquete : controler les comptes avant AG,
  transformer un PV d'AG en plan d'action, gerer un incident, preparer un
  chantier, transmettre la memoire ;
- prototyper les ecrans prioritaires avec des donnees locales et explicables :
  Cockpit, Atelier piece, Registre, Comptes, Memoire ;
- rendre visibles les limites : points candidats, pieces manquantes, documents
  obsoletes, preuves insuffisantes, informations a ne pas diffuser ;
- mesurer la valeur par le nombre de sujets ayant une prochaine action claire,
  une preuve source et un statut comprehensible.

Livrables attendus :

- un cockpit conseil syndical qui trie les sujets par urgence et risque ;
- une vue DocOps actionnable : pieces presentes, manquantes, obsoletes, a
  demander ;
- un depot de document guide qui rattache la piece a un sujet, une preuve ou
  une demande sans exposer l'original ;
- un atelier PDF/image permettant de poser commentaires, points, actions et
  preuves sous forme d'annotations separees du fichier source ;
- un controle comptes guide qui transforme les anomalies en questions au
  syndic ;
- une boite de demandes multi-canaux, car les coproprietaires n'arrivent pas
  tous par le meme chemin ;
- un registre decision -> action -> preuve minimal ;
- une memoire de copropriete exportable pour passation.

### Horizon 2 - Produit V1

Objectif : faire de CoproScope un produit local-first fiable, utilisable par des
conseils syndicaux non techniciens et verifiable par des contributeurs.

Decisions :

- le vault devient la source de verite : blobs chiffres, evenements signes,
  historique append-only, snapshots et index reconstruisibles ;
- la sync reste un transport, jamais une autorite metier ;
- le vault doit resister a l'accaparement : plusieurs copies autorisees,
  aucun administrateur unique, verification des trous et reconstruction par un
  coproprietaire lecteur pour tout le corpus qui lui est ouvert ;
- une meme application locale peut ouvrir plusieurs coffres de copro separes,
  comme plusieurs vaults Obsidian, pour les personnes qui ont plusieurs biens
  ou plusieurs mandats ;
- les gouvernances complexes restent une recherche separee : syndicat
  primaire/secondaire, ASL, union, perimetres croises et droits partages ;
- l'archive complete doit pouvoir etre telechargee par un coproprietaire :
  les parties ouvertes se reconstruisent, les parties restreintes restent
  chiffrees mais verifiables par hash, presence et decision de restriction ;
- les cles critiques doivent avoir des filets de secours : quorum,
  gardiens d'archive, parts inutilisables seules, rotation et ceremonie de
  recuperation signee en cas de defaillance du CS ;
- les corrections et conflits sont des evenements explicites, pas des
  reecritures silencieuses ;
- les objets noyau doivent couvrir les primitives les plus frequentes :
  document, piece, point, action, decision, preuve, depense, export, statut,
  diffusion, demande, annotation, journal d'action, membre, commission ;
- l'import et la migration deviennent des parcours produit : Drive vers local,
  local vers vault, verification, reprise relancable, rapport de ce qui a ete
  importe ou ignore.

Livrables attendus :

- `vault init`, `vault import`, `vault status`, `vault verify`, `vault snapshot`
  comme socle produit visible ;
- reconstruction locale SQLite depuis l'historique signe ;
- affichage de l'historique d'un document, d'une action, d'un point et d'un
  export ;
- affichage des comptes utilisateurs, roles copro/CS, commissions thematiques,
  referents et productions ;
- preparation AG et contentieux comme dossiers probatoires restreints quand
  necessaire ;
- rapport de survivabilite du vault : replicas connus, snapshots, blobs
  manquants, cles de secours, risques de capture et capacite de reconstruction
  coproprietaire ;
- experience coproprietaire `telecharger/verifier/reconstruire`: l'utilisateur
  conserve l'archive complete, ouvre ce qui lui est permis, et voit les zones
  chiffrees sans pouvoir les lire ;
- indicateurs centraux de pilotage : consommations, entretien, investissements,
  espaces verts, travaux, gouvernance, demandes et risques, toujours relies a
  une preuve, une periode et une prochaine action ;
- accessibilite et langage novice : infobulles, registre de vocabulaire,
  parcours guides et vues avancees separees ;
- gestion visible des conflits, signatures invalides, auteurs inconnus et
  evenements ignores ;
- exports sobres pour AG, passation et diffusion controlee.

### Horizon 3 - Ecosysteme plugin signe

Objectif : etendre CoproScope sans diluer le noyau de confiance.

Decisions :

- les traitements lourds deviennent des plugins officiels signes : DocOps,
  ComptaScope, PrivacyOps, BiffageOps, DocAI/OCR, Evidence/Exports ;
- un plugin n'est jamais synchronise comme executable dans le vault ;
- le vault historise seulement les references verifiables : manifeste signe,
  version, permissions accordees, hash d'entrees, hash de sorties, evenements
  produits ;
- aucune permission n'est implicite, et toute activation est historisee ;
- la revocation bloque les executions futures sans effacer les resultats deja
  signes.

Livrables attendus :

- manifeste V1 signe et verifiable ;
- permissions explicites, compatibles avec un usage local-first ;
- journal d'execution plugin consultable depuis l'UI ;
- politique de revocation et compatibilite visible ;
- pas de plugin communautaire avant stabilisation de la chaine de confiance.

## Lecons Obsidian traduites en decisions CoproScope

| Lecon Obsidian | Decision CoproScope |
|---|---|
| Local-first d'abord | L'app travaille dans une copie locale. Le dossier sync transporte un vault chiffre, pas un etat applicatif en clair. |
| Sync comme transport | Le cloud ne decide rien : il transporte blobs, evenements et snapshots. L'etat metier est reconstruit localement. |
| Historique natif | Chaque changement important est un evenement signe append-only. Les corrections, suppressions metier et resolutions de conflit sont de nouveaux evenements. |
| File recovery et sync history | La suppression malveillante doit etre detectee et reversible par reconstruction. Un coproprietaire autorise doit pouvoir conserver une copie reconstructible de l'information collective. |
| Primitives noyau vs plugins | Les objets frequents et probatoires restent dans le noyau. Les traitements couteux ou specialises deviennent des plugins officiels signes. |
| Importer/migration comme produit | La migration Drive -> local -> vault doit etre relancable, auditable, explicable et rassurante pour des benevoles. |
| Plugins puissants mais risqués | Un plugin doit etre signe, permissionne, compatible, revocable et historise. Pas d'auto-update silencieux. |
| Bases/Dataview devenus coeur | Les tableaux universels ne restent pas plugins : demandes, actions, AG, contentieux, commissions et action logs deviennent des objets noyau. |
| Plusieurs vaults | Le multi-copro est d'abord un switcher de coffres separes, pas une base commune multi-tenant. |
| Ecosysteme de plugins | Une veille open source continue identifie ce qui merite un plugin officiel, mais le noyau reste petit et verifiable. |
| Annotations comme couche au-dessus des fichiers | Les PDF restent immuables ; commentaires, ancres, points et actions sont des evenements separes, synchronisables et verifiables. |

## Priorite interface

### 1. Cockpit

Role : donner au conseil syndical une vue de travail quotidienne.

Il doit repondre a quatre questions : qu'est-ce qui demande attention, quelle
preuve existe, quelle action est legitime maintenant, que peut-on partager.

Priorites :

- sujets a traiter ;
- pieces manquantes ou obsoletes ;
- demandes syndic avec echeances ;
- comptes et anomalies prioritaires ;
- confidentialite, biffage et documents diffusables.

### 2. Atelier piece

Role : transformer une piece documentaire en objet de travail.

L'atelier piece doit relier un document a sa classification, ses versions, ses
preuves, ses liens metier, son statut de diffusion et son historique. C'est la
surface ou CoproScope montre qu'il ne se contente pas de stocker.

Priorites :

- source, hash, version et statut de verification ;
- type de piece et utilite metier ;
- liens vers decision, action, depense, incident, travaux ou contrat ;
- risques de diffusion et besoin de biffage ;
- historique signe et resultats plugins.

### 3. Registre

Role : combler l'angle mort du marche : decision -> action -> document ->
depense -> preuve -> restitution.

Priorites :

- resolutions AG transformees en actions suivies ;
- statuts, echeances, responsables et preuves ;
- demandes au syndic et relances ;
- corrections et conflits visibles ;
- vue passation des sujets ouverts.

### 4. Comptes

Role : rendre ComptaScope probatoire mais pedagogique.

Le controle ne doit pas pretendre juger definitivement. Il doit preparer les
bonnes questions, classer les risques et produire une restitution exploitable
avant AG.

Priorites :

- statuts `OK`, `P2`, `P1` lisibles ;
- rapprochements et anomalies cites a leurs sources ;
- questions au syndic ;
- rapport AG ;
- liens vers factures, budgets, contrats et decisions.

### 5. Memoire

Role : rendre la passation possible quand les benevoles changent ou fatiguent.

La memoire de copropriete n'est pas une archive morte. C'est un pack vivant :
sujets ouverts, decisions importantes, risques, acces, calendrier, preuves et
documents diffusables.

Priorites :

- dossier nouveau conseil syndical ;
- ligne du temps des decisions et actions ;
- sujets ouverts et risques ;
- documents clefs avec statut de diffusion ;
- export local sobre, partageable apres controle.

## Paris a ne pas faire maintenant

Ces paris peuvent etre seduisants, mais ils detournent CoproScope de la valeur
testable issue de l'enquete utilisateur.

| Pari | Pourquoi le reporter |
|---|---|
| SaaS multi-tenant | Trop de risque donnees, securite et exploitation avant stabilisation du vault local. |
| Application mobile native | Utile plus tard, mais les objets metier et le cockpit doivent d'abord etre stabilises. |
| Plugin communautaire ouvert | Surface de risque trop grande tant que signature, permissions, compatibilite et revocation ne sont pas eprouvees. |
| Auto-update silencieux des plugins | Incompatible avec une chaine probatoire lisible. |
| Chatbot IA autonome | Risque de sur-promesse. L'IA doit rester citee, incertaine et validee humainement. |
| Vote electronique complet | Le besoin differenciant est le suivi des suites d'AG, pas la concurrence frontale avec les outils de vote. |
| Reseau social de coproprietaires | L'enquete pointe l'action, la preuve et la memoire, pas la conversation generale. |
| Jumeau numerique 3D | Hors cap court terme et peu lie aux douleurs prioritaires. |
| Marketplace de plugins | Aucune valeur avant un noyau stable, des contrats d'evenements clairs et une politique de revocation. |
| Sync temps reel complexe | Le besoin court terme est une sync fiable, verifiable et comprehensible, pas une collaboration instantanee. |

## Ordre de developpement conseille

1. Valider les cinq interfaces prioritaires sur corpus local ou synthetique.
2. Stabiliser les objets noyau : document, piece, point, action, decision,
   preuve, depense, export, diffusion.
3. Relier le cockpit aux preuves, statuts et prochaines actions.
4. Faire du registre decision-action-preuve la colonne vertebrale des parcours
   AG, incidents, travaux et passation.
5. Industrialiser le vault : init, import, status, verify, snapshot.
6. Ajouter les plugins officiels seulement quand leurs entrees, sorties et
   evenements sont verifiables par le noyau.

## Critere de coherence

Une fonctionnalite future merite d'entrer dans CoproScope si elle renforce au
moins une de ces promesses :

- rendre une preuve plus retrouvable ou plus verifiable ;
- transformer un fait en action legitime ;
- securiser une diffusion ;
- transmettre la memoire du conseil syndical ;
- conserver l'historique sans dependance a un service central.

Dans le doute, privilegier le parcours utilisateur observe sur la sophistication
technique. La strategie Obsidian-like n'est pas une fin en soi : elle sert a
donner aux conseils syndicaux une base locale, durable et verifiable pour agir.
