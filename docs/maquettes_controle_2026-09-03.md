# Maquettes de controle - mesure du 2026-09-03

Date: 2026-09-03.
Auteur: designer UI, rang **3 de l'ordre de preuve** - la maquette reelle,
rendue et mesuree.
Rang 1 applique: [`blueprint_chaine_depot_controle.md`](./blueprint_chaine_depot_controle.md).
Corpus de reference: [`etalon_corpus_tests_ux.md`](./etalon_corpus_tests_ux.md).
Statut: **deux maquettes autonomes, rendues, mesurees en pleine charge.**
Aucune ligne de l'application n'a ete modifiee.

Fichiers, tous dans `docs/assets/maquettes-controle-2026-09-03/`:

| Fichier | Role |
|---|---|
| `maquette_controle_gouvernance.html` | ecran a creer - six voies, 55 resolutions reelles |
| `maquette_controle_comptes.html` | ecran existant - quatre voies, 700 factures |
| `cs-maquette.css` | CSS recopie de l'application, regles `COPIE` et `NOUVEAU` marquees |
| `donnees.js` | le proces-verbal du 03/07/2024 recopie de l'etalon, plus 700 factures |
| `controle.js` | moteur commun: filtre par voie, matrice, sonde `mesurer()` |
| `construire_recette.py` | reconstruit les fichiers de mesure et les 10 captures |
| `captures/` | 10 captures desktop, 716 x 695 et etats de filtre |

Ouvrir les deux `.html` dans un navigateur. Pour re-mesurer:
`python construire_recette.py --captures` depuis ce dossier.

---

## 0. Ce que cette maquette devait prouver

Trois exigences, dans l'ordre ou elles ont ete recues.

**Le filtre par voie.** Brice a fixe la cible minimale: *"si deja on peut
afficher un tableau dans lequel on peut filtrer chaque colonne independamment
des autres"*, c'est une vraie livraison. Il est donc traite comme une exigence de
premier rang. Il fonctionne reellement dans les deux maquettes; il n'est pas
dessine, il est clicable, et son effet est mesure en section 4.

**La generalisabilite.** Identifier ou il y a variation et ou il y a invariant.
Eprouve sur un second corpus, section 5.

**Ne pas etre plausible et faux.** Mesure en pleine charge, et confrontee aux
chiffres de l'audit, section 3.

Une **voie** est une colonne du tableau de controle: une source de preuve avec
son mecanisme back.

---

## 1. La correction de corpus, et ce qu'elle a change

Cette maquette a d'abord ete construite sur l'etalon publie: 34 resolutions a
l'assemblee du 21/02/2024, un devis a 18 240,00 adopte, un autre a 22 200,00
rejete. **Cet etalon est faux**, et `etalon_corpus_tests_ux.md` le refute point
par point: le proces-verbal du 21/02/2024 n'existe pas au dossier, et les deux
montants ne figurent dans aucun proces-verbal - ils viennent d'une convocation
scannee sans couche de texte, citee par une note qui renvoie a un fichier
d'extraction vide.

La maquette a ete refaite sur le seul proces-verbal reellement disponible.
Ce qu'elle affiche maintenant est recopie de l'etalon, resolution par
resolution, et la maquette le reproduit exactement:

| Mesure | Etalon | Rendu par la maquette |
|---|---:|---:|
| Resolutions numerotees | 55 | **55** |
| Adoptees | 39 | **39** |
| Rejetees | 7 | **7** |
| Portant `Pas de vote` | 8 | **8** |
| Issue non enoncee par le proces-verbal | 1 | **1** |
| Majorite non enoncee | 1 | **1** |

**Aucun montant n'est invente.** Le proces-verbal n'enonce de montant que pour
quatre resolutions: les comptes 2023 approuves, les honoraires de gestion, et
les budgets previsionnels 2024 et 2025. Les 51 autres affichent `-` dans la
colonne `Cout`, et la ligne de tri dit pourquoi. C'est laid, et c'est vrai.

**Consequence de conception, non prevue et importante.** La doctrine impose un
tri par montant en jeu. Sur ce corpus, **51 resolutions sur 55 n'ont aucun
montant**: le tri par montant ne trie presque rien. La maquette trie donc par
montant d'abord, **puis par gravite du constat**, et le dit dans la ligne de
compte. L'ecran s'ouvre par consequent sur la resolution 28, budget previsionnel
2024, 280 000,00 EUR, dont le proces-verbal n'enonce jamais l'issue. C'est a la
fois la ligne la plus chere et le constat le plus grave, et c'est un hasard
heureux du corpus, pas une regle: **sur un corpus ou les deux ne coincident pas,
il faudra choisir**, et c'est l'arbitrage A de la section 7.

