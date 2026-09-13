"""Les liens que le pont ECRIT entre un acte et ses pieces.

Troisieme part de l'ecriture du pont, separee de `_pont_actes_lignes` le
2026-09-05 parce que le module reunissait trois sujets et passait 600 lignes.
La coupure suit la barre de section qui etait deja la: l'acte et ses attributs
decrivent la resolution, les liens decrivent ce qui l'appuie.

Un lien porte une **force probatoire** et une **provenance**, et les deux
disent des choses differentes. La force dit sur quoi le lien repose - une piece
au dossier, ou la seule affirmation du syndic. La provenance dit qui l'a pose -
un calcul de CoproScope, le syndic, un humain. Un lien affirme par le syndic et
jamais verifie reste un lien: il est ecrit, visible, et il porte la mention de
ce qu'il vaut. C'est le contraire de le taire.
"""

from __future__ import annotations

from typing import Any, Iterable

from . import _resolutions_registre
from ._actes_schema import lien_id
from ._actes_seuils_normes import (
    NORME_NON_ATTRIBUEE,
    NormeSeuil,
    norme_arretee,
)
from ._actes_vocabulaire import (
    FORCE_AFFIRME,
    FORCE_PIECE,
    KIND_ACTE,
    KIND_DEVIS_CITE,
    KIND_DOCUMENT,
    ORIGINE_EXTRAIT,
    PORTEE_ENGAGEMENT_DEPENSE,
    PORTEE_SEUIL,
    PROV_CALCUL,
    PROV_SYNDIC,
    REL_AVIS_CS,
    REL_DEVIS_RETENU,
    RESULTAT_ADOPTEE,
)
from ._pont_actes_source import Candidat, _lu


# --------------------------------------------------------------------------
# Liens
# --------------------------------------------------------------------------

#: Ce qu'on ecrit quand l'appelant n'a fourni AUCUNE norme pour un acte de
#: seuil. Ce n'est pas le meme cas que `norme_arretee` qui ne sait pas conclure:
#: ici la question n'a pas ete posee, et un lien qui se tairait la-dessus
#: laisserait croire a une attribution.
MOTIF_NORME_ABSENTE = (
    "la norme arretee par cette deliberation n'a pas ete recherchee: le lien "
    "est rattache sans dire quelle obligation le montant declenche"
)


def _lien(
    acte: dict[str, str],
    relation: str,
    target_kind: str,
    target_id: str,
    provenance: str,
    force: str,
    motif: str,
    *,
    libelle_cible: str = "",
    montant_impute: str = "",
    doute: str = "",
) -> dict[str, str]:
    return {
        "lien_id": lien_id(
            KIND_ACTE, acte["acte_id"], relation, target_kind, target_id, provenance
        ),
        "source_kind": KIND_ACTE,
        "source_id": acte["acte_id"],
        "relation": relation,
        "target_kind": target_kind,
        "target_id": target_id,
        "provenance": provenance,
        "force_probatoire": force,
        "motif": motif,
        "doute": doute,
        "montant_impute": montant_impute,
        "libelle_cible": libelle_cible,
        # Un lien ARRIERE n'a pas d'echeance: il est une condition de validite,
        # pas une obligation datee.
        "echeance": "",
        # La date du fait, pas celle de l'execution du programme. Une vue qui
        # comparerait des dates de traitement ne serait pas reproductible.
        "constate_le": acte.get("date_effet", ""),
        "auteur": "",
        "page": acte.get("page", ""),
        "ancre": acte.get("ancre", ""),
        "doc_id": acte.get("doc_id", ""),
        "origine": ORIGINE_EXTRAIT,
    }


