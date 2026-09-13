"""La source calculee unique de l'ecran de controle de gouvernance.

**Une seule source calculee, deux rendus, jamais deux calculs.** La synthese ne
compte rien: elle mesure la taille d'un filtre. Le nombre affiche par un constat
EST `len(appliquer_filtres(lignes, filtre))`, et le tableau affiche
`appliquer_filtres(lignes, le meme filtre)`. Il n'existe aucun second chemin de
calcul a faire diverger du premier.

Ce dispositif a attrape deux contradictions de compteurs pendant la conception,
dont une dans le code cense la rendre impossible. Il n'est pas affaibli ici.

**D'ou viennent les lignes.** De `v_matrice_gouvernance` et de `v_constats`,
c'est-a-dire du modele relationnel, jamais d'un comptage refait dans le
gabarit. Une ligne du tableau est un **acte d'autorisation**: resolution
d'assemblee, decision deleguee du conseil syndical, ou depense engagee en
urgence. Les constats qui portent sur une depense appartiennent a l'ecran
comptes - blueprint section 3.2 - et sont seulement denombres ici.

**Ce que ce module n'invente pas.** Quand une donnee que la maquette affichait
n'existe pas encore dans le modele, la cellule le dit. Le franchissement de
seuil n'est calcule nulle part - trou T9 du blueprint: la colonne l'ecrit, elle
ne le simule pas.
"""

from __future__ import annotations

from typing import Any, Iterable

from ..modules import actes_autorisation as A
from ..modules._actes_typologie import (
    CTRL_ANNEXE,
    CTRL_AVIS_CS,
    CTRL_DEVIS,
    CTRL_EXECUTION,
    CTRL_RAPPORT_CS,
    CTRL_SEUIL,
    controle_applicable,
    motif_hors_controle,
)
from ..modules._resolutions_assemblees import copies_concurrentes
from ._controle_gouvernance_cellules import (
    _execution,
    _nombre,
    _fonde,
    _montant,
    _seuil,
    _source_acte,
    _titre_acte,
)
from ._controle_gouvernance_vocabulaire import (
    CONCLUSIONS,
    CONSTATS_HORS_ECRAN,
    FORCE_VERS_STATUT,
    LIBELLES_CONSTAT,
    NATURES,
    ORDRE_STATUT,
    PORTEES,
    RESULTATS,
    STATUTS_BULLE,
    _bulle,
    _cellule,
    euros,
    pire_statut,
)


# --------------------------------------------------------------------------
# Construction des lignes
# --------------------------------------------------------------------------

#: Le tri: la gravite du constat, puis le montant en jeu. Le tableau ne tronque
#: rien, donc l'ordre est la seule chose qui met le grave devant.
GRAVITE = {
    "ACTE_SANS_FONDEMENT": 6,
    "URGENCE_JAMAIS_PORTEE": 6,
    "PLAFOND_DEPASSE": 5,
    "DELEGATION_EXPIREE": 5,
    "ISSUE_NON_ENONCEE": 5,
    "OBLIGATION_NON_TENUE": 4,
    "MONTANT_DIVERGENT": 4,
    "MAJORITE_NON_ENONCEE": 3,
    "ACTE_SANS_EXECUTION": 2,
    # Meme rang qu'`ACTE_SANS_EXECUTION`, et pour la meme raison: les deux
    # nomment un trou de l'outil, pas un manquement. Les mettre plus haut
    # ferait passer nos propres defauts de lecture devant les ruptures que les
    # pieces etablissent.
    "ISSUE_NON_LUE_A_RELIRE": 2,
}


def _rang_de_conclusion(trace: dict[str, Any]) -> tuple[str, str]:
    """De la plus ancienne a la plus recente, avec un ordre TOTAL.

    `constate_le` d'abord: c'est la seule donnee qui porte du sens.
    `trace_id` ensuite, et **uniquement pour rendre l'ordre total** - ce n'est
    pas une regle de choix. `trace_id` est un jeton aleatoire, donc a
    l'interieur d'une meme journee *laquelle est la derniere* reste
    indecidable a partir de ce qui est ecrit: `constate_le` a une granularite
    au JOUR. **Ce residu se declare au lieu d'etre masque par le tri.** Ce que
    le tri garantit est l'autre chose, celle qui manquait: la reponse ne
    depend plus de l'ordre dans lequel le magasin a rendu les lignes.
    """
    return (str(trace.get("constate_le") or ""),
            str(trace.get("trace_id") or ""))


