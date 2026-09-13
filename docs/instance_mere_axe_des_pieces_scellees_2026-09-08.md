# L'instance mere: sur quel axe distinguer une piece recue d'une sortie du produit

**Mesure du 2026-09-08, sur le coffre en LECTURE SEULE.** Aucun fichier du
coffre n'a ete cree, modifie, deplace ni supprime. Rien n'a encore ete copie:
ce document etablit le critere **avant** de construire quoi que ce soit.

## Pourquoi ce critere doit etre pose avant, et pas pendant

La doctrine du depot dit qu'un lot qui touche la chaine d'absorption repart
d'une instance **vide** qu'il reconstruit depuis les pieces sources. Elle
avertit aussi que le coffre porte, melees aux pieces recues, **les sorties d'une
version anterieure du produit**. Reprendre le coffre tel quel ferait donc
rentrer la sortie de la version precedente comme si c'etait une entree - le
defaut exact que la regle existe pour empecher.

Tout repose donc sur une seule question: **qu'est-ce qui distingue une piece
recue d'un fichier fabrique ?** Une reponse approximative ne se verrait pas: on
obtiendrait une instance qui tourne, qui compte, et qui mesure son propre
ancetre.

## L'axe: ce qui a PRODUIT le fichier

Ce qui varie d'un fichier a l'autre, c'est **son producteur**. Une piece est
*scellee* quand elle a ete produite hors de CoproScope et transmise telle
quelle; elle est *derivee* quand un traitement - de ce produit ou d'une version
anterieure - l'a fabriquee.

Ce qui reste invariant le long de cet axe: **un derive a toujours un amont, une
piece scellee n'en a pas.**

Degradation attendue: un fichier qu'on ne sait pas rattacher n'est **ni absorbe
ni ignore en silence** - il est compte et nomme.

## Ce que la mesure a REFUTE

**Hypothese testee: un derive porte le radical de son source.** Un OCR de
`piece.pdf` s'appellerait `piece.txt`, une image de page `piece.png`.

**Refutee. 29 fichiers sur 5 969, soit 0,5 %.** Les derives sont renommes -
identifiants opaques, numeros de page, empreintes. Le rattachement par radical
ne rattache rien.

C'est une hypothese qu'il aurait ete facile de supposer vraie: elle est
plausible, elle marche sur les quelques exemples qu'on regarde d'abord, et un
critere fonde dessus aurait laisse passer 99,5 % des derives.

## Ce que la mesure ETABLIT

Le coffre porte **7 223 fichiers**. Repartis par extension susceptible d'etre
une piece transmise (PDF, bureautique, images, courriels), il en reste **1 254
fichiers pour 1 220 contenus distincts**.

Ces 1 220 contenus se separent nettement:

| | contenus |
|---|---:|
| presents **uniquement** dans la zone de sortie declaree du produit | **336** |
| presents a la fois dans la zone de sortie et ailleurs | **0** |
| **jamais** dans la zone de sortie | **884** |

La separation est **totale**: aucun contenu ne se trouve des deux cotes. Et les
336 sont tous d'une seule famille, que leur chemin declare - des copies
**caviardees** produites par une version anterieure, nommees par identifiant de
document. Elles ressemblent a des pieces recues (ce sont des PDF), elles n'en
sont pas.

**Le critere opere est donc: la zone declaree.** Le coffre nomme ses racines, et
deux d'entre elles disent ce qu'elles contiennent - l'une se declare *collecte
brute non modifiee*, l'autre *systeme*. C'est une declaration, pas une
inference sur le contenu, et c'est ce qui en fait un axe et non une liste de
formats observes.

Repartition par zone, en distinguant les pieces susceptibles d'etre transmises
du reste:

| zone (deux niveaux) | transmissibles | autres |
|---|---:|---:|
| zone systeme / execution du produit | 336 | 2 553 |
| referentiel / reglement et modificatifs | 30 | 2 343 |
| zone systeme / textes OCR et journaux | 0 | 425 |
| boite de reception, sous-dossier d'un exercice | 386 | 0 |
| collecte brute non modifiee / captation | 270 | 2 |
| collecte brute non modifiee / extranet | 71 | 0 |
| assemblees generales par date | 68 | 45 |

Deux zones sont **de la reception pure** - 386 pieces et 0 autre fichier, 341
pieces et 2. Deux autres sont **de la fabrication quasi pure** - 2 553 et 2 343
fichiers qui ne sont pas des pieces transmises.

## Ce que ce document ne dit pas

1. **Il ne prouve pas que les 884 sont toutes des pieces recues.** Il prouve
   qu'aucune ne vient de la zone de sortie declaree. Une piece fabriquee
   ailleurs - un document de travail redige a la main, un export range hors zone
   - y figure encore. Le tri fin reste a faire, et il se fera **en nommant ce
   qui est ecarte**, jamais en le retirant en silence.
2. **Il ne dit rien des versions.** Deux exemplaires d'un meme acte, l'un
   tamponne, l'autre non, comptent ici pour deux contenus sans lien. C'est le
   meme residu que la verification de completude du coffre a deja nomme.
3. **Il ne dit rien de ce qui n'a jamais ete transmis.** Aucune mesure interne
   au coffre ne peut repondre a cette question.
4. **Aucune copie n'a encore ete faite.** La construction de l'instance mere est
   une tache separee, qui devra nommer ce qu'elle copie, le compter, et dire ce
   qu'elle laisse.

## Suite ouverte

Le chainage du derive vers sa source manque toujours - c'est `RM-2026-0147`, et
les 336 copies caviardees mesurees ici en sont l'illustration la plus nette:
**elles ne declarent pas de quel original elles viennent.** C'est precisement ce
qui a rendu ce document necessaire: sans ce chainage, il a fallu une mesure pour
retrouver une propriete qu'une colonne aurait dite.
