# Un total qui somme des assemblées déclare ce qu'il compte deux fois

Lot du 2026-09-10, rattaché à `RM-2026-0077`.
Corpus : instance **vide** `test_reabsorption_complete_20260910`, reconstruite
par réabsorption de 858 pièces sources depuis le `raw/` de l'instance mère,
registres et coffre vidés avant la chaîne. Lecture seule.

## En une phrase

Une garde existait pour signaler qu'une même assemblée était comptée deux fois.
**Améliorer la lecture des dates l'a éteinte** — sans faire échouer un seul
test. La conservation ajoutée ici ne dépend plus de la date, et déclare ce que
tout total obtenu par sommation compte plusieurs fois.

## Le fait

`_resolutions_assemblees.copies_concurrentes` ne rend une entrée que si
**au moins une des assemblées n'a pas de date lue**. C'était vrai sur le corpus
qui l'a fait naître : les copies y avaient toutes perdu leur date.

Le correctif de lecture de date du 2026-09-08 a rendu leur date à ces copies.
La duplication, elle, est restée. Résultat mesuré sur la base fraîche :

| Paire d'assemblées | Objets identiques | Rangs | Bloc contigu | Vue par la garde existante |
|---|---:|---|---|---|
| A × B | 49 | 11–46 | non | **non** |
| C × D | 25 | 31–55 | oui | **non** |
| C × E | 23 | 8–30 | oui | oui |
| F × G | 17 | 2–26 | non | **non** |
| H × C | 4 | 1–4 | oui | **non** |
| F × I | 2 | 2–3 | oui | **non** |
| G × I | 2 | 2–3 | oui | **non** |

**Six paires sur sept étaient muettes.** Les identifiants sont remplacés par des
lettres ici ; ils figurent dans la mesure locale, pas dans un document du dépôt.

Au total : **238 actes sur 550** portent un objet qui existe aussi sous une
autre assemblée, et **deux assemblées n'apportent aucun objet qui leur soit
propre** — leurs 25 et 23 objets sont entièrement contenus dans une troisième
qui en porte 55.

Cette troisième assemblée est la concaténation exacte de trois autres, en blocs
de rangs contigus : rangs 1–4, 8–30, 31–55. Un seul document y apporte 48 des
55 objets.

## L'axe, l'invariant, et ce que le code en fait

**Ce qui varie** — la raison pour laquelle deux assemblées portent le même
objet : un procès-verbal relu après un nouvel OCR, un recueil qui reprend
plusieurs assemblées, une convocation et le procès-verbal qui la suit, une
résolution de pure forme qui revient chaque exercice avec le même libellé.

**Ce qui reste invariant le long de cet axe** — quelle que soit la raison,
**un total qui somme les assemblées compte ces lignes plusieurs fois**.

**Ce que le code en fait** — il énonce cet invariant et rien d'autre. Il ne dit
jamais *ce sont des doublons*, il dit *voici combien de lignes de ce total
existent aussi ailleurs*. Le refus d'élire une copie qui fait foi, posé en
`C054`, vaut ici mot pour mot : la mesure d'origine avait montré que le choix
par défaut aurait été le mauvais.

**Hors des valeurs observées** — un corpus sans recouvrement rend zéro et
n'affirme rien. Un recouvrement partiel est rendu comme une proportion, sans
seuil qui le ferait basculer d'un verdict à l'autre. Une assemblée entièrement
contenue dans une autre est signalée parce que c'est une propriété exacte des
jeux, pas un franchissement.

## Le résidu, nommé

**Cette mesure ne distingue pas un procès-verbal relu d'une résolution
récurrente.** Les deux produisent un objet partagé. Distinguer demanderait de
conclure sur une ressemblance, ce que le dépôt s'interdit.

Les éléments qui permettraient à un humain de trancher sont donc rendus à côté
du compte, sans être interprétés : combien d'assemblées portent cet objet, et
si les rangs partagés forment un bloc contigu. Sur ce corpus, un bloc de
25 objets aux rangs 31–55 est presque sûrement le même procès-verbal relu, et
deux objets aux rangs 2–3 portés par trois assemblées sont presque sûrement des
résolutions de séance. **Presque sûrement n'est pas sûrement**, et la fonction
ne tranche ni l'un ni l'autre.

Seconde borne : les libellés sont comparés tels qu'ils ont été lus, sans
normalisation. Un OCR qui change une lettre produit deux objets distincts, donc
cette mesure **sous-estime** le recouvrement. L'erreur inverse — rapprocher ce
qui diffère — fabriquerait un fait, ce qui est plus coûteux.

## Ce que le journal dit maintenant

```
238 actes sur 550 portent un objet qui existe aussi sous une autre assemblee:
un total obtenu par sommation les compte plusieurs fois, et 2 assemblees
n'apportent aucun objet qui leur soit propre
```

## Preuve que la garde mord

Quatre mutations appliquées pour de vrai au code protégé, chacune rejouée puis
annulée :

| Ligne cassée | Verdict |
|---|---|
| le seuil de partage passe de *plus d'une assemblée* à *plus de deux* | 4 échecs, 4 erreurs |
| l'inclusion redevient stricte, donc deux copies **égales** passent | 2 échecs |
| la clé d'objet perd le libellé : le rang seul redevient la matière | 7 échecs |
| le motif n'est plus publié | 1 échec, 4 erreurs |

Le témoin de santé de l'instrument est écrit dans le test : deux assemblées
sans objet commun doivent produire **zéro** et **aucun motif**. Une garde qui ne
sait pas se taire ne mesure rien.

## Ce que ce lot ne fait pas

- Il ne déduplique pas et n'élit aucune copie.
- Il ne remplace pas `copies_concurrentes`, qui reste juste sur son propre axe :
  une assemblée sans date lue est indiscernable de toute autre au même rang.
- Il ne remesure pas les dénombrements globaux du produit. Les écrans qui
  somment des assemblées devront lire `actes_partages` ; ce câblage n'est pas
  fait ici.
- Il ne dit pas laquelle des deux assemblées entièrement partagées devrait
  disparaître, ni si l'une devrait disparaître.

## Réserves

La mesure porte sur une instance reconstruite le 2026-09-10 par réabsorption
complète. Les tests du dépôt, eux, s'appuient sur des témoins écrits à la main :
la CI n'a pas le droit de lire une instance privée. Une preuve obtenue sur
`examples/synthetic_copro` vaudrait pour la non-régression, jamais pour la
justesse.
