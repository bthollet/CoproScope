# Audit du systeme de design - 2026-09-04

Lot `RM-2026-0083` / `CONV-2026-2135`. Methode : skill `design:design-system`, mode audit.
Perimetre : lecture seule sur tout le code. Mesures prises sur le serveur de recette
integre (port 8796) et non deduites de la feuille de style. Viewport de reference
716 x 695, controle a 360 et 1280.

Mesures brutes : [`assets/systeme-design-2026-09-04/mesures.md`](./assets/systeme-design-2026-09-04/mesures.md).

Aucune donnee nominative ne figure dans cette note ni dans ses annexes. Les captures
prises pendant l'audit ont ete caviardees a la source - flou applique sur `.cs-main`, le
bandeau de contexte, le titre et le pied de page avant declenchement - et ne sont pas
versionnees : elles ne portaient aucune information que les tableaux de mesures ne
portent pas.

---

## 1. Navigation entre deux vues d'un meme ecran

### Reponse

**Une barre d'onglets, mise en forme comme `cs-comptes-tabs`, cablee comme
`cs-reprise-tabs` : des liens serveur portant un parametre de vue, une seule vue rendue a
la fois. Cout mesure : 37 px.**

**Pas de deroulant dans le bandeau de gauche.**

### Le chiffre qui decide

Sondes injectees dans la page reelle a 716 x 695, puis retirees.

| Candidat | Hauteur au repos | Hauteur a l'ouverture | Verdict |
|---|---:|---:|---|
| `cs-comptes-tabs`, 2 vues | **37** | - | retenu |
| `<select>` dans une barre | 42 | - | 2e choix |
| `<details>` / `<summary>` | 44 | 99 | non |
| `cs-reprise-tabs`, 2 vues | 60 | - | non |
| Deroulant dans le bandeau lateral | 46 | **224 a 566** | non |

Le nombre de vues ne change rien pour les barres : a 716 px, 2 comme 3 onglets tiennent
sur une ligne. `cs-comptes-tabs` reste a 37 px, `cs-reprise-tabs` a 60 px. `cs-reprise-tabs`
paie 23 px pour un cadre blanc autour de la barre, sans rien apporter, et bascule a 106 px
des 5 onglets. `cs-comptes-tabs` n'a pas de conteneur : c'est la meme barre, nue.

### Pourquoi le deroulant lateral ne peut pas etre le motif

Trois constats mesures, pas une preference.

**Premier constat : a 716 px, il n'y a pas de bandeau de gauche.** En dessous de 980 px,
`.cs-sidebar` passe en `position: relative`, largeur 100 %, et devient une bande
horizontale au-dessus du contenu. En dessous de 720 px, sa navigation passe en
`max-height: 46px; overflow: hidden`, avec `order: -1` sur l'entree active.

A la largeur de recette, mesure sur la page reelle : la bande fait **46 px** et laisse voir
**2 entrees sur 25**. Les 23 autres sont coupees. L'entree active est l'une des deux, par
l'effet du `order: -1`. La conception s'appuierait donc sur un composant qui, au viewport
ou la recette se mesure, n'existe pas sous la forme imaginee.

**Deuxieme constat : ouvrir cette bande coute entre 224 et 566 px, et repousse le contenu
hors de l'ecran.** La bande n'est pas en surimpression : elle est dans le flux. Son
deploiement pousse tout le reste vers le bas.

| Page | Navigation deployee | Bandeau complet | Position de `.cs-main` |
|---|---:|---:|---|
| `/comptes/rapprochement` | 224 | 295 | dans l'ecran |
| `/incidents` | 566 | 637 | **y = 744**, hors du viewport de 695 |

Sur `/incidents`, ouvrir la navigation fait disparaitre la page entiere sous la ligne de
flottaison. Ajouter deux sous-entrees porte la navigation deployee de 224 a 274 px sur la
page la plus favorable : 39 % du viewport pour choisir entre deux vues qu'une barre de
37 px designe sans rien deplacer. **Le rapport est de 6 a 15 pour 1.**

**Troisieme constat : a 1280 px, ou le rail existe vraiment, il est deja sature.**

| Mesure a 1280 x 695 | Valeur |
|---|---:|
| Hauteur du rail | 1484 |
| Debordement sous la ligne de flottaison | **789** |
| Entrees atteignables sans defilement | **11 sur 25** |

