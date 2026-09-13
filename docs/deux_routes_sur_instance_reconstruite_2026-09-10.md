# Les deux routes de `RM-2026-0071`, rendues sur l'instance reconstruite

Lot du 2026-09-10. L'action de l'item demandait de réabsorber dans une instance
fraîche, puis d'**ouvrir `/ag-contentieux` et `/comptes` dessus**. La
réabsorption existait — 858 pièces sources, instance vide — mais aucun document
ne montrait ces deux pages rendues, et c'est le reste sur lequel la revue
d'intégration a refusé de fermer.

Base : `test_reabsorption_complete_20260910`, lecture seule. Rendu par le client
de test sur les routes de production ; aucun serveur lancé, aucun port réservé.

## Ce que les deux pages rendent

| | `/ag-contentieux` | `/comptes` |
|---|---:|---:|
| Statut HTTP | **200** | **200** |
| Document rendu | 347 667 car. | 25 839 car. |
| Lignes de tableau | 775 | **6** |
| Liens | 34 | 45 |
| Formulaires | 2 | 3 |
| Panneaux | 7 | 4 |
| État vide déclaré | **aucun** | **`cs-empty-state`** |

**Les deux pages s'ouvrent et ne sont pas blanches.** C'est ce que l'item
demandait de vérifier.

## Le contraste est le vrai résultat

`/ag-contentieux` porte la matière : 775 lignes, sept assemblées nommées par
leur date, sept panneaux de section — questions AG, pièces de convocation,
dossiers contentieux, notes de risque, preuves et sources, pack de passation,
et les procès-verbaux déposés.

`/comptes` **déclare un état vide**. Ses quatorze titres de section existent —
catégories à contrôler, détail, pièces, questions au syndic, rapport AG — mais
six lignes de tableau seulement. La page n'est pas cassée : elle dit qu'elle n'a
pas de quoi remplir, ce qui est le comportement voulu du produit. Sur cette
instance, **la chaîne comptable n'a pas produit** ce que l'écran attend.

C'est un constat, pas une conclusion : rien ici ne dit *pourquoi*. La
réabsorption a porté sur les pièces sources ; savoir si le jeu comptable en fait
partie, ou si l'étape comptable n'a pas tourné, demande une mesure distincte.

## Ce que la page des assemblées dit maintenant du total

La conservation livrée le matin même est rendue sur cette instance :

> **68 de ces 354 résolutions portent un objet qui figure aussi sous une autre
> assemblée.** Le total ci-dessous les compte donc plusieurs fois.

Sept assemblées affichées, 354 résolutions au total, trois versions écartées et
nommées. Le total ne ment plus par omission.

**À noter, et c'est plus faible que la mesure de base** : la vue regroupe déjà
plusieurs lectures d'une même assemblée avant d'afficher, donc le partage
observé à l'écran — 68 — est inférieur à celui mesuré sur les actes bruts —
238 sur 550. Les deux chiffres sont justes : ils ne portent pas sur la même
population. Celui de l'écran porte sur ce que l'écran additionne, ce qui est
exactement ce qu'un lecteur doit pouvoir corriger dans sa tête.

## Une erreur de vérification, de moi

Mon premier contrôle a conclu que **la phrase de conservation ne s'affichait
pas**. Faux deux fois de suite : je cherchais `assemblee` sans accent là où le
gabarit écrit `assemblée`, puis un motif que la mise en forme du gabarit coupe.
La phrase est rendue, avec ses deux nombres.

C'est la sixième fois de la journée qu'une mesure exacte porte sur un autre
objet que celui dont j'allais conclure — et la première où j'ai failli déclarer
cassée une fonctionnalité qui marche.

## Ce que ce document ne prouve pas

- Il ne mesure aucune **justesse** : les nombres décrivent ce que le gabarit
  rend, pas ce que la copropriété doit. Une preuve de justesse demanderait un
  étalon établi à la main.
- Il ne dit pas pourquoi `/comptes` est vide sur cette instance.
- Aucune capture n'est jointe : le corpus est privé, et les dénombrements
  suffisent à établir que les pages s'ouvrent et portent leur structure.
