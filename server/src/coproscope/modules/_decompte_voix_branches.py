"""Une branche de calcul par assiette, et la confrontation qui les traverse.

Extrait de `_decompte_voix` le 2026-09-04. Chaque fonction rend un `Verdict`
complet; aucune n'ecrit dans un magasin et aucune ne lit un document.

Ce qui est commun aux quatre regimes est ici, et ne l'etait pas avant:

- la **confrontation a l'issue proclamee** au proces-verbal. Elle n'avait lieu
  que sous l'article 25, par un `startswith("adopt")`, si bien que
  `decompte_resolution("24", voix_pour=100, voix_contre=10,
  issue_annoncee="Rejetee")` rendait `ADOPTEE_CONFIRMEE`. Il n'existait aucun
  etat pour "le decompte contredit l'issue proclamee";
- la **confrontation du denominateur imprime** et le **signalement d'un seuil
  hors d'atteinte**, que la branche de l'article 26 ne faisait ni l'une ni
  l'autre - alors que c'est le regime ou le seuil est le plus haut;
- le **retrait des voix par correspondance assimilees a des defaillants** quand
  la resolution a ete amendee en seance, qui n'existait nulle part.

Aucune donnee nominative ne transite par ce module.
"""

from __future__ import annotations

from typing import Optional

from ._decompte_voix_controles import (
    ISSUE_ADOPTEE,
    ISSUE_REJETEE,
    constat_denominateur,
    constat_hors_atteinte,
    issue_proclamee,
    passerelle_25_1_ouverte,
    seuil_deux_tiers,
    seuil_majorite_absolue,
    seuil_passerelle_25_1,
    voix_exprimees,
)
from ._decompte_voix_etats import (
    ETAT_ADOPTEE_CONFIRMEE,
    ETAT_ASSIETTE_INDETERMINEE,
    ETAT_DECOMPTE_INCOHERENT,
    ETAT_DECOMPTE_INSUFFISANT,
    ETAT_ISSUE_CONTREDITE,
    ETAT_PASSERELLE_25_1_NON_OUVERTE,
    ETAT_PASSERELLE_25_1_REQUISE,
    ETAT_REJET_CONFIRME,
    Verdict,
)
from ._decompte_voix_regimes import (
    MAJORITE_25_1,
    REGIMES,
    SOURCE_CORRESPONDANCE_AMENDEE,
    Regime,
)


def confronter(atteint: bool, issue_annoncee: Optional[str]) -> str:
    """L'etat rendu par la confrontation du decompte a l'issue proclamee.

    Le mot `CONFIRMEE` promettait une comparaison qui n'avait lieu que sous
    l'article 25. La confrontation est desormais la meme sous les quatre
    regimes. Quand l'issue n'est pas fournie, il n'y a pas de comparaison: le
    decompte rend le seuil, et rien de plus.
    """

    proclamee = issue_proclamee(issue_annoncee)
    if atteint:
        if proclamee == ISSUE_REJETEE:
            return ETAT_ISSUE_CONTREDITE
        return ETAT_ADOPTEE_CONFIRMEE
    if proclamee == ISSUE_ADOPTEE:
        return ETAT_DECOMPTE_INSUFFISANT
    return ETAT_REJET_CONFIRME


def motif_confrontation(etat: str, enonce: str) -> str:
    if etat == ETAT_ISSUE_CONTREDITE:
        return (
            "le seuil de la majorite annoncee est atteint et le proces-verbal "
            f"conclut au rejet ({enonce})"
        )
    if etat == ETAT_DECOMPTE_INSUFFISANT:
        return (
            "proclamee adoptee alors que le seuil de la majorite annoncee "
            f"n'est pas atteint ({enonce})"
        )
    return enonce


