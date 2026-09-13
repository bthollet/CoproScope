"""Lecture des totaux d'une annexe comptable reglementaire.

L'annexe est la piece que **les deux cabinets mesures produisent**. L'etat des
depenses, lui, n'existe que chez l'un des deux: c'est une modalite de cabinet,
pas un axe. C'est la raison pour laquelle ce lecteur existe a cote de celui de
l'etat des depenses, et non a sa place.

Le lecteur s'en tient aux **totaux que les textes nomment explicitement**: il
lit le numero, l'exercice, l'intitule, les exercices que les colonnes
comparent, et la ligne de total.

Ce module declarait que les modeles d'annexes 1 a 5 portent au Journal officiel
accessible par machine la mention `Annexe non reproduite`, et qu'en verifier la
structure irait au-dela de la source. **Limitation levee le 2026-09-12, `RM-2026-0094`.** Elle portait sur l'ACCES
et non sur l'existence de la source: trois voies numeriques l'ont confirmee
le 2026-09-06 - l'API rend `Annexe non reproduite`, la page du JO renvoie au
tableau papier, le PDF est refuse en 401 puis 403. **Brice a depose le fichier
officiel lui-meme** - `joe_20050318_0065_0007.pdf`, JO du 18 mars 2005, texte 7
sur 102, NOR `SOCU0412534D` - lu page par page, releve dans
`docs/annexes_comptables_decret_2005-240.md`. Les quatre egalites de controle
sont desormais executables dans `_comptes_egalites_annexes.py`.
**Ce qui n'est PAS leve:** les rubriques de ventilation des annexes 3 et 4 sont
*arretees en fonction des clauses du reglement de copropriete*. Elles ne sont
donc jamais universelles, et aucun controle ne doit les coder.

Ce lecteur ne lit toujours qu'un total par annexe, et c'est le residu nomme du
lot `RM-2026-0094`: l'annexe 2 en porte DEUX, operations courantes d'une part,
travaux de l'article 14-2 et operations exceptionnelles de l'autre. Les
egalites exigent le bloc NOMME et rendent `INDETERMINE` sans lui, plutot que de
comparer au hasard.

Axe des colonnes comparatives. Un cabinet en aligne cinq: exercice precedent
approuve, exercice clos budget vote, exercice clos realise, budget en cours,
budget a voter. Rien n'impose ce nombre, et le second cabinet mesure n'aligne
pas la meme chose. Le lecteur compte donc les colonnes au lieu de les supposer,
et rend la ligne de total **complete**: c'est a l'appelant de designer la
colonne qu'il veut, en la nommant.
"""

from __future__ import annotations

import re
from collections import Counter
from decimal import Decimal

from ._comptes_extraction_lexique import detecter_separateur_decimal, lire_montant
from ._comptes_extraction_roles import entetes_de_colonnes, roles_des_entetes
from ._comptes_extraction_modele import (
    SEPARATEUR_INDECIDABLE,
    STRUCTURE_DE_COLONNES_INCONNUE,
    TOTAL_AMBIGU,
    TOTAL_INTROUVABLE,
    AnnexeComptable,
    ColonneAnnexe,
    ConstatExtraction,
    ProfilTableau,
)

_NUMERO = re.compile(r"ANNEXE\s*N\s*[°ºo]?\s*(\d)", re.IGNORECASE)
_PERIODE = re.compile(r"du\s+(\d{2}/\d{2}/\d{4})\s+au\s+(\d{2}/\d{2}/\d{4})", re.IGNORECASE)
_AU = re.compile(r"\bau\s+(\d{2}/\d{2}/\d{4})", re.IGNORECASE)
_EXERCICE_NU = re.compile(r"^(19|20)\d{2}$")

# Intitules de total. Compares sans blanc, pour la meme raison que dans l'etat
# des depenses: l'espacement lettre a lettre est une mise en page, pas un sens.
_SANS_BLANC = re.compile(r"\s+")
#
# Familles d'intitules de total, par ordre de preference. L'ordre compte: la
# meme annexe peut porter plusieurs totaux, et prendre le dernier venu donnerait
# le total des travaux la ou l'article 10 du decret parle des charges pour
# operations courantes.
#
# `TOTAL I` designe la premiere section d'une annexe, celle des operations
# courantes; `TOTAL II` celle des travaux et operations exceptionnelles. Le
# chiffre romain est donc porteur de sens, pas de mise en page: c'est un axe.
# La comparaison etant faite sur la chaine compactee entiere, `TOTALI` ne peut
# pas attraper `TOTALII`.
_FAMILLES_DE_TOTAL = (
    ("TOTALCHARGESNETTES",),
    ("TOTALDESCHARGES",),
    ("TOTALI",),
    ("TOTALCHARGES",),
)
_TOTAUX = tuple(intitule for famille in _FAMILLES_DE_TOTAL for intitule in famille)