---

## 2. Le verdict de disposition, tranche par la mesure

`CC-IT-031` a mesure quatre colonnes a **155,3 px** a 716 px de fenetre, et
`CC-IT-039/040/041` ont du raccourcir trois fois pour y tenir. 155,3 px est donc
la limite basse eprouvee, pas une preference.

Mesure a **716 x 695**, instruments de recette masques, pleine charge:

| Disposition de la matrice | Largeur de cellule | Verdict |
|---|---:|---|
| **Deux rangees nommees de trois** | **218,1 px** | **RETENUE** - 40 % au-dessus de la limite |
| Une rangee de six | 106,1 px | ECHEC - 32 % **sous** la limite |
| Cinq en rangee, execution hors matrice | 128,5 px | ECHEC - 17 % **sous** la limite |

Les memes trois dispositions a **1440 x 900**: 347,7 px, 170,9 px, 206,2 px.
**Les trois passent en desktop.** C'est le point important: la mesure desktop ne
tranche rien, et un designer qui n'aurait teste qu'en desktop aurait valide la
rangee unique de six. C'est la mesure a 716 px qui tranche, exactement comme
`CC-IT-031`.

**Verdict: deux rangees nommees de trois**, `Ce qui autorisait` puis
`Ce qui a ete engage`. L'arbitrage **C** de la section 6 du blueprint est clos
par le chiffre. L'ordre des six voies reste stable, la lecture reste de gauche a
droite, et la coupure separe le mandat de son execution - les deux missions de
l'article 21.

### 2.1 Cible de recette a 716 x 695

| Mesure | Cible | Gouvernance | Comptes |
|---|---|---:|---:|
| Hauteur de l'en-tete de travail | au plus 61 px | **61** | **61** |
| Haut de la matrice | sous 520 px | 521 - **manque de 1 px** | **482** |
| Haut de `Action immediate` | premier ecran | 361 | 361 |
| Largeur de cellule | au moins 155,3 px | **218,1** | **162,1** |
| Scroll horizontal de la page | aucun | non | non |
| Identifiant technique visible | aucun | aucun | aucun |
| Hauteur totale de page | - | 2 605 px (3,75 ecrans) | 2 224 px (3,20 ecrans) |

**Le pixel manquant est assume et explique.** La matrice de gouvernance est a
501 px quand la phrase d'action tient sur une ligne, et a 521 px quand elle en
prend deux. Sur la ligne ouverte par defaut, cette phrase est
`Les trois lignes de vote figurent au proces-verbal, la phrase d'issue non.
Conclure a l'adoption ajouterait au document ce qu'il ne dit pas.` C'est la
phrase la plus importante de l'ecran. Elle a ete raccourcie une fois, ce qui n'a
pas change le point de retour a la ligne, et elle n'a pas ete raccourcie
davantage pour gagner un pixel. La matrice reste entierement dans le premier
ecran, 521 px sur 695 px de hauteur utile.

### 2.2 Desktop 1440 x 900 et etroit 360 x 800

| Mesure | Gouv. 1440 | Comptes 1440 | Gouv. 360 | Comptes 360 |
|---|---:|---:|---:|---:|
| En-tete de travail | 74 | 74 | 99 | 110 |
| Haut de la matrice | 383 | 383 | 781 | 663 |
| Largeur de cellule | 347,7 | 259,3 | 152,2 | 152,2 |
| Hauteur de page | 2 179 px (2,42 ecrans) | 1 951 px (2,17) | 3 725 px | 3 192 px |
| Scroll horizontal | non | non | non | non |

L'en-tete mesure 74 px en desktop contre 61 px a 716 px. La cible de 61 px de
`CC-IT-031` a ete posee a 716 px seulement; a confirmer qu'elle ne s'applique
pas en desktop, ou l'en-tete a de la place et sert la lecture.

---

## 3. Les chiffres de l'audit, en face des miens

L'audit du 2026-09-03 a mesure sur l'application reelle des defauts independants
de la qualite des donnees. Voici ce que la maquette leur oppose, a charge
comparable: 55 resolutions cote gouvernance, 700 factures regroupees en 161
depenses cote comptes.

