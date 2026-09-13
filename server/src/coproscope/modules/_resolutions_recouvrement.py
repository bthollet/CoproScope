# -*- coding: utf-8 -*-
"""Un total qui somme des assemblees declare ce qu'il compte plusieurs fois.

**La tache que `RM-2026-0077` nomme, dans ses mots:** *annoter un rang ne
corrige pas un TOTAL. Tout compte qui somme des resolutions additionne encore
les deux copies. La reponse n'est pas d'elire ni de dedoublonner, c'est la
CONSERVATION: un total declare combien de ses lignes reposent sur un rang
marque concurrent, comme la voie des seuils declare son residu.*

**Pourquoi un second module, alors que `_resolutions_assemblees` existe deja.**
`copies_concurrentes` ne rend une entree que lorsque **au moins une des
assemblees n'a pas de date lue**. Cette condition etait juste sur le corpus qui
l'a fait naitre, ou les copies avaient toutes perdu leur date. Elle ne l'est
plus: le correctif de lecture de date du 2026-09-08 a rendu leur date aux
copies, et **la garde s'est tue en meme temps que le defaut redevenait
invisible**. Mesure du 2026-09-10 sur une instance VIDE reabsorbant 858 pieces
sources: sept paires d'assemblees partagent des objets, **six sont muettes pour
la garde existante**, dont une paire de 25 objets identiques dont les deux
assemblees sont datees.

C'est le motif que la doctrine du depot appelle une **modalite prise pour un
axe**: *la date manque* etait la forme que prenait l'indiscernabilite sur un
corpus donne, pas l'indiscernabilite elle-meme. Et le defaut a la forme la plus
couteuse qui soit: **ameliorer la lecture des dates a eteint la garde**, sans
faire echouer un seul test.

**L'axe retenu ici.** Ce qui VARIE, c'est la raison pour laquelle deux
assemblees portent le meme objet: un proces-verbal relu apres un nouvel OCR, un
recueil qui reprend plusieurs assemblees, une convocation et le proces-verbal
qui la suit, ou une resolution de pure forme qui revient a chaque exercice avec
le meme libelle. Ce qui reste INVARIANT quelle que soit la raison, c'est
qu'**un total qui somme les assemblees compte ces lignes plusieurs fois**.

La conservation porte donc sur cet invariant, et **sur rien d'autre**. Elle ne
dit pas *ce sont des doublons*: elle dit *voici combien de lignes de ce total
existent aussi ailleurs*. La question de savoir laquelle fait foi reste
ouverte, et c'est volontaire - le refus d'elire de `_resolutions_assemblees`
vaut ici mot pour mot.

**Hors des valeurs observees.** Un corpus sans recouvrement rend zero et
n'affirme rien. Un recouvrement partiel - une assemblee dont un tiers des
objets existe ailleurs - est rendu tel quel, comme un tiers, sans seuil qui le
ferait basculer d'un verdict a l'autre. Une assemblee entierement contenue dans
une autre est signalee comme telle parce que c'est une propriete exacte des
jeux, pas un franchissement de seuil.

**LE RESIDU, et il est central: cette mesure ne distingue pas un proces-verbal
relu d'une resolution recurrente.** Les deux produisent un objet partage, et
c'est assume: distinguer demanderait de conclure sur une ressemblance, ce que
le depot s'interdit depuis `C054`. Les elements structurels qui permettraient a
un humain de trancher - combien d'assemblees portent cet objet, et si les rangs
partages forment un bloc contigu - sont donc **rendus a cote du compte**, pour
qu'une lecture humaine puisse le faire. Le module ne le fait pas a sa place.

Mesure du 2026-09-10 qui montre que ce residu n'est pas theorique: sur ce
corpus, un bloc de 25 objets aux rangs 31 a 55 est presque surement le meme
proces-verbal relu, tandis que deux objets aux rangs 2 et 3, portes par trois
assemblees et longs de 29 caracteres en moyenne, sont presque surement des
resolutions de seance. **Presque surement n'est pas surement**, et cette
fonction ne tranchera ni l'un ni l'autre.
"""

from __future__ import annotations

from typing import Any, Iterable

from ._resolutions_assemblees import NATURE_RESOLUTION, date_lue

__all__ = [
    "assemblees_incluses",
    "conservation_du_total",
    "objet_partage",
    "recouvrements",
]


def _cle_objet(acte: dict[str, Any]) -> tuple[str, str, str]:
    """La coordonnee d'un objet DANS son assemblee, libelle compris.

    Le rang seul ne suffit pas: deux assemblees d'exercices differents ont
    chacune une resolution n° 7 sans rapport, et `_resolutions_assemblees` le
    dit deja. Le libelle est ce qui fait la difference entre *le meme rang* et
    *la meme matiere*.

    Le libelle est compare tel qu'il a ete lu, sans normalisation. C'est
    volontaire et c'est une borne: un OCR qui change une lettre produit deux
    objets distincts, donc cette mesure **sous-estime** le recouvrement. Une
    normalisation approximative ferait l'erreur inverse - rapprocher ce qui
    differe - et cette erreur-la fabrique un fait.
    """
    return (
        str(acte.get("numero") or "").strip(),
        str(acte.get("sous_numero") or "").strip(),
        str(acte.get("objet") or "").strip(),
    )


def _resolutions(actes: Iterable[dict[str, Any]]) -> list[dict[str, Any]]:
    return [a for a in actes if str(a.get("nature") or "") == NATURE_RESOLUTION]


