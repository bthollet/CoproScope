# Ecran de controle de gouvernance - deux vues, une source

Date: 2026-09-04.
Auteur: designer UI, lot `RM-2026-0070` / `CONV-2026-2128`.
Rang **3 de l'ordre de preuve**: maquettes reelles, rendues, mesurees en pleine
charge. Aucune ligne de l'application n'a ete modifiee.

Rang 1 applique: [`blueprint_chaine_depot_controle.md`](./blueprint_chaine_depot_controle.md).
Modele: [`modele_gouvernance_decisions.md`](./modele_gouvernance_decisions.md), sections 1 a 4.
Mesure precedente: [`maquettes_controle_2026-09-03.md`](./maquettes_controle_2026-09-03.md).
Corpus: [`etalon_corpus_tests_ux.md`](./etalon_corpus_tests_ux.md).

Fichiers, tous dans `docs/assets/synthese-gouvernance-2026-09-04/`:

| Fichier | Role |
|---|---|
| `controle_gouvernance.html` | **l'ecran retenu**: deux vues, une source, et leur lien |
| `constats.js` | **la source unique**: le predicat de filtre et les constats |
| `cs-synthese.css` | regles nouvelles, plus la copie verbatim de `cs-comptes-tabs` |
| `vue_synthese.js` | la vue qui oriente, et n'ecrit rien |
| `tableau.js` | la vue qui rapproche et modifie |
| `proposition_a_recit.html` | proposition A du premier tour - le compte rendu de l annee |
| `proposition_b_carte.html` | proposition B du premier tour - la carte de l annee |
| `proposition_c_plan.html` | proposition C, retenue par Brice, autonome |
| `proposition_tableau_decision.html` | le tableau corrige, autonome |
| `donnees_synthese.js`, `decisions.js`, `synthese.js` | corpus et derivation |
| `coque.js` | **la barre laterale reelle du produit**: 25 entrees, 3 sections |
| `cs-maquette.css` | copie inchangee du CSS du 2026-09-03 |
| `mesure.js` | sonde de mesure |
| `construire_recette.py`, `mesures.json`, `captures/` | 24 captures et toutes les mesures |

`python construire_recette.py --captures` reconstruit tout.

---

## 0. Ce qui a change depuis le premier rendu

Brice a retenu la proposition C - *"ce premier jet de mise en forme me plait
bien"* - puis a demande deux vues. Voici ce que chaque retour est devenu.

| Retour | Ce qui a ete fait | Ou le verifier |
|---|---|---|
| **1 instance = 1 copro** | Le selecteur de copropriete est **supprime** des ecrans. La preuve inter-copro se fait en **rendant les memes pages contre une autre instance**. | `synthese.js`, `instanceCourante()`; `construire_recette.py`, `INSTANCE_B` |
| **`Noter mon controle` incompris** | Trois libelles reecrits pour dire ce que l'action **fait**. | section 1.2 |
| **Incoherence comptes adoptes / demande de doc** | Trouvee, et c'etait deux incoherences. Corrigees. | section 1.3 |
| **`Sources et limites` seulement si calculable** | Le bloc est **entierement derive de comptes du coffre**. Toutes les phrases tenues a la main sont parties. | section 1.4 |
| **File groupable par type de resolution** | Type ajoute, file groupee, colonne filtrable, et **controle de seuil suspendu** hors engagement de depense. | section 1.5 |
| **Depenses sans acte: verifier le budget vote** | L'outil ne conclut plus. Il presente la matiere et rend le geste. | section 1.6 |
| **Deux vues, et le lien entre elles** | Section 2. C'est le lot. | `constats.js` |
| **Tenir compte de la barre laterale reelle** | Coque refaite a 25 entrees. **Resultat mesure inattendu**, section 3.1. | `coque.js` |
| **Forme de navigation tranchee** | `cs-comptes-tabs` en forme, `cs-reprise-tabs` en cablage, sans motif ARIA. Cout net mesure: **11 px**. | section 3.2 |
| **Un onglet inactif n'occupe rien** | Verifie par la mesure: 377 elements en synthese, 2 242 en tableau. | section 3.2 bis |
| **Tons `cs-card-tone-*` uniquement** | Seule famille employee. `cs-status-dot` + `cs-tone-warn` a 2,40:1 n'est pas ecrit. | section 3.2 ter |
| **Annotation ligne et colonne** | Parquee, notee comme cible connue, non construite. | `coque.js`, `blocNote()` |

| Retour du 2026-09-04, deuxieme passe | Ce qui a ete fait | Ou |
|---|---|---|
| Une seule vue tableau, pas une vue par constat | Un constat pose un filtre, il n'ouvre pas une page. Configuration identique quel que soit le lien. | 4.1 |
| Le titre du constat, le retour arriere, savoir ou on est | Bandeau de provenance: titre du constat, son **intention**, une puce retirable par filtre, deux sorties. | 4.1 |
| Rappel des seuils, avec Legifrance et verbatim | Trois bulles en tete de tableau, avec resolution, verbatim, article, date butoir, et une demande de validation **si et seulement si** l'extraction est incertaine. | 4.3 |
| Une colonne montant avec code couleur | Colonne montant, quatre etats, **doubles par un pictogramme et un mot**. | 4.2 |
| Urgence: deux etapes, et des controles non applicables | Avis du conseil, mise en concurrence et annexe passent a **Non exige ici**. Deux etapes nommees. Doublon supprime. | 4.4 |
| Depenses sans acte a repenser: le **marche** | La ligne devient un marche, 12 factures en 7 marches, deux questions avec article, bulles facture 1..n. | 4.5 |
| La colonne qui fonde porte plusieurs blocs; l'annexe en sous-bulle | Fait, et trois colonnes fusionnent dedans. | 4.2 |
| Fin de ligne = la decision de l'utilisateur | Colonne **Ma conclusion**, un selecteur par ligne. | 4.2 |
| Trois blocs a supprimer | Bloc copropriete en bas, bloc fixe *A faire sur cette decision*, mention des trois versions. | 4.7 |
| La vue des seuils est a refaire | Elle n'est plus une vue: rappel permanent plus un constat qui filtre les resolutions qui fixent les seuils. | 4.3 |
| La vue des decisions sans montant n'a pas de but | Chaque constat porte desormais une **intention**. Celui-la demande une saisie, pas une alerte. | 4.1 |
| Code couleur explicite | Pictogramme et mot sur le montant; le conforme a son propre ton. | 4.2 |
| Demandes au syndic a deux niveaux, et le compte qui ne collait pas | Deux niveaux. Et **l'arithmetique est affichee**: les constats se recoupent, donc leur somme depasse le nombre de lignes. | 4.9 |
| *Ce que le controle ne dit pas* est ambigu | Le mot est tranche partout: lecture automatique d'un cote, ce que j'ai verifie moi-meme de l'autre. | 4.7 |
| Libelle *resolution dont le document n'ecrit jamais le resultat* | Devient: **votes comptes, conclusion absente du document**, avec la phrase qui l'explique. | 4.6 |
| Libelle *obligation a echeance* | Disparait comme colonne; la notion passe dans ce qui la fonde. | 4.2 |
| **Deux apports metier de Brice** | Resolution adoptee sans la majorite, et resolution jamais inscrite a l'ordre du jour. Modelisees toutes les deux. | 4.6 |

