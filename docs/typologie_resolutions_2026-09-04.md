# Typologie des résolutions d'assemblée générale

Lot `RM-2026-0081` — 4 septembre 2026. Sources juridiques vérifiées sur
Légifrance à la date du 3 septembre 2026, via la plateforme PISTE.

## Synthèse

L'écran de gouvernance appliquait **tous les contrôles à toutes les
résolutions**. Sur le procès-verbal étalon de 55 résolutions, cela produisait 55
cellules « seuil : source manquante » et 55 cellules « avis du conseil syndical :
source manquante » — alors que **43 de ces 55 résolutions ne passent aucun
marché** : vingt-deux désignations de personnes, quatorze modalités de
financement, deux seuils, deux budgets, une approbation de comptes, une
autorisation donnée à un copropriétaire, une désignation de syndic.

Un constat faux ne se contente pas d'être faux. Il noie les vrais, et la liste
de travail cesse d'être lue.

Ce lot livre trois choses :

1. **une typologie de onze types de résolutions**, chacun fondé sur un article
   de loi ou de décret cité avec son identifiant Légifrance ;
2. **une matrice « type × contrôle »** qui dit, pour chaque type, quels
   contrôles s'appliquent, lesquels ne s'appliquent pas, et **pour quel motif de
   droit** ;
3. **la mesure sur les deux cabinets du corpus** : sur le procès-verbal étalon,
   43 constats de seuil sur 55 disparaissent, et 43 avis manquants sur 55.

Les quatre pistes ouvertes le 4 septembre sont tranchées par la source. L'une
d'elles s'est révélée à moitié fondée, et la moitié vraie n'était pas là où on
la cherchait — voir la section « Les quatre pistes ».

## Vocabulaire

Quelques mots reviennent. Ils sont définis une fois ici.

- **Résolution** : une question soumise au vote de l'assemblée générale, et le
  résultat de ce vote.
- **Syndicat des copropriétaires** : la personne morale que forment ensemble
  tous les copropriétaires. C'est elle qui dépense, pas le syndic.
- **Syndic** : le professionnel (ou le bénévole) qui représente et gère le
  syndicat. Il est désigné par l'assemblée.
- **Conseil syndical** : des copropriétaires élus pour assister et contrôler le
  syndic.
- **Mise en concurrence** : l'obligation de demander plusieurs devis au-delà
  d'un certain montant, montant que l'assemblée elle-même fixe.
- **Budget prévisionnel** : l'enveloppe annuelle votée d'avance pour les
  dépenses courantes.
- **Portée** : dans le modèle CoproScope, le champ qui dit **sur quoi** une
  décision porte. C'est le nom technique du « type » dont parle cette note.

## La règle de conception appliquée

**On conçoit sur des axes de généralisation, jamais sur des modalités
observées.**

Le piège est visible à l'œil nu sur le corpus. Un cabinet écrit « Élection du
syndic », l'autre « Désignation du syndic ». Un cabinet écrit « Vote du montant
des marchés et contrats à partir desquels la consultation du Conseil Syndical
est obligatoire », l'autre « Fixation du montant des marchés et contrats, à
partir duquel la consultation du conseil syndical est rendue obligatoire ».
Retenir le verbe reviendrait à apprendre un cabinet par cœur, et à se tromper au
troisième.

Ce qui ne varie pas est ce que le texte impose :

- **la fonction est nommée par la loi.** Syndic (loi art. 25 c), conseil
  syndical (loi art. 21), président de séance et scrutateurs (décret art. 15),
  représentant du syndicat secondaire (décret art. 24). Les deux cabinets
  doivent l'écrire, parce que c'est elle que l'assemblée désigne ;
- **l'objet est nommé par la loi.** « budget prévisionnel » (art. 14-1 I),
  « fonds de travaux » (art. 14-2), « mise en concurrence » (art. 21 al. 2),
  « appels de fonds » (art. 14-1 I al. 3 et décret art. 35) ;
- **la structure tranche ce que les mots laissent ambigu.** Un exercice clos
  avant la date de l'assemblée ne peut pas être un budget ; un exercice qui
  court après elle ne peut pas être une approbation de comptes. Aucun mot n'est
  requis pour cela : seulement deux dates.

