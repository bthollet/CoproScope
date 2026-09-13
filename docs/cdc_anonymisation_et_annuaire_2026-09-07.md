# Cahier des charges - anonymisation et annuaire des personnes

**Statut: specification de construction.** Ce document dit quoi construire, dans
quel ordre, avec quels contrats et quels criteres d'acceptation. Il ne remplace
pas [`cdc_base_personnes_et_biffage.md`](./cdc_base_personnes_et_biffage.md),
qui reste l'expose du besoin: il en ferme les dix points ouverts de sa
section 6, avec les mesures qui manquaient a l'epoque.

Enquete amont: [`cadrage_annuaire_verificateur_biffage_2026-09-07.md`](./cadrage_annuaire_verificateur_biffage_2026-09-07.md).
Mesures anterieures reutilisees sans les refaire:
[`corpus_caviarde_2026-09-04.md`](./corpus_caviarde_2026-09-04.md).

Gouvernail: `RM-2026-0096` a `RM-2026-0099`. Une decision de Brice reste
requise avant ouverture de chantier, section 14.

---

## 1. Les huit mesures qui commandent la conception

Aucune ligne de ce cahier ne repose sur une intuition. Chaque exigence descend
d'un de ces huit constats, tous dates et rejouables.

| # | Mesure | Consequence sur la conception |
|---|---|---|
| M1 | Tilleuls (pseudo): une liste nominative extraite = 200 personnes d'un coup, et un rappel de 95,4 % sur le PV. Erables (pseudo): aucune liste dans le corpus, 0 personne extraite, rappel non mesurable. | L'annuaire EST le systeme. Sans lui il ne reste qu'une heuristique. |
| M2 | 5 mises en page de liste nominative sur 7 rendent 0 personne, sans rien signaler. `server/tests/test_annuaire_formes_liste_nominative.py`. | L'extracteur de liste est le premier lot, et il se refait sur des axes. |
| M3 | Le groupement des formes suspectes par racine ne reduit la file que de 7 % et 9 %. La partition sur `nb_documents >= 2` la reduit de 66 % et 64 %. `tools/mesure_file_arbitrage.py`. | La file se partitionne par diffusion, jamais par ressemblance. |
| M4 | `RegistrePseudonymes` n'a aucun chemin de suppression, et les detections generiques y creent des entites permanentes que `applique_annuaire` propage ensuite a tout le corpus. | Une detection ne cree JAMAIS une entite. Elle cree un candidat. |
| M5 | Instance `tilleul_pseudo_vide_20260907`, 2026-09-07: 825 documents, 539 marques `redaction` requise, **0 biffe**, 0 alias produit sur 2 449 fichiers, aucun reglage `corpus_caviarde`. | La chaine annuaire est inactive par defaut et rien ne le dit a l'ecran. |
| M6 | Meme instance: 478 documents sur 825 en `no_ai`. `core/privacy.py:337` calcule ce plafond sur le college BRUT seul; `derivative_max_college` existe et n'est jamais consulte pour cela. | Le plafond IA se reevalue sur le derive, sinon le derive ne sert a rien. |
| M7 | Meme instance, page `/confidentialite`: quatre nombres pour `a biffer` - 539 au rapport, 564 en file, 123 au registre, 79 en decision. | Un mot, une definition, un comptage. |
| M8 | Meme page: les noms de fichiers bruts sont affiches en clair, et l'un d'eux porte un patronyme, sur l'ecran qui decide de la diffusion. | Le nom de fichier est une surface d'anonymisation, au meme titre que le contenu. |

## 2. Probleme

Un coproprietaire veut faire lire ses pieces par un outil - le sien, ou un
agent - sans que les noms de ses voisins circulent, et en sachant ce qui reste
dessus.

Formulation novice, a tenir dans l'interface: *je donne mes documents a lire
sans donner le nom de mes voisins, et l'outil me dit ce qu'il n'a pas su
masquer.*