## 0 bis. Relecture ligne par ligne du retour, et son etat

Methode appliquee: chaque point du retour est coche `fait`, `non applicable` ou
`pas fait`, avec sa raison. **Toutes les verifications de suppression sont faites
sur le rendu, commentaires retires** - un commentaire qui explique une
suppression compte comme une occurrence dans un grep de source, et fait croire a
un oubli qui n'existe pas, ou l'inverse.

| # | Point du retour | Etat | Ou / pourquoi |
|---|---|---|---|
| A | Une seule vue tableau, pas une vue par constat | **fait** | Un constat pose un filtre, il n'ouvre pas de page. Configuration identique quel que soit le lien. |
| A2 | Le titre du constat doit apparaitre a l'arrivee | **fait** | Bandeau de provenance, mesure a 345 px, visible sans defiler a 716 x 695. |
| A3 | Le retour arriere est difficile | **fait** | Deux sorties permanentes, mesurees a 384 et 411 px: visibles sans defiler. Plus une puce retirable par filtre. |
| A4 | La navigation doit mettre en lumiere ou on est | **fait** | Onglet actif a 213 px avec `aria-current="page"` et son compte filtre, lisible en meme temps que le titre du constat. **Reserve**: l'etat actif de la famille `cs-comptes-tabs` se distingue mal a l'oeil, defaut de famille signale au lot systeme de design. |
| B | Seuils rappeles en bulles, avec Legifrance et verbatim | **fait** | Trois bulles en tete de tableau: resolution qui l'arrete, verbatim, article, date butoir. |
| C | Une colonne montant avec code couleur | **fait** | Quatre etats, et la couleur est doublee d'un pictogramme et d'un mot. |
| D | Urgence en deux etapes, controles non applicables | **fait** | Avis du conseil, mise en concurrence et annexe passent a `Non exige ici`. Deux etapes nommees, avec les deux chemins back demandes. |
| D2 | Doublon urgence sans ratification / depense sans decision | **fait** | L'urgence est une nature de ligne, plus un constat separe. Le doublon n'existe plus. |
| E | Depenses sans acte: la ligne devient le marche | **fait** | 12 factures en 7 marches, l'absence de decision se lit dans la colonne qui fonde, l'execution porte facture 1..n. |
| E2 | Deux questions oui/non avec infobulle Legifrance | **fait** | Sur la ligne de marche, avec une troisieme reponse: je ne peux pas trancher sans la piece. |
| E3 | Cocher `depense urgente`, rattacher un mail | **fait** | Geste present sur la ligne de marche, il fait apparaitre l'etape de ratification. |
| E4 | Colonne `marche suppose` avec nom du fournisseur, et scission | **partiel** | Le libelle de ligne porte le marche. **La scission n'est pas construite** et le fournisseur n'existe pas dans le corpus - il porte le poste comptable. Les deux sont portes comme exigences back, points 4 de la section 4.8. |
| F | `Ce qui la fonde` porte plusieurs blocs | **fait** | Resolution, delegation, devis concurrents, avis du conseil selon les seuils, obligation nee apres. |
| F2 | L'annexe cesse d'etre une colonne, en sous-bulle | **fait** | Realisable, et plus juste: une annexe existe parce qu'une resolution y renvoie. La sous-bulle porte ce lien, une colonne le perdait. |
| G | Fin de ligne = la decision de l'utilisateur | **fait** | Colonne `Ma conclusion`, un selecteur par ligne - un seul arret de tabulation. |
| H | Supprimer le bloc copropriete en bas | **fait** | Verifie sur le rendu: 0 occurrence. L'identite est en haut, une seule fois. |
| H2 | Supprimer `A faire sur cette decision`, non cable | **fait** | Verifie sur le rendu: 0 occurrence. Un panneau remonte du bas quand une ligne est choisie. |
| H3 | `trois versions au coffre` n'existera pas | **fait** | Verifie sur le rendu: 0 occurrence. Le dedoublonnage est livre et integre. |
| H4 | **La copropriete doit etre nommee** | **fait** | `Residence Les Tilleuls`, nom deja employe par l'instance de demonstration du produit. Second jeu: `Residence Les Cypres`. Verifie sur le rendu: 0 occurrence de l'alias technique. |
| I | La vue des controles de seuil est a refaire | **fait** | Elle n'est plus une vue. Rappel permanent en tete, plus un constat qui filtre les resolutions qui **fixent** les seuils, avec validation du montant et de la date butoir. |
| I2 | La bulle `suspendu` seulement si l'extraction n'est pas sure | **fait** | Porte par un champ de certitude d'extraction, exige du back au point 1 de la section 4.8. |
| J | La vue des decisions sans montant n'a pas de but | **fait** | Chaque constat porte une **intention**. Celui-la demande une saisie, et l'action de ligne est devenue `Confirmer que cette resolution n'a pas de portee comptable`. |
| J2 | La colonne qui fonde n'y est peut-etre pas pertinente | **pas fait** | Ecarte volontairement: la colonne reste, parce qu'elle porte la resolution et ses annexes, qui servent a decider si la resolution a une portee comptable. La masquer par filtre demanderait des colonnes variables, ce qui reintroduirait la configuration variable que le point A interdit. |
| K | Le code couleur doit etre explicite, pictogramme | **fait** | Pictogramme et mot sur le montant, et le conforme a son propre ton. |
| L | Demandes au syndic a deux niveaux | **fait** | Niveau 1: remontees automatiques en attente de confirmation. Niveau 2: consolides. La formule rejetee est retiree. |
| L2 | **Le compte des points ne colle pas** | **fait, et il y avait bien un defaut** | Deux definitions coexistaient - un drapeau pose a la main sur chaque ligne, et le comptage des constats - qui donnaient **23 et 59 sur le meme corpus**. Une seule definition desormais, derivee des constats. Voir 4.9. |
| L3 | `Ceux qui ne demandent rien`: place douteuse | **fait** | Le bloc reste, en dernier, et ne compte plus dans les points a instruire. |
| M | `Ce que le controle ne dit pas` est ambigu | **fait** | Le mot est tranche partout, verifie sur le rendu: 0 occurrence de l'emploi ambigu. |
| R1 | `resolution dont le document n'ecrit jamais le resultat` | **fait** | Devient `votes comptes, conclusion absente du document`, avec la phrase qui l'explique. |
| R2 | `obligation a echeance` incomprehensible | **fait** | Disparait comme colonne; la notion passe dans ce qui la fonde. |
| N1 | Resolution faussement acceptee | **fait** | Modelisee, avec les voix comptees et la majorite requise. |
| N2 | Resolution jamais mise a l'ordre du jour | **fait** | Modelisee. Ce n'est pas un manque de preuve, c'est un manquement date du syndic, et la phrase le dit. |
| Q1 | Un seuil peut-il porter des conditions plus fines | **non anticipe** | Le verbatim est affiche et non resume, ce qui laisse la place a la reponse sans la prejuger. |
| Q2 | Une depense de travaux doit-elle transiter par le fonds travaux | **non anticipe** | Aucune des deux questions du marche ne parle du fonds travaux. |