| Defaut mesure sur l'application | Application reelle | Gouvernance | Comptes |
|---|---:|---:|---:|
| Hauteur de page | 410 000 a 418 000 px, environ 460 ecrans, sur `/documents/ajouter` ; 58 709 px sur `/ag-contentieux` | **2 605 px, 3,75 ecrans** | **2 224 px, 3,20 ecrans** |
| Elements du document | 68 003 | **1 300** | **2 637** |
| Arrets de tabulation | 3 157 ; 832 sur `/comptes/factures-a-revoir` | **32** | **25** |
| Motifs distincts | **1 seul** pour 827 lignes | **12** pour 55 | **160** pour 161 |
| Actions distinctes | 4 pour 790 lignes | 9 | 67 |
| Contraste de l'etat actif | 4,28:1 - echec | **4,66:1** | **4,66:1** |
| Identites affichees ensemble | 2 concurrentes | **1** | **1** |
| Compteurs contradictoires | 8, dont 89 et 12 sur la meme page | **0** | **0** |
| Total des charges 2025 | 21 994 060,46 affiche | - | **357 493,10** |

Cinq precisions, parce qu'un tableau qui se donne raison tout seul ne vaut rien.

**Un. La hauteur n'a pas ete gagnee par des marges.** Elle a ete gagnee en
decidant quoi montrer. Cote comptes, 700 factures sont regroupees par
fournisseur et par poste avant tout affichage: 700 pieces deviennent 161 lignes,
et chaque ligne dit combien de pieces elle porte. Le regroupement precede la
troncature, et il n'y a **aucune** troncature: le compteur affiche
`161 depenses sur 161 apres filtre`. Rien n'est cache.

**Deux. Le total est juste, et il porte sa methode.** La maquette affiche
`Total des charges 2025: 357 493,10 EUR - somme de 304 021,37 EUR de charges
courantes et de 53 471,73 EUR de travaux et operations exceptionnelles, etat
detaille des depenses du 01/01/2025 au 31/12/2025, 35 pages. Le meme ecran
affichait 21 994 060,46 EUR le 2026-09-02.` Les 700 factures synthetiques sont
mises a l'echelle pour que leur somme fasse exactement ce total: la page ne peut
donc pas afficher un total qui contredit ses propres lignes. **Un total sans sa
methode ne peut pas etre pris en defaut**, et c'est precisement ce qui a laisse
passer un facteur soixante.

**Trois. Les motifs sont distincts parce qu'ils portent le chiffre de leur
ligne.** Cote comptes, 160 motifs distincts pour 161 lignes. Cote gouvernance,
12 pour 55, et c'est correct: sur ce proces-verbal, dix paires de resolutions
`travaux / appel de fonds` decrivent la meme situation pour dix entrees
differentes, et leur donner dix phrases differentes serait de la variete
decorative. Les seuls motifs repetes sont ceux des situations reellement
identiques.

**Quatre. Les compteurs ne peuvent pas diverger par construction.** Les
indicateurs, le compteur de navigation et la ligne de compte du tableau sont
derives des memes lignes, dans la meme fonction. Le badge de navigation
`Controle gouvernance` affiche 16, qui est 7 rejetees plus 8 sans vote plus 1
sans issue enoncee: il n'est ecrit nulle part en dur. Et une page n'affiche
aucun compteur pour l'ecran qu'elle ne calcule pas, plutot qu'un tiret qui aurait
l'air d'un bug.

**Cinq. Le contraste est verifie a chaque recette, pas une fois.** La sonde
`mesurer()` recalcule le rapport reel entre le fond et le texte de l'etat actif
et le rend avec les autres mesures. `#2f73f6` donnait 4,28:1; `#2c6ee8` donne
4,66:1.

### Ce qui a ete herite et non reconstruit

Sur les points que l'audit a juges bons: `lang="fr"`, un seul `h1`, un seul
`main`, aucun saut de niveau de titre, lien d'evitement, aucun controle sans nom
accessible, mise en page tenue de 360 a 980 px. Le panneau
`Rapprochement 4 sources` n'a pas ete redessine: il est repris tel quel comme
grammaire de cellule, et la matrice de gouvernance en est la transposition.

---

## 4. Le filtre par voie, et le cas qui l'a fait changer de nature

Chaque colonne porte son propre selecteur, et les filtres se combinent sans se
gener. Le compteur dit ce qui reste, et il dit aussi ce qu'il ne montre pas.

### 4.1 Un filtre de statut ne suffisait pas

La premiere version filtrait chaque voie sur les trois statuts publics
`Source disponible` / `A confirmer` / `Source manquante`. **L'etalon a montre que
c'etait insuffisant**, et pour un motif de fond.