## 3. Perimetre

**Construit ici**

- l'annuaire des entites, ses trois sources d'alimentation et leur separation;
- l'extracteur de liste nominative, refait sur axes;
- la file d'arbitrage et ses trois verbes;
- la gate d'absorption qui reclame la liste nominative;
- l'anonymisation du nom de fichier;
- la reserve ecrite sur le derive et la reevaluation du plafond IA.

**Hors perimetre, et il faut le dire**

- toute inference de modele: aucun runtime n'existe dans le produit,
  `docai._write_qwen_review_payload` ecrit un JSON de statut. A reexaminer
  seulement quand la file d'arbitrage aura ete videe une fois et qu'on saura ce
  qu'elle laisse passer;
- l'OCR et l'ajout d'une couche texte, deja arbitre comme decision de
  packaging;
- la synchronisation entre postes;
- la refonte des colleges d'acces, qui appartient a `confidentialite_et_biffage.md`.

## 4. Exigences

### 4.1 Fonctionnelles

| # | Exigence | Descend de |
|---|---|---|
| F1 | Une liste nominative est reconnue quelle que soit sa mise en page, ou declaree non lue avec son motif. | M2 |
| F2 | Une detection generique ne cree jamais une entite d'annuaire: elle cree un candidat en quarantaine. | M4 |
| F3 | Une entite d'annuaire nait de deux gestes seulement: l'extraction d'une liste nominative structurelle, ou une saisie humaine. | M4 |
| F4 | Toute entite est supprimable, et sa suppression retire ses alias du corpus au rebuild suivant. | M4 |
| F5 | Une forme suspecte recoit une des trois reponses: personne connue, personne inconnue, pas une personne. | M3 |
| F6 | Une exclusion `pas une personne` est motivee et propre a l'instance. | M3 |
| F7 | Une reponse humaine survit a toute re-extraction. | doctrine `CORRIGE_HUMAIN` |
| F8 | Une ambiguite entre homonymes n'est jamais tranchee par la machine. | CDC 4 ter |
| F9 | Une personne absente de l'annuaire recoit un alias ephemere, propre au document. | cadrage 7.2 |
| F10 | L'absorption reclame la liste nominative quand elle n'en trouve pas, et distingue `absente` de `illisible`. | M1, M2 |
| F11 | Le nom de fichier d'un derive ne porte aucun patronyme; l'interface n'affiche jamais un nom de fichier brut d'une piece restreinte. | M8 |
| F12 | Le plafond IA d'un derive est calcule sur le derive, pas herite du brut. | M6 |
| F13 | Le derive porte ecrit contre qui il protege et ce qu'il ne couvre pas. | cadrage 9 |
| F14 | Chaque nombre affiche dit a QUELLE QUESTION il repond. Un mot, une question. | M7 |

### 4.2 Non fonctionnelles

| # | Exigence | Raison |
|---|---|---|
| N1 | Aucun octet ne quitte la machine. | Local-first; le sel ne sort jamais de l'instance. |
| N2 | Aucune degradation silencieuse: un annuaire vide se voit a l'ecran. | M5, et regle d'acceptation des extracteurs de `CLAUDE.md`. |
| N3 | Le budget humain est la ressource rare, pas le CPU. | M3: 1 046 formes = ~87 minutes d'attention. |
| N4 | Pas de nouvelle dependance runtime sans arbitrage. | Le produit est un exe PyInstaller. |
| N5 | Deux passages sur le meme corpus rendent le meme alias. | Le sel d'instance l'assure deja. |
| N6 | Aucun fichier de code au-dessus de 600 lignes. | `CLAUDE.md`. |

## 5. Architecture

