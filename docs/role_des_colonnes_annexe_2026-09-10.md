# Une colonne d'annexe se désigne par son rôle, jamais par sa position

Lot du 2026-09-10, constat `C037` de `RM-2026-0086`.

## Ce que le constat disait, et pourquoi il fallait le remesurer

> le total des charges d'une annexe est pris dans la dernière colonne, donc
> souvent un budget à venir au lieu du réalisé de l'exercice

L'instruction du 2026-09-10 avait déjà montré que la conclusion ne suivait pas :
le seul consommateur de ce champ **veut** un budget, donc remplacer la valeur
par le réalisé casserait l'appelant au lieu de le réparer.

## Ce que la mesure sur les deux cabinets a trouvé à la place

39 documents d'annexe — 36 chez le premier cabinet, 3 chez le second.

| Forme | Documents | `total_charges` élu avant ce lot |
|---|---:|---|
| 5 colonnes, 5 totaux | 8 | oui, légitimement |
| **0 colonne**, 1 total | 7 | **oui** |
| **0 colonne**, 2 totaux | 5 + 2 (cabinet B) | **oui** |
| **0 colonne**, 4 totaux | 1 | **oui** |
| **0 colonne**, 8 totaux | 1 | **oui** |
| 10 colonnes, 5 totaux | 3 | **oui** |
| 0 colonne, 0 total | 10 + 1 | non |
| 3 colonnes, 0 total | 1 | non |

**19 documents élisaient un total dans une liste dont la structure était
inconnue.** Chez le second cabinet, c'était le cas de **tous** les documents
portant un total.

Le défaut n'est donc pas *on prend la mauvaise colonne*. C'est **on élit une
valeur dans une liste dont on ignore la structure**, et le résultat a
l'apparence d'un chiffre normal.

## Une affirmation du gouvernail est réfutée

Il était écrit que `_USAGES` ne connaît « que deux libellés compactés
qu'**aucun des deux cabinets mesurés n'écrit** ».

C'est faux :

| Clé | Cabinet A | Cabinet B |
|---|---:|---:|
| `POURAPPROBATIONDESCOMPTES` | 70 | 30 |
| `POURLEVOTEDUBUDGET` | 70 | 10 |

Ce qui est vrai, c'est qu'**aucun usage n'est jamais attribué** : `_usage_de`
n'attribue que s'il y a exactement autant d'usages annoncés que de colonnes, et
deux usages sur cinq colonnes ne disent pas où passe la frontière. **Le refus
est fondé. Sa conséquence ne l'était pas** : le module refusait de nommer les
colonnes, puis en élisait une par sa position.

La fixture du dépôt, elle, ne porte **aucune annexe** — 0 document sur 18. Cette
partie de l'affirmation était juste.

## L'axe

**Ce qui varie** : la formulation et la mise en page. `Exercice clos réalisé à
approuver`, `Exercice clos réalisé`, un renvoi `(N)`, un `N + 2` sur sa propre
ligne, un libellé coupé en trois par le retour à la ligne.

**Ce qui reste invariant** : un en-tête de colonne situe la colonne sur **deux
dimensions indépendantes**.

1. **La nature** — un montant *constaté* (`réalisé`) ou *prévu* (`budget`,
   `prévisionnel`).
2. **Le statut** — déjà *arrêté* (`approuvé`, `voté`) ou *soumis* maintenant
   (`à approuver`, `à voter`, `proposé`).

Les quatre combinaisons existent et se rencontrent. C'est pourquoi ce sont deux
axes et non une liste de cinq libellés : **une énumération de cinq casse au
sixième ; deux axes binaires rendent `inconnu` sur la dimension qu'ils n'ont pas
lue.**

Un point d'ordre qui n'est pas cosmétique : `à approuver` **contient**
`approuver`, et `budget voté` contient `voté`. Les marques du soumis sont donc
cherchées d'abord — se tromper ici transforme un montant soumis au vote de ce
soir en un montant déjà acquis.

## Un repère d'exercice a deux formes et un seul axe

Le premier cabinet écrit le millésime (`2029`). Le second écrit le repère
**relatif** du modèle réglementaire (`N`, `N + 1`, `N + 2`, `N - 1`).

Mesure : un localisateur limité aux millésimes trouvait **zéro bloc d'en-tête**
chez le second cabinet ; **vingt-huit** une fois les repères relatifs admis.
Coder la seule forme vue chez le premier cabinet aurait rendu ce lecteur aveugle
à tout un cabinet.

## Ce que le lot livre

- **Le refus d'élire.** Un total n'est élu que si la ligne de total porte
  exactement autant de nombres que l'en-tête annonce de colonnes. Sinon, aucun
  total, et un constat `STRUCTURE_DE_COLONNES_INCONNUE` nomme les deux comptes.
- **Le rôle sur la colonne.** `ColonneAnnexe.role` porte les deux axes quand le
  bloc d'en-têtes se découpe en autant de libellés que de colonnes ; `None`
  sinon.
- **`colonne_du_role(colonnes, nature, statut)`** répond à une demande **nommée**
  — ce que le docstring du lecteur promettait déjà et que `totaux[-1]`
  contredisait dans le même fichier.

## Effet mesuré du correctif

| | Avant | Après |
|---|---|---|
| Documents élisant un total sans structure connue | 19 | **0** |
| Documents déclarant le refus | 0 | **19** |
| Documents portant des rôles de colonnes complets | 0 | 8 (4 rôles chacun) |

Le cinquième rôle de ces huit documents reste incomplet : `Exercice précédent
approuvé` ne dit pas s'il s'agit d'un réalisé. Le module le déclare au lieu de
le ranger d'office.

## Preuve que la garde mord

| Ligne cassée | Verdict |
|---|---|
| le total redevient élu par position, structure inconnue comprise | 2 échecs |
| le `SOUMIS` ne l'emporte plus : un montant à voter passe pour acquis | 9 échecs |
| le découpage n'exige plus autant d'en-têtes que de colonnes | 1 échec |
| le repère relatif `N+2` n'est plus reconnu | 1 échec |
| deux colonnes de même rôle sont départagées par position | 1 échec |

## Limites déclarées

- **Le localisateur d'en-têtes n'est pas prouvé sur les deux cabinets.** Il est
  concordant sur 52 blocs du premier cabinet et sur les textes de test ; sur le
  second, il localise bien 28 blocs de 5 colonnes mais le découpage n'y rend pas
  5 en-têtes. Le second cabinet obtient donc **aucun rôle** — le comportement
  voulu, mais pas une preuve de justesse.
- Le refus d'élire, lui, **est** prouvé sur les deux : il s'y déclenche 17 fois
  et 2 fois.
- Rien ne change pour la colonne qui alimente le budget prévisionnel quand la
  structure est connue : c'est toujours la dernière, et elle porte désormais un
  rôle lisible qui permettra à un appelant de la désigner autrement.
- La fixture du dépôt ne porte aucune annexe : les tests de ce lot construisent
  leurs propres textes, et ne dépendent d'aucune instance.
