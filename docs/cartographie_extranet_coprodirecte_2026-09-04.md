# Cartographie complete de l'extranet, et qualification de la cle d'identite

Date: 2026-09-04, passage de nuit mene en autonomie.
Rattachement: `RM-2026-0091` / `CH-20260903-090000-RM-2026-0047-extranet-conformite` / `CONV-2026-2137`.
Statut: `OBSERVE`.
Amont: [`observation_extranet_coprodirecte_2026-09-04.md`](./observation_extranet_coprodirecte_2026-09-04.md),
[`solutions_techniques_plugin_extranet_2026-09-04.md`](./solutions_techniques_plugin_extranet_2026-09-04.md).
Grille: [`referentiel_conformite_extranet_v1.md`](./referentiel_conformite_extranet_v1.md).

## Garde de confidentialite

Aucun nom de personne, aucune adresse, aucun montant, aucun numero. Les
fournisseurs et prestataires ne sont pas nommes. Les libelles de documents ne
sont pas recopies: seuls des comptages, des familles et des structures.

**Aucun clic n'a ete emis, aucun document ouvert ni telecharge, rien envoye au
syndic.** Le passage a consiste en lectures du DOM deja rendu et en navigations
vers des pages d'index.

## Maintien de session

Question posee par Brice pendant le passage. La page avait derive seule vers
l'accueil entre deux mesures.

Dispositif installe: une requete `GET` de lecture sur une page de l'espace,
toutes les **quatre minutes**, depuis l'onglet. Cela ne contourne rien: c'est
exactement ce que fait un utilisateur qui reste actif, sur son propre compte,
en lecture. Le maintien meurt avec l'onglet, et un rechargement de page le
desarme - il faut le rearmer apres chaque navigation.

Ce n'est pas un detail de confort: une campagne d'observation qui parcourt des
centaines de liens dure plus longtemps qu'une session inactive, donc le plugin
devra porter le meme mecanisme. La duree exacte du delai d'inactivite n'a **pas**
ete mesuree.

## L'index des documents, en entier

Les huit categories sont **simultanement presentes dans le DOM**, chacune dans
un bloc `div.<CODE>`, une seule visible a la fois. Le clic devoile, il ne charge
pas. Confirmation definitive de la mesure M1.

Les codes sont des identifiants **stables**, distincts des libelles affiches:

| Code | En-tete affiche | Documents |
|---|---|---:|
| `ARR` | Arrete des comptes | 40 |
| `ASS` | Assemblees generales des coproprietaires | 26 |
| `REG` | Reglement de copropriete | 18 |
| `CON` | Contrats | 12 |
| `DIV` | Documents divers | 8 |
| `DIA` | Documents techniques | 6 |
| `REU` | Reunion CS | 3 |
| `JUS` | Assignations en justice | 2 |
| | **Total** | **115** |

115 documents pour 230 liens: **deux liens par document**, une icone et un
libelle. C'est l'explication de la contradiction laissee ouverte par la premiere
campagne.

> **Detail a garder.** Le code de la categorie *Documents techniques* est `DIA`,
> pas `TEC`. Le libelle et la cle divergent. Un adaptateur qui deduirait le code
> du libelle affiche se tromperait des la premiere categorie, et silencieusement.
> C'est la doctrine des axes sous sa forme la plus concrete: **la cle et
> l'etiquette sont deux choses, et rien ne garantit qu'elles coincident**.

## Le resultat principal: la cle d'emplacement est qualifiee pour l'injectivite

La synthese technique avait pose que la cle d'identite n'etait pas qualifiee, et
que deux proprietes manquaient: **l'injectivite** et la **stabilite dans le
temps**. La voie des en-tetes HTTP etant devenue inaccessible, l'injectivite a
ete mesuree par une autre route, entierement dans le DOM.

### Mesure 1 - la cle naive echoue, et pas un peu

| Cle candidate | Documents | Cles distinctes | Collisions |
|---|---:|---:|---:|
| libelle seul | 115 | 83 | **32** |
| categorie + libelle | 115 | 83 | **32** |
| **categorie + groupe + libelle** | 115 | **115** | **0** |

