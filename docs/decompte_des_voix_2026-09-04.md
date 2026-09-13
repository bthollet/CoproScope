# Le decompte des voix: quelle assiette, et quand l'ecran a le droit de calculer

Lot `RM-2026-0086` / `CONV-2026-2139`, chantier `chantier/decompte-des-voix`.
Date: 2026-09-04.

## Synthese, lisible sans connaissance juridique ni comptable

Un vote d'assemblee generale se compte toujours en **voix**, et une voix vaut un
tantieme de parties communes. Mais **le total sur lequel on rapporte ces voix
change selon la majorite applicable**. C'est ce que Brice a avance, et c'est
exact.

- **Article 24**: on compte sur les voix **exprimees** - le pour et le contre -
  des coproprietaires presents, representes ou ayant vote par correspondance.
  Les abstentions sortent de l'assiette.
- **Article 25**: on compte sur les voix de **tous** les coproprietaires, y
  compris ceux qui ne sont pas venus.
- **Article 25-1**: ce n'est pas une majorite, c'est une **passerelle**. Si un
  projet de l'article 25 recueille au moins le tiers des voix de tous, la meme
  assemblee revote immediatement a la majorite de l'article 24.
- **Article 26**: **deux** conditions cumulatives - une majorite en nombre de
  coproprietaires **et** les deux tiers des voix.

L'ecart mesure le 2026-09-03 - certains votes exprimes sur 4 899 parts, d'autres
sur 10 000 - **est explique, et l'explication est bien celle de Brice**: 10 000
est le total du syndicat, 4 899 le total des presents et representes. Ce ne sont
pas deux erreurs, ce sont deux assiettes legales.

**Mais la verification a produit un resultat que l'hypothese ne prevoyait pas, et
il est plus important que l'hypothese elle-meme.** Le nombre imprime apres la
barre oblique ne dit pas de facon fiable quelle assiette a ete employee. Sur le
proces-verbal etalon, quatre resolutions annoncees sous l'article 24 sont
imprimees `/10.000` alors que leur assiette legale est 4 899. Sur le second
cabinet, **une seule resolution porte jusqu'a trois denominateurs differents**.
Conclusion produit: **l'assiette se deduit de la majorite annoncee, jamais du
denominateur imprime.**

Enfin, une decouverte de fait: **la feuille de presence de Tilleuls (pseudo) existe.**
Brice pensait ne pas l'avoir. Elle n'est pas un fichier separe: elle est la
rubrique d'ouverture du proces-verbal du 03/07/2024.

## Methode et limites du controle

Toutes les sources sont lues sur Legifrance via l'API PISTE le 2026-09-04, fonds
`LODA_DATE`, filtre de date pose au jour de la lecture. `VIGUEUR` signifie "en
vigueur a la date demandee", jamais "a jour": la date de version fait partie de
la citation.

Les mesures portent sur deux cabinets de syndic, designes **cabinet A** et
**cabinet B**, et sur les proces-verbaux disponibles au corpus local. Aucun
serveur n'a ete lance. Les instances sont restees en lecture seule.

Limite principale: **ce document etablit ce que les textes imposent et ce que les
pieces portent. Il n'interprete pas un dossier, ce qui releve d'un avocat.**

### Sources

| Texte | Article | `LEGIARTI` | En vigueur depuis |
|---|---|---|---|
| Loi n. 65-557 du 10 juillet 1965 | 6-4 | `LEGIARTI000037657840` | 2018-11-25 |
| Loi n. 65-557 | 10 | `LEGIARTI000043977284` | 2023-01-01 |
| Loi n. 65-557 | 17-1 A | `LEGIARTI000039313644` | 2020-06-01 |
| Loi n. 65-557 | 22 | `LEGIARTI000039313531` | 2020-06-01 |
| Loi n. 65-557 | 24 | `LEGIARTI000051749514` | 2025-06-18 |
| Loi n. 65-557 | 25 | `LEGIARTI000051749507` | 2025-06-18 |
| Loi n. 65-557 | 25-1 | `LEGIARTI000049398359` | 2024-04-11 |
| Loi n. 65-557 | 26 | `LEGIARTI000050623612` | 2024-11-21 |
| Decret n. 67-223 du 17 mars 1967 | 11 | `LEGIARTI000053191281` | 2025-12-25 |
| Decret n. 67-223 | 13 | `LEGIARTI000006488391` | 2004-09-01 |
| Decret n. 67-223 | 14 | `LEGIARTI000042078670` | 2020-07-04 |
| Decret n. 67-223 | 14-1 | `LEGIARTI000042076720` | 2020-07-04 |
| Decret n. 67-223 | 17 | `LEGIARTI000042078689` | 2020-07-04 |
| Decret n. 67-223 | 17-1 | `LEGIARTI000042076794` | 2020-07-04 |

