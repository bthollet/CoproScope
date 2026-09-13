# Les nombres de `RM-2026-0124`, refaits sur instance reconstruite

Lot du 2026-09-10.

`RM-2026-0124` déclarait ses propres chiffres à refaire : ils avaient été
comptés sur une base produite **avant** la correction `RM-2026-0154`, laquelle
a montré que la chaîne d'absorption écrasait 194 résolutions sur 400 en silence
et fabriquait une assemblée fantôme de 96 résolutions à partir d'une date lue
dans un nom de dossier de collecte.

Base employée ici : `test_reabsorption_complete_20260910` — instance **vide**
réabsorbant 858 pièces sources, lecture seule. Même règle de comptage que
l'original : *comptage dans le document rendu, donc indépendant de la justesse
des données*. Écran : `/controle-gouvernance?vue=tableau`, 2 428 984 caractères.

## Les nombres

| Grandeur | Annoncé (base amputée) | Refait (instance reconstruite) |
|---|---:|---:|
| Lignes du tableau | 363 | **551** |
| Éléments cliquables | 363 | **1 768** |
| Bulles | 2 179 | **3 662** |
| Citations | 605 | **1 162** |
| Citations qui nomment un document et une page **sans y mener** | 332 | **0** |
| Badges de conclusion à « À instruire » | 363 sur 363 | **550 sur 550** |

## Ce que la remesure change aux constats structurels

L'item déclarait les propriétés structurelles « valables sans remesure ». Deux
des quatre ne le sont plus.

**« 363 éléments cliquables tous dans une seule colonne » — faux aujourd'hui.**
Trois colonnes sur six portent des liens :

| Colonne | Lignes portant un élément interactif | Liens |
|---|---:|---:|
| 1. Décision | 550 | 550 |
| 2. Montant | **0** | **0** |
| 3. Ce qui la fonde | 542 | 614 |
| 4. Seuils franchis | 274 | 548 |
| 5. Exécution | **0** | **0** |
| 6. Ma conclusion | **0** | **0** |

**« Un seul lien par ligne » — faux.** Moyenne 3,11, répartie ainsi :

| Liens sur la ligne | Lignes |
|---:|---:|
| 0 | 1 |
| 1 | 8 |
| 2 | 251 |
| 3 | 17 |
| 4 | 219 |
| 5 | 55 |

**« 332 citations nomment un document et une page sans y mener » — corrigé.**
Zéro. Les 1 162 citations portent toutes un lien ; 443 nomment en plus une page.
C'est ce que `RM-2026-0158` avait pour objet.

**« Trois des quatre valeurs de `f_conclusion` inatteignables » — la moitié de
ce constat est fausse, et c'est moi qui l'ai écrite.** Le filtre offre
`a_instruire`, `QUESTION_POSEE`, `CONTROLE_TRACE` et `RESERVE`. La table
`traces_controle` porte **0 ligne**, et la colonne « Ma conclusion » ne porte
**aucun élément interactif sur aucune des 551 lignes** — cela, c'est exact.

J'en avais conclu que *rien sur cet écran ne permet d'en changer un*. **C'est
faux.** Le geste vit dans le panneau latéral « Ligne choisie », atteignable
depuis chacune des 550 lignes. Vérifié par la route de production : 550 liens de
sélection, le panneau s'ouvre, le formulaire y est, les trois verdicts sont
offerts, le bouton d'enregistrement aussi, et `POST
/controle-gouvernance/conclusion` écrit dans `traces_controle`. C'est le lot
**L1**, livré le 2026-09-09.

`traces_controle` est donc vide parce que **personne n'a encore conclu** sur
cette instance reconstruite, pas parce que le chemin manque. Ce qui reste un
défaut d'ergonomie : le geste demande un détour par le panneau, aucune des trois
colonnes mortes ne le porte en ligne.

**Le motif de l'erreur est celui des deux autres de la journée** : une mesure
exacte portant sur un autre objet que celui dont j'ai tiré la conclusion. Je
mesurais le gabarit de la colonne, et j'ai conclu sur le parcours.

## Ce qui reste mort, nommé précisément

Trois colonnes sur six ne répondent à rien : **Montant**, **Exécution**,
**Ma conclusion**. C'est le reliquat exact de ce que l'item dénonçait, réduit de
cinq colonnes à trois.

## Une erreur de comptage de moi, corrigée avant publication

Mon premier passage a compté **3 486 citations et 7 324 bulles**. C'était faux,
par un facteur exact : le document porte trois classes qui commencent par
`cs-citation` — `cs-citation`, `cs-citation-lien`, `cs-citation-reserve` — et
deux qui commencent par `cs-bulle`. Un motif `class="[^"]*cs-citation` les
compte toutes. Les bons nombres sont **1 162** et **3 662**.

C'est encore une mesure exacte portant sur autre chose que l'objet visé : le
compte des occurrences du *préfixe de classe* était juste ; ce n'était pas le
compte des citations.

## Réserves

- Mesure faite via le client de test, sur le document réellement rendu par la
  route de production ; aucun serveur n'a été lancé, donc aucun port réservé.
- Le corpus est privé : ce document ne porte aucun contenu, seulement des
  dénombrements.
- Les chiffres valent pour ce corpus. Ce qui vaut au-delà est la propriété
  structurelle — trois colonnes sans aucun élément interactif — parce qu'elle
  est une propriété du gabarit et non des pièces.
