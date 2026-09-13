# Le coffre contient-il tout ? Reponse etablie le 2026-09-08

Document de reference. Il clot la question et n'a pas vocation a etre rejoue.
Il ne contient aucun nom de document, aucun patronyme, aucun chemin de piece:
des comptes, des methodes et des verdicts.

Ce qui a ete mesure: le coffre local de la copropriete, et l'ensemble des
fichiers detenus par CoproScope sur le poste. Ce qui a ete cherche: un document
recu du syndic qui existerait dans CoproScope sans exister dans le coffre.

---

## 1. La reponse en une phrase

**Oui, le coffre contient tout. Zero document recu manque.**

Le controle qui tranche est le plus court des sept qui ont ete faits: sur les
**3 388 pieces posees dans les zones de pieces recues des instances et issues de
la copropriete, 3 388 sont dans le coffre, octet pour octet.** Aucune exception.

La confrontation brute avait d'abord affiche **3 907 empreintes presentes dans
CoproScope et absentes du coffre**. Aucune n'est un document manquant. Elles se
rangent ainsi, et la somme est exacte:

| Ce que c'est | Combien | A chercher dans le coffre ? |
|---|---:|---|
| Sorties d'extraction en texte fabriquees par le produit | 2 212 | non |
| Images de pages fabriquees par le produit pour lire les PDF | 594 | non |
| Registres, journaux, index et bases ecrits par le produit | 1 025 | non |
| Copies caviardees de pieces que le coffre porte deja | 7 | non |
| Outillage, configuration et materiel de cle des lots | 44 | non, et leur presence y serait le defaut |
| Fixtures fictives de demonstration | 3 | non |
| Pieces sources d'une **autre** copropriete, second cabinet | 22 | non, elles ne relevent pas de ce coffre |
| **Documents recus reellement absents** | **0** | — |

Un elargissement de perimetre fait en fin de campagne a ajoute **159 absences**
supplementaires, toutes du meme genre: 156 sorties du pseudonymiseur et 3
fixtures de demonstration. Le total d'absences reelles depasse donc 4 000, et le
nombre de documents manquants reste **zero**.

---

## 2. Comment on l'a etabli, et pourquoi trois voies

Une seule mesure ne peut pas se contredire elle-meme. Trois voies independantes
ont donc ete construites, chacune aveugle la ou les autres voient.

**Voie A - l'empreinte de contenu du coffre.** Chaque fichier du coffre a ete lu
en lecture seule stricte et reduit a une empreinte numerique de son contenu
(SHA-256): deux fichiers identiques au bit pres ont la meme empreinte, un seul
octet different donne une empreinte totalement differente. Resultat: **7 223
fichiers, 5 934 empreintes distinctes, 1,98 Go, zero fichier illisible.**
La sortie ne porte ni nom ni chemin, et les lignes sont triees par empreinte,
ce qui casse toute correlation avec l'arborescence.

**Voie B - l'empreinte de contenu de CoproScope.** Meme instrument, applique aux
fichiers detenus par le produit. Les racines ou le produit ECRIT sont exclues
par contrat: chaque instance declare elle-meme, dans sa configuration, ou elle
ecrit et quelle racine ne doit jamais etre modifiee. Resultat sur l'arbre
complet: **1 050 empreintes de format scelle** (document pagine, traitement de
texte, tableur), dont 859 presentes au coffre.

**Voie C - le nom et la structure, sans lire un seul octet de contenu.** Elle
compte, par dossier et par extension, les fichiers et les volumes des deux
cotes. Resultat: **7 223 fichiers cote coffre, 26 772 cote instances**, soit un
rapport de 3,7 en nombre et 6,7 en volume.

**Pourquoi trois.** Parce que chacune a corrige une erreur des autres, et que
c'est la seule preuve valable qu'une mesure a ete eprouvee.

- La voie C, qui ne lit aucun contenu, a detecte que la voie B avait un trou de
  perimetre: une zone de travail de 809 pieces n'etait pas comptee. Elle a ete
  hachee avant toute conclusion.
- La voie B a corrige la voie C en sens inverse: la voie C annoncait 1 691
  divergences, la voie B a montre que 1 630 d'entre elles sont le meme contenu
  sous un autre nom. La voie C surestimait la divergence d'un facteur 27, et
  elle l'avait elle-meme annonce comme son angle mort principal.