Un fait mesuré qui justifie ce second temps : la qualification par mots seuls
rangeait « Modalités de recouvrement des charges » en approbation des comptes,
parce que le corps de la résolution dit « approuve » et « charges ». La
confirmation par la période close supprime ce faux positif sans rien ajouter au
vocabulaire.

**Une seconde règle, tenue partout : ne pas savoir n'est pas une raison de
classer sans suite.** Une résolution dont le type n'est pas reconnu garde tous
ses contrôles. Le doute penche du côté du contrôle.

## Deux axes, pas un

Le modèle portait déjà un champ `nature` à trois valeurs — résolution
d'assemblée, décision déléguée au conseil syndical, dépense engagée en urgence
par le syndic. Ce champ dit **d'où vient l'autorisation**.

Le type livré ici dit **sur quoi elle porte**. Ce sont deux axes distincts, et
le modèle a besoin des deux. Une décision du conseil syndical qui engage une
dépense se contrôle par sa nature — elle doit être fondée sur une délégation en
vigueur — **et** par son type — elle doit respecter le seuil de mise en
concurrence. Remplacer l'un par l'autre ferait perdre la moitié du contrôle.

Techniquement, le type est porté par le champ `portee`, qui existait déjà et
dont le vocabulaire était incomplet : quatre valeurs utiles et une valeur
fourre-tout, `ORDINAIRE`, qui portait précisément le défaut — tout ce qui n'était
pas déjà nommé arrivait sur le même plan. Aucune colonne n'a été ajoutée.

## La typologie

Onze types. Un type n'existe que s'il **change au moins un contrôle** : c'est la
discipline qui empêche cette typologie de devenir un exercice de classement.
C'est aussi pourquoi l'habilitation à agir en justice et le pouvoir d'exécution
donné au syndic sont rangés avec les modalités : ils n'ont, aujourd'hui, aucun
contrôle propre à eux.

Les sept contrôles du modèle sont : **seuil** (le montant au-delà duquel la mise
en concurrence est obligatoire), **avis du conseil syndical** (sa consultation
préalable sur un marché), **rapport du conseil syndical** (son compte rendu
annuel de mission), **devis retenu**, **annexe visée**, **exécution** (une
dépense est-elle rattachée à ce qui a été voté), **majorité**.

### 1. Désignation du syndic

- **Définition** : désigne la personne qui représente légalement le syndicat.
- **Fondement** : loi 65-557 art. 25 c (`LEGIARTI000051749507`) ; décret 67-223
  art. 11 I 4°, projet de contrat joint à la convocation
  (`LEGIARTI000053191281`).
- **Ne s'applique pas** : seuil, avis préalable, devis, exécution.
- **Motif** : l'article 21 al. 2 exclut expressément le contrat de syndic du
  seuil de mise en concurrence — il vise les marchés et contrats « autres que
  celui de syndic ». Le contrat de syndic a son propre régime, triennal et à la
  charge du conseil syndical, et ce régime n'est pas prescrit à peine
  d'irrégularité de la désignation.
- **S'applique** : majorité, annexe (le projet de contrat est une pièce de
  validité).

### 2. Désignation d'un organe

- **Définition** : désigne une personne à une fonction du syndicat autre que le
  syndic — membres et président du conseil syndical, bureau de l'assemblée,
  représentant du syndicat secondaire au conseil du syndicat principal.
- **Fondement** : loi art. 21 (`LEGIARTI000039313574`), majorité de l'art. 25 c
  (`LEGIARTI000051749507`) ; décret art. 15, bureau de l'assemblée
  (`LEGIARTI000022124075`) ; décret art. 24, représentant
  (`LEGIARTI000006488509`).
- **Ne s'applique pas** : seuil, avis préalable, devis, annexe, exécution.
- **Motif** : les deux seuils de l'article 21 al. 2 portent sur les marchés et
  les contrats. Une désignation de personne n'est ni l'un ni l'autre, n'engage
  aucun euro, et on ne consulte pas le conseil syndical sur l'élection de ses
  propres membres.