def objet_partage(
    actes: Iterable[dict[str, Any]],
) -> dict[tuple[str, str, str], set[str]]:
    """Par objet, les assemblees qui le portent."""
    porteurs: dict[tuple[str, str, str], set[str]] = {}
    for acte in _resolutions(actes):
        ag = str(acte.get("ag_id") or "")
        if not ag:
            continue
        cle = _cle_objet(acte)
        if not cle[0] and not cle[2]:
            continue
        porteurs.setdefault(cle, set()).add(ag)
    return porteurs


def _jeux_par_assemblee(
    porteurs: dict[tuple[str, str, str], set[str]],
) -> dict[str, set[tuple[str, str, str]]]:
    jeux: dict[str, set[tuple[str, str, str]]] = {}
    for cle, assemblees in porteurs.items():
        for ag in assemblees:
            jeux.setdefault(ag, set()).add(cle)
    return jeux


def recouvrements(actes: Iterable[dict[str, Any]]) -> list[dict[str, Any]]:
    """Par paire d'assemblees, ce qu'elles ont en commun - sans verdict.

    Chaque entree porte de quoi lire le fait, et de quoi lire ce que le fait ne
    dit pas: le nombre d'objets communs, l'etendue des rangs partages, si ces
    rangs forment un bloc contigu, et combien de ces objets sont portes par plus
    de deux assemblees. Ce dernier compte est ce qui separe, a l'oeil d'un
    humain, une resolution de seance d'un proces-verbal relu.
    """
    porteurs = objet_partage(actes)
    jeux = _jeux_par_assemblee(porteurs)

    trouves: list[dict[str, Any]] = []
    noms = sorted(jeux)
    for rang_gauche, gauche in enumerate(noms):
        for droite in noms[rang_gauche + 1:]:
            commun = jeux[gauche] & jeux[droite]
            if not commun:
                continue
            rangs = sorted(int(c[0]) for c in commun if c[0].isdigit())
            trouves.append({
                "assemblees": [gauche, droite],
                "objets_communs": len(commun),
                "rang_min": rangs[0] if rangs else None,
                "rang_max": rangs[-1] if rangs else None,
                # Un bloc contigu de rangs partages est la trace d'un document
                # repris en entier; des rangs epars sont la trace d'objets qui
                # se ressemblent. Le fait est rendu, la conclusion ne l'est pas.
                "bloc_contigu": bool(rangs) and len(rangs) == rangs[-1] - rangs[0] + 1,
                # Porte par plus de deux assemblees: la marque d'une formalite
                # qui revient, et non d'une copie.
                "objets_portes_par_plus_de_deux": sum(
                    1 for c in commun if len(porteurs[c]) > 2),
                # Rendu pour memoire, jamais comme condition: c'est justement la
                # modalite sur laquelle la garde precedente s'etait calee.
                "dates_lues": [date_lue(gauche), date_lue(droite)],
            })
    trouves.sort(key=lambda r: (-r["objets_communs"], r["assemblees"]))
    return trouves


def assemblees_incluses(actes: Iterable[dict[str, Any]]) -> list[dict[str, Any]]:
    """Les assemblees dont TOUS les objets existent aussi sous une autre.

    Inclusion des jeux, pas un seuil. Une assemblee dans ce cas n'apporte
    aucune matiere propre au total: chacune de ses lignes y est deja comptee
    une premiere fois ailleurs.

    **L'inclusion est LARGE et non stricte, et ce detail decide du cas
    principal.** Avec une inclusion stricte, deux copies d'un meme
    proces-verbal - jeux d'objets EGAUX - ne seraient signalees ni l'une ni
    l'autre, chacune echouant a etre un sous-ensemble propre de l'autre. Or
    c'est exactement la situation que `RM-2026-0077` decrit depuis son
    ouverture. Une egalite est donc rendue des deux cotes: aucune des deux
    n'apporte de matiere que l'autre n'ait deja, et le lecteur voit la
    symetrie au lieu du silence.
    """
    jeux = _jeux_par_assemblee(objet_partage(actes))
    incluses: list[dict[str, Any]] = []
    for petite, jeu in sorted(jeux.items()):
        if not jeu:
            continue
        contenants = sorted(
            grande for grande, autre in jeux.items()
            if grande != petite and jeu <= autre)
        if contenants:
            incluses.append({
                "assemblee": petite,
                "objets": len(jeu),
                "contenue_dans": contenants,
            })
    return incluses


def conservation_du_total(actes: Iterable[dict[str, Any]]) -> dict[str, Any]:
    """Ce qu'un total doit declarer pour ne pas mentir par omission.

    Ne dit jamais *ce sont des doublons*. Dit: sur ce total, voici combien de
    lignes portent un objet qui existe aussi sous une autre assemblee, donc
    combien de lignes un compte par sommation aura vues plusieurs fois.
    """
    resolutions = _resolutions(actes)
    porteurs = objet_partage(actes)
    par_assemblee: dict[str, dict[str, int]] = {}
    partages = 0
    for acte in resolutions:
        ag = str(acte.get("ag_id") or "")
        entree = par_assemblee.setdefault(ag, {"actes": 0, "partages": 0})
        entree["actes"] += 1
        if len(porteurs.get(_cle_objet(acte), ())) > 1:
            entree["partages"] += 1
            partages += 1
    return {
        "actes": len(resolutions),
        "actes_partages": partages,
        "assemblees": len(par_assemblee),
        "assemblees_entierement_partagees": assemblees_incluses(actes),
        "recouvrements": recouvrements(actes),
        "par_assemblee": {ag: v for ag, v in sorted(par_assemblee.items())},
    }
