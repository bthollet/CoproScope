# Ce qu'une cellule de contrôle nomme, on peut l'ouvrir

`RM-2026-0157`, lot A du retour de Brice sur la maquette des contrôles.
Mesures du 2026-09-09.

## En une phrase

Chaque cellule de l'écran de contrôle citait déjà « telle pièce, page 18,
sous-point 13-4 » **sans y mener**. Le nom de la pièce est devenu un lien, la
page voyage avec lui, et le lecteur sait avant de cliquer ce que la
destination pourra lui montrer.

## Le geste qui plante : ce qu'on a cherché, et ce qu'on a trouvé

L'item disait de corriger d'abord un geste qui échoue — Brice, `[00:04:59]` :
*« voir le devis retenu, ça a planté »*. Un geste qui échoue détruit la
confiance dans les autres.

**Aucune exception ne se lève.** Les 786 citations de l'écran ont été jouées
une par une contre la fiche document : 786 fois `200`. Le défaut est ailleurs,
et il est pire qu'un plantage parce qu'il ne se signale pas.

**Les 13 pièces que cite tout l'écran sont en zone brute, arbitrage de biffage
non tranché.** La fiche document refuse alors l'aperçu — et elle a raison, ce
sont des pièces réelles non biffées. Le lecteur qui suivait le lien arrivait
donc sur une page annonçant *« Aucun aperçu exploitable »*. Du point de vue de
celui qui clique, c'est la même chose qu'un plantage.

Ce n'est pas un défaut à réparer : c'est un fait à **dire avant le clic**.

## Ce que la mesure a établi

Corpus du lot : instance jetable `test_atteignable_20260909`, copie des
registres et du coffre d'une instance déjà absorbée, plus les seules pièces
citées. 557 lignes de matrice, 858 documents au registre.

| Ce qui est compté | Nombre |
|---|---:|
| Citations portant un `doc_id` | 786 |
| dont le document est absent du registre — **lien mort** | **0** |
| Citations portant aussi une page | 386 |
| Citations portant une ancre sans page | 400 |
| Documents distincts cités par tout l'écran | 13 |
| dont l'aperçu est refusé par le garde-fou de biffage | **13** |
| Citations rendues sur l'écran, après correction | 621 |
| dont porteuses d'un lien | **621** |
| Destinations distinctes, suivies pour de vrai | 34 → 34 fois `200` |

## Trois axes, et ils ne se recoupent pas

L'écran en confondait deux.

| Axe | Ce qu'il dit | Ce qui le renseigne |
|---|---|---|
| **Nommable** | comment appeler la pièce | table des convocations |
| **Atteignable** | y a-t-il quelque chose à ouvrir | registre documentaire |
| **Montrable** | la destination affichera-t-elle le contenu | arbitrage de biffage |

**La confusion mesurée.** La citation écrivait *« pièce que le registre des
convocations ne nomme pas »* dès qu'un `doc_id` manquait à la table des
convocations. Un lecteur y comprend *on ne sait pas de quelle pièce il
s'agit*. C'est faux : **400 citations d'acte sur 786 sont dans ce cas, et les
400 désignent un document présent au registre documentaire**. Le produit sait
exactement quel fichier c'est ; il ne sait pas comment l'appeler.

La phrase est devenue « cette pièce (le registre des convocations ne la nomme
pas) » : le fait reste écrit, hors du lien, là où il ne peut plus se lire
comme une ignorance.

## Ce que le code fait de chaque axe

- **Document connu du registre** → le nom de la pièce est un lien.
- **Document inconnu du registre** → aucun lien, et l'écran dit qu'il n'y a
  rien à ouvrir. Un chemin mort coûte plus cher qu'un chemin absent.
- **Page citée** → elle voyage dans l'adresse, et le lecteur PDF s'y ouvre.
- **Pas de page** → rien de plus dans l'adresse. Fabriquer `page=1` par défaut
  ferait passer une valeur par défaut pour une lecture.
- **Page hors bornes** → le lecteur ouvre page 1 **et le dit**, en nommant les
  deux nombres. Le registre porte `page_count`, le magasin de liens porte
  `page` : deux chemins d'écriture que rien ne recoupe, donc l'écart doit
  pouvoir arriver et se voir.
- **Contenu couvert par l'arbitrage de biffage** → étiquette de deux mots sous
  la cellule, et **une phrase, une seule fois pour tout l'écran**, avec le
  nombre de pièces concernées — qui est une tâche. Répétée sous chaque
  citation, elle aurait été rendue 621 fois à l'identique.