- **S'applique** : majorité.

### 3. Approbation des comptes

- **Définition** : porte sur un exercice **clos**. Elle arrête des comptes déjà
  exécutés ; elle n'engage rien.
- **Fondement** : loi art. 24 I (`LEGIARTI000051749514`) ; décret art. 11 I 1°,
  état financier et compte de gestion joints (`LEGIARTI000053191281`) ; décret
  2005-240 art. 8, cinq annexes obligatoires (`LEGIARTI000006239516`).
- **Ne s'applique pas** : seuil, avis préalable, devis, exécution.
- **S'applique** : **rapport du conseil syndical**, annexe, majorité.

### 4. Budget prévisionnel

- **Définition** : vote l'enveloppe des dépenses courantes d'un exercice **à
  venir**. Ce vote **vaut autorisation** de ces dépenses, sans résolution ligne
  à ligne.
- **Fondement** : loi art. 14-1 I (`LEGIARTI000043977299`) ; décret art. 11 I 2°
  (`LEGIARTI000053191281`).
- **Ne s'applique pas** : seuil, avis préalable, devis, exécution.
- **Motif** : une enveloppe ne se rapproche pas d'une dépense, elle se compare à
  un réalisé. Exiger une dépense rattachée à un budget de plusieurs centaines de
  milliers d'euros produirait un constat à chaque exercice.

### 5. Fonds de travaux

- **Définition** : alimente le fonds de travaux, ou arrête le plan pluriannuel.
- **Fondement** : loi art. 14-2 (`LEGIARTI000043977289`).
- **Ne s'applique pas** : seuil, avis préalable, devis, exécution.
- **Motif** : le fonds est une réserve. Sa contrepartie est un solde, pas une
  dépense rattachée.

### 6. Engagement de dépense

- **Définition** : engage l'argent du syndicat sur un marché, un contrat ou des
  travaux non compris dans le budget prévisionnel. Un montant, un bénéficiaire.
- **Fondement** : loi art. 14-1 II, renvoi au décret (`LEGIARTI000043977299`) ;
  décret art. 44, liste des dépenses hors budget (`LEGIARTI000006488761`) ;
  décret art. 45, définition de la maintenance (`LEGIARTI000006488770`) ; décret
  art. 11 I 3°, conditions essentielles du contrat (`LEGIARTI000053191281`).
- **C'est le seul type auquel les six contrôles de dépense s'appliquent au
  complet.**

### 7. Autorisation donnée à un copropriétaire

- **Définition** : autorise un copropriétaire à faire **à ses frais** des
  travaux affectant les parties communes. Le syndicat n'engage aucune dépense.
- **Fondement** : loi art. 25 b (`LEGIARTI000051749507`) ; passerelle de
  l'art. 25-1 (`LEGIARTI000049398359`).
- **Ne s'applique pas** : seuil, avis préalable, devis, exécution.
- **Motif** : aucun euro du syndicat n'est engagé. Exiger une dépense rattachée
  reviendrait à reprocher au syndicat de n'avoir pas payé ce qu'il n'a pas à
  payer. Le devis, s'il existe, lie le copropriétaire à son entreprise.
- **S'applique** : majorité (art. 25, avec la passerelle de l'art. 25-1).

### 8. Délégation au conseil syndical

- **Définition** : délègue au conseil syndical des décisions relevant de
  l'article 24, pour deux ans au plus et sous un montant maximum.
- **Fondement** : loi art. 21-1, conditions et matières exclues
  (`LEGIARTI000039301559`) ; art. 21-2, montant maximum
  (`LEGIARTI000039301561`) ; art. 21-3, deux ans au plus
  (`LEGIARTI000039301563`) ; art. 21-5, compte rendu et rapport
  (`LEGIARTI000039301567`).
- **Ne s'applique pas** : seuil, devis, exécution ligne à ligne.
- **S'applique** : **rapport du conseil syndical** — l'art. 21-5 le fait rendre
  « devant l'assemblée générale votant l'approbation des comptes » — plus le
  contrôle de durée, de plafond et de matières exclues, déjà en place.

