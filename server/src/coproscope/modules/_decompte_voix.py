"""L'assiette du decompte des voix: ce que la loi impose de compter.

Ce module ne lit aucun document et n'ecrit dans aucun magasin. Il repond a une
seule question, celle que la maquette du 2026-09-03 n'a pas su trancher: **sur
quel total un pourcentage de voix a-t-il le droit d'etre calcule ?**

Le defaut mesure. Le meme proces-verbal exprime certains votes sur 4 899 parts
et d'autres sur 10 000. La maquette a refuse de calculer le moindre pourcentage,
faute de savoir nommer la base. Elle avait raison de refuser, et pour une raison
plus forte qu'elle ne le croyait: **le denominateur imprime a cote d'un vote
n'est pas l'assiette legale de ce vote**. C'est une modalite d'ecriture de
cabinet, mesuree divergente sur les deux corpus:

- cabinet A, quatre resolutions annoncees sous l'article 24 impriment `/10.000`
  alors que l'assiette legale est celle des presents et representes; les trois
  dont le detail est publie totalisent bien 4 899, pas 10 000;
- cabinet B imprime jusqu'a **trois denominateurs differents dans une seule
  resolution** - un sur la ligne `pour`, un autre sur la ligne `abstention`, un
  troisieme sur la ligne du defaillant - et alterne, d'une resolution a l'autre
  du meme type, entre le total des voix exprimees et le total du syndicat.

D'ou la regle des axes, appliquee ici a la lettre: **la maniere dont un syndic
ecrit son decompte est une modalite; ce que la loi impose de compter est
l'invariant.** L'assiette se deduit de la majorite annoncee et de la cle de
repartition, jamais du nombre imprime apres la barre oblique. Le denominateur
ecrit ne sert qu'a une chose: etre confronte a l'assiette deduite, et produire un
constat quand les deux divergent.

----------------------------------------------------------------------
Les cinq replis muets fermes le 2026-09-04
----------------------------------------------------------------------

1. **L'article 25-1 etait accepte comme majorite d'entree sans verifier le tiers
   qui l'ouvre.** `decompte_resolution("25-1", voix_pour=3000, voix_contre=100,
   voix_totales=10000)` proclamait `ADOPTEE_CONFIRMEE` a 96,77 %, alors que
   3 000 est sous le tiers de 3 334 et que le second vote n'etait donc pas
   ouvert. C'est le cas exact que ce module existe pour rendre impossible: il
   autorisait un pourcentage a tort.
2. **Aucun controle de coherence** entre les voix pour, la presence et le total
   du syndicat. 6 000 voix pour dans une assemblee ou 4 899 sont presentes
   rendaient 98,36 % d'adoption confirmee.
3. **`voix_abstention` etait un parametre mort**, alors qu'il porte le seul
   controle croise dont ce module ait les elements.
4. **`DECOMPTE_ABSENT` accusait le syndic d'une irregularite** pour des
   resolutions ou le proces-verbal ecrit qu'il n'y a simplement pas eu de vote:
   sept irregularites inventees sur la piece etalon, citation d'article a
   l'appui.
5. **Le vote par correspondance amende n'existait pas dans le code**, alors que
   la doctrine est ecrite et que le retrait des voix assimilees a des
   defaillants fait basculer un verdict de l'adoption au rejet.

Deux replis mineurs fermes au passage: le denominateur imprime etait jete par
les verdicts de refus au lieu d'y etre restitue comme piste, et le refus d'une
majorite non reconnue affirmait qu'aucune majorite n'etait enoncee - accusant le
document d'un defaut qui etait dans l'outil.

Le module est decoupe en quatre fichiers, qui n'ont pas le meme rythme de
changement: `_decompte_voix_regimes` (la table des regimes et ses sources),
`_decompte_voix_etats` (les etats rendus et le verdict), `_decompte_voix_controles`
(seuils, coherence, issue proclamee) et `_decompte_voix_branches` (une branche de
calcul par assiette). Ce fichier-ci n'orchestre que l'ordre des refus.

----------------------------------------------------------------------
Ce que ce module controle, et sur quoi il ne s'exerce pas encore
----------------------------------------------------------------------

**A lire avant de conclure qu'un controle est en service.** Le seul
consommateur de production, `_pont_actes_lignes._decompte`, passe
**cinq parametres sur quatorze**: `majorite`, `voix_pour`, `voix_contre`,
`voix_abstention` et `denominateur_ecrit`. Il ne passe ni `voix_totales`, ni
`voix_presentes`, ni `issue_annoncee`, ni `resolution_amendee`, ni
`nombre_membres`, ni `nombre_votants_pour`, ni `cle_speciale`.

Consequence a dire franchement: la verification du tiers de l'article 25-1, le
controle croise de coherence avec la feuille de presence, la confrontation a
l'issue proclamee, la double condition de l'article 26 et le retrait des voix
par correspondance amendees sont ecrits et testes **au niveau du module**, et
ne s'exercent aujourd'hui sur aucune donnee reelle. Le cablage tient en une
ligne chez le proprietaire du pont; il n'a pas ete fait ici, et ce module ne
peut pas le faire seul.

Sources lues sur Legifrance via PISTE le 2026-09-04, fonds `LODA_DATE`, filtre de
date pose au jour de la lecture. `VIGUEUR` signifie "en vigueur a la date
demandee", jamais "a jour": la date de version fait partie de la citation.

Aucune donnee nominative ne transite par ce module: il ne manipule que des
totaux de voix.
"""