## Hors des valeurs observées

- **Pièce désignée mais absente du registre : zéro occurrence sur ce corpus.**
  La branche existe, elle est éprouvée sur un témoin construit pour cela, et
  elle n'a jamais été déclenchée par de la matière réelle. L'item prévoyait
  d'y router vers l'écran d'ancrage `RM-2026-0158` : cet écran n'existe pas
  encore, donc le chemin est absent plutôt qu'inventé.
- **Ancre sans page** (400 citations) : l'ancre n'entre pas dans l'adresse. La
  fiche document ne sait pas se placer sur un sous-point, et un paramètre
  qu'elle ignorerait ferait croire à une précision qu'elle n'a pas.
- **Instance sans registre documentaire** : aucun lien nulle part. Proposer un
  chemin enverrait chaque clic sur un 404.

## Deux résidus, nommés

1. **Le verdict porte sur le registre, pas sur le fichier.** Un document
   inscrit dont le fichier a disparu reçoit quand même un lien ; sa fiche
   s'ouvre et déclare elle-même l'absence. Vérifier le disque coûterait une
   lecture par cellule à chaque affichage.
2. **La deuxième entrée de la résolution n'est pas livrée.** Brice
   `[00:01:30]` : *« soit vers la résolution elle-même dans le corps du PDF,
   soit vers les annexes. D'ailleurs il pourrait y avoir les deux boutons. »*
   L'annexe est déjà une sous-bulle avec sa propre citation, donc elle porte
   son propre lien quand elle en a un — mais aucune annexe n'est rattachée sur
   ce corpus, donc **cette moitié n'a pas été éprouvée sur de la matière**.

## Ce qui a été cassé en route, et réparé

**Une garde rouge, et ce n'est pas le lot qui l'a manquée — c'est moi.**
`test_ecrans_sans_instance_declarent_leur_nature` exigeait qu'**au moins un
écran aveugle existe** — sa doctrine annonce huit. Le commit `4140931`
(*« identité : douze écrans nommaient une copropriété qui n'était pas la
leur »*) a donné un paramètre `instance` à ces huit constructeurs, et la
population de la garde est passée de huit à zéro. Les deux lots ne touchaient
pas les mêmes lignes : **aucun conflit à signaler**.

**Correction d'une affirmation que j'avais écrite, et elle est injuste.**
J'ai d'abord dit que le lot `RM-2026-0059` avait livré cette garde rouge sans
le voir. C'est faux, et son propre message de commit le dit noir sur blanc :
*« NON CORRIGE, et c'est la décision à prendre : […] est ROUGE sur 913d744
comme sur 77c3b5e. Son critère […] ne désigne plus aucun écran depuis que les
constructeurs ont reçu `instance: Any | None = None`. […] Redéfinir le critère
est un arbitrage produit. »* Le lot a mesuré le défaut, l'a nommé, et a laissé
l'arbitrage ouvert. **C'est moi qui l'ai fusionné sans jouer ce module.**

C'est tout de même la **deuxième fois dans la même journée** qu'un lot vide le
corpus de la garde d'un autre sans qu'aucun outil ne le voie.

Deux corrections :

- **un compteur de défauts n'est pas une garde d'instrument.** Exiger qu'un
  écran aveugle existe revient à exiger que le défaut survive. La garde prouve
  désormais son instrument en deux temps : la collecte atteint le code, et le
  critère sait encore dire non — éprouvé sur un témoin écrit pour cela ;
  **mais l'instrument réparé ne rend pas la couverture perdue, et je l'avais
  présenté comme si.** Les huit écrans que `RM-2026-0059` visait rendent
  toujours du contenu fictif — mesuré : de 3 à 23 marqueurs par écran — et
  **aucune garde ne leur impose plus de le déclarer**. Les huit portent bien
  une `notice` aujourd'hui, donc l'honnêteté tient ; ce qui a disparu est ce
  qui la forçait. L'arbitrage que le lot demandait reste **ouvert**, et il est
  celui de Brice : redéfinir le critère sur ce qui compte — *l'écran
  invente-t-il des données* — plutôt que sur la forme de sa signature ;
- **la collecte ne regarde plus le nom des fichiers.** Elle lisait
  `endswith("_view")`. Son module frère a corrigé exactement ce point le même
  jour ; la correction n'avait pas été portée ici. *Une correction ne couvre
  que le site qu'elle touche* — leçon déjà écrite dans le `CLAUDE.md`, et
  reproduite.

