# Referentiel de conformite extranet - V0

Date: 2026-09-03.
Rattachement: `RM-2026-0047`.
Statut: `BROUILLON_NON_VERIFIE`.
Diffusion: interne projet.

## Avertissement de fiabilite

Ce referentiel a ete redige **sans acces reseau a Legifrance**: la session
distante qui l'a produit a la sortie internet fermee (`legifrance.gouv.fr`,
`service-public.fr` et `coprodirecte.fr` sont refuses par la passerelle).

Toutes les bases legales ci-dessous portent donc le statut
`SOURCE_A_VERIFIER`. Aucune n'a ete relue dans sa version en vigueur.

Regle de securite associee, opposable au code:

> Une rubrique dont la base legale est `SOURCE_A_VERIFIER` ne peut jamais
> produire un verdict `NON_CONFORME`. Elle produit au mieux `INDETERMINE`.

La levee du statut se fait avec la skill `piste-api` depuis le poste de Brice,
en citant pour chaque ligne l'identifiant `LEGIARTI...` et la date de version
retenue. Tant que cette passe n'est pas faite, le referentiel sert de plan de
verification, pas de grille de controle.

## Ce que le referentiel est, et n'est pas

Il decrit **la norme attendue**, independamment de tout editeur d'extranet.
C'est la partie stable du dispositif: elle ne bouge qu'avec le droit.

Il ne decrit pas **comment lire une page** chez un editeur donne. Cette partie
fragile appartient aux adaptateurs, et change a chaque refonte d'interface.

Cette separation est la decision d'architecture principale du chantier. La
melanger produirait un outil qui se casse a chaque mise a jour d'extranet et
dont on ne saurait plus si une erreur vient du droit ou de la lecture.

## Vocabulaire des verdicts

| Verdict | Sens | Condition d'emission |
|---|---|---|
| `CONFORME` | Rubrique servie et satisfaisant les criteres. | Observation + base legale `VERIFIE`. |
| `NON_CONFORME` | Rubrique attendue et non servie, ou servie hors criteres. | Observation + couverture d'exploration prouvee + base legale `VERIFIE`. |
| `INDETERMINE` | On ne peut pas conclure. | Base legale non verifiee, couverture insuffisante, adaptateur en echec. |
| `SANS_OBJET` | L'obligation ne s'applique pas a cette copropriete. | Dispense votee, seuil non atteint, immeuble hors champ. |

`INDETERMINE` est le verdict par defaut. Un outil de controle qui ne sait pas
dire "je ne sais pas" fabrique des faux manquements, ce qui est le pire echec
possible ici: il detruit la credibilite du conseil syndical qui s'en sert.

## Regle de couverture d'exploration

Le plugin n'observe que ce que l'utilisateur ouvre lui-meme. Une rubrique
jamais visitee est `NON_EXPLORE`, jamais `ABSENT`.

Pour conclure a une absence, il faut avoir observe **la page d'index qui
enumere la categorie** de la rubrique attendue. Sans cette observation, la
qualification reste `INDETERMINE`.

C'est la transposition directe d'une regle d'echantillonnage: on ne conclut a
l'absence d'une espece que si le protocole d'observation couvrait l'habitat ou
elle aurait du se trouver.

## Etape 0 - controles prealables

Ces deux controles conditionnent tous les autres. Ils doivent passer avant
toute qualification de rubrique.