from __future__ import annotations

from typing import Optional

from ._decompte_voix_branches import (
    verdict_amendement,
    verdict_article_25,
    verdict_article_26,
    verdict_unanimite,
    verdict_voix_exprimees,
)
from ._decompte_voix_controles import (
    CONSTAT_CONTROLE_CROISE_NON_CONDUIT,
    ISSUE_SANS_VOTE,
    incoherences,
    issue_proclamee,
    lire_voix,
    majorite_25_atteignable,
    passerelle_25_1_ouverte,
    seuil_deux_tiers,
    seuil_majorite_absolue,
    seuil_passerelle_25_1,
    voix_exprimees,
)
from ._decompte_voix_etats import (
    ETAT_ADOPTEE_CONFIRMEE,
    ETAT_ASSIETTE_INDETERMINEE,
    ETAT_DECOMPTE_ABSENT,
    ETAT_DECOMPTE_ILLISIBLE,
    ETAT_DECOMPTE_INCOHERENT,
    ETAT_DECOMPTE_INSUFFISANT,
    ETAT_ISSUE_CONTREDITE,
    ETAT_PASSERELLE_25_1_NON_OUVERTE,
    ETAT_PASSERELLE_25_1_REQUISE,
    ETAT_REJET_CONFIRME,
    ETAT_SANS_VOTE,
    Verdict,
)
from ._decompte_voix_regimes import (
    ASSIETTE_DOUBLE,
    ASSIETTE_TOUTES_LES_VOIX,
    ASSIETTE_UNANIMITE,
    ASSIETTE_VOIX_EXPRIMEES,
    ASSIETTES,
    MAJORITE_24,
    MAJORITE_25,
    MAJORITE_25_1,
    MAJORITE_26,
    MAJORITE_UNANIMITE,
    REGIMES,
    SOURCE_CLE_SPECIALE,
    SOURCE_CORRESPONDANCE_AMENDEE,
    SOURCE_CORRESPONDANCE_PRESENT,
    SOURCE_FEUILLE_ANNEXEE,
    SOURCE_FEUILLE_PRESENCE,
    SOURCE_VOIX,
    Regime,
    majorite_enoncee,
    normaliser_majorite,
    regime_de_majorite,
    sources_du_scrutin,
)

