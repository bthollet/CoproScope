# Referentiel de conformite extranet - V1 verifiee

Date: 2026-09-04.
Rattachement: `RM-2026-0091` / `CH-20260903-090000-RM-2026-0047-extranet-conformite` / `CONV-2026-2137`.
Renumerotation: le lot avait ete ouvert en session cloud sous `RM-2026-0047`, numero
deja attribue au lot Audit des comptes bancaires le 2026-08-20. La session distante
travaillait sur une base de juin ou ce numero n'existait pas. L'identifiant de
chantier est conserve tel quel: il porte la trace de l'ouverture.
Seconde renumerotation, le 2026-09-07: `RM-2026-0085` etait a son tour en
collision, sur `main`, avec le lot du venv partage - et connaissait meme un
troisieme sens dans un lot de systeme de design anterieur. Le lot passe a
`RM-2026-0091`, ses deux items lies a `RM-2026-0092` et `RM-2026-0093`.
`RM-2026-0090` est saute: deja employe par un lot reel jamais inscrit au
gouvernail.
Statut: `VERIFIE`. Seconde passe du 2026-09-04: les cinq textes du plan de
verification ont ete relus. Une seule reserve subsiste, section finale.
Diffusion: interne projet.
Remplace: [`referentiel_conformite_extranet_v0.md`](./referentiel_conformite_extranet_v0.md),
conserve comme trace de l'etat non verifie.

## Ce que cette version change, et pourquoi

La V0 a ete redigee par une session distante **sans acces reseau a Legifrance**.
Toutes ses bases legales portaient `SOURCE_A_VERIFIER`, et elle interdisait
elle-meme d'en tirer un verdict `NON_CONFORME`.

Cette passe a ete faite depuis le poste local avec la skill `piste-api`, en
lecture seule, sur l'etat du droit **en vigueur au 2026-09-03**. Douze textes
relus. La regle de securite de la V0 est confirmee comme necessaire: **cinq
corrections de fond** ont ete trouvees, dont quatre auraient produit des faux
manquements et une aurait masque cinq obligations reelles.

| # | Ce que disait la V0 | Ce que dit le texte relu | Effet si on ne l'avait pas vu |
|---|---|---|---|
| 1 | Base de l'extranet: loi 65-557 **art. 18 II** | **art. 18 I**, dernier alinea. Le II traite du compte separe et de la comptabilite. | Citation fausse dans tout rapport remis au conseil syndical. |
| 2 | Listes minimales tirees du **decret 67-223 art. 33-1-1** | Les listes sont dans le **decret 2019-502 du 23 mai 2019**, articles 1, 2 et 3. L'article 33-1-1 existe mais porte les modalites d'acces, pas les listes. | Le referentiel n'aurait jamais pu etre justifie ligne par ligne devant le syndic. |
| 3 | College C: assurances, contrats d'entretien, marches de travaux | Ces trois rubriques sont au **college A**, article 1er 5°, 6° et 7°: elles sont dues a **tous les coproprietaires**, pas au seul conseil syndical. | Trois obligations declarees satisfaites parce que cherchees dans le mauvais college. |
| 4 | `EXT-A-09` annexes comptables, `EXT-C-07` etat des impayes | **Absents des trois listes minimales.** La V0 signalait deja un doute sur `EXT-C-07`. | Deux manquements reproches a tort a un syndic conforme. |
| 5 | Aucun critere transversal | L'article 33-1-1 impose que les documents soient **telechargeables et imprimables**, et que l'espace entier soit **actualise dans les trois mois suivant l'assemblee annuelle des comptes**. | Deux controles simples, observables par un plugin, purement absents du dispositif. |

Cinq rubriques legalement dues manquaient par ailleurs a la V0: elles sont
ajoutees ci-dessous et marquees **`NOUVEAU`**.

## Bases legales relues

Toutes lues dans leur version en vigueur au **2026-09-03**. Un identifiant
`LEGIARTI` designe une **version** d'article, pas l'article: le citer sans sa
date ne prouve rien.

