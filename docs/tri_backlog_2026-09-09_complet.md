<!-- Note de tri du gouvernail. Aucun nom reel, aucune adresse, aucun montant. -->

# Le tri du backlog, 73 items — et un seul se ferme

*2026-09-09. Ce tri couvre les 73 items ouverts que la conversation `CONV-2026-2172`
ne détenait pas elle-même. 31 agents, aucune erreur. Chaque affirmation ci-dessous
vient d'une mesure faite dans le dépôt.*

---

## 1. Le compte, et la mauvaise nouvelle d'abord

| Verdict | Nombre |
|---|---:|
| `FERMABLE`, verdict attaqué **et tenu** | **1** |
| `FERMABLE` ou `PERIME` **abattus** par la contre-enquête | **4** |
| `PARTIEL` | 42 |
| `OUVERT` | 25 |
| `FAIT_SANS_GARDE` | 1 |

**Cinq verdicts de fermeture ont été soumis à une contre-enquête. Quatre sont
tombés.** Quatre sur cinq, contre trois sur cinq au tri précédent. Ce taux n'est
pas un accident de rédaction : c'est la mesure d'un biais stable, et il a
toujours la même forme.

> **Le premier lecteur vérifie que le LIVRABLE existe. Le mandat, lui, est écrit
> plus loin — en fin de description, ou dans la colonne d'à côté.**

Quatre illustrations, toutes vérifiées :

- **`RM-2026-0055`** — cinq points de la description sont réellement faits. Mais
  la colonne *preuve* ajoutait une cible chiffrée : *« matrice sous 520 px »*. Le
  livrable mesure **521 px**, et il l'écrit lui-même dans son propre tableau de
  cibles. Le premier lecteur a cité le 521 comme *preuve que la mesure était
  faite* — il a lu le chiffre sans lire la cible d'à côté.
- **`RM-2026-0062`** — le mécanisme demandé est fait et il est bon. Mais l'item
  n'existe pas pour produire un mécanisme : il existe pour **lever un blocage**,
  et le document de référence du corpus dit encore le contraire aujourd'hui dans
  `HEAD`. Le premier lecteur prouvait la levée par la **présence physique d'un
  fichier dans un dossier**.
- **`RM-2026-0076`** — le premier lecteur affirmait *« le barème n'a pas été
  touché »*, en montrant que deux lignes de priorité n'avaient pas bougé. **Le
  commit qu'il citait lui-même comme correctif modifie le barème** : il n'avait
  regardé que les priorités, pas les mots-clés.
- **`RM-2026-0089`** — déclaré périmé. En réalité, quatre points sur cinq restent
  ouverts. Le registre stocke `legiarti`, `version` et `lu_le`, mais **pas le
  texte retenu** : son champ `texte` porte la désignation du texte englobant, pas
  une ligne de l'article lu.

**Ce que ce tri se reconnaît comme limite.** Les 68 verdicts `PARTIEL` et
`OUVERT` **n'ont pas été contre-enquêtés** : seuls les verdicts de fermeture le
sont. Au taux constaté, une partie des `PARTIEL` sous-estime ou surestime ce qui
reste. Un `PARTIEL` est une piste, pas un jugement définitif.

---

## 2. Ce qui se ferme : un item

**`RM-2026-0057` — le test de sécurité Drive.** Verdict attaqué et tenu.
Correctif commité (`acae9bf`, vérifié ancêtre de `HEAD`), rejoué dans les deux
ordres avec ses voisins, 13 tests verts des deux côtés.

**Mais la ligne raconte une histoire fausse, et c'est la partie durable.** Elle
accusait un *« état partagé »* et une dépendance à l'ordre d'exécution. Il n'y en
avait aucun. La vraie cause : le test fabriquait son code « truqué » en
remplaçant le dernier caractère par `0` — or ce caractère est un chiffre
hexadécimal, donc **une fois sur seize le code truqué était identique à
l'original**, l'import réussissait, et le test rendait vert. Fermer sans corriger
le motif laisserait au gouvernail une explication démentie qu'un lecteur futur
reprendrait.

---

## 3. Là où l'éclusage se gagne vraiment

Un gros item dont il ne reste qu'un huitième est un petit item déguisé. Voici
ceux dont le reste est mesuré et petit.

### 3.1 Dix minutes à une heure

- **`RM-2026-0050`** — une pièce du corpus est présente mais absente du manifeste
  (30 fichiers pour 29 lignes), et **les six valeurs à inscrire sont déjà
  calculées** dans le journal du lot qui a posé le manifeste. Copier-coller.
- **`RM-2026-0128`** — priorités et liens de l'artefact gouvernail : une demi-heure.
- **`RM-2026-0004`** — la deuxième demande **est faite, mais sous un autre
  numéro**, ce qui explique qu'on ne la voyait pas ; la troisième demandait de ne
  rien faire, et rien n'a été fait. Ne reste qu'une recette **orpheline de son
  instance** : celle que la ligne nomme n'existe plus. Arbitrage, pas ingénierie.

### 3.2 Une demi-journée, et un défaut de forme grave à chaque fois