Le rail fait plus du double de la hauteur disponible. Un deroulant place dedans herite de
ce defilement : le lecteur devrait faire defiler une navigation pour changer de vue dans
une page qui, elle, ne defile pas.

### La question posee : profondeur ajoutee ou profondeur servie ?

Le blueprint a decide que l'ecran de gouvernance **remplace** `/ag-contentieux` dans la
navigation plutot que de s'y ajouter. Cette decision protege un compte : 25 entrees, pas 26.

Un deroulant dans le bandeau **contredit cette decision**, et pour une raison qui n'est pas
le comptage.

La decision "remplacer plutot qu'ajouter" repose sur un principe implicite : la navigation
laterale repond a la question *ou suis-je*. Les deux vues de l'ecran de controle ne
repondent pas a cette question. Elles repondent a *qu'est-ce que je regarde en ce moment*.
Ce sont deux etats d'une meme destination, pas deux destinations.

Mettre l'etat d'un ecran dans la navigation globale fait porter deux questions au meme
composant. Le compte de 25 serait alors preserve par une astuce : cacher les sous-entrees
derriere un repli. Mais le repli n'est pas gratuit - 224 a 566 px a l'ouverture - et il
rend la navigation moins lisible pour tous les autres ecrans, qui heritent d'une profondeur
dont ils n'ont pas l'usage.

La barre d'onglets, elle, sert la decision du blueprint : une entree dans la navigation,
un ecran, deux etats affiches dans l'ecran. La navigation garde sa question.

### Forme exacte a retenir

Ne pas reprendre le cablage de `accounting.html`. Ses "onglets" sont une liste d'ancres
`#detail`, `#pieces`, `#questions`, `#rapport-ag` : les quatre panneaux sont rendus
simultanement et empiles. Mesure a 716 px : les 4 `cs-tab-panel` totalisent **2 539 px**, le
plus grand en fait 1 084. Le faux onglet coute donc **1 455 px** de page pour ne rien
masquer. C'est le plus gros gaspillage de hauteur trouve dans l'audit.

Le cablage a reprendre est celui de `_actions_reprise_syndic.html` : un `<nav>` de liens
portant `?vue=...`, `is-active` sur le courant, un seul panneau rendu par le serveur. Aucun
JavaScript, un aller-retour serveur, l'etat dans l'URL - donc partageable, mettable en
signet et compatible avec le bouton Retour.

### Budget de hauteur

L'ecran vise 520 px de matrice et la conception en cours en est a 598.

- La barre d'onglets ajoute **37 px**. Elle n'est pas la ou se joue l'ecart.
- L'en-tete depasse deja son budget de **47 px** : `.cs-topbar` mesure **108 px** a 716 px
  sur `/comptes`, `/actions` et `/incidents`, contre 61 annonces. Elle ne fait 58 px que sur
  `/comptes/rapprochement`, qui remplace le bloc de recherche. **Reprendre ce choix rend
  50 px** - plus que la barre d'onglets ne coute.
- Le poste `cs-rappro-*` etrangle sa propre matrice (voir 4.9). Liberer la file rendrait
  environ **150 px** de hauteur de matrice.

50 + 150 = 200 px disponibles sans toucher au contenu, contre 37 px de cout pour la
navigation. **L'ecart de 78 px se comble dans l'en-tete et le poste de travail, pas dans le
choix du motif de navigation.**

---

## 2. Les familles de ton

### Reponse

Il y en a **trois**, pas quatre. `cs-status-*` n'est pas une famille de ton : c'est une
famille de forme.

| Famille | Ce qu'elle fait | Usages | Sort |
|---|---|---:|---|
| `cs-card-tone-*` | fond + filet, **sans toucher a la couleur du texte** | 15 | **canonique** |
| `cs-tone-*` | fond + filet **+ couleur du texte** | 22 | amputer sa moitie couleur, fondre le reste |
| `cs-reprise-tone-*` | fond + filet, valeurs de fond derivees | 16 | morte, a fondre |
| `cs-status-dot` / `cs-status-badge` | forme : puce en `currentColor`, pastille | 8 | conserver, ce n'est pas un ton |

### Ce qu'un ecran de controle doit employer aujourd'hui