| Reference | Identifiant de version | Ce qu'elle fonde |
|---|---|---|
| Loi 65-557, art. 18 I | `LEGIARTI000049398867` | Existence de l'obligation, limite aux **syndics professionnels**, acces differencie, dispense a la majorite de l'art. 25. |
| Loi 65-557, art. 18-1 | `LEGIARTI000042120918` | Consultation des pieces justificatives des charges entre convocation et tenue de l'AG. |
| Loi 65-557, art. 21 | `LEGIARTI000039313574` | Missions du conseil syndical; **penalites par jour de retard** au-dela d'un mois apres demande. |
| Loi 65-557, art. 8-2 | `LEGIARTI000039313533` | Fiche synthetique, mise a jour annuelle, penalites au-dela d'un mois apres demande. |
| Loi 65-557, art. 14-2 | `LEGIARTI000043977289` | Projet de plan pluriannuel de travaux. |
| Loi 65-557, art. 14-2-1 | `LEGIARTI000043967792` | Fonds de travaux. |
| Decret 67-223, art. 33-1-1 | `LEGIARTI000042078765` | Modalites d'acces, format, **rythme d'actualisation**. |
| Decret 67-223, art. 32 | `LEGIARTI000053191325` | Liste des coproprietaires visee au college C. |
| Decret 2019-502, art. 1 | `LEGIARTI000042412719` | **Liste minimale college A.** |
| Decret 2019-502, art. 2 | `LEGIARTI000038503795` | **Liste minimale college B.** |
| Decret 2019-502, art. 3 | `LEGIARTI000038503789` | **Liste minimale college C.** |
| Decret 2005-240, annexes 1 a 5 | `LEGIARTI000042412731`, `LEGIARTI000042412729`, `LEGIARTI000033839910`, `LEGIARTI000033839957`, `LEGIARTI000033839959` | Les cinq annexes comptables. **Contenu non reproduit par Legifrance**, voir la reserve finale. |
| Decret 2020-1229, art. 1 et 2 | `LEGIARTI000042411558`, `LEGIARTI000042411560` | Montant des penalites de retard: **15 euros par jour** pour l'art. 8-2 comme pour l'art. 21. |
| CCH, art. L. 711-1 | `LEGIARTI000033974279` | Institution du registre national d'immatriculation des syndicats. |
| CCH, art. L. 711-2 | `LEGIARTI000049398053` | Donnees a declarer au registre, **et toute modification les concernant**. |
| CCH, art. L. 711-6 | `LEGIARTI000028779458` | **Un coproprietaire** peut mettre le syndic en demeure de s'immatriculer, par lettre recommandee. |
| CCH, art. L. 126-31 | `LEGIARTI000054140304` | Diagnostic de performance energetique collectif, avec ses conditions d'application. |

Identifiants de texte utiles: loi 65-557 `LEGITEXT000006068256`, decret 67-223
`LEGITEXT000006061423`, decret 2019-502 `LEGITEXT000038503779`.

> Piege rencontre, a garder en memoire: l'identifiant `LEGITEXT000006061419`,
> plausible pour le decret 67-223, designe en realite un decret de 1967 sur les
> statuts de fonctionnaires. Un identifiant qui ressemble n'est pas un
> identifiant verifie.

## Ce que le referentiel est, et n'est pas

Inchange depuis la V0, et c'est la decision d'architecture principale du
chantier: ce document decrit **la norme attendue**, independamment de tout
editeur. Lire une page chez un editeur donne appartient aux adaptateurs.
Melanger les deux produit un outil qui casse a chaque refonte d'interface et
dont on ne sait plus si une erreur vient du droit ou de la lecture.

## Vocabulaire des verdicts