__all__ = [
    "ASSIETTES",
    "ASSIETTE_DOUBLE",
    "ASSIETTE_TOUTES_LES_VOIX",
    "ASSIETTE_UNANIMITE",
    "ASSIETTE_VOIX_EXPRIMEES",
    "ETAT_ADOPTEE_CONFIRMEE",
    "ETAT_ASSIETTE_INDETERMINEE",
    "ETAT_DECOMPTE_ABSENT",
    "ETAT_DECOMPTE_ILLISIBLE",
    "ETAT_DECOMPTE_INCOHERENT",
    "ETAT_DECOMPTE_INSUFFISANT",
    "ETAT_ISSUE_CONTREDITE",
    "ETAT_PASSERELLE_25_1_NON_OUVERTE",
    "ETAT_PASSERELLE_25_1_REQUISE",
    "ETAT_REJET_CONFIRME",
    "ETAT_SANS_VOTE",
    "MAJORITE_24",
    "MAJORITE_25",
    "MAJORITE_25_1",
    "MAJORITE_26",
    "MAJORITE_UNANIMITE",
    "REGIMES",
    "Regime",
    "SOURCE_CLE_SPECIALE",
    "SOURCE_CORRESPONDANCE_AMENDEE",
    "SOURCE_CORRESPONDANCE_PRESENT",
    "SOURCE_FEUILLE_ANNEXEE",
    "SOURCE_FEUILLE_PRESENCE",
    "SOURCE_VOIX",
    "Verdict",
    "decompte_resolution",
    "incoherences",
    "issue_proclamee",
    "lire_voix",
    "majorite_25_atteignable",
    "majorite_enoncee",
    "normaliser_majorite",
    "passerelle_25_1_ouverte",
    "regime_de_majorite",
    "seuil_deux_tiers",
    "seuil_majorite_absolue",
    "seuil_passerelle_25_1",
    "sources_du_scrutin",
    "voix_exprimees",
]


