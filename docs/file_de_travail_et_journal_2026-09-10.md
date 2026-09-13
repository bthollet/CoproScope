# Le gouvernail est un journal. La file est ailleurs, et elle est courte

Lot du 2026-09-10. Consigne de Brice du 2026-09-09 : *« Mets en place ces
outils »*, puis *« pour la file, c'est toi qui connais les bons standards »*.

## Le défaut, et il est arithmétique

Taux d'arrivée ÷ taux de fermeture = **4,8 pour 1**. Au-dessus de 1 soutenu, un
registre cesse d'être un outil de pilotage. Ce n'est pas un défaut en soi — un
défaut connu vaut mieux qu'un défaut invisible. **Le défaut est de s'en servir
pour savoir où l'on en est.**

## L'état réel, mesuré le 2026-09-10

| | |
|---|---:|
| Items au registre actif | **161** |
| `ENGAGE` — on y travaille | **55** / plafond 3 |
| `DECISION` — la balle est chez Brice | **6** / plafond 5 |
| `JOURNAL` — connu, tenu, non traité | 52 |
| `CLOS` | 48 |

**Les deux plafonds sont dépassés.** Et le chiffre qui compte : 55 items sont
déclarés en cours pour une personne seule.

Ce chiffre corrige aussi ma façon de rendre compte. Je rapportais « 5 P0
`ACTIF` » comme mesure d'avancement — c'est vrai, mais c'est la **tranche P0**.
Toutes priorités confondues, le registre dit que **55 choses sont en cours**.

## Les quatre états, et pourquoi le troisième manquait

| État | Ce qu'il dit | Statuts du gouvernail |
|---|---|---|
| `ENGAGE` | quelqu'un y travaille maintenant | `ACTIF` |
| `DECISION` | la balle est chez l'humain | `A_ARBITRER`, `EN_ATTENTE_USER` |
| `JOURNAL` | connu, tenu par une garde, non traité | `PRET_A_INTEGRER`, `A_QUALIFIER`, `BLOQUE` |
| `CLOS` | tranché, dans un sens ou dans l'autre | `INTEGRE`, `ABANDONNE` |

**Sans `JOURNAL`, tout défaut connu compte comme du travail en retard**, et le
nombre d'`ACTIF` devient ininterprétable. `PRET_A_INTEGRER` en particulier
n'est pas du travail engagé : c'est du travail **fini** qui attend une
intégration. Le compter dans la file gonflerait celle-ci de tout ce qui a déjà
abouti.

## Les deux plafonds, et le second est le vrai goulot

**Trois items engagés** — standard du kanban personnel pour une personne seule.

**Cinq décisions en attente au maximum.** Le 2026-09-09, **13 décisions
attendaient Brice**. Aucun débit de développement ne rattrape cela : le goulot
n'est pas la production, c'est l'arbitrage.

Au-delà d'un plafond : **rien n'entre tant que rien ne sort.**

## La politique d'âge : nommer, jamais fermer

Un item que personne n'a touché depuis 90 jours est revu ou fermé. La règle du
métier : *si ça n'a pas valu la peine en trois mois, ça se ferme — ça reviendra
si ça compte*.

L'outil **ne ferme rien**. Il nomme. Six items dorment depuis plus de 100 jours,
dont deux `PRET_A_INTEGRER` de fin mai. **Fermer est une décision.**

## Ce que l'outil refuse de faire, et c'est la leçon du jour

**Il ne vérifie jamais qu'un compte reste au-dessus d'un seuil.**

Une garde écrite ce matin même exigeait `len(mesurees) > 10` sur un ensemble qui
ne contient que les P0 encore `ACTIF`. Elle a échoué **le jour où un chantier a
abouti**. Une garde qui exige que le backlog reste plein est une garde à
l'envers. Ici, tous les plafonds sont des **maxima**, et un test dont c'est le
seul objet vérifie qu'un registre vide reste silencieux.

**Il ne crée aucun second registre.** Écrire les items ailleurs reproduirait le
défaut numéro un du produit — plusieurs comptages concurrents pour la même
notion, constaté le 2026-09-02 avec quatre comptages pour une seule notion. La
file est **dérivée** : elle se recalcule à chaque appel, il n'y a qu'une source.

**Il ne fait pas échouer `agent-check`.** Un plafond dépassé est une information
de pilotage, pas une régression de code — et une garde qui bloquerait le travail
parce que la file est pleine empêcherait précisément de la vider.

## Deux défauts de ma propre écriture, trouvés par la mutation

**Le premier jet comptait 185 items là où le registre en porte 161.** Le
document aligne des lignes `RM-*` dans **quatre sections** : le registre actif,
`Hors file d'exécution`, `Temps humain explicite`, et une synthèse de mai. Un
outil qui les additionne fabrique exactement le cinquième comptage concurrent
qu'il existe pour éviter. L'outil lit désormais **la seule** section du registre
actif, et **refuse** si le titre a changé au lieu de se rabattre sur le document
entier.

**Mon test sur l'échappement ne gardait rien.** Il vérifiait que le statut
restait lu malgré une barre échappée. Or le statut est trouvé par balayage de
valeur sur toutes les cellules : un découpage naïf en produit davantage, et la
valeur s'y trouve quand même. La mutation passait au vert. Ce qui dépend
vraiment de l'échappement, c'est la cellule lue **par sa position** — le titre,
coupé à la première barre citée, et le résultat reste crédible.

## Preuve que la garde mord

| Ligne cassée | Verdict |
|---|---|
| l'outil relit tout le document | 7 échecs |
| le découpage ignore l'échappement | 1 échec |
| le plafond devient un **plancher** | 5 échecs |
| du travail fini compte comme engagé | 1 échec |
| un item déjà clos redevient dormant | 2 échecs |
| un statut inconnu entre dans la file | 1 échec |

## Ce qui reste à faire, et ce n'est pas à moi de le faire

1. **Remplir la file.** Une file se décide ; elle ne se dérive pas d'une colonne
   d'intention. Aujourd'hui l'outil lit `ACTIF` faute de mieux, et 55 items y
   entrent. Les trois qui sont réellement engagés, c'est Brice qui les nomme.
2. **Trancher les six décisions en attente**, dont l'historique GitHub
   (`RM-2026-0137`) et le sort de `tools/reconstruction_protocol.py`
   (`RM-2026-0152`).
3. **Statuer sur les six dormants** de plus de 100 jours.

## La règle que je me donne, et qui me concerne d'abord

**`found → fixed in the same change`** : un défaut que mon propre instrument
trouve se corrige ou se décline **sur place**. On ne dépose que ce qu'on ne fera
pas maintenant.

Je suis le premier moteur d'entrée du registre : j'ouvrais un item par constat.
C'est cette règle, et non le débit de fermeture, qui ramène le rapport
arrivée/fermeture sous 1.