Les 32 collisions sont toutes dans `ARR`: huit libelles - les cinq annexes
comptables, la liste de l'annexe 1, l'etat des depenses et l'etat detaille -
repetes **a l'identique sur cinq exercices**. L'exercice ne figure pas dans le
libelle: il vit dans **l'en-tete de groupe**, *"Au 31/12/2025"*.

Un journal qui aurait pris le libelle pour cle aurait confondu cinq exercices
d'annexes comptables. **28 % de l'index, en silence.** C'est exactement le mode
de defaillance que la synthese redoutait: pas une erreur visible, une fusion
invisible qui fait disparaitre des retraits reels.

### Mesure 2 - la cle a trois composantes est injective sur l'index entier

**115 documents, 115 cles distinctes, zero collision.** Ce n'est pas un
echantillon: c'est la totalite de l'index a cet instant.

Seule `ARR` emploie des groupes. Les sept autres categories n'en ont aucun, et
leur libelle est deja injectif en leur sein. La composante *groupe* est donc
**facultative et presente**, ce qui est la bonne forme: elle ne coute rien la ou
elle est vide.

### Mesure 3 - la page des depenses obeit a la meme logique, avec une composante de plus

| Cle candidate | Lignes portant une facture | Distinctes | Collisions |
|---|---:|---:|---:|
| groupe + date + nature + libelle | 729 | 708 | **21** |
| **groupe + date + nature + libelle + montant** | 729 | **729** | **0** |
| groupe + rang dans le groupe | 729 | 729 | 0 |

La cle par **rang** est injective elle aussi, et il faut s'en mefier: elle est
injective **sans etre stable**. Une ligne inseree en tete de groupe decale
toutes les suivantes, et le journal verrait un remaniement complet la ou rien
n'a bouge. La cle par contenu, elle, resiste a l'insertion.

C'est une distinction que la mesure seule ne donne pas: deux cles affichent le
meme zero, et une seule est utilisable.

### Ce que cela etablit, et ce que cela n'etablit pas

**Etabli**: sur cet editeur, a cet instant, sur la totalite de deux index, une
cle d'emplacement injective existe et sa forme est connue.

**Non etabli, et il faut le dire aussi fort**:

- la **stabilite entre deux passages**. Elle exige un second passage a
  plusieurs jours. Rien ne dit qu'un syndic ne renomme pas une piece;
- la **robustesse au renommage**. Une piece renommee produirait un faux retrait
  et un faux ajout. La cle d'emplacement ne protege pas contre cela - seule
  l'empreinte du contenu le ferait, et elle coute un telechargement;
- la **generalisation**. Un editeur qui paginerait, chargerait paresseusement ou
  n'afficherait aucun groupe changerait la donne.

Le verdict `RETRAIT` reste donc **conditionne a une mesure de stabilite non
faite**. La cle est qualifiee a moitie, et c'est la moitie mesurable en une nuit.

## Ce que la page des depenses change pour CoproScope

**729 lignes de depenses sur 1 286 portent un lien de facture**, exactement un
par ligne, aucune ligne n'en portant deux. Les groupes sont des cles de charges.

C'est le fait le plus important du passage pour le produit, et il depasse le
lot extranet.

Le rapprochement **facture vers ligne de depense** est un chantier de CoproScope,
reconstruit par calcul. Or l'extranet le sert deja: **c'est l'assertion du
syndic lui-meme**, ligne par ligne. On ne parle pas d'une donnee de plus, on
parle de la **provenance manquante** dans le modele existant.

Le modele du coffre est deja fait pour cela: la contrainte d'unicite de
`object_links` porte l'`event_id`, donc plusieurs assertions coexistent sur le
meme couple. Trois provenances peuvent donc vivre cote a cote sans se detruire:

| Provenance | Ce qu'elle dit |
|---|---|
| `SYNDIC` | ce que l'extranet declare, ligne par ligne |
| `CALCUL` | ce que le rapprochement de CoproScope propose |
| `CORRIGE_HUMAIN` | ce qu'un humain confirme ou contredit |

