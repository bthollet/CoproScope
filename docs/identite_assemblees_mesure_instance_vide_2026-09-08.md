# L'identite des assemblees, mesuree sur une instance VIDE reconstruite

**Ce que cette mesure vaut, et pourquoi elle a exige une instance neuve.** Les
chiffres ci-dessous viennent d'une instance **vide** qui a reabsorbe 858 pieces
sources copiees du coffre, sans reprendre aucun registre ni aucune sortie
anterieure. Une instance chargee aurait porte la sortie de la version
precedente du code, et les memes nombres auraient alors mesure leur propre
ancetre. C'est exactement la situation que la doctrine du depot decrit.

## Trois faits, du plus visible au plus couteux

### 1. La meme assemblee existe toujours sous deux identifiants

Table `resolutions`, sur une base reconstruite de zero:

| `ag_id` | resolutions |
|---|---:|
| `AG-2026-09-02` | **96** |
| `AG-2024-07-03` | **55** |
| `AG-DOC-7139EDAD85E4` | **55** |

Les deux dernieres lignes sont **la meme assemblee**. `RM-2026-0077` est donc
confirme sur une reconstruction propre: ce n'etait pas une sequelle d'instance
historique.

### 2. La date d'assemblee est lue dans le CHEMIN, et un dossier de collecte
n'est pas une assemblee

**270 documents portent la meme `suspected_date`.** Tous les 270 viennent d'un
seul dossier, dont le nom se termine par cette date. **Aucun** ne porte cette
date dans son nom de fichier.

Ce dossier est un dossier de **captation**: son nom enregistre *le jour ou le
lot a ete collecte*, pas ce que les documents contiennent. La chaine ne fait pas
la difference: elle prend la date qu'elle trouve dans le chemin.

Comme `_ag_id` construit `AG-<date>`, tous les proces-verbaux de ce lot
deviennent **une seule assemblee**, celle du jour de la collecte. C'est l'origine
des 96 resolutions de la premiere ligne du tableau: **plusieurs assemblees
reelles empilees sous une date qui n'est celle d'aucune d'elles.**

**L'axe.** Ce qui varie, c'est la maniere dont un lot de documents est range:
par date de reception, par exercice, par sujet, par expediteur. Ce qui reste
invariant, c'est qu'**un dossier decrit un RANGEMENT, jamais le contenu d'un
document**. Une date lue dans un chemin est donc, au mieux, un indice sur le
classement - jamais une propriete de la piece.

**Ce qui se passe hors des valeurs observees:** un cabinet qui range par
exercice produirait `AG-2024` pour tout un exercice; un rangement par mois
produirait une assemblee par mois. Le defaut ne fait echouer aucun test: il
change le nombre d'assemblees.

### 3. Le run a rapporte `ok` en jetant la plus grande part des resolutions

Le meme passage annonce:

- `resolutions_construites`: **400**
- `resolutions_ecrasees`: **84 cles**, chacune libellee *« 4 ou 5 lignes pour une
  seule cle »*, toutes sous `AG-2026-09-02`
- et en base, **206** lignes au total.

Autrement dit: la chaine **dit** qu'elle ecrase, elle **nomme** chaque cle
ecrasee - c'est du bon comportement, et il faut le porter au credit du code - et
elle conclut `"status": "ok"`.

**Le defaut n'est donc pas le silence: c'est le verdict.** Un traitement qui
perd la majorite de ce qu'il construit n'est pas dans un etat `ok`, quelle que
soit la qualite de son journal. Un lecteur qui regarde le statut - c'est-a-dire
tout le monde, et toute automatisation - conclut que le passage s'est bien
passe.

**Corollaire mesure sur le meme passage:** le compteur d'etape annonce
`resolutions: 12` la ou la base en porte **206**. Deux comptes de la meme notion
dans une seule sortie.

## Ce que cela invalide, et ce que cela n'invalide pas

**Invalide:** tout denombrement d'assemblees, et tout total de resolutions
presente sans reserve, sur cette copropriete.

**N'invalide pas:** les mesures de conservation faites cette nuit sur la voie
des seuils. Cette instance reconstruite rend **121** liens de seuil de
consultation et **178** de mise en concurrence - **exactement** les nombres
obtenus par le lot `RM-2026-0144` sur une autre instance. La migration ne perdait
rien, et cela se verifie maintenant sur une base neuve.