| Verdict | Sens | Condition d'emission |
|---|---|---|
| `SERVI_EN_APPARENCE` | Une piece occupe la rubrique attendue. **Ne dit rien de sa validite.** | Observation de presence seule. |
| `CONFORME` | Rubrique servie **et** satisfaisant les criteres. | Observation + **lecture de la piece** + base legale `VERIFIE`. |
| `NON_CONFORME` | Rubrique attendue et non servie, ou servie hors criteres. | Observation + couverture d'exploration prouvee + base legale `VERIFIE`. |
| `INDETERMINE` | On ne peut pas conclure. | Base legale non verifiee, couverture insuffisante, adaptateur en echec. |
| `SANS_OBJET` | L'obligation ne s'applique pas a cette copropriete. | Dispense votee, syndic non professionnel, immeuble hors champ. |

**`SERVI_EN_APPARENCE` est le verdict que rend une observation d'extranet, et
il ne doit jamais etre affiche comme `CONFORME`.** Mise en garde de Brice le
2026-09-06: *attention au faux servi*. Une rubrique peut porter le bon nombre de
pieces sans que ce soient les bonnes - une attestation d'assurance perimee, un
projet de contrat au lieu du contrat signe, un extrait au lieu du
proces-verbal complet, un diagnostic hors validite.

Passer de l'apparence a la conformite exige de **lire la piece**, ce que
l'observation ne fait pas et ce que le plugin ne fera jamais. C'est la ou le
rattachement a CoproScope prend sa force, et c'est un chantier a part entiere.

`INDETERMINE` reste le verdict par defaut. Un outil de controle qui ne sait pas
dire "je ne sais pas" fabrique des faux manquements, ce qui detruit la
credibilite du conseil syndical qui s'en sert.

## Regle de couverture d'exploration

Inchangee. Le plugin n'observe que ce que l'utilisateur ouvre lui-meme. Une
rubrique jamais visitee est `NON_EXPLORE`, jamais `ABSENT`. Pour conclure a une
absence, il faut avoir observe **la page d'index qui enumere la categorie** ou
la rubrique aurait du se trouver.

## Etape 0 - controles prealables

| ID | Controle | Base legale | Statut | Observable | Effet si echec |
|---|---|---|---|---|---|
| `EXT-000` | Un espace en ligne securise existe et est accessible au compte. | Loi 65-557, art. 18 I | `VERIFIE` | Connexion aboutie, arborescence lisible. | Manquement de premier rang; le reste devient sans objet. |
| `EXT-001` | Un espace distinct est servi au conseil syndical. | Loi 65-557, art. 18 I; decret 2019-502, art. 3 | `VERIFIE` | Zone dont le contenu depasse le college "tous coproprietaires". | Le college C entier passe `NON_CONFORME` en bloc. |
| `EXT-002` | Aucune resolution d'assemblee ne dispense le syndic de l'espace en ligne. | Loi 65-557, art. 18 I | `VERIFIE` | Lecture des proces-verbaux. | Si dispense votee: tout le referentiel bascule `SANS_OBJET`. |
| `EXT-003` **`NOUVEAU`** | Le syndic est un **syndic professionnel**. | Loi 65-557, art. 18 I | `VERIFIE` | Contrat de syndic, carte professionnelle. | Si syndic benevole ou cooperatif: tout le referentiel est `SANS_OBJET`. |

`EXT-002` et `EXT-003` sont les deux facteurs de confusion a ecarter avant de
conclure quoi que ce soit. Le texte reserve l'obligation au syndic
professionnel et la soumet a une dispense votable **a la majorite de l'article
25**; ni l'un ni l'autre ne s'observe sur l'extranet.

## Criteres transversaux - decret 67-223, art. 33-1-1

Ils s'appliquent a **toute** rubrique des trois colleges. Absents de la V0.