Sur les 55 resolutions, il y a **deux absences de sens different**:

- `Pas de vote`, 8 cas: l'assemblee n'a pas vote;
- `Issue non enoncee`, 1 cas, la resolution 28: l'assemblee **a vote**, les trois
  lignes de vote figurent au proces-verbal, et le document n'ecrit jamais la
  phrase de conclusion.

Un filtre sur la force probatoire les confond: dans les deux cas la source
existe et elle est lisible. Or c'est exactement le cas qui compte - conclure a
l'adoption sur la resolution 28 serait ajouter au document ce qu'il ne dit pas,
sur un budget de 280 000,00 EUR.

**La voie `Resolution` se filtre donc sur l'issue du vote**, quatre valeurs, et
les autres voies restent sur les trois statuts. La grammaire generale n'est pas
cassee: une voie declare la table sur laquelle elle se filtre, et le mecanisme
est le meme partout. Aucun quatrieme statut public n'a ete cree.

Les quatre issues se distinguent **par la couleur et par la forme du point**,
jamais par la couleur seule: rond plein vert pour `Adoptee`, carre plein rouge
pour `Rejetee`, rond **creux** gris-bleu pour `Pas de vote`, carre **tirete**
ambre pour `Issue non enoncee`. Aucune n'est rendue par un blanc.

La majorite suit la meme discipline: la resolution 23 n'enonce aucune majorite,
et la cellule le dit comme un constat sur le document - `Aucune majorite
enoncee`, avec la mention que seuls les membres elus votent - et non comme une
donnee absente.

### 4.2 L'effet du filtre, mesure

**Gouvernance, 55 resolutions:**

| Filtres actifs | Lignes restantes |
|---|---:|
| aucun | 55 |
| Resolution = Adoptee | 39 |
| Resolution = Pas de vote | 8 |
| Resolution = Rejetee | 7 |
| Resolution = Issue non enoncee | **1** |
| Avis du conseil = Source manquante | 30 |
| Resolution = Issue non enoncee **et** Seuil = Source disponible | **0** |
| retour a `Toutes` | 55 |

**Comptes, 161 depenses:**

| Filtres actifs | Lignes restantes |
|---|---:|
| aucun | 161 |
| Decision / devis = Source manquante | 66 |
| + Comptabilite = Source disponible | 34 |
| + Facture = Source manquante | **0** |
| retour a `Toutes` | 161 |

Le cas a zero ligne ne produit pas un ecran vide silencieux. Il affiche, en
appliquant `CC-IT-037`:

> Aucune resolution ne correspond a ce filtre. 55 resolutions existent hors de
> ce filtre. Remettez une voie sur "Toutes" pour les revoir.

Captures: `gouvernance_716x695_tableau_filtre.png`,
`gouvernance_716_tableau_lignes.png`,
`gouvernance_716x695_filtre_sans_resultat.png`,
`comptes_716x695_tableau_filtre.png`, `comptes_desktop_tableau_filtre.png`.

---

## 5. La generalisabilite, eprouvee sur un second corpus

Critere de Brice: identifier ou il y a variation et ou il y a invariant. Fait
mesure: chez un second syndic, la convocation n'a **aucun corps de resolution**;
l'ordre du jour porte l'entreprise et les devis arrivent en fichiers voisins.

La maquette porte un commutateur de corpus. Mesure a 716 x 695:

| | Syndic A - le PV porte les resolutions | Syndic B - ordre du jour seul |
|---|---:|---:|
| Largeur de cellule | 218,1 px | **218,1 px** |
| Haut de la matrice | 521 px | **521 px** |
| En-tete de travail | 61 px | **61 px** |
| Scroll horizontal | non | non |

**La grille ne bouge pas.** Ce qui bouge est le contenu de deux cellules et la
maniere dont elles le disent.

La solution est un **sixieme champ de cellule**, la `provenance`, en plus des
cinq de `CC-IT-035`. Elle dit que l'information existe, mais pas dans la piece ou
le corpus de reference la met:

> **Devis retenu** - A confirmer
> Devis dans un fichier voisin
> *Information hors de la piece de reference: 2 PDF voisins sur les 22 deposes.*
> L'ordre du jour nomme l'entreprise; le devis est un PDF depose a cote, hors
> convocation. Le rattachement est deduit du nom de l'entreprise, il n'est pas
> ecrit.