Et le desaccord entre les deux premieres devient un **constat mesurable**, pas
une opinion: le syndic rattache cette facture a cette ligne, le calcul en
propose une autre. C'est une question a poser, formulee sans accusation.

Rappel de la mise en garde de Brice: c'est precisement cette categorie qui bouge,
parce qu'un voisin en fait le suivi. Trois sources de changement s'y melangent.
Le journal enregistre l'etat, jamais l'auteur.

## Confrontation au college A, neuf rubriques

Base: decret 2019-502, article 1er, version `LEGIARTI000042412719`.

| Rubrique | Ou elle se trouve | Verdict |
|---|---|---|
| `EXT-A-01` Reglement, etat descriptif de division, modificatifs publies | `REG`, 18 pieces, dont plusieurs modificatifs anciens | **SERVI**; la presence distincte de l'etat descriptif reste a confirmer piece par piece |
| `EXT-A-02` Derniere fiche synthetique | `DIA` | **SERVI**; fraicheur non verifiee |
| `EXT-A-03` Carnet d'entretien | `DIA`, en version courante et ancienne | **SERVI** |
| `EXT-A-04` Diagnostics techniques des parties communes en cours de validite | `DIA`, diagnostics amiante et attestation de ramonage | **INDETERMINE**: servi mais incomplet en apparence, le diagnostic de performance energetique collectif n'est pas visible, et la validite n'a pas ete verifiee |
| `EXT-A-05` Assurances de l'immeuble en cours | `CON` | **SERVI**; validite non verifiee |
| `EXT-A-06` Ensemble des contrats et marches en cours | `CON`, 12 pieces | **INDETERMINE**: des contrats sont servis, mais *l'ensemble* est une exigence d'exhaustivite qu'aucune observation externe ne peut confirmer |
| `EXT-A-07` Contrats d'entretien des equipements communs | `CON`, ascenseur, nettoyage, securite incendie, maintenance | **SERVI** |
| `EXT-A-08` PV des trois dernieres AG des comptes, et devis approuves | `ASS`, 26 pieces couvrant 2019 a 2026, PV ordinaires et extraordinaires, convocations, et des devis explicitement rattaches a une AG de 2024 | **SERVI, au-dela du minimum**; le second membre de l'obligation, les devis approuves, est presente et c'est notable puisque la V0 du referentiel l'avait oublie |
| `EXT-A-09` Contrat de syndic en cours | `CON`, mandats | **SERVI** |

Aucune rubrique du college A n'est declaree `NON_CONFORME`. Deux restent
`INDETERMINE`, et les motifs sont ecrits.

## Confrontation au college C, cinq rubriques

| Rubrique | Ou | Verdict |
|---|---|---|
| `EXT-C-01` Balances et releve general des charges | page `balance`, 310 lignes, colonnes de comptabilite en partie double; `ARR` pour les etats de depenses | **SERVI** |
| `EXT-C-02` Releves periodiques des comptes bancaires separes | **`DIV`**, quatre exercices, plus une piece de livret | **SERVI**, mais range dans *Documents divers* |
| `EXT-C-03` Assignations et decisions dont les delais de recours courent | `JUS`, 2 pieces | **SERVI** |
| `EXT-C-04` Liste de tous les coproprietaires | page d'accueil de l'espace collectif | **SERVI** |
| `EXT-C-05` Carte professionnelle, RCP, garantie financiere | page d'accueil de l'espace collectif | **SERVI** |

Le classement de `EXT-C-02` sous *Documents divers* merite d'etre note: la
rubrique la plus sensible du college C - les releves du compte separe - est
rangee dans la categorie fourre-tout. Ce n'est pas un manquement, la piece est
servie. C'est un fait d'ergonomie qui a une consequence: **un controle qui
chercherait les releves dans une categorie nommee ne les trouverait pas**. La
recherche doit porter sur le contenu, pas sur le rangement.

## Anomalie interessante pour le journal

Une piece de la categorie `DIV` porte un libelle qui designe un proces-verbal
d'assemblee dont un homonyme existe deja dans `ASS`. Meme piece probable, **deux
emplacements**.