### 9. Seuil de l'article 21

- **Définition** : arrête le montant des marchés et contrats au-delà duquel la
  consultation du conseil syndical, ou la mise en concurrence, devient
  obligatoire. Ce sont **deux montants distincts**, votés séparément.
- **Fondement** : loi art. 21 al. 2 (`LEGIARTI000039313574`).
- **Ne s'applique pas** : seuil, avis préalable, devis, exécution.
- **Motif** : une résolution qui *arrête* un seuil ne se contrôle pas contre un
  seuil. Elle est la source du contrôle, pas son sujet.

### 10. Modalités

- **Définition** : règle une modalité d'organisation ou de financement sans
  engager de dépense propre — appels de fonds, exigibilité, recouvrement,
  habilitation à agir en justice, pouvoir d'exécution donné au syndic,
  autorisation permanente donnée à la police municipale.
- **Fondement** : loi art. 14-1 I al. 2 et 3, et II, exigibilité
  (`LEGIARTI000043977299`) ; décret art. 35, les huit fondements d'un appel de
  fonds (`LEGIARTI000053191341`) ; décret art. 55, habilitation à agir en
  justice (`LEGIARTI000053191360`) ; loi art. 24 II h, autorisation permanente
  à la police municipale (`LEGIARTI000051749514`).
- **Ne s'applique pas** : seuil, avis préalable, devis, exécution.
- **Motif** : la dépense qu'une modalité finance a été votée par une **autre**
  résolution, qui porte le contrôle. Rattacher la dépense aux deux la compterait
  deux fois — précisément le défaut que ce lot cherche à supprimer.

### 11. Portée non déterminée

- **Définition** : aucun type n'a été reconnu, et il n'est pas supposé.
- **Tous les contrôles restent appliqués.** C'est le seul cas où l'écran a le
  droit de se tromper, et il doit le dire.

## Les quatre pistes, tranchées par la source

### Piste 1 — « L'approbation des comptes ne relève pas des seuils »

**Fondée, et le rattachement de remplacement existe, avec une base textuelle
plus solide que supposé.**

Les seuils de l'article 21 al. 2 portent sur des marchés et des contrats à
passer. Une approbation de comptes porte sur un exercice clos : elle n'en passe
aucun.

Le régime de contrôle qui lui est propre est ailleurs, et trois textes
convergent :

| Fondement | Identifiant | Ce qu'il rattache |
|---|---|---|
| Décret 67-223 art. 22 al. 2 | `LEGIARTI000006488493` | « Le conseil syndical rend compte à l'assemblée, chaque année, de l'exécution de sa mission » |
| Décret 67-223 art. 11 II 4° | `LEGIARTI000053191281` | Ce compte rendu est notifié avec l'ordre du jour |
| Loi 65-557 art. 21-5 | `LEGIARTI000039301567` | Le compte rendu de délégation est rendu devant l'assemblée votant l'approbation des comptes |

Le décret art. 26 (`LEGIARTI000042078742`) définit d'ailleurs la mission du
conseil syndical en termes directement comptables : il contrôle « la comptabilité
du syndicat, la répartition des dépenses » et « l'élaboration du budget
prévisionnel dont il suit l'exécution ».

**Ce que le code fait maintenant** : une septième cellule, `rapport du conseil
syndical`, distincte de `avis du conseil syndical`. Les deux portaient le même
nom et ne sont pas la même chose — l'avis est une consultation *préalable* sur
un *marché*, le rapport est un compte rendu *annuel* sur une *gestion*. Cette
cellule n'est exigible que de deux types : l'approbation des comptes et la
délégation.

### Piste 2 — « Une exception réglementaire sur les seuils pour l'élection du syndic »

**À moitié fondée, et la moitié vraie n'est pas là où on la cherchait.**

La passerelle de l'article 25-1 (`LEGIARTI000049398359`) **ne comporte aucune
exclusion**, ni pour le syndic ni pour aucune autre matière : elle vise l'article
25 « ou une autre disposition », sans réserve. Il n'y a donc pas d'exception de
majorité pour la désignation du syndic.

