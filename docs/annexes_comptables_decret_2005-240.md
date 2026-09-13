# Les cinq annexes comptables du decret 2005-240, structure reelle

Date: 2026-09-06.
Rattachement: `RM-2026-0091`.
Statut: `VERIFIE`.

## Provenance, et pourquoi elle merite d'etre dite

Cette structure a resiste a trois tentatives par voie numerique le 2026-09-06:

- l'API Legifrance rend `Annexe non reproduite` et un lien;
- la page du Journal officiel dit *"vous pouvez consulter le tableau dans le JO
  n° 65 du 18/03/2005 texte numero 7"*;
- le PDF est refuse - 401 par l'API, 403 en acces direct.

**Brice a depose le fichier lui-meme**, et c'est ce qui a debloque le point:
`joe_20050318_0065_0007.pdf`, Journal officiel du 18 mars 2005, texte 7 sur 102,
NOR `SOCU0412534D`. Publication officielle, lue page par page.

La lecon vaut d'etre gardee: une source peut etre publique, officielle,
parfaitement identifiee, et rester **hors de portee de tout acces
programmatique**. Declarer une lacune plutot que de reconstituer de memoire
etait la bonne conduite - et c'est ce qui a permis a un humain de la combler en
une minute.

**Etat du texte.** Ceci est la version d'origine de 2005. Le decret 2020-1229 y
a ajoute, dans l'annexe 1, partie *I. Situation financiere et tresorerie*,
rubrique *Provisions et avances*, le compte **106 Provisions pour travaux au
titre de la delegation de pouvoirs accordee au conseil syndical** - entree en
vigueur le 31 decembre 2020, `LEGIARTI000042412731`.

---

## Ce que le decret impose, avant les tableaux

| Article | Ce qu'il pose |
|---|---|
| 5 | Exercice de **douze mois**. Premier exercice: au plus **dix-huit mois**. Un changement de date de cloture exige **cinq ans** entre deux decisions d'assemblee. |
| 6 | Les pieces justificatives sont des **originaux**, datees, portant les references du syndicat, **conservees dix ans**. |
| 7 | Les creances sur chaque coproprietaire se ventilent en **quatre rubriques**: operations courantes, travaux de l'article 14-2 et operations exceptionnelles, avances, emprunts. |
| 8 | Les documents de synthese sont l'**etat financier**, le **compte de gestion general** et l'**etat des travaux** votes non clotures, **conformes aux modeles des annexes 1 a 5**. |
| 9 | Les charges et produits attendus sur operations courantes sont presentes **conformement a l'annexe 2**. |
| 10 | Double presentation: **par nature** (annexe 2) et **par ventilation analytique** (annexes 3 et 4), dont *les rubriques sont arretees en fonction des clauses du reglement de copropriete*. |
| 11 | Les modalites sont precisees par un **arrete conjoint** - non lu a ce jour. |
| 12 | Les annexes sont conservees **avec le proces-verbal** de l'assemblee qui approuve les comptes, et font l'objet d'un classement particulier aux archives. |

Deux points de l'article 10 comptent pour la suite. D'abord, **les rubriques de
ventilation dependent du reglement de copropriete**: elles ne sont donc pas
universelles, et un controle qui les coderait en dur se tromperait d'immeuble.
Ensuite, il pose des **egalites obligatoires**, ci-dessous.

---

## Les egalites de controle, article 10

C'est le passage le plus utile du decret pour un outil de verification: il
n'impose pas une opinion, il impose des **totaux qui doivent coincider**.

> Pour l'approbation des comptes, le total des charges pour operations
> courantes de l'annexe n° 3 doit etre egal au total des charges de l'annexe
> n° 2 et le total des charges pour travaux de l'article 14-2 et operations
> exceptionnelles de l'annexe n° 4 doit etre egal au total des charges de
> l'annexe n° 2.
>
> Pour le vote du budget previsionnel, le total des charges pour operations
> courantes de l'annexe n° 3 doit etre egal au total des charges de l'annexe
> n° 2.

