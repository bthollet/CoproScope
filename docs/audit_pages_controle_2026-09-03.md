# Audit de l'etat reel des pages de controle - 2026-09-03

Role de l'auteur: novice et critique. Rattachement: RM-2026-0051, voie
"etat reel des pages de controle". Ce document est l'"avant" de la comparaison
avant/apres demandee par Brice. Il ne propose pas de cible et ne corrige rien.

Le protocole `docs/protocole_agents_claude_code.md` section 3 demande qu'au moins
un role puisse conclure "a refaire" et pas seulement "a corriger". C'est le mandat
de ce document. L'auteur n'a recu le raisonnement d'aucun autre role: il a recu
onze ecrans et des criteres.

## Conditions de la mesure

| Element | Valeur |
|---|---|
| Instance | `tilleul_pseudo_test`, exercice 2025 |
| Serveur | port 8792 reserve, jeton de recette dedie |
| Fenetres testees | 360, 375, 390, 412, 430, 480, 540, 640, 768, 980, 1024, 1440 px |
| Premier passage de mesure | 2026-09-03 01:45:43 -> 01:45:50 |
| Second passage (controle de derive) | 2026-09-03 02:05:09 |
| Captures | 2026-09-03 01:52 -> 02:12 |

### Avertissement sur la stabilite de l'instance

Une autre conversation ecrivait dans le coffre de la meme instance pendant la
mesure. Le controle de derive le confirme: entre 01:45:47 et 02:05:09, sans
aucune action de l'auteur, la page `/ag-contentieux` a gagne 54 lignes de
tableau (une assemblee supplementaire, huit resolutions). Les dix autres pages
sont revenues octet pour octet identiques.

Consequence directe, et c'est deja un constat: **les quatre compteurs de tete de
cette page (223 / 123 / 57 / 180) n'ont pas bouge d'une unite alors que la liste
qu'ils annoncent grossissait.** Un compteur qui ne suit pas la liste qu'il coiffe
est faux quelle que soit la qualite des donnees.

### Deux classes de constats

Brice a pose que les instances historiques ont subi de tres nombreuses
variations et ne sont pas fiables. `tilleul_pseudo_test` est concernee. Les constats
sont donc ranges en deux classes, et le rangement fait partie du livrable.

- **Classe 1** - ne depend pas de la verite des donnees. Verdict ferme.
- **Classe 2** - exige un etalon de verite indisponible ici. Le nombre est
  publie, la justesse n'est pas tranchee. A confronter au corpus etalon de
  RM-2026-0050 (35 pieces, etalon etabli a la main avant tout traitement outil).

---

## 1. Verdict

> **Sur les seuls defauts independants de la qualite des donnees, ces pages sont
> A REFAIRE.**

Deux raisons, et une seule suffirait.

**Premiere raison: la regle de generation, pas les donnees.** Sur les cinq pages
qui portent du volume, la page produit une ligne par enregistrement et s'arrete
la. Elle ne regroupe pas, ne pagine pas, ne hierarchise pas. Le resultat mesure:
`/documents/ajouter` fait 410 000 a 418 000 pixels de haut, soit 456 a 464 ecrans
de portable, avec 3 157 arrets de tabulation et 68 003 elements de page. Ce n'est
pas un ecran a retoucher, c'est l'absence d'un ecran. Aucun reglage de marge,
de couleur ou de libelle ne ramene 464 ecrans a un ecran: il faut decider quoi
montrer, ce qui est une decision de conception, pas une retouche.

**Seconde raison: quatre des onze pages ne sont branchees sur rien.**
`/gouvernance/atelier-ag`, `/gouvernance/compte-rendu-cs`,
`/gouvernance/participants-ag` et `/gouvernance/roles-commissions` sont des
maquettes HTML. Leur fonction de construction ne prend que l'annee en argument
et retourne un dictionnaire ecrit en dur; elle ne lit ni instance, ni coffre, ni
base. Ces pages ne peuvent pas devenir une beta par retouche, parce qu'il n'y a
rien a retoucher: tout le travail reste a faire.

Ce verdict est volontairement etroit. Il ne dit pas que le produit est mauvais.
Il dit que ces onze ecrans, tels qu'ils sont, ne sont pas un point de depart
qu'on ajuste.