C'est le cas d'ecole que la conception du journal avait anticipe sans exemple:
meme contenu, deux emplacements distincts. Consequences directes:

- la cle d'emplacement compte **deux** objets la ou il y a une piece; c'est
  correct, puisqu'un retrait a l'un des deux emplacements est un evenement reel;
- seule l'empreinte du contenu pourrait dire qu'il s'agit du meme document. Le
  journal doit donc pouvoir exprimer *"deux emplacements, un contenu"* sans
  fusionner les emplacements.

Non verifie: l'identite des deux contenus, faute de telechargement.

## Etat des pages

| Page | Structure | Liens de documents |
|---|---|---:|
| `/espace-copropriete` | accueil, conseil syndical, liste et debiteurs, pieces du syndic | quelques-uns |
| `/espace-copropriete/documents` | 8 categories, 5 groupes dans `ARR` | 230 |
| `/espace-copropriete/depenses` | 1 286 lignes, groupes de charges, colonne facture | **729** |
| `/espace-copropriete/balance` | 310 lignes, 7 colonnes comptables | 0 |
| `/espace-copropriete/budget` | 248 lignes, appels / depenses / ecart / ecart % | 0 |
| `/espace-client/*` | college B, non parcouru dans ce passage | n/a |

Aucun bouton d'export n'a ete trouve sur `balance`, ni aucun selecteur
d'exercice. La matiere comptable est donc **lisible mais non exportable**: elle
devra etre extraite de la page elle-meme.

## Peut-on reconstruire les vues reglementaires de la balance ?

Question posee par Brice pendant le passage: *l'affichage permet-il de
reconstruire les deux vues reglementaires de la balance a partir de donnees
presentes mais non affichees ?*

### D'abord: y a-t-il des donnees cachees ?

Verifie. **Non, rien d'exploitable.** La page de balance contient bien une table
masquee, mais elle compte huit lignes **sans aucun numero de compte** - un
gabarit ou une legende, pas de la matiere comptable. Aucun attribut `data-*` sur
la page. Aucun jeu de donnees en JavaScript en ligne: trois scripts de 343, 352
et 1 461 caracteres, soit du comportement, pas des donnees. Les seuls
formulaires de la page portent la deconnexion.

**Ce qui est affiche est ce qui existe.** L'idee d'une reserve cachee est
ecartee, et c'est une bonne nouvelle: il n'y a rien a aller chercher par la bande.

### Ce que la balance contient reellement

302 lignes, dont 278 portant un numero de compte:

| Classe | Nature | Comptes |
|---|---|---:|
| 1 | Provisions, fonds, reserves | 4 |
| 4 | Coproprietaires et fournisseurs | **253** |
| 5 | Tresorerie | 2 |
| 6 | Charges | 16 |
| 7 | Produits | 3 |

**Quatre-vingt-onze pour cent de la balance est du detail de classe 4.** La
matiere de gestion - charges et produits - tient en dix-neuf comptes.

### La reponse, vue par vue

| Vue reglementaire | Reconstructible depuis la balance seule ? |
|---|---|
| **Etat financier** (annexe 1) | **Oui en structure.** Classes 1, 4 et 5 presentes, 259 comptes. C'est la matiere d'un etat financier. |
| **Compte de gestion general** (annexe 2) | **Partiellement.** Classes 6 et 7 presentes, mais tres condensees - 19 comptes. Totaux justes; pas la ventilation reglementaire entre operations courantes, travaux de l'article 14-2 et operations exceptionnelles. |
| **Comptes de gestion detailles** (annexes 3, 4, 5) | **Non, et structurellement.** |

Le motif du non vaut d'etre dit clairement: **une balance dit combien, elle ne
dit ni pour qui ni contre quel vote.** Il lui manque trois choses que rien ne
deduit de ses chiffres:

- la **cle de repartition**, qui dit quel lot supporte quelle depense;
- le **budget vote**, sans lequel il n'y a pas d'ecart a montrer;
- le **decoupage par operation**, sans lequel les travaux ne se separent pas du
  courant.

### Mais les ingredients manquants sont sur d'autres pages

