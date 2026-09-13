# Plan d'action — retour de Brice sur la maquette des deux contrôles

Rattachement: `RM-2026-0124`. Chantier: `CH-20260908-1015-RM-2026-0124-retour-maquette-controles`.
Conversation: `CONV-2026-2180`. Date: 2026-09-08.

## D'où vient ce plan

Message vocal de Brice du 2026-09-08, **31 minutes et 48 secondes**, enregistré en
parcourant la maquette « Où cliquer dans les contrôles » publiée la veille. Il commente
les six planches dans l'ordre, écran ouvert.

Transcription locale, aucun envoi réseau: `faster-whisper`, modèle `large-v3-turbo`,
français, filtre de voix actif. Le fichier audio source n'a pas été modifié. Le texte
brut est conservé hors dépôt, dans le scratchpad de session — il contient la voix de
Brice et n'a pas vocation à entrer dans Git.

**Réserve de fidélité.** Une transcription automatique n'est pas une citation certaine.
Les citations de ce document portent leur horodatage pour permettre une réécoute ciblée.
Les passages où Brice hésite à voix haute — il le fait souvent, et c'est précieux — sont
rendus comme des questions ouvertes, pas comme des décisions.

## Ce que Brice valide sans réserve

Trois verdicts nets, qui bornent le travail restant:

- planche 1, le constat mesuré: « **j'ai rien à répondre là-dessus** » `[00:00:10]`;
- planche 4, l'écran d'aujourd'hui: « **rien à rajouter** » `[00:20:47]`;
- planche 5, le geste au bout du filtre: « **rien à rajouter** » `[00:21:54]`;
- planche 2, la cellule qui agit: « **c'est quand même une très bonne base** » `[00:13:50]`.

Le désaccord ne porte donc ni sur le diagnostic, ni sur le principe des verbes, ni sur
l'action de masse. Il porte sur **ce qu'une cellule doit contenir**, sur **ce qu'un
contrôle veut dire**, et sur la page des comptes — dont Brice dit qu'elle « ne paraît pas
mûre du tout » `[00:24:52]`.

## Ce qui tombe, et pourquoi

**Le geste « comparer les deux assertions de seuil » est retiré.** Je l'avais dessiné
comme la réponse à une ambiguïté, puis requalifié en exigence back après le constat C095.
Brice tranche autrement, et sur le fond: « la question des seuils, c'est **le dernier
qu'il faut retenir** [...] la question de l'ambiguïté, elle ne se pose pas. C'est le
dernier vote » `[00:06:31]` à `[00:06:54]`.

Ce n'est pas un désaccord d'interface, c'est une règle de droit que le modèle ignorait.
Conséquence directe: `RM-2026-0086 / C095` change de nature. Il ne s'agit plus d'exposer
la provenance de l'assertion perdante pour la faire arbitrer par un humain, mais
d'**ordonner les délibérations et de retenir la dernière**. À reverser au constat.

## Les axes, avant les lots

Conformément à la règle du dépôt, chaque lot ci-dessous nomme l'**axe** de généralisation,
ce qui reste **invariant** le long de l'axe, et ce que le code fait **hors des valeurs
observées**. Cinq axes traversent tout le retour.

### Axe 1 — Un contrôle nomme une pièce; toute pièce nommée est atteignable

Invariant: si une cellule sait dire « annexe visée », « seuil applicable », « avis du
conseil syndical », alors elle sait quelle pièce elle désigne, et cette désignation est
un chemin. Brice `[00:05:11]`: « si je clique sur le titre de la pièce, **et ça dans
toutes les cellules** — si je clique sur résolution 13.4 ça m'ouvre la résolution, si je
clique sur annexe ça m'ouvre les annexes, si je clique sur seuil applicable ça m'ouvre la
décision du seuil applicable ».

Hors valeurs observées: quand la pièce est désignée mais non identifiée dans le coffre, le
chemin ne disparaît pas — il mène à l'écran d'ancrage (axe 2). Quand elle n'est pas
désignée du tout, la cellule ne montre aucun chemin plutôt qu'un chemin mort.

### Axe 2 — Une pièce logique n'est pas un fichier

Une résolution, une annexe, un devis sont des objets que le dossier désigne; un PDF est un
contenant qui peut en porter plusieurs, ou aucun. Brice `[00:06:11]`: « s'il s'agit de
poser des ancres dans un document PDF qui tient plusieurs pièces ». Et `[00:03:07]`: « si
ça se trouve elle est dans un document à part, ou elle n'a pas été identifiée. Ça veut
dire qu'il faut imaginer une interface pour poser les ancres à la main ».