def liens_du_devis(candidat: Candidat, acte: dict[str, str]) -> list[dict[str, str]]:
    """Le devis retenu, et l'avis du conseil syndical - tels qu'AFFIRMES.

    Les deux liens portent `SYNDIC_AFFIRME`, parce que c'est la convocation qui
    les enonce. La force probatoire les separe: un devis dont le montant est lu
    est une piece produite; un avis du conseil syndical annonce sans document
    joint reste `AFFIRME_SANS_PIECE`, donc `A confirmer` a l'ecran, et il ne
    franchit jamais la frontiere vers une sortie destinee a un tiers.
    """
    ligne = candidat.ligne
    liens: list[dict[str, str]] = []
    entreprise = ligne.get("entreprise", "")
    # Un montant illisible n'est pas une piece produite: le lien retombe sur
    # `AFFIRME_SANS_PIECE`, comme s'il n'y avait pas de montant du tout. C'est
    # le bon repli - il demande une relecture au lieu d'affirmer un chiffre.
    montant, _ = _lu(ligne.get("montant_ttc", ""))
    cible = ligne.get("devis_cite_id", "")
    if cible:
        libelle = " , ".join(x for x in (entreprise, f"{montant} EUR" if montant else "") if x)
        liens.append(
            _lien(
                acte,
                REL_DEVIS_RETENU,
                KIND_DEVIS_CITE,
                cible,
                PROV_SYNDIC,
                # **Toujours `AFFIRME_SANS_PIECE`, meme quand le montant est
                # lu.** Jusqu'au 2026-09-06 la force valait `PIECE_PRODUITE`
                # des qu'un nombre etait lu, et l'ecran rendait alors « Le
                # devis retenu est au dossier. » sur 54 actes du coffre reel
                # dont AUCUN n'avait de devis rattache. Ce qui avait ete lu
                # n'etait pas une piece: c'etait un nombre dans une phrase de
                # la convocation, c'est-a-dire l'affirmation du syndic.
                #
                # La force ne remontera a `PIECE_PRODUITE` que le jour ou ce
                # lien visera un `document` reel - et ce jour-la ce sera un
                # humain qui l'aura dit, avec un motif.
                FORCE_AFFIRME,
                (
                    f"La convocation de l'assemblee du {acte['date_effet']} cite "
                    f"ce devis au point {ligne.get('numero', '')}"
                    + (f"-{ligne['sous_numero']}" if ligne.get("sous_numero") else "")
                    + (
                        f" pour {montant} EUR, sans joindre la piece."
                        if montant
                        else " sans en chiffrer le montant."
                    )
                ),
                libelle_cible=libelle,
                montant_impute=montant,
                doute=(
                    "devis cite et chiffre par la convocation, aucune piece jointe"
                    if montant
                    else "montant du devis non lu dans la convocation"
                ),
            )
        )
    if (ligne.get("avis_cs_affirme") or "").lower() == "oui":
        liens.append(
            _lien(
                acte,
                REL_AVIS_CS,
                KIND_DOCUMENT,
                # **Cible vide, et c'est la verite.** Jusqu'au 2026-09-06 ce
                # lien visait `acte["doc_id"]`, c'est-a-dire la convocation qui
                # porte l'affirmation. Mesure sur le coffre reel: 72 liens, UNE
                # seule cible distincte, et les 72 pointaient sur le document
                # de leur propre acte. « 72 liens vers un document » etait vrai
                # et vide - le lien ne menait a aucun avis, il bouclait sur
                # celui qui l'affirme.
                #
                # Une cible vide dit ce qui est etabli: le syndic affirme qu'un
                # avis existe, et nous ne l'avons pas localise. Le jour ou il
                # sera retrouve, c'est SON identifiant qui viendra ici.
                "",
                PROV_SYNDIC,
                FORCE_AFFIRME,
                (
                    "La convocation affirme que le conseil syndical a ete "
                    "consulte sur ce projet. Aucune piece n'est jointe a "
                    "l'appui, et aucun document du dossier n'a ete rattache a "
                    "cette affirmation."
                ),
                doute="avis affirme par le syndic, piece non localisee",
            )
        )
    return liens


def normes_seuil(
    candidats: Iterable[Candidat], actes: Iterable[dict[str, str]]
) -> dict[str, tuple[NormeSeuil, str]]:
    """Quelle norme chaque acte de portee SEUIL arrete, et pourquoi si on l'ignore.

    **La distinction n'est pas inventee ici: elle est recuperee.** La voie
    resolutions qualifie deja separement `SEUIL_CONSULTATION_CS` et
    `SEUIL_MISE_EN_CONCURRENCE`, sur deux motifs distincts et sur le corps de la
    resolution. Le modele des actes ecrasait les deux en une portee `SEUIL`
    unique, puis en une relation unique. Cette fonction reprend le discriminant
    la ou il a ete ecrit, dans la colonne `qualifications` du registre, au lieu
    de le recalculer sur un intitule tronque.

    `candidats` et `actes` sont apparies par leur RANG, parce que c'est ainsi
    que l'appelant les construit: un acte par candidat, dans l'ordre. Recalculer
    l'identifiant ici en ferait une seconde source de verite pour l'identite
    d'un acte, ce que `acte_id_resolution` est justement seul a decider.

    L'appariement est `strict`: un appelant qui filtrerait l'une des deux listes
    obtiendrait sinon un decalage silencieux, et les normes seraient attribuees
    aux mauvais actes sans qu'aucun compteur ne bouge - le total des liens
    resterait juste. C'est exactement la forme de defaut que ce lot corrige.

    Rend un dictionnaire pour les seuls actes de portee `SEUIL`: les autres ne
    posent pas de norme, et une entree pour eux se lirait comme une reponse.
    """
    normes: dict[str, tuple[NormeSeuil, str]] = {}
    for candidat, acte in zip(candidats, actes, strict=True):
        if acte.get("portee") != PORTEE_SEUIL:
            continue
        normes[acte["acte_id"]] = norme_arretee(
            candidat.ligne.get("qualifications", "")
        )
    return normes