- La confrontation finale a montre que les deux voies etaient d'accord: les 32
  empreintes qu'elle isole portent exactement les 61 cles nom+taille que la
  voie C isolait. Deux comptages du meme fait, l'un en noms, l'autre en
  contenus.

**Puis chaque groupe d'absences a ete attaque.** Sept agents ont recu chacun un
groupe et trois hypotheses a essayer de faire tenir: (1) ce ne sont pas des
pieces recues mais des fabrications du produit, (2) le document est au coffre
sous une autre empreinte, (3) l'un des deux cotes a ete mal lu. **Sept groupes
sur huit sont tombes.** Le huitieme, les 22 pieces d'un second cabinet, a tenu -
mais pour une raison differente de celle qu'on lui pretait, voir section 4.

---

## 3. Ce que chaque voie ne voit pas

Cette section n'est pas une precaution de style. C'est ce qui empeche de faire
dire a la mesure plus qu'elle ne dit.

**La voie A - l'empreinte du coffre - ne voit pas:**

- la difference entre un doublon voulu et un doublon fautif. Elle a trouve 1 289
  doublons exacts, 17,9 % des fichiers. Ce ne sont pas 1 289 erreurs: un
  exemplaire de sauvegarde, un classement volontairement redondant et un
  accident produisent le meme signal;
- le meme document reencode. Un re-scan, un re-export, un tampon ajoute, une
  correction d'accent creent une empreinte neuve pour un document que n'importe
  qui reconnaitrait. **La voie sous-estime donc la duplication et surestime la
  diversite. Le sens de l'erreur est connu, son ampleur ne l'est pas;**
- la difference entre une source et son derive. Une sortie d'extraction et le
  document dont elle provient sont deux empreintes sans lien visible;
- le vide. 79 fichiers de taille nulle partagent une seule empreinte alors
  qu'ils n'ont aucun contenu commun. Le meme piege se rejoue en plus subtil:
  146 empreintes d'extractions vides font ressembler a de la duplication ce qui
  est en realite 685 echecs d'extraction independants;
- ce qui n'est pas un octet: ni date, ni auteur, ni titre, ni sens. Elle ne peut
  repondre a aucune question d'audit. L'extension et la profondeur de dossier
  sont des conventions de nommage, pas des proprietes mesurees.

**La voie B - l'empreinte de CoproScope - ne voit pas:**

- ce qui est hors du perimetre qu'on lui donne. Le perimetre initial etait faux:
  deux racines entieres, 159 empreintes, etaient dehors. Mesure et corrige;
- la difference entre un contenu et un acte juridique. Deux exemplaires du meme
  acte scannes deux fois comptent pour deux;
- ce que l'extension ne dit pas. La regle qui separe une piece recue d'une
  fabrication du produit s'appuie sur le format: une piece recue arrive posee et
  paginee, une fabrication est regenerable. C'est un axe solide, mais c'est un
  proxy: il classe faux les corpus d'essai ecrits a la main en texte brut, et il
  ne distingue pas une photo de sinistre recue d'une capture d'ecran produite;
- la justesse. Elle compte ce qui est POSE, jamais ce qui a ete absorbe, classe
  ou affiche correctement;
- l'identite de copropriete declaree par les instances, qui **n'est pas fiable**:
  une instance porte 338 documents reels en declarant l'entite par defaut de
  l'exemple synthetique, et cinq identifiants d'instance sont portes chacun par
  deux ou trois dossiers differents. Le seul rattachement defendable est le
  recoupement d'empreintes, jamais le champ declare.

**La voie C - le nom et la structure - ne voit pas:**

- le renommage, et c'est son angle mort principal, chiffre par elle-meme: 1 630
  cles qu'elle classe divergentes portent en realite une taille presente au
  coffre. La chaine d'absorption renomme, et la voie lit ce renommage comme une
  difference de corpus;
- la taille comme substitut d'identite, qui n'est pas discriminante: le coffre
  porte 1 132 tailles distinctes pour 1 187 fichiers d'un meme format, et 51
  tailles y portent deja plus d'un fichier;