- **`RM-2026-0006`** — le mandat dit *« garder le panier live comme
  régression »*. Mesuré : ce panier rend `Ran 0 tests — OK (skipped=1)`. Il
  s'active par une variable d'environnement que **personne ne pose**, ni la CI ni
  aucun outil. **Un panier de régression qui annonce OK en ayant joué zéro test
  ne garde rien : il rassure.**
- **`RM-2026-0014`** — trois points sur quatre faits. Le quatrième a été
  **contourné, pas rempli** : le module livré sous ce numéro (565 lignes, vert)
  **n'est importé par rien** — seulement par son propre test. **Un module mort qui
  porte le nom du mandat fait croire que le mandat est rempli**, et c'est ce qui a
  failli fermer l'item.
- **`RM-2026-0056`** — la règle livrée produit deux nouveaux états de doute. Ils
  **n'apparaissent nulle part dans la couche web** et ne figurent pas parmi les
  statuts qui font remonter un document à la boîte de réception. **Le doute
  produit ne remonte pas à l'humain.** Attention en corrigeant : cette liste est
  une énumération de modalités ; y ajouter deux chaînes ferait passer ce cas et
  laisserait le neuvième statut tomber dans le même trou.
- **`RM-2026-0003`** — les trois éléments existent et sont tenus par 16 tests,
  mais **le troisième n'a jamais été recetté**, et la chronologie le prouve à la
  minute : la recette se termine à 01h21, l'exigence est écrite à 01h19, et le
  code concerné n'atterrit qu'à 23h53 — **22 heures après la recette**. En prime,
  sa description **s'auto-renouvelle** : sa « prochaine suite » a été exécutée
  deux fois sans jamais être remplacée, donc **l'item ne peut pas se fermer, quoi
  qu'on livre**.
- **`RM-2026-0051`** — trois mandats sur quatre. Il manque **les deux critères
  chiffrés qui exigent d'écrire dans le produit et d'en sortir un livrable** —
  soit exactement les deux gestes que l'audit s'était interdits. Ce n'est pas un
  oubli de rédaction, c'est un pan de protocole non joué.

---

## 4. Ce qui ne coûte rien et débloque beaucoup

**`RM-2026-0137` est décomposable en trois lots, et deux ne sont pas bloqués.**
L'item attend aujourd'hui pour rien sur ses deux tiers.

1. **Petit et immédiat — poser une garde sur `git push`.** C'est le défaut de
   conception que l'item nomme lui-même : la garde de partage gouverne le module
   de **publication**, et **rien ne relie `git push` à la doctrine**. Quelques
   dizaines de lignes.
2. **Moyen et non bloqué** — les captures d'écran des campagnes et les trois notes
   qui portent des montants réels. Se traite pièce par pièce.
3. **Lourd et réellement bloqué** — le résidu de `docs/` et surtout l'historique
   déjà public, qui exige une réécriture irréversible et un détecteur de
   patronymes fiable (bloqué par `RM-2026-0065` et `RM-2026-0068`).

**Trois items visent une seule ligne de code** — `RM-2026-0065`, `RM-2026-0097`,
`RM-2026-0099`, la garde du patronyme seul. Dire lequel porte la réparation coûte
une minute et évite que trois lots réparent la même chose.

**Une dépendance morte immobilise en silence.** `RM-2026-0152` sert un chantier
`ABANDONNE` depuis le 2026-05-31, dont la ligne est `CLOSE` depuis le 2026-09-04.

---

## 5. Ce que ce tri ne pouvait pas décider

**Une question, une seule, et elle débloque deux items.**

> **L'outil `tools/reconstruction_protocol.py` sert-il encore ?**

Il porte **les huit dernières occurrences du nom réel de la copropriété hors
`docs/`** dans tout le dépôt suivi, et il sert un chantier abandonné. La mesure
penche vers la suppression : quatre gestes, une demi-heure. La conserver coûte
deux heures de refonte — sortir l'instance attendue de sa constante et réécrire
son refus sur une propriété au lieu d'un patronyme.

Deux autres décisions sont hors de portée d'un tri :

- effacer de l'historique GitHub ce qui y est public depuis juin demande une
  réécriture irréversible ;
- un module produit porte le nom d'un fournisseur réel : c'est un choix de
  conception, et aussi une modalité au sens de la règle des axes.

---

## Limites de cette note

Les 42 `PARTIEL` et 25 `OUVERT` **n'ont pas été contre-enquêtés**. Au taux mesuré
sur les fermetures — quatre sur cinq —, une part d'entre eux se révélera plus
petite ou plus grosse qu'annoncé.

**Un défaut de ma propre chaîne, qui aurait pu passer inaperçu.** La synthèse
automatique de ce tri a reçu les 73 instructions **tronquées à 110 000
caractères**, et a rendu une note qui annonçait couvrir 18 items sans dire
nulle part que 55 avaient été coupés. La troncature était muette. Les 73
instructions ont été récupérées depuis le journal du tri, et c'est sur elles que
cette note est écrite. C'est le même motif que ceux traqués ailleurs : une sortie
qui a l'air complète et qui ne l'est pas.

Aucun nom réel, aucune adresse et aucun montant ne figure dans cette note.