| ID | Controle | Verbatim | Observable |
|---|---|---|---|
| `EXT-X-01` **`NOUVEAU`** | Acces par code personnel securise, identification fiable. | *"au moyen d'un code personnel securise garantissant la fiabilite de l'identification des coproprietaires"* | Presence d'une authentification nominative, pas d'un code partage. |
| `EXT-X-02` **`NOUVEAU`** | Documents **telechargeables et imprimables**. | *"Les documents mis a disposition par le syndic dans cet espace sont telechargeables et imprimables."* | Un document consultable en lecture seule, sans telechargement, est `NON_CONFORME`. |
| `EXT-X-03` **`NOUVEAU`** | Actualisation au moins annuelle, **dans les trois mois suivant l'AG annuelle des comptes**. | *"actualises au minimum une fois par an par le syndic, dans les trois mois suivant la derniere assemblee generale annuelle ayant ete appelee a connaitre des comptes"* | Date de la derniere AG des comptes + horodatage des rubriques. |

`EXT-X-02` est le controle le plus rentable du dispositif: il est binaire,
observable en une interaction, ne demande aucune interpretation, et un extranet
qui affiche sans laisser telecharger est un cas frequent.

`EXT-X-03` remplace les criteres de fraicheur inventes rubrique par rubrique
dans la V0. La norme est **globale et unique**, ce qui la rend mesurable.

## College A - accessible a tous les coproprietaires

Base: decret 2019-502, art. 1er, version `LEGIARTI000042412719`. Statut `VERIFIE`.
Neuf rubriques, reprises dans l'ordre du texte.

| ID | Rubrique legale | Critere de presence | Critere complementaire |
|---|---|---|---|
| `EXT-A-01` | Reglement de copropriete, etat descriptif de division et actes les modifiant | Documents servis et ouvrables. | **Uniquement s'ils ont ete publies** - condition posee par le texte; un modificatif non publie n'est pas du. |
| `EXT-A-02` | Derniere fiche synthetique (loi art. 8-2) | Document servi. | Millesime coherent avec la mise a jour annuelle de l'art. 8-2. |
| `EXT-A-03` | Carnet d'entretien de l'immeuble | Document servi. | Derniere mise a jour datee. |
| `EXT-A-04` | Diagnostics techniques des **parties communes** | Chaque diagnostic applicable servi. | **En cours de validite**: le texte ne vise que ceux-la, donc un diagnostic perime ne satisfait pas l'obligation. |
| `EXT-A-05` | Contrats d'assurance de l'immeuble conclus par le syndic au nom du syndicat | Documents servis. | **En cours de validite.** Une attestation echue ne satisfait pas l'obligation. |
| `EXT-A-06` **`NOUVEAU`** | **L'ensemble des contrats et marches en cours** signes par le syndic au nom du syndicat | Liste servie et documents ouvrables. | Exclusion expresse: **contrats de travail des preposes du syndicat**. Rubrique la plus large du college. |
| `EXT-A-07` **`NOUVEAU`** | Contrats d'entretien et de maintenance des **equipements communs** en cours | Liste servie et documents ouvrables. | Rapprochement avec les charges recurrentes de la balance. |
| `EXT-A-08` | Proces-verbaux des **trois dernieres assemblees generales annuelles appelees a connaitre des comptes** | Trois proces-verbaux servis. | **Et les devis de travaux approuves lors de ces assemblees** - second membre de la meme obligation, oublie par la V0. |
| `EXT-A-09` | Contrat de syndic en cours | Document servi. | Periode de mandat couvrant la date d'observation. |

Deux precisions de comptage qui changent le resultat:

- l'unite n'est pas l'exercice mais **l'assemblee annuelle appelee a connaitre
  des comptes**. Une copropriete qui a tenu deux assemblees dans l'annee, dont
  une seule sur les comptes, n'en compte qu'une;
- `EXT-A-06` et `EXT-A-07` se recouvrent partiellement. Un contrat d'entretien
  est aussi un contrat en cours. Le controle doit dedupliquer, sinon il compte
  deux manquements pour une seule piece absente.

## College B - propre a chaque coproprietaire

Base: decret 2019-502, art. 2, version `LEGIARTI000038503795`. Statut `VERIFIE`.