- l'inverse: meme nom, meme taille, contenu different. Comptes comme un seul
  document. Une piece corrigee ou caviardee passerait inapercue;
- la deduplication reelle du disque: elle compte des entrees de repertoire, donc
  un lien dur ou symbolique est compte plein;
- la chronologie: elle ne dit pas quelle copie precede laquelle.

---

## 4. Les absences retenues, et ce qu'il faut en faire

**Une seule absence a survecu a l'attaque, et ce n'est pas une lacune.**

### 4.1 Les 22 pieces d'une autre copropriete

Elles sont reellement absentes du coffre, et **c'est le comportement correct**:
le coffre est celui d'une seule copropriete, et ces pieces en decrivent une
autre. Trois hypotheses ont ete essayees contre elles et ont echoue: ce ne sont
pas des derives (elles vivent sous une racine de pieces recues, et leurs propres
derives existent ailleurs), elles ne sont pas au coffre sous une autre empreinte
(aucun jumeau de pagination, de texte, de geometrie ou de pixels), et aucun des
deux cotes n'a ete mal lu.

**Le raisonnement d'origine etait faux et il est remplace.** Il s'appuyait sur
le nom de l'outil declare dans les metadonnees des fichiers - un outil grand
public que n'importe qui peut employer. C'est exactement le defaut que la
doctrine du depot interdit: raisonner sur des modalites observees. L'invariant
qui le remplace est fonde sur le metier: un proces-verbal, une convocation, un
appel de fonds NOMME toujours sa copropriete. Mesure sur le texte integral:
**zero occurrence du nom de la copropriete du coffre dans ces 22 documents, 83
occurrences du nom d'une autre copropriete**; et dans l'autre sens, aucun des
4 948 fichiers texte du coffre ne cite cette autre copropriete.

**Action, et elle n'est pas cote coffre:** une instance declare l'entite de la
copropriete principale tout en portant, dans sa racine de pieces recues, ces 22
pieces sources d'une seconde copropriete, a cote de 346 fichiers du corpus
principal. Deux coproprietes sous une seule entite declaree. C'est un point
d'hygiene a traiter cote instances.

### 4.2 Ce que la campagne a exhume au passage, et qui n'est pas une absence

Quatre constats sont sortis de la mesure. Aucun n'est un document manquant, tous
demandent une suite.

**a) Le chainage source vers derive n'existe pas au moment du caviardage.** Sept
copies caviardees ne sont plus tracables jusqu'a leur source par empreinte -
c'est normal, une empreinte identifie un contenu, jamais un document. Le lien
n'existe aujourd'hui que par le nom de fichier, conserve a l'identique. C'est
fragile et implicite. Ce qui manque n'est pas une piece, c'est un chainage ecrit
au moment ou le derive est produit.

**b) Deux defauts produit sur l'extraction.** 685 sorties d'extraction ne
contiennent aucun caractere utile, soit **1 790 pages dont pas un caractere n'a
ete extrait**, en silence. Et une sortie d'extraction pese 72 Mo pour un seul
tableur de 37,8 Mo: 70,7 millions de caracteres pour dix pages declarees.

**c) Le coffre porte lui-meme les sorties d'une version anterieure du produit.**
Il heberge un environnement complet du produit: sorties d'extraction, images de
pages, exports tabulaires, une base, des modeles de reconnaissance de texte et
des sauvegardes horodatees. **Consequence directe pour la doctrine de l'instance
vide qui reabsorbe: repartir du coffre tel quel ferait rentrer la sortie de la
version precedente comme si elle etait une entree.** Une reabsorption honnete ne
doit reprendre que les formats scelles.

**d) Le corpus est recopie une vingtaine de fois.** 5 308 exemplaires pour 891
contenus distincts, mediane de 6 instances par contenu, 12,6 Go cote instances
contre 1,9 Go cote coffre. C'est une question de menage, pas de perte.

---

## 5. Les absences ecartees, et pourquoi

Cette section est aussi importante que la precedente: c'est elle qui evite de
rejouer la mesure. Chaque ligne dit le nombre annonce, le verdict et la preuve
qui l'a fait tomber.

