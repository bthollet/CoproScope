# Extraction des pieces comptables d'une assemblee

Lot `RM-2026-0074` / `CONV-2026-2138`. Date: 2026-09-04.
Code: `server/src/coproscope/modules/comptes_extraction.py` et ses cinq parties.
Tests: `server/tests/test_comptes_extraction.py`.

## Synthese pour un lecteur presse

Un drapeau rouge avait ete leve: les documents que le classement automatique
etiquette `Etat_Depenses`, `Grand_Livre` et `Budget_Previsionnel` ne sont
peut-etre pas ce que leur etiquette dit. **Le drapeau etait justifie, mais pas
la ou on l'attendait.**

- **Le grand livre n'existe pas.** L'unique document etiquete ainsi est une note
  de travail produite par l'outil lui-meme, qui dit d'ailleurs en toutes lettres
  que les ratios sont bloques faute de grand livre. Le coffre le reclame au
  syndic depuis mai 2026, au niveau de priorite le plus haut, sans qu'aucune
  trace d'envoi formel ni de reponse ne soit conservee.
- **Aucun document autonome de budget previsionnel n'existe non plus.** Les deux
  etiquettes portent sur des fichiers de travail. Ce n'est pas une piece
  manquante: le budget previsionnel **vit dans les annexes 2 et 3**, sous forme
  de colonnes comparatives. C'est une correction du contrat d'entree, pas une
  demande a adresser au syndic.
- **Les etats des depenses, en revanche, sont authentiques.** Six documents
  reels, sur quatre exercices, produits par le logiciel comptable du syndic,
  avec une couche de texte integrale. Ils ne sont ni des doublons ni des
  fabrications.
- **Le vrai sujet de conformite est ailleurs, et il est reel.** L'etat des
  depenses n'est pas une annexe reglementaire. C'est une restitution de synthese
  editee par le cabinet. Les pieces primaires qui permettraient de la verifier -
  grand livre, balances, journaux, releves bancaires, rapprochements bancaires -
  n'ont jamais ete communiquees.

Le lot n'a donc pas change de nature: le corpus existe et il est exploitable.
Mais il **s'est deplace**. L'extracteur livre ne s'appelle plus extracteur
d'etat des depenses: il lit les pieces comptables d'une assemblee, et l'etat des
depenses n'en est qu'une parmi deux familles.

## Etape 0: ce que les pieces sont reellement

Dix-neuf lignes de registre portent l'etiquette `Etat_Depenses` ou
`Etat_Depenses_Detaillees`, reparties sur deux registres. Elles designent
**neuf documents distincts**, dont trois ne sont pas des etats des depenses.

| Ce que l'etiquette annonce | Ce que la piece est | Nombre |
|---|---|---:|
| Etat des depenses | Etat des depenses reel, edite par le logiciel comptable du syndic | 6 |
| Etat des depenses | Conversion en texte d'un des six, produite par l'outil | 1 |
| Etat des depenses | Registre d'avancement interne de l'outil | 1 |
| Grand livre | Note d'instruction interne de l'outil | 1 |
| Budget previsionnel | Tableaux de travail produits par l'audit | 2 |

Les six documents reels couvrent quatre exercices, en deux niveaux de detail:

| Exercice | Etat de synthese | Etat detaille |
|---|---|---|
| N-3 | present | present |
| N-2 | present | present |
| N-1 | present (deux copies au contenu identique) | absent du dossier |
| N | absent | present |

**Le nom de fichier ment sur deux points au moins.** Un fichier dont le nom
porte `detaillees` contient un etat de synthese; un autre, dont le nom ne le dit
pas, contient un etat detaille. Le code ne lit donc jamais un nom de fichier:
il lit le contenu. C'est une regle de conception, pas une precaution.

### Le sujet de conformite, tel qu'il est etabli

Trois choses distinctes ont ete confondues sous le mot conformite. Elles se
separent ainsi.

1. **Les etats des depenses sont authentiques et arithmetiquement justes.** Sur
   les six documents, la somme des lignes lues retombe **exactement** sur le
   total general imprime, et la somme des sous-totaux par cle de repartition
   aussi. Rien ne permet de dire que ces documents ne sont pas ce qu'ils
   annoncent.
2. **Ils ne sont pas des annexes reglementaires**, et ne peuvent pas en tenir
   lieu. Les annexes 1 a 5 existent, elles, pour les trois exercices clos, et
   elles ont ete lues. Le total des charges courantes de l'annexe 3 pour
   l'exercice N-1 **coincide au centime** avec le total des charges courantes de
   l'etat des depenses du meme exercice. Les deux familles de pieces se
   confirment mutuellement: l'etat est le detail de l'annexe.