def verdict_amendement(
    voix_pour: int,
    voix_correspondance_favorables: Optional[int],
    assiette: str,
    sources: tuple,
    denominateur_ecrit: Optional[int],
) -> tuple[Optional[Verdict], int, list[str]]:
    """Retire les voix par correspondance assimilees a des defaillants.

    L'article 17-1 A al. 2 assimile a un coproprietaire defaillant le votant par
    correspondance **ayant vote favorablement**, et seulement si la resolution
    est **amendee** en seance. La doctrine tranche: il faut recalculer, et non
    refuser de conclure - **mais uniquement quand le proces-verbal publie la
    ligne des defaillants assimiles.** Sans cette ligne, le recalcul serait une
    reconstitution, pas une lecture.

    Mesure de l'ecart, sur les 741 voix du cas mesure au cabinet B: pour 15 400
    contre 15 325, la resolution est adoptee a 50,12 % sur une base de 30 725;
    apres retrait des 741 favorables devenus defaillants, elle est rejetee a
    48,89 % sur une base de 29 984. Le verdict bascule sur 2,4 % d'assiette.

    Rend le triplet (verdict de refus ou `None`, voix pour retenues, constats).
    """

    if voix_correspondance_favorables is None:
        return (
            Verdict(
                etat=ETAT_ASSIETTE_INDETERMINEE,
                assiette=assiette,
                voix_pour=int(voix_pour),
                motif=(
                    "la resolution a ete amendee en seance: le votant par "
                    "correspondance ayant vote favorablement est assimile a un "
                    "coproprietaire defaillant, et ses voix sortent du pour "
                    "comme de l'assiette; le proces-verbal ne publie pas la "
                    "ligne de ces voix, le recalcul serait une reconstitution "
                    "et le controle n'est pas conduit"
                ),
                sources=sources + (SOURCE_CORRESPONDANCE_AMENDEE,),
                denominateur_ecrit=denominateur_ecrit,
            ),
            voix_pour,
            [],
        )

    retirees = int(voix_correspondance_favorables)
    if retirees < 0 or retirees > int(voix_pour):
        return (
            Verdict(
                etat=ETAT_DECOMPTE_INCOHERENT,
                assiette=assiette,
                voix_pour=int(voix_pour),
                motif=(
                    f"le proces-verbal publie {retirees} voix favorables par "
                    f"correspondance assimilees a des defaillants, pour "
                    f"{int(voix_pour)} voix pour: la ligne ne peut pas etre "
                    "retiree du pour"
                ),
                sources=sources + (SOURCE_CORRESPONDANCE_AMENDEE,),
                denominateur_ecrit=denominateur_ecrit,
            ),
            voix_pour,
            [],
        )

    constat = (
        f"resolution amendee en seance: {retirees} voix favorables exprimees "
        "par correspondance sont assimilees a des defaillants et sortent du "
        "pour comme de l'assiette"
    )
    return None, int(voix_pour) - retirees, [constat]


def verdict_article_26(
    regime: Regime,
    voix_pour: int,
    voix_totales: Optional[int],
    voix_presentes: Optional[int],
    denominateur_ecrit: Optional[int],
    issue_annoncee: Optional[str],
    nombre_membres: Optional[int],
    nombre_votants_pour: Optional[int],
    sources: tuple,
    constats: list[str],
) -> Verdict:
    """La double condition de l'article 26, et ce qu'elle ne peut pas verifier.

    La branche ne confrontait aucun denominateur imprime et ne signalait aucun
    seuil hors d'atteinte, alors que c'est le regime ou le seuil est le plus
    haut - deux tiers - et donc le plus surement inatteignable avec une presence
    faible.
    """

    seuil_voix = seuil_deux_tiers(voix_totales)
    if seuil_voix is None:
        return Verdict(
            etat=ETAT_ASSIETTE_INDETERMINEE,
            assiette=regime.assiette,
            voix_pour=voix_pour,
            motif="le total des voix du syndicat n'est pas connu",
            sources=sources,
            constats=constats,
            denominateur_ecrit=denominateur_ecrit,
        )

    base = int(voix_totales)
    for constat in (
        constat_denominateur(denominateur_ecrit, base),
        constat_hors_atteinte(voix_presentes, seuil_voix, base, "26"),
    ):
        if constat:
            constats.append(constat)

    if nombre_membres is None or nombre_votants_pour is None:
        return Verdict(
            etat=ETAT_ASSIETTE_INDETERMINEE,
            assiette=regime.assiette,
            base_retenue=base,
            seuil_requis=seuil_voix,
            voix_pour=voix_pour,
            motif=(
                "l'article 26 exige une majorite en nombre de membres du "
                "syndicat en plus des deux tiers des voix; le nombre de "
                "membres n'est pas publie, la seconde condition ne peut "
                "pas etre verifiee"
            ),
            sources=sources,
            constats=constats,
            denominateur_ecrit=denominateur_ecrit,
        )

    atteint = (
        voix_pour >= seuil_voix
        and int(nombre_votants_pour) * 2 > int(nombre_membres)
    )
    etat = confronter(atteint, issue_annoncee)
    if atteint:
        constats.append(CONSTAT_UNANIMITE_NON_VERIFIEE)
    return Verdict(
        etat=etat,
        assiette=regime.assiette,
        base_retenue=base,
        seuil_requis=seuil_voix,
        voix_pour=voix_pour,
        pourcentage=round(100.0 * voix_pour / base, 2),
        motif=motif_confrontation(etat, regime.enonce),
        sources=sources,
        constats=constats,
        denominateur_ecrit=denominateur_ecrit,
    )