Il existe en revanche deux règles propres, réelles :

1. **Le contrat de syndic est expressément exclu du seuil de mise en
   concurrence.** L'article 21 al. 2 vise les marchés et contrats « autres que
   celui de syndic ». Le contrat de syndic relève d'une mise en concurrence
   triennale à la charge du conseil syndical (al. 3), et le texte précise que
   son défaut n'entache pas la validité de la désignation. **C'est cette règle
   qui est implémentée** : la désignation du syndic ne porte plus de cellule
   seuil.
2. **Une condition de procédure sur la passerelle.** Décret 67-223 art. 19
   (`LEGIARTI000042078704`) : « lorsque l'assemblée est appelée à approuver un
   contrat, un devis ou un marché mettant en concurrence plusieurs candidats,
   elle ne peut procéder au second vote prévu à ces articles qu'après avoir voté
   sur **chacune** des candidatures à la majorité applicable au premier vote. »
   Avec plusieurs candidats syndics, on ne peut pas basculer à l'article 24 après
   n'avoir testé qu'un seul candidat. **Ce contrôle n'est pas implémenté** — voir
   « Ce qui reste ouvert ».

Note complémentaire : lorsque la copropriété n'a pas institué de conseil
syndical, la mise en concurrence n'est pas obligatoire du tout (art. 21 al. 2 in
fine). Un contrôle de seuil devrait donc d'abord savoir si un conseil syndical
existe. Ce point n'est pas non plus implémenté.

### Piste 3 — « Les dépenses sans acte : vérifier ce qui relève du budget déjà voté »

**Fondée, et le texte est explicite.**

La loi art. 14-1 I (`LEGIARTI000043977299`) : « Pour faire face aux dépenses
courantes de maintenance, de fonctionnement et d'administration […] le syndicat
des copropriétaires vote, chaque année, un budget prévisionnel. » Le vote du
budget vaut autorisation de ces dépenses. Aucune résolution ligne à ligne n'est
due.

Le II du même article pose la frontière : « Ne sont pas comprises dans le budget
prévisionnel les dépenses du syndicat pour travaux, dont la liste est fixée par
décret. » Cette liste est celle du décret art. 44 (`LEGIARTI000006488761`), et
c'est le décret art. 45 (`LEGIARTI000006488770`), en définissant la maintenance,
qui trace la limite en creux.

**La mesure.** Le procès-verbal étalon donne le partage lui-même, dans le texte
de la résolution d'approbation des comptes de l'exercice clos : **263 803,64 €
de dépenses courantes** (annexe 3) et **4 350,56 € de dépenses hors budget**
(annexe 4). Soit **98,4 % des euros de l'exercice couverts par le budget
prévisionnel déjà voté, et 1,6 % relevant d'un vote séparé.**

Un contrôle « cet euro, qui l'a autorisé ? » qui ignore le budget accuserait donc
à tort la quasi-totalité des euros de l'exercice.

**Ce que le code fait maintenant**, et ce qu'il ne fait pas :

- une dépense imputée au budget prévisionnel ne produit **plus** de constat
  « aucun acte ne la couvre » ;
- une dépense hors budget sans acte reste un manquement, et le constat le dit
  désormais explicitement : « imputée hors budget prévisionnel, et aucun acte
  d'autorisation ne la couvre » ;
- **une dépense dont l'imputation n'est pas tranchée n'est plus rangée d'office
  du côté du manquement.** Elle produit un constat distinct,
  `IMPUTATION_A_TRANCHER`, qui **nomme les deux réponses possibles et l'article
  qui les sépare** : dépense courante de maintenance couverte par le budget
  (art. 14-1 I), ou dépense de travaux exigeant un vote séparé (décret art. 44),
  la frontière tenant à la définition de la maintenance de l'article 45.

Ce dernier point est l'alternative que Brice avait acceptée : **le partage
art. 44 / art. 45 ne s'automatise pas de façon sûre**, parce que le décret art. 45
assimile au courant le remplacement d'un équipement « lorsque son prix est
compris forfaitairement dans le contrat de maintenance » — une information qui
n'est ni dans la facture, ni dans le procès-verbal, mais dans le contrat. Le
constat rend donc la matière à l'utilisateur au lieu de trancher à sa place,
dans un sens qui accuserait à tort ou dans l'autre qui blanchirait à tort.