**Aucun statut supplementaire n'a ete cree.** "L'information est ailleurs" n'est
pas un degre de force probatoire, c'est un fait de provenance: la source reste
`A confirmer` parce que le rattachement est deduit et non ecrit. Un statut
`Ailleurs` aurait melange deux questions - la force de la preuve, et l'endroit ou
elle se trouve - et casse la projection exacte des trois etats de l'avis du
conseil syndical sur les trois statuts de `CC-IT-036/038`.

**Invariants confirmes sur les deux corpus:** six voies, ordre stable, trois
statuts publics, quatre issues de vote, l'absence en information de premier
niveau, le refus de conclure sur une source unique. **Variation:** la piece qui
porte l'information, et elle seule.

---

## 6. Ce que la forme homogene a coute

Les deux pages partagent la meme grammaire de cellule, le meme vocabulaire de
statut, la meme place de l'action, le meme comportement de filtre. La preuve
n'est pas une impression: **a 716 x 695, les deux pages mesurent le meme en-tete
a 61 px, la meme `Action immediate` a 361 px, et un tableau qui se comporte
identiquement.** La meme grammaire produit la meme geometrie.

Cela a coute trois choses.

**Un. La page des comptes perd son poste de travail en deux colonnes.**
L'application place aujourd'hui la file a gauche sur 430 px et le detail a
droite. La maquette empile: detail, puis tableau, sur toute la largeur. Motif
arithmetique: une file de 430 px ne peut pas porter six colonnes filtrables, et
un detail ampute de 430 px ramene les six cellules a environ 104 px **meme en
desktop**. La regle de `CC-IT-021` - la file n'enterre jamais la ligne
selectionnee - reste tenue par l'ordre de la pile et par le repli du panneau de
detail de `CC-IT-026`.

**Deux. La sixieme voie a impose les deux rangees.** La page des comptes garde
ses quatre cellules sur une rangee, la gouvernance en a deux. C'est la seule
difference de forme visible entre les deux pages, et elle est justifiee par la
mesure de la section 2.

**Trois. La voie `Resolution` sort du vocabulaire commun des trois statuts** pour
se filtrer sur les quatre issues du vote. C'est une entorse a l'homogeneite,
assumee et argumentee en 4.1: l'alternative etait de rendre le filtre aveugle au
seul cas qui compte.

**Trois defauts trouves en chemin, dont un dans l'application.**

**Un, dans l'application, a remonter.** La regle `.cs-rappro-action` est une
grille `1fr auto` sans repli etroit. A 360 px, le bouton garde sa colonne, le
texte se casse lettre a lettre, et le bloc mesure **1 740 px de haut** - il
repoussait la matrice a 2 201 px. Meme cause et meme forme que les 58 709 px de
`/ag-contentieux`. La maquette empile ce bloc sous 640 px: la matrice remonte a
663 px et la page passe de 4 656 a 3 192 px.

**Deux, dans la maquette, corrige.** Les regles de couleur des issues avaient ete
ecrites **avant** les regles de statut, a specificite egale. `Pas de vote`
s'affichait donc en vert, comme `Source disponible`. Trouve par lecture des
styles calcules, pas a l'oeil: la capture ne le montrait pas clairement.

**Trois, dans la maquette, corrige, et c'est le plus instructif.** Le panneau du
tableau declarait `grid-template-rows: auto auto minmax(0, 1fr)`, trois rangees
pour trois enfants. Quand le total de l'exercice est devenu un quatrieme enfant
cote comptes, il est tombe dans une rangee implicite, l'`overflow: hidden` l'a
rogne, et **la barre de filtres a disparu du rendu desktop** - c'est-a-dire
exactement la fonction que Brice a nommee comme la livraison. La page restait
belle et mesurait juste: en-tete 74 px, matrice 383 px, aucun scroll horizontal.
Toutes les mesures passaient, et la fonction n'etait plus la. Le panneau est
passe en colonne flexible, qui ne depend d'aucun nombre d'enfants.

Ces deux derniers disent la meme chose que l'audit sur l'application: **un ecran
peut mesurer juste et etre faux.** C'est pour cela que les captures ont ete
relues une par une apres chaque correction, et que la sonde `mesurer()` compte
desormais aussi les elements de filtre presents.

---

## 7. Arbitrages mis de cote pour Brice

**A. Le tri par montant ne trie presque rien sur ce corpus.** 51 resolutions sur
55 ne portent aucun montant au proces-verbal. La maquette trie par montant puis
par gravite du constat. Sur ce corpus les deux coincident heureusement; sur un
autre, non. **Quel est le tri par defaut quand l'euro manque?**