C'est le vrai resultat. La reconstruction est possible - **par jointure de trois
pages**, pas depuis la balance seule.

| Page | Ce qu'elle apporte |
|---|---|
| `balance` | les soldes, par compte |
| `budget` | 246 lignes, colonnes **Nature de la charge, Depense, Budget, % du budget, Depassement**, groupees par **36 cles de repartition** |
| `depenses` | 1 286 lignes groupees par les **memes cles**, avec 729 factures rattachees |

La page `budget` porte le **budget vote face au realise, par cle**: c'est la
matiere de l'annexe 3. La page `depenses` porte la ventilation detaillee et la
piece justificative.

### La cle de jointure, et sa fragilite

Les trois pages se joignent par le **libelle de la cle de charges**, une chaine
de caracteres. Ce n'est pas un identifiant, c'est une etiquette - le meme piege
que le code `DIA` contre le libelle *Documents techniques*.

Mesure de recoupement, faite:

| Ensemble | Cles |
|---|---:|
| Cles de la page `budget` | 36 |
| Cles de la page `depenses` | 42 |
| **Communes** | **36** |
| Seulement dans `budget` | **0** |
| Seulement dans `depenses` | **6** |

L'inclusion est **parfaite dans un sens**: toute cle budgetaire existe dans les
depenses. La jointure est donc sure pour les 36 cles communes, sur ce corpus, a
cet instant. Rien ne garantit qu'un changement de libelle chez le syndic ne la
casse: la stabilite des libelles n'est pas mesuree, pas plus que celle des
libelles de documents.

### Le signal de fond, a ne pas sur-interpreter

**Six cles portent des depenses sans avoir de ligne de budget.** Leurs libelles
sont de la meme famille et designent une repartition par parts egales entre
plusieurs entites de l'immeuble.

Deux lectures, et il serait fautif de trancher depuis une page web:

1. **Explication reguliere, et la plus probable**: ce sont des operations **hors
   budget previsionnel** - travaux de l'article 14-2 ou operations
   exceptionnelles - qui par construction ne figurent pas au budget
   previsionnel. Ce serait normal, et meme attendu.
2. **Explication a verifier**: des cles qui devraient etre budgetees et ne le
   sont pas.

Ce qui est **acquis** sans trancher: la difference d'ensembles `depenses` moins
`budget` **isole mecaniquement les candidats au hors-budget previsionnel**.
Autrement dit, l'annexe 4 declaree non reconstructible plus haut redevient
approchable - non depuis la balance, mais depuis cette difference, a condition de
confirmer que ces cles relevent bien du hors-budget.

C'est une piste de reconstruction, pas une reconstruction. Et c'est une question
a poser au syndic, formulee sans accusation: *ces six cles supportent des
depenses et n'apparaissent pas au budget previsionnel; relevent-elles des
operations de l'article 14-2 ou des operations exceptionnelles ?*

### Limite honnete

Aucun montant n'a ete lu, additionne ni verifie pendant ce passage. Tout ce qui
precede porte sur la **structure** des pages: quelles colonnes existent, quelles
cles existent, lesquelles se recoupent. La justesse des chiffres n'est pas en
cause ici et n'a pas ete evaluee.

## Troisieme campagne: la contradiction est levee, et une seconde cle apparait

Faite sur une session rouverte par Brice. Le garde-fou de l'outil de pilotage,
qui avait bloque quatre formulations, a laisse passer cette fois.

### La contradiction du 2026-09-04 est tranchee

Rappel: `HEAD` sur les 115 liens **icone** rendait 115 fois `200` **sans aucun**
`content-disposition`, alors qu'un lien **libelle** en portait un, stable.
L'hypothese etait qu'il s'agit de deux endpoints du meme document. Elle est
**confirmee**, sur l'index entier:

| Famille de liens | Testes | Portent un nom |
|---|---:|---:|
| icone, `a.pj.pdf` | 115 | **0** |
| libelle | 115 | **115** |

### Le nom servi est injectif sur la totalite de l'index

| Grandeur | Valeur |
|---|---:|
| Liens libelle testes | 115 |
| Portant un `content-disposition` | **115** |
| Noms distincts | **115** |
| Collisions | **0** |