def decompte_resolution(
    majorite: Optional[str],
    voix_pour: Optional[int] = None,
    voix_contre: Optional[int] = None,
    voix_abstention: Optional[int] = None,
    voix_totales: Optional[int] = None,
    voix_presentes: Optional[int] = None,
    denominateur_ecrit: Optional[int] = None,
    issue_annoncee: Optional[str] = None,
    nombre_membres: Optional[int] = None,
    nombre_votants_pour: Optional[int] = None,
    resolution_amendee: bool = False,
    voix_correspondance_favorables: Optional[int] = None,
    voix_pour_premier_vote: Optional[int] = None,
    cle_speciale: bool = False,
) -> Verdict:
    """Rend ce que l'ecran a le droit d'afficher, ou pourquoi il ne peut rien.

    `voix_totales` est le total de la cle de repartition sur laquelle la
    resolution est votee - les tantiemes generaux, ou ceux d'une cle speciale
    quand le reglement reserve le vote aux coproprietaires concernes.

    `voix_pour_premier_vote` n'est utile que sous l'article 25-1: la condition
    d'ouverture de la passerelle porte sur le **premier** vote, pas sur le
    second. En son absence, `voix_pour` en tient lieu et le constat le dit.

    `cle_speciale` est **declare par l'appelant**, jamais deduit ici. Le
    denominateur imprime a cote d'un vote ne dit pas sur quelle cle de
    repartition ce vote a eu lieu, et le deduire contredirait la doctrine que
    ce module existe pour tenir. Declare, il fait citer l'article 10 dernier
    alinea, qui fonde le scrutin restreint.

    Les nombres de voix acceptent le type que l'extracteur produit reellement -
    des chaines, vides quand le proces-verbal ne publie rien. Une chaine vide
    est une absence; une valeur ecrite qu'on ne sait pas lire est
    `DECOMPTE_ILLISIBLE`, jamais une absence et jamais un zero.

    L'ordre des quatre refus n'est pas indifferent. Une assiette inconnue prime
    sur tout: rien ne se calcule sans elle. Vient ensuite l'absence de voix, qui
    se lit differemment selon que le proces-verbal enonce ou non qu'il n'y a pas
    eu de vote. Puis la coherence des nombres lus: un decompte impossible ne
    doit pas atteindre une division. Puis seulement le retrait des voix par
    correspondance assimilees a des defaillants, qui modifie l'assiette.

    Les etats de refus sont des resultats a part entiere. Un ecran qui affiche
    `ASSIETTE_INDETERMINEE` en nommant la donnee manquante est plus utile qu'un
    ecran qui affiche un pourcentage tire d'un denominateur d'imprimeur.

    **Effet de cet ordre, a ne pas laisser decouvrir a un relecteur.** La porte
    de coherence passe avant les constats de seuil. La mesure d'origine du
    constat sur l'article 26 - 7 000 voix pour, 4 899 presentes, 10 000 au
    total - ne rend donc plus le constat "hors d'atteinte" mais
    `DECOMPTE_INCOHERENT`, ce qui est juste: 7 000 voix pour dans une assemblee
    ou 4 899 sont presentes est d'abord un decompte impossible. Le constat
    "hors d'atteinte" reste atteignable des que les nombres peuvent etre vrais
    ensemble - 4 000 pour, 4 899 presentes, 10 000 au total le produisent. La
    preuve d'origine ne se rejoue plus telle quelle; le controle qu'elle
    fondait, si.
    """

    regime = regime_de_majorite(majorite)
    constats: list[str] = []

    if regime is None:
        return Verdict(
            etat=ETAT_ASSIETTE_INDETERMINEE,
            motif=_motif_majorite_absente(majorite),
            denominateur_ecrit=denominateur_ecrit,
        )

    lectures: dict[str, Optional[int]] = {}
    refus_de_lecture: list[str] = []
    for nom, brut in (
        ("les voix pour", voix_pour),
        ("les voix contre", voix_contre),
        ("les abstentions", voix_abstention),
        ("le total des voix du syndicat", voix_totales),
        ("la feuille de presence", voix_presentes),
        ("le denominateur imprime", denominateur_ecrit),
        ("le nombre de membres du syndicat", nombre_membres),
        ("le nombre de votants pour", nombre_votants_pour),
        ("les voix favorables par correspondance", voix_correspondance_favorables),
        ("les voix pour du premier vote", voix_pour_premier_vote),
    ):
        valeur, refus = lire_voix(nom, brut)
        lectures[nom] = valeur
        if refus:
            refus_de_lecture.append(refus)

    voix_pour = lectures["les voix pour"]
    voix_contre = lectures["les voix contre"]
    voix_abstention = lectures["les abstentions"]
    voix_totales = lectures["le total des voix du syndicat"]
    voix_presentes = lectures["la feuille de presence"]
    denominateur_ecrit = lectures["le denominateur imprime"]
    nombre_membres = lectures["le nombre de membres du syndicat"]
    nombre_votants_pour = lectures["le nombre de votants pour"]
    voix_correspondance_favorables = lectures[
        "les voix favorables par correspondance"
    ]
    voix_pour_premier_vote = lectures["les voix pour du premier vote"]

    sources = sources_du_scrutin(
        regime,
        cle_speciale=cle_speciale,
        presence_lue=voix_presentes is not None,
        correspondance_lue=(
            resolution_amendee or voix_correspondance_favorables is not None
        ),
    )

    if refus_de_lecture:
        # Une valeur ecrite et illisible n'est ni absente ni fausse: c'est un
        # refus de lecture, et il precede toute division comme toute conclusion
        # d'absence. La confondre avec `DECOMPTE_ABSENT` accuserait le syndic
        # d'une omission qu'il n'a pas commise.
        return Verdict(
            etat=ETAT_DECOMPTE_ILLISIBLE,
            assiette=regime.assiette,
            motif=refus_de_lecture[0],
            constats=list(refus_de_lecture),
            sources=sources,
            denominateur_ecrit=denominateur_ecrit,
        )

    if voix_pour is None:
        if issue_proclamee(issue_annoncee) == ISSUE_SANS_VOTE:
            return Verdict(
                etat=ETAT_SANS_VOTE,
                assiette=regime.assiette,
                motif=(
                    "le proces-verbal enonce que la question n'a pas ete mise "
                    "aux voix; l'absence de decompte est constatee sur le "
                    "document et n'est pas une irregularite du syndic"
                ),
                sources=sources,
                denominateur_ecrit=denominateur_ecrit,
            )
        return Verdict(
            etat=ETAT_DECOMPTE_ABSENT,
            assiette=regime.assiette,
            motif=(
                "le proces-verbal ne publie pas les voix; l'article 17 du "
                "decret impose pourtant le resultat du vote sous chaque "
                "question"
            ),
            sources=_avec(sources, SOURCE_FEUILLE_ANNEXEE),
            denominateur_ecrit=denominateur_ecrit,
        )

    if cle_speciale and voix_presentes is not None:
        constats.append(CONSTAT_CONTROLE_CROISE_NON_CONDUIT)

    contradictions = incoherences(
        voix_pour=voix_pour,
        voix_contre=voix_contre,
        voix_abstention=voix_abstention,
        voix_presentes=voix_presentes,
        voix_totales=voix_totales,
        cle_speciale=cle_speciale,
    )
    if contradictions:
        return Verdict(
            etat=ETAT_DECOMPTE_INCOHERENT,
            assiette=regime.assiette,
            voix_pour=int(voix_pour),
            motif=contradictions[0],
            constats=list(contradictions),
            sources=_avec(sources, SOURCE_FEUILLE_PRESENCE),
            denominateur_ecrit=denominateur_ecrit,
        )

    if resolution_amendee:
        refus, voix_pour, constats_amendement = verdict_amendement(
            int(voix_pour),
            voix_correspondance_favorables,
            regime.assiette,
            sources,
            denominateur_ecrit,
        )
        if refus is not None:
            return refus
        constats.extend(constats_amendement)
        sources = _avec(sources, SOURCE_CORRESPONDANCE_AMENDEE)

    if regime.assiette == ASSIETTE_UNANIMITE:
        return verdict_unanimite(
            regime,
            voix_pour=int(voix_pour),
            voix_totales=voix_totales,
            denominateur_ecrit=denominateur_ecrit,
            issue_annoncee=issue_annoncee,
            sources=sources,
            constats=constats,
        )

    if regime.assiette == ASSIETTE_DOUBLE:
        return verdict_article_26(
            regime,
            voix_pour=int(voix_pour),
            voix_totales=voix_totales,
            voix_presentes=voix_presentes,
            denominateur_ecrit=denominateur_ecrit,
            issue_annoncee=issue_annoncee,
            nombre_membres=nombre_membres,
            nombre_votants_pour=nombre_votants_pour,
            sources=sources,
            constats=constats,
        )

    if regime.assiette == ASSIETTE_VOIX_EXPRIMEES:
        return verdict_voix_exprimees(
            regime,
            voix_pour=int(voix_pour),
            voix_contre=voix_contre,
            voix_totales=voix_totales,
            voix_pour_premier_vote=voix_pour_premier_vote,
            denominateur_ecrit=denominateur_ecrit,
            issue_annoncee=issue_annoncee,
            sources=sources,
            constats=constats,
        )

    return verdict_article_25(
        regime,
        voix_pour=int(voix_pour),
        voix_totales=voix_totales,
        voix_presentes=voix_presentes,
        denominateur_ecrit=denominateur_ecrit,
        issue_annoncee=issue_annoncee,
        sources=sources,
        constats=constats,
    )