| Groupe | Annonce | Verdict | Ce qui l'a fait tomber |
|---|---:|---|---|
| Sorties d'extraction en texte | 2 212 | **refute, 0** | Les 2 212 ont ete relocalisees, aucune par sondage. 2 055 vivent dans une racine que l'instance declare elle-meme comme zone d'ecriture. Surtout: 1 480 contiennent EXACTEMENT le contenu d'un fichier du coffre, a 19 caracteres pres - un bandeau appose en tete par l'extracteur, verifie caractere par caractere sur 401 cas. Et 1 940 ont un document source dont l'empreinte est au coffre. |
| Images de pages | 594 | **refute, 0** | 593 sur 594 sont des pages A4 rendues aux resolutions standard d'un moteur de rendu. Preuve mecanique: pour 23 documents le nombre d'images egale exactement le nombre de pages de la source, pour les 18 autres c'est un multiple entier exact. Zero incoherence. Et 339 sont visuellement la meme page qu'une image deja au coffre. |
| Registres et journaux | 1 025 | **refute, 0** | Derriere 1 025 empreintes il n'y a que 151 livrables distincts: un fichier reecrit a chaque passage produit une empreinte neuve a chaque passage. 923 des 1 025 ne sont qu'un passage parmi d'autres du meme livrable. 540 sont des fiches qui DESIGNENT une piece sans en etre une. Aucune piece recue. |
| Copies caviardees | 7 | **refute, 0** | Les sept ont un jumeau exact au coffre: meme pagination 7 fois sur 7, meme geometrie de page 7 fois sur 7. Apres retrait des alias poses par le caviardage, 89 a 100 % du texte de la copie se retrouve mot pour mot dans l'original du coffre. Ce sont les originaux moins les identites, plus les alias. |
| Outillage, configuration, cles | 44 | **refute, 0** | Les 23 fichiers de code se compilent, les 19 configurations se parsent et portent le schema de description d'une instance. Les 2 fichiers de 254 octets sont un secret local de 32 octets tire au hasard, que la conception du produit specifie comme ne devant JAMAIS sortir de son instance. **Leur absence du coffre est la garantie qui fonctionne, pas une alerte.** |
| Fixtures de demonstration | 3 | **refute, 0** | Deux portent, imprime en clair sur chaque page, un avertissement de document fictif et le nom d'une copropriete d'exemple. Le troisieme, 43 octets, n'est meme pas un fichier valide. Le registre du produit les declare lui-meme comme fictives. Le coffre ne contient aucun fichier de ce format sous 9 332 octets: rien ne peut leur correspondre. |
| Pieces d'un second cabinet | 22 | **confirme, 22** | Voir section 4.1. Absence normale et attendue. |
| Pieces recues du corpus principal | 0 | **confirme, 0** | Reverifie de zero, sur un perimetre elargi a l'arbre entier. |

**Deux erreurs de methode reperees et corrigees en chemin, a ne pas repeter.**

1. La regle qui classait un fichier en "fixture fictive" s'appuyait sur la
   presence d'un mot dans le nom du dossier. Elle est tombee juste par chance.
   C'est un generateur de faux negatifs silencieux: le jour ou un lot appelle
   son dossier avec ce mot et y pose une vraie piece, une absence reelle sera
   classee fictive et ne remontera jamais. L'axe existait pourtant: chaque
   instance et chaque document declarent leur statut dans une donnee prevue
   pour cela.
2. L'instrument de confrontation connait deux categories - la racine des pieces
   recues et les racines d'ecriture declarees. Il lui manque une troisieme:
   **ce que le produit ecrit pour se decrire lui-meme.** Un fichier de
   description d'instance n'est ni l'une ni l'autre, tombe dans une zone sans
   regle, et de la dans le seau des absents. C'est ce qui a produit l'alerte sur
   le materiel de cle.

---

## 6. Le residu: ce que cette verification ne garantit pas

Ce qui suit n'est pas lisse.

**1. On compare des CONTENUS, pas des documents, et pas des versions.** Un
document present des deux cotes mais DIFFERENT - corrige, tamponne, page
ajoutee, rescanne - ne ressort pas ici: il compte comme deux contenus sans lien.
Symetriquement, un acte scinde en deux fichiers puis recompose peut disparaitre
du comptage. Le sens de l'erreur est connu, son ampleur ne l'est pas.

