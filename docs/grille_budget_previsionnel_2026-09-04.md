# Grille de controle du budget previsionnel

Lot `RM-2026-0082` / `CONV-2026-2134`. Grille lettree, sur le modele de celle de
`RM-2026-0047`. Seize controles: sept sur le contenu du budget (famille `B`),
neuf sur la procedure du vote (famille `P`).

Predicats executables: `server/src/coproscope/modules/budget_previsionnel.py`.
Tests: `server/tests/test_budget_previsionnel.py`.

## Ce que la source dit, et ou l'intuition se trompait

Six pistes avaient ete proposees comme pistes. Chacune a ete confrontee au
texte. Deux tiennent telles quelles, trois sont vraies mais deplacees, une est
fausse. La refutation est le resultat le plus utile du lot.

| Piste proposee | Verdict | Ce que dit reellement le texte |
|---|---|---|
| 1. Le previsionnel N se confronte au realise N-1 | **Fausse comme obligation** | Le comparatif exige au vote du budget est previsionnel contre previsionnel: `article 11 I 2.` du decret du 17 mars 1967 impose "le projet du budget presente avec le comparatif du dernier budget previsionnel vote". Le realise n'entre qu'a l'approbation des comptes, et il s'y compare a deux autres references: le budget vote pour le meme exercice et les comptes approuves de l'exercice precedent (`article 8` du decret du 14 mars 2005). Confronter le previsionnel N au realise N-1 est une bonne pratique d'audit; ce n'est pas une regle. |
| 2. Les postes suivent la nomenclature | **Vraie, mais deplacee** | Ce qui est reglementaire est le NUMERO (`article 7` de l'arrete du 14 mars 2005), pas le libelle. Et l'`article 8` du meme arrete autorise "toute subdivision necessaire": un numero inconnu est d'abord une subdivision licite. Voir la section "axe". |
| 3. Le total de l'annexe 2 egale celui de l'annexe 3 | **Vraie, avec une precision qui change le controle** | `article 10` du decret du 14 mars 2005: pour le VOTE DU BUDGET, une seule egalite, annexe 3 courantes contre annexe 2. Les deux egalites, avec l'annexe 4, ne valent que pour l'APPROBATION DES COMPTES. Coder l'annexe 4 dans le controle du budget serait une faute. |
| 4. Les depenses de l'article 44 sont exclues | **Vraie, mais non codable telle quelle** | `article 44` du decret du 17 mars 1967, cinq categories. Aucune ne se reconnait a un libelle: la frontiere entre la maintenance et la conservation "autre que de maintenance" est une qualification de fait. Ce qui est codable est le reflet comptable: les classes 67 et 68. |
| 5. Le budget est vote avant l'exercice, sinon provisions transitoires | **Moitie vraie, moitie fausse** | Le principe existe (`article 43` alinea 1). Mais son alinea 2 ORGANISE le vote en cours d'exercice, et l'`article 14-1 I` de la loi donne six mois a l'assemblee a compter du dernier jour de l'exercice precedent. Un vote posterieur au debut de l'exercice n'est donc pas en soi une irregularite. Le regime transitoire est borne: autorisation prealable de l'assemblee, deux provisions trimestrielles au plus, chacune egale au quart du budget PRECEDEMMENT VOTE. |
| 6. La cotisation au fonds de travaux | **Vraie, avec deux conditions absentes de l'enonce** | `article 14-2-1 I` de la loi: le fonds n'existe qu'au terme de dix ans depuis la reception des travaux de construction, et seulement en immeuble a destination totale ou partielle d'habitation. Le plancher est double quand un plan pluriannuel est adopte: 5 % du budget previsionnel ET 2,5 % des travaux du plan. |

Controles ajoutes, absents des six pistes: avance de reserve plafonnee au
sixieme du budget (`article 35 1.` du decret de 1967), montant alloue au conseil
syndical inclus dans le budget (`article 2` du decret de 2005), question de la
suspension des cotisations quand le fonds excede le budget (`article 14-2-1 II`),
notification du projet de budget pour la validite de la decision
(`article 11 I`), duree de douze mois de l'exercice, majorite de l'article 24,
concertation avec le conseil syndical (`article 18 II`), archivage des annexes
avec le proces-verbal (`article 12` du decret de 2005).

## Sources verifiees

Toutes lues sur Legifrance via PISTE le 2026-09-03, fonds `LODA_DATE`, filtre de
date pose au jour de la lecture. Aucune ne porte de date de fin de vigueur.
`VIGUEUR` signifie "en vigueur a la date demandee", jamais "a jour": la date de
version fait partie de la citation.

| Texte | Article | `LEGIARTI` | Version en vigueur depuis |
|---|---|---|---|
| Loi n. 65-557 du 10 juillet 1965 | 14-1 | `LEGIARTI000043977299` | 2023-01-01 |
| Loi n. 65-557 | 14-2 | `LEGIARTI000043977289` | 2023-01-01 |
| Loi n. 65-557 | 14-2-1 | `LEGIARTI000043967792` | 2023-01-01 |
| Loi n. 65-557 | 18 | `LEGIARTI000049398867` | 2024-04-11 |
| Loi n. 65-557 | 24 | `LEGIARTI000051749514` | 2025-06-18 |
| Decret n. 67-223 du 17 mars 1967 | 11 | `LEGIARTI000053191281` | 2025-12-25 |
| Decret n. 67-223 | 35 | `LEGIARTI000053191341` | 2025-12-25 |
| Decret n. 67-223 | 43 | `LEGIARTI000006488753` | 2004-06-04 |
| Decret n. 67-223 | 44 | `LEGIARTI000006488761` | 2004-06-04 |
| Decret n. 67-223 | 45-1 | `LEGIARTI000042078810` | 2020-07-04 |
| Decret n. 2005-240 du 14 mars 2005 | 2 | `LEGIARTI000042412723` | 2020-12-31 |
| Decret n. 2005-240 | 5 | `LEGIARTI000006239513` | 2005-03-18 |
| Decret n. 2005-240 | 8 | `LEGIARTI000006239516` | 2005-03-18 |
| Decret n. 2005-240 | 9 | `LEGIARTI000006239517` | 2005-03-18 |
| Decret n. 2005-240 | 10 | `LEGIARTI000006239518` | 2005-03-18 |
| Decret n. 2005-240 | 12 | `LEGIARTI000006239520` | 2005-03-18 |
| Decret n. 2005-240 | annexe 2 | `LEGIARTI000042412729` | 2020-12-31 |
| Arrete du 14 mars 2005 | 6 | `LEGIARTI000006501186` | 2005-03-18 |
| Arrete du 14 mars 2005 | 7 | `LEGIARTI000042413155` | 2020-12-31 |
| Arrete du 14 mars 2005 | 8 | `LEGIARTI000006501225` | 2005-03-18 |

Deux limites de source, a garder en tete pour tout le reste de la grille.

1. **Les modeles d'annexes ne sont pas lisibles.** Les annexes 1 a 5 du decret
   du 14 mars 2005 portent sur Legifrance la mention "Annexe non reproduite" et
   un renvoi au PDF du Journal officiel. Seules les rubriques nommees par les
   textes modificatifs sont connues par machine. Tout controle qui pretendrait
   verifier la structure exacte d'une annexe irait au-dela de sa source.
2. **La lettre de l'article 10 est defectueuse.** Elle dit que le total des
   charges courantes de l'annexe 3 doit egaler "le total des charges de
   l'annexe n. 2", puis que le total travaux de l'annexe 4 doit egaler, mot pour
   mot, "le total des charges de l'annexe n. 2". Appliquee litteralement, elle
   imposerait l'egalite de l'annexe 3 et de l'annexe 4, ce qui est absurde. Le
   controle `B-4` s'en tient au seul cas non ambigu, celui du vote du budget.

Reference legale defectueuse observee dans les textes eux-memes: l'arrete du
14 mars 2005 vise l'"article 21-1" de la loi pour la delegation au conseil
syndical, la ou le decret de 1967 et celui de 2005 visent l'article 21-2. Un
controle ne doit pas s'appuyer sur le renvoi, seulement sur le numero de compte.

## Famille B - contenu et arithmetique du budget

### B-1 - Perimetre de l'article 44

- **Enonce.** Aucune depense de l'article 44 ne figure au budget previsionnel.
- **Sources.** `LEGIARTI000043977299` (loi, art. 14-1 II), `LEGIARTI000006488761`
  (decret 1967, art. 44), `LEGIARTI000042412723` et `LEGIARTI000006239517`
  (decret 2005, art. 2 et 9).
- **Entree exigee.** `budget.lignes`, chaque ligne portant un numero de compte
  et un montant. Un compte sans montant ne suffit pas.
- **Constat en cas d'echec.** Comptes des classes 67 ou 68 portes au budget, avec
  leur numero brut et le compte normalise.
- **Ce qu'il ne prouve pas.** Rien sur la qualification des lignes retenues. La
  frontiere entre la maintenance, qui est au budget, et la conservation ou
  l'entretien de l'article 44 1., qui n'y est pas, se juge sur la nature des
  travaux et non sur un numero. Une reprise de toiture imputee en 615 passe ce
  controle. Le controle ne tranche pas non plus la classe 66: voir ci-dessous.

**La classe 66 n'est pas tranchee, et le module ne tranche pas a la place du
texte.** Les deux cabinets mesures la rangent differemment dans l'annexe 2: l'un
porte 662 avec les operations courantes, l'autre porte 661 et 662 avec les
travaux. Le modele d'annexe 2 qui deciderait n'est pas reproduit sur Legifrance.
Une ligne de classe 66 au budget rend donc `A_VERIFIER_HUMAIN`, pas `ECART`.

### B-2 - Appartenance a la nomenclature

- **Enonce.** Tout compte porte au budget appartient a la nomenclature ou en est
  une subdivision.
- **Sources.** `LEGIARTI000006501186`, `LEGIARTI000042413155`,
  `LEGIARTI000006501225` (arrete, art. 6, 7 et 8).
- **Entree exigee.** `budget.lignes`, numeros de compte tels qu'imprimes.
- **Constat.** Numeros hors nomenclature et non rattachables par prefixe.
- **Ce qu'il ne prouve pas.** Ni l'exactitude du libelle, ni la justesse de
  l'imputation. L'article 8 autorisant toute subdivision necessaire, un numero
  inconnu mais rattachable est licite: le controle ne signale que ce qui ne se
  rattache a rien.

### B-3 - Compte retire de la nomenclature

- **Enonce.** Aucun compte retire de la nomenclature en vigueur n'est utilise.
- **Sources.** `LEGIARTI000042413155`, `LEGIARTI000006501225`.
- **Entree exigee.** `budget.lignes`.
- **Constat.** Comptes supprimes encore utilises. Le seul connu a ce jour est
  1032, porte "(Supprime)" par la version en vigueur.
- **Ce qu'il ne prouve pas.** Que l'operation soit irreguliere: seul le compte
  l'est. Et le controle ne couvre que les suppressions connues du module; une
  suppression posterieure a la version lue passerait inapercue.

### B-4 - Egalite annexe 3 / annexe 2 au vote du budget

- **Enonce.** Le total des charges pour operations courantes de l'annexe 3 egale
  le total des charges de l'annexe 2.
- **Sources.** `LEGIARTI000006239518` (art. 10), `LEGIARTI000006239517`,
  `LEGIARTI000042412729`.
- **Entrees exigees.** `annexes.total_charges_annexe2_courantes`,
  `annexes.total_charges_annexe3_courantes`.
- **Constat.** Ecart chiffre entre les deux totaux, au centime.
- **Ce qu'il ne prouve pas.** Rien sur l'annexe 4, que l'article 10 n'appelle
  que pour l'approbation des comptes. Et l'egalite porte sur deux totaux: deux
  ventilations fausses qui se compensent la passent.

### B-5 - Plancher de la cotisation au fonds de travaux

- **Enonce.** La cotisation annuelle atteint le plancher legal.
- **Sources.** `LEGIARTI000043967792` (art. 14-2-1 I), `LEGIARTI000043977289`,
  `LEGIARTI000043977299`.
- **Entrees exigees.** `copropriete.destination_habitation`,
  `copropriete.date_reception_travaux_construction`,
  `copropriete.cotisation_fonds_travaux_votee`, `budget.total_charges`,
  `copropriete.plan_pluriannuel_adopte` et, si un plan est adopte,
  `copropriete.montant_travaux_plan_adopte`.
- **Constat.** Cotisation votee inferieure a 5 % du budget previsionnel, ou a
  2,5 % des travaux du plan adopte.
- **Ce qu'il ne prouve pas.** L'article ne designe pas l'exercice auquel le
  budget de reference se rapporte; le module n'a pas a trancher ce que le texte
  laisse ouvert. Il ne dit rien du versement effectif sur le compte separe, qui
  releve de l'article 18. Il est **inapplicable** avant le terme de dix ans
  depuis la reception des travaux, et hors immeuble d'habitation.

### B-6 - Plafond de l'avance de reserve

- **Enonce.** L'avance constituant la reserve n'excede pas le sixieme du budget
  previsionnel.
- **Source.** `LEGIARTI000053191341` (decret 1967, art. 35 1.).
- **Entrees exigees.** `copropriete.avance_reserve_prevue_reglement`,
  `budget.total_charges`.
- **Constat.** Avance superieure au sixieme du budget.
- **Ce qu'il ne prouve pas.** L'exigibilite: l'avance suppose en outre que le
  reglement de copropriete la prevoie. Un plafond respecte n'autorise pas a
  appeler.

### B-7 - Question de la suspension des cotisations

- **Enonce.** L'assemblee se prononce sur la suspension des cotisations quand le
  fonds excede le budget previsionnel.
- **Source.** `LEGIARTI000043967792` (art. 14-2-1 II).
- **Entrees exigees.** `annexes.solde_fonds_travaux`, `budget.total_charges`,
  `convocation.question_suspension_cotisation_inscrite`.
- **Constat.** Fonds superieur au budget sans question inscrite a l'ordre du jour.
- **Ce qu'il ne prouve pas.** Le sens de la decision: le texte impose que la
  question soit posee, pas que la suspension soit votee. Et il ajoute un second
  seuil, 50 % des travaux du plan, quand un plan est adopte; ce seuil n'est pas
  encore couvert.

## Famille P - procedure du vote

### P-1 - Vote avant le debut de l'exercice

- **Enonce.** Le budget previsionnel est vote avant le debut de l'exercice qu'il
  couvre.
- **Source.** `LEGIARTI000006488753` (decret 1967, art. 43 alinea 1).
- **Entrees exigees.** `vote.date_assemblee`, `budget.exercice_debut`.
- **Constat.** Vote posterieur au debut de l'exercice, rendu `A_VERIFIER_HUMAIN`.
- **Ce qu'il ne prouve pas.** **Une irregularite.** Le second alinea du meme
  article organise cette situation. Ce controle est un aiguillage vers `P-2`,
  jamais un manquement. C'est le piege principal de la grille.

### P-2 - Regime des provisions transitoires

- **Enonce.** Le vote en cours d'exercice respecte le regime transitoire.
- **Sources.** `LEGIARTI000006488753` (art. 43 alinea 2), `LEGIARTI000043977299`.
- **Entrees exigees.** `vote.autorisation_provisions_transitoires`,
  `vote.provisions_transitoires_appelees`,
  `vote.assiette_provisions_transitoires`, `vote.budget_precedent_vote`.
- **Constat.** Absence d'autorisation prealable, plus de deux provisions
  appelees, ou provision differente du quart du budget precedemment vote.
- **Ce qu'il ne prouve pas.** Rien sur les impayes: le meme alinea ecarte la
  procedure de l'article 19-2 dans cette situation, et un retard de paiement ne
  peut donc pas en etre deduit.

### P-3 - Duree de l'exercice

- **Enonce.** Le budget previsionnel couvre un exercice comptable de douze mois.
- **Sources.** `LEGIARTI000006488753`, `LEGIARTI000006239513` (decret 2005, art. 5).
- **Entrees exigees.** `budget.exercice_debut`, `budget.exercice_fin`,
  `copropriete.premier_exercice`.
- **Constat.** Exercice different de douze mois, ou premier exercice au-dela de
  dix-huit mois.
- **Ce qu'il ne prouve pas.** Rien pour le premier exercice, que l'article 5
  laisse aller jusqu'a dix-huit mois. Rien non plus contre un changement de date
  de cloture, licite sur decision motivee, sous reserve de cinq ans entre deux
  changements.

### P-4 - Delai de six mois

- **Enonce.** L'assemblee appelee a voter le budget est reunie dans les six mois
  du dernier jour de l'exercice precedent.
- **Source.** `LEGIARTI000043977299` (loi, art. 14-1 I).
- **Entrees exigees.** `vote.date_assemblee`,
  `copropriete.cloture_exercice_precedent`.
- **Constat.** Assemblee reunie au-dela du delai, avec le nombre de jours.
- **Ce qu'il ne prouve pas.** La nullite de la decision: le texte fixe un delai
  de reunion, pas une sanction. Inapplicable a la premiere assemblee.

### P-5 - Comparatif du dernier budget vote

- **Enonce.** Le projet de budget est notifie, au plus tard avec l'ordre du
  jour, accompagne du comparatif du dernier budget previsionnel vote.
- **Sources.** `LEGIARTI000053191281` (decret 1967, art. 11 I 2.),
  `LEGIARTI000006239516`.
- **Entrees exigees.** `convocation.projet_budget_notifie`,
  `convocation.comparatif_dernier_budget_vote_notifie`.
- **Constat.** Piece manquante. L'article 11 range ces documents parmi ceux
  notifies **pour la validite de la decision**.
- **Ce qu'il ne prouve pas.** Le comparatif exige est previsionnel contre
  previsionnel. Ce controle ne dit donc rien de la confrontation au realise de
  l'exercice precedent, qui n'est pas attachee au vote du budget. Il ne prouve
  pas non plus que le comparatif soit exact, seulement qu'il est present.

### P-6 - Presentation conforme au modele de l'annexe 2

- **Enonce.** Le projet de budget suit le modele obligatoire de l'annexe 2.
- **Sources.** `LEGIARTI000053191281`, `LEGIARTI000006239516`,
  `LEGIARTI000006239517`, `LEGIARTI000006239518`, `LEGIARTI000042412729`.
- **Entree exigee.** `convocation.presentation_conforme_annexe2`, qui est une
  qualification humaine.
- **Constat.** Presentation non conforme.
- **Ce qu'il ne prouve pas.** Il ne peut pas etre automatise. Les modeles ne
  sont pas reproduits sur Legifrance: seules les rubriques nommees par les
  textes modificatifs sont verifiables par machine.

### P-7 - Majorite de l'article 24

- **Enonce.** Le budget previsionnel est vote a la majorite de l'article 24.
- **Sources.** `LEGIARTI000051749514`, `LEGIARTI000043977299`.
- **Entree exigee.** `vote.article_majorite`.
- **Constat.** Majorite annoncee autre que celle de l'article 24.
- **Ce qu'il ne prouve pas.** Le decompte des voix, seulement l'article vise.
  **Dependance declaree:** la reconnaissance d'une resolution de vote du budget
  releve du typage des resolutions, tenu par un autre lot. Ce module ne type
  aucune resolution; il consomme le resultat du typage.

### P-8 - Concertation avec le conseil syndical

- **Enonce.** Le budget previsionnel est etabli en concertation avec le conseil
  syndical.
- **Source.** `LEGIARTI000049398867` (loi, art. 18 II).
- **Entree exigee.** `copropriete.concertation_conseil_syndical_tracee`.
- **Constat.** `A_VERIFIER_HUMAIN`, jamais `ECART`.
- **Ce qu'il ne prouve pas.** Aucune piece standard n'atteste la concertation.
  L'absence de trace n'est pas la preuve d'une absence de concertation: ce
  controle produit une question a poser au syndic, pas un grief.

### P-9 - Archivage des annexes

- **Enonce.** Les annexes sont conservees avec copie du proces-verbal qui vote
  le budget.
- **Source.** `LEGIARTI000006239520` (decret 2005, art. 12).
- **Entree exigee.** `copropriete.annexes_archivees_avec_pv`.
- **Constat.** Annexes non conservees avec le proces-verbal.
- **Ce qu'il ne prouve pas.** Le "classement particulier" exige par le meme
  article, qui est une modalite d'archivage que le dossier ne porte pas.

## Question ouverte 1 - la premiere annee

La question etait: un budget previsionnel N ne peut pas etre confronte a un
realise N-1 qui n'existe pas; que dit la reglementation ?

**Elle n'est pas muette.** Trois dispositions repondent, et aucune n'exige de
comparatif.

1. `LEGIARTI000006239513`, article 5 du decret du 14 mars 2005: "Pour le premier
   exercice, l'assemblee generale des coproprietaires fixe la date de cloture
   des comptes et la duree de cet exercice qui ne pourra exceder dix-huit mois."
   La regle des douze mois est donc explicitement ecartee.
2. `LEGIARTI000053191341`, derniers alineas de l'article 35 du decret de 1967:
   a la mise en copropriete, le syndic provisoire peut appeler la provision
   prevue par le reglement de copropriete; a defaut, ou une fois cette provision
   consommee, il appelle le remboursement des depenses "regulierement engagees
   et effectivement acquittees", et ce "jusqu'a la premiere assemblee generale
   reunie a son initiative qui votera le premier budget previsionnel et
   approuvera les comptes de la periode ecoulee". Le financement de la premiere
   periode ne passe donc pas par un budget vote.
3. `LEGIARTI000053191281`, article 11 I 2.: le comparatif porte sur "le dernier
   budget previsionnel vote". S'il n'en existe aucun, l'obligation n'a pas
   d'objet.

**Comportement d'outil retenu, et il ne fabrique aucun constat.** `P-5` et `P-4`
rendent `INAPPLICABLE` quand `copropriete.premier_exercice` vaut vrai, en
nommant l'entree qui manque plutot qu'en concluant a la conformite. `P-3`
bascule sur le plafond de dix-huit mois. Et quand le rang de l'exercice est
simplement **inconnu**, les deux controles refusent de choisir: un comparatif
absent peut etre une piece manquante ou l'absence de tout budget anterieur, une
duree de quinze mois peut etre irreguliere ou un premier exercice licite. Dans
les deux cas le constat est `INAPPLICABLE` et nomme `copropriete.premier_exercice`. `B-5` reste inapplicable tant que le
terme de dix ans depuis la reception des travaux n'est pas atteint, ce qui
couvre le cas d'un immeuble neuf. Le meme raisonnement vaut pour une
copropriete dont les comptes anterieurs sont indisponibles: l'entree manque, le
controle le dit, et l'outil demande la piece au lieu de trancher.

## Question ouverte 2 - l'egalite entre annexes

La question etait: l'egalite supposee est-elle bien celle-la, entre ces
annexes-la ?

**Oui pour le vote du budget, et une seule.** `LEGIARTI000006239518`, article 10
du decret du 14 mars 2005, dernier alinea: "Pour le vote du budget previsionnel,
le total des charges pour operations courantes de l'annexe n. 3 doit etre egal
au total des charges de l'annexe n. 2." L'annexe 4 n'y figure pas.

**Non pour la generalisation.** L'alinea precedent, qui vaut pour l'approbation
des comptes, pose DEUX egalites, dont une avec l'annexe 4. Les transposer au
vote du budget serait une faute.

**Et la lettre du texte n'est pas codable.** Cet alinea precedent dit deux fois
"le total des charges de l'annexe n. 2", pour l'annexe 3 puis pour l'annexe 4.
Applique litteralement, il imposerait l'egalite de l'annexe 3 et de l'annexe 4.
La lecture utile est que chaque ventilation analytique s'aligne sur son propre
bloc de l'annexe 2, mais cette lecture n'est pas dans le texte: elle vient du
modele d'annexe, qui n'est pas reproduit sur Legifrance. `B-4` s'en tient donc
au seul cas non ambigu.

## L'axe, et sa mesure sur les deux cabinets

**Axe.** La nomenclature est reglementaire et invariante. Ce qui varie est sa
presentation. La reconnaissance se fonde donc sur le numero normalise, puis, a
defaut, sur le rattachement par prefixe qui est la subdivision licite de
l'article 8. Elle ne regarde jamais le libelle.

Variations mesurees, aucune supposee:

| Variation | Cabinet A | Cabinet B |
|---|---|---|
| Ecriture du numero | numero nu | remplissage a quatre chiffres: `4501`, `5010`, `1050`, `1210` pour `450-1`, `501`, `105`, `12-1` |
| Agregation | regroupements imprimes: `60x`, `62... (autres que 621 et 622)`, `671-673` | ligne par ligne |
| Libelle | conforme au texte | `613` intitule "Locations compteurs" la ou le texte dit "Locations mobilieres" |
| Classe 66 | `661` et `662` ranges avec les travaux | `662` range avec les operations courantes |
| Structure de la convocation | annexes et ordre du jour dans un meme document | convocation eclatee en plusieurs PDF, annexes separees |

Mesure de la reconnaissance, restreinte a la region de l'annexe 2 des documents
qui portent une colonne "budget previsionnel a voter":

| | Cabinet A | Cabinet B |
|---|---:|---:|
| Blocs d'annexe 2 exploites | 13 | 4 |
| Numeros lus a cote d'un libelle | 480 | 49 |
| Reconnus directement | 396 | 43 |
| Reconnus apres normalisation | 22 | 6 |
| Non rattachables | 62 | 0 |

Les 62 non rattachables du cabinet A ne sont pas des comptes: ce sont des renvois
d'articles (`18-1`, `24`) et des numeros de page captes par la sonde de mesure,
pas par les predicats. Les 28 formes normalisees couvrent exactement les deux
familles de variation attendues: les agregats `60x` et `62...` d'un cote, le
remplissage a quatre chiffres de l'autre.

**Un compte supprime est bien en usage.** Le compte `1032`, porte "(Supprime)"
par `LEGIARTI000042413155`, apparait dans l'annexe 1 du cabinet B sur quatre
exercices, sous l'intitule "Avances travaux Art.18-6" - une reference legale
elle-meme perimee. Il est hors de la region du budget, donc `B-3` ne se declenche
pas ici: le controle existe pour le jour ou il y figurera, et la constatation
appartient a un controle d'annexe 1 qui n'est pas dans ce lot.

## Mesure des controles: applicables, et surtout inapplicables

### En l'etat du depot

Aucun extracteur d'annexes n'existe. Le `Dossier` est donc vide sur les deux
cabinets, et le resultat est le meme des deux cotes:

| | Cabinet A | Cabinet B |
|---|---:|---:|
| `CONFORME` | 0 | 0 |
| `ECART` | 0 | 0 |
| `INAPPLICABLE` | **16 / 16** | **16 / 16** |

C'est le chiffre important, et il est volontaire. Un module qui rendrait
`CONFORME` sur un dossier vide ferait passer une copropriete non verifiee pour
une copropriete en regle. Un test le verrouille.

### Si le texte deja extrait suffisait

Sonde de presence de chaque entree dans les documents qui portent une annexe 2
avec colonne "budget previsionnel a voter". Le chiffre est un nombre de blocs
d'annexe ou l'entree est detectable, pas un nombre d'exercices controles.

| Entree du contrat | Cab. A | Cab. B | Controles debloques |
|---|---:|---:|---|
| `budget.exercice_debut` | 10 | 2 | P-1, P-2, P-3 |
| `budget.exercice_fin` | 10 | 2 | P-3 |
| `budget.lignes` | 10 | 2 | B-1, B-2, B-3 |
| `budget.lignes[].montant` | **0** | **0** | B-1 |
| `budget.total_charges` | 10 | 2 | B-5, B-6, B-7 |
| `annexes.total_charges_annexe2_courantes` | 10 | 2 | B-4 |
| `annexes.total_charges_annexe3_courantes` | 7 | 2 | B-4 |
| `annexes.solde_fonds_travaux` | 10 | 2 | B-7 |
| `convocation.comparatif_dernier_budget_vote_notifie` | 10 | 2 | P-5 |
| `convocation.projet_budget_notifie` | 4 | **0** | P-5 |
| `convocation.question_suspension_cotisation_inscrite` | **0** | **0** | B-7 |
| `convocation.presentation_conforme_annexe2` | **0** | **0** | P-6 |
| `copropriete.cloture_exercice_precedent` | 10 | 2 | P-4 |
| `copropriete.destination_habitation` | 4 | **0** | B-5 |
| `copropriete.date_reception_travaux_construction` | **0** | **0** | B-5 |
| `copropriete.plan_pluriannuel_adopte` | **0** | **0** | B-5 |
| `copropriete.cotisation_fonds_travaux_votee` | 1 | **0** | B-5 |
| `copropriete.avance_reserve_prevue_reglement` | 4 | **0** | B-6 |
| `copropriete.premier_exercice` | **0** | **0** | P-3 et P-5, conditionnellement |
| `copropriete.concertation_conseil_syndical_tracee` | **0** | **0** | P-8 |
| `copropriete.annexes_archivees_avec_pv` | **0** | **0** | P-9 |
| `vote.date_assemblee` | 4 | **0** | P-1, P-2, P-4 |
| `vote.article_majorite` | 4 | **0** | P-7 |
| `vote.autorisation_provisions_transitoires` | 1 | **0** | P-2 |

Trois lectures s'imposent.

**Le montant du budget n'est jamais lisible en l'etat.** `budget.lignes[].montant`
est a zero des deux cotes: les numeros de compte et les libelles se lisent, la
colonne de chiffres correspondante non. C'est le verrou du lot, et c'est le meme
que celui de `RM-2026-0074`.

**Le cabinet B eclate sa convocation, ce qui casse toute lecture par document.**
Ses annexes sont dans un PDF, l'ordre du jour dans un autre. Toutes les entrees
de contexte - date d'assemblee, majorite, destination de l'immeuble, avance de
reserve - y sont a zero non parce qu'elles manquent, mais parce qu'elles ne sont
pas dans le document qui porte l'annexe. **Le contrat d'entree doit etre par
assemblee, pas par document.**

**Deux exercices sur quatre sont perdus chez le cabinet B.** Sur ses quatre
exercices 2023 a 2026, deux seulement portent une annexe 2 avec en-tetes de
colonnes lisibles; les deux autres sont des scans dont l'extraction a perdu la
structure. Ce n'est pas un defaut de la grille: c'est un defaut de source, et il
doit etre dit comme tel dans un rapport.

**Trois controles resteront inapplicables meme avec un extracteur parfait:**
`P-6` (conformite au modele, qualification humaine), `P-8` (concertation, aucune
piece standard), `P-9` (archivage, etat du classement hors document). Ils
appellent une saisie humaine ou une demande au syndic, pas de l'extraction.

## Ce qui manque en entree - contrat pour `RM-2026-0074`

Ce lot ne construit aucun extracteur. Il declare ce qu'il attend. La forme est
celle des dataclasses de `_budget_previsionnel_modele.py`. Toute valeur absente
reste `None`; **`None` ne doit jamais etre remplace par zero**, sans quoi la
distinction entre "verifie" et "pas verifiable" disparait.

Portee: **une assemblee generale**, pas un document. Un cabinet mesure eclate sa
convocation en plusieurs PDF; l'extracteur doit consolider avant de rendre.

| Objet | Champs attendus | Source documentaire probable |
|---|---|---|
| `BudgetPrevisionnel` | `exercice_debut`, `exercice_fin`, `lignes[(compte_brut, libelle, montant)]`, `total_charges`, `total_produits` | colonne "budget previsionnel a voter" de l'annexe 2 |
| `Annexes` | `total_charges_annexe2_courantes`, `total_charges_annexe3_courantes`, `solde_fonds_travaux` | annexes 1, 2 et 3 |
| `Vote` | `date_assemblee`, `article_majorite`, `adopte`, `budget_precedent_vote`, `autorisation_provisions_transitoires`, `provisions_transitoires_appelees`, `assiette_provisions_transitoires`, `modalites_de_provision_votees`, `montant_provision_periodique` | proces-verbal et resolutions typees |
| `Convocation` | `projet_budget_notifie`, `comparatif_dernier_budget_vote_notifie`, `presentation_conforme_annexe2`, `question_suspension_cotisation_inscrite` | convocation et ordre du jour |
| `Copropriete` | `destination_habitation`, `date_reception_travaux_construction`, `plan_pluriannuel_adopte`, `montant_travaux_plan_adopte`, `premier_exercice`, `cloture_exercice_precedent`, `avance_reserve_prevue_reglement`, `cotisation_fonds_travaux_votee`, `concertation_conseil_syndical_tracee`, `annexes_archivees_avec_pv` | reglement de copropriete, fiche synthetique, PPPT, saisie humaine |

Deux exigences supplementaires sur le format des lignes de budget:

- `compte_brut` doit etre conserve tel qu'imprime. C'est la seule facon de
  rendre compte d'un regroupement de presentation comme `671-673` sans le
  maquiller en compte reel.
- une ligne sans montant lu doit porter `montant=None` et non `0.0`. `B-1`
  rend alors `INAPPLICABLE` au lieu de conclure a un perimetre propre.

Champs qui ne viendront jamais d'un extracteur et qu'il faudra saisir ou
demander: `premier_exercice`, `concertation_conseil_syndical_tracee`,
`annexes_archivees_avec_pv`, `presentation_conforme_annexe2`,
`date_reception_travaux_construction`.

## Confidentialite

Aucun nom, aucun montant nominatif, aucun chemin local ne figure dans cette
grille. Les cabinets sont designes par alias. Les deux instances sont restees en
lecture seule.