### Ce qui marche et qu'il ne faut pas jeter

Un verdict "a refaire" qui ne nomme pas ce qui tient est un verdict paresseux.

- **L'ossature d'accessibilite est bonne.** Zero controle sans nom accessible sur
  les onze pages. Un `h1` et un `main` par page, aucun saut de niveau de titre,
  `lang="fr"`, `meta viewport`, lien d'evitement "Aller au contenu" avec style de
  focus. C'est mieux que la moyenne des applications metier.
- **La mise en page repond correctement de 360 a 980 px.** Verifie a onze
  largeurs: aucun debordement horizontal, aucun controle hors ecran. (Note
  methodologique: les premieres captures mobiles laissaient croire a un
  rognage; verification faite, c'etait un artefact de capture, pas un defaut du
  produit. Les captures ont ete refaites.)
- **Le bloc "Aide rapide"** annonce explicitement le parcours clavier et rappelle
  que les statuts ne reposent pas seulement sur la couleur.
- **Le panneau "Rapprochement 4 sources"** de `/comptes/rapprochement`
  (comptabilite / banque / facture / decision, chacun avec son etat) est le seul
  endroit du produit ou un benevole comprend d'un coup d'oeil ce qui manque pour
  conclure. C'est un bon objet de conception.
- **Les blocs "Mots utiles - definitions courtes"** de deux pages gouvernance
  sont exactement ce qu'il faut pour un novice. Ils n'existent pas sur les pages
  comptes, qui en auraient plus besoin.
- **La prudence de diffusion est tenue partout**: chaque page repete ce qu'elle
  n'est pas, ce qu'elle ne declenche pas, et ce qui reste a valider par un
  humain. C'est rare et c'est precieux.

---

## 2. Les cinq defauts les plus graves

Classes par gravite. Pour chacun: est-ce l'ecran, ou le modele derriere.

### D1 - La page rend tout, sans regroupement ni pagination
**Classe 1. Defaut du modele derriere (regle de generation).**

| Page | Hauteur (px) | Ecrans de 900 px | Arrets de tabulation | Elements de page |
|---|---:|---:|---:|---:|
| `/documents/ajouter` | 410 274 - 418 003 | 456 - 464 | 3 157 | 68 003 |
| `/comptes/factures-a-revoir` | 72 238 - 84 499 | 80 - 94 | 832 | 18 818 |
| `/ag-contentieux` | 48 946 - 59 821 | 54 - 66 | 44 | 7 435 |
| `/comptes` | 9 274 - 9 332 | 10,3 | 85 | 1 119 |
| `/comptes/rapprochement` | 1 413 | 1,6 | 878 | 4 432 |
| `/gouvernance` | 3 222 | 3,6 | 42 | 423 |
| Cockpit `/` | 1 724 | 1,9 | 84 | 531 |
| 4 pages maquettes gouvernance | 1 969 - 2 715 | 2,2 - 3,0 | 45 - 47 | 291 - 389 |

Les fourchettes viennent des deux passages de mesure; l'ecart traduit la derive
d'instance signalee plus haut, pas une imprecision de mesure.

Poids servi: de 36 Ko (cockpit) a **4,36 Mo pour `/documents/ajouter`**, qui met
6,0 secondes a s'afficher en local, sans reseau.

Ou commence le travail utile, mesure au pixel sur une fenetre de 900 px:

| Page | Premier element a traiter | Ecrans de preambule |
|---|---:|---:|
| `/documents/ajouter` | y = 3 590 | 4,0 |
| `/comptes` | y = 1 372 | 1,5 |
| `/ag-contentieux` | y = 1 283 | 1,4 |
| Cockpit `/` | y = 1 372 | 1,5 |

Sur quatre pages sur cinq, il faut derouler une fois et demie a quatre fois la
hauteur de l'ecran avant d'atteindre la premiere chose a faire. Sur une fenetre
de 768 px de large, 465 px sur 844 - **55 % du premier ecran** - sont occupes par
la navigation avant tout contenu.