---

## 1. Les six corrections de fond

### 1.1 Une instance, une copropriete

Le selecteur de copropriete que portaient les quatre pages est supprime. Il
suggerait qu'un ecran de controle choisit sa copropriete ou en compare deux, ce
que le modele produit ne fait pas.

La consigne du matin - *"soit tu me dis que tu as fait des tests inter-copro,
soit tu m'exposes une copro en manipulable"* - reste tenue, autrement: la
recette **rend les memes pages deux fois, contre deux instances**, en posant
`window.INSTANCE` avant tout script de page. Six captures viennent ainsi de la
Copropriete B. C'est la forme correcte de la preuve: le produit se relance sur
une autre instance, il ne bascule pas dans la page.

Observation faite sur le serveur integre du port 8796, page d'accueil, en
lecture seule: la barre du haut affiche `Coffre tilleul_pseudo-reconstruite-20260904`
et un bouton de bascule d'instance. Le bouton est a sa place - changer
d'instance, c'est changer de copropriete, pour toute l'application a la fois.
Mais l'identite affichee est un **nom de dossier de coffre**, pas un nom de
copropriete. C'est precisement ce que la bande d'identite de cet ecran corrige:
elle nomme la copropriete, l'exercice, l'assemblee retenue, le nombre de
decisions et l'arbitrage de version. A verifier sur la route de gouvernance
elle-meme, que je n'ai pas ouverte.

### 1.2 Les libelles disent ce que l'action fait

`Noter mon controle` a echoue exactement comme `trace du conseil syndical`:
l'utilisateur cible ne le decode pas. Le defaut de fond est le meme dans les
deux cas - le libelle nommait la **categorie** de l'action, pas son **effet**.

| Avant | Apres |
|---|---|
| `Noter mon controle` (barre du haut) | `Ecrire ce que j ai verifie` |
| `Noter ce controle apres verification` (bouton de ligne) | `Ecrire ce que j ai verifie` |
| `Ma note de controle` (panneau) | `Ce que j ai verifie moi-meme` |
| `Poser une reserve` | `Ecrire un desaccord sur cette decision` |

Le panneau dit maintenant ce que le geste produit: *ce que vous ecrivez ici est
enregistre dans votre coffre local, avec votre nom et la date; cela ne part chez
personne, cela ne conclut pas qu'une decision est reguliere, et cela ne vaut pas
preuve devant un tiers.* Et il nomme la confusion qu'il faut eviter: **a ne pas
confondre avec l'avis du conseil syndical**, qui est une piece rendue au syndic
avant une decision, et qui se demande et se rattache.

### 1.3 L'incoherence comptes adoptes - et il y en avait deux

**La premiere, la vraie.** La resolution 5 approuve les comptes de l'exercice
2023, elle est **adoptee**, elle porte 263 803,64 EUR - donc au-dessus du seuil
d'avis du conseil syndical - et la page demandait au syndic *le compte rendu du
conseil syndical consulte avant cette decision*. Reclamer une piece
d'autorisation prealable sur une resolution qui **approuve des comptes** est une
demande absurde. Et une demande absurde ne coute pas seulement elle-meme: elle
coute la credibilite de toutes les autres demandes du meme courrier.

La correction n'est pas de decider que le seuil ne s'applique pas - c'est un
point de droit en cours de verification a la source, et ce n'est pas au dessin
de le trancher. La correction est de **suspendre le controle et de le dire**:
`Controle suspendu, type a qualifier`. Ni leve, ni maintenu. Voir 1.5.

**La seconde, plus discrete.** La bande d'identite affichait *pieces tenues: 1
etat detaille des depenses de 35 pages*, et la meme page affichait, sur la
resolution 5, *annexe visee absente du dossier - la resolution renvoie a une
annexe comptable qui n'a pas ete deposee*. L'ecran tenait une piece et
paraissait la redemander. La cellule nomme maintenant l'exercice: *la resolution
approuve les comptes de l'exercice 2023 et renvoie a ses annexes; le coffre
tient l'etat detaille des depenses de 2025, pas les annexes de 2023: ce sont
deux exercices differents.*

### 1.4 `Sources et limites` ne survit que calcule

Condition acceptee telle quelle: une limite tenue a la main ment a la premiere
donnee qui change. Le bloc a donc ete audite phrase par phrase, et il ne reste
que ce qui se compte, hors ligne, sur le coffre local seul.

| Phrase de l'ancien bloc | Sort |
|---|---|
| *Le proces-verbal du 21/02/2024 n'existe pas au dossier* | **retiree** - non calculable |
| *La convocation de decembre 2025 n'est pas exploitable* | **remplacee** par `N pieces deposees n'ont aucune couche de texte` |
| *Source unique: le proces-verbal de l'assemblee du ...* | **remplacee** par `N documents lus comme proces-verbaux, M assemblees retenues, K versions ecartees` |
| *Le lien acte-euro n'existe pas encore* | **gardee**, avec son compte: `0 lien` |
| *Deux bases de tantiemes coexistent* | **gardee**, avec son compte: `2 bases` |
| Les seuils en vigueur | **gardee** - lue dans la table des seuils |
| *N decisions sans montant, N controles suspendus* | **ajoutees** - derivees des lignes |

Le bloc porte desormais sa propre garantie: *chacune de ces lignes est un compte
fait sur le coffre local, sans reseau, et refait a chaque ouverture. Aucune n'est
tenue a la main.*

### 1.5 Le type de resolution

Le type est **lu dans l'intitule** et affiche comme tel - `Approbation des
comptes`, `Election ou designation`, `Fixation d'un seuil`, `Budget
previsionnel`, `Engagement de depense`, `Autorisation a un coproprietaire`,
`Appel de fonds`, `Ordre interne de seance`. Chaque ligne du tableau porte la
mention `lu dans l'intitule`, en gris, et le lot de typage remplacera cette
valeur par une valeur etablie sur la source legale.

Il sert a trois choses, et a rien d'autre:

1. **la file de la synthese est groupee par type**, l'engagement de depense en
   premier - c'est la ou l'argent se joue;
2. **le tableau porte une colonne `Type de resolution` filtrable** comme les
   autres;
3. **le controle de seuil est suspendu** hors engagement de depense.

**Les nombres n'ont pas ete recales a la main.** Ils se sont deplaces tout
seuls, parce que le declencheur consulte maintenant le type. Et le resultat est
un constat que je n'avais pas anticipe:

> Les 13 franchissements du seuil d'avis se separent en **9** engagements de
> depense reels et **4** resolutions qui n'en sont pas: l'approbation des comptes
> 2023, l'election du syndic et ses honoraires, et les deux budgets
> previsionnels. **Aucun des franchissements de seuil au niveau des resolutions
> ne porte sur un marche.** Tous portent sur les trois cas exacts que la
> verification legale en cours a isoles.

C'est la meilleure justification du lot de typage que la maquette pouvait
produire, et elle sort de la mesure et non d'une intuition.

### 1.6 Les depenses sans acte

L'ecran affirmait `12 depenses payees qu'aucun acte connu n'autorise`. C'etait
une sur-affirmation: une depense sans acte propre peut relever du budget
previsionnel deja vote, et l'outil ne sait pas trancher - il faudrait lire le
contrat, au sens des articles 44 et 45 du decret. C'est le trou T4 du blueprint,
et il ne se referme pas par une phrase.

L'alternative acceptee est appliquee: **l'outil presente la matiere et rend le
geste.** Le libelle devient `12 depenses payees dont l'acte d'autorisation n'est
pas identifie`, l'action devient `Dire si cette depense entre dans le budget
previsionnel 2025 deja vote`, et le detail de la ligne porte un bloc
`De quoi trancher vous-meme`:

> Depense imputee au poste **Entretien et petites reparations** pour 1 914,00 EUR.
> Budget previsionnel 2025 arrete a 280 000,00 EUR par la resolution 29, adoptee.
> Entretien courant et menues reparations: couvert par ce budget. Travaux autres
> que la maintenance, amelioration, diagnostic ou consultation: articles 44 et
> 45 du decret, un vote separe etait exige.
>
> `Elle entre dans le budget vote` · `Elle exigeait un vote separe` · `Je ne peux pas trancher sans la piece`

Trois issues, dont une qui refuse de conclure. Le troisieme bouton n'est pas un
ornement: sans lui, l'ecran force un verdict que l'utilisateur n'a pas les
moyens de rendre.

---

## 2. Le lot: deux vues, et ce qui rend la divergence impossible

### 2.1 Le mecanisme, et pourquoi ce n'est pas une discipline

Le defaut numero un de ce produit est d'afficher plusieurs comptages concurrents
de la meme notion. Constate le 2026-09-02, remesure le 2026-09-03 par un audit
independant - 8 contradictions, dont 89 et 12 pour la meme notion visibles
ensemble sur une meme page - et **reproduit a l'identique sur une instance
neuve** le 2026-09-04. Il est donc dans le code.

Une regle de conduite - *"les deux vues doivent utiliser la meme source"* - ne
protege de rien: elle est vraie le jour ou on l'ecrit, et fausse au troisieme
correctif. La parade retenue est une construction:

> **La synthese ne compte rien. Elle mesure la taille d'un filtre.**

Un constat de la synthese n'est pas une phrase accompagnee d'un nombre. C'est un
**filtre nomme**, et son nombre **est** la longueur de l'ensemble que le tableau
affichera si on clique dessus:

```
mesurerConstat(s, c)  ->  appliquerFiltres(s.lignes, c.filtre).length
lignesFiltrees()      ->  appliquerFiltres(T.s.lignes, T.filtres)
```

`appliquerFiltres` est ecrit **une fois**, dans `constats.js`. La synthese
l'appelle pour produire son nombre; le tableau l'appelle pour produire ses
lignes. Il n'existe aucun second chemin de calcul a faire diverger du premier.
Faire mentir la synthese exigerait de modifier cette fonction **pour un appelant
et pas pour l'autre** - ce qu'aucune modification locale ne peut faire, puisqu'il
n'y en a qu'une.

Meme construction un cran plus bas: les colonnes filtrables ne sont declarees
qu'a un seul endroit, `CHAMPS_FILTRABLES`. Le tableau y construit ses selecteurs,
la synthese y ecrit ses constats. Ajouter une colonne sans l'ajouter la la rend
**infiltrable**, ce qui se voit a la premiere ouverture - au contraire d'un
compteur divergent, qui ne se voit jamais.

### 2.2 L'alarme, et le fait qu'elle s'est declenchee

Le lien porte le filtre **et le nombre annonce**. Le tableau compare ce nombre a
ce qu'il trouve, et affiche un bandeau rouge en cas d'ecart. Avec un predicat
unique cette comparaison ne peut pas echouer - et c'est exactement pourquoi elle
est faite: le jour ou quelqu'un introduit un second chemin de calcul, l'ecran le
dit a voix haute au lieu de mentir en silence pendant six mois.

**Elle s'est declenchee pendant la construction, et elle avait raison.** Le
premier script de recette retapait l'URL a la main avec `n=13`, le nombre des
franchissements de seuil. Le constat clique etait `au-dessus du seuil ET sans
avis du conseil`, qui en vaut 9. Le script de recette etait lui-meme le second
chemin de calcul que le dispositif existe pour attraper. Corrige: la recette
**suit le lien que la synthese a produit**, comme le ferait un clic.

La capture `vues_alarme_divergence.png` conserve l'alarme, declenchee par une
divergence simulee.

### 2.3 Le contrat de liaison, point par point

**De la synthese vers le tableau.** Chaque constat est un lien qui emporte son
filtre, son nombre et son identifiant. Le tableau pose le filtre, **le nomme en
toutes lettres** dans un bandeau d'arrivee - *9 lignes, le nombre annonce par la
synthese. Filtre pose: Seuils franchis = Au-dessus du seuil d'avis ; Avis du
conseil syndical = Source manquante* - et offre deux sorties: `Retirer le filtre`
et `Revenir a la synthese`. L'utilisateur ne peut pas ignorer ce qu'il regarde.

**Du tableau vers la synthese: quand les nombres changent.** Choix retenu, et il
porte sur deux questions distinctes.

*Ce qu'une trace change.* Une reserve, une note, un rattachement confirme
marquent la ligne `traite`. Ils ne la **retirent jamais** du constat. Le constat
garde son nombre et gagne un second nombre: `9, dont 3 deja traites par vous`.
Motif tire directement du modele: plusieurs assertions concurrentes coexistent
sur le meme objet - le syndic affirme, CoproScope calcule, un humain confirme ou
contredit. Une note humaine n'efface pas ce que la machine a lu. Et
operationnellement, un constat qui disparait parce que quelqu'un a ecrit trois
mots est un compteur qu'on peut vider sans rien corriger.

*Quand le recalcul a lieu.* **A l'entree dans la vue synthese**, pas sur un
geste explicite. Les trois options se defendaient; celle-ci est retenue parce
qu'une synthese perimee est exactement le defaut qu'on combat - deux nombres
vrais a deux instants differents produisent la meme contradiction a l'ecran que
deux nombres faux. Un bouton `rafraichir` aurait rendu la fraicheur optionnelle.
Et le recalcul est bon marche: il porte sur les lignes deja en memoire.

**L'etat survit-il a un aller-retour.** Oui, **par construction**: il vit dans
l'URL. C'est la grammaire du produit - `_actions_reprise_syndic.html` porte
deja ses onglets en `?tab=`. Un filtre pose, un aller en synthese, un retour: le
filtre est toujours la, parce qu'il n'a jamais quitte l'adresse. La bascule de
vue reconduit d'ailleurs le filtre dans les deux sens.

**Ce qui appartient a quelle vue.** La frontiere, et c'est elle qui justifie deux
vues plutot qu'une page longue:

> **La synthese agit sur l'ensemble et jamais sur une ligne.
> Le tableau agit sur une ligne et jamais sur l'ensemble.**

Appliquee, elle a deplace des choses. `Constituer la demande au syndic` est une
action d'ensemble - un seul courrier pour tous les points ouverts - elle reste
en synthese. `Ecrire ce que j'ai verifie`, `Ecrire un desaccord`, et le bloc
`De quoi trancher vous-meme` sont des actions de ligne: **elles ont ete retirees
de la synthese et vivent dans le tableau**. Aucun bouton de la vue synthese
n'ecrit dans le coffre; elle ne contient que des liens.