**2. La question repondue est: "le coffre contient-il tout ce que CoproScope
detient ?". Elle n'est pas: "le coffre contient-il tout ce qui existe ?".** Un
document que le syndic n'a jamais transmis, ou qui n'a jamais ete copie dans une
instance, est invisible des DEUX cotes. Aucune extension de cette methode ne le
verra: il faudrait une liste independante de ce qui devrait exister - suite des
exercices, numerotation des assemblees, ordres du jour annonces. C'est une autre
mesure, et elle n'a pas ete faite.

**3. Le sens inverse n'a pas ete traite.** 1 797 empreintes du coffre n'existent
dans aucune instance. Ce n'est pas un probleme de coffre, c'est du travail non
fait cote produit, et cela repond a une question differente: "CoproScope a-t-il
tout absorbe ?". Ne pas confondre les deux.

**4. Trois des 22 pieces du second cabinet n'ont pas de couche texte.** Leur
identite repose sur leur place dans le corpus et sur l'absence de jumeau
geometrique ou pixel, pas sur leur contenu textuel. Si l'on refusait cet appui,
elles resteraient indecidables sur leur seul contenu; les 19 autres sont
confirmees sans reserve.

**5. Certaines causes reposent sur des indices declaratifs.** L'extension d'un
fichier est une convention de nommage: rien ne garantit qu'un fichier annonce
comme document pagine en soit un. Une date de derniere modification peut etre
une date de COPIE et non de creation. Les verdicts des pieces d'un second
cabinet, des fixtures et du corpus principal sont mesures; les autres sont
etablis par faisceau, avec une preuve positive dans chaque cas, mais sans
lecture documentaire complete.

**6. C'est un instantane**, pris le 2026-09-08, sur des instances dont plusieurs
appartiennent a des lots ouverts et peuvent bouger pendant qu'on lit ce chiffre.

**7. Aucune justesse n'a ete mesuree.** Rien ici ne dit que le produit LIT
correctement ces documents: ni le total d'une annexe, ni le nombre de
resolutions d'une assemblee, ni le rattachement d'une facture a une ligne de
depenses. La verification porte sur la presence des octets, point.

**8. Une phrase d'un lot intermediaire est fausse et ne doit pas etre reprise.**
Il annoncait 891 empreintes scellees "verifie sur l'integralite des instances".
L'assiette reelle est **1 050**, dont 859 au coffre et 191 absentes, toutes
expliquees. Deux racines entieres etaient restees dehors. Le chiffre de
documents manquants, lui, survit sans changement.

---

## 7. Comment refaire la mesure, si un jour il le faut

Ce qui suit est la commande, pas le resultat. Trois regles avant tout:
**le coffre s'ouvre en lecture seule**, rien n'y est ecrit ni renomme, pas meme
un fichier temporaire; **toutes les sorties vont dans un dossier de travail hors
depot**; **les sorties ne portent aucun nom de fichier**, seulement empreinte,
taille, extension, profondeur et zone.

**Etape 0 - le controle qui suffit dans la quasi-totalite des cas, et qui prend
quelques minutes.** Ne pas commencer par la confrontation complete. Poser
directement la seule question qui compte: *les pieces posees dans les racines de
pieces recues, et issues de cette copropriete, sont-elles toutes au coffre ?* Si
la reponse est oui, la reponse generale est oui, et tout le reste n'est que du
classement de fabrications du produit.

**Etape 1 - inventorier le coffre par empreinte.**

```powershell
# racines en variables, jamais en dur dans un script partage
$coffre = '<RACINE_DU_COFFRE>'
$sortie = '<DOSSIER_DE_TRAVAIL_HORS_DEPOT>'
```

En Python, ouverture en mode binaire seul, une ligne par fichier, triee par
empreinte:

```python
import hashlib, os
for racine, _, fichiers in os.walk(coffre):
    for f in fichiers:
        chemin = os.path.join(racine, f)
        h = hashlib.sha256()
        with open(chemin, 'rb') as fh:        # lecture seule, aucune ecriture
            for bloc in iter(lambda: fh.read(1 << 20), b''):
                h.update(bloc)
        # ecrire: empreinte, taille, extension, profondeur, zone - PAS le nom
```