Arrete du 2 juillet 2020 fixant le modele de formulaire de vote par
correspondance: `LEGITEXT000042076555`, article `LEGIARTI000042076565`.

---

## Question 1 - L'assiette de chaque majorite

**Reponse. Elle differe bien d'un article a l'autre, et sur deux dimensions
distinctes qu'il ne faut pas confondre: la population comptee, et la cle de
repartition employee.**

### La population comptee

**Article 24.** Le I dispose que "les decisions de l'assemblee generale sont
prises a la majorite des voix **exprimees** des coproprietaires **presents,
representes ou ayant vote par correspondance**, s'il n'en est autrement ordonne
par la loi" (`LEGIARTI000051749514`). Trois consequences: les absents ne comptent
pas; les votants par correspondance comptent comme presents; et **les abstentions
sortent de l'assiette**, puisqu'une abstention n'est pas une voix exprimee.
L'assiette de l'article 24 est donc *pour + contre*, et rien d'autre.

**Article 25.** "Ne sont adoptees qu'a la majorite des voix de **tous les
coproprietaires** les decisions concernant: [...]" (`LEGIARTI000051749507`).
L'assiette est le syndicat entier. Un absent pese donc contre le projet par son
absence meme - c'est l'effet mecanique du texte, et c'est ce qui rend la
passerelle de l'article 25-1 necessaire.

**Article 25-1.** Ce n'est pas une majorite mais une procedure de rattrapage:
"lorsque l'assemblee generale des coproprietaires n'a pas decide a la majorite
des voix de tous les coproprietaires, [...] mais que le projet a recueilli **au
moins le tiers de ces voix**, la meme assemblee se prononce a la majorite prevue
a l'article 24 en procedant **immediatement** a un second vote"
(`LEGIARTI000049398359`). Le tiers se calcule sur *tous* les coproprietaires; le
second vote se calcule sur les *exprimees*. **Une seule resolution change donc
d'assiette en cours de traitement.** Un second alinea, propre aux travaux
d'economie d'energie du f de l'article 25, autorise une nouvelle assemblee dans
les trois mois sur un projet identique.

**Article 26.** "Sont prises a la majorite des **membres du syndicat**
representant au moins les **deux tiers des voix**" (`LEGIARTI000050623612`).
C'est une **double** condition: une majorite en nombre de tetes, et deux tiers
en voix. Le texte ajoute des cas d'unanimite, notamment pour l'alienation de
parties communes necessaires a la destination de l'immeuble.

### La cle de repartition employee

C'est la seconde dimension, et elle est independante de la premiere. Le nombre de
voix d'un coproprietaire correspond a "sa quote-part dans les parties communes"
(article 22 I, `LEGIARTI000039313531`), avec une correction: celui qui detient
plus de la moitie voit ses voix reduites a la somme des voix des autres.

Mais **le vote peut etre reserve a une partie des coproprietaires**. Le dernier
alinea de l'article 10 (`LEGIARTI000043977284`) le dit: "lorsque le reglement de
copropriete met a la seule charge de certains coproprietaires les depenses
d'entretien et de fonctionnement entrainees par certains services collectifs ou
elements d'equipements, il peut prevoir que ces coproprietaires prennent seuls
part au vote sur les decisions qui concernent ces depenses. Chacun d'eux dispose
d'un nombre de voix **proportionnel a sa participation auxdites depenses**."
L'existence de parties communes speciales suppose leur mention expresse au
reglement (article 6-4, `LEGIARTI000037657840`).

**Consequence produite et mesuree.** Les tantiemes generaux et les tantiemes
speciaux ne sont pas deux facons d'ecrire la meme chose: ce sont deux
populations et deux baremes. Une resolution de l'article 24 votee sur une cle
speciale se compte sur les voix exprimees **de cette cle**.

### Ce que le texte ne dit pas