Cette frontiere a un effet de bord utile sur la hauteur: la matiere n'est plus
repetee sur onze lignes de la file, ce qui rendait la page a 4 101 px.

---

## 3. Les mesures

Chrome sans interface, corpus complet, 24 captures, toutes les valeurs dans
`mesures.json`.

### 3.1 La barre laterale reelle - et une surprise

Les maquettes precedentes portaient une barre de 5 entrees. La barre reelle,
recopiee de `web/templates/base.html` et confirmee sur le serveur integre du
port 8796, en porte **25, en 3 sections**. La coque a ete refaite a l'identique.

**Le resultat contredit l'attente, et dans le bon sens.** A 716 px, la barre
laterale du produit ne s'empile pas: elle devient une **barre horizontale d'une
seule ligne, a defilement**, comportement voulu par `CC-IT-023`. Vingt-cinq
entrees y coutent donc exactement la meme hauteur que cinq - et **moins** que la
maquette precedente, dont les 5 entrees se repartissaient sur deux lignes.

| Mesure a 716 x 695 | Coque de 5 entrees | Coque reelle de 25 |
|---|---:|---:|
| Haut de la matrice, vue tableau seule | 598 px | **565 px** |
| Arrets de tabulation, page tableau | 24 | 43 |

La mesure de 598 px n'etait donc pas optimiste en hauteur: elle etait
**pessimiste**. Elle l'etait en revanche sur le clavier - la barre reelle ajoute
19 arrets de tabulation avant le contenu, sur toutes les pages du produit. En
desktop, la barre est une colonne de gauche que la maquette portait deja: les
mesures a 1440 px sont inchangees.

### 3.2 La bascule: forme tranchee, et ce qu'elle coute reellement

La forme est **`cs-comptes-tabs`, cablee comme `cs-reprise-tabs`** - des liens
qui portent l'etat dans l'adresse. Verdict de mesure du coordinateur, applique
tel quel: 37 px au repos, la moins chere des cinq candidates.

**Ce que je n'ecris pas, et pourquoi.** Ni `role="tablist"`, ni `role="tab"`,
ni `aria-selected`. Le depot n'en contient zero occurrence - la mesure a ete
refaite: les dix presumees etaient des `role="table"`. Et le motif ARIA complet
exige une gestion clavier en JavaScript - fleches, Home/Fin, `tabindex` roulant -
qui ne sera pas ecrite. **Un motif ARIA a moitie implemente est pire que pas de
motif du tout**: il promet au lecteur d'ecran un comportement qui n'existe pas.
Des liens dans un `nav` nomme donnent nativement le clavier, l'annonce, et
l'ouverture dans un nouvel onglet. `aria-current="page"` marque l'actif, comme
partout ailleurs dans le depot.

**Le cout net est de 11 px, pas de 37.** La barre pese bien 36 px mesures, mais
son installation a paye 25 px en supprimant une repetition qu'elle a rendue
visible.

| Mesure a 716 x 695 | Cible | Avant bascule | Avec la barre d'onglets |
|---|---|---:|---:|
| Hauteur de l'en-tete de travail | au plus 61 px | 52 | **52** |
| Hauteur de la barre d'onglets | - | - | **36** |
| Haut de la matrice, vue tableau | sous 520 px | 565 | **576** |
| Haut de la matrice, arrivee depuis un constat | sous 520 px | 626 | 633 |
| Largeur de cellule | au moins 155,3 px | 213,0 | **213,0** |
| Filtres de colonne visibles | 10 | 10 | **10** |
| Scroll horizontal | aucun | non | non |

**Les 25 px rendus.** L'identite de la decision selectionnee etait enoncee
**trois fois** avant la matrice: dans l'en-tete de travail, dans le resume du
panneau depliable, puis dans le bloc d'action. C'est la repetition que Brice
reprochait deja au tableau, et elle coutait de la hauteur au premier ecran. Il
n'en reste qu'un enonce, dans l'en-tete de travail, qui porte maintenant le
titre de la decision et sa ligne de contexte - nature, source, montant avec son
role. S'y ajoutent trois economies de mise en page dans le poste de travail:
marge interne du panneau de detail a 12 px au lieu de 18, lignes de resume
devenues vides effacees par `:empty`, matrice collee a l'action qu'elle
documente.

**Un essai mesure et abandonne**, garde parce qu'il est contre-intuitif: placer
la bascule dans le slot droit de l'en-tete de travail economise sa rangee de
48 px. Elle retrecit alors la colonne du titre, le titre de la decision passe
sur trois lignes, et l'en-tete monte a **113 px**. Le placement econome coute
65 px de plus qu'il n'en rend. La bascule garde sa propre rangee.

**L'ecart residuel a 520 px est de 56 px**, et il faut etre precis sur son
sort. Les 200 px de credit identifies par l'audit - 50 px en remplacant le bloc
de recherche de l'en-tete, environ 150 px en desserrant le poste `cs-rappro-*` -
sont dans **l'application**, pas dans cette maquette. La maquette a un en-tete
deja au plancher et un poste de travail qui n'a rendu que 25 px parce qu'il
etait deja serre. Je ne peux pas depenser un credit qui ne m'appartient pas.
Ce que cette mesure etablit, c'est donc un **plancher**: la barre d'onglets
coute 11 px nets, et l'application qui appliquera ses deux reprises passera
sous 520 px avec les onglets installes. La cible n'est pas atteinte ici, elle
est atteignable la-bas, et le chiffre a soustraire est connu.

### 3.2 bis Un onglet inactif n'occupe rien

Defaut a ne pas heriter, mesure sur `accounting.html`: ses quatre panneaux sont
**empiles et tous rendus**, 1 455 px dont un panneau de 1 084 px. Ce ne sont pas
des onglets, ce sont des ancres qui font defiler.