**Controle d'integrite avant d'aller plus loin:** le compte doit etre coherent
avec la reference. Au 2026-09-08 le coffre porte **7 223 fichiers, 5 934
empreintes distinctes, 1,98 Go, zero illisible**. Un ecart signifie que le
coffre a bouge, pas que la mesure est fausse.

**Etape 2 - inventorier CoproScope, et surtout ne pas se limiter a une racine.**
C'est l'erreur qui a ete commise deux fois pendant cette campagne. Hacher
**l'arbre entier**, y compris les zones de travail, les sorties et les dossiers
hors instances. Une racine oubliee ne peut qu'ajouter des absents, jamais en
retirer - mais elle rend le total inutilisable pour toute autre question.

**Etape 3 - soustraire les deux ensembles d'empreintes**, puis classer chaque
absence dans **quatre** categories, pas trois:

1. pose dans une racine de pieces recues declaree intouchable;
2. ecrit dans une racine que l'instance declare comme zone d'ecriture;
3. **ecrit par le produit pour se decrire lui-meme** - description d'instance,
   secret local, materiel de configuration. Categorie manquante de l'instrument
   actuel, et source de fausses alertes;
4. hors des trois precedentes: c'est la seule qui merite une enquete.

**Etape 4 - pour toute absence de categorie 1 ou 4, appliquer les trois attaques
dans cet ordre**, et n'accepter un verdict que si les trois echouent:

- est-ce une fabrication du produit plutot qu'une piece recue ? Preuve positive
  attendue: emplacement declare, correspondance mecanique avec une source
  (nombre de pages, contenu inclus a un bandeau pres), nom fabrique par l'etape
  de traitement et non par un emetteur;
- le document est-il au coffre sous une AUTRE empreinte ? Ne pas s'arreter a
  l'empreinte exacte: comparer pagination, geometrie de page, texte, et si
  besoin les pixels;
- l'un des deux cotes a-t-il ete mal lu ? Verifier le compte de fichiers, le
  nombre d'illisibles, l'unicite de la racine du coffre, et l'absence de lien ou
  de jonction qui masquerait une branche.

**Ce qu'il ne faut PAS refaire:** conclure a partir du nom de l'outil declare
dans les metadonnees d'un fichier, ou d'un mot-cle present dans un nom de
dossier. Les deux ont produit des conclusions fausses pendant cette campagne. Un
critere doit nommer son axe et rester vrai hors des valeurs observees.

---

## Ligne a inscrire au gouvernail

A inscrire par le fil pilote dans le registre actif. Prendre le premier
identifiant libre si `RM-2026-0145` est deja pris, et remplacer le chantier par
celui du lot.

```text
| `RM-2026-0145` | Le coffre contient tout: zero document recu absent, sur trois voies independantes et huit attaques adverses | Coffre / completude documentaire / doctrine des preuves | `INTEGRE` | P0 | Fil pilote CONV-2026-2172 | Question posee par Brice le 2026-09-08: « une fois que ca, c'est regle, je ne veux plus qu'on y revienne » | **Clos. Reponse: oui.** 3 388 pieces posees dans les racines de pieces recues et issues de la copropriete, 3 388 au coffre octet pour octet, zero exception. Les 3 907 empreintes absentes du coffre s'expliquent toutes: 3 838 fabrications du produit, 44 objets d'outillage et de cle, 3 fixtures fictives, 22 pieces d'une AUTRE copropriete. Sept groupes sur huit refutes par attaque adverse; l'elargissement de perimetre a ajoute 159 absences, toutes du meme genre. Methode, limites et residu: `docs/coffre_contient_tout_2026-09-08.md`. **Quatre suites ouvertes, aucune n'est une absence:** une instance porte deux coproprietes sous une seule entite declaree; le chainage source vers derive manque au caviardage; 685 sorties d'extraction sans un seul caractere utile (1 790 pages) et une sortie de 72 Mo pour un tableur; le coffre porte lui-meme les sorties d'une version anterieure, donc une reabsorption ne doit reprendre que les formats scelles. **Residu nomme:** la mesure compare des contenus, pas des versions ni des documents, et ne dit rien de ce qui n'a jamais ete transmis | `<CH du lot>` | inventaires par empreinte hors depot, huit refutations tracees | 2026-09-08 |
```