```text
                   ABSORPTION                    |        LECTURE
                                                 |
  piece deposee                                  |
       |                                         |
       v                                         |
  [ couche texte ? ]--non--> PDF_SANS_COUCHE_TEXTE (angle mort declare)
       | oui                                     |
       v                                         |
  [ G1: liste nominative ? ]                     |
       |         |          |                    |
   trouvee   absente    illisible                |
       |         |          |                    |
       |         +----------+--> demande a l'utilisateur, motif distinct
       v                                         |
  [ extracteur de liste, sur AXES ]              |
       |                                         |
       v                                         |
  +--> ANNUAIRE DES ENTITES (C8) <--- saisie humaine
  |    entites + liens + banque d'alias          |
  |          |                                   |
  |          v                                   |
  |    [ passe A: alias des entites connues ]    |
  |          |                                   |
  |          v                                   |
  |    [ passe B: regles generiques ]            |
  |          |            \                      |
  |          |             \--> QUARANTAINE (candidats, jamais des entites)
  |          v                        |          |
  |    derive caviarde ------------------------> lisible par un agent
  |    + reserve ecrite               |          |  (plafond IA recalcule
  |          |                        |          |   SUR LE DERIVE)
  |          v                        |          |
  |    [ passe C: suspects residuels ]|          |
  |          |                        |          |
  |          v                        v          |
  |    +--------------------------------+        |
  |    | FILE D'ARBITRAGE               |        |
  |    | partition: nb_documents >= 2   |        |
  |    +--------------------------------+        |
  |          |         |          |              |
  |      connue    inconnue   pas une personne   |
  |          |         |          |              |
  +----------+---------+          v              |
     rattache    cree l'entite   exclusion motivee
                                 propre a l'instance
```

**La boucle qui ferme le systeme part de la file et revient dans l'annuaire.**
Tant que cette fleche n'existe pas, ameliorer la detection ne fait que remplir
plus vite une file que personne ne vide.

## 6. Les trois sources de l'annuaire, et la regle qui les separe

C'est la decision structurante de ce cahier, et elle corrige M4.

| Source | Cree une entite ? | Pourquoi |
|---|---|---|
| Liste nominative structurelle | **Oui** | Elle porte un numero de compte, donc un rattachement verifiable. C'est une declaration du syndic, pas une inference. |
| Saisie humaine | **Oui** | Une personne repond de son geste. |
| Regles generiques de detection | **Non, jamais** | Une correspondance de forme n'est pas une identite. |

Aujourd'hui la troisieme source ecrit directement dans l'annuaire, sans chemin
de retour: un faux positif devient une entite permanente que `applique_annuaire`
propage ensuite a tout le corpus, et se renforce a chaque passage. La regle
inverse le sens: **une detection produit un candidat en quarantaine, et seul un
humain le promeut en entite.**

Consequence sur la valeur du systeme: la qualite de l'anonymisation ne se joue
plus dans la finesse des regexes, elle se joue dans le nombre de listes
nominatives absorbees. Un document fourni au bon moment vaut 200 arbitrages.

## 7. Modele de donnees

### 7.1 Ce qui vit ou

| Donnee | Emplacement | Motif |
|---|---|---|
| Sel d'instance | `sel_alias.key`, C8 | Existe. Ne sort jamais. |
| Entites, liens, banque d'alias | **SQLite du coffre**, magasin `gouvernance_store` | Doctrine du 2026-09-03: pas de nouveau registre CSV. |
| Assertions datees | idem | Idem. |
| Quarantaine des candidats | idem | Idem. |
| Exclusions d'instance | idem | Idem. |
| Arbitrages humains | idem, `origine = CORRIGE_HUMAIN` | F7. |
| `annuaire_personnes.csv` | C8, conserve | Registre preexistant; la doctrine ne migre pas l'existant sans demande. Devient une projection en lecture. |
| File de suspects | `corpus_caviarde_suspects.csv`, C8 | Existe. Contient par construction des noms non caviardes. |