3. **Le grief reel est probatoire.** Les rapports d'audit du coffre le formulent
   deja: ces documents sont des restitutions de synthese, et elles ne suffisent
   pas a verifier les ecritures, les dates de comptabilisation, les paiements et
   les soldes fournisseurs. Les pieces qui le permettraient - grand livre, livre
   journal, balances generale, fournisseurs et coproprietaires, releves
   bancaires periodiques, rapprochements bancaires - **ne sont pas au dossier et
   n'y ont jamais ete**.

Une decouverte faite par l'extracteur lui-meme merite d'etre signalee, parce
qu'elle corrige une erreur que la lecture des noms de fichiers avait produite.
Le decoupage des annexes de la derniere convocation semblait montrer que
l'annexe 3 n'avait pas ete notifiee: les quatre fichiers portaient les numeros
1, 2, 4 et 5. **C'est faux.** Le fichier nomme annexe 2 contient en realite
l'annexe 2 **et** l'annexe 3. La lecture du contenu l'etablit; la lecture des
noms disait le contraire.

### Ce qui reste a reclamer, par ordre de priorite

Cette liste consolide les demandes deja redigees dans le coffre. Aucune n'est
enregistree comme envoyee ni comme satisfaite.

1. Grand livre general, grand livre fournisseurs, grand livre coproprietaires,
   pour les quatre exercices.
2. Balances generale, fournisseurs et coproprietaires; journaux comptables.
3. Releves bancaires periodiques des comptes separes, y compris travaux et fonds
   de travaux. Un relevé d'identite bancaire ne vaut pas relevé de compte.
4. Rapprochements bancaires.
5. Etat detaille des depenses de l'exercice N-1, absent du dossier.
6. Etat age des dettes fournisseurs et etat age des impayes.

**Point de gouvernance a arbitrer.** La doctrine "pas d'approbation des comptes
sans pieces primaires" est ecrite dans les fiches de controle du coffre, mais
elle n'a jamais ete portee au journal des decisions comme une decision datee. Et
le registre des demandes ne contient que sa ligne d'en-tete. En l'etat, le
levier des penalites de retard prevu au benefice du conseil syndical ne peut pas
etre actionne, faute de preuve d'une demande formelle.

## Ce que l'extracteur fait, et ce qu'il vaut

### Mesure contre l'etalon

L'etalon a ete etabli **a la main**, par lecture humaine, avant tout traitement.
L'extracteur retombe dessus exactement.

| Grandeur de l'exercice N | Etalon etabli a la main | Lu par l'extracteur |
|---|---:|---:|
| Total general | 357 493,10 | **357 493,10** |
| dont charges courantes | 304 021,37 | **304 021,37** |
| dont travaux et exceptionnel | 53 471,73 | **53 471,73** |
| dont charges locatives | 226 205,97 | **226 205,97** |
| Taxe totale | 44 324,59 | **44 324,59** |
| Taxe sur les courantes | 37 930,82 | **37 930,82** |
| Taxe sur les travaux | 6 393,77 | **6 393,77** |

Les **huit** sous-totaux par cle de repartition de l'etalon sont reproduits
chacun exactement, et leur somme retombe sur les agregats. Sur les six documents
reels, la somme des lignes lues egale le total general imprime, au centime, sans
exception. Pour memoire, l'ecran affichait 24 397 501,24 avant ce lot.

### Le piege de lecture, et comment il est desamorce

La colonne du montant a repartir est un **toutes taxes comprises**, et la
colonne de taxe donne la taxe **incluse** dans ce montant. Un outil qui lirait
la premiere comme un hors taxes, ou qui additionnerait les deux, gonflerait
chaque ligne du montant de sa taxe.

Le module ne se contente pas de le savoir: **il le prouve sur chaque ligne**. Un
nombre n'est retenu comme taux que si la taxe voisine retombe dessus au centime,
et les deux conventions possibles sont testees. La convention effectivement
etablie est portee au profil du document. Un cabinet qui publierait des hors
taxes serait donc lu correctement sans qu'une ligne de code change.

### Les trois ecarts reels, et par quelle voie chacun se voit

C'est le resultat le plus instructif du lot. **Aucun des trois ecarts n'est une
erreur d'arithmetique.** Dans les trois cas, le taux affiche et la taxe extraite
retombent l'un sur l'autre au centime. Un controle qui ne lirait que l'etat des
depenses ne verrait rien, et c'est ce qui s'est produit a la premiere mesure.