#: Ce que les deux tiers de l'article 26 ne repondent pas. L'article 26 dernier
#: alinea reserve a l'unanimite certains objets - l'alienation d'une partie
#: commune necessaire au respect de la destination de l'immeuble, la
#: modification de cette destination. Ce module ne lit pas l'objet de la
#: resolution: il ne peut pas savoir si l'unanimite etait requise. Le dire est
#: un fait nomme; se taire laisserait croire que les deux tiers repondent a
#: toute la question.
CONSTAT_UNANIMITE_NON_VERIFIEE = (
    "les deux tiers sont le seuil general de l'article 26; son dernier alinea "
    "reserve certains objets a l'unanimite des voix. L'objet de la resolution "
    "n'est pas lu ici: la question de savoir si l'unanimite etait requise "
    "n'est pas tranchee par ce verdict"
)


def verdict_unanimite(
    regime: Regime,
    voix_pour: int,
    voix_totales: Optional[int],
    denominateur_ecrit: Optional[int],
    issue_annoncee: Optional[str],
    sources: tuple,
    constats: list[str],
) -> Verdict:
    """L'unanimite: la totalite des voix, et aucun second vote.

    Elle ne se range pas sous l'article 25 malgre la meme base. L'article 25 se
    gagne a la moitie plus une et ouvre la passerelle de l'article 25-1;
    l'unanimite se gagne a la totalite et n'ouvre rien. Les router ensemble
    aurait propose un second vote la ou la loi n'en offre aucun.
    """

    if voix_totales is None or int(voix_totales) <= 0:
        return Verdict(
            etat=ETAT_ASSIETTE_INDETERMINEE,
            assiette=regime.assiette,
            voix_pour=voix_pour,
            motif=(
                "l'unanimite se compte sur les voix de tous les "
                "coproprietaires; ce total n'est pas connu"
            ),
            sources=sources,
            constats=constats,
            denominateur_ecrit=denominateur_ecrit,
        )

    base = int(voix_totales)
    constat = constat_denominateur(denominateur_ecrit, base)
    if constat:
        constats.append(constat)

    etat = confronter(voix_pour >= base, issue_annoncee)
    return Verdict(
        etat=etat,
        assiette=regime.assiette,
        base_retenue=base,
        seuil_requis=base,
        voix_pour=voix_pour,
        pourcentage=round(100.0 * voix_pour / base, 2),
        motif=motif_confrontation(etat, regime.enonce),
        sources=sources,
        constats=constats,
        denominateur_ecrit=denominateur_ecrit,
    )


def _refus_passerelle_non_verifiable(
    regime: Regime,
    voix_pour: int,
    sources: tuple,
    constats: list[str],
    denominateur_ecrit: Optional[int],
) -> Verdict:
    return Verdict(
        etat=ETAT_ASSIETTE_INDETERMINEE,
        assiette=regime.assiette,
        voix_pour=voix_pour,
        motif=(
            "le second vote de l'article 25-1 n'est ouvert que si le projet a "
            "recueilli au moins le tiers des voix de tous les coproprietaires; "
            "ce total n'est pas connu et la condition d'ouverture ne peut pas "
            "etre verifiee"
        ),
        sources=sources,
        constats=constats,
        denominateur_ecrit=denominateur_ecrit,
    )