Invariant: le lien entre un contrôle et sa preuve est une **ancre** — un document, une
position — pas un nom de fichier. Hors valeurs observées: une ancre posée à la main vaut
autant qu'une ancre trouvée par la machine, et elle dit qui l'a posée.

### Axe 3 — Un acte a une vie juridique indépendante de son contenu

Une décision peut être contestée, en instance, annulée par une décision ultérieure, sans
que rien de son texte ne change. Brice `[00:07:04]`: « il peut y avoir des documents ou
des décisions qui sont contestées [...] il faudrait pouvoir tracer le statut des
documents ». Et le cas qui rend l'axe indispensable `[00:07:37]`: « pour le seuil
applicable, ce n'est pas la même AG — il faudrait juste à côté un petit point
d'exclamation cliquable, ou avec une infobulle, qui dit que l'AG où il y a le seuil, elle
est contestée ».

Invariant: **tout contrôle qui s'appuie sur une pièce hérite du doute attaché à cette
pièce**, y compris quand la pièce vient d'une autre assemblée que la ligne affichée.

### Axe 4 — L'exécution a au moins deux dimensions indépendantes

Brice `[00:13:05]`: « qu'est-ce qu'il faut mettre dans cette cellule exécution, parce
qu'il y a l'exécution du point de vue financier — est-ce que l'argent a été enlevé ou pas,
ou une partie — et puis après il y a l'exécution réelle, c'est-à-dire est-ce que les
artisans sont venus, est-ce que le travail est fait, est-ce que ce qui a été livré a été
accepté, ou est-ce qu'il y a une contestation ».

Invariant: l'argent et la chose avancent séparément, et **toutes les combinaisons
existent** — payé non fait, fait non payé, partiellement l'un et l'autre. Hors valeurs
observées: ne jamais déduire l'une de l'autre. Une cellule qui n'affiche qu'un rattachement
de dépense code une modalité, pas l'axe.

### Axe 5 — Une conclusion a un auteur, et l'auteur n'est pas toujours le collectif

Brice `[00:15:34]`: « si moi, conseiller syndical, je tranche quelque chose, est-ce que
c'est mon avis qui est noté, ou est-ce que c'est la base qui considère que c'est tranché ?
Parce que si on commence à être plusieurs personnes, il y a la question de comment on
tranche collectivement. Est-ce que si une personne tranche, ça tranche pour tout le
monde ? Ou pas ? »

Invariant: une trace porte toujours son auteur. Hors valeurs observées: à un seul
utilisateur, les deux niveaux coïncident visuellement mais restent deux champs distincts
en base — sans quoi le passage à plusieurs utilisateurs réécrit l'histoire.

## Les lots

Ordre de dépendance, pas de préférence. **Chaque lot porte son `RM-*`**, alloué en un bloc
contigu `RM-2026-0157` à `RM-2026-0166` sur décision de Brice le 2026-09-08. Le bloc a été
vérifié libre sur toutes les branches locales et dans les deux registres de chacune, puis
annoncé au coordinateur avant écriture — trois mécanismes de collision distincts s'étaient
produits dans la journée, et l'annonce préalable est le seul des trois que la vérification
ne couvrait pas.

### Lot A — Rendre atteignable ce que la cellule nomme déjà  
`RM-2026-0157`

Axe 1. Le moins cher et le plus attendu: 332 citations nomment déjà un document **et une
page** sans y mener.

- Le titre de chaque bulle ouvre la pièce qu'il désigne, à sa position.
- La résolution porte **deux entrées distinctes**, corps du procès-verbal et annexes.
  Brice `[00:01:30]`: « soit vers la résolution elle-même dans le corps du PDF, soit vers
  les annexes. D'ailleurs il pourrait y avoir les deux boutons. »
- **Défaut à corriger d'abord**: « voir le devis retenu, ça a planté » `[00:04:59]`. Un
  geste qui plante est pire qu'un geste absent — il détruit la confiance dans les autres.
  Reproduire, isoler, corriger avant d'en ajouter.

Acceptation: sur l'instance du lot, tout titre de bulle qui désigne une pièce identifiée
ouvre le visualiseur à la bonne position; aucun clic ne produit d'erreur; les titres qui
ne désignent aucune pièce identifiée ne sont pas cliquables.

### Lot B — L'écran d'ancrage manuel  
`RM-2026-0158`

Axe 2. C'est le contenu réel du verbe **Rattacher**, et c'est un écran à part entière, pas
un bouton.

- Ouvrir un document, désigner la page et la zone, déclarer « ceci est l'annexe de la
  résolution 13.4 ».