Il ne dit pas comment se resout une resolution qui melangerait deux cles. Il ne
fixe aucun arrondi pour "le tiers" ni pour "les deux tiers": le module retient
l'arrondi au superieur, seule lecture compatible avec "au moins", et **c'est une
lecture, pas une citation**. Il ne dit pas non plus comment etablir le nombre de
membres du syndicat exige par l'article 26 quand le proces-verbal ne le publie
pas.

---

## Question 2 - Le vote par correspondance et la resolution modifiee en seance

**Reponse. Brice a raison sur le principe, et la regle reelle est plus etroite
que sa formulation sur deux points qui changent le calcul.**

Le texte est l'article 17-1 A, alinea 2 (`LEGIARTI000039313644`):

> "Si la resolution objet du vote par correspondance est **amendee** en cours
> d'assemblee generale, le votant par correspondance **ayant vote favorablement**
> est assimile a un coproprietaire **defaillant** pour cette resolution."

**Trois precisions, et chacune compte.**

1. **Le declencheur est l'amendement, pas toute modification.** Le texte vise la
   resolution "amendee en cours d'assemblee generale". Une correction de plume,
   un changement d'intitule sans portee, ou une simple precision ne sont pas
   necessairement un amendement. **Le texte ne definit pas l'amendement**, et
   l'outil n'a pas a trancher cette qualification: c'est un champ a valider par
   un humain.
2. **Seul le votant favorable tombe.** Le texte ne vise que "le votant par
   correspondance ayant vote favorablement". **Il est muet sur celui qui a vote
   contre et sur celui qui s'est abstenu par correspondance.** Dire que "les
   votes par correspondance tombent" est donc trop large: le contre par
   correspondance n'est pas vise par cette disposition.
3. **Il devient defaillant, ni oppose ni hors decompte.** "Defaillant" est la
   qualite de celui qui n'a pas participe. Consequence arithmetique directe:
   - il **sort** de l'assiette de l'**article 24**, puisqu'il n'exprime plus de
     voix;
   - il **reste** dans l'assiette de l'**article 25**, qui compte tous les
     coproprietaires;
   - il conserve la **qualite pour agir** en contestation, l'article 42 alinea 2
     ouvrant l'action aux opposants **et aux defaillants**.

**Le proces-verbal doit le publier.** L'article 17 du decret
(`LEGIARTI000042078689`) impose que le proces-verbal precise "les noms et nombre
de voix des coproprietaires ou associes qui se sont opposes a la decision, qui
se sont abstenus, ou **qui sont assimiles a un coproprietaire defaillant en
application du deuxieme alinea de l'article 17-1 A**". Le renvoi est explicite:
la categorie a une existence documentaire obligatoire.

**Une regle voisine, distincte, et qu'il ne faut pas confondre.** L'article 14-1
du decret (`LEGIARTI000042076720`) dispose qu'"au moment du vote, le formulaire
de vote par correspondance **n'est pas pris en compte** lorsque le
coproprietaire, l'associe ou leur mandataire est **present** a l'assemblee
generale". Ici le formulaire est neutralise non par un amendement mais par la
presence: la personne vote en seance. Ce n'est pas une defaillance, c'est une
substitution.