La preuve que je ne l'ai pas reproduit est dans la mesure, et elle est nette:

| Vue rendue | Elements du document |
|---|---:|
| Synthese | **377** |
| Tableau | **2 242** |

Une seule vue est construite a la fois. La vue inactive n'existe pas dans le
document: elle n'occupe ni hauteur, ni memoire, ni arret de tabulation. C'est
la consequence directe du cablage `cs-reprise-tabs` - l'etat est dans l'adresse,
donc le serveur ne rend que la vue demandee - et c'est la raison pour laquelle
la forme `cs-comptes-tabs` avec le cablage `cs-reprise-tabs` etait le bon
mariage, plutot que la forme et le cablage d'`accounting.html`.

### 3.2 ter Les tons de couleur

Une seule famille est employee: **`cs-card-tone-*`**, sur les cartes de constat
et sur les blocs de recit. C'est la seule qui ne touche jamais la couleur du
**texte** - elle ne pose qu'une bordure gauche et un fond - donc la seule qui ne
peut pas casser un contraste par composition.

`cs-tone-*` n'apparait nulle part dans le balisage de ces maquettes, et la
composition `cs-status-dot` + `cs-tone-warn`, mesuree a **2,40:1**, n'est pas
ecrite. Elle etait pourtant exactement ce qu'un ecran de controle a envie
d'ecrire, et c'est ce qui la rend dangereuse: un ecran qui signale des defauts
attire les tons d'avertissement, et c'est precisement ce ton-la qui echoue.

Les couleurs restantes qui ne viennent pas de cette famille sont des
**encodages de donnee** et non des tons de carte: les barres de l'histogramme
de seuils et les tuiles du mur. Aucune ne porte de texte sur son aplat.

### 3.2 quater Ce que la refonte du tableau a change dans les mesures

Six colonnes au lieu de huit, une seule configuration de page, et les actions
sorties des cellules. Mesure a 716 x 695, corpus complet, 62 lignes.

| Mesure | Avant refonte | Apres refonte |
|---|---:|---:|
| Hauteur de la page, vue tableau | 2 787 px | **1908 px** |
| En ecrans | 4,01 | **2.75** |
| Haut du tableau | - | 470 px |
| Arrets de tabulation, vue tableau | 304 | **110** |
| Arrets de tabulation, vue synthese | - | 44 |
| Elements du document, vue tableau | - | 2708 |

**Les 304 arrets de tabulation etaient un defaut que la mesure seule a revele.**
Chaque bulle portait son lien et son bouton, chaque ligne portait trois boutons
de conclusion: 62 lignes faisaient trois cents obstacles au clavier avant la fin
du tableau. Deux corrections, et une regle qui en sort:

- **le tableau montre, le panneau agit**: les liens et les gestes ont quitte les
  cellules pour le panneau qui remonte quand une ligne est choisie;
- **un seul arret par ligne** pour la conclusion, un selecteur au lieu de trois
  boutons - meme forme que la barre de filtres, clavier natif.

De 304 a **110**. La regle qui en sort vaut au-dela de cet ecran: dans une file
longue, une action par ligne est une action, cinq actions par ligne sont un mur.

**Un defaut de composant, trouve en deplacant le panneau.** Le panneau du tableau
portait une regle de placement absolue, heritee du poste de travail dont il
etait l'enfant. Sorti de cette grille, il remontait en deuxieme rangee et passait
**par-dessus** les onglets, l'en-tete et le rappel des seuils: ils etaient dans
le document, et invisibles a l'ecran. La sonde ne le voyait pas - elle mesurait
un en-tete de 52 px bien present. C'est la capture qui l'a montre. A remonter au
lot systeme de design: une regle de placement absolue laissee dans un composant
reutilisable est un piege pour le prochain qui le deplace.

### 3.3 Sur les deux instances

| Mesure | Copropriete A | Copropriete B |
|---|---:|---:|
| Decisions | 67 | 19 |
| Points ouverts | 31 | 16 |
| Motifs distincts | 24 | 6 |
| Haut de la matrice a 716 px | 565 | 597 |
| Copropriete nommee dans le corps | oui | oui, avec la mention `mise en situation fictive` |

La Copropriete B est une mise en situation fictive, signalee comme telle a
l'ecran. Elle existe pour une seule raison: eprouver les ecrans sur une
copropriete ou la **delegation au conseil syndical existe** - 13 890,00 EUR
cumules pour un plafond de 8 000,00 EUR, franchissement qu'aucune des six
decisions prises isolement ne montre. Sans elle, le troisieme seuil resterait un
texte.

### 3.4 Le cout au clavier, et ce qu'il tranche

| Page | Arrets de tabulation | Elements du document |
|---|---:|---:|
| Synthese, deux vues | 44 | 378 |
| Tableau, deux vues | 44 | 2 243 |
| Proposition A | 30 | 270 |
| **Proposition B, mur de tuiles** | **97** | 359 |

La barre reelle en apporte 19 a toutes. Le mur de tuiles de la proposition B en
ajoute a lui seul **53** - 67 tuiles focalisables - pour une information portee
par la couleur seule. Le verdict du premier tour tient et se durcit: le mur
merite d'exister derriere un geste explicite, jamais a l'arrivee.

---

## 4. Le tableau, refait apres l'essai utilisateur

### 4.1 Le principe qui commande tout: une seule vue tableau

Brice a releve trois fois, en naviguant, que la page d'arrivee changeait de
configuration selon le constat clique. C'etait un defaut, pas une intention, et
il commande toute cette revision.

Il n'y a plus qu'une vue tableau. Memes colonnes, meme barre de filtres, meme
comportement, quel que soit le lien d'ou l'on vient. **Un constat n'ouvre pas
une page, il pose un filtre.** Consequence directe et demandee: les filtres se
retirent un par un, et l'on remonte par degres vers la globalite.

Trois manques de navigation sont corriges au meme endroit, dans un bandeau de
provenance:

- **le titre du constat clique est affiche**, avec ce qu'il attend de vous -
  chaque constat porte desormais une **intention**, parce qu'un constat sans
  intention est une alerte qui ne demande rien;
- **chaque filtre pose est une puce retirable**, avec son libelle en clair;
- **deux sorties permanentes**: tout afficher, et revenir a la synthese.

### 4.2 Six colonnes au lieu de huit

Decision | Montant | Ce qui la fonde | Seuils franchis | Execution | Ma conclusion

**La colonne qui fonde porte plusieurs bulles**, pas un statut unique: la
resolution et, en sous-bulles, les annexes qu'elle vise; la delegation quand elle
existe; les devis concurrents; l'avis du conseil syndical quand un seuil le rend
exigible; et l'obligation nee **apres** la decision - compte rendu du conseil
devant l'assemblee, ratification d'une urgence. Trois colonnes disparaissent en
fusionnant ici: annexe visee, mise en concurrence, obligation a echeance.

