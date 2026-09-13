"""De quoi une extraction de convocation se refute elle-meme.

Une extraction qui ne fournit rien contre quoi se verifier est plausible, jamais
refutable. Quatre formes, selon ce que la source donne - et la quatrieme n'est
pas de meme nature que les trois autres:

    enumeration annoncee   l'ordre du jour promet N points
    sequence               la numerotation et ses trous
    total affiche          une resolution annonce le total d'une annexe
    reference qui resout   une promesse de la source, verifiee en la suivant

Les trois premieres mesurent la qualite de NOTRE lecture. La quatrieme suit une
promesse de la SOURCE, donc elle produit un constat opposable a celui qui l'a
faite, pas un signal de qualite.

Aucune ne demande d'etalon manuel. C'est ce qui manque a `agscope`, qui compte
des `resolution_count` sans rien contre quoi les verifier.
"""

from __future__ import annotations

from ._convocation_extraction import Convocation
from ._convocation_motifs import PRIX_NON_LU, PRIX_QUANTIFIE


def enumeration(convocation: Convocation) -> dict[str, object]:
    """L'ordre du jour promet N sous-points, la lecture en rend combien.

    `controle_effectif` dit si la comparaison a un sens. Quand la frontiere
    entre l'ordre du jour et les projets n'a pas ete trouvee, les memes lignes
    sont comptees des deux cotes: le controle rend alors `complete` quoi qu'il
    arrive. Un controle qui ne peut pas echouer ne prouve rien, et le taire
    serait pire que de ne pas l'avoir.
    """
    annonces = {p.reference for p in convocation.points if p.sous_numero}
    lus = {d.reference for d in convocation.devis}
    return {
        "sous_points_annonces": len(annonces),
        "sous_points_lus": len(lus),
        "annonces_non_lus": sorted(annonces - lus),
        "lus_non_annonces": sorted(lus - annonces),
        "controle_effectif": convocation.projets_delimites,
        "complete": annonces == lus,
    }


def sequence(convocation: Convocation) -> dict[str, object]:
    """Un trou dans la numerotation est un point qu'on n'a pas vu, ou retire."""
    numeros = sorted({p.numero for p in convocation.points if not p.sous_numero})
    if not numeros:
        return {"premier": 0, "dernier": 0, "trous": [], "complete": False}
    trous = [n for n in range(numeros[0], numeros[-1] + 1) if n not in numeros]
    return {
        "premier": numeros[0],
        "dernier": numeros[-1],
        "trous": trous,
        "complete": not trous,
    }


def quantification(convocation: Convocation) -> dict[str, object]:
    """Combien de devis nomment un montant, combien n'en nomment aucun.

    Un devis retenu sans prix global n'est pas une lecture ratee: c'est une
    assemblee qui vote sans montant. Le distinguer du defaut d'extraction est
    tout l'interet de la mesure.
    """
    total = len(convocation.devis)
    quantifies = [d for d in convocation.devis if d.etat_prix == PRIX_QUANTIFIE]
    non_lus = [d for d in convocation.devis if d.etat_prix == PRIX_NON_LU]
    return {
        "devis_cites": total,
        "quantifies": len(quantifies),
        "non_quantifies": total - len(quantifies) - len(non_lus),
        "non_lus": len(non_lus),
        "references_non_lues": sorted(d.reference for d in non_lus),
        # L'intitule annonce, le corps decide. Un ecart entre les deux n'est pas
        # un defaut de lecture: c'est une resolution qui ne dit pas la meme chose
        # selon l'endroit ou on la lit, et le constat vaut d'etre nomme.
        "discordances_intitule_corps": sorted(
            d.reference for d in convocation.devis if d.discordance_intitule_corps
        ),
        "taux_quantification": round(len(quantifies) / total, 3) if total else 0.0,
    }


def affirmations_sans_piece(convocation: Convocation) -> dict[str, object]:
    """Ce que la convocation affirme d'elle-meme, et avec quelle variance.

    Une formule repetee a l'identique sur soixante-quatre projets n'est pas la
    trace de soixante-quatre consultations: c'est la signature d'un gabarit. Un
    processus reel produit de la variation. La variance mesuree vaut donc mieux
    que le seul comptage, et elle est adressable au syndic.

    Ces affirmations emanent du syndic, dans un document qu'il redige: il atteste
    de sa propre conformite a une obligation qui le lie. Elles ne valent jamais
    preuve et ne franchissent pas la frontiere vers une sortie destinee a un
    tiers.
    """
    lus = [d for d in convocation.devis if d.etat_prix != PRIX_NON_LU]
    return {
        "projets_lus": len(lus),
        "avis_cs_affirme": sum(1 for d in lus if d.avis_cs_affirme),
        "analyse_offres_affirmee": sum(1 for d in lus if d.analyse_offres_affirmee),
        "piece_produite": 0,
    }


def references_a_resoudre(convocation: Convocation) -> dict[str, object]:
    """Les promesses de la source, listees pour etre suivies.

    On ne les resout pas ici: la resolution demande l'autre assemblee et le
    dossier d'annexes. On les expose, nommees, pour que le controle les suive.
    """
    contestees: list[str] = []
    ag_visees: set[str] = set()
    for declaration in convocation.declarations:
        if declaration.ag_visee:
            ag_visees.add(declaration.ag_visee)
        contestees.extend(declaration.questions_visees)
    return {
        "ag_visees": sorted(ag_visees),
        "questions_visees": sorted(dict.fromkeys(contestees)),
        "annexes_citees": list(convocation.annexes_citees),
        "totaux_a_verifier": [
            {"annexe": t.annexe, "montant": t.montant, "page": t.page}
            for t in convocation.totaux_annonces
        ],
    }


def controles(convocation: Convocation) -> dict[str, object]:
    """Tous les controles, dans un seul resume verifiable."""
    resume = {
        "enumeration": enumeration(convocation),
        "sequence": sequence(convocation),
        "quantification": quantification(convocation),
        "affirmations": affirmations_sans_piece(convocation),
        "references": references_a_resoudre(convocation),
    }
    resume["extraction_complete"] = bool(
        resume["enumeration"]["controle_effectif"]
        and resume["enumeration"]["complete"]
        and resume["sequence"]["complete"]
    )
    return resume