## Residu

1. **Une seule copropriete.** Le second cabinet n'a pas ete reabsorbe ici.
2. **Le lien entre les faits 2 et 3 n'est pas prouve dans le detail.** Que le
   dossier de captation produise l'assemblee de 96 resolutions est etabli; que
   les 84 cles ecrasees soient *toutes* dues a cela ne l'est pas - elles sont
   toutes sous cet `ag_id`, ce qui rend l'hypothese forte, pas certaine.
3. **Des dates invalides passent.** Le registre porte des valeurs comme un mois
   `13`, et une valeur reduite a une annee-mois. Rien ne les refuse.
4. **L'instance de lot n'est pas supprimee**, parce que le chantier n'est pas
   fini: elle porte la mesure ci-dessus et servira a eprouver la correction.
   Elle se nomme `test_identite_ag_20260908`, donc son nom dit qu'elle est
   jetable.

---

# Apres correction: le mecanisme exact, et un chiffre que je dois retirer

## Le mecanisme n'etait pas un repli, c'etait une priorite

Le paragraphe 2 ci-dessus disait *la date est lue dans le chemin*. C'est vrai,
et **c'est plus grave que ce que la phrase laisse entendre**. L'echantillon qui
sert au classement se construit ainsi:

    [nom_de_fichier, chemin_complet]  +  [le texte extrait]

et la date y etait cherchee par premiere correspondance. Le chemin etant
concatene **avant** le texte, une date presente dans l'arborescence gagnait
**systematiquement** contre le document. Ce n'etait donc pas un dernier recours
quand rien n'est lisible - c'etait la source prioritaire.

Verification sur les 270 pieces concernees: la date du dossier de collecte
n'apparait **nulle part** dans leurs textes extraits, et **aucune** ne la porte
dans son nom. 228 d'entre elles n'ont aucune date lisible du tout.

## La correction, et ce qu'elle change

`date_du_document(texte, nom_de_fichier)` **ne recoit pas de chemin**. La
garantie est structurelle et non comportementale: il n'existe aucun parametre
par lequel passer un chemin, et un test le verifie sur la signature elle-meme.
Sans date lisible, la date est **vide**, et une note dit quelle date du
rangement a ete ecartee.

Meme instance, reconstruite vide, avant et apres:

| | avant | apres |
|---|---:|---:|
| resolutions construites | 400 | 400 |
| **cles ecrasees** | **84** | **0** |
| resolutions en base | **206** | **400** |
| assemblee fantome | 96 resolutions | **disparue** |

**194 resolutions cessent d'etre ecrasees en silence**, et la conservation est
exacte: 400 construites, 400 stockees. A la place de la fausse assemblee,
**sept assemblees distinctes**, dont six identifiees par leur document faute de
date lisible. La fusion muette est devenue une separation avec incertitude
declaree - et c'est le dispositif deja en place qui la nomme.

## Le chiffre que je retire

Le paragraphe *Ce que cela invalide* ci-dessus affirmait que cette instance
rendait **121 + 178** liens de seuil, *exactement* les nombres du lot
`RM-2026-0144`, et en concluait que la migration etait innocentee par un temoin
independant.

**Sur la base corrigee, c'est 121 + 121.** Les 57 liens d'ecart venaient de
l'assemblee fantome.

Ce qui reste vrai: la **conservation** de la migration - 299 = 121 + 178 + 0 -
etait exacte sur la base ou elle a ete mesuree. Ce qui etait faux: ma phrase
presentant ces nombres comme retrouves sur une base independante. Ma base neuve
portait encore le defaut de date.

**Consequence a tenir:** aucun compte ABSOLU sur cette copropriete ne doit etre
retenu des mesures de cette journee. Ce qui tient, ce sont les proprietes de
conservation, chacune sur sa base.

## Defaut annexe corrige au meme endroit

Le motif de date acceptait deux chiffres commencant par 0 ou 1 comme mois: le
registre portait des valeurs a mois 13 et a mois 00. Un mois va de 01 a 12, un
jour de 01 a 31. La borne porte sur la VALEUR du champ, pas sur les valeurs
rencontrees.