**Mesure.** Le cabinet B applique la regle et la nomme. Ses proces-verbaux
portent, sous chaque resolution, une rubrique `Est defaillant : 1 coproprietaire
(Vote par correspondance)`, doublee d'une ligne `Defaillant (vote par
correspondance) : Non exprime`. Sur une resolution de l'assemblee 2024, la
verification arithmetique est exacte: 30 725 voix exprimees + 4 570 abstentions +
741 voix devenues defaillantes = **36 036**, soit exactement le total de la
feuille de presence. La chaine legale entiere se lit dans le document.

**Ce que le texte ne dit pas, et qui decide du comportement produit.** Il ne dit
pas si un second vote doit etre organise, ni si le votant peut etre reconsulte.
Il ne dit pas non plus ce qu'il advient du vote favorable par correspondance
lorsque l'amendement est **favorable au votant**. **Reponse a la question posee:
il faut recalculer, et non refuser de conclure - mais uniquement quand le
proces-verbal publie la ligne des defaillants assimiles.** Sans cette ligne, le
recalcul serait une reconstitution, pas une lecture; l'ecran doit alors dire que
le controle n'est pas conduit.

---

## Question 3 - Departs et arrivees en cours de seance

### Il n'y a pas de quorum

**Reponse. Le texte est muet, et ce silence est un resultat.** Aucune des
dispositions qui gouvernent la composition de l'assemblee et le comptage des
voix - articles 22, 24, 25, 25-1 et 26 de la loi, articles 13, 14, 14-1, 15,
15-1, 17 et 17-1 du decret - ne mentionne de quorum. Une recherche du mot dans
le fonds `LODA_DATE`, controlee par une sonde a terme impossible pour verifier
que le moteur honore bien la requete, ne ramene ni la loi de 1965 ni le decret
de 1967.

C'est coherent avec la construction meme de l'article 24: puisqu'il compte les
voix exprimees **des presents**, l'assemblee delibere valablement quelle que soit
l'affluence. La contrainte n'est pas un quorum, elle est arithmetique, et elle ne
mord que sur l'article 25.

**Attention au vocabulaire des syndics.** Le cabinet A ecrit "Le quorum etant
atteint la seance est ouverte" et, sur une resolution de l'article 25 b),
"**Pas le quorum. Pas de vote**". Ce mot n'a pas de fondement dans les textes de
la copropriete: le syndic designe ainsi le fait que le seuil de l'article 25 est
hors d'atteinte compte tenu des presents. **C'est une modalite d'ecriture. Le
produit ne doit ni reprendre ce mot a son compte ni en deduire une regle.**

### La feuille de presence

**Elle est obligatoire, son contenu est fixe, et elle est annexee au
proces-verbal.** L'article 14 du decret (`LEGIARTI000042078670`) ouvre par un
indicatif qui vaut obligation - "il est tenu une feuille de presence" - et fixe
son contenu:

- les nom et domicile de chaque coproprietaire ou associe **present physiquement
  ou represente**, **participant par visioconference, audioconference ou autre
  moyen electronique**, et **ayant vote par correspondance avec mention de la
  date de reception du formulaire par le syndic**;
- pour un represente, les nom et domicile du **mandataire**;
- **pour chaque coproprietaire, le nombre de voix dont il dispose**, "le cas
  echeant en faisant application" de la reduction de l'article 22 I et du dernier
  alinea de l'article 10 - c'est-a-dire, precisement, des cles speciales;
- l'**emargement** par chaque coproprietaire present physiquement ou son
  mandataire;
- la **certification exacte par le president de seance**;
- elle peut etre tenue sous forme electronique.

L'article 17 du decret ajoute, en une phrase: "**La feuille de presence est
annexee au proces-verbal.**" Elle n'est donc pas une piece annexe facultative:
elle fait corps avec le proces-verbal.

**L'article 14 est, textuellement, le lieu ou l'assiette de chaque scrutin est
etablie.** C'est la seule piece qui porte a la fois la population presente et le
bareme de voix applicable, cle speciale comprise. Un decompte sans feuille de
presence n'est pas verifiable.

### Ce que le texte dit du changement de composition

**Il n'en dit rien, et c'est la vraie limite.** Aucune disposition n'organise le
depart ou l'arrivee en cours de seance, ne prescrit de mettre a jour la feuille
de presence, ni ne dit a quelle resolution s'applique quel etat de presence.

Ce qui s'en deduit, et qui n'est pas dans le texte mais dans sa logique: puisque
l'article 24 compte les presents **au moment du vote**, et puisque l'article 14-1
neutralise le formulaire de correspondance quand la personne est presente "au
moment du vote", **l'assiette de l'article 24 est une donnee par resolution, pas
par assemblee**. L'assiette de l'article 25, elle, ne bouge pas: le syndicat ne
change pas de taille pendant la seance.

**Un filet de securite, et il ne sauve pas tout.** L'article 17-1
(`LEGIARTI000042076794`) dispose qu'une irregularite **formelle** du
proces-verbal ou de la feuille de presence "relative aux conditions de vote ou a
la computation des voix n'entraine pas necessairement la nullite de l'assemblee
generale", a deux conditions cumulatives: pouvoir reconstituer le sens du vote
**et** que le resultat "n'en soit pas affecte". Une presence mal suivie qui
change le resultat n'entre donc pas dans ce pardon.

**Mesure - et c'est le cabinet B qui donne la bonne pratique.** Son
proces-verbal de 2026 ecrit, en clair et au fil de la seance:

> "Est arrive en cours de seance: [...] La feuille de presence fait desormais
> reference a **31 913** tantiemes presents, representes ou votant par
> correspondance sur **48 750** tantiemes."
>
> "Est parti en cours de seance: [...] La feuille de presence fait desormais
> reference a **31 308** tantiemes [...] sur 48 750 tantiemes."

Le meme cabinet en 2024 enregistre une arrivee portant le total a **36 036**. Le
cabinet A, lui, publie un total unique d'ouverture - 4 899 sur 10 000 - et ne
trace aucun mouvement.

**Axe et invariant.** L'axe est *la maniere dont un cabinet trace, ou ne trace
pas, les mouvements de seance*. L'invariant est que **l'assiette de l'article 24
vaut au moment du vote**. Un produit qui supposerait une presence constante sur
toute l'assemblee coderait la modalite du cabinet A et se tromperait sur le
cabinet B, ou l'assiette bouge deux fois dans un meme document.

---

## Question 4 - L'acte d'autorisation et le devis lie: lequel fait foi ?

**Reponse. C'est l'acte - la resolution votee - qui fait foi, parce que lui seul
est une decision. Mais cette primaute est conditionnee, et la condition est
precisement ce que le produit ne mesure pas aujourd'hui.**

**Pourquoi l'acte prime.** Un devis est une offre d'un prestataire; il n'engage
le syndicat que par la decision qui l'accepte. La decision, c'est la resolution.
Le produit a donc raison dans sa direction.

**Mais l'article 13 du decret (`LEGIARTI000006488391`) pose une double
condition**: "l'assemblee generale ne prend de decision valide que sur les
questions **inscrites a l'ordre du jour** et **dans la mesure ou les
notifications ont ete faites** conformement aux dispositions des articles 9 a
11-I". Et l'article 11 I 3° (`LEGIARTI000053191281`) range, **"pour la validite
de la decision"**, la notification prealable des "conditions essentielles du
contrat ou, en cas d'appel a la concurrence, des contrats proposes, lorsque
l'assemblee est appelee a approuver un contrat, **un devis** ou un marche,
notamment pour la realisation de travaux".

**Consequence, et elle repond a l'inquietude de Brice sur le prestataire present
en seance.** Le montant du devis notifie n'est pas un simple element de contexte:
il fait partie des conditions essentielles dont la notification conditionne la
validite de la decision. Un montant renegocie en seance avec un prestataire
present n'a, lui, pas ete notifie. Deux effets se cumulent alors:

1. la decision prise sur un montant non notifie est exposee au grief de
   l'article 13;
2. la resolution est **amendee** - ce qui fait tomber, par l'article 17-1 A
   alinea 2, les votes par correspondance favorables.

**Un montant discute en seance n'est donc jamais un detail d'affichage: il
declenche les deux questions de ce document a la fois.**

**Mesure.** Sur le proces-verbal etalon, les resolutions de travaux incorporent
le devis **dans** la resolution: la resolution enonce les propositions
concurrentes avec leurs montants, puis conclut "L'Assemblee Generale vote le
devis de [prestataire]: [montant] T.T.C". Acte et devis portent alors le meme
montant par construction, et la question ne se pose pas. Elle se pose quand les
deux divergent, ou quand le devis lie au dossier n'est pas celui que la
resolution nomme.

**Ce que le texte ne dit pas.** Aucune disposition ne dit lequel des deux
montants l'emporte en cas de divergence, ni ce qui se passe quand le montant vote
depasse le montant notifie. **Le point n'est pas tranche ici et ne doit pas etre
affirme dans un rapport.** Ce qui est certain, c'est que la divergence est un
fait juridiquement pertinent, et non un artefact d'extraction a normaliser.

**Verdict sur le choix actuel du produit.** Faire primer la colonne de l'acte est
**la bonne direction, mais le choix est incomplet**: il ne doit pas conduire a
ecarter silencieusement le montant du devis. Le produit doit conserver les deux
et produire un constat quand ils different.

---

## La mesure, sur les deux cabinets

### La feuille de presence: elle existe, et Brice ne le savait pas

**Cabinet A.** Elle n'est pas un fichier separe - c'est pourquoi elle semblait
absente. Elle est la **rubrique d'ouverture du proces-verbal du 03/07/2024**, et
elle porte reellement:

- la liste nominative des presents, des representes avec le nom du mandataire,
  et des votants par correspondance;
- la quote-part individuelle de chacun, en 10 000emes;
- le total des presents et representes: **4 899 / 10 000**;
- le total des absents: **5 101 / 10 000**.

Controle de coherence: 4 899 + 5 101 = 10 000. La presence est de 48,99 %.

Ce qui **manque** au regard de l'article 14: aucun emargement n'y figure - le
bloc est une liste imprimee -, et la **date de reception du formulaire** des
votants par correspondance n'est pas portee. La certification par le president de
seance n'apparait pas dans le bloc. Ce sont des irregularites formelles au sens
de l'article 17-1, dont l'effet depend de savoir si le resultat en est affecte.

Une **version pseudonymisee** du meme document existe au corpus caviarde: elle
conserve integralement les tantiemes et la structure presents / representes /
absents. C'est la seule copie a employer pour tout travail exploitable.

**Cabinet B.** Aucune feuille de presence n'est versee au corpus. Les
proces-verbaux n'en donnent que le **total agrege**, mais ils le donnent bien, et
ils le **mettent a jour a chaque mouvement de seance** (voir question 3). Base du
syndicat: 48 750 tantiemes.

Aucun pouvoir signe ni formulaire de vote rempli n'existe dans aucun des corpus;
les seuls formulaires presents sont vierges et sans couche de texte.

**Signal qualite a transmettre a la voie competente, hors de mon perimetre.** Le
type documentaire `Feuille_Presence_AG` du classifieur compte 51 documents sur
une instance de reconstruction, et **aucun n'est une feuille de presence** - ce
sont des pages du reglement de copropriete et des tableaux d'audit. Symetriquement,
le seul vrai bloc de feuille de presence est classe `Convocation_AG`.

### L'ecart 4 899 / 10 000: explique, et plus riche que prevu

Le proces-verbal etalon annonce, resolution par resolution, la majorite
applicable et la base de vote. La correspondance est la suivante, mesuree sur les
55 resolutions:

| Resolutions | Majorite annoncee | Base annoncee | Assiette legale |
|---|---|---|---|
| 1 a 6, 28 a 31 | article 24 | tantiemes generaux | voix exprimees des presents (4 899 au plus) |
| 7 a 27, 32 a 34 | articles 25 et 25-1 | tantiemes generaux | toutes les voix: 10 000 |
| 35 | article 25 b) | tantiemes generaux | toutes les voix: 10 000 |
| 36 a 55 | article 24 | **tantiemes entree** | voix exprimees de la cle: 525, 610, 967, 968 ou 1 155 |
| 23 | aucune enoncee | aucune | indeterminable |

**L'hypothese de Brice est donc confirmee dans sa substance** - les deux bases
sont bien les deux assiettes legales - **et elle est incomplete sur deux points**.

**Premier point: il y a trois familles de bases, pas deux.** Vingt resolutions
sont votees sur une **cle speciale d'entree**, fondee sur le dernier alinea de
l'article 10. Un outil qui ne connaitrait que 4 899 et 10 000 se tromperait sur
vingt resolutions du meme document.

**Second point, et c'est le resultat le plus important du lot: le denominateur
imprime ne nomme pas l'assiette.**

- Les resolutions 28, 29 et 30, annoncees sous l'**article 24**, impriment la
  ligne "ont vote pour" sur **`/10.000`**. Or le detail publie de la resolution
  28 totalise 4 746 + 105 + 48 = **4 899**, exactement les presents et
  representes. Le denominateur imprime est le total du syndicat; l'assiette
  legale est celle des exprimees.
- Chez le **cabinet B**, une seule resolution porte **trois** denominateurs
  differents: 30 725 sur les lignes pour et contre - qui est bien la somme des
  exprimees -, **48 009** sur la ligne d'abstention, et **36 036** sur la ligne
  du defaillant. Et d'une resolution a l'autre du meme type, le cabinet alterne
  entre le total des exprimees et le total du syndicat: sur 21 resolutions
  chiffrees, **9 seulement** impriment un denominateur egal aux voix exprimees.

### Le resultat qui explique l'assemblee entiere

Avec **4 899 voix presentes sur 10 000**, le seuil de l'article 25 - plus de
5 000 voix - est **arithmetiquement hors d'atteinte**, quel que soit le vote.

La verification confirme la deduction sans une exception:

- **aucune** des 21 resolutions annoncees sous les articles 25 et 25-1
  n'atteint 5 001 voix; le maximum releve est **4 794**;
- les **18** declarees adoptees franchissent **toutes** le tiers de 10 000, soit
  3 334 voix - elles ne peuvent donc l'avoir ete que par le **second vote de
  l'article 25-1**;
- les **3** declarees rejetees - 3 152, 1 982 et 1 369 voix - sont **toutes** en
  dessous de ce tiers, ce qui fermait la passerelle.

**21 resolutions sur 21 s'expliquent par la seule regle de l'article 25-1.** Ceci
eclaire la mesure anterieure du produit - 48 resolutions **appliquees** a
l'article 24 pour 30 seulement **annoncees** sous cet article: l'ecart de 18 est
exactement le nombre de passerelles reellement empruntees.

---

## La regle des axes appliquee

| Difference constatee entre cabinets | L'axe | L'invariant le long de l'axe | Ce que le code en fait | Hors des valeurs observees |
|---|---|---|---|---|
| `/10.000` vs `/4899` vs `/30725` vs trois valeurs dans une meme resolution | la maniere dont un cabinet imprime le denominateur d'un vote | la majorite annoncee impose l'assiette; le denominateur imprime n'en est qu'un temoin | l'assiette est **deduite de la majorite**; le denominateur imprime est confronte et produit un constat en cas d'ecart | un quatrieme format de denominateur ne change rien: il n'est jamais lu comme une assiette |
| `VOTE AUX TANTIEMES GENERAUX` / `TANTIEMES ENTREE` vs `Base de repartition : CHARGES BATIMENT B` | la maniere de nommer la cle de repartition | tout scrutin porte sur une cle, et une cle a un total | le total de la cle est un parametre d'entree `voix_totales`, jamais une constante | une cle inconnue est acceptee: seul son total est requis |
| `Article24` / `Majorite simple` / `Majorite absolue` / `Double majorite` | le vocabulaire de la majorite | quatre regimes legaux, et un cinquieme etat: non enonce | seuls les articles sont reconnus; un libelle non reconnu rend `ASSIETTE_INDETERMINEE` | un libelle inconnu **ne devient jamais l'article 24 par defaut** |
| total de presence unique vs mis a jour a chaque mouvement | la maniere de tracer les mouvements de seance | l'assiette de l'article 24 vaut au moment du vote | l'assiette se reconstitue par resolution, jamais une fois pour l'assemblee | une assemblee a dix mouvements se traite comme une a zero |
| `Pas le quorum` | le vocabulaire du syndic pour l'echec de l'article 25 | il n'existe aucun quorum en copropriete | le mot n'est pas repris; l'etat rendu nomme le seuil non atteint | un cabinet inventant un autre mot ne cree pas de regle |

**Epreuve d'acceptation.** Un troisieme syndic arrivant avec un denominateur
inconnu, une cle inconnue ou un libelle de majorite inconnu obtient soit un
verdict correct, soit un etat de refus explicite. Aucun chemin ne produit un
pourcentage faux en silence.

---

## Ce que l'ecran doit en faire

### Peut-il afficher un pourcentage ?

**Oui, mais seulement quand il peut nommer sa base.** Trois conditions
cumulatives:

1. **la majorite est enoncee** - sans elle, l'assiette est inconnue et ne se
   suppose pas;
2. **la donnee de l'assiette est disponible**: pour l'article 24, les voix pour
   **et** contre; pour l'article 25, le total de la cle de repartition;
3. **la base est affichee a cote du pourcentage**, en toutes lettres.

Un pourcentage sans sa base nommee est interdit. C'est la regle qui a manque a la
maquette du 2026-09-03, et elle avait raison de refuser de calculer.

### Que doit-il afficher quand il ne le peut pas ?

Six etats, dont quatre sont des refus assumes. **Un refus qui nomme la donnee
manquante est plus utile qu'un pourcentage tire d'un denominateur d'imprimeur.**

| Etat | Quand | Ce que l'ecran dit |
|---|---|---|
| `ADOPTEE_CONFIRMEE` | le seuil de la majorite annoncee est atteint sur son assiette | le pourcentage, **et sa base nommee** |
| `REJET_CONFIRME` | le seuil n'est pas atteint et le proces-verbal conclut au rejet | les chiffres confirment le document |
| `PASSERELLE_25_1_REQUISE` | seuil de l'article 25 non atteint, mais au moins le tiers recueilli | l'adoption ne s'explique que par un second vote a l'article 24; **verifier qu'il a eu lieu** |
| `ADOPTEE_MAIS_DECOMPTE_INSUFFISANT` | proclamee adoptee sans le seuil ni le tiers | le document affirme le contraire de ses propres chiffres |
| `ASSIETTE_INDETERMINEE` | majorite non enoncee, total de cle inconnu, ou nombre de membres manquant pour l'article 26 | **nommer la donnee qui manque**, ne rien calculer |
| `DECOMPTE_ABSENT` | le proces-verbal ne publie pas les voix | irregularite au regard de l'article 17, et aveu que le controle n'est pas conduit |

### Quatre exigences supplementaires

1. **Ne jamais lire l'assiette dans le denominateur imprime.** Le confronter, et
   afficher un constat quand il diverge - libelle: *le proces-verbal imprime le
   vote sur N, l'assiette imposee par la majorite annoncee est M*.
2. **Afficher le constat d'inatteignabilite au niveau de l'assemblee, pas de la
   resolution.** Quand les presents ne depassent pas la moitie du syndicat,
   l'ecran doit le dire une fois, en tete: *aucune resolution de l'article 25 ne
   pouvait etre adoptee a cette assemblee*. C'est une information de premier
   ordre pour un conseiller syndical, et elle se calcule avec deux nombres.
3. **Traiter l'article 26 comme incontrolable par defaut.** La majorite en nombre
   de membres n'est pas publiee; l'ecran doit afficher `ASSIETTE_INDETERMINEE` en
   disant laquelle des deux conditions il ne peut pas verifier, plutot que de
   valider sur les seules voix.
4. **Porter la feuille de presence comme une piece a part entiere.** Elle est
   annexee au proces-verbal par l'article 17, elle etablit l'assiette par
   l'article 14, et le corpus montre qu'elle peut etre **incluse dans le
   proces-verbal** plutot que jointe. Un controle "feuille de presence absente"
   qui ne regarde que les fichiers separes produira un faux constat sur le
   cabinet A.

### Le predicat livre

Un module nouveau, `server/src/coproscope/modules/_decompte_voix.py`, porte ces
regles et rien d'autre: il ne lit aucun document, n'ecrit dans aucun magasin, et
ne manipule que des totaux de voix - aucune donnee nominative n'y transite. Ses
33 tests, dans `server/tests/test_decompte_voix.py`, rejouent les mesures des
**deux** cabinets, y compris les 18 passerelles et les 3 rejets de l'assemblee
etalon.

---

## Ce qui reste ouvert

Quatre points n'ont pas de reponse textuelle nette et ne doivent etre ni
tranches par un ecran ni affirmes dans un rapport:

- **la qualification de l'amendement** (question 2): le texte ne definit pas ce
  qui constitue un amendement en seance; c'est un champ a valider par un humain;
- **le sort du vote par correspondance defavorable ou abstentionniste** en cas
  d'amendement (question 2): le texte ne vise que le vote favorable et se tait
  sur les autres;
- **la mise a jour de la feuille de presence en cours de seance** (question 3):
  aucune disposition ne l'organise; la pratique du cabinet B est une bonne
  pratique, pas une obligation demontree;
- **le montant qui l'emporte entre l'acte et le devis notifie en cas de
  divergence** (question 4): l'acte est la decision, mais aucun texte ne regle la
  divergence elle-meme.

Un cinquieme point est une lecture assumee et non une citation: **l'arrondi au
superieur** retenu pour "au moins le tiers" et "au moins les deux tiers".

## Confidentialite

Aucun nom, aucun tantieme individuel, aucun vote nominatif ne figure dans ce
document ni dans le module et ses tests. Le proces-verbal etalon nomme environ
120 coproprietaires avec le sens de leur vote: c'est la donnee la plus sensible
du corpus, et elle n'a servi qu'a produire des totaux. Les cabinets sont designes
par alias. Aucun chemin local, aucun nom de fichier brut, aucune piece brute
n'est reproduit. Les deux instances sont restees en lecture seule et aucun
serveur n'a ete lance.