def construire_lignes(
    matrice: list[dict[str, Any]],
    constats: list[dict[str, Any]],
    traces: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Une ligne par acte, six colonnes, les constats du modele rattaches."""
    # Les rangs de resolution occupes par plusieurs assemblees dont l'une au
    # moins n'a pas de date lue. Calcule sur la matrice ENTIERE, avant tout
    # filtre: un filtre qui masque la copie ne rend pas la copie inexistante,
    # et l'ecran doit dire la meme chose dans les deux cas.
    copies = copies_concurrentes(matrice)

    par_acte: dict[str, list[dict[str, Any]]] = {}
    for constat in constats:
        if constat.get("sujet_kind") != "acte":
            continue
        par_acte.setdefault(str(constat.get("sujet_id")), []).append(constat)

    # **Plusieurs conclusions portent sur le MEME acte - une trace ne s'ecrase
    # pas - et jusqu'au 2026-09-12 l'ecran en montrait une TIREE AU SORT.**
    # Le repli etait `conclusion_par_acte[acte] = verdict` dans une boucle:
    # le DERNIER itere gagnait. Or l'ordre de lecture est
    # `constate_le DESC, trace_id` (`_actes_schema.TRACE_ORDRE`), applique tel
    # quel en SQL. Deux consequences mesurees:
    #   - a dates differentes, `DESC` met le plus recent en tete, donc le
    #     dernier itere - le gagnant - etait le PLUS ANCIEN: l'ecran retenait
    #     la PREMIERE conclusion ecrite, l'inverse de ce qui etait annonce;
    #   - `_horodate()` rend une DATE, pas un instant. Deux conclusions du meme
    #     jour portent le meme `constate_le`, et le depart tombait sur
    #     `trace_id`, c'est-a-dire sur `secrets.token_hex(5)`. **Le verdict
    #     affiche etait tire au sort**, y compris dans le scenario du test qui
    #     pretendait figer ce comportement.
    #
    # La reparation est celle que `RM-2026-0134` a recue le meme jour: la
    # valeur est gardee, et TOUS LES CANDIDATS AVEC ELLE. Le tri rend la
    # reponse fonction de l'ENSEMBLE des traces et non de leur ordre de
    # lecture; le nombre et la liste des verdicts voyagent a cote, pour qu'on
    # puisse remonter de l'affichage aux etats.
    conclusions_par_acte: dict[str, list[dict[str, Any]]] = {}
    for trace in traces:
        if trace.get("sujet_kind") == "acte":
            conclusions_par_acte.setdefault(
                str(trace.get("sujet_id")), []).append(trace)
    for candidats in conclusions_par_acte.values():
        candidats.sort(key=_rang_de_conclusion)

    lignes: list[dict[str, Any]] = []
    for row in matrice:
        acte_id = str(row.get("acte_id") or "")
        portee = str(row.get("portee") or "ORDINAIRE")
        mes_constats = par_acte.get(acte_id, [])
        codes = {str(c.get("code")) for c in mes_constats}
        fonde = _fonde(row, portee)
        seuil = _seuil(row, portee)
        execution = _execution(row, portee)
        candidats = conclusions_par_acte.get(acte_id, [])
        conclusion = (str(candidats[-1].get("verdict") or "")
                      if candidats else "a_instruire")
        lignes.append({
            "id": acte_id,
            "nature": str(row.get("nature") or ""),
            "portee": portee,
            "resultat": str(row.get("resultat") or ""),
            "exercice": str(row.get("exercice") or ""),
            "objet": str(row.get("objet") or "").strip() or "Objet non lu sur la pièce",
            "titre": _titre_acte(row),
            "source": _source_acte(row),
            "date_effet": str(row.get("date_effet") or ""),
            "doc_id": str(row.get("doc_id") or ""),
            "entreprise": str(row.get("entreprise_effective") or ""),
            "montant": _montant(row),
            "montant_valeur": _nombre(row.get("montant_autorise")) or 0.0,
            "fonde": fonde,
            "seuil": seuil,
            "execution": execution,
            "constats": codes,
            "motifs": [str(c.get("motif") or "") for c in mes_constats],
            "conclusion": conclusion if conclusion in CONCLUSIONS else "a_instruire",
            # **De quoi remonter de l'affichage aux etats.** Sans ces deux
            # champs, deux conclusions de sens oppose - `QUESTION_POSEE` puis
            # `RESERVE` - produisent une cellule qui en montre UNE, et le
            # lecteur n'a aucun moyen de savoir qu'une autre existe: c'est le
            # test d'acceptation de `RM-2026-0160`, une TABLE reduite a un
            # SCALAIRE. Ce qui manque ne se voit pas, et c'est ce qui distingue
            # cette faute d'une simple imprecision.
            "conclusions_nombre": len(candidats),
            "conclusions_candidates": [str(c.get("verdict") or "")
                                       for c in candidats],
            # Lu sur la CELLULE de l'avis, pas sur le pire statut de toute la
            # colonne. Un constat dont le titre nomme l'avis du conseil syndical
            # doit filtrer l'avis du conseil syndical: sinon son titre ment sur
            # son filtre, et c'est exactement ce que le dispositif combat.
            "statut_avis": FORCE_VERS_STATUT.get(row["cel_avis_cs"], "manquante"),
            # **Une absence n'est un manquement que la ou un texte l'exige**
            # (`RM-2026-0164`). Ce champ dit si l'assemblee a arrete un montant
            # a partir duquel la consultation du conseil syndical devient
            # obligatoire pour cet acte. Il ne dit PAS que le montant le
            # franchit: la comparaison n'existe pas encore dans le modele, et
            # c'est le trou T9. Trois valeurs, jamais deux.
            "exigence_avis": _exigence_avis(row),
            "statut_fonde": pire_statut(fonde),
            "statut_seuil": pire_statut(seuil),
            "statut_execution": pire_statut(execution),
            "gravite": max((GRAVITE.get(c, 1) for c in codes), default=0),
            "rompu": bool(codes),
            # C054. Ce n'est ni un constat du modele ni une conclusion: c'est
            # une incertitude nommee. La ligne dit combien d'autres lignes de
            # l'ecran occupent le meme rang de resolution, et laquelle des
            # assemblees en cause n'a pas de date lue. Elle n'affirme jamais
            # que c'est le meme document - le produit n'en sait rien, et
            # l'affirmer serait la faute que ce lot combat.
            "copies": {
                "rang": _titre_acte(row),
                "total": len(copies[acte_id]) + 1,
                "sans_date": sum(
                    1 for c in copies[acte_id] if not c["date_lue"]
                ) + (0 if row.get("date_effet") else 1),
                "autres": copies[acte_id],
            } if acte_id in copies else None,
        })
    lignes.sort(key=lambda l: (-l["gravite"], -l["montant_valeur"], l["id"]))
    return lignes


#: Ce que l'on sait de l'exigence de consultation du conseil syndical sur une
#: ligne. **Trois valeurs, et la troisieme est celle qu'on oublie.**
#:
#: - `SEUIL_RATTACHE`: une assemblee a arrete un montant declencheur, rattache
#:   a cet acte. L'exigence peut naitre - elle nait si le montant le franchit,
#:   ce que le modele ne calcule pas encore (trou T9);
#: - `AUCUN_SEUIL`: aucun montant declencheur n'est rattache. **Aucun texte
#:   n'exige donc la piece ici**, et son absence n'est pas un manquement;
#: - `SANS_OBJET`: le controle est retire sur ce type d'acte, donc la question
#:   ne se pose pas.
EXIGENCE_SEUIL_RATTACHE = "SEUIL_RATTACHE"
EXIGENCE_AUCUN_SEUIL = "AUCUN_SEUIL"
EXIGENCE_SANS_OBJET = "SANS_OBJET"

EXIGENCES_AVIS = {
    EXIGENCE_SEUIL_RATTACHE: "Un seuil de consultation est rattaché",
    EXIGENCE_AUCUN_SEUIL: "Aucun seuil de consultation rattaché",
    EXIGENCE_SANS_OBJET: "Consultation sans objet sur ce type",
}


def _exigence_avis(row: dict[str, Any]) -> str:
    """L'exigence de consultation, telle que la base la porte - jamais deduite.

    **Mesure du 2026-09-10 qui donne sa raison d'etre a ce champ**, sur une
    instance reabsorbee a vide: la pastille `avis_manquant` compte 293 lignes,
    dont **219 portent un seuil de consultation rattache et 74 n'en portent
    AUCUN**. Sans ce partage, l'ecran melange 74 absences qu'aucun texte
    n'exige avec 219 dont l'exigence reste a etablir - et le lecteur ne peut pas
    savoir laquelle il regarde.
    """
    if str(row.get("cel_avis_cs") or "") == "NON_APPLICABLE":
        return EXIGENCE_SANS_OBJET
    try:
        rattaches = int(row.get("nb_seuil_consultation_cs") or 0)
    except (TypeError, ValueError):
        rattaches = 0
    return EXIGENCE_SEUIL_RATTACHE if rattaches >= 1 else EXIGENCE_AUCUN_SEUIL


# --------------------------------------------------------------------------
# LE predicat. Un seul, appele par les deux vues.
# --------------------------------------------------------------------------

#: Un champ filtrable declare la colonne reelle qu'il lit. Aucun operateur de
#: texte n'est atteignable ici, pas plus que dans `_actes_requetes`: on compare
#: une valeur declaree a une valeur declaree, jamais des mots dans une phrase.
CHAMPS_FILTRABLES: tuple[dict[str, Any], ...] = (
    {"cle": "nature", "label": "Nature de la décision", "options": NATURES,
     "lire": lambda l: l["nature"]},
    {"cle": "type", "label": "Type de résolution", "options": PORTEES,
     "lire": lambda l: l["portee"]},
    {"cle": "issue", "label": "Issue du vote", "options": RESULTATS,
     "lire": lambda l: l["resultat"]},
    {"cle": "seuil", "label": "Seuils franchis", "options": STATUTS_BULLE,
     "lire": lambda l: l["statut_seuil"]},
    {"cle": "fonde", "label": "Ce qui la fonde", "options": STATUTS_BULLE,
     "lire": lambda l: l["statut_fonde"]},
    {"cle": "execution", "label": "Exécution", "options": STATUTS_BULLE,
     "lire": lambda l: l["statut_execution"]},
    {"cle": "conclusion", "label": "Ma conclusion", "options": CONCLUSIONS,
     "lire": lambda l: l["conclusion"]},
    # Le seul champ multivalue: une ligne porte plusieurs constats a la fois, et
    # c'est justement ce qui fait que la somme des constats depasse le nombre de
    # lignes. Le predicat teste l'appartenance quand la lecture rend un
    # ensemble - une egalite sur une valeur declaree, toujours pas un balayage.
    {"cle": "avis", "label": "Avis du conseil syndical", "options": STATUTS_BULLE,
     "lire": lambda l: l["statut_avis"]},
    {"cle": "exigence_avis", "label": "Exigence de consultation",
     "options": EXIGENCES_AVIS, "lire": lambda l: l["exigence_avis"]},
    {"cle": "constat", "label": "Constat", "options": LIBELLES_CONSTAT,
     "lire": lambda l: l["constats"]},
)

CHAMP_PAR_CLE = {champ["cle"]: champ for champ in CHAMPS_FILTRABLES}

#: Les champs offerts a la barre de filtres. `constat` et `avis` en sont
#: absents: ils sont poses par les constats de la synthese, et la barre
#: porterait sinon deux chemins pour le meme filtre. Sept selecteurs, comme la
#: forme mesuree; en ajouter deux coute deux rangees de barre au premier ecran.
HORS_BARRE = ("constat", "avis", "exigence_avis")
CHAMPS_BARRE = tuple(c for c in CHAMPS_FILTRABLES if c["cle"] not in HORS_BARRE)


def appliquer_filtres(
    lignes: list[dict[str, Any]], filtres: dict[str, str]
) -> list[dict[str, Any]]:
    """LE predicat. La synthese en mesure la taille, le tableau en rend le
    contenu. Il n'y a pas de second chemin."""
    actifs = [
        cle for cle, valeur in (filtres or {}).items()
        if valeur and valeur != "toutes" and cle in CHAMP_PAR_CLE
    ]
    if not actifs:
        return list(lignes)
    resultat = []
    for ligne in lignes:
        garde = True
        for cle in actifs:
            lu = CHAMP_PAR_CLE[cle]["lire"](ligne)
            attendu = filtres[cle]
            if isinstance(lu, (set, frozenset)):
                if attendu not in lu:
                    garde = False
                    break
            elif lu != attendu:
                garde = False
                break
        if garde:
            resultat.append(ligne)
    return resultat


def libelle_filtres(filtres: dict[str, str]) -> list[dict[str, str]]:
    """Les filtres actifs, en toutes lettres, pour les puces retirables."""
    puces = []
    for cle, valeur in (filtres or {}).items():
        if not valeur or valeur == "toutes" or cle not in CHAMP_PAR_CLE:
            continue
        champ = CHAMP_PAR_CLE[cle]
        puces.append({
            "cle": cle,
            "label": champ["label"],
            "valeur": champ["options"].get(valeur, valeur),
        })
    return puces