**`cs-card-tone-{ok|warn|danger|info}`** sur les surfaces - cartes, cellules de matrice,
lignes de synthese. **`cs-status-dot`** pour le marqueur de statut en ligne.

**Et jamais la composition `cs-status-dot` + `cs-tone-*`.** C'est exactement le defaut
mesure en 5.

### Pourquoi `cs-card-tone-*` et pas `cs-tone-*`

Deux raisons, dans cet ordre.

**Elle ne peut pas casser le contraste.** Valeurs calculees sur element reel :

| Classe | color | background |
|---|---|---|
| `cs-card-tone-ok` | herite, #101828 | #edfdf7 |
| `cs-tone-ok` | **#13976b** | #edfdf7 |

`cs-tone-*` impose une couleur de texte qui echoue sur son propre fond : ok 3,51:1, warn
**2,40:1**, danger 4,17:1. Seul info passe, a 5,17:1. `cs-card-tone-*` laisse le texte a
#101828 et passe partout.

**C'est la seule que les gabarits adressent depuis le domaine.** 12 des 15 usages sont
interpoles : `cs-card-tone-{{ proof.status }}`, `cs-card-tone-{{ tone_for(...) }}`. La
famille accepte directement un statut metier - `verified`, `candidate`, `missing`,
`blocked`, `draft`, `closed`, `rejected`, `sent`, `answered`, `local`, `to` - et le projette
sur l'une des quatre surfaces. Les onze modificateurs "en trop" ne sont pas du gras : ce
sont les points d'entree du domaine, et le code Python emet bien ces valeurs - `blocked`
54 fois, `missing` 53, `verified` 30, `candidate` 29.

C'est aussi ce qui explique le desordre : la famille porte **deux vocabulaires dans un seul
espace de noms** - un vocabulaire de ton, ok/warn/danger/info, et un vocabulaire de statut.
Ce n'est pas a corriger dans ce lot, mais un ecran nouveau doit le savoir : il ecrit un
statut, pas une couleur.

### Cout de la convergence

Faible, et il ferme trois defauts au passage.

1. **`cs-reprise-tone-*` : duplication pure.** Memes quatre tons, memes filets, fonds
   derives de facon imperceptible - `#f0fdf8` contre `#edfdf7` pour ok, `#fbfcff` contre
   `#eef4ff` pour info. Ajouter 4 selecteurs au groupe `cs-card-tone-*`, supprimer 4 regles
   dans `styles_part_12.css`. Aucune regression visible : l'ecart de fond est sous le seuil
   de perception.
2. **`cs-tone-*` : amputer, pas supprimer.** Sa moitie surface - `styles_part_07.css`,
   lignes 116-138 - est deja fusionnee avec `cs-card-tone-*` : les selecteurs sont groupes
   dans le meme bloc. Sa moitie couleur - `styles_part_05.css`, lignes 169-183 - est un
   second bloc, dans un autre fichier, qui n'annule rien et s'ajoute. **Supprimer ces quatre
   declarations `color:` ferme les trois echecs de contraste vivants de la page d'accueil**
   et laisse les 22 usages valides.
3. **`cs-status-badge` : declaration morte.** `styles_part_06.css` la definit ligne 386 avec
   `color: #1d5fd8`, puis la redefinit ligne 517 avec `color: #101828`, dans le meme fichier.
   La premiere ne s'applique jamais.

Total : environ 20 lignes de CSS, un remplacement de nom dans une famille de gabarits.

---

## 3. Inventaire utile - ce qu'un ecran de controle reutilise

Vingt classes, pas 354. Pour chacune : ce qu'elle fait, ou elle est definie, et un gabarit
qui l'emploie correctement.

### Structure de page

| Classe | Fait | Definie | Exemple |
|---|---|---|---|
| `cs-page-header` | titre + outils de page | `styles_part_06.css:165` | `accounting.html` |
| `cs-panel-head` | en-tete de panneau : titre + compteur a droite | `styles_part_05.css:92` | `accounting.html` |
| `cs-card-list` | grille verticale de cartes | `styles_part_06.css:456` | `accounting.html` |
| `cs-empty` | etat vide avec phrase d'action | `styles_part_06.css:367` | `accounting.html` |
| `button-link` | action primaire, cible tactile 44 px | `styles_part_01.css:417` | `accounting.html` |

### Navigation entre vues - le motif retenu