def _avec(sources: tuple, source: tuple) -> tuple:
    """Ajoute une source sans la citer deux fois.

    `sources_du_scrutin` attache desormais l'article 14 du decret des qu'une
    feuille de presence est lue. Les verdicts qui l'ajoutaient deja pour leur
    propre compte le repeteraient sans ce garde, et une liste de sources qui
    repete un article se lit comme deux fondements distincts.
    """

    return sources if source in sources else sources + (source,)


def _motif_majorite_absente(majorite: Optional[str]) -> str:
    """Deux refus differents, qui disaient jusqu'ici la meme phrase.

    Le refus etait prudent et son motif etait faux: `25B`, `23` ou `Article 24`
    faisaient dire "la majorite n'est pas enoncee" alors qu'elle l'etait. Un
    lecteur concluait a un defaut du document quand le defaut etait dans la
    table des regimes.
    """

    if majorite_enoncee(majorite):
        return (
            f"la majorite \"{normaliser_majorite(majorite)}\" est enoncee au "
            "proces-verbal mais n'est pas un regime reconnu par ce module; "
            "l'assiette du decompte en depend et ne peut pas etre supposee. Le "
            "document n'est pas en defaut"
        )
    return (
        "la majorite applicable n'est pas enoncee; l'assiette du decompte en "
        "depend et ne peut pas etre supposee"
    )