| Ecart | Visible sur le seul etat ? | Par quel moyen |
|---|---|---|
| Taxe sur une prime d'assurance | **Oui** | Par le **numero** du compte, jamais par son libelle. Une prime d'assurance supporte une taxe sur les conventions d'assurance, deja comprise dans le montant appele, et non une taxe sur la valeur ajoutee. |
| Taux a 20 pour cent sur une piece emise a 10 pour cent | Non | Confrontation avec la piece, par sa reference. |
| Taxe constatee sur une piece portant `taxe non applicable` | Non | Confrontation avec la piece, par sa reference. |

D'ou la separation du code en deux familles de controles, et d'ou l'importance
de la **colonne de reference de piece**: c'est elle qui porte le rapprochement
facture vers ligne. Sans elle, le rapprochement se rabat sur le montant, qui
n'est pas identifiant.

Aucun de ces constats ne corrige quoi que ce soit. Chacun conserve la valeur du
document **et** la valeur attendue, et nomme la piece. Seul le syndic peut dire
s'il s'agit d'un parametrage de compte ou d'une erreur d'imputation.

## Axes de generalisation

Un seul cabinet fournit la quasi-totalite du corpus. Le risque etait donc de
coder ses habitudes. Chaque difference constatee est ci-dessous ramenee a un
axe, avec ce qui reste invariant le long de cet axe, ce que le code en fait, et
ce qui se passe hors des valeurs observees.

### 1. Separateur decimal

- **Modalites observees.** Virgule chez le premier cabinet, point chez le second.
- **Invariant.** Un document utilise un seul separateur, de bout en bout.
- **Ce que le code en fait.** Il le **detecte** en comptant les jetons conformes
  a chacune des deux notations, et refuse explicitement la notation opposee.
- **Hors des valeurs observees.** Un document ou les deux notations
  s'equilibrent rend `SEPARATEUR_INDECIDABLE` et **aucun montant n'est lu**.
  C'est deliberé: lire `1.234` comme mille deux cent trente-quatre dans un
  document a virgule vaudrait un facteur mille, sans aucun signe visible.

### 2. Presence et ordre des colonnes

- **Modalites observees.** Quatre colonnes chez le premier cabinet - montant a
  repartir, charges locatives, taux, taxe - mais la colonne des charges
  locatives est **absente sur certaines lignes du meme document**. Le second
  cabinet n'a ni colonne de taxe ni colonne de charges locatives.
- **Invariant.** Le premier nombre d'un enregistrement est le montant a
  repartir. Et quand un taux est present, il precede immediatement sa taxe.
- **Ce que le code en fait.** Il ne lit **jamais** les valeurs par position. Il
  les lie par preuve: l'identite de taxe. Un enregistrement a trois nombres se
  lit correctement sans savoir a l'avance si la colonne locative est la.
- **Hors des valeurs observees.** Un enregistrement qui ne se lie a aucune
  combinaison prouvable conserve son seul montant a repartir et emet
  `COLONNES_NON_LIABLES`. Aucune valeur n'est inventee pour completer un
  gabarit.
- **Limite assumee.** L'ordre annonce par l'entete n'est pas recuperable quand
  l'entete tient sur plusieurs lignes que l'aplatissement entrelace. Le module
  le conserve pour information et **ne s'en sert jamais** pour lier les valeurs.

### 3. Convention du montant

- **Modalite observee.** Toutes taxes comprises, taxe incluse.
- **Invariant.** La relation entre montant, taux et taxe est une identite
  arithmetique, quelle que soit la convention.
- **Ce que le code en fait.** Il teste les deux conventions et retient celle qui
  tient. La convention etablie est portee au profil.
- **Hors des valeurs observees.** Quand aucune ligne ne la prouve, la convention
  reste `CONVENTION_INCONNUE`, et **aucun calcul de taxe derive n'est fait**.

### 4. Expression des cles de repartition

- **Modalites observees.** Un code numerique a trois chiffres suivi d'un
  libelle, ou un code prefixe d'une lettre. Le nombre de parts est parfois
  annonce dans l'intitule du total, parfois non. Un marqueur de cle est parfois
  accole au montant lui-meme.
- **Invariant.** Un code suivi d'un libelle ouvre une section; un total de cle
  la ferme.
- **Ce que le code en fait.** Il distingue une cle d'un sous-poste par sa
  **place**, pas par la forme de son code: un code rencontre avant tout compte,
  ou juste apres un total de cle, ouvre une cle. Les marqueurs accoles sont
  detaches du montant et conserves a part.
- **Hors des valeurs observees.** Un marqueur d'une autre forme n'est pas
  reconnu; le montant reste lisible, le marqueur est perdu et vaut chaine vide.