| Classe | Fait | Definie | Exemple |
|---|---|---|---|
| `cs-comptes-tabs` | barre nue, 37 px, liens 32 px min | `styles_part_07.css:318` | `accounting.html` (forme) |
| `cs-reprise-tabs` | barre encadree, 60 px, liens 38 px min | `styles_part_11.css:364` | `_actions_reprise_syndic.html` (cablage) |
| `cs-tab-panel` | panneau de vue, `aria-labelledby` | `styles_part_06.css:562` | `accounting.html` |

Prendre la forme de la premiere, le cablage de la seconde. `cs-tab-panel` sert de panneau -
a un seul exemplaire rendu a la fois, contrairement a `accounting.html`.

### Statut et ton

| Classe | Fait | Definie | Exemple |
|---|---|---|---|
| `cs-card-tone-*` | surface + filet selon statut ou ton | `styles_part_07.css:116` | `accounting.html` |
| `cs-status-dot` | puce ronde 7 px en `currentColor` + libelle gras | `styles_part_05.css:424` | `overview.html` |
| `cs-status-badge` | pastille encadree, 30 px min | `styles_part_06.css:386` | `accounting.html` |
| `cs-summary-card` | carte de synthese chiffree, cliquable | `styles_part_06.css:261` | `actions.html` |
| `cs-metric-chip` | pastille de metrique compacte | `styles_part_32.css:53` | `overview.html` |

### Poste de travail - `cs-rappro-*`, meme composant, autre jeu de cellules

| Classe | Fait | Definie |
|---|---|---|
| `cs-rappro-workbench` | grille file + matrice, `minmax(300px, 430px) 1fr` | `styles_part_30.css:1` |
| `cs-rappro-queue-panel` | rail de file collant, `top: 78px`, hauteur bornee | `styles_part_30.css:8` |
| `cs-rappro-matrix` | zone de matrice, `min-width: 0` | `styles_part_30.css:168` |
| `cs-rappro-matrix-grid` | grille de 4 colonnes egales, gouttiere 6 px | `styles_part_30.css:194` |
| `cs-rappro-source-cell` | cellule : filet superieur 4 px + etat `is-*` | `styles_part_30.css:200` |
| `cs-rappro-action` | bloc d'action, `1fr auto`, repli a 1 colonne sous 560 px | `styles_part_30.css:114` |

Gabarit de reference : `compta_rapprochement.html`.

**Reserve avant reutilisation.** `cs-rappro-workbench` fixe une file de 430 px qui ne se
replie jamais au-dessus de 980 px. Mesure : a 1280 px la matrice n'a que 438 px sur 948
disponibles, ses 4 colonnes tombent a 105 px, et la cellule monte a **277 px de haut** -
contre **127 px a 716 px**, ou la matrice a toute la largeur. **La cellule est plus haute sur
ecran large que sur ecran etroit.** Un ecran de gouvernance qui vise 520 px de matrice doit
rendre cette file repliable ou la reduire ; il gagnera environ 150 px.

Les etats de cellule sont deja nommes en dur : `.is-strong_match` - filet #13976b, fond
#f5fffb - et `.is-candidate` - filet #f28705, fond #fffaf2. Un autre jeu de cellules devra
soit reutiliser ces deux noms, soit en ajouter : ce sont des noms de domaine comptable dans
une classe de presentation.

---

## 4. Les incoherences qui coutent

Dix, chiffrees, rangees par cout. Le cout est ce que la prochaine equipe paie, pas ce que la
correction coute.

### 4.1 Deux jetons utilises et jamais definis - 38 declarations muettes

`var(--border)` et `var(--text)` sont appeles **55 fois dans 13 feuilles** et ne sont definis
nulle part. Le `:root` de `styles_part_01.css` declare 20 jetons ; ni l'un ni l'autre n'en
fait partie.

Consequence mesuree sur la page reelle : `border: 1px solid var(--border)` devient invalide
au calcul, le raccourci entier est annule, `border-style` retombe a `none`. Verifie sur
`.inc-summary`, `.inc-status`, `.inc-definitions` : **`border-top-width: 0px`**. Les cartes
que le CSS dit encadrees n'ont aucun filet.

**19 raccourcis + 19 longues = 38 declarations mortes**, sur 13 ecrans. Correction : deux
lignes dans `:root`. C'est le meilleur rapport du lot - mais il changera l'apparence de 13
ecrans d'un coup, donc il appelle une recette, pas un commit discret.