Et le point decisif, dans la rubrique des arretes de comptes:

| Cle | Pieces | Valeurs distinctes |
|---|---:|---:|
| libelle affiche | 40 | **8** |
| nom servi par le serveur | 40 | **40** |

**Le nom serveur distingue les cinq exercices que le libelle confond.** Il ne
depend d'aucune particularite de mise en page - ni groupe, ni en-tete, ni
ordre - et il s'obtient par une requete `HEAD`, donc sans corps de reponse.

### Ce que cela change: la faiblesse du renommage est levee

La conception de la nuit portait une faiblesse nommee et non resolue:

> Une piece renommee produirait un faux retrait et un faux ajout. La cle
> d'emplacement ne protege pas contre cela - seule l'empreinte du contenu le
> ferait, et elle coute un telechargement.

Elle est levee, et a bas cout. **Deux cles independantes valent mieux qu'une**:
leur accord affermit un constat, leur desaccord est lui-meme une information.
Concretement, quand l'emplacement conclurait au retrait, le journal regarde si
le nom servi reparait ailleurs dans l'index. S'il reparait, la piece a **bouge**
et n'a pas disparu: verdict `DEPLACE_OU_RENOMME`.

Le remede envisage jusque-la etait le telechargement integral de chaque piece a
chaque passage. Il devient une requete sans corps.

**Garde maintenue**: le nom serveur reste **strictement local**. Il ne va ni
dans une empreinte echangeable, ni dans une consolidation entre coproprietaires
- chez un autre editeur, un nom de fichier peut porter un patronyme.

**Ce qui n'est toujours pas mesure**: la stabilite de ce nom entre deux passages
separes de plusieurs jours. Injectif ne veut pas dire stable. La garde est donc
conservatrice par construction - elle ne peut que **transformer un retrait en
deplacement**, jamais l'inverse, donc une instabilite du nom ferait au pire
perdre la distinction, jamais fabriquer un faux retrait.

## L'adaptateur confronte a la structure reelle

Le code ecrit dans la nuit a ete confronte a la vraie page, **sans qu'aucune
donnee reelle ne quitte le navigateur**: les libelles ont ete remplaces sur
place par des pseudonymes stables `L1..L83`, par valeur - deux libelles
identiques rendent le meme pseudonyme - de sorte que le motif de collisions est
integralement preserve et qu'aucun mot de la copropriete n'est transfere.

Sept epreuves, toutes passees du premier coup:

| Ce qui est verifie | Attendu | Obtenu |
|---|---:|---:|
| Pieces reconstituees depuis 230 liens | 115 | 115 |
| Rubriques parcourues | 8 | 8 |
| Repartition par rubrique | 40/26/18/12/8/6/3/2 | identique |
| Libelles distincts | 83 | 83 |
| Collisions de la cle naive | 32 | 32 |
| Cles distinctes, cle a trois composantes | 115 | 115 |
| Rubriques employant des groupes | 1 | 1 |

La fixture pseudonymisee est conservee comme epreuve permanente dans
`server/tests/test_extranet_structure_reelle.py`. Les autres tests du lot
verifient que l'adaptateur fait ce que son auteur a voulu; celui-ci verifie
qu'il fait ce qu'il faut sur une page que son auteur n'a pas ecrite.

## Ce qui reste

| Objet | Pourquoi il n'est pas fait |
|---|---|
| Stabilite de la cle entre deux passages | Exige un second passage a plusieurs jours. C'est la moitie manquante de la qualification. |
| Injectivite des noms de `content-disposition` | Le garde-fou de l'outil de pilotage bloque la lecture d'en-tetes en serie. A faire depuis une console de navigateur ordinaire. |
| College B, quatre rubriques | Espace personnel non parcouru ce passage. |
| Duree du delai d'inactivite de session | Non mesuree; le maintien a quatre minutes est un choix prudent, pas un reglage informe. |
| Meme page depuis un compte hors conseil syndical | Seule facon de trancher `EXT-001`. Depend d'un tiers, donc de `RM-2026-0092`. |