**B. Le regroupement ne ramene pas 700 a moins de 20.** Mesure: 700 factures
donnent **161 depenses**. Sur un corpus synthetique la distribution est
volontairement uniforme, donc 161 est une borne haute et un corpus reel sera plus
concentre. La conclusion tient quand meme: **le regroupement seul ne suffit
pas.** Ce qui rend 161 lignes travaillables, c'est le tri et le filtre par voie,
pas la troncature. Faut-il quand meme un plafond d'affichage - arbitrage E du
blueprint, encore ouvert.

**C. Le tableau defile lateralement a l'interieur de son panneau a 716 px.** Six
voies plus le cout, l'objet et l'etat demandent 940 px; quatre voies en demandent
700. La page, elle, ne defile jamais lateralement. Acceptable, ou faut-il retirer
des colonnes en largeur etroite - ce qui reviendrait a cacher des voies, donc a
cacher des absences?

**D. Le slot `provenance` et la table de filtre par voie sont deux ajouts a une
grammaire acquise par 34 iterations.** Ils sont argumentes en 4.1 et 5, mais ils
meritent un accord explicite avant tout dev.

**E. Les seuils concurrents de l'article 21.** La cellule affiche les deux
montants et nomme la concurrence comme un constat, sans trancher. Une premiere
version faisait pourtant trancher la phrase d'action, qui disait `Au-dessus du
montant arrete a 1 000 EUR`: l'affichage choisissait un montant que le back
refuse de choisir. Corrige. **Ce contournement ne resout pas la question de
droit**, il l'affiche: une depense entre 500 et 1 000 EUR reste sans reponse tant
qu'un humain ne dit pas lequel des deux montants fait foi.

**F. Les deux bases de tantiemes.** Le meme proces-verbal exprime certains votes
sur 4 899 parts et d'autres sur 10 000. La maquette **ne calcule aucun
pourcentage** pour cette raison, et le dit dans son bloc de limites. Si un ecran
doit un jour afficher un pourcentage de voix, il devra d'abord dire sur quelle
base.

**G. La navigation.** La maquette applique la decision deja prise:
`/ag-contentieux` est remplace par `Controle gouvernance` a l'entree 06, sans
vingt-sixieme entree. Les huit autres sections de `/ag-contentieux` ne sont pas
reprises et attendent leur page secondaire.

---

## 8. Conditions et limites de cette mesure

- Les mesures ont ete prises dans un **navigateur Chromium**, pas dans
  `CoproScope.exe`. `CC-IT-023` et `CC-IT-031` exigent la recette dans
  l'executable. Les valeurs a 716 x 695 devraient etre proches, mais **elles ne
  remplacent pas la recette executable**, qui reste devant.
- Le bac a sable de l'agent ne peut pas ouvrir de socket local: aucun serveur
  statique n'a pu etre lance, et le port 8791 pressenti n'a jamais ete occupe.
  Les mesures ont ete faites sur des fichiers `file://` autoportants regeneres
  par `construire_recette.py`.
- **Cote gouvernance, les donnees sont reelles**, recopiees de
  `etalon_corpus_tests_ux.md`: numeros, majorites, issues, objets et les quatre
  montants reellement enonces. Aucun nom de personne, aucun nom de fichier brut,
  aucun chemin local. **Cote comptes, les 700 factures sont synthetiques**, avec
  des fournisseurs marques `FICTIF`; seul leur total est reel.
- La maquette ne prouve pas que le back sait produire ces cellules. La voie
  `Execution` est `Source manquante` sur les 55 resolutions, et la cellule dit
  pourquoi: le lien entre un acte et un euro n'existe pas encore dans l'outil.
  C'est le trou T1 du blueprint, et c'est un etat de l'outil, pas un constat sur
  la copropriete. **Les trois etats interessants de cette cellule - `vote, rien
  de paye`, `paye plus que vote`, `paye a une autre entreprise` - n'ont donc pas
  pu etre montres sur donnees reelles**, et ne l'ont pas ete sur donnees
  inventees.
- Aucun fichier de l'application n'a ete modifie.

---

## 9. Condition d'arret

Les deux maquettes sont rendues, mesurees en pleine charge a 716 x 695, en
desktop et a 360 px, capturees en dix images. Le verdict de disposition est
chiffre. Le filtre par voie fonctionne, distingue les deux absences de sens
different, et son effet est mesure. La generalisabilite est eprouvee sur un
second corpus. Sept arbitrages sont poses pour Brice.