| Controle | Egalite exigee | Quand |
|---|---|---|
| `CTRL-A10-1` | total charges operations courantes **annexe 3** = total charges operations courantes **annexe 2** | approbation des comptes |
| `CTRL-A10-2` | total charges travaux art. 14-2 et operations exceptionnelles **annexe 4** = total de ces memes charges **annexe 2** | approbation des comptes |
| `CTRL-A10-3` | total charges operations courantes **annexe 3** = total charges operations courantes **annexe 2** | vote du budget previsionnel |

**Reserve de lecture, a ne pas escamoter.** Le texte ecrit deux fois *"le total
des charges de l'annexe n° 2"* sans preciser lequel des deux blocs. L'annexe 2
en porte pourtant deux, nettement separes: les charges pour operations
courantes, et les charges pour travaux et operations exceptionnelles. La lecture
retenue ci-dessus - chaque annexe se compare au bloc de meme nature - est la
seule qui ait un sens comptable, et elle est cohérente avec la structure des
tableaux. Elle reste une **lecture**, et un ecart constate devra etre presente
en la citant.

---

## Annexe 1 - Etat financier apres repartition

Deux colonnes: *exercice precedent approuve*, *exercice clos*.

**I. Situation financiere et tresorerie**

- Tresorerie: `50` Fonds places, `51` Banques ou fonds disponibles en banque,
  `53` Caisse → **Tresorerie disponible, Total I**
- Provisions et avances: `102` Provisions pour travaux, **`106` Provisions pour
  travaux au titre de la delegation au conseil syndical** *(ajout 2020)*,
  `103` Avances, dont `1031` Avances de tresorerie, `1032` Avances travaux,
  `1033` Autres avances
- `131` Subventions en instance d'affectation
- `12` Solde en attente sur travaux ou operations exceptionnelles

**II. Creances** - `45` Coproprietaires, sommes exigibles restant a recevoir;
`459` Coproprietaires, creances douteuses; comptes de tiers `42 a 44` Autres
creances, `46` Debiteurs divers, `47` Compte d'attente, `48` Comptes de
regularisation → **Total II**, puis **Total general (I)+(II)**

**Dettes** - `45` Coproprietaires, excedents verses; `40` Fournisseurs;
`42 a 44` Autres dettes; `46` Crediteurs divers; `47` Compte d'attente;
`48` Comptes de regularisation; `49` Depreciation des comptes de tiers →
**Total II**, puis **Total general (I)+(II)**

**Emprunts: montant restant du**, hors totaux.

Deux notes du tableau, qui sont des regles de lecture: une somme affectee du
signe « - » indique un decouvert bancaire correspondant a une dette du
syndicat; les creances douteuses et les excedents verses appellent une **liste
individualisee, nom et montant, jointe**.

---

## Annexe 2 - Compte de gestion general et budget previsionnel

Cinq colonnes, et c'est leur presence simultanee qui fait la valeur de
l'annexe: *exercice precedent approuve N-1*, *exercice clos budget vote N*,
*exercice clos realise a approuver N*, *budget previsionnel en cours vote N+1*,
*budget previsionnel a voter N+2*.

**Charges pour operations courantes**

| Compte | Poste |
|---|---|
| `60` | Achats de matieres et fournitures |
| `601` | Eau, compteur general |
| `602` | Electricite |
| `603` | Chauffage, energie, combustible |
| `60X` | Autres |
| `61` | Services exterieurs |
| `611` | Nettoyage des locaux |
| `612` | Locations immobilieres |
| `613` | Locations mobilieres |
| `614` | Contrats de maintenance |
| `615` | Entretien et petites reparations |
| `616` | Primes d'assurance |
| `62` | Frais d'administration |
| `621` | Remuneration du syndic sur gestion copropriete |
| `622` | Autres honoraires du syndic |
| `62...` | Autres, autres que 621 et 622 |
| `63` | Impots et taxes |
| `64` | Frais de personnel |

**Charges pour travaux et autres operations exceptionnelles**:
`661` Remboursement d'annuites d'emprunt, `671` et `673` Travaux,
`677` Pertes sur creances irrecouvrables, `678` Charges exceptionnelles,
`68` Depreciations sur creances douteuses.

**Produits pour operations courantes**: `701` Provisions coproprietaires,
`711` Subventions sur frais de fonctionnement, `713` Indemnites d'assurances,
`714` Produits divers, `716` Produits financiers.