| ID | Rubrique legale | Critere de presence | Critere complementaire |
|---|---|---|---|
| `EXT-B-01` | Compte individuel du coproprietaire | Situation de compte servie. | **Arrete apres approbation des comptes par l'assemblee annuelle** - ce n'est pas "a jour du dernier appel" comme l'ecrivait la V0. |
| `EXT-B-02` | Charges courantes et hors budget previsionnel des **deux derniers exercices clos**, payees par le coproprietaire | Montants servis pour deux exercices. | Le texte vise ce qui a ete **paye**, pas ce qui a ete appele. |
| `EXT-B-03` **`NOUVEAU`** | Part du **fonds de travaux rattachee au lot** | Montant servi. | Du **seulement si** le syndicat dispose d'un fonds de travaux; sinon `SANS_OBJET`. Arrete apres approbation des comptes. |
| `EXT-B-04` | Avis d'appel de fonds | Documents servis. | **Sur les trois dernieres annees** - duree fixee par le texte, absente de la V0. |

Point de vigilance donnees personnelles, inchange et renforce: si une page du
college B laisse voir des donnees d'un autre coproprietaire, c'est un defaut de
cloisonnement. C'est un constat a remonter et une donnee a **ne pas capturer**.
L'adaptateur doit s'arreter, pas enregistrer.

## College C - reserve aux membres du conseil syndical

Base: decret 2019-502, art. 3, version `LEGIARTI000038503789`. Statut `VERIFIE`.
Le texte rattache expressement ce college aux **missions d'assistance et de
controle definies a l'article 21** de la loi.

| ID | Rubrique legale | Critere de presence | Critere complementaire |
|---|---|---|---|
| `EXT-C-01` | Balances generales des comptes du syndicat | Balance servie. | **Et le releve general des charges et produits de l'exercice echu** - second membre oublie par la V0. |
| `EXT-C-02` | Releves periodiques des comptes bancaires separes | Releves servis. | *"Le cas echeant"*: absence de compte separe a ecarter avant de conclure. Serie mensuelle sans trou. |
| `EXT-C-03` **`NOUVEAU`** | **Assignations en justice** delivrees au nom du syndicat pour les procedures en cours, et **decisions de justice dont les delais de recours n'ont pas expire** | Documents servis. | Rubrique a **fort enjeu** pour un conseil syndical: c'est la seule qui revele un contentieux en cours. Totalement absente de la V0. |
| `EXT-C-04` **`NOUVEAU`** | **Liste de tous les coproprietaires** etablie en application du decret 67-223, art. 32 | Liste servie. | **Contient etat civil, domicile et adresse electronique** de chaque coproprietaire. A constater comme presente ou absente; **ne jamais capturer le contenu**. |
| `EXT-C-05` | Carte professionnelle du syndic, attestation d'assurance responsabilite civile professionnelle, attestation de **garantie financiere** | Trois documents servis. | **En cours de validite**, article 3 de la loi 70-9 du 2 janvier 1970. Recoupement possible avec les registres d'entreprises. |

## Rubriques ecartees de la liste minimale

Elles ne sont pas illegitimes, mais elles **ne relevent pas de l'article 18 I**.
Les y laisser produirait des manquements imaginaires.

| Rubrique V0 | Sort | Motif |
|---|---|---|
| `EXT-A-09` V0, annexes comptables du dernier exercice clos | **ECARTE** de la liste minimale | Ne figure dans aucun des trois articles du decret 2019-502. Reste due par d'autres voies - convocation de l'AG des comptes - mais pas au titre de l'extranet. |
| `EXT-C-07` V0, etat des impayes et creances | **ECARTE** de la liste minimale | Absent des trois listes. La V0 portait deja la reserve *"presence dans la liste minimale a confirmer"*: elle est confirmee negative. |
| `EXT-A-02` V0, coherence des tantiemes avec les cles comptables | **DEPLACE** en controle arithmetique | C'est un controle de coherence, pas un critere de presence d'un document. |
| Criteres de fraicheur par rubrique | **REMPLACES** par `EXT-X-03` | Le texte fixe une regle unique d'actualisation, pas une regle par document. |

