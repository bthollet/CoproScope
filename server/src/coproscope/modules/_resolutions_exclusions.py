# -*- coding: utf-8 -*-
"""Ce qu'une resolution ne peut PAS etre, meme quand on ignore ce qu'elle est.

Extrait de `_resolutions_qualification.py`, qui passait a 615 lignes en
accueillant ce bloc. Le decoupage suit l'objet mesure et non la taille: ce module
ne type rien. Il repond a une question differente de celle de la qualification -
non pas *qu'est-ce que cette decision est*, mais *qu'est-ce qu'elle ne peut pas
etre*. Les deux questions ont des reponses independantes, et c'est precisement
ce que `RM-2026-0116` a etabli.
"""
from __future__ import annotations

import re

#: Ce qui ferait d'une resolution un marche ou un contrat a passer. C'est la
#: seule chose que le seuil de l'article 21 alinea 2 mesure: *un montant des
#: marches et des contrats a partir duquel la consultation du conseil syndical
#: est rendue obligatoire*. Une resolution qui ne passe aucun marche ne peut pas
#: le depasser, quelle que soit la somme qu'elle mentionne.
ENGAGE_UN_MARCHE_RE = re.compile(
    r"(?i)\bmarch[ée]s?\b|\bcontrats?\b|\bdevis\b|\btravaux\b|\bprestat\w*"
    r"|\bentreprise\b|\bfournisseur\b|\bmise\s+en\s+concurrence\b"
)

#: Le fonctionnement de l'assemblee: elle arrete, elle quitte, elle elit, elle
#: se prononce sur des comptes deja executes. Aucun de ces actes ne passe un
#: marche.
FONCTIONNEMENT_ASSEMBLEE_RE = re.compile(
    r"(?i)\bquitus\b|approb\w*\s+des\s+comptes|arr[êe]t[ée]\s+des\s+comptes"
    r"|\b[ée]lection\b|d[ée]signation\s+des\s+membres|proc[èe]s-verbal\s+de\s+la\s+pr[ée]c[ée]dente"
)


def controles_exclus(segment: str) -> list[dict[str, str]]:
    """Ce que cette resolution ne peut PAS etre, meme quand on ignore ce qu'elle est.

    **Le defaut corrige, mesure le 2026-09-08.** `portee_resolution` exigeait,
    pour typer une approbation de comptes, que la periode visee soit lisible ET
    close. `periode_close` rend trois valeurs - vrai, faux, et `None` qui veut
    dire *je ne sais pas*. Le code traitait `None` comme faux, donc la
    resolution retombait sur `ORDINAIRE`, le seau generique. Mesure: le libelle
    *Approbation des comptes de l'exercice CLOS au 31 decembre 2024* rendait
    `ORDINAIRE`, tandis que le libelle vague *Approbation des comptes de
    l'exercice 2024* rendait `APPROBATION_COMPTES`. **Le libelle qui dit
    explicitement `exercice clos` etait celui qui echouait.**

    **L'intention du module etait juste et sa consequence ne l'etait pas.** Sa
    docstring dit: *une resolution non typee garde tous ses controles*. C'est de
    la prudence sur le TYPAGE - ne pas fabriquer un type - et c'etait bien vu.
    Mais << garder tous ses controles >> fait heriter un doute de contraintes
    qui ne le concernent pas. Brice l'a dit dans ces termes: *« il ne peut pas
    etre dans les marches. On ne peut pas dire que c'est au-dessus du seuil. Il
    faut le sortir, c'est a part. »*

    **L'axe, et il vaut au-dela de ce cas: la portee dit ce que la decision EST,
    une exclusion dit ce qu'elle N'EST PAS.** Ne pas savoir la premiere n'empeche
    pas de savoir la seconde. Cette fonction ne type rien et ne remplace pas
    `portee_resolution`: elle retire un controle dont on peut prouver qu'il ne
    s'applique pas.

    **Ce qui reste vrai le long de l'axe:** le seuil de l'article 21 al. 2 porte
    sur des marches et des contrats **a passer**. Une resolution qui n'en passe
    aucun ne peut pas le franchir - c'est une impossibilite de nature, pas une
    question de montant.

    **Hors des valeurs observees:** quand le texte ne permet pas de conclure,
    **aucune exclusion n'est rendue** et le controle reste. Se taire laisse un
    controle inutile, ce qui coute une verification; exclure a tort effacerait un
    controle du, ce qui coute une fuite. Le defaut penche donc du bon cote.
    """
    exclusions: list[dict[str, str]] = []
    if FONCTIONNEMENT_ASSEMBLEE_RE.search(segment) and not ENGAGE_UN_MARCHE_RE.search(segment):
        exclusions.append({
            "controle": "SEUIL",
            "motif": (
                "Cette resolution porte sur le fonctionnement de l'assemblee - comptes deja "
                "executes, quitus, election - et ne passe aucun marche ni contrat. Le seuil de "
                "l'article 21 alinea 2 mesure des marches et des contrats a passer: il ne peut "
                "pas etre franchi ici."
            ),
            "fondement": "loi 65-557, article 21 alinea 2",
        })
    return exclusions