**Le piege a ne pas retomber dedans.** `_reset_schema` est appele a chaque
reconstruction, complete ou incrementale. Une table ajoutee a la base de
reconstruction sans recorder ni projection serait effacee au rebuild suivant,
et la perte serait differee donc invisible. `vault/gouvernance_store.py` a deja
resolu ce probleme en ouvrant une base dediee qui n'est pas reconstruite: c'est
ce magasin qu'on etend.

### 7.2 L'entite

Une entite est une personne physique ou morale. Elle porte:

- un identifiant stable derive du sel d'instance;
- une nature: `physique` ou `morale`;
- un alias lisible `PERSONNE_<ARBRE>_<COULEUR>`, deja implemente et conserve;
- une racine de famille `PERSONNE_<ARBRE>`, partagee par les homonymes: c'est
  elle qui exprime l'ambiguite sans la trancher;
- une banque d'alias attendus - graphies, variantes, formes abregees, nom de
  jeune fille, `epouse X`, indivisions.

Les liens entre entites portent un type: `nom_commercial`, `gerant`, `associe`,
`representant`, `indivision`. Motif du CDC 4 ter: `T Services` est le nom
commercial de l'entreprise individuelle `Tanore`, et une SCI a un gerant nomme
ailleurs dans le corpus.

### 7.3 L'assertion datee

Une entree n'ecrit pas un **etat**, elle ecrit une **assertion**:

| Champ | Sens |
|---|---|
| `entite_id` | la personne |
| `assertion` | `coproprietaire`, `mandataire`, `tiers`, `personne_morale` |
| `doc_id` | la piece qui la porte |
| `date_piece` | date du document, PAS date de saisie |
| `source` | `LISTE_NOMINATIVE`, `SAISIE_HUMAINE` |
| `origine` | `EXTRAIT` ou `CORRIGE_HUMAIN`, liste fermee |

Motif: le fichier des coproprietaires n'est jamais aligne sur l'etat de la
copropriete a la date de l'assemblee traitee. Un PV de 2019 se lit contre
l'annuaire de 2019.

**Correction du 2026-09-07, apres exploration du schema.** Cette section disait
que la structure existait deja et qu'il suffisait de reutiliser `object_links`,
dont la contrainte UNIQUE porte `event_id` pour laisser coexister plusieurs
assertions sur un meme couple. Le MOTIF est bon; la reutilisation directe ne
l'est pas. `object_links` vit dans la base de RECONSTRUCTION, et les 24 tables
de cette base sont droppees a chaque reconstruction
(`vault/_reconstruction_parts/02_schema.py:10`) - aucune n'y survit. Deux voies
possibles, a trancher au lot: reproduire le motif dans le magasin
`gouvernance_store`, qui lui n'est pas reconstruit, ou passer par le journal
d'evenements avec son recorder et sa projection.

## 8. Axes de generalisation

Obligatoire pour tout extracteur, par `CLAUDE.md`. Pour chaque axe: ce qui
varie, ce qui reste vrai, ce que le code en fait, et ce qui se passe hors des
valeurs observees.

### 8.1 Mise en page d'une liste nominative

- **Varie**: le nombre de lignes entre le numero de compte, le nom et le
  montant; la presence de barres verticales; la casse du nom; la longueur du
  numero de compte; la presence d'un symbole monetaire.
- **Invariant**: un numero de compte, un nom et un montant se suivent dans cet
  ordre, dans une zone de texte contigue.
- **Le code**: reconnait la sequence `compte -> nom -> montant` en tolerant un
  nombre quelconque de separateurs entre les trois, y compris zero.
- **Hors valeurs observees**: rend `LISTE_ILLISIBLE` avec le fragment de
  structure reconnu, jamais une liste vide silencieuse.

### 8.2 Forme sous laquelle une personne est nommee

- **Varie**: civilite + prenom + nom, nom seul, initiale, prenom seul,
  description definie (`le coproprietaire du lot 12`).
- **Invariant**: la mention occupe une place syntaxique ou un referent humain
  est attendu.