| ID | Controle | Base legale presumee | Statut source | Observable | Effet si echec |
|---|---|---|---|---|---|
| `EXT-000` | Un espace en ligne securise existe et est accessible au compte. | Loi 65-557, art. 18 II | `SOURCE_A_VERIFIER` | Connexion aboutie, arborescence lisible. | Manquement de premier rang; tout le reste devient sans objet. |
| `EXT-001` | Un espace distinct est servi au conseil syndical. | Loi 65-557, art. 18 II; decret 67-223, art. 33-1-1 | `SOURCE_A_VERIFIER` | Presence d'une zone dont le contenu depasse le college "tous coproprietaires". | Le college C entier passe `NON_CONFORME` en bloc, pas rubrique par rubrique. |
| `EXT-002` | Aucune resolution d'assemblee ne dispense le syndic de l'espace en ligne. | Loi 65-557, art. 18 II (dispense a la majorite de l'art. 25) - **a confirmer** | `SOURCE_A_VERIFIER` | Lecture des proces-verbaux des trois derniers exercices. | Si dispense votee: tout le referentiel bascule `SANS_OBJET`. |

`EXT-002` est le facteur de confusion a ecarter avant de conclure quoi que ce
soit. Il ne s'observe pas sur l'extranet mais dans les proces-verbaux, donc il
depend d'une lecture humaine ou de DocOps, pas de l'adaptateur.

## College A - documents accessibles a tous les coproprietaires

Base presumee: loi 65-557, art. 18 II, alinea 1; decret 67-223, art. 33-1-1.
Statut source de la liste entiere: `SOURCE_A_VERIFIER`.

| ID | Rubrique attendue | Critere de presence | Critere de fraicheur | Critere complementaire |
|---|---|---|---|---|
| `EXT-A-01` | Reglement de copropriete | Document servi et ouvrable. | Sans objet. | Modificatifs publies presents s'ils existent. |
| `EXT-A-02` | Etat descriptif de division | Document servi et ouvrable. | Sans objet. | Somme des tantiemes coherente avec les cles utilisees en comptabilite. |
| `EXT-A-03` | Derniere fiche synthetique de la copropriete | Document servi. | Millesime de l'exercice precedent au plus. | Mise a jour annuelle; art. 8-2 prevoit des penalites de retard - a confirmer. |
| `EXT-A-04` | Carnet d'entretien de l'immeuble | Document servi. | Derniere mise a jour datee. | Doit refleter les travaux votes et receptionnes. |
| `EXT-A-05` | Diagnostics techniques | Chaque diagnostic applicable servi. | En cours de validite a la date d'observation. | Un diagnostic perime present est `NON_CONFORME`, pas `CONFORME`. |
| `EXT-A-06` | Contrat de syndic en cours | Document servi. | Periode de mandat couvrant la date d'observation. | Conformite au contrat type - decret 2015-342, a confirmer. |
| `EXT-A-07` | Proces-verbaux des assemblees des trois derniers exercices | Trois exercices servis. | Chaque proces-verbal date; delai de mise en ligne mesurable. | Annexes du proces-verbal presentes. |
| `EXT-A-08` | Contrats d'assurance de l'immeuble en cours | Document servi. | Periode de garantie couvrant la date d'observation. | Une attestation echue vaut `NON_CONFORME`. |
| `EXT-A-09` | Annexes comptables du dernier exercice clos | Annexes 1 a 5 servies. | Dernier exercice clos. | Rapprochement avec la balance du college C. |

## College B - documents propres a chaque coproprietaire

| ID | Rubrique attendue | Critere de presence | Critere de fraicheur | Critere complementaire |
|---|---|---|---|---|
| `EXT-B-01` | Compte individuel du coproprietaire | Situation de compte servie. | A jour du dernier appel. | Aucun compte de tiers visible depuis ce college. |
| `EXT-B-02` | Charges courantes et hors budget des deux derniers exercices clos | Montants servis pour deux exercices. | Deux derniers exercices clos. | Coherence avec les annexes `EXT-A-09`. |
| `EXT-B-03` | Avis d'echeance et appels de fonds | Documents servis. | Appel en cours present. | Montant appele coherent avec le budget vote. |

Point de vigilance donnees personnelles: si une page du college B laisse voir
des donnees d'un autre coproprietaire, c'est un defaut de cloisonnement de
l'extranet. C'est un constat a remonter, et surtout une donnee a **ne pas
capturer**. L'adaptateur doit s'arreter, pas enregistrer.

## College C - documents reserves au conseil syndical

Base presumee: loi 65-557, art. 18 II; decret 67-223, art. 33-1-1.

| ID | Rubrique attendue | Critere de presence | Critere de fraicheur | Critere complementaire |
|---|---|---|---|---|
| `EXT-C-01` | Releves bancaires du compte separe du syndicat | Releves servis. | Serie continue jusqu'au dernier mois clos. | Absence de trou dans la serie mensuelle. |
| `EXT-C-02` | Balance generale des comptes du syndicat | Balance servie et exportable. | Exercice en cours et dernier exercice clos. | Controles arithmetiques ci-dessous. |
| `EXT-C-03` | Contrats d'assurance en cours du syndicat | Documents servis. | Garanties en cours. | Distinguer assurance de l'immeuble et responsabilite civile. |
| `EXT-C-04` | Contrats d'entretien et de maintenance en cours | Liste servie et documents ouvrables. | Contrats en cours a la date d'observation. | Rapprochement avec les charges recurrentes de la balance. |
| `EXT-C-05` | Marches de travaux en cours | Documents servis. | Marches non solde a la date d'observation. | Rapprochement avec les resolutions d'assemblee. |
| `EXT-C-06` | Carte professionnelle, garantie financiere et assurance responsabilite civile professionnelle du syndic | Documents servis. | En cours de validite. | Recoupement avec les registres d'entreprises. |
| `EXT-C-07` | Etat des impayes et des creances | Etat servi. | Arrete a une date lisible. | **Presence dans la liste minimale a confirmer.** |

## Controles arithmetiques sur `EXT-C-02`

Ces controles sont deterministes: ils produisent un ecart chiffre, jamais un
jugement. C'est ce qui les rend publiables sans risque d'accusation.

| ID | Controle | Attendu |
|---|---|---|
| `EXT-CTRL-01` | Equilibre de la balance | Total des debits egal au total des credits. |
| `EXT-CTRL-02` | Classe 4 contre etat des impayes | Somme des soldes debiteurs coproprietaires egale a l'etat `EXT-C-07`. |
| `EXT-CTRL-03` | Classe 5 contre releves bancaires | Solde de tresorerie egal au solde bancaire a la meme date. |
| `EXT-CTRL-04` | Fonds de travaux | Solde comptable adosse a un compte separe remunere - loi 65-557, art. 14-2-1, a confirmer. |
| `EXT-CTRL-05` | Balance contre annexes comptables | Les annexes `EXT-A-09` sont des recompositions de la balance; tout ecart non nul est a expliquer. |
| `EXT-CTRL-06` | Repartition par cle contre tantiemes | Cles de charges coherentes avec `EXT-A-02`. |

`EXT-CTRL-05` est le controle le plus solide du dispositif: il ne compare pas
un document a une opinion, mais deux expressions du meme objet qui doivent
coincider par construction.

## Obligations connexes, hors liste minimale

Ces points ne relevent pas de l'article 33-1-1 mais se verifient par
recoupement avec des sources publiques independantes du syndic. C'est le seul
ancrage externe du dispositif.

| ID | Obligation | Source de controle independante | Statut source |
|---|---|---|---|
| `EXT-D-01` | Immatriculation au registre national des coproprietes et declaration annuelle a jour | Donnees ouvertes du registre national; skill `datagouv-tabulaire` | `SOURCE_A_VERIFIER` |
| `EXT-D-02` | Existence juridique et dirigeants de la societe de syndic | Registres d'entreprises; skills `registres-entreprises` et `sirene-insee` | `SOURCE_A_VERIFIER` |
| `EXT-D-03` | Plan pluriannuel de travaux selon age et taille de l'immeuble | Loi 65-557, art. 14-2 | `SOURCE_A_VERIFIER` |
| `EXT-D-04` | Fonds de travaux et son compte separe | Loi 65-557, art. 14-2-1 | `SOURCE_A_VERIFIER` |
| `EXT-D-05` | Diagnostic de performance energetique collectif | Code de la construction et de l'habitation | `SOURCE_A_VERIFIER` |

Un desaccord entre le registre national et l'extranet est un indicateur a
haute valeur: les deux declarations emanent du meme syndic, a des
destinataires differents.

## Indicateurs de delai

Mesurables seulement par observation repetee. C'est l'apport propre du plugin:
un audit ponctuel ne les voit pas.

| ID | Delai mesure | Norme presumee | Statut source |
|---|---|---|---|
| `EXT-T-01` | Assemblee generale -> mise en ligne du proces-verbal | Notification sous un mois - a confirmer | `SOURCE_A_VERIFIER` |
| `EXT-T-02` | Demande ecrite du conseil syndical -> communication du document | Un mois, puis penalites par jour de retard sur les honoraires de gestion courante - loi 65-557, art. 21, a confirmer | `SOURCE_A_VERIFIER` |
| `EXT-T-03` | Convocation -> ouverture de la consultation des pieces justificatives | Loi 65-557, art. 18-1 | `SOURCE_A_VERIFIER` |
| `EXT-T-04` | Anciennete d'une rubrique annoncee "a venir" ou vide | Aucune norme; indicateur de suivi | Sans objet |

## Passe de verification a executer

A faire depuis le poste de Brice, avec la skill `piste-api`, avant tout code:

1. Loi 65-557 du 10 juillet 1965, articles 18, 18-1, 21, 8-2, 14-2 et 14-2-1.
2. Decret 67-223 du 17 mars 1967, article 33-1-1 et suivants.
3. Decret 2019-502 du 23 mai 2019, texte complet.
4. Decret 2015-342 du 26 mars 2015, contrat type de syndic, pour `EXT-T-02`.
5. Decret 2005-240 du 14 mars 2005, plan comptable, pour les annexes 1 a 5.

Pour chaque ligne du referentiel, la passe doit produire: identifiant
`LEGIARTI...`, date de version retenue, et statut `VERIFIE` ou `ECARTE`.
Toute ligne restee `SOURCE_A_VERIFIER` reste bloquee en `INDETERMINE`.
