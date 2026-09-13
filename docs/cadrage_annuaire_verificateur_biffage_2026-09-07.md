# Cadrage: annuaire, file d'arbitrage et verificateur d'oublis

**Statut: cadrage, non executoire.** Ce document est le bloc d'enquete exige par
`CLAUDE.md` avant tout code applicatif sur une feature transverse. Il ne
declare aucun chantier, aucun owner et aucun port. Il se termine par une gate
GO/NO-GO dont une condition est un arbitrage de Brice.

Rattachement gouvernail: `RM-2026-0096` (verificateur d'oublis),
`RM-2026-0097` (patronyme isole), `RM-2026-0098` (reserve sur le derive),
`RM-2026-0099` (entree dans l'annuaire). Chevauchement declare avec
`RM-2026-0026`.

Sources mesurees reutilisees ici sans les refaire:
[`corpus_caviarde_2026-09-04.md`](./corpus_caviarde_2026-09-04.md),
[`cdc_base_personnes_et_biffage.md`](./cdc_base_personnes_et_biffage.md),
[`confidentialite_et_biffage.md`](./confidentialite_et_biffage.md).

---

## 1. Probleme utilisateur

Un coproprietaire veut faire tourner une analyse - la sienne, ou celle d'un
agent - sur les pieces de sa copropriete, sans que les noms des autres
coproprietaires circulent. La passe automatique de caviardage laisse des
oublis. Aujourd'hui ces oublis sont **comptes** et personne ne les traite.

Formulation novice: *je veux pouvoir donner mes documents a lire a un outil,
sans donner en meme temps le nom de mes voisins, et savoir ce qui reste
dessus.*

## 2. Perimetre

**Dans le perimetre**

- l'entree des personnes dans l'annuaire, automatique et humaine;
- la file d'arbitrage des formes suspectes deja produite en C8;
- la confrontation locale d'une forme suspecte a l'annuaire;
- la reserve ecrite sur le derive.

**Hors perimetre, et il faut le dire**

- l'OCR et l'ajout d'une couche texte: decision de packaging, pas de module,
  deja arbitre au lot du 2026-09-04;
- la synchronisation entre postes;
- le graphe personnes physiques / personnes morales du CDC section 4 ter: il est
  necessaire a terme, il n'est pas necessaire pour consommer la file;
- toute inference de modele, tant que la gate de la section 13 n'est pas
  franchie.

## 3. Exigences

**Fonctionnelles**

| # | Exigence |
|---|---|
| F1 | Une forme suspecte peut recevoir une des trois reponses: personne connue, personne inconnue, pas une personne. |
| F2 | Une reponse humaine est definitive vis-a-vis de la machine: une re-extraction ne l'ecrase pas. |
| F3 | Une personne absente de l'annuaire recoit un alias ephemere, propre au document, jamais reutilise ailleurs. |
| F4 | Une ambiguite entre homonymes n'est jamais tranchee par la machine. |
| F5 | Une exclusion (`pas une personne`) est motivee et propre a l'instance. |
| F6 | Le derive porte ecrit contre qui il protege. |

**Non fonctionnelles**

| # | Exigence | Raison |
|---|---|---|
| N1 | Aucun octet ne quitte la machine par defaut. | Local-first; `ai_processing_ceiling` ne connait que `no_ai` et `local_only`. |
| N2 | Aucune degradation silencieuse: un annuaire vide doit se voir. | Regle d'acceptation des extracteurs de `CLAUDE.md`. |
| N3 | Le budget humain est la ressource rare, pas le CPU. | Voir section 4. |
| N4 | Pas de nouvelle dependance runtime sans arbitrage. | Le produit est un exe PyInstaller; `torch` et des poids changent la nature du livrable. |
| N5 | Reproductibilite: deux passages sur le meme corpus rendent le meme alias. | Le sel d'instance l'assure deja. |

**Contraintes de contexte**

- une instance = une copropriete = un poste Windows, un seul utilisateur;
- le sel ne quitte jamais l'instance;
- l'annuaire et la table de correspondance vivent en C8;
- `corpus_caviarde.enabled` est faux par defaut.

## 4. Estimation de charge, et la contrainte liante

Chiffres releves, pas estimes (`corpus_caviarde_2026-09-04.md`):

| | Tilleuls (pseudo) | Erables (pseudo) |
|---|---:|---:|
| documents | 32 | 22 |
| personnes a l'annuaire | 296 | 330 |
| dont issues d'une liste nominative | 200 | **0** |
| formes suspectes distinctes | 582 | 1 046 |
| occurrences suspectes | 4 140 | 5 742 |
| rappel mesure sur le PV | 95,4 % | non mesurable, pas de verite terrain |

Le calcul qui commande l'architecture:

- **cout d'une decision humaine**: environ 7 occurrences levees par forme
  arbitree (4 140 / 582). A cinq secondes par forme, 1 046 formes coutent
  environ 87 minutes d'attention continue.
- **cout d'un document fourni a l'absorption**: l'annexe des soldes de
  Tilleuls (pseudo) a rendu 200 personnes d'un coup, et porte le rappel du PV a
  95,4 %.

**Rapport de levier: environ 200 pour 1 en faveur de l'entree.** Le CPU n'est
jamais la contrainte - 32 documents se traitent en secondes sur un poste. La
contrainte est l'attention d'une personne, et elle se depense mal si on la met
sur la file avant d'avoir nourri l'annuaire.

Un coffre reel compte environ 1 090 documents, soit trente fois le corpus de
test. Le nombre de formes distinctes croit moins vite que le nombre de
documents, mais l'ordre de grandeur reste le millier. Une file non hierarchisee
est donc inexploitable par construction, quel que soit le detecteur qui la
remplit.

## 5. Vue d'ensemble

```text
                      ENTREE                          |          LECTURE
                                                      |
  piece deposee                                       |
       |                                              |
       v                                              |
  [ absorption ]---- couche texte ? --non--> PDF_SANS_COUCHE_TEXTE
       |                                     (angle mort declare, pas une fuite)
       | oui                                          |
       v                                              |
  [ G1 gate annuaire ] --- liste nominative ? --non--> demande explicite
       |                     (annexe des soldes)       a l'utilisateur
       | oui                                          |
       v                                              |
  [ annuaire C8 ]  <---- assertions datees -----+     |
       |                                        |     |
       v                                        |     |
  [ passe A: applique_annuaire ]                |     |
       |                                        |     |
       v                                        |     |
  [ passe B: regles generiques ]                |     |
       |                                        |     |
       v                                        |     |
  derive Markdown caviarde  ------------------------> lisible par un agent
       |                                        |     |
       v                                        |     |
  [ passe C: suspects_residuels ]  (local, sans IA, existe deja)
       |                                        |
       v                                        |
  corpus_caviarde_suspects.csv (C8)             |
       |                                        |
       v                                        |
  [ file d'arbitrage: 3 verbes ] ---------------+
       |         |            |
    connue   inconnue    pas une personne
       |         |            |
       v         v            v
  rattache   cree l'entite  exclusion motivee
             (alias stable)  propre a l'instance
```

Ce que ce schema dit, et qui est le coeur du cadrage: **la seule boucle qui
ferme le systeme part de la file et revient dans l'annuaire.** Tant que cette
fleche de retour n'existe pas, ameliorer le detecteur ne change rien - il
remplit plus vite une file que personne ne vide.

## 6. Le geste a plus fort levier: la gate G1

`corpus_caviarde_2026-09-04.md` l'ecrit deja: *la bonne reponse produit n'est
pas une meilleure heuristique, c'est d'exiger l'annexe des soldes a
l'absorption.* Erables (pseudo) le prouve par l'absurde: 0 personne issue d'une
liste nominative, 1 046 formes suspectes, et un rappel qui n'est meme pas
mesurable.

**Sonde du 2026-09-07, sur donnees fictives, et le resultat est plus large
que l'hypothese.** J'avais soupconne que `extrait_entrees_annuaire` ne
reconnaissait que l'annexe en trois lignes. Sept mises en page portant les
memes quatre personnes fictives:

| Forme de la liste nominative | Personnes trouvees |
|---|---:|
| trois lignes `compte / NOM / montant` - la forme observee | 4/4 |
| trois lignes, montant suivi du symbole euro | 4/4 |
| une seule ligne `compte NOM montant` | **0/4** |
| table a barres verticales `\| compte \| nom \| solde \|` | **0/4** |
| deux lignes `compte NOM` puis `montant` | **0/4** |
| trois lignes, nom en casse mixte `Marchand Etienne` | **0/4** |
| trois lignes, numero de compte a quatre chiffres | **0/4** |

**Cinq formes sur sept rendent zero personne, sans rien signaler.** La sonde
est versionnee et rejouable: `server/tests/test_annuaire_formes_liste_nominative.py`,
trois tests. Ce ne sont pas cinq bugs: c'est une seule cause, l'extracteur code la mise en page observee
chez un cabinet au lieu de nommer l'axe. L'axe est *la maniere dont une liste
nominative distribue compte, nom et montant sur des lignes*; l'invariant le long
de cet axe est qu'un numero de compte, un nom et un montant se suivent dans cet
ordre, quel que soit le nombre de sauts de ligne entre eux.

La casse mixte et le compte a quatre chiffres sont les plus revelateurs: ce ne
sont meme pas des mises en page differentes, juste des valeurs voisines sur un
autre axe. La reponse produit ne peut donc pas etre `ajouter la table a barres`.

**G1** est donc une gate d'absorption, pas un ecran de plus:

- a l'absorption d'un corpus, l'outil dit s'il a trouve une liste nominative;
- s'il n'en trouve pas, il **demande** la piece, en nommant laquelle - annexe
  des soldes, etat des comptes individuels, liste d'emargement - au lieu de
  produire un derive qui a l'air propre;
- tant que la piece manque, le derive est produit mais porte la mention
  `ANNUAIRE_ABSENT` et la reserve de la section 9.

Precedent produit a reutiliser tel quel: `/documents/non-lus` demande deja
l'accord OCR, et enregistre la reponse pour ne jamais redemander. Meme forme.

## 7. Contrats

### 7.1 Contrat d'entree dans l'annuaire

Une entree est une **assertion datee**, jamais un etat.

| Champ | Sens |
|---|---|
| `entite_id` | identifiant stable de la personne, derive du sel |
| `assertion` | `coproprietaire`, `mandataire`, `tiers`, `personne_morale` |
| `doc_id` | piece qui porte l'assertion |
| `date_piece` | date du document, pas date de saisie |
| `source` | `LISTE_NOMINATIVE`, `REGLE_GENERIQUE`, `SAISIE_HUMAINE` |
| `origine` | `EXTRAIT` ou `CORRIGE_HUMAIN` |

Motif: le CDC section 3.2 exige une base datee - un PV de 2019 se lit contre
l'annuaire de 2019, et un ancien coproprietaire nomme dans une piece ancienne
n'est pas une erreur. La structure existe deja: `object_links` porte `event_id`
dans sa contrainte UNIQUE, precisement pour laisser coexister plusieurs
assertions sur un meme couple.

### 7.2 Contrat de la file d'arbitrage

En entree, ce que `suspects_residuels` produit deja: `doc_id`, `genere_le`,
`forme`, `occurrences`, `motif`.

Il manque trois champs pour que la file soit hierarchisable, et c'est le seul
ajout de schema necessaire cote detection:

| Champ | Sens |
|---|---|
| `racine_normalisee` | `normalize_identity_key(forme)`, pour grouper les variantes d'une meme personne en UNE decision |
| `nb_documents` | nombre de pieces ou la forme apparait, pour le rang |
| `appariement_propose` | entite de l'annuaire approchee, s'il y en a une seule; vide si zero ou plusieurs |

**Mesure du 2026-09-07, rejouable par `tools/mesure_file_arbitrage.py`, et elle
refute l'hypothese de ce cadrage.** J'avais
ecrit que le groupement par racine ramenerait la file a un nombre de decisions
nettement inferieur. Mesure sur les deux corpus du lot `corpus_caviarde_lot_20260904`:

| | formes | occurrences | groupes par racine | reduction |
|---|---:|---:|---:|---:|
| Tilleuls (pseudo) | 582 | 4 140 | 543 | **7 %** |
| Erables (pseudo) | 1 046 | 5 742 | 952 | **9 %** |

Le groupement ne sert a rien, parce que la distribution est plate: il faut
encore 336 decisions chez Tilleuls (pseudo) et 665 chez Erables (pseudo) pour couvrir
95 % des occurrences. Et l'appariement automatique ne sauve pas non plus - seuls
24 groupes sur 543, et 77 sur 952, ont une racine deja presente comme patronyme
dans l'annuaire.

**Ce qui marche, mesure dans la meme passe: partitionner sur le nombre de
documents.** Une forme presente dans au moins deux pieces est a la fois plus
probablement une personne - un coproprietaire recurre a travers les pieces, une
raison sociale ponctuelle ou un intitule comptable non - et plus fuyante, parce
qu'elle apparait plus souvent.

| | groupes | dont 1 seule occurrence | dont 1 seul document | **presents dans >= 2 documents** |
|---|---:|---:|---:|---:|
| Tilleuls (pseudo) | 543 | 237 | 361 | **182 (-66 %)** |
| Erables (pseudo) | 952 | 464 | 606 | **346 (-64 %)** |

`nb_documents` n'est donc pas une cle de tri, c'est la **partition primaire** de
la file. Premier lot: les formes vues dans plusieurs pieces, 182 et 346
decisions, de l'ordre de 15 et 29 minutes. Second lot: le reste, en priorite
basse.

**Et c'est une partition, jamais une exclusion.** Une fuite dans une seule piece
reste une fuite. Tant que le second lot n'est pas traite, le derive doit le dire
dans sa reserve - voir section 9.

### 7.3 Contrat d'un detecteur externe, si un jour il y en a un

Non requis par ce cadrage. Ecrit ici pour qu'il ne soit pas improvise plus tard.

- entree: une fenetre, pas un dossier, degradee sur tout ce qui n'est pas la
  tache (`<MONTANT>`, `<COMPTE>`), a longueurs preservees;
- sortie: `{debut, fin, longueur, categorie, indice}`, jamais du texte reecrit;
- validation locale: un span dont le texte ne correspond pas est rejete sans
  etre interprete;
- **un seul tour**: le resultat de la confrontation ne repart jamais vers le
  detecteur, sinon il devient un oracle d'appartenance qui reconstitue
  l'annuaire par interrogation.

## 8. Modele de donnees et stockage

| Donnee | Ou | Pourquoi |
|---|---|---|
| sel d'instance | `sel_alias.key`, C8 | existe; ne quitte jamais l'instance |
| annuaire des personnes | `annuaire_personnes.csv`, C8 | registre preexistant; la doctrine ne migre pas l'existant sans demande |
| table de correspondance | C8 | existe |
| file de suspects | `corpus_caviarde_suspects.csv`, C8 | existe; contient par construction des noms non caviardes |
| **arbitrages humains** | **SQLite du coffre** | ajout: la doctrine du 2026-09-03 interdit un nouveau registre CSV |
| **exclusions d'instance** | **SQLite du coffre** | idem |
| **assertions datees** | **SQLite du coffre** | idem |

**Le piege a ne pas retomber dedans.** `_reset_schema` est appele a chaque
reconstruction, complete ou incrementale
(`vault/_reconstruction_parts/02_schema.py`). Une table ajoutee a la base de
reconstruction sans recorder ni projection serait effacee au rebuild suivant,
et la perte serait differee donc invisible. `vault/gouvernance_store.py` a deja
resolu ce probleme en ouvrant une base dediee qui n'est pas reconstruite:
**c'est ce magasin-la qu'il faut etendre, pas la base de reconstruction.**

Colonne `origine`, liste fermee `EXTRAIT` / `CORRIGE_HUMAIN`, deja imposee par
`gouvernance_store`. Elle porte F2 a elle seule: la clause
`DELETE ... AND origine <> 'CORRIGE_HUMAIN'` epargne une correction humaine.
Une troisieme valeur est un arbitrage, jamais une commodite d'appel - le
precedent `EXTRAIT_V2` a produit un euro double.

## 9. La reserve ecrite sur le derive

En tete de chaque derive, deux lignes, en langage novice:

- **contre qui il protege**: un lecteur exterieur a la copropriete. Pas un
  coproprietaire, qui dispose de l'etat date et peut relier un alias a un lot;
- **ce qu'il ne couvre pas**: les pieces sans couche texte
  (`PDF_SANS_COUCHE_TEXTE`), et l'etat de l'annuaire (`ANNUAIRE_ABSENT` ou
  nombre de personnes connues).

Motif: les quasi-identifiants conserves - lot, tantiemes, montants, dates - sont
le vecteur de reidentification, et ce sont exactement ceux qu'il faut garder
pour que le derive reste analysable. Une protection non ecrite est une
protection affirmee et non delivree.

## 10. Degradation: la regle est de ne jamais repondre faux en silence

| Situation | Comportement exige |
|---|---|
| pas de couche texte | `PDF_SANS_COUCHE_TEXTE`, deja en place; angle mort declare |
| aucune liste nominative trouvee | G1 demande la piece; derive marque `ANNUAIRE_ABSENT` |
| forme suspecte appariee a plusieurs entites | `PERSONNE_{racine}` sans couleur, plus une entree en file; jamais de choix |
| forme suspecte appariee a rien | alias ephemere de document, plus une entree en file; jamais `donc ce n'est pas une personne` |
| annuaire vide | le derive est produit, mais le compteur de personnes connues affiche 0 et la reserve le dit |

Le cas interdit est celui que Erables (pseudo) expose: produire un derive
`MARKDOWN_OK` sur un annuaire vide sans que rien ne le signale a
l'utilisateur.

## 11. Criteres d'acceptation et tests attendus

Etalon: `instances/tests_ux` et `docs/etalon_corpus_tests_ux.md`, etabli a la
main avant tout traitement outil. Epreuve inter-cabinet obligatoire sur
`instances/erables_pseudo_test`. Jamais une instance historique comme etalon.

| # | Critere | Mesure |
|---|---|---|
| A1 | Une decision humaine survit a une re-extraction complete | rejouer l'absorption, verifier que les lignes `CORRIGE_HUMAIN` sont intactes |
| A2 | Un faux positif de la passe B peut etre retire de l'annuaire | aujourd'hui impossible: `RegistrePseudonymes` n'a aucun chemin de suppression |
| A3 | Une exclusion d'instance ne fuit pas vers une autre instance | deux instances, meme forme, deux decisions independantes |
| A4 | G1 se declenche sur un corpus sans liste nominative | Erables (pseudo) doit lever la demande, pas produire un derive muet |
| A5 | ~~Le groupement par racine reduit reellement la file~~ | **MESURE LE 2026-09-07, REFUTE**: 7 % chez Tilleuls (pseudo), 9 % chez Erables (pseudo). Critere abandonne. |
| A5bis | La partition sur `nb_documents >= 2` reduit reellement la file | **MESURE LE 2026-09-07, TENU**: 543 -> 182 groupes (-66 %) et 952 -> 346 (-64 %). C'est ce critere qui remplace A5. |
| A8 | `extrait_entrees_annuaire` ne rend jamais zero en silence | **MESURE LE 2026-09-07, ECHOUE**: 5 formes de liste nominative sur 7 rendent zero personne sans rien signaler. Voir section 6. |
| A6 | Le rappel ne baisse pas | rappel du PV Tilleuls (pseudo) >= 95,4 %, valeur de reference du 2026-09-04 |
| A7 | La precision ne s'effondre pas | `article NN` 139/139 et montants 307/307 conserves; c'est la garde anti-incident du 2026-09-03 |

A2 est un critere de conception, pas seulement de test: il n'est aujourd'hui
pas satisfiable, et c'est la raison principale de `RM-2026-0099`.

## 12. Arbitrages explicites

| Choix | Retenu | Rejete | Cout du choix |
|---|---|---|---|
| Ou porter l'effort | l'entree (G1 + file) | un meilleur detecteur | on garde un detecteur imparfait plus longtemps |
| Detecteur d'oublis | `suspects_residuels`, local, deja la | un modele local | on renonce aux formes que la regex ne voit pas: prenoms isoles, descriptions definies |
| Runtime de modele | aucun, pour l'instant | `torch` + poids dans l'exe | on ne saura pas ce que l'IA aurait attrape tant qu'on n'aura pas vide la file |
| Alias d'un inconnu | ephemere, par document | stable | deux mentions du meme inconnu dans deux pieces restent non reliees |
| Ambiguite | non tranchee, racine seule | choix par score | l'utilisateur voit un alias moins precis |
| Magasin | base dediee `gouvernance_store` | base de reconstruction | une convergence reste a faire plus tard |
| Annuaire CSV | conserve | migration SQLite | deux magasins coexistent le temps du lot |

**L'arbitrage central, et il tient a une mesure.** Aucun runtime de modele
n'existe dans le produit: `_write_qwen_review_payload` ecrit un JSON de statut
et ne fait aucune inference. Ajouter un detecteur IA n'est donc pas un
increment, c'est une dependance runtime dans un exe PyInstaller. Or personne
n'a encore traite une seule des 1 628 formes deja signalees par le detecteur
local. **On ne peut pas savoir qu'un modele est necessaire avant d'avoir vide
la file et mesure ce qu'elle laisse passer.** L'IA est donc la derniere etape,
pas la premiere - et peut-etre pas une etape du tout.

## 13. Ce que je reviserais quand le systeme grandit

- **Le graphe d'entites.** Des qu'une SCI ou un nom commercial apparait
  (`T Services` / `Tanore` du CDC), la ligne plate ne suffit plus. Signal de
  bascule: la premiere ambiguite qui n'est pas un homonyme mais une identite
  entre personne physique et morale.
- **L'annuaire en SQLite.** Signal: le jour ou une entree doit porter une
  periode de validite, le CSV ne suffit plus.
- **La file partagee entre postes.** Hors perimetre ici; deviendra necessaire
  si deux membres du conseil syndical arbitrent en parallele.
- **Le detecteur.** Reexaminer seulement quand A5 et A6 sont mesures sur une
  file reellement consommee.

## 14. Gate GO / NO-GO

**NO-GO tant que ces trois conditions ne sont pas remplies:**

1. **Arbitrage Brice sur le chevauchement `RM-2026-0026` / `RM-2026-0099`.**
   Les deux construisent la meme base d'entites - les coproprietaires portent
   les tantiemes. Un seul des deux doit la posseder. Deux items qui construisent
   la meme base est le defaut mesure par l'audit `RM-2026-0084`.
2. **Mesure A5 faite**, cote detection seule: combien de decisions humaines
   apres groupement par racine, sur les deux corpus. Sans ce nombre, promettre
   une file exploitable est une affirmation non delivree.
3. **Equipe d'agents constituee** selon
   `docs/strategie_equipes_multi_agents.md`, avec au minimum expert domaine,
   QA/privacy et novice. La doctrine l'exige pour une feature transverse, et un
   owner unique de fichier n'en tient pas lieu.

**Les deux mesures annoncees ici comme faisables sans attendre ont ete faites
le 2026-09-07, et versees au depot le meme jour apres challenge du fil de
coordination.** Un chiffre qui fixe un ordre de travaux et qu'on ne peut pas
rejouer est une affirmation, pas une mesure. Les deux instruments n'ont pas le
meme statut, parce que leurs entrees n'ont pas le meme statut:
`server/tests/test_annuaire_formes_liste_nominative.py` est un TEST - donnees
fictives, rejouable en CI, il echouera le jour ou le defaut sera repare;
`tools/mesure_file_arbitrage.py` est un OUTIL et ne peut pas devenir un test,
son entree etant un fichier de C8 qui contient des noms non caviardes et
n'entrera jamais dans Git. Il n'imprime que des entiers.** Elles n'ont touche aucun fichier de code, ouvert aucun serveur
et cree aucune instance; elles ont lu en place les sorties du lot
`corpus_caviarde_lot_20260904` et sonde un extracteur sur des donnees fictives.

**La condition 2 est levee, et sa reponse est negative.** Le groupement par
racine ne reduit la file que de 7 a 9 %. Ce n'est pas la file qui etait mal
triee, c'est le critere de tri qui etait faux. Le critere qui tient est la
partition sur `nb_documents >= 2`: -66 % et -64 %, soit 182 et 346 decisions en
premier lot. Section 7.2 pour le detail. Le cadrage est corrige en consequence,
et A5 remplace par A5bis.

**Un defaut neuf est apparu, et il precede tout le reste**: cinq mises en page
de liste nominative sur sept rendent zero personne sans rien signaler
(section 6). Tant que ce point n'est pas traite, la gate G1 ne peut pas
distinguer `ce corpus n'a pas de liste nominative` de `ce corpus en a une que je
ne sais pas lire` - et c'est exactement la confusion qui rend la degradation
silencieuse. **Ce defaut est prioritaire sur la file d'arbitrage**, parce qu'un
annuaire complet vide la file par le haut alors que la file ne remplit
l'annuaire qu'une decision a la fois.

**Reste donc au NO-GO**: la condition 1, qui appartient a Brice, et la
condition 3, qui en depend.