### 4.2 Dix-sept prefixes prives - 288 classes hors systeme

| Mesure | Valeur |
|---|---:|
| Classes `cs-*` distinctes | 354 |
| Classes non `cs-*` distinctes | **288** |
| Prefixes prives par ecran | **17** |

`drive-` 76, `mei-` 69, `memory-` 67, `rol-` 62, `inc-` 60, `ctr-` 52, `sug-` 49, `act-` 45,
`pag-` 42, `cpr-` 42, `agw-` 38, `travaux-` 36, `crcs-` 31, `coffre-` 28, `pilotage-` 24.

Chacune redeclare les memes primitives - `hero`, `status`, `summary`, `definitions`, `cards` -
avec les memes valeurs et le meme `var(--border)` casse. Sur 10 490 lignes de CSS, c'est la
moitie du volume.

**Le cout pour ce lot est immediat** : la coutume locale veut qu'un nouvel ecran ouvre un
18e prefixe, `gov-`. Ne pas le faire. Le nouvel ecran doit ecrire en `cs-*` et reutiliser
`cs-rappro-*`.

### 4.3 La navigation est inutilisable a la largeur de recette

A 716 px : **2 entrees visibles sur 25**, les 23 autres derriere un `max-height: 46px;
overflow: hidden` qui ne s'ouvre que sur `:hover` ou `:focus-within`.

- Pas de `<button>`, pas d'`aria-expanded`, pas de nom accessible pour le mecanisme.
- Sur ecran tactile, il n'y a **pas de `:hover`**. Le seul chemin restant est le focus, qui
  exige de tabuler dans des liens invisibles.
- L'ouverture pousse le contenu : sur `/incidents`, `.cs-main` part a y = 744 dans un
  viewport de 695.

L'audit du 2026-09-03 a conclu "mise en page tenue de 360 a 980 px". C'est vrai pour la mise
en page. **Ce n'est pas vrai pour l'atteignabilite de la navigation.**

### 4.4 L'en-tete depasse son budget de 47 px sur 3 pages sur 4

`.cs-topbar` a 716 px : **108 px** sur `/comptes`, `/actions` et `/incidents`, contre 61
annonces. 58 px seulement sur `/comptes/rapprochement`.

Cause : `.cs-search` - 38 px - passe sur sa propre ligne sous le titre - 41 px. La page qui
respecte le budget est celle qui remplace le bloc de recherche.

Et a cette largeur, `.instance-meta` et `.cs-top-action` passent en `display: none` : **le
bouton "Mode test", le selecteur de copropriete et l'action primaire de la page
disparaissent exactement au viewport ou la recette se fait.** Ils sont bien retires de
l'ordre de tabulation - ce n'est pas un defaut d'accessibilite, c'est une perte de fonction
dans la seule fenetre ou on la teste.

### 4.5 Les faux onglets de `accounting.html` - 1 455 px

Quatre `cs-tab-panel` rendus simultanement, relies par des ancres `#`. A 716 px :
245 + 1 084 + 969 + 241 = **2 539 px**. En n'affichant que le plus grand : 1 084 px. **1 455 px
de page pour un composant qui ne masque rien.**

Le nouvel ecran ne doit pas copier ce cablage. Voir 1.

### 4.6 Trois familles de ton pour quatre tons

22 + 15 + 16 = 53 usages en gabarit, pour quatre tons, repartis sur trois espaces de noms et
trois fichiers. Detail et sort en 2. Convergence : environ 20 lignes.

### 4.7 Une couche de jetons decorative

| Mesure | Valeur |
|---|---:|
| Litteraux hexadecimaux | **653** |
| Valeurs distinctes | **122** |
| Appels `var(--*)` | 314 |
| Jetons definis | 20 |

Le probleme n'est pas le ratio, c'est que **les jetons definis ne decrivent plus
l'interface**. `--accent: #1f6f64` est un vert-bleu ; `--blue: #315f9c` est un bleu grise.
L'interface vivante est bleue en **#1d5fd8**, employe **68 fois en dur**, et jamais declare
comme jeton. Le `:root` est une palette de premiere generation que le code a laissee derriere
lui.

Consequence pour ce lot : ne pas ecrire `var(--accent)` en croyant reprendre la couleur du
produit. Ecrire #1d5fd8, comme le reste, et signaler le jeton manquant.