def liens_seuil(
    actes: Iterable[dict[str, str]],
    etats_par_date: dict[str, list[dict[str, Any]]],
    normes_par_acte: dict[str, tuple[NormeSeuil, str]],
) -> list[dict[str, str]]:
    """Rattache chaque engagement de depense au seuil en vigueur a sa date.

    **Un lien par norme, et non un lien par seuil rencontre.** Corrige le
    2026-09-08 (`RM-2026-0144`). Le meme jour, la meme assemblee arrete deux
    montants: celui a partir duquel la consultation du conseil syndical est
    obligatoire, et celui a partir duquel la mise en concurrence l'est. Les deux
    partaient sur la relation `SEUIL_APPLICABLE`, donc l'ecran mettait en
    concurrence deux votes qui ne repondaient pas a la meme question - et les
    declarait `non tranche` faute de pouvoir les departager, devant une
    copropriete parfaitement en regle.

    `normes_par_acte` dit, pour chaque acte de portee `SEUIL`, laquelle des deux
    obligations il arrete. Un acte absent de ce dictionnaire, ou dont la norme
    n'a pas ete attribuee, tombe sur la relation residuelle avec le motif ecrit
    dans `doute`: **il ne se range jamais dans l'une des deux par defaut.**

    **C'est le lien qui rend le registre transverse aux exercices visible.** Sur
    l'instance a deux exercices, les seuils de l'article 21 sont votes le
    03/07/2024 pour vingt-quatre mois; les engagements de depense soumis au vote
    de l'assemblee du 29/04/2026 tombent dans cette fenetre. Le lien traverse
    donc deux exercices sans qu'aucune requete ne prenne d'annee en parametre -
    ce que la premiere decision back demandait.

    `etats_par_date` vient de `_resolutions_registre.seuils_en_vigueur`, qui
    porte les nuances qu'un simple encadrement de dates perdrait: un seuil
    ancien sans terme qui reprendrait la main apres l'expiration d'un seuil plus
    recent, et deux seuils adoptes actifs a la meme date. Ces deux cas ne se
    tranchent pas ici - ils remplissent `doute`.
    """
    liste = list(actes)
    seuils = [
        a for a in liste
        if a["portee"] == PORTEE_SEUIL
        and a["resultat"] == RESULTAT_ADOPTEE
        and a["valide_du"]
    ]
    liens: list[dict[str, str]] = []
    for acte in liste:
        if acte["portee"] != PORTEE_ENGAGEMENT_DEPENSE or not acte["date_effet"]:
            continue
        date = acte["date_effet"]
        applicables = [
            s for s in seuils
            if s["valide_du"] <= date and (not s["valide_au"] or date <= s["valide_au"])
        ]
        if not applicables:
            continue
        etats = etats_par_date.get(date, [])
        doutes = [
            e["seuil"] for e in etats
            if e.get("reprise_seuil_anterieur") or e.get("seuils_concurrents")
        ]
        for seuil in sorted(applicables, key=lambda s: s["valide_du"]):
            norme, motif_norme = normes_par_acte.get(
                seuil["acte_id"], (NORME_NON_ATTRIBUEE, MOTIF_NORME_ABSENTE)
            )
            liens.append(
                _lien(
                    acte,
                    norme.relation,
                    KIND_ACTE,
                    seuil["acte_id"],
                    PROV_CALCUL,
                    FORCE_PIECE,
                    (
                        f"Article 21 alinea 2: {norme.phrase}. Ce montant a "
                        f"ete arrete le {seuil['date_effet']}"
                        + (
                            f" a {seuil['montant_autorise']} EUR"
                            if seuil["montant_autorise"]
                            else " sans montant lisible"
                        )
                        + (
                            f", pour une validite s'arretant le {seuil['valide_au']}."
                            if seuil["valide_au"]
                            else ", sans terme enonce."
                        )
                    ),
                    libelle_cible=(
                        f"{norme.libelle} du {seuil['date_effet']}, "
                        f"resolution {seuil['numero']}"
                    ),
                    doute=" ; ".join(
                        x for x in (
                            motif_norme,
                            (
                                "plusieurs seuils adoptes sont actifs a cette date: "
                                + ", ".join(doutes)
                                if doutes
                                else ""
                            ),
                        ) if x
                    ),
                )
            )
    return liens