## Controles arithmetiques

Inchanges dans leur principe: ils produisent un ecart chiffre, jamais un
jugement, ce qui les rend publiables sans risque d'accusation. Leur matiere
vient desormais de `EXT-C-01` et non d'annexes qui ne sont pas dues.

| ID | Controle | Attendu | Statut base |
|---|---|---|---|
| `EXT-CTRL-01` | Equilibre de la balance | Total des debits egal au total des credits. | Arithmetique, sans base legale a verifier. |
| `EXT-CTRL-02` | Classe 4 contre etat des impayes | Egalite des soldes debiteurs. | **Conditionnel**: l'etat des impayes n'est pas du au titre de l'extranet; controle possible seulement si la piece est fournie par ailleurs. |
| `EXT-CTRL-03` | Classe 5 contre releves bancaires | Solde de tresorerie egal au solde bancaire a la meme date. | `EXT-C-02`. |
| `EXT-CTRL-04` | Fonds de travaux sur compte separe remunere | Solde comptable adosse au compte prevu a l'art. 18 II. | `VERIFIE`: loi art. 14-2-1 et art. 18 II, compte separe remunere expressement impose. |
| `EXT-CTRL-05` | Balance contre releve general des charges et produits | Deux expressions du meme objet; tout ecart non nul est a expliquer. | `EXT-C-01`. |
| `EXT-CTRL-06` | Repartition par cle contre tantiemes | Cles coherentes avec l'etat descriptif de division. | `EXT-A-01`. |
| `EXT-CTRL-07` | Annexe 3 contre annexe 2, operations courantes | Egalite **imposee par le decret**, article 10. | `VERIFIE` - decret 2005-240, art. 10 |
| `EXT-CTRL-08` | Annexe 4 contre annexe 2, travaux de l'article 14-2 et operations exceptionnelles | Egalite imposee, article 10. Voir la reserve de lecture sur le libelle du texte. | `VERIFIE` - decret 2005-240, art. 10 |
| `EXT-CTRL-09` | Colonne E de l'annexe 5 contre le compte 12 de l'annexe 1 | *"Ce solde correspond au solde du compte 12 dans l'annexe n° 1"*, note du tableau. | `VERIFIE` - decret 2005-240, annexe 5 |

`EXT-CTRL-05` reste le controle le plus solide du dispositif, et il gagne a
etre reformule: la V0 comparait la balance aux annexes comptables, qui ne sont
pas dues sur l'extranet. Le releve general des charges et produits, lui, est du
par le meme article que la balance. Le controle devient donc realisable avec
les seules pieces que le syndic doit fournir.

## Obligations connexes, hors liste minimale

Verifiables par recoupement avec des sources publiques independantes du syndic.
C'est le seul ancrage externe du dispositif.