### Piste 4 — « L'autorisation donnée à un copropriétaire n'est pas un engagement de dépense »

**Fondée, sans réserve.**

Loi art. 25 b (`LEGIARTI000051749507`) : « L'autorisation donnée à certains
copropriétaires d'effectuer **à leurs frais** des travaux affectant les parties
communes ou l'aspect extérieur de l'immeuble, et conformes à la destination de
celui-ci. »

Le syndicat ne passe aucun marché et n'engage aucun euro. Les quatre contrôles
de dépense — seuil, avis préalable, devis, exécution — sont retirés.

Le type est reconnu chez les deux cabinets, qui l'écrivent pourtant très
différemment : l'un le formule comme une demande individuelle assortie d'une
autorisation à donner, l'autre comme une demande d'autorisation de travaux
privatifs affectant les parties communes. Les trois éléments du texte — une
autorisation, des travaux, un bénéficiaire copropriétaire — sont présents dans
les deux cas, parce que ce sont ceux que la loi exige.

Un piège écarté au passage : l'autorisation permanente donnée à la police
municipale de pénétrer dans les parties communes n'est **pas** une autorisation
de l'article 25 b. Elle relève de l'art. 24 II h (`LEGIARTI000051749514`), ne
comporte aucun travaux, et est rangée avec les modalités.

## La mesure

Deux cabinets, quatre procès-verbaux dont trois exploitables, une convocation.
Aucun nom, aucun montant nominatif.

### Procès-verbal étalon — 55 résolutions, un cabinet

**53 résolutions typées sur 55, soit 96 %.**

| Type | Nombre |
|---|---:|
| Désignation d'un organe | 22 |
| Modalités | 14 |
| Engagement de dépense | 10 |
| Seuil | 2 |
| Budget prévisionnel | 2 |
| Approbation des comptes | 1 |
| Désignation du syndic | 1 |
| Autorisation à un copropriétaire | 1 |
| **Portée non déterminée** | **2** |

Les deux non typées sont deux décisions d'aménagement dont le procès-verbal
n'écrit ni le mot « travaux », ni aucun prix. Aucun type n'en est déductible, et
elles gardent donc tous leurs contrôles.

**Les constats qui disparaissent.** Chaque ligne compte les cellules marquées
« source manquante » avant le typage, puis après.

| Contrôle | Avant | Après | Retirés |
|---|---:|---:|---:|
| Seuil applicable | 55 | 12 | **43** |
| Avis du conseil syndical | 55 | 12 | **43** |
| Devis retenu | 55 | 12 | **43** |
| Exécution | 55 | 12 | **43** |
| Annexe visée | 55 | 33 | 22 |
| Rapport du conseil syndical | — | 1 exigible sur 55 | — |

Sur la file de constats proprement dite, le total passe de 12 à 8 : quatre
constats « résolution adoptée pour un montant, aucune dépense rattachée »
disparaissent, parce qu'ils portaient sur des budgets, des seuils et des
modalités qui n'ont jamais eu vocation à être rapprochés d'une facture.

**Réponse chiffrée à la question posée** : l'écran annonçait des dépassements de
seuil et des avis manquants sur des décisions qui, pour 78 % d'entre elles, ne
sont soumises ni à l'un ni à l'autre. La part des élections y est prépondérante :
vingt-deux désignations sur cinquante-cinq résolutions, soit 40 % du
procès-verbal.

### Second cabinet — 91 résolutions, deux procès-verbaux

**55 résolutions typées sur 91, soit 60 %.**

| Type | Nombre |
|---|---:|
| Engagement de dépense | 15 |
| Désignation d'un organe | 14 |
| Modalités | 7 |
| Délégation au conseil syndical | 5 |
| Fonds de travaux | 5 |
| Désignation du syndic | 4 |
| Autorisation à un copropriétaire | 3 |
| Seuil | 2 |
| **Portée non déterminée** | **36** |