- Écrire l'ancre dans le magasin de liens, avec son auteur et sa date, sans écraser ce que
  la machine avait lu.
- Le cas qui commande le besoin: la pièce existe, elle est dans un document qui en contient
  d'autres, et personne ne l'a identifiée.

Acceptation: une ancre posée à la main survit à une re-extraction. Deux ancres
contradictoires sur le même couple coexistent et disent qui les affirme.

### Lot C — Le statut juridique des actes et des documents  
`RM-2026-0159`

Axe 3.

- Un acte et un document portent un statut: **non contesté, contesté, en instance, annulé
  par décision ultérieure**. Saisi par un humain; rien ne le déduit.
- Toute cellule qui s'appuie sur une pièce dont l'acte d'origine est contesté porte un
  signal cliquable qui le dit, **y compris quand l'acte vient d'une autre assemblée**.
- Une vue par assemblée dit si l'instance est contestée.

Acceptation: sur une AG marquée contestée, les contrôles d'autres lignes qui s'appuient sur
ses délibérations affichent le signal, et le signal mène à l'acte contesté.

### Lot D — La colonne Exécution, dédoublée  
`RM-2026-0160`

Axe 4. Brice demande explicitement une enquête: « là je ne sais pas comment il faudrait le
traiter, donc il y a peut-être une enquête à faire là-dessus » `[00:13:45]`.

Statuts qu'il propose lui-même `[00:08:25]` à `[00:08:53]`: « en attente d'exécution,
annulé par décision ultérieure, en cours de réalisation, exécuté ». Côté financier, il
énumère `[00:24:00]`: « provisionnées, appelées, tracées en compta, appelées mais pas
payées, payées mais pas appelées ».

Bloc d'enquête d'abord, code ensuite. Le bloc doit rendre: quelles preuves existent pour
l'exécution réelle dans un dossier de copropriété (procès-verbal de réception, facture de
solde, constat), et par quelles pièces elles arrivent.

### Lot E — Le vocabulaire de la conclusion, et ses deux niveaux  
`RM-2026-0161`

Axe 5. **Brice me demande explicitement des propositions**: « il y a deux niveaux, je ne
sais pas comment les traiter, fais-moi des propositions » `[00:18:14]`.

**Ce que je propose.** Ne pas faire une liste de six valeurs dans une seule colonne, mais
**deux champs qui ne fusionnent jamais**:

1. **Mon avis**, propre à chaque personne: `à instruire`, `vérifié`, `réserve`,
   `non conforme`. Toujours attribué, jamais écrasé par quelqu'un d'autre.
2. **Position du conseil**, collective: `sans position`, `position du conseil syndical`.
   Elle ne se déduit d'aucun avis individuel. Elle demande un acte explicite, et elle
   **cite les avis individuels qu'elle consolide**.

Motif: une seule colonne qui porterait les deux fait que le second qui écrit efface le
premier — c'est le défaut numéro un du produit sous une forme neuve. Deux champs répondent
aussi à la question de Brice sur le collectif: **un conseiller qui tranche n'engage que
lui**, et la position du conseil ne bouge que par un geste qui se nomme comme tel.

**Écarté devient non conforme.** Brice `[00:20:09]`: « il faut pouvoir acter une décision
non conforme. Écartée, ça ne veut rien dire. Non conforme. » Et sa nuance juridique, à
conserver telle quelle dans l'écran `[00:19:32]`: passé le délai de deux mois de
contestation, « à part acter la non-conformité [...] il n'y a pas grand-chose à faire,
sauf éventuellement attaquer au nom du syndicat » — « la portée n'est pas évidente ».
L'écran doit donc **acter sans promettre un recours**.

Traces avec noms d'utilisateurs `[00:18:22]`. Un écran ultérieur listera les points non
conformes et leur traitement `[00:19:25]`.

### Lot F — Le cycle de vie d'une demande  
`RM-2026-0162`

Brice `[00:16:19]`: « quand j'ai fait une demande et qu'elle arrive, comment est-ce qu'elle
est réintégrée ? Est-ce qu'il y a genre demande traitée ? Est-ce qu'il y a un rattachement
automatique ? »

Proposition: statuts `à demander`, `demandée le JJ/MM`, `relancée`, `reçue et rattachée`,
`sans réponse à l'échéance`. **Pas de rattachement automatique**: une pièce qui arrive est
*proposée* contre les demandes ouvertes, un humain confirme. Un rattachement automatique
écrirait un lien que personne n'affirme, ce que l'axe 2 interdit.