| ID | Obligation | Source de controle | Statut base |
|---|---|---|---|
| `EXT-D-01` | Immatriculation au registre national des coproprietes, donnees a jour | Donnees ouvertes du registre national; skill `datagouv-tabulaire` | `VERIFIE` - CCH L. 711-1 `LEGIARTI000033974279` et L. 711-2 `LEGIARTI000049398053`. **Reserve de formulation**: le texte lu impose de declarer les donnees *et toute modification les concernant*, ce qui n'est pas exactement une *declaration annuelle*; la periodicite annuelle des donnees financieres n'a pas ete retrouvee dans la portion relue. Ne pas ecrire "declaration annuelle" sans l'avoir verifiee. **Levier direct**: L. 711-6 `LEGIARTI000028779458` permet a **un coproprietaire** de mettre le syndic en demeure par lettre recommandee - c'est une action que Brice peut engager seul, sans passer par le conseil syndical. |
| `EXT-D-02` | Existence juridique et dirigeants de la societe de syndic | Skills `registres-entreprises` et `sirene-insee` | Sans base a verifier; recoupement factuel |
| `EXT-D-03` | Projet de plan pluriannuel de travaux | Loi 65-557, art. 14-2 | `VERIFIE` - `LEGIARTI000043977289`: du **quinze ans apres la reception des travaux de construction**, actualise tous les dix ans, immeubles a destination partielle ou totale d'habitation |
| `EXT-D-04` | Fonds de travaux | Loi 65-557, art. 14-2-1 | `VERIFIE` - `LEGIARTI000043967792`: constitue **dix ans apres la reception**, destination totale ou partielle d'habitation |
| `EXT-D-05` | Diagnostic de performance energetique collectif | CCH, art. L. 126-31 | `VERIFIE` - `LEGIARTI000054140304`. **Trois conditions, toutes absentes de la V0**: ne vise que les batiments d'habitation collective dont le **permis de construire a ete depose avant le 1er janvier 2013**; renouvele ou mis a jour **tous les dix ans**; **dispense** si un diagnostic realise apres le 1er juillet 2021 classe le batiment en A, B ou C. Sans ces conditions, un immeuble recent ou bien classe serait declare en manquement. |

`EXT-D-03` et `EXT-D-04` portent des **conditions d'anciennete de l'immeuble**
que la V0 ne mentionnait pas. Sans elles, un immeuble neuf serait declare en
manquement. La date de reception des travaux devient donc une donnee
d'instance necessaire au controle.

Un desaccord entre le registre national et l'extranet reste un indicateur a
haute valeur: les deux declarations emanent du meme syndic, a des
destinataires differents.

## Indicateurs de delai

| ID | Delai mesure | Norme | Statut base |
|---|---|---|---|
| `EXT-T-01` | Derniere AG des comptes -> actualisation de l'espace en ligne | **Trois mois**, decret 67-223 art. 33-1-1 | `VERIFIE` - `LEGIARTI000042078765`. Remplace la norme "un mois" de la V0, qui confondait actualisation de l'extranet et notification du proces-verbal. |
| `EXT-T-02` | Demande ecrite du conseil syndical -> communication du document | **Un mois**, puis penalites par jour de retard imputees sur la **remuneration forfaitaire annuelle** du syndic | `VERIFIE` - loi art. 21, `LEGIARTI000039313574`. La V0 ecrivait "honoraires de gestion courante": le texte dit remuneration forfaitaire annuelle. Montant journalier: **15 euros par jour de retard**, decret 2020-1229 art. 2 `LEGIARTI000042411560`. |
| `EXT-T-03` | Demande d'un coproprietaire -> mise a disposition de la fiche synthetique | **Un mois**, puis **15 euros par jour de retard**, decret 2020-1229 art. 1 `LEGIARTI000042411558` | `VERIFIE` - loi art. 8-2, `LEGIARTI000039313533`. **Non applicable** aux syndics administrant des immeubles a destination totale autre que d'habitation. |
| `EXT-T-04` | Convocation -> ouverture de la consultation des pieces justificatives | Periode entre convocation et tenue de l'AG des comptes | `VERIFIE` - loi art. 18-1, `LEGIARTI000042120918`. Ce n'est pas un delai a respecter mais une **fenetre a ouvrir**; le controle porte sur l'ouverture effective. |
| `EXT-T-05` | Anciennete d'une rubrique annoncee "a venir" ou vide | Aucune norme; indicateur de suivi | Sans objet |

`EXT-T-02` et `EXT-T-03` partagent une meme structure: le delai **court a
compter d'une demande**, pas d'une date calendaire. Un plugin ne peut donc pas
les mesurer seul: il faut que la demande soit enregistree quelque part. C'est
une contrainte de conception, pas un detail.

## La reserve qui subsistait, et comment elle a ete levee