def _verdict_passerelle_fermee(
    regime: Regime,
    premier: int,
    tiers: Optional[int],
    voix_totales: int,
    sources: tuple,
    constats: list[str],
    denominateur_ecrit: Optional[int],
) -> Verdict:
    constats.append(
        f"le premier vote a recueilli {premier} voix pour un tiers de {tiers} "
        f"sur {voix_totales}: la passerelle de l'article 25-1 n'etait pas "
        "ouverte"
    )
    return Verdict(
        etat=ETAT_PASSERELLE_25_1_NON_OUVERTE,
        assiette=regime.assiette,
        base_retenue=voix_totales,
        seuil_requis=tiers,
        voix_pour=premier,
        motif=(
            "un second vote a la majorite de l'article 24 a ete applique alors "
            "que le premier vote n'a pas atteint le tiers des voix de tous les "
            "coproprietaires; la loi interdisait ce second vote, aucun "
            "pourcentage n'est recevable"
        ),
        sources=sources,
        constats=constats,
        denominateur_ecrit=denominateur_ecrit,
    )


def verdict_voix_exprimees(
    regime: Regime,
    voix_pour: int,
    voix_contre: Optional[int],
    voix_totales: Optional[int],
    voix_pour_premier_vote: Optional[int],
    denominateur_ecrit: Optional[int],
    issue_annoncee: Optional[str],
    sources: tuple,
    constats: list[str],
) -> Verdict:
    """Les articles 24 et 25-1, et la condition d'ouverture du second vote.

    L'article 25-1 n'est pas une majorite d'entree: c'est un second vote, ouvert
    **seulement** si le projet a recueilli au moins le tiers des voix de tous
    les coproprietaires. Ce tiers n'etait jamais verifie, et le module
    proclamait une adoption confirmee a 96,77 % sur une resolution que la loi
    interdisait de soumettre a un second vote.
    """

    if regime.majorite == MAJORITE_25_1:
        premier = (
            voix_pour if voix_pour_premier_vote is None else int(voix_pour_premier_vote)
        )
        ouverte = passerelle_25_1_ouverte(premier, voix_totales)
        if ouverte is None:
            return _refus_passerelle_non_verifiable(
                regime, voix_pour, sources, constats, denominateur_ecrit
            )
        tiers = seuil_passerelle_25_1(voix_totales)
        if not ouverte:
            return _verdict_passerelle_fermee(
                regime,
                premier,
                tiers,
                int(voix_totales),
                sources,
                constats,
                denominateur_ecrit,
            )
        origine = (
            "au premier vote"
            if voix_pour_premier_vote is not None
            else "au vote lu (le premier vote n'est pas fourni separement)"
        )
        constats.append(
            f"condition d'ouverture de l'article 25-1 verifiee: {premier} voix "
            f"{origine}, pour un tiers de {tiers} sur {int(voix_totales)}"
        )

    base = voix_exprimees(voix_pour, voix_contre)
    if base is None:
        return Verdict(
            etat=ETAT_ASSIETTE_INDETERMINEE,
            assiette=regime.assiette,
            voix_pour=voix_pour,
            motif=(
                "les voix contre ne sont pas publiees; les voix exprimees "
                "ne peuvent pas etre reconstituees, et les abstentions "
                "n'en font pas partie"
            ),
            sources=sources,
            constats=constats,
            denominateur_ecrit=denominateur_ecrit,
        )
    if base <= 0:
        return Verdict(
            etat=ETAT_ASSIETTE_INDETERMINEE,
            assiette=regime.assiette,
            motif="aucune voix exprimee: il n'y a rien a rapporter a une base",
            sources=sources,
            constats=constats,
            denominateur_ecrit=denominateur_ecrit,
        )
    seuil = base // 2 + 1
    constat = constat_denominateur(denominateur_ecrit, base)
    if constat:
        constats.append(constat)
    etat = confronter(voix_pour >= seuil, issue_annoncee)
    return Verdict(
        etat=etat,
        assiette=regime.assiette,
        base_retenue=base,
        seuil_requis=seuil,
        voix_pour=voix_pour,
        pourcentage=round(100.0 * voix_pour / base, 2),
        motif=motif_confrontation(etat, regime.enonce),
        constats=constats,
        sources=sources,
        denominateur_ecrit=denominateur_ecrit,
    )