Le seuil de la strategie est de 20 points a traiter sur corpus restreint. En
pleine charge, la mesure donne: 24 cartes sur `/comptes`, 790 lignes sur
`/comptes/factures-a-revoir`, 827 lignes sur `/comptes/rapprochement`, 460 points
annonces sur `/ag-contentieux`, 2 175 lignes de tableau sur `/documents/ajouter`.

### D2 - Motifs strictement identiques repetes sur des lignes distinctes
**Classe 1. Defaut du modele derriere (regle de generation). Seuil: zero.**

| Page | Lignes affichees | Libelles distincts | Redondances strictes |
|---|---:|---:|---:|
| `/comptes/rapprochement` | 827 | **1** | 826 |
| `/comptes/factures-a-revoir` | 790 | **4** | 786 |
| `/documents/ajouter` | 2 175 | 359 | 1 816 |
| `/comptes` | 24 | 6 | 18 |
| `/ag-contentieux` | 511 | 456 | 55 |

Le detail rend la chose concrete.

- `/comptes/rapprochement`: 827 lignes de travail, **un seul** motif de controle
  (828 occurrences de la meme pastille) et **une seule** action suivante (830
  occurrences de la meme phrase). Un benevole qui ouvre 827 lignes lit 827 fois
  la meme instruction.
- `/comptes/factures-a-revoir`: 790 lignes pour 4 actions distinctes, reparties
  539 / 226 / 133 / 24. Les deux tiers du travail consistent a lire que l'outil a
  ingere deux fois le meme document.
- `/documents/ajouter`: trois lignes de tableau sont repetees **310 fois chacune**,
  a l'identique.
- `/comptes`: 12 des 24 cartes sont rigoureusement identiques - meme statut,
  meme motif, meme champ fournisseur vide, meme preuve attendue, meme suite.
- `/ag-contentieux`: 80 occurrences identiques de la meme action, 80 de la meme
  mention de diffusion, 67 du meme titre de ligne.

C'est un defaut de regle, pas de donnees: une regle qui produit le meme texte
pour 827 cas differents ne discrimine rien, quel que soit le contenu du coffre.

### D3 - Compteurs contradictoires, y compris sur le meme ecran
**Classe 1. Defaut du modele derriere (chaque compteur a sa propre source).**

Le defaut connu au 2026-09-02 etait "quatre comptages concurrents pour la meme
notion". Il est vivant et il s'est etendu.

| Notion | Valeurs affichees | Ou |
|---|---|---|
| Pieces manquantes | **89** et **12** | badge lateral et tuile, **simultanement visibles sur `/comptes`** |
| Controle des comptes | **31**, **827**, **2 349**, **24**, **30** | badge lateral / tuiles / cartes / onglet |
| Factures a revoir | **827** et **790** | `/comptes` + `/comptes/rapprochement` vs `/comptes/factures-a-revoir` |
| Repartition sur la meme page | **790** vs **254 + 535 = 789** | `/comptes/factures-a-revoir` |
| AG et contentieux | **0**, **-**, **223**, **461** | badge cockpit / badge sur la page / corps de la page |
| Demandes au syndic | **46**, **30**, **"le registre est vide"** | badge / onglet `/comptes` / `/gouvernance` |
| Documents a qualifier | **310** et **346** | en-tete et carte source, **meme page** |
| Avancement | **0 prets** sous une barre a **39 %** | `/documents/ajouter` |

Le cas le plus net tient dans une seule capture: sur `/comptes`, l'etiquette
"Pieces manquantes" apparait deux fois a l'ecran, une fois avec 89 et une fois
avec 12. Il n'existe aucune lecture des donnees qui rende ces deux nombres
simultanement vrais pour la meme etiquette.

S'y ajoute un troisieme etat: les badges lateraux affichent des chiffres sur
certaines pages, des **tirets** sur `/comptes/rapprochement` et `/ag-contentieux`,
et disparaissent sous 980 px de large.

### D4 - Identite fictive affichee sur des donnees reelles
**Classe 1. Defaut d'ecran (et de garde-fou).**

