# L'arbre suivi ne porte plus de nom de copropriété

Lot du 2026-09-10, rattaché à `RM-2026-0137`.

## En une phrase

`tools/verifier_avant_push.py` sortait en **1** depuis sa création — donc le
crochet `pre-push` **refusait tout push**, et le dépôt était bloqué en écriture
sans que le gouvernail le dise. Il sort maintenant en **0**.

## La mesure avant

| Grandeur | Valeur |
|---|---:|
| Fichiers suivis | 1 701 |
| Fichiers lus (non binaires) | 1 374 |
| Fichiers portant le terme | 38 |
| Occurrences | 286 |
| dont en documentation | 278 |
| dont en code | 8 |
| Noms de fichiers portant le terme | 2 |

## Ce que la mesure des voisinages a changé dans la réponse

Le réflexe aurait été de remplacer un nom par une périphrase. La mesure des
caractères immédiatement voisins dit autre chose :

| Voisin de droite | Occurrences |
|---|---:|
| `_` | 206 |
| `-` | 37 |
| `.` | 23 |
| autre (backtick, espace, `/`) | 20 |
| **une lettre** | **0** |

Le terme n'est **jamais** collé à une lettre : ce n'est pas un mot de prose,
c'est un **jeton d'identifiant**, presque toujours préfixe d'un nom de dossier
ou de fichier. La substitution s'est donc décidée sur le voisinage et non sur
une liste de fichiers :

- voisin identifiant ou chemin → `tilleul_pseudo`, la forme déjà en place sur
  le poste avec `instances/tilleul_pseudo_mere` ;
- mot d'une phrase → `Tilleuls (pseudo)`, mention comprise.

Résultat : **278 en forme d'identifiant, 0 en forme de phrase** — exactement ce
que la mesure annonçait. Une liste de fichiers écrite à la main aurait produit
le même nombre par hasard, sans jamais dire pourquoi.

## Les 8 occurrences en code étaient un piège

Elles vivent dans `tools/reconstruction_protocol.py` et son test. Là, **le nom
EST le critère de la garde** : le code refuse explicitement une ancienne
instance nommée en clair.

Un remplacement aveugle aurait **vidé cette garde sans faire échouer un seul
test**.

**Vérification faite avant de toucher quoi que ce soit.** La condition générale
qui suit refuse déjà tout dossier dont le parent n'est pas l'instance attendue :

```python
if instance.name.lower() != "instance" or instance.parent.name != attendue:
    raise ProtocolError(...)
```

L'ancienne instance était donc refusée **deux fois**, et la ligne nommée ne
changeait que le libellé du message. Ce qui disparaît est un message ; ce qui
reste est le refus.

**Le nom attendu sort du dépôt** vers `COPROSCOPE_INSTANCE_RECONSTRUCTION`,
pour la raison que `verifier_avant_push` donne déjà pour les termes interdits :
écrire le nom réel dans le fichier censé le protéger serait la première fuite.

**Sans configuration, l'outil refuse au lieu de laisser passer.** Trois états et
non deux — trouvé, absent, *pas configuré* — et le troisième n'est jamais un feu
vert. Une valeur par défaut ferait qu'un poste mal configuré validerait le
premier dossier venu, ce qui est le contraire d'un garde-fou.

Le test ne porte plus aucun nom réel : il emploie un nom de fixture et vérifie
le refus sur ce qui le fonde vraiment — un dossier dont le parent n'est pas
l'instance déclarée est refusé, **quel que soit son nom**.

## Preuve que la garde mord après le changement

| Ligne cassée | Verdict |
|---|---|
| le refus d'une instance non déclarée disparaît | 3 échecs |
| l'outil non configuré ne refuse plus | 1 échec |

## Les deux noms de fichiers

Renommés par `git mv`. Les liens qui les citaient avaient déjà été réécrits par
la substitution de contenu, et ils résolvent : **zéro lien mort dans l'arbre
suivi**.

## Ce qui reste, et cela demande un arbitrage

**L'arbre suivi est net. L'historique ne l'est pas.** Le terme reste dans les
commits déjà poussés sur GitHub. Le nettoyer demande une réécriture d'historique
et un push forcé sur un dépôt public : c'est une décision de Brice, pas d'un lot.

Second reliquat, mineur : les autres worktrees locaux portent encore le terme
sur leurs propres branches. Le crochet `pre-push` les attrapera au moment où
elles voudront partir — c'est précisément ce pour quoi il porte sur
`git ls-files` et non sur un diff.

## Ce que ce lot ne fait pas

- Il ne réécrit aucun historique.
- Il ne juge pas du sort de `tools/reconstruction_protocol.py`, qui reste sous
  arbitrage (`RM-2026-0152`) ; il retire seulement la donnée personnelle qu'il
  portait.
- Il n'ajoute pas de test qui ferait tourner le contrôle sur l'arbre réel : ce
  contrôle a besoin du fichier local des termes interdits, absent en
  intégration continue, et un test qui se saute est un test qui se tait.
  Le crochet `pre-push` est le bon endroit, et il existe.
