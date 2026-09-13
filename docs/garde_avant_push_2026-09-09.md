<!-- Aucun nom reel, aucune adresse, aucun montant dans ce document. -->

# Regarder ce que `git push` enverrait

*2026-09-09. `RM-2026-0137`, lot 1. Outil : `tools/verifier_avant_push.py`.*

## Le défaut que cet outil répare

Le gouvernail le nommait lui-même, et personne ne l'avait traité parce que
l'item entier paraissait bloqué :

> La garde `prefixes_jamais_partager` gouverne le module de **publication**, pas
> `git push` ; **rien ne relie le second à la doctrine.**

Vérifié le 2026-09-09 : aucun fichier de `server/src`, `server/tests` ou
`tools/` ne mentionnait `git push`. Le même jour, une adresse postale réelle a
traversé le pseudonymat et s'est retrouvée dans un fichier suivi ; une autre est
publique depuis juin. **Aucun contrôle ne se déclenchait au moment où la donnée
part.**

## L'axe, et pourquoi il décide de toute la conception

Ce qui varie : quelle donnée, quel fichier, quelle branche, quel oubli.
Ce qui reste invariant : **ce que `git push` envoie est exactement ce que Git
suit.**

Le contrôle porte donc sur `git ls-files`, jamais sur un diff, une liste de
dossiers sensibles ou une convention de nommage. Un fichier nouveau, déplacé ou
renommé y entre tout seul. Un dossier « sensible » qu'on oublie de déclarer
n'existe pas comme catégorie, donc ne peut pas être oublié.

## Trois états, et non deux

| Code | Sens |
|---:|---|
| `0` | rien trouvé |
| `1` | quelque chose trouvé — ne pas pousser |
| `2` | **le contrôle n'a pas pu être fait** |

C'est la distinction qui porte l'outil. Les termes interdits ne peuvent pas
vivre dans le dépôt : écrire le nom réel d'une copropriété dans le fichier qui
interdit de l'écrire serait la première fuite. Ils vivent donc **hors dépôt**, et
ce fichier peut manquer — sur une autre machine, après un clone, dans la CI.

**Un contrôle qui se tait faute de matière est pire qu'aucun contrôle**, parce
qu'il laisse croire qu'il a regardé. D'où le troisième état.

L'outil **n'affiche jamais le terme cherché** : il rend un chemin, un numéro de
ligne et un compte. Un rapport de fuite qui recopie la fuite est une fuite.

## Emploi

```bash
python tools/verifier_avant_push.py
python tools/verifier_avant_push.py --ref origin/main
```

Le fichier des termes se donne par la variable `COPROSCOPE_NOMS_INTERDITS`, ou
se cherche à `../noms_interdits.txt` puis `../dev/noms_interdits.txt` — hors du
dépôt produit, donc jamais suivi. Un terme par ligne, `#` commente, la casse est
ignorée.

## Ce qu'il mesure aujourd'hui

| Cible | Fichiers portant le nom réel | Adresses postales |
|---|---:|---:|
| `origin/main` (**déjà public**) | **38** | **3** |
| Arbre suivi (ce qu'un push ajouterait) | 49 | **0** |

Les 49 se répartissent en **47 dans `docs/`** et deux fichiers hors `docs/` : le
garde-fou d'instance de `RM-2026-0152`, **où le nom est la règle**. Ces chiffres
confirment au fichier près la mesure indépendante du tri du backlog.

## Le brancher sur `git push` — à votre main

Le hook n'est **pas installé** : il changerait le comportement de vos `git push`
sans que vous l'ayez demandé. Pour l'installer :

```bash
printf '#!/bin/sh\nexec python tools/verifier_avant_push.py\n' > .git/hooks/pre-push && chmod +x .git/hooks/pre-push
```

Pour le retirer :

```bash
rm .git/hooks/pre-push
```

Un hook refuse le push quand l'outil rend `1` **ou `2`** — donc aussi quand le
fichier de termes manque. C'est voulu : sur une machine qui ne sait pas quoi
chercher, on ne pousse pas.

## Limites, nommées

- **Il ne détecte pas les patronymes.** Un nom de personne inconnu n'a aucune
  forme reconnaissable. Ce blocage est réel et il est déjà porté par
  `RM-2026-0065` et `RM-2026-0068`.
- **Il ne lit pas les binaires** : 327 fichiers de l'arbre suivi, dont les
  captures d'écran. Le lot 2 de `RM-2026-0137` les traite pièce par pièce.
- **Il ne dit rien de l'historique déjà poussé.** `--ref origin/main` mesure ce
  qui est public ; l'effacer demande une réécriture irréversible, qui n'est pas
  un geste d'outil.
- Une commune de moins de quatre lettres, ou écrite en minuscules, échappe à la
  règle d'adresse. Déclaré dans le code, avec la raison.