**Cinq pages sur onze** portent le titre d'onglet `CoproScope - Copropriete
FICTIVE` alors que la barre laterale et le bandeau de contexte de la meme page
nomment la copropriete reelle:

1. `/comptes/rapprochement`
2. `/gouvernance/atelier-ag`
3. `/gouvernance/compte-rendu-cs`
4. `/gouvernance/participants-ag`
5. `/gouvernance/roles-commissions`

Pour les quatre pages gouvernance, l'etiquette est exacte: elles sont
effectivement fictives, et elles le disent franchement dans leur corps ("aucun
import reel", "les donnees affichees sont synthetiques"). C'est honnete.

**`/comptes/rapprochement` est le cas grave.** Cette page affiche 827 lignes de
donnees reelles, des montants reels, des noms de fournisseurs reels, et une
lettre au syndic prete a etre copiee - sous un onglet nomme "Copropriete
FICTIVE". Elle affiche en outre, dans l'en-tete, la pastille **"Coffre FICTIF"**,
alors que `/comptes`, dans la meme session et sur la meme instance, affiche
**"Coffre tilleul_pseudo-test"**. Deux identites de coffre contradictoires a deux
clics d'ecart.

Le risque n'est pas theorique: un membre du conseil syndical qui voit
"FICTIF" peut classer sans suite un chiffre exact, ou l'inverse.

### D5 - L'ordre de grandeur du chiffre de tete
**Classe 1 par exception d'ordre de grandeur. Defaut du modele derriere
(regle d'admission au corpus).**

`/comptes` affiche en plus gros caractere de la page:

> **Total charges 21 994 060,46 EUR - Exercice 2025**

Vingt-deux millions d'euros de charges annuelles pour une copropriete. Le defaut
signale au 2026-09-02 est donc toujours vivant.

Le mecanisme se demontre **sans aucun etalon de verite**, a partir des seules
colonnes de provenance que l'export affiche lui-meme:

- le total est la somme des debits du grand livre reconstruit, 601 lignes;
- **4 de ces 601 lignes portent 5 285 937,26 EUR chacune**, soit 21 143 749,04 EUR,
  c'est-a-dire **94,5 % du chiffre affiche**;
- ces 4 lignes proviennent de **deux documents seulement**, chacun compte deux
  fois: un fichier de tableau de bord au format tableur, et un rapport
  d'assemblee au format texte structure - plus les deux vidages texte de ces
  memes documents. Aucun des deux n'est une facture;
- hors ces 4 lignes et apres dedoublonnage sur le triplet (fournisseur, numero de
  facture, montant), le total tombe a **311 845,76 EUR**.

Le diagnostic "erreur d'un facteur cent" etait la bonne odeur mais le mauvais
mecanisme. Ce n'est pas une confusion centimes/euros. C'est une **regle
d'admission au corpus qui accepte comme facture tout fichier texte contenant un
nombre**. La mediane des 601 montants est de 117,32 EUR et 393 d'entre eux sont
sous 500 EUR: le corpus est majoritairement plausible, et le chiffre de tete est
fabrique par une poignee de lignes qui n'auraient jamais du y entrer.

Meme regle, meme effet sur le champ "fournisseur": sur les 149 valeurs distinctes
affichees, **103 (69 %) ne sont pas des noms de fournisseur**. On y trouve une
ligne d'en-tete de fichier tableur (une suite de noms de colonnes separes par des
virgules), des titres de note interne, le mot "TTC" seul (repete sur 94 lignes),
des montants, une adresse postale et des noms de fichiers. Reconnaitre que "TTC"
n'est pas une entreprise ne demande aucun etalon.

---

## 3. Reponses aux neuf questions posees

### 3.1 Le premier chiffre affiche est-il juste
Voir D5. **Classe 1** pour l'ordre de grandeur et pour le mecanisme.
**Classe 2** pour la valeur exacte du total de charges: reference de verite
indisponible, a confronter a l'etalon de RM-2026-0050.

### 3.2 Combien de points a traiter, en pleine charge
Seuil de la strategie: 20. Mesure: 24 / 790 / 827 / 460 / 2 175 selon la page
(detail en D1). **Classe 1** pour le depassement du seuil, qui est une propriete
de la regle d'affichage. **Classe 2** pour la question de savoir si ces
enregistrements devaient exister.

### 3.3 Combien de motifs strictement identiques
Seuil: zero. Mesure: 826, 786, 1 816, 18, 55 selon la page (detail en D2).
**Classe 1.**

### 3.4 Identite fictive sur donnees reelles
Cinq pages sur onze. Detail et liste en D4. **Classe 1.**

### 3.5 Coherence des compteurs entre eux, barre laterale et cockpit inclus
Huit contradictions mesurees, dont deux sur un seul ecran. Detail en D3.
**Classe 1.**

### 3.6 Les ecrans vides disent-ils ce qui manque et comment le construire
Resultat mitige, et le point faible est le meme partout: **aucune des onze pages
ne propose, sur un etat vide, l'action qui le remplirait.**

- `/gouvernance`, bloc "Demandes au syndic": dit ce qui manque ("aucune demande
  chargee", "la boite de demandes est prete, le registre synthetique est vide").
  C'est explicite. Mais il n'y a pas de geste propose, et le badge lateral de la
  meme page affiche 46 demandes.
- `/comptes`, tuile "Factures rapprochees 0": le zero est pose sans explication.
  La raison existe, mais ailleurs sur la page.
- `/documents/ajouter`: "0 prets" sous une barre annoncant 39 % d'avancement.
- `/gouvernance`, "Survie de l'archive": six pastilles rouges de meme niveau
  ("aucune copie de securite complete lue", "aucune cle de secours declaree"...).
  Six alertes de rang egal ne hierarchisent rien et ne disent pas par ou commencer.

**Classe 1.**

### 3.7 Les montants sont-ils formates de la meme facon partout
Non. **Trois conventions coexistent**, dont deux dans un meme premier ecran.

| Convention | Exemple observe | Ou |
|---|---|---|
| Francaise, espace + virgule + "EUR" | `21 994 060,46 EUR` | tuile de tete de `/comptes` |
| Anglaise, point decimal, sans separateur | `5285937.26 EUR`, `198.00 EUR` | cartes de la meme page, et 159 a 160 occurrences sur les deux pages factures |
| Symbole, ou aucune unite | `1 200,00 EUR` (symbole), `180,00` | `/comptes/rapprochement`, `/comptes/factures-a-revoir` |

Sur `/comptes`, la premiere et la deuxieme convention sont visibles ensemble sans
defiler. **Classe 1.**

### 3.8 Accessibilite (WCAG 2.1 AA)

**Echecs**

| # | Constat | Critere | Gravite | Correction |
|---|---|---|---|---|
| 1 | Texte blanc sur le bleu d'element actif: **4,28:1** (exige 4,5:1). Present sur les 11 pages, 2 a 5 occurrences par page: libelle 14 px, numero d'ordre 10 px a 82 % d'opacite, badge 12 px | 1.4.3 Contraste | Majeur | Assombrir le bleu d'etat actif. Un seul jeton a changer, tout le produit suit |
| 2 | **Une seule legende de tableau dans tout le produit** (le cockpit). 9 tableaux sur 10 n'en ont pas | 1.3.1 Information et relations | Majeur | Ajouter une legende par tableau |
| 3 | `/comptes/rapprochement` **n'a aucun element de tableau**: ses 827 lignes de travail sont des blocs sans entetes de colonne ni relation ligne/colonne | 1.3.1 | Critique | Structurer la liste principale, ou lui donner un role et des entetes explicites |
| 4 | Liens de navigation **237 x 42 px** (42 < 44). 825 cibles sous 44 px sur `/comptes/factures-a-revoir`, **3 137** sur `/documents/ajouter` | 2.5.5 Taille de cible | Mineur a majeur selon la page | 2 px de hauteur en plus sur la navigation; le reste decoule de D1 |
| 5 | A **1024 px** de large, `/comptes` deborde de 46 px et le bouton "Filtrer" sort de l'ecran. Aucun debordement de 360 a 980 px | 1.4.10 Redistribution | Majeur | Point de rupture manquant entre 980 et 1024 px |
| 6 | **3 157 arrets de tabulation** sur `/documents/ajouter`, 878 sur `/comptes/rapprochement`, 832 sur `/comptes/factures-a-revoir` | 2.4.3 Ordre de focus | Critique en pratique | Techniquement conforme, humainement infranchissable. Se resout avec D1 |
| 7 | Sur `/comptes/factures-a-revoir`, le texte "Action suivante" **passe sous le bouton** "Ouvrir le document protege" et sa troisieme ligne devient illisible, sur toutes les lignes du premier ecran | 1.4.4 / lisibilite | Majeur | Defaut de gabarit de cellule |
| 8 | Entetes et valeurs coupes en milieu de mot: "COMPTE" rendu en "COMPT / E", un identifiant de compte coupe sur trois lignes | 1.4.10 | Mineur | Colonnes trop etroites |

**Conformites, a porter au credit**

- **Zero controle sans nom accessible** sur les onze pages, y compris les 3 157
  controles de `/documents/ajouter`. Les etiquettes sont correctement associees.
- Un `h1` et un `main` par page, **zero saut de niveau de titre** sur les onze pages.
- `lang="fr"`, `meta viewport`, lien d'evitement avec style de focus visible.
- Aucune image porteuse de sens, donc aucun probleme de texte alternatif.
- Mise en page correcte de 360 a 980 px.
- Le bloc "Aide rapide" documente le parcours clavier et rappelle que les
  statuts ne reposent pas seulement sur la couleur.

Le bilan d'accessibilite est **le point le plus solide du produit**. Aucun de ces
echecs ne justifie a lui seul un "a refaire": les items 1, 2, 5 et 8 sont des
retouches, et les items 3, 4 et 6 disparaissent avec D1.

### 3.9 Vocabulaire incomprehensible pour un benevole non comptable

Mots et signes releves qu'un coproprietaire decouvrant le sujet ne peut pas
interpreter, avec le nombre d'occurrences quand il est significatif.

| Terme affiche | Ou | Probleme |
|---|---|---|
| **P1**, **P2** | tuiles de tete de `/comptes`, texte "Prochain geste humain" | Jamais definis nulle part sur la page. Ce sont pourtant les deux mots qui pilotent tout le tri |
| **ETAT_DEPENSES_A_FOURNIR** | titre de niveau 3 du panneau de detail de `/comptes` | Constante machine utilisee comme titre de section, en gros caractere |
| **A_CLASSER** | `/documents/ajouter`, 278 occurrences | Idem |
| MONTANT_TTC_ABSENT, DATE_FACTURE_ABSENTE, INCOHERENCE_HT, SANS_ETAT_DEPENSES | cockpit, `/comptes` | Idem. Les versions en francais existent ailleurs dans le produit: la traduction n'est pas appliquee partout |
| **622000**, **606100**, un libelle de compte en minuscules soudees | `/comptes/factures-a-revoir`, `/comptes/rapprochement` | Numeros et libelles du plan comptable, sans explication |
| **copro_simple** | `/gouvernance` | Valeur technique interne affichee comme etiquette |
| **source_of_truth=false** | 2 pages gouvernance | Expression de code, en anglais, dans une phrase francaise |
| Identifiants de piece a 12 caracteres | 5 pages | Affiches comme s'ils etaient parlants |
| "rapprochement", "grand livre", "etat des depenses", "diligence", "synthese derivee" | pages comptes | Vocabulaire metier non defini sur ces pages |

**Ce que le produit sait deja faire et n'applique pas la ou il faut:**
`/gouvernance/participants-ag` et `/gouvernance/roles-commissions` ouvrent par un
bloc "Mots utiles - definitions courtes" qui explique en une ligne chacun des
termes qu'elles emploient. C'est exactement le bon geste. Aucune des trois pages
comptes n'en a un, alors que ce sont elles qui concentrent le jargon.

**Classe 1.**

---

## 4. Autres constats notables

### 4.1 Quatre pages sur onze ne lisent aucune donnee
**Classe 1** - c'est un fait de code, pas de donnees.

`governance_atelier_ag_view.py`, `governance_cr_cs_view.py`,
`participants_ag_view.py` et `roles_commissions_view.py` exposent chacun une
fonction de construction qui ne prend que l'annee en argument et retourne un
dictionnaire ecrit en dur. Aucun acces a l'instance, au coffre ou a la base.

Les identifiants affiches sont d'ailleurs explicites: profils, lots et
resolutions y sont numerotes avec le mot "fictif" dans l'identifiant.

Deux de ces maquettes sont **incoherentes avec elles-memes**, ce qui est
remarquable pour du contenu ecrit a la main:

- `/gouvernance/atelier-ag` annonce "**3** questions a preparer" au-dessus d'un
  tableau qui en contient **2**;
- `/gouvernance/participants-ag` annonce "**2** pouvoirs recus" puis, plus bas,
  "**1** pouvoir a relire avant feuille de presence".

Si les compteurs ecrits a la main se contredisent deja, le probleme n'est pas
l'extraction.

`/gouvernance/roles-commissions` est, elle, coherente (5 / 3 / 6 / 5).

### 4.2 `/gouvernance` est une page de documentation, pas de controle
**Classe 1.**

Sur 3 222 px de haut, l'essentiel explique ce qu'est un coffre, ce qu'est un
syndicat secondaire, ce qu'est une association syndicale libre, avec des tableaux
d'exemples ecrits en dur ("cas concret / regle simple"). Deux de ses quatre
indicateurs de tete ("6 profils d'acces", "6 themes suivis") comptent des
constantes du code, pas des objets de l'instance. Le titre annonce un "tableau de
controle local"; le contenu est un memo pedagogique.

### 4.3 Textes destines a sortir du produit, casses
**Classe 1** - defaut de gabarit de texte, independant des donnees.

`/comptes/rapprochement` propose une lettre au syndic explicitement destinee a
etre copiee. Elle contient une elision fautive: *"Pouvez-vous transmettre
l'piece comptable (...) ?"* - la forme correcte etant "la piece". La ligne
d'objet et la salutation sont par ailleurs collees l'une a l'autre, et l'objet se
termine par un fragment de trois lettres tronque.

`/ag-contentieux` affiche "Separarer" pour "Separer".

Un texte que le produit invite a envoyer au syndic ne peut pas contenir de faute
de grammaire generee par gabarit.

### 4.4 Saturation de priorite
**Classe 1** pour la regle, **Classe 2** pour le compte exact.

Sur `/comptes/factures-a-revoir`, **686 des 790 lignes (87 %)** sont marquees
"Priorite haute". Une regle de priorite qui classe 87 % du volume au rang le plus
eleve ne transporte aucune information, quel que soit le contenu du corpus.

### 4.5 Documents de travail de l'outil ingeres comme pieces de copropriete
**Classe 2** pour la justesse du classement, **Classe 1** pour ce que l'ecran en
fait.

Les listes de factures et de questions d'assemblee contiennent des titres de
notes internes d'audit, des registres d'avancement au format tableur et des modes
operatoires - presentes comme "facture detectee", en "priorite haute", imputes a
un compte d'honoraires. Sur `/ag-contentieux`, sur environ 337 documents cites,
187 sont des fichiers de travail (texte structure et tableurs) plutot que des
pieces de copropriete.

L'ecran, lui, ne signale rien: il presente ces lignes exactement comme les
autres. Une page de controle qui ne distingue pas une facture d'une note de
travail ne peut pas servir de page de controle.

### 4.6 Dates hors exercice
**Classe 2** pour la justesse, **Classe 1** pour l'absence de traitement.

Sur `/comptes/factures-a-revoir`, page intitulee "exercice 2025": 694 lignes
datees de 2025, mais **54 datees de 2026**, 8 de 2024 et 2 de 2022. Certaines
portent des dates posterieures a la date de la mesure. La page les affiche et les
marque "facture hors exercice", puis les laisse dans la liste de travail de
l'exercice 2025.

### 4.7 Encombrement du bandeau superieur
**Classe 1. Defaut d'ecran.**

Sur les onze pages, le bandeau superieur affiche l'action "Choisir ma copro"
**deux fois**, sur deux lignes differentes, l'une des deux en gris tres clair, a
cote d'un ou deux boutons ronds vides. Sur `/documents/ajouter`, le titre de
niveau 1 se replie sur deux lignes dans une colonne d'environ 330 px pendant que
la moitie droite de la page reste vide, et l'indicateur "39 %" deborde de sa
carte.

### 4.8 Trente-deux feuilles de style chainees
**Classe 1. Observation technique.**

La feuille de style principale ne contient que 32 directives d'import en chaine,
consequence de la limite de 600 lignes par fichier. Chaque import est un aller-
retour supplementaire avant le premier rendu. La contrainte de taille est
respectee, mais elle est payee a l'affichage.

---

## 5. Recapitulatif du rangement en classes

**Classe 1 - tranche ici, verdict ferme (13 constats)**

D1 hauteur et densite - D2 motifs identiques - D3 compteurs contradictoires -
D4 identite fictive sur donnees reelles - D5 ordre de grandeur et regle
d'admission - 3.6 etats vides sans geste propose - 3.7 trois formats de montants -
3.8 accessibilite - 3.9 vocabulaire - 4.1 quatre pages non branchees -
4.3 textes sortants casses - 4.7 bandeau encombre - 4.8 feuilles de style chainees.

**Classe 2 - mesure publiee, justesse non tranchee (5 constats)**

| Question | Ce que l'ecran affiche | Statut |
|---|---|---|
| Le total des charges est-il juste | 21 994 060,46 EUR | Reference de verite indisponible, a confronter a l'etalon tests_ux (RM-2026-0050). L'ordre de grandeur est neanmoins classe 1 |
| Le nombre de factures a revoir est-il le bon | 827, ou 790 selon la page | Reference de verite indisponible. La contradiction entre les deux, elle, est classe 1 |
| Le nombre de documents a qualifier | 310, ou 346 selon l'endroit | Idem |
| Une facture est-elle rattachee a la bonne ligne de depenses | 0 rapprochement etabli sur 827 lignes | Reference de verite indisponible |
| Le classement des documents est-il correct | 41 % des lignes portent un champ fournisseur qui n'est pas un nom de fournisseur | Reference de verite indisponible pour le classement. Le fait que "TTC" ou une ligne d'en-tete de tableur ne soient pas des entreprises est, lui, classe 1 |

---

## 6. Captures

Repertoire: `docs/assets/audit-pages-controle-2026-09-03/`. Vingt-deux fichiers,
onze pages en fenetre de bureau (1440 x 1000) et en fenetre de telephone
(390 x 844).

**Regle de confidentialite appliquee.** Les six pages qui affichent des donnees
reelles sont archivees en version **caviardee**: le texte y est rendu illisible
par traitement typographique, tandis que les bordures, les tailles, les positions
et les rythmes de repetition restent exacts. Ces captures prouvent la densite, la
redondance, la hauteur et les chevauchements sans laisser lire un seul nom de
fournisseur, nom de fichier ou chemin local. Suffixe `-redacted`.

Les cinq pages gouvernance qui ne contiennent aucune donnee reelle sont archivees
en clair.

Aucune capture ne contient de nom de coproprietaire, de chemin local ou de nom de
fichier brut. Les constats qui reposaient sur du texte non publiable sont
enonces en mots dans le corps du present document.

---

## 7. Limites de ce controle

- L'instance `tilleul_pseudo_test` n'est pas fiable comme reference de verite. Tout
  constat de classe 2 attend RM-2026-0050.
- L'instance a bouge pendant la mesure (voir en tete). Les hauteurs de page et le
  contenu de `/ag-contentieux` sont donnes en fourchette entre les deux passages.
- Les tests de lecteur d'ecran ont ete conduits par analyse de l'arbre
  d'accessibilite et des roles, non par ecoute reelle avec NVDA ou VoiceOver. Le
  constat 3 de la section 3.8 (liste principale sans structure de tableau)
  merite une verification a l'ecoute.
- Le parcours clavier a ete mesure par denombrement des arrets de tabulation et
  par verification des styles de focus, non par parcours manuel de bout en bout.
  Sur `/documents/ajouter`, un parcours manuel complet n'etait pas praticable:
  c'est en soi le constat.
- Les onze pages ont ete ouvertes et mesurees. Aucun formulaire n'a ete soumis,
  aucun bouton d'action irreversible n'a ete active, aucune donnee n'a ete ecrite.