**Une garde d'immuabilité rouge sur un faux positif de plateforme.**
`test_fixtures_versionnees_immuables` annonçait *contenu modifié (18)* sur
l'instance partageable, avec des écarts de 1 à 117 octets — exactement leur
nombre de lignes — alors que `git status` disait ces fichiers propres. Cause :
`.gitattributes` déclare `eol=lf` depuis le 2026-05-23, les fixtures datent des
20 et 21 mai, et un arbre de travail créé avant cette déclaration garde des
fins de ligne Windows que git normalise à la lecture. **L'arbre était
l'anomalie, pas la référence** : les fichiers ont été restaurés depuis l'index,
`git status` reste vide. `git add --renormalize` ne suffit pas — il ne réécrit
que l'index. Le signe distinctif est maintenant écrit dans la garde, pour que
le prochain ne le cherche pas : *quelques octets d'écart sur un fichier que
`git status` dit propre, ce sont des fins de ligne*.

**Un sélecteur de test trop large.** `page.count("cs-citation")` comptait une
sous-chaîne : l'ajout de `cs-citation-lien` et `cs-citation-reserve` en a fait
compter trois pour un seul cartouche. Le compte porte désormais sur
`class="cs-citation"`. Un sélecteur de mesure trop large échoue exactement
comme une énumération, dans l'autre sens.

**Une garde d'identifiant qui passait pour une raison fragile.**
`test_la_page_ne_montre_jamais_la_reference_interne_du_fichier` interdit
qu'un `doc_id` sorte à l'écran. Il passait parce que son instance de recette
ne déclare aucun registre documentaire, donc aucune citation n'y porte de
lien. Il mesure désormais le texte en excluant les attributs d'adresse : la
règle porte sur ce qui se **lit**, et l'adresse `/documents/<doc_id>` est la
même que sur les écrans des comptes et des factures à revoir.

## Ce que la recette sur page réelle a trouvé, et que les tests n'avaient pas vu

Serveur local port 8781, instance jetable bâtie sur `examples/synthetic_copro`
— donc partageable — avec les trois cas côte à côte. Les trois rendent
exactement ce qui était voulu : lien avec `?page=1` pour la pièce ouvrable,
lien sans page pour celle sous réserve (son acte n'en porte pas), **texte
simple** pour celle qu'aucun registre ne porte. Le clic mène bien à la pièce.

**Deux fautes d'accord, invisibles à 23 tests et lisibles en trois secondes.**
« 1 **attendent** un arbitrage » sous les filtres, et « dépasse **les 1 pages**
de ce document » dans le lecteur. Aucun test ne les voyait, parce que tous
portaient sur des comptes pluriels. Corrigées, puis gardées sur les deux
nombres — c'est la raison pour laquelle une livraison qui touche un bout de
page se **regarde**, et pas seulement se mesure.

**Un piège de recette, à connaître.** Le serveur relancé continuait à servir
l'ancien texte : le processus tué était un intermédiaire, et son
petit-fils Python tenait toujours le port. La relance ne pouvait pas se lier,
sans le dire. Un serveur de recette qui sert du code périmé est pire qu'un
serveur absent : il fait valider ce qu'on n'a pas livré.

## Les gardes, et la preuve qu'elles mordent

`server/tests/test_citation_de_controle_ouvre_sa_piece.py`, 21 tests sur
`examples/synthetic_copro` — dont les neuf documents portent **les deux
verdicts**, sept ouvrables et deux sous réserve, ce qui éprouve les deux
branches.

Quatre mutations jouées, quatre attrapées :

| Ce qu'on casse | Ce qui rougit |
|---|---|
| le gabarit ne pose plus de lien | 3 tests |
| `chemin_de_piece` fabrique `page=1` | `..._ne_fabrique_pas_page_1` |
| la page hors bornes se rabat en silence | 2 tests |
| un lien est posé sur une pièce inconnue | dont le clic joué, qui rend 404 |

**Un affaiblissement trouvé par la mutation, avant livraison.** La garde
« chaque lien répond » cherchait `href="/documents/..."`. Elle est restée
**verte** alors que plus aucune citation ne portait de lien : l'écran porte
d'autres liens vers `/documents/`, et ils suffisaient à la satisfaire. Le
sélecteur porte désormais la classe de la citation.

**Ce corpus ne prouve rien sur la justesse.** `examples/synthetic_copro` est
l'instance partageable ; ses pièces ont été écrites pour passer. Les nombres
de ce document viennent d'un corpus réel, sur une instance de lot supprimée en
fin de chantier.