def verdict_article_25(
    regime: Regime,
    voix_pour: int,
    voix_totales: Optional[int],
    voix_presentes: Optional[int],
    denominateur_ecrit: Optional[int],
    issue_annoncee: Optional[str],
    sources: tuple,
    constats: list[str],
) -> Verdict:
    """L'article 25, et la passerelle qui explique une adoption sous son seuil."""

    seuil = seuil_majorite_absolue(voix_totales)
    if seuil is None:
        return Verdict(
            etat=ETAT_ASSIETTE_INDETERMINEE,
            assiette=regime.assiette,
            voix_pour=voix_pour,
            motif=(
                "l'article 25 se compte sur les voix de tous les "
                "coproprietaires; ce total n'est pas connu"
            ),
            sources=sources,
            constats=constats,
            denominateur_ecrit=denominateur_ecrit,
        )

    base = int(voix_totales)
    for constat in (
        constat_denominateur(denominateur_ecrit, base),
        constat_hors_atteinte(voix_presentes, seuil, base, "25"),
    ):
        if constat:
            constats.append(constat)

    pourcentage = round(100.0 * voix_pour / base, 2)

    if voix_pour >= seuil:
        etat = confronter(True, issue_annoncee)
        return Verdict(
            etat=etat,
            assiette=regime.assiette,
            base_retenue=base,
            seuil_requis=seuil,
            voix_pour=voix_pour,
            pourcentage=pourcentage,
            motif=motif_confrontation(etat, regime.enonce),
            constats=constats,
            sources=sources,
            denominateur_ecrit=denominateur_ecrit,
        )

    if passerelle_25_1_ouverte(voix_pour, voix_totales):
        return Verdict(
            etat=ETAT_PASSERELLE_25_1_REQUISE,
            assiette=regime.assiette,
            base_retenue=base,
            seuil_requis=seuil,
            voix_pour=voix_pour,
            pourcentage=pourcentage,
            motif=(
                "le seuil de l'article 25 n'est pas atteint, mais le projet a "
                f"recueilli au moins le tiers des voix "
                f"({seuil_passerelle_25_1(base)}); la passerelle de l'article "
                "25-1 ouvre un second vote immediat a la majorite de "
                "l'article 24"
            ),
            constats=constats,
            sources=REGIMES[MAJORITE_25_1].sources,
            denominateur_ecrit=denominateur_ecrit,
        )

    if issue_proclamee(issue_annoncee) == ISSUE_ADOPTEE:
        return Verdict(
            etat=ETAT_DECOMPTE_INSUFFISANT,
            assiette=regime.assiette,
            base_retenue=base,
            seuil_requis=seuil,
            voix_pour=voix_pour,
            pourcentage=pourcentage,
            motif=(
                "proclamee adoptee alors que ni le seuil de l'article 25 ni le "
                "tiers ouvrant la passerelle de l'article 25-1 ne sont atteints"
            ),
            constats=constats,
            sources=sources + REGIMES[MAJORITE_25_1].sources,
            denominateur_ecrit=denominateur_ecrit,
        )

    return Verdict(
        etat=ETAT_REJET_CONFIRME,
        assiette=regime.assiette,
        base_retenue=base,
        seuil_requis=seuil,
        voix_pour=voix_pour,
        pourcentage=pourcentage,
        motif=(
            "ni le seuil de l'article 25 ni le tiers de l'article 25-1 ne sont "
            "atteints"
        ),
        constats=constats,
        sources=sources + REGIMES[MAJORITE_25_1].sources,
        denominateur_ecrit=denominateur_ecrit,
    )