Deux gestes de plus dans la cellule, demandés à `[00:03:37]` et `[00:04:23]`: **demander au
conseil syndical** — pas seulement au syndic — et **mettre un commentaire**. Motif de
Brice, à garder: l'avis a pu être donné oralement, « c'est border en termes de conformité,
mais dans la pratique peut-être que ça s'est fait comme ça ».

Et le panier `[00:02:30]`: la demande d'une cellule « ajoute à la liste des demandes »
plutôt que de partir seule. La planche 5 le fait au niveau du filtre; il manque au niveau
de la cellule.

### Lot G — Densité et repos de la ligne  
`RM-2026-0163`

Deux demandes de forme, sans dépendance.

- **Le montant quitte sa colonne** et devient une bulle de la colonne Décision `[00:01:56]`:
  « est-ce que la colonne montant, ça ne pourrait pas être une bulle dans la colonne
  décision, vu que chaque ligne a quand même pas mal de hauteur ». Libère une colonne
  entière sur six.
- **La ligne conclue se simplifie** `[00:09:14]`: « une fois qu'on a mis contrôle tracé, il
  faut que la ligne se simplifie, avec tous les petits boutons qui disparaissent et toutes
  les bulles qui deviennent juste une ligne de texte ». C'est la troisième forme de la
  planche 3, appliquée à la ligne entière au lieu de la cellule.

### Lot H — « Devis retenu » est un mauvais nom  
`RM-2026-0164`

Brice `[00:09:42]` à `[00:12:22]`. Deux choses distinctes:

- **Architecture des résolutions.** « Est-ce que c'est résolution 13, choix du devis, et
  13.1, 13.2, 13.3, 13.4, c'est quatre devis ? [...] en général ce qui se passe, c'est
  qu'il y a un vote sur chaque devis, une résolution sur chaque devis. » Axe: le rapport
  entre une résolution et les devis qu'elle met en jeu **varie** — un vote par devis, un
  vote pour plusieurs, aucun devis. Ne pas coder « 13.4 signifie quatre devis ».
- **Le nom et la sémantique.** « Devis associés » plutôt que « devis retenu », ou mieux:
  **présence du devis, oui ou non** — « puisque le devis, il n'est pas obligatoire ». Donc
  une absence de devis n'est pas un manquement, et la cellule ne doit pas la présenter en
  rouge comme une source manquante. Si non: on peut le demander au syndic.

Ce lot corrige une erreur de ma maquette: j'ai compté 89 « devis retenu » comme des pièces
manquantes à réclamer. Sur un contrôle qui n'est pas obligatoire, c'est un faux positif de
masse.

### Lot I — Contrôle des comptes: refonte, pas retouche  
`RM-2026-0165`

Brice `[00:22:41]`: « c'est moins mûr ». `[00:24:52]`: « ça ne me paraît pas mûr du tout,
cette page de compta ». `[00:23:33]`: « il y a peut-être un travail d'enquête sur comment
ça se contrôle, les comptes ».

Ce qu'il donne déjà comme cible, et qui est plus qu'une correction:

- **La colonne Décision passe à gauche de la compta** `[00:23:04]`.
- **Le marché à gauche, l'exécution tout à droite** `[00:27:33]`, « parce que l'un comme
  l'autre peuvent être des clés d'entrée pour créer une ligne ». Le motif est décisif et
  il vaut aussi pour la gouvernance: **on peut avoir des travaux exécutés mais pas
  décidés** `[00:27:02]`. Une ligne peut donc naître d'une dépense sans décision.
- **Entre les deux**, les colonnes qui disent où en est l'argent: payé, appelé, sur quel
  compte — avec la difficulté nommée `[00:28:34]`: « il y a peut-être des choses qui
  peuvent changer de compte un peu après ».
- **L'exécution porte les factures et les preuves de réalisation** `[00:28:12]`.
- **Une facture de gros travaux peut porter plusieurs situations** `[00:22:52]`: « sur des
  gros travaux, il peut y avoir plusieurs avis de situation ». Le rapport facture/dépense
  n'est pas un pour un.
- **Double ligne dépenses et recettes** `[00:28:46]`, parce qu'il y a des prêts et des
  subventions.

Et le constat qui commande la scission des pages `[00:25:02]`: « la manière dont on a pensé
ce qu'on a appelé la gouvernance, ça recouvre quand même pas mal ce qu'il y a marqué dans
la compta, **sauf qu'on n'a pas l'état de paiement au niveau comptable** ».

Bloc d'enquête obligatoire avant tout code, conformément au dépôt: le contrôle des comptes
est une feature transverse et le cadrage manque.