# Ce que chaque colonne sert, quand l'annexe le dit. L'usage est lu, pas
# suppose: une annexe qui ne l'ecrit pas laisse le champ vide.
_USAGES = {
    "POURAPPROBATIONDESCOMPTES": "approbation des comptes",
    "POURLEVOTEDUBUDGET": "vote du budget",
    "POURLEVOTEDUBUDGETPREVISIONNEL": "vote du budget",
}


def _compacte(brut: str) -> str:
    return _SANS_BLANC.sub("", brut).upper()


def lire_annexe(texte: str) -> AnnexeComptable:
    """Lit une annexe comptable au niveau de ses totaux."""
    lignes = texte.splitlines()
    separateur = detecter_separateur_decimal(lignes)
    if separateur is None:
        return AnnexeComptable(
            constats=(
                ConstatExtraction(
                    code=SEPARATEUR_INDECIDABLE,
                    message=(
                        "Le separateur decimal de l'annexe n'a pas pu etre etabli. "
                        "Aucun total n'est lu."
                    ),
                ),
            )
        )

    numero = ""
    intitule = ""
    debut = ""
    fin = ""
    exercices: list[str] = []
    usages: list[str] = []
    for brut in lignes:
        nu = brut.strip()
        if not numero:
            trouve = _NUMERO.search(nu)
            if trouve is not None:
                numero = trouve.group(1)
        if not debut:
            periode = _PERIODE.search(nu)
            if periode is not None:
                debut, fin = periode.group(1), periode.group(2)
                if not intitule:
                    intitule = _PERIODE.sub("", nu).strip(" ()")
            elif not fin:
                arrete = _AU.search(nu)
                if arrete is not None and "/" in arrete.group(1):
                    fin = arrete.group(1)
                    if not intitule:
                        intitule = _AU.sub("", nu).strip(" ()")
        usage = _USAGES.get(_compacte(nu))
        if usage is not None and usage not in usages:
            usages.append(usage)

    exercices = _exercices_compares(lignes)
    totaux, constats = _ligne_de_total(lignes, separateur, len(exercices))
    # Le ROLE de chaque colonne, lu dans les mots de son entete. Rendu vide
    # quand le bloc d'entetes ne se decoupe pas en autant de libelles que de
    # colonnes: une attribution partielle ne dirait pas ou passe la frontiere,
    # exactement comme pour `_usage_de`.
    entetes = entetes_de_colonnes(lignes)
    roles = roles_des_entetes(entetes) if len(entetes) == len(exercices) else []
    colonnes = tuple(
        ColonneAnnexe(
            exercice=exercice,
            intitule=entetes[index] if len(entetes) == len(exercices) else "",
            usage=_usage_de(index, usages, len(exercices)),
            role=roles[index] if roles else None,
        )
        for index, exercice in enumerate(exercices)
    )
    total, constat_structure = _total_elu(totaux, len(colonnes))
    constats = list(constats) + constat_structure
    return AnnexeComptable(
        numero=numero,
        exercice_debut=debut,
        exercice_fin=fin,
        intitule=re.sub(r"\s+", " ", intitule).strip(),
        colonnes=colonnes,
        total_charges=total,
        total_charges_par_colonne=tuple(totaux),
        profil=ProfilTableau(separateur_decimal=separateur),
        constats=tuple(constats),
    )


def _total_elu(totaux: list[Decimal], nombre_de_colonnes: int):
    """Le total de la derniere colonne, **ou rien, et alors on le dit**.

    **Le defaut `C037`, dans sa forme reellement mesuree.** Cette ligne
    s'ecrivait `totaux[-1] if totaux else None`. Mesure du 2026-09-10 sur les
    deux cabinets, 39 documents d'annexe: dans **16** d'entre eux, un total
    etait elu alors qu'**aucune colonne n'etait identifiee** - la derniere
    valeur d'une suite de 1, 2, 4 ou 8 nombres sans nom. Chez le second
    cabinet, c'etait le cas de TOUS les documents portant un total. Trois
    autres annoncaient dix colonnes pour cinq totaux.

    Le defaut n'est donc pas *on prend la mauvaise colonne*: c'est **on elit
    une valeur dans une liste dont on ignore la structure**, et le resultat est
    un chiffre d'apparence normale.

    **L'invariant pose:** un total n'est elu que lorsque la ligne de total porte
    exactement autant de nombres que l'entete annonce de colonnes. Sinon rien
    n'est elu, et un constat nomme les deux comptes. Une absence declaree se
    voit; un chiffre faux ne se voit pas.
    """
    if not totaux:
        return None, []
    if nombre_de_colonnes and len(totaux) == nombre_de_colonnes:
        return totaux[-1], []
    return None, [
        ConstatExtraction(
            code=STRUCTURE_DE_COLONNES_INCONNUE,
            message=(
                "La ligne de total porte %d nombre(s) et l'entete annonce %d "
                "colonne(s). Aucun total n'est elu: designer une colonne par sa "
                "position dans une liste dont la structure n'est pas etablie "
                "rendrait un chiffre d'apparence normale."
                % (len(totaux), nombre_de_colonnes)
            ),
        )
    ]