- **Le code**: apparie les variantes generees par la banque d'alias de l'entite.
- **Hors valeurs observees**: a l'extremite droite de l'axe, aucun apparieur de
  noms ne peut fonctionner - seule la suppression de quasi-identifiants agit.
  A dire dans la reserve, pas a masquer.

### 8.3 Ambiguite d'un patronyme avec le lexique commun

- **Varie**: le patronyme est ou n'est pas un mot courant, dans CETTE
  copropriete.
- **Invariant**: l'ambiguite se leve dans le contexte d'une copropriete donnee,
  jamais dans une liste universelle.
- **Le code**: teste le voisinage - position de ligne, proximite d'un numero de
  compte ou d'un montant, casse d'origine, appartenance a une colonne
  nominative - et demande une fois par forme, puis retient.
- **Hors valeurs observees**: la garde actuelle `len < 4 or in VOCABULAIRE`
  laisse en clair les patronymes de trois lettres et biffe les mots courants
  homographes. Elle est remplacee, pas allongee.

### 8.4 Support de la mention

- **Varie**: texte courant, cellule de table, bloc signature, en-tete, **nom de
  fichier**, image sans couche texte.
- **Invariant**: une mention identifie, quel que soit son support.
- **Le code**: traite le nom de fichier comme une surface a part entiere (F11).
- **Hors valeurs observees**: une piece image n'entre dans aucune garantie
  textuelle et doit etre marquee comme telle, jamais declaree biffee.

## 9. Contrats

### 9.1 Extraction de liste nominative

Entree: le texte d'une piece. Sortie: `{statut, entrees, motif}` ou `statut`
vaut `LISTE_TROUVEE`, `LISTE_ABSENTE` ou `LISTE_ILLISIBLE`.

**Les trois statuts sont l'exigence, pas un detail d'implementation.** Rendre
une liste vide pour `absente` et pour `illisible` est le defaut M2: la gate
d'absorption ne peut alors pas demander la bonne piece, puisqu'elle ne sait pas
laquelle des deux situations elle voit.

### 9.2 File d'arbitrage

Entree, en plus des champs actuels `doc_id, genere_le, forme, occurrences,
motif`:

| Champ | Sens |
|---|---|
| `nb_documents` | nombre de pieces ou la forme apparait - **partition primaire**, pas cle de tri |
| `racine_normalisee` | pour regrouper les variantes d'une meme personne |
| `appariement_propose` | entite approchee s'il n'y en a qu'une; vide si zero ou plusieurs |

Premier lot: `nb_documents >= 2`, soit 182 et 346 decisions sur les deux corpus
mesures. Second lot: le reste, priorite basse.

**C'est une partition, jamais une exclusion.** Une fuite dans une seule piece
reste une fuite; tant que le second lot n'est pas traite, le derive le dit dans
sa reserve.

### 9.3 Alias

| Situation | Alias rendu |
|---|---|
| Entite unique appariee | `PERSONNE_<ARBRE>_<COULEUR>`, stable dans tout le corpus |
| Plusieurs entites possibles | `PERSONNE_<ARBRE>`, racine de famille - vrai, la ou trancher serait faux |
| Aucune entite | alias ephemere, propre au document, jamais reutilise |

La stabilite est une propriete de l'entite, pas de la chaine. Un alias stable
attribue a une chaine inconnue recreerait le defaut central du CDC d'origine:
*l'alias est attache a une valeur, pas a une entite*.

### 9.4 Plafond IA du derive

`ai_processing_ceiling` se calcule aujourd'hui sur `raw_max_college` seul
(`core/privacy.py:337`), alors que `derivative_max_college` existe et n'est
jamais consulte pour cela. Un derive caviarde herite donc du plafond de sa
source et reste `no_ai` a vie - 478 documents sur 825 sur l'instance mesuree.