| Contrôle | Avant | Après | Retirés |
|---|---:|---:|---:|
| Seuil applicable | 91 | 51 | 40 |
| Avis du conseil syndical | 91 | 56 | 35 |
| Devis retenu | 91 | 51 | 40 |
| Exécution | 91 | 51 | 40 |
| Annexe visée | 91 | 77 | 14 |

Le taux de typage plus faible n'est pas un défaut de la typologie : c'est un
défaut d'**extraction** en amont, et il faut le dire séparément. Chez ce cabinet,
l'extracteur retient fréquemment la phrase de décompte des voix comme objet de
la résolution au lieu de son intitulé, et une part des blocs sont des en-têtes de
re-vote sans contenu propre. Une résolution dont l'objet lu est « à la majorité
des voix des copropriétaires présents et représentés, soit N/M tantièmes » ne
peut pas être typée, et ne doit pas l'être.

**Les deux cabinets ensemble : 146 résolutions, 108 typées, soit 74 %.**

### Ce que le corpus a appris en passant

- Un des trois procès-verbaux du second cabinet **n'a aucune couche texte** : le
  fichier livre onze caractères pour un document entier. Ce n'est pas typable, et
  c'est un fait à remonter, pas une absence de résolutions.
- Sur les quatre convocations du second cabinet, **une seule** livre au parseur
  actuel une série de résolutions exploitable. Les trois autres ne sont pas
  reconnues comme documents d'assemblée. Constat d'extraction, hors périmètre de
  ce lot, mais il borne la mesure.

## Ce que cela change pour un copropriétaire

Trois choses concrètes.

**La liste de travail redevient lisible.** Quand un outil signale cinquante-cinq
anomalies dont quarante-trois n'en sont pas, personne ne lit les douze qui
comptent. Le conseil syndical passe son temps à écarter du bruit au lieu
d'instruire les vraies questions.

**Une accusation retirée est une accusation qu'on ne portera pas à tort.**
Reprocher au syndic de n'avoir pas mis en concurrence l'élection du conseil
syndical, ou de n'avoir pas produit de devis pour une approbation de comptes,
décrédibilise l'ensemble du contrôle — y compris les constats fondés.

**La question de l'argent est reposée au bon endroit.** Sur l'exercice mesuré,
98,4 % des euros relèvent du budget prévisionnel déjà voté. Le contrôle utile ne
porte donc pas sur « chaque euro a-t-il sa résolution » — il porte sur les 1,6 %
de dépenses hors budget, sur le respect du budget voté, et sur les dépenses dont
l'imputation reste à trancher. C'est là que se trouvent les rattrapages, les
appels de fonds exceptionnels et les tensions de trésorerie.

## Ce qui reste ouvert

Ces points sont identifiés, non traités, et aucun n'est supposé résolu.

1. **Le typage n'est branché sur aucune chaîne d'écriture.** Aucun code
   n'alimente aujourd'hui la table des actes d'autorisation à partir du registre
   des résolutions. La fonction de typage, le vocabulaire et la matrice sont
   livrés et testés ; leur appel au moment de l'extraction reste à écrire par la
   voie qui possédera ce pont.

2. **La condition de procédure du décret art. 19 n'est pas contrôlée.** Avec
   plusieurs candidats syndics, la passerelle de l'art. 25-1 n'est ouverte
   qu'après un vote sur chacune des candidatures à la majorité du premier tour.
   Le second cabinet présente régulièrement quatre projets de contrat de syndic
   dans la même convocation : le cas est réel, pas théorique.

3. **L'absence de conseil syndical n'est pas prise en compte.** L'article 21
   al. 2 in fine dispense de mise en concurrence la copropriété qui n'a pas
   institué de conseil syndical. Un contrôle de seuil devrait d'abord savoir si
   un conseil existe.