**Produits pour travaux et autres operations exceptionnelles**:
`702` Provisions pour travaux, `703` Avances versees par les coproprietaires,
`704` Remboursement d'annuites d'emprunts, `711` Subventions sur travaux,
`712` Emprunts a utiliser sur travaux, `713` Indemnites d'assurances,
`714` Produits divers, `716` Produits financiers, `718` Produits exceptionnels,
`78` Reprises de depreciation sur creances douteuses.

Chaque bloc porte un **sous-total**, puis un **solde, excedent ou insuffisance**.

---

## Annexe 3 - Ventilation par categories, operations courantes

Memes colonnes que l'annexe 2. Neuf categories, chacune en trois lignes -
**Charges**, **Produits affectes**, **Net**:

charges communes generales; charges communes a un groupe d'immeubles; charges
batiment; charges cage d'escalier ou d'entree; charges d'ascenseurs; charges
d'eau froide; charges d'eau chaude; charges de chauffage; charges de parkings;
puis une ligne libre *autre nature de charges*.

Puis **Total charges nettes**, **Provisions coproprietaires**, et le **solde**.

**Ces categories ne sont pas universelles.** L'article 10 les fait arreter *en
fonction des clauses du reglement de copropriete*. Un controle qui les coderait
en dur echouerait des le deuxieme immeuble - c'est un axe de generalisation, et
la valeur observee chez un syndic n'est pas la regle.

---

## Annexe 4 - Ventilation, travaux de l'article 14-2 et operations exceptionnelles

Colonnes: *exercice clos, depenses votees (N)* hors budget previsionnel, puis
*exercice clos realise a approuver (N)* en deux volets **Depenses** et
**Provisions appelees**, puis **Solde**.

Deux blocs: **Travaux de l'article 14-2**, detailles par operation - chaque
operation en Charges / Produits affectes / Net - puis `TOTAL TRAVAUX ARTICLE
14-2`; et **Operations exceptionnelles**, meme forme, puis `TOTAL OPERATIONS
EXCEPTIONNELLES`, enfin `TOTAL TRAVAUX DE L'ART. 14-2 ET OPERATIONS
EXCEPTIONNELLES`.

Notes du tableau: detailler **par poste, par imputation**, avec indication
facultative des numeros de compte; detailler **par marche de travaux**; detailler
**sur l'ensemble des cles de repartition** concernees par le marche.

---

## Annexe 5 - Etat des travaux votes non encore clotures

Une ligne par operation - le modele donne en exemple *travaux ravalement*,
*travaux toiture* - et six colonnes designees par des lettres:

| Colonne | Contenu |
|---|---|
| **A** | Travaux votes, montant et date |
| **B** | Travaux payes, montant et date |
| **C** | Travaux realises, montant et date |
| **D** | Appels travaux, emprunts et subventions recus, montant et date |
| **E = D − C** | **Solde en attente sur travaux** |
| **F** | Subventions et emprunts a recevoir, montant et date |

Puis une ligne **TOTAL**.

Deux notes, dont la seconde est un **controle croise avec l'annexe 1**:

- detailler par marche de travaux ou operations exceptionnelles, **et par cle
  de repartition**;
- *"ce solde correspond au solde du compte 12 dans l'annexe n° 1"*.

| Controle | Egalite exigee |
|---|---|
| `CTRL-A5-1` | total de la colonne **E** de l'annexe 5 = solde du compte **12** de l'annexe 1 |

C'est un rapprochement de meme nature que ceux de l'article 10: deux expressions
du meme objet, qui doivent coincider par construction. Un ecart n'est pas une
opinion, c'est un chiffre a expliquer.

---

## Ce que cela change pour le referentiel

| Avant | Apres |
|---|---|
| `EXT-CTRL-05` reposait sur une structure d'annexes inconnue | les postes, les colonnes et les totaux sont connus et cites |
| Aucune egalite legale n'etait citable | **quatre** le sont: trois de l'article 10, une de l'annexe 5 |
| Le decret 2005-240 restait `SOURCE_A_VERIFIER` | il devient `VERIFIE`, sauf l'arrete de l'article 11 |

Reste non lu: **l'arrete conjoint prevu a l'article 11**, qui precise les
modalites d'etablissement des comptes. Il ne conditionne aucun controle
ci-dessus.