L'annexe sous la resolution qui la vise etait la question posee - *est-ce
realisable ?* La reponse est oui, et c'est meme la forme la plus juste: une
annexe n'existe pas en soi, elle existe **parce qu'une resolution y renvoie**. La
sous-bulle porte ce lien; une colonne le perdait.

Obligation a echeance etait incomprehensible et disparait comme colonne. La
notion reste: c'est une obligation nee **apres** la decision, et sa place est
bien dans ce qui la fonde.

**Montant devient une colonne**, avec un code couleur explicite: rouge au-dessus
du seuil de mise en concurrence, orange au-dessus du seuil d'avis, vert en
dessous, gris quand aucun montant n'est lu. **La couleur ne porte jamais
l'information seule**: un pictogramme et un mot la doublent - au-dessus du seuil
d'avis, sous les seuils, montant non lu. Un lecteur daltonien lit la meme chose.

**Ma conclusion est en bout de ligne** - conforme, pas conforme, justificatif
manquant - et non dans un formulaire en bas de page.

### 4.3 Le rappel des seuils, en tete du tableau

Trois bulles compactes, une par seuil. Chacune s'ouvre sur sa source: **la
resolution qui l'arrete, le verbatim lu au document, l'article de loi, la date
butoir**. Le verbatim est affiche et non resume, parce qu'une resolution peut
poser des conditions plus fines qu'un montant - et cette question precise est
partie en verification, je ne l'anticipe pas.

Une bulle ne signale quelque chose **que si l'extraction n'est pas sure**. Sur la
Copropriete A, deux le sont: le seuil d'avis porte deux montants concurrents, et
le seuil de mise en concurrence a bien ete arrete mais son montant n'a pas ete
lu. Les deux affichent *a valider* et proposent trois gestes: confirmer,
corriger, ouvrir la resolution. Sur la Copropriete B les trois seuils sont surs,
et aucune bulle ne clignote.

C'est la refonte de l'ancienne vue des controles de seuil, dont le verbatim etait
juge inintelligible. Elle n'est plus une vue: c'est un rappel permanent en tete
du tableau, plus un constat qui filtre les resolutions qui **fixent** les seuils -
celles qu'il faut relire et valider, puisque ce sont elles qui arment tous les
autres controles.

### 4.4 Une urgence se controle en deux etapes, et trois controles ne s'y appliquent pas

Correction de fond. La version precedente ecrivait *absente* sur l'avis du conseil
syndical, la mise en concurrence et l'annexe d'une depense d'urgence. C'etait
faux: la loi ne les exige pas la. Elles affichent maintenant **Non exige ici**, un
statut distinct de l'absence.

Ce que l'urgence exige, elle, est en deux etapes nommees:

1. **la preuve que l'urgence a ete demandee** - qui l'a declaree, quand - par une
   piece rattachee ou, a defaut, un champ de saisie;
2. **l'assemblee de ratification**, avec deux chemins cote back: detection
   automatique de la resolution correspondante dans l'assemblee qui a suivi les
   travaux, ou, a defaut, un geste qui ouvre la recherche dans les resolutions de
   l'assemblee suivante.

L'execution y ajoute ce que la facture ne prouve pas: une **preuve d'execution**,
ou la confirmation du conseiller syndical qui est alle voir.

**Le doublon est supprime.** Une depense d'urgence sans ratification et une
depense sans decision etaient deux constats pour la meme ligne. L'urgence est
maintenant une **nature** de la ligne, pas un constat separe.

### 4.5 La ligne n'est plus une facture, c'est un marche

*S'il n'y a pas d'acte, il n'y a rien qui le fonde.* Le libelle de ligne change
donc de nature: au lieu de depense sans acte, **le marche**. Sur ce corpus, les
12 factures se regroupent en **7 marches**; l'absence de decision se lit dans la
colonne qui fonde, et la colonne execution porte autant de bulles que de factures
- facture 1, facture 2, et ainsi de suite.

La cle de regroupement du produit sera le **fournisseur**. Le corpus n'en porte
pas: il porte le poste comptable, et c'est lui qui groupe ici. Le libelle le dit -
**marche suppose** - et jamais marche.

A la place de l'ancien *budget previsionnel a verifier*, **deux questions**,
chacune avec son article et une reponse oui / non / je ne peux pas trancher:

> Cette depense releve-t-elle du budget previsionnel deja vote ?
> Cette depense correspond-elle a des travaux decides ?

Et sur la ligne, un geste **Marquer comme depense urgente**, qui rattache un
courriel ou un commentaire et fait apparaitre l'etape de ratification.

### 4.6 Deux cas metier que ni le modele ni moi n'avions vus

Ils viennent de Brice, ils sont dans les donnees, et ils sont modelises.

**La resolution marquee adoptee sans atteindre la majorite.** Ce n'est pas une
resolution rejetee: le document affirme le contraire de ce que ses propres
chiffres de vote montrent. La bulle le dit avec les nombres - 4 810 voix pour sur
10 000, la ou l'article 25 en demande plus de 5 000 - et la consequence est
propre: une depense engagee sur cette base repose sur un acte contestable.

**La resolution demandee par ecrit et jamais mise a l'ordre du jour.** Elle
n'apparaissait nulle part, puisque rien ne la portait. Elle change la **nature**
de la non-conformite: ce n'est pas une piece qui manque au dossier, c'est une
obligation du syndic qui n'a pas ete tenue. La phrase le dit ainsi, et le constat
porte son propre nom.

### 4.7 Trois blocs supprimes, et un mot tranche

Le bloc *Copropriete A* en bas de page est **supprime**: l'identite est en haut,
une seule fois, et elle nomme la copropriete. Le bloc *A faire sur cette
decision*, fixe et cable a rien, est **supprime**: un panneau remonte du bas quand
une ligne est choisie, et lui seul porte les questions et les gestes. La mention
*trois versions au coffre* **disparait**: le dedoublonnage est livre et integre,
une assemblee rend une ligne.

Et le mot **controle**, qui designait deux choses dans la page, est tranche
partout: la **lecture automatique** est ce que la machine etablit a l'integration
des pieces - le bloc des limites s'appelle desormais *Ce que la lecture
automatique n'a pas pu etablir*; **ce que j'ai verifie moi-meme** est le travail
du conseiller syndical. Les deux ne se melangent jamais.

### 4.8 Ce que cela exige du back

Verifie dans les modules d'actes du serveur au 2026-09-04.

1. **La relation de seuil unique doit disparaitre.** Un seuil est une valeur du
   referentiel portee par l'acte de portee SEUIL qui l'a arretee. Manquent le
   **type** de seuil, sa **valeur** datee, son **verbatim**, sa **date butoir** et
   surtout un **degre de certitude d'extraction**: c'est lui qui decide si l'ecran
   demande une validation ou se tait.
2. **Le declencheur est un calcul, pas un lien**, et sa place est une vue a cote
   de la vue d'acte effectif. Trou T9.