Exigence: le derive porte son propre plafond, calcule sur son propre college,
apres caviardage. Sans quoi la couche caviardee ne peut pas remplir la fonction
pour laquelle elle est produite.

## 10. Sequence de construction

L'ordre n'est pas negociable: il descend de M1 et M3. Un annuaire complet vide
la file par le haut; la file ne remplit l'annuaire qu'une decision a la fois.

| Lot | Objet | Debloque | Critere de sortie |
|---|---|---|---|
| **L1** | Extracteur de liste nominative sur axes, trois statuts | Tout le reste. Sans lui, un corpus sans annexe reste a zero personne. | A1, A2 |
| **L2** | Quarantaine des detections + entree humaine + suppression d'entite | Arrete la contamination par faux positif permanent | A3, A4 |
| **L3** | Gate G1 a l'absorption, avec `absente` / `illisible` distincts | Rend l'annuaire nourrissable par l'utilisateur | A5 |
| **L4** | File d'arbitrage partitionnee, trois verbes, exclusions d'instance | Rend le reliquat traitable | A6 |
| **L5** | Nom de fichier, reserve du derive, plafond IA recalcule, comptage unique | Rend le produit honnete sur ce qu'il delivre | A7, A8, A9 |

L5 est le seul lot qui ne depend d'aucun autre. Il peut se livrer en premier si
la priorite est l'honnetete de l'affichage plutot que la couverture.

## 11. Degradation

La regle unique: **ne jamais repondre faux en silence.**

| Situation | Comportement exige |
|---|---|
| Pas de couche texte | `PDF_SANS_COUCHE_TEXTE`, angle mort declare |
| Liste nominative absente | `LISTE_ABSENTE`, gate demande la piece en la nommant |
| Liste nominative illisible | `LISTE_ILLISIBLE` + fragment reconnu, motif distinct du precedent |
| Annuaire vide | Le derive est produit, marque `ANNUAIRE_ABSENT`, et le compteur de personnes connues affiche 0 a l'ecran |
| Forme appariee a plusieurs entites | Racine de famille + entree en file, jamais de choix |
| Forme appariee a rien | Alias ephemere + entree en file, jamais `donc ce n'est pas une personne` |
| Chaine desactivee par reglage | L'ecran le dit; aujourd'hui rien ne le dit (M5) |

Le cas interdit est celui que l'instance du 2026-09-07 expose: 539 documents
marques a biffer, 0 biffe, et une page qui presente un etat d'avancement.

## 12. Criteres d'acceptation

Etalon: `instances/tests_ux` et `docs/etalon_corpus_tests_ux.md`, etabli a la
main avant tout traitement outil. Epreuve inter-cabinet obligatoire sur
`instances/erables_pseudo_test`. Jamais une instance historique comme etalon.

| # | Critere | Mesure |
|---|---|---|
| A1 | Les 7 mises en page de `test_annuaire_formes_liste_nominative` rendent 4/4 | Le test existe et passe aujourd'hui en figeant l'echec; il doit s'inverser |
| A2 | Une mise en page inconnue rend `LISTE_ILLISIBLE`, jamais une liste vide | Forme fabriquee hors des 7 |
| A3 | Une detection generique ne cree aucune entite | Compter les entites avant/apres une passe sur un corpus sans liste |
| A4 | Une entite supprimee ne reapparait pas et ses alias disparaissent du corpus | Supprimer, rebuild, recompter |
| A5 | Erables (pseudo) declenche la demande de liste au lieu d'un derive muet | Le corpus n'a pas d'annexe: c'est le cas de reference |
| A6 | La partition `nb_documents >= 2` tient sur un troisieme corpus | `tools/mesure_file_arbitrage.py` |
| A7 | Aucun nom de fichier brut d'une piece restreinte n'apparait dans le HTML rendu | Assertion sur la reponse de `/confidentialite` |
| A8 | Chaque nombre affiche porte l'enonce de sa question, et la file ne contient plus de doublon | Assertion sur le HTML rendu; `doc_id` distincts == lignes de la file |
| A9 | Le rappel ne baisse pas et la precision ne s'effondre pas | Rappel PV Tilleuls (pseudo) >= 95,4 %; `article NN` 139/139 et montants 307/307 |