def _exercices_compares(lignes: list[str]) -> list[str]:
    """Millesimes des colonnes comparatives, dans l'ordre, doublons compris.

    Le nombre de colonnes est un axe: un cabinet en aligne cinq, dont deux
    portent le meme millesime, l'un pour le budget vote et l'autre pour le
    realise. Deduplicquer les perdrait, et perdre une colonne decale toute la
    lecture du total. Les millesimes sont donc pris tels quels.

    L'entete est repete a chaque page, et l'aplatissement colle parfois deux
    repetitions bout a bout. Prendre la plus longue suite donnerait alors le
    double du nombre de colonnes. Le module retient donc la longueur **la plus
    frequente** parmi les suites d'au moins deux millesimes: une repetition
    d'entete est par nature majoritaire, une concatenation accidentelle ne l'est
    pas.
    """
    suites: list[list[str]] = []
    courante: list[str] = []
    for brut in lignes:
        nu = brut.strip()
        if _EXERCICE_NU.match(nu):
            courante.append(nu)
            continue
        if len(courante) >= 2:
            suites.append(courante)
        courante = []
    if len(courante) >= 2:
        suites.append(courante)
    if not suites:
        return []
    longueurs = Counter(len(suite) for suite in suites)
    retenue = longueurs.most_common(1)[0][0]
    for suite in suites:
        if len(suite) == retenue:
            return suite
    return []


def _usage_de(index: int, usages: list[str], nombre: int) -> str:
    """Usage d'une colonne, quand l'annexe en annonce et seulement alors.

    Deux usages annonces sur cinq colonnes ne disent pas ou passe la frontiere.
    Le module ne l'invente pas: il n'attribue un usage que lorsqu'il y en a
    exactement autant que de colonnes.
    """
    if len(usages) != nombre:
        return ""
    return usages[index]


def _ligne_de_total(
    lignes: list[str],
    separateur: str,
    nombre_de_colonnes: int,
) -> tuple[list[Decimal], list[ConstatExtraction]]:
    """Les nombres de la ligne de total, du cote ou l'aplatissement les a mis.

    **Les deux dispositions existent, chez deux cabinets differents.** L'un
    imprime les valeurs avant l'intitule du total, l'autre apres. Le cote ne se
    devine donc pas: il se choisit sur le nombre de colonnes comparatives
    annonce par l'entete. Le cote qui en porte au moins autant gagne; quand les
    deux le peuvent, le module retient celui qui suit l'intitule et le dit.

    Hors des valeurs observees, c'est-a-dire quand l'entete n'annonce aucune
    colonne, le module prend le cote qui suit l'intitule s'il en porte, sinon
    l'autre, et ne pretend a aucune certitude.
    """
    for famille in _FAMILLES_DE_TOTAL:
        retenus, constats = _total_de_famille(lignes, separateur, nombre_de_colonnes, famille)
        if retenus or constats:
            return retenus, constats
    return [], []


def _total_de_famille(
    lignes: list[str],
    separateur: str,
    nombre_de_colonnes: int,
    famille: tuple[str, ...],
) -> tuple[list[Decimal], list[ConstatExtraction]]:
    """Cherche le total d'une seule famille d'intitules, en partant de la fin."""
    for index in range(len(lignes) - 1, -1, -1):
        if _compacte(lignes[index]) not in famille:
            continue
        avant = _nombres_contigus(lignes, index - 1, -1, separateur)
        apres = _nombres_contigus(lignes, index + 1, 1, separateur)
        if nombre_de_colonnes > 0:
            avant_possible = avant[-nombre_de_colonnes:] if len(avant) >= nombre_de_colonnes else []
            apres_possible = apres[:nombre_de_colonnes] if len(apres) >= nombre_de_colonnes else []
            if avant_possible and apres_possible:
                return apres_possible, [
                    ConstatExtraction(
                        code=TOTAL_AMBIGU,
                        message=(
                            "Les deux cotes de l'intitule de total portent autant "
                            "de nombres que l'entete annonce de colonnes. Le cote "
                            "qui suit l'intitule est retenu."
                        ),
                    )
                ]
            if avant_possible or apres_possible:
                return avant_possible or apres_possible, []
        retenus = apres or avant
        if retenus:
            return retenus, []
        return [], [
            ConstatExtraction(
                code=TOTAL_INTROUVABLE,
                message=(
                    "Un intitule de total a ete trouve, mais aucun nombre ne le "
                    "borde. Le total n'est pas lu."
                ),
            )
        ]
    return [], []


def _nombres_contigus(
    lignes: list[str],
    depart: int,
    pas: int,
    separateur: str,
) -> list[Decimal]:
    """Suite ininterrompue de nombres a partir de `depart`, dans l'ordre du texte."""
    trouves: list[Decimal] = []
    index = depart
    while 0 <= index < len(lignes):
        valeur = lire_montant(lignes[index].strip(), separateur)
        if valeur is None:
            break
        trouves.append(valeur)
        index += pas
    return list(reversed(trouves)) if pas < 0 else trouves


__all__ = ["lire_annexe"]