3. **Les exigences de lien doivent devenir conditionnelles** au montant, au type
   de resolution **et a la nature de l'acte**. C'est ce qui permet a une urgence
   de dire *non exige ici* sur l'avis du conseil et la mise en concurrence, au
   lieu de crier a l'absence.
4. **Un objet marche** au-dessus des factures, avec sa cle de regroupement - le
   fournisseur - et la possibilite de **scinder** un marche. Sans lui, la ligne
   reste la facture et le constat se repete autant de fois qu'il y a de pieces.
5. **Deux liens nouveaux pour l'urgence**: la declaration d'urgence, et la
   resolution de ratification dans l'assemblee suivante, avec sa recherche.
6. **Le plafond de delegation a besoin d'un cumul**, pas d'une colonne.
7. **Deux etats de resultat nouveaux**: adoptee sans atteindre la majorite, qui
   exige de stocker les voix comptees et la majorite requise; et demandee, jamais
   inscrite a l'ordre du jour, qui exige d'enregistrer les demandes d'inscription
   des coproprietaires - un objet qui n'existe pas.
8. **Un role de montant**, sans lequel tout total peut additionner un budget vote
   et une facture payee.
9. **La conclusion de l'utilisateur** par ligne, avec auteur et date, distincte de
   tout constat machine.
10. **Le lien acte vers euro** reste le trou de tete, T1, inchange.

### 4.9 Le compte qui ne collait pas

Brice a eu raison de le relever, et la cause n'est pas une erreur de calcul:
**les constats se recoupent**. Une meme ligne peut etre au-dessus du seuil et
sans conclusion de vote. La somme des constats depasse donc toujours le nombre
de lignes, et cacher ce fait fait croire a une incoherence.

La page affiche desormais les trois nombres et leur relation: combien de marques
les constats posent, sur combien de lignes distinctes, et combien de lignes en
portent plusieurs. **Le nombre de points a instruire est le nombre de lignes
distinctes**, et c'est celui-la qui commande le courrier au syndic.

Et les demandes au syndic ont deux niveaux, comme demande. Niveau 1: les
remontees automatiques **qui attendent votre confirmation** - rien ne part tant
que vous n'avez pas tranche sur la ligne. Niveau 2: les points **consolides**,
ceux que vous avez deja conclus, qui partent tels quels. La formule *ce que
personne d'autre ne peut trancher a votre place* est retiree: elle decrivait un
sentiment, pas un etat.

---

## 5. Mon verdict

**L'ecran retenu est `controle_gouvernance.html`**: la proposition C en vue
synthese, le tableau corrige en vue tableau, et entre les deux le contrat de
liaison de la section 2. Les propositions A et B restent au dossier comme
archive du premier tour, avec deux emprunts deja faits a A - la phrase de tete
calculee - et a B - les bandes de seuil, devenues les constats cliquables.

**Ce dont je suis sur.** Le mecanisme anti-divergence tient, et il tient parce
qu'il est structurel et non disciplinaire. Il s'est d'ailleurs declenche contre
son propre auteur pendant la construction, ce qui est la seule preuve qui vaille.
La frontiere entre les deux vues - l'ensemble contre la ligne - est nette,
verifiable bouton par bouton, et c'est elle qui justifie deux vues.

**Ce dont je ne suis pas sur, et qui merite d'etre attaque.** Le recalcul a
l'entree dans la vue suppose que le recalcul reste bon marche. Sur 67 lignes il
l'est. Sur 700 depenses et plusieurs exercices, il faudra le mesurer, et si le
cout devient reel, la tentation sera de mettre en cache - c'est-a-dire de
recreer un second etat. C'est la ou ce dispositif cassera, et c'est la qu'il
faudra le defendre.

**La forme de la bascule est tranchee** et je la reprends telle quelle:
`cs-comptes-tabs` en forme, `cs-reprise-tabs` en cablage. Je souscris aussi a
l'argument conceptuel qui accompagne le verdict, et je le trouve plus solide que
les mesures qui le soutiennent: la navigation laterale repond a *ou suis-je*,
mes deux vues repondent a *qu'est-ce que je regarde*. Ce sont deux etats d'une
destination, pas deux destinations - et c'est aussi pourquoi l'etat de filtre se
transporte de l'une a l'autre sans se perdre.

**Une reserve de rendu, mineure mais reelle.** L'etat actif de
`cs-comptes-tabs` ne se distingue que par une bordure a 1 px qui change de
teinte et un fond tres pale. Sur la capture a 716 px, l'onglet actif se
distingue mal de l'inactif. `aria-current="page"` regle le cas du lecteur
d'ecran, pas celui de l'oeil. Je n'ai pas invente de quatrieme style pour le
corriger - ce serait exactement la faute que le systeme de design cherche a
arreter. A remonter au lot systeme de design comme defaut de la famille, pas
comme exception de cet ecran.

---

## 6. Ce qui reste ouvert

**A. Le typage des resolutions.** Mes 9 franchissements de seuil et mes 4
controles suspendus sortent d'un type **lu dans l'intitule**. Le lot de typage
les remplacera, et le partage 9/4 bougera probablement. La conception, elle, ne
bougera pas: elle a une place pour un type etabli sur source.

**B. Deux points de droit** - l'approbation des comptes releverait d'un rapport
du conseil syndical plutot que des seuils; une exception reglementaire
existerait pour l'election du syndic. Les deux tombent exactement sur trois de
mes quatre controles suspendus. Je n'ai rien anticipe: l'ecran dit qu'il ne sait
pas.

**C. L'annotation ligne par ligne et colonne par colonne**, avec `Ce que j'ai
verifie` en agregation de ces annotations. **Cible connue, parquee**, notee dans
le bloc lui-meme, non construite. Elle touchera la frontiere entre les deux
vues: une annotation de colonne est une action d'ensemble posee depuis le
tableau, le premier objet qui ne rentre proprement dans aucune des deux moities.

**D. Le seuil de mise en concurrence de la Copropriete A**, arrete par la
resolution 27 et jamais lu. La colonne dit `Obligation non testable` sur 67
lignes: honnete et pauvre.

**E. Le total des charges affiche par la synthese**, 357 493,10 EUR, vient de
l'etalon etabli a la main et non de l'application, qui affiche encore 24,4
millions pour la meme notion. La page dit d'ou vient son chiffre et que
l'application a tort. Ce n'est pas une solution, c'est une maquette qui ne peut
pas etre branchee tant que le correctif n'est pas passe.

---

## 7. Condition d'arret

L'ecran a deux vues est rendu, capture et mesure a 716 x 695, 1440 x 900,
548 x 800 et 360 x 800, sur deux instances, avec la barre laterale reelle du
produit. Le contrat de liaison est ecrit et son alarme est capturee en action.
Les six corrections de fond sont integrees. La forme de navigation n'est pas
tranchee et son plancher est chiffre.

Aucun fichier de `server/` n'a ete modifie, aucune instance n'a ete touchee,
aucun serveur n'a ete lance ni coupe - le port 8796 a ete consulte en lecture
seule, une requete - et rien n'a ete pousse.