Les cinq textes du plan ont ete relus. Il restait **une** lacune: le contenu des
cinq annexes comptables du decret 2005-240 n'etait pas lisible. Les articles
existaient, avec des identifiants stables et en vigueur, mais Legifrance ne
reproduisait pas leur contenu.

**Levee le 2026-09-06.** Trois voies numeriques ont echoue: l'API rend `Annexe
non reproduite`, la page du Journal officiel renvoie au tableau papier, et le
PDF est refuse - 401 par l'API, 403 en direct. **Brice a depose le fichier
officiel lui-meme**: JO n° 65 du 18 mars 2005, texte 7 sur 102, NOR
`SOCU0412534D`.

La structure des cinq annexes est relevee poste par poste dans
[`annexes_comptables_decret_2005-240.md`](./annexes_comptables_decret_2005-240.md).

Ce qu'elle apporte, et qui manquait: **quatre egalites de controle citables**,
imposees par le texte lui-meme et non deduites - trois a l'article 10, une en
note de l'annexe 5. Ce ne sont pas des opinions comptables, ce sont des totaux
qui doivent coincider par construction; un ecart est un chiffre a expliquer.

**La lecon vaut d'etre gardee.** Une source peut etre publique, officielle,
parfaitement identifiee et rester hors de portee de tout acces programmatique.
Declarer la lacune plutot que de reconstituer la structure de memoire etait la
bonne conduite: c'est ce qui a permis a un humain de la combler en une minute,
et ce qui garantit que ce qui est ecrit ici vient bien du texte.

Note de perimetre: le decret 2015-342 sur le contrat type de syndic n'a pas ete
relu et n'a plus a l'etre pour ce lot. La V0 en faisait le fondement de
`EXT-T-02`; le fondement reel est la loi art. 21. Il reste utile pour apprecier
le contenu du contrat de syndic de `EXT-A-09`, ce qui est un autre sujet.

## Etat de la gate `NO-GO DEV`

La gate `NO-GO DEV` de `RM-2026-0091` avait quatre causes. **Trois sont levees
au 2026-09-04.** La derniere est une observation, pas une decision:

1. **Base legale verifiee** - leve par cette passe.
2. **Structure reelle de l'editeur cible** - **partiellement levee le
   2026-09-04**, premiere observation reelle chez l'editeur Coprodirecte:
   [`observation_extranet_coprodirecte_2026-09-04.md`](./observation_extranet_coprodirecte_2026-09-04.md).
   Ossature connue, deux espaces et cinq index reperes, trois contraintes de
   conception mesurees. Restent a ouvrir les huit categories de documents et
   les pages comptables. `EXT-001` est `INDETERMINE` et le restera tant qu'un
   compte hors conseil syndical n'aura pas vu la meme page.
3. **Ligne rouge** - **tranchee le 2026-09-04**, et reformulee. Voir
   [`journal_observation_extranet.md`](./journal_observation_extranet.md),
   section Ligne rouge: le plugin agit sur la machine de l'utilisateur autant
   qu'il le faut, tout ce qui sort vers le syndic passe par un clic humain.
4. **Doctrine "instrument de mesure"** - **tranchee le 2026-09-04**: l'outil
   mesure et date, il n'accuse pas. Un ecart se presente comme une question a
   poser, jamais comme un manquement impute a quelqu'un.

## Suite du lot

Le lot a pris une seconde dimension le 2026-09-04, a la demande de Brice:
tracer les differences entre deux passages et telecharger ce qui est nouveau.
Conception dans [`journal_observation_extranet.md`](./journal_observation_extranet.md).
Ce n'est pas un ajout de confort: c'est ce qui rend mesurables `EXT-X-03`,
`EXT-T-01` et `EXT-T-02`, declares ici mesurables par observation repetee sans
qu'aucun mecanisme ne le permette.

Aucun code applicatif n'a ete ecrit. Aucune donnee reelle n'a ete lue. Aucun
serveur n'a ete lance.