4. **Deux résolutions récurrentes semblent avoir perdu leur objet légal, et ce
   n'est pas vérifié jusqu'au bout.**
   - Les *modalités de consultation des pièces justificatives des charges* : la
     loi art. 18-1 (`LEGIARTI000042120918`) renvoie au décret, et le décret
     art. 9-1 (`LEGIARTI000038702079`) confie la fixation de ces modalités **au
     syndic**, non à l'assemblée. L'alinéa qui les confiait à l'assemblée a
     disparu avec l'ordonnance du 15 juillet 2020.

     **Correction du 2026-09-10, constat `C057`.** Cette ligne affirmait que
     *« les deux cabinets continuent pourtant de les soumettre au vote »*. Au
     présent, c'est faux. Mesure sur les deux corpus, par recherche de la
     locution dans les procès-verbaux et convocations : **une seule occurrence
     chez le second cabinet, dans une convocation du 19/06/2023**, et rien
     après — l'usage a cessé. Chez le premier, une occurrence, dans un
     procès-verbal dont la date n'a pas été lue. **Réserve de méthode :** ce
     comptage mesure la présence de la locution, pas la mise au vote ; une
     mention dans une convocation n'est pas nécessairement une résolution
     soumise au vote, et le distinguer demanderait de lire chaque bloc.
   - La *clause d'aggravation des charges* : l'article 10-1
     (`LEGIARTI000039313543`) impute de plein droit certains frais au seul
     copropriétaire concerné, par dérogation légale à la clé de répartition. Il
     ne se vote pas. Les deux cabinets la mentionnent — 6 documents chez le
     second, 10 chez le premier, mesure du 2026-09-10 — avec la même réserve :
     la locution est comptée, pas la mise au vote.

   Ces deux points mériteraient un contrôle « résolution sans objet légal
   actuel », qui n'existe pas et n'a pas été créé ici.

5. **Le président du conseil syndical est élu par les membres du conseil, pas
   par l'assemblée.** Le procès-verbal étalon porte, sur cette résolution, une
   majorité non énoncée — ce qui produit un constat aujourd'hui, et n'est
   probablement pas un défaut. Le décret art. 22 devrait le fonder, mais
   **l'alinéa exact n'a pas été vérifié** et la règle n'est donc pas écrite dans
   le code. Un constat sur cinquante-cinq.

6. **La représentation du syndicat auprès d'une association syndicale libre
   n'est pas vérifiée.** Aucun article de la loi 65-557 ne la fonde ; la réponse
   se trouve probablement dans l'ordonnance du 1er juillet 2004, qui n'a pas été
   interrogée. La désignation d'un représentant auprès d'un *syndicat principal*,
   elle, est vérifiée (décret art. 24).

7. **Le contenu ligne à ligne des annexes comptables 1 à 5 n'est pas vérifiable
   par l'API Légifrance** : elles y sont servies « non reproduites », avec renvoi
   au Journal officiel. Leur existence, leur numérotation et leur caractère
   obligatoire sont établis ; les égalités de totaux imposées entre annexes par
   le décret 2005-240 art. 10 (`LEGIARTI000006239518`) sont des contrôles
   arithmétiques opposables et directement implémentables, mais non implémentés.

## Où se trouve quoi

| Fichier | Ce qu'il porte |
|---|---|
| `server/src/coproscope/modules/_actes_vocabulaire.py` | Les onze valeurs de portée, et l'état « ne s'applique pas » ajouté aux forces probatoires |
| `server/src/coproscope/modules/_actes_typologie.py` | Le fondement légal de chaque type, et la matrice type × contrôle avec le motif de chaque retrait |
| `server/src/coproscope/modules/_resolutions_qualification.py` | La reconnaissance du type sur le texte d'une résolution |
| `server/src/coproscope/modules/_actes_constats.py` | Les constats, bornés par la matrice |
| `server/src/coproscope/modules/_actes_vues.py` | Les cellules de la matrice de gouvernance, dont la septième |
| `server/tests/test_resolutions_typage.py` | 34 tests, dont un par piste et un par cabinet |

Les sources juridiques ne sont pas recopiées dans le code sous forme de
citations longues : chaque type porte son article et son identifiant Légifrance,
et un test refuse tout type dont l'identifiant ne serait pas de la forme
attendue. Une règle de majorité ne se cite pas de mémoire.