**La frontière entre les deux pages est tranchée, et elle ne passe pas par les colonnes.**
Formulation de `CONV-2026-2172`, dérivée des mots de Brice ci-dessus: la question n'est pas
ce que chaque page affiche, c'est **ce qui a le droit de faire naître une ligne**. La page
des comptes doit pouvoir montrer une ligne qu'aucune décision n'explique — c'est même son
cas le plus intéressant — là où la page des décisions part forcément d'une décision.
**Deux pages qui ne peuplent pas leur table par le même bout ne se recouvrent pas, quelles
que soient leurs colonnes.** L'autre moitié de la réponse est dans la phrase de Brice sur
l'état de paiement: ce que la page des comptes a et que la gouvernance n'aura jamais, c'est
le **payé / appelé**.

Trois de ses phrases réfutent d'avance des conceptions plausibles: **une facture de gros
travaux porte plusieurs situations**, donc « facture = dépense » est faux; **double ligne
dépenses et recettes**, donc une page qui ne sait afficher que des dépenses manque la moitié
du sujet; et **l'imputation peut changer de compte après coup**, donc ce n'est pas une
colonne mais une histoire de versions.

### Lot J — Imputation et clés de répartition  
`RM-2026-0166`

Brice `[00:29:55]` à `[00:31:36]`. **Absentes de la base aujourd'hui**, et il le dit
lui-même: « c'est quelque chose qu'on n'a pas en base aujourd'hui, c'est-à-dire les clés de
répartition et l'imputation ».

Ses exemples, qui sont l'axe même: travaux d'ascenseur → un bâtiment; toiture → un bloc;
jardin → tout le monde; ascenseurs → tout le monde sauf les premiers étages, « puisqu'on a
des ascenseurs en entresol »; eau → indéterminée, avec des dépenses communes qui partent
sur certains compteurs de bâtiments.

Invariant: **la facturation doit correspondre à l'imputation** `[00:31:28]`.

Brice demande explicitement une recherche: « il y a tout un chemin là que moi je ne sais
pas dépatouiller, et sur lequel j'aurais besoin que je fasse des recherches ». Ce lot est
donc une **recherche métier**, pas un lot de développement, et il conditionne le lot I.

## Ce qui reste ouvert, et que je ne tranche pas

- **Le lot D et le lot I demandent une enquête** avant tout code, sur demande explicite de
  Brice. Les ouvrir en développement serait passer outre.
- **Le lot J est une recherche**, et son résultat peut changer le modèle de données.
- **La portée juridique de la non-conformité** au-delà du délai de deux mois: Brice dit
  lui-même « la portée, elle n'est pas évidente ». À faire vérifier à la source, comme
  l'article 21 l'a été le 2026-09-08 — un constat précis peut être faux sur le fond quand
  personne n'a ouvert le texte.
- **Les subventions et prêts en copropriété**: attribués individuellement ou
  collectivement ? Brice: « je ne sais pas bien ». Question de recherche, rattachée au
  lot J.

## Ordre proposé

1. **Lot A — `RM-2026-0157`**, dont la correction du geste qui plante. Le moins cher, le
   plus visible, et il ne dépend de rien.
2. **Lot G — `RM-2026-0163`**, forme pure, sans dépendance.
3. **Lot H — `RM-2026-0164`**, qui retire un faux positif de masse avant qu'il n'entre dans
   un courrier au syndic.
4. **Lot E — `RM-2026-0161`**, qui débloque la colonne que rien ne remplit aujourd'hui.
5. **Lot B — `RM-2026-0158`**, puis **lot F — `RM-2026-0162`** qui s'appuie dessus.
6. **Lot C — `RM-2026-0159`**.
7. **Enquêtes D — `RM-2026-0160` et I — `RM-2026-0165`**, puis **recherche J —
   `RM-2026-0166`**, en parallèle du reste. Aucune ne s'ouvre en développement: Brice les a
   demandées comme enquêtes.

## Traces

- Maquette commentée: canvas « Où cliquer dans les contrôles », publié le 2026-09-07,
  corrigé le 2026-09-08 après relecture.
- Instance de la mesure: `instances/design_interactions_20260907`, jetable, copiée de
  `tilleul_pseudo_exploration_20260907`. Port `8808`, token `design-interactions-8808`.
- Mesures qui fondent le constat, obtenues par comptage dans le document rendu et donc
  indépendantes de la justesse des données: 2 905 objets en forme de carte, 363 éléments
  cliquables tous dans une seule colonne, 2 179 bulles, 605 citations dont 332 nomment un
  document et une page, 121 annoncent une assertion concurrente, 363 badges de conclusion
  tous à « À instruire ».