A9 est la garde anti-incident: la table d'alias du 2026-09-03 avait remplace
environ 5 400 etiquettes sur 6 099, dont `Article 24` et `Vote`, detruisant ce
que le parcours d'analyse doit extraire.

## 13. Arbitrages explicites

| Choix | Retenu | Rejete | Cout du choix |
|---|---|---|---|
| Ou porter l'effort | L'entree: liste nominative et saisie | Un meilleur detecteur | On garde un detecteur imparfait plus longtemps |
| Detections generiques | Quarantaine | Ecriture directe en annuaire | Une etape humaine de plus avant qu'un nom soit alias partout |
| Alias d'un inconnu | Ephemere | Stable | Deux mentions du meme inconnu dans deux pieces restent non reliees |
| Ambiguite | Racine de famille | Choix par score | L'utilisateur voit un alias moins precis |
| Magasin | Base dediee `gouvernance_store` | Base de reconstruction | Une convergence reste a faire plus tard |
| Annuaire CSV | Conserve en projection | Migration immediate | Deux representations coexistent le temps des lots |
| Detecteur d'oublis | `suspects_residuels`, local, deja la | Un modele local | On renonce aux prenoms isoles et aux descriptions definies |
| Runtime de modele | Aucun | `torch` + poids dans l'exe | On ne saura pas ce qu'une IA aurait attrape avant d'avoir vide la file une fois |

## 14. Decisions requises de Brice

**D1 - Qui possede la base des entites.** `RM-2026-0026` (fichier des
coproprietaires relie aux AG) et `RM-2026-0099` construisent la meme base: le
CDC d'origine dit que les coproprietaires sont la population prioritaire
*parce qu'ils portent les tantiemes*. Un seul des deux doit la posseder.
Element de decision: `RM-2026-0026` est `PRET_A_INTEGRER` mais son livrable est
creux - `participants_ag_view.py` retourne un dictionnaire ecrit a la main, sans
acces instance ni coffre; `RM-2026-0099` part d'un annuaire qui fonctionne, 296
et 330 personnes mesurees sur deux cabinets.
**Ce cahier est ecrit sous l'hypothese que la base est unique et que le lot
annuaire la possede.** Si l'arbitrage va dans l'autre sens, les sections 6, 7 et
10 changent d'owner mais pas de contenu.

**D2 - L5 en premier, ou dans l'ordre.** L5 - nom de fichier, reserve, plafond
IA, comptage unique - ne depend d'aucun autre lot et corrige ce qui se voit
aujourd'hui a l'ecran. L1 corrige ce qui empeche le systeme de fonctionner.
Priorite a l'honnetete ou a la couverture: c'est un choix produit.

**D3 - Le seuil de C8.** 474 documents sur 825 en `C8_Restreint_Critique`
ressemble a un classement par prudence plutot qu'a un jugement piece par piece.
Independamment de F12, ce seuil merite d'etre reexamine - mais il appartient a
`confidentialite_et_biffage.md`, pas a ce cahier.

## 15. Ce qu'on revisera quand le systeme grandira

- **Le graphe d'entites** devient necessaire des la premiere identite entre une
  personne physique et une personne morale - une SCI, un nom commercial. Signal
  de bascule: une ambiguite qui n'est pas un homonyme.
- **L'annuaire en SQLite** le jour ou une entree doit porter une periode de
  validite; le CSV ne suffira plus.
- **La file partagee** si deux membres du conseil syndical arbitrent en
  parallele.
- **Le detecteur d'oublis** seulement quand A6 et A9 auront ete mesures sur une
  file reellement consommee, jamais avant.