### 4.8 Deux bleus pour le meme etat actif - et le seul echec de contraste connu

| Etat actif | Couleur | Contraste | Verdict |
|---|---|---:|---|
| Entree de navigation active | #ffffff sur **#2f73f6** | **4,28:1** | echec |
| Onglet actif `cs-reprise-tabs` | #1d5fd8 sur #eef4ff | 5,17:1 | conforme |
| Texte #1d5fd8 sur blanc | - | 5,71:1 | conforme |

Les deux disent "actif". L'un echoue, l'autre passe. **Remplacer #2f73f6 par #1d5fd8 dans
`styles_part_04.css` ferme l'echec de contraste et supprime un bleu concurrent d'un seul
geste.** Le contraste passe de 4,28 a 5,71.

### 4.9 Le poste de travail etrangle sa propre matrice

| Mesure | 716 x 695 | 1280 x 800 |
|---|---:|---:|
| Largeur de la matrice | 654 | **438** |
| Largeur de cellule | 159 | **105** |
| **Hauteur de cellule** | **127** | **277** |
| Hauteur de `cs-rappro-action` | 107 | 309 |

La file `minmax(300px, 430px)` prend 430 px fixes et ne se replie qu'en dessous de 980 px. A
1280 px, la matrice recoit 438 px sur 948 disponibles. **Le composant est plus a l'aise dans
une fenetre etroite que large.** Pour un ecran vise a 520 px de matrice, c'est environ 150 px
a recuperer.

### 4.10 Des feuilles d'ecran modifient la coque partagee

`styles_part_22.css:190` :

```
.cs-sidebar .nav:has(a.active[href*="/incidents"]) {
  grid-template-columns: repeat(2, minmax(0, 1fr));
}
```

`styles_part_19.css` fait de meme via `body.cs-shell:has(.mei-hero) .cs-sidebar`.

Une feuille d'ecran reecrit la navigation globale en se reconnaissant a l'URL de son propre
lien actif. Effet mesure : la navigation deployee a 716 px vaut **224 px sur une page et
566 px sur une autre**, pour un composant cense etre identique partout. Un ecran nouveau
herite d'une coque dont il ne peut pas predire la hauteur.

---

### Verifie et clos : `RM-2026-0067`

La regle annoncee - `.cs-rappro-action` en `1fr auto` sans repli etroit, 1 740 px de bloc et
matrice repoussee a 2 201 px a 360 px - **n'est plus reproductible.**

Mesure a 360 x 695 sur le code integre :

| Mesure | Attendu par la regle | Mesure |
|---|---:|---:|
| Colonnes de `.cs-rappro-action` | 2 | **1** |
| Hauteur du bloc | 1 740 | **180** |
| Position haute de la matrice | 2 201 | **737** |
| Debordement horizontal | - | aucun, `scrollWidth` = 360 |

Le repli existe : `@media (max-width: 560px) { .cs-rappro-action { grid-template-columns: 1fr } }`,
`styles_part_30.css:546`. `RM-2026-0067` peut etre ferme sur preuve.

Reserve : le repli est a 560 px. Entre 561 et 980 px, la colonne `auto` subsiste. Mesure a
716 px : le bloc fait 107 px et se tient. Le defaut est corrige, pas seulement deplace.

---

## 5. Accessibilite du motif retenu

Le motif retenu est **un `<nav>` de liens serveur**, pas un widget d'onglets ARIA.

### Ce que ce choix donne gratuitement

| Aspect | Comportement |
|---|---|
| Clavier | `Tab` atteint chaque vue, `Entree` l'ouvre. Comportement natif du lien. |
| Lecteur d'ecran | Annonce "lien, Synthese". `aria-label` sur le `<nav>` nomme le groupe. |
| Vue courante | `aria-current="page"` - deja la convention de `base.html`. |
| Retour arriere | Fonctionne : l'etat est dans l'URL. |
| Sans JavaScript | Fonctionne. |
| Cible tactile | 38 px pour `cs-reprise-tabs`, 32 px pour `cs-comptes-tabs`. |