### 5. Emplacement du total general

- **Modalites observees.** Une ligne intitulee chez le premier cabinet. Absent
  du document du second. **Et, dans le meme document du premier cabinet, le
  total des charges courantes est imprime sur certains exercices et pas sur
  d'autres.**
- **Invariant.** Un total se declare par un intitule qui contient le mot total,
  et ne porte jamais de taux.
- **Ce que le code en fait.** Il compare les intitules **apres suppression de
  tout blanc**, parce que le meme cabinet espace certains totaux lettre a lettre
  et pas d'autres. Quand le total des charges courantes manque, il est deduit
  du total general moins les travaux, et le resultat **dit qu'il est deduit**.
- **Hors des valeurs observees.** Un document sans total general emet
  `TOTAL_GENERAL_ABSENT` et rend `None`, jamais zero.
- **Attrape ici.** Un total a deux nombres est reellement ambigu: montant plus
  charges locatives, ou montant plus taxe. Il est tranche par recoupement avec
  les lignes du bloc, pas par une convention de cabinet.

### 6. Reference de piece

- **Modalites observees.** Presente dans les etats detailles, absente des etats
  de synthese. Numerique chez un cabinet, alphanumerique prefixee chez l'autre,
  et absente sur certaines lignes du meme document.
- **Invariant.** Quand elle existe, elle suit la date de la ligne.
- **Ce que le code en fait.** Il la reconnait sur une forme volontairement
  large, et porte au profil le fait qu'elle soit presente ou non.
- **Hors des valeurs observees.** Une reference manquee coute plus cher qu'une
  reference retenue a tort, qui reste visible dans le rapport. Le compromis est
  assume dans ce sens.

### 7. Granularite du tableau

- **Modalites observees.** Synthese et detail, avec un nom de fichier qui ment
  dans les deux sens.
- **Invariant.** Un etat detaille porte une date sur chacune de ses lignes.
- **Ce que le code en fait.** Il la **mesure**: detaille si la majorite des
  lignes porte sa propre date.
- **Hors des valeurs observees.** Un document mixte tombe du cote majoritaire, et
  la coexistence des deux formes reste visible ligne par ligne.

### 8. Nombre et disposition des colonnes d'annexe

- **Modalites observees.** Cinq colonnes comparatives chez le premier cabinet,
  dont deux portent le meme millesime. Deux colonnes chez le second. Les valeurs
  du total **precedent** l'intitule chez l'un et le **suivent** chez l'autre.
- **Invariant.** Le nombre de valeurs de la ligne de total egale le nombre de
  colonnes annoncees par l'entete.
- **Ce que le code en fait.** Il compte les millesimes de l'entete, sans les
  dedupliquer, puis choisit le cote de l'intitule qui en porte autant.
- **Hors des valeurs observees.** Quand l'entete n'annonce aucun millesime, le
  module prend le cote qui suit l'intitule s'il en porte, sinon l'autre, et
  **ne pretend a aucune certitude**. Quand les deux cotes conviennent, il retient
  celui qui suit et emet `TOTAL_AMBIGU`.

### 9. Intitule du total d'une annexe

- **Modalites observees.** `TOTAL CHARGES NETTES` dans l'annexe 3; `TOTAL I` et
  `TOTAL II` dans l'annexe 2.
- **Invariant.** Le chiffre romain porte le sens: la section I est celle des
  operations courantes, la section II celle des travaux.
- **Ce que le code en fait.** Il cherche par familles d'intitules, dans un ordre
  de preference explicite. Prendre le dernier total venu donnerait le total des
  travaux la ou l'article 10 du decret parle des operations courantes.

### 10. Nombre de fichiers par assemblee

- **Modalites observees.** Le premier cabinet eclate sa convocation en dix-neuf
  fichiers, dont un par annexe - **sauf que le fichier de l'annexe 2 contient
  aussi l'annexe 3**. Le second empile ses cinq annexes dans un unique fichier,
  et y repete l'annexe 3 une fois par cle de repartition.
- **Invariant.** Une assemblee porte un jeu d'annexes; le decoupage en fichiers
  est une commodite d'envoi.
- **Ce que le code en fait.** **Le contrat d'entree est par assemblee.**
  `dossier_assemblee` prend un sac de pieces sans ordre impose. Chaque fichier
  est decoupe sur le **changement de numero d'annexe**, jamais sur l'apparition
  de l'intitule: compter les apparitions donnerait sept annexes 3 la ou il y en
  a une, declinee.
- **Hors des valeurs observees.** Une piece qu'aucun lecteur ne reconnait sort
  dans `sans_nature` au lieu de disparaitre silencieusement.