**Ne pas ajouter `role="tablist"` / `role="tab"` / `aria-selected`.** Verification faite : ces
attributs n'existent nulle part dans le depot. Les 10 correspondances "role=tab" sont des
`role="table"`, et `aria-selected` a **zero occurrence**. Le motif ARIA d'onglets exige une
gestion clavier au JavaScript - fleches, `Home`/`End`, `tabindex` roulant. Le declarer sans
l'implementer produit une promesse non tenue au lecteur d'ecran. Des liens honnetes valent
mieux qu'un faux `tablist`.

### Deux points a corriger avant livraison

**Etat actif.** Utiliser #1d5fd8 sur #eef4ff, soit **5,17:1**, comme `cs-reprise-tabs`. Ne pas
reprendre le #2f73f6 de la navigation laterale : c'est le 4,28:1 connu.

**Cible tactile.** `cs-comptes-tabs` donne des liens de 32 px de haut. `@media (pointer:
coarse)` dans `styles_part_31.css` porte deja des cibles a 44 px : verifier qu'il couvre bien
ce selecteur, sinon forcer `min-height: 44px` en pointeur grossier. Le budget de 37 px passe
alors a 49 px en tactile - toujours quatre a onze fois moins que le deroulant lateral.

### L'acquis du 2026-09-03 est plus fragile qu'annonce

Balayage de contraste refait sur **tous** les noeuds texte de la page d'accueil a 716 px, fond
calcule en remontant les ancetres :

| Combinaison | Ratio | Seuil | Occurrences |
|---|---:|---:|---:|
| #ffffff sur #2f73f6 - navigation active | 4,28 | 4,5 | 1 |
| #138866 sur #eaf7f1 - pastille verte | **4,02** | 4,5 | 1 |
| #f28705 sur #fff7ed - `cs-status-dot` + `cs-tone-warn` | **2,40** | 4,5 | **3** |

**Cinq echecs sur la seule page d'accueil, trois combinaisons distinctes**, pas un seul a 4,28.
Le pire est a **2,40:1**, sur du texte de 13 px en graisse 700 - donc pas du texte large, le
seuil de 4,5 s'applique bien. Ce sont des libelles de statut dans un tableau :
`<span class="cs-status-dot cs-tone-warn">Ouvert</span>`, `overview.html` lignes 329, 339, 348.

C'est la composition exacte qu'un ecran de controle a envie d'ecrire. **Supprimer les quatre
declarations `color:` de `cs-tone-*` dans `styles_part_05.css`, lignes 169-183, ferme ces trois
occurrences** et ramene le libelle a #101828 sur son fond de ton, qui passe.

Le reste de l'acquis tient et n'est pas remis en cause : `lang="fr"`, lien d'evitement,
structure de titres, noms accessibles sur les controles.

---

## 6. Ce que je n'ai pas pu mesurer

- **Le lecteur d'ecran lui-meme.** Aucun NVDA, JAWS ou Narrateur n'a ete lance. Les
  conclusions du point 5 se deduisent de la semantique HTML et des attributs presents, pas
  d'une ecoute. A verifier en recette avant `PRET_A_INTEGRER`.
- **Le contraste sur l'ensemble des ecrans.** Le balayage complet n'a porte que sur la page
  d'accueil, plus des sondes ciblees sur `/comptes`, `/actions`, `/incidents` et
  `/comptes/rapprochement`. Les 13 ecrans a prefixe prive n'ont pas ete balayes.
- **L'effet visuel de la correction 4.1.** Definir `--border` et `--text` fera apparaitre 38
  filets absents sur 13 ecrans. Je n'ai pas evalue si ces ecrans ont ete concus, depuis, en
  s'accommodant de leur absence. La correction demande une recette visuelle, pas un commit.
- **L'ecran de gouvernance lui-meme.** Il n'existe pas encore : aucune route servie sur 8796
  ne lui correspond. Toutes les mesures de composants viennent de `/comptes/rapprochement`,
  qui est le poste de travail dont il heriterait.
- **Le comportement tactile reel.** `@media (hover: none)` et `@media (pointer: coarse)` ont
  ete lus dans le CSS, pas eprouves sur un appareil tactile. La conclusion du 4.3 - navigation
  inatteignable au doigt sous 720 px - est deduite de l'absence de `:hover` sur ces appareils.
  Elle demande une confirmation sur materiel.
- **Le repli entre 561 et 980 px pour `cs-rappro-action`.** Mesure a 360, 716 et 1280. Pas de
  balayage continu entre ces points.