### Ce que l'epreuve sur le second cabinet a reellement montre

Le second jeu de test a bien un corpus comptable exploitable, et il a servi a
eprouver sept des dix axes ci-dessus. Mais il apporte surtout **un resultat que
le premier cabinet ne pouvait pas donner**:

> **Il n'y a chez lui aucun etat des depenses.** Aucun. Ses cinq annexes
> reglementaires portent tout.

Autrement dit, l'etat des depenses est une **modalite** propre a un cabinet, et
l'annexe est l'**axe**. Un extracteur construit uniquement autour de l'etat des
depenses aurait ete inutilisable sur la moitie du corpus disponible. C'est la
raison pour laquelle le module livre lit les deux familles, et pourquoi il
s'appelle extracteur de pieces comptables et non extracteur d'etat des depenses.

## Contrat de sortie: une proposition, pas une modification

Le contrat de plugin `expense.statement` attend un fichier de lignes de depense.
Il n'est fabrique aujourd'hui que par le module de demonstration, en recopiant
des fixtures: sur une instance reelle il n'existe jamais, d'ou zero ligne
chargee et zero rapprochement sur douze attendus.

Le module livre produit exactement la matiere qui manque. **Il ne modifie ni le
chargeur ni le catalogue**, qu'une conversation pair possede. Trois points sont
soumis a cette conversation.

1. **Une ligne de depense a besoin de son taux et de sa taxe.** Le contrat
   actuel ne porte qu'un montant. Sans le taux et la taxe, deux des trois ecarts
   reels du corpus sont indetectables. Trois colonnes sont proposees: `taux_tva`,
   `montant_tva` et `convention_montant`.
2. **La convention du montant doit voyager avec les lignes.** Un fichier de
   lignes toutes taxes comprises et un fichier de lignes hors taxes ne se
   distinguent par aucune valeur. Ne pas transporter la convention, c'est
   accepter que le prochain lecteur se trompe d'un montant de taxe.
3. **Le nom du contrat est trop etroit.** `expense.statement` designe une piece
   qu'un cabinet sur deux ne produit pas. `accounting.lines` decrirait ce qui est
   reellement transporte.

## Contrat d'entree du controle du budget previsionnel

La grille du budget previsionnel rendait seize controles sur seize
`INAPPLICABLE`, faute de la colonne de chiffres. `dossier_assemblee` rend
desormais le `Dossier` qu'elle attend, avec les totaux des annexes 2 et 3
renseignes des que les pieces correspondantes sont dans le sac.

**Une correction de cadrage est proposee a ce lot.** Le budget previsionnel
n'est pas un document: c'est une colonne de l'annexe 2 ou 3. Chercher une piece
autonome intitulee budget previsionnel serait chercher ce qui n'existe pas, et
les deux etiquettes posees par le classement le confirment: elles portent toutes
les deux sur des fichiers de travail.

La lecture **ligne a ligne** de la colonne budgetaire n'est pas faite dans ce
lot. `budget.lignes` reste donc vide, et les controles qui en dependent
resteront `INAPPLICABLE` en nommant l'entree manquante - ce qui est le
comportement voulu. C'est le chantier suivant identifie.

## Limites de ce lot

- La lecture ligne a ligne des annexes n'est pas faite; seuls les totaux le sont.
- L'annexe 1 et l'annexe 5 ne portent pas d'intitule de total reconnu par le
  module: leurs totaux ne sont pas lus.
- Chez le second cabinet, l'annexe 2 n'annonce aucun millesime en entete: le
  module ne peut pas borner sa ligne de total et rend une suite trop longue.
- La confrontation aux pieces exige un dictionnaire de pieces que ce lot ne
  fabrique pas. Il decrit la forme attendue et la teste; le remplir revient au
  module de factures.
- Un total a deux nombres reste tranche par recoupement. Le cas ou aucune des
  deux sommes candidates ne retombe est couvert par un repli documente, pas par
  une preuve.

## Verification

- Suite complete: 1247 tests, 3 echecs et 1 erreur, tous preexistants et sans
  rapport avec ce lot. La base de reference etait de 1210 tests avec les memes
  3 echecs et la meme erreur; les 37 tests ajoutes passent tous.
- `check_code_line_limit.py`: aucun fichier de code au-dela de 600 lignes.
- `git diff --check`: propre.
- Mesure contre l'etalon: executee en processus, sans serveur ni socket.
- Aucune donnee reelle dans le depot. Les gabarits de test reproduisent la
  structure mesuree avec des montants inventes et des libelles neutres.
