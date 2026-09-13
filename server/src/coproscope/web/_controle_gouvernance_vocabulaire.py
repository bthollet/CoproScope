"""Le vocabulaire d'affichage de l'ecran de gouvernance, et ses bulles.

Extrait de `_controle_gouvernance_source` le 2026-09-06, en meme temps que les
cellules, parce que le module approchait la limite de 600 lignes et que quatre
lots a venir y ecrivent.

Ce module est **la racine des imports de l'ecran**: les cellules en dependent,
la construction des lignes en depend, et lui ne depend de rien de l'ecran. Le
sens est unique, et il doit le rester - un cycle d'import ne casse rien tant
qu'un appelant amorce les modules dans le bon ordre, puis casse tout au premier
decoupage suivant.
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


# --------------------------------------------------------------------------
# Vocabulaire d'affichage
# --------------------------------------------------------------------------

#: Les trois statuts publics de la grammaire commune (CC-IT-036, CC-IT-038),
#: plus le quatrieme que la typologie a rendu necessaire: `Non exige ici`. Sur
#: une urgence, l'avis du conseil syndical, la mise en concurrence et l'annexe
#: ne sont pas obligatoires - ecrire `absente` sur ces trois-la serait faux.
STATUTS_BULLE = {
    "disponible": "Source disponible",
    "confirmer": "À confirmer",
    "manquante": "Source manquante",
    "non_applicable": "Non exigé ici",
}

#: force probatoire du modele -> statut public. La coincidence des trois
#: premiers n'est pas fortuite: les deux vocabulaires ont ete concus pour dire
#: la meme chose, la force probatoire d'une source.
FORCE_VERS_STATUT = {
    A.FORCE_PIECE: "disponible",
    A.FORCE_AFFIRME: "confirmer",
    A.FORCE_ABSENT: "manquante",
    "NON_APPLICABLE": "non_applicable",
}

NATURES = {
    "RESOLUTION_AG": "Résolution d'assemblée",
    "DECISION_CS_DELEGUEE": "Décision du conseil syndical",
    "URGENCE_SYNDIC": "Dépense engagée en urgence",
}

#: Les onze types de la typologie. Le libelle est un libelle de lecteur, pas la
#: valeur de la colonne: aucun libelle brut au premier niveau (CC-IT-027).
PORTEES = {
    "ENGAGEMENT_DEPENSE": "Engagement de dépense",
    "APPROBATION_COMPTES": "Approbation des comptes",
    "BUDGET_PREVISIONNEL": "Budget prévisionnel",
    "FONDS_TRAVAUX": "Fonds de travaux",
    "DELEGATION_CS": "Délégation au conseil syndical",
    "SEUIL": "Seuil de l'article 21",
    "DESIGNATION_SYNDIC": "Désignation du syndic",
    "DESIGNATION_ORGANE": "Désignation à une fonction",
    "AUTORISATION_COPROPRIETAIRE": "Autorisation à un copropriétaire",
    "MODALITES": "Modalité d'organisation",
    "ORDINAIRE": "Type non reconnu",
}

#: Les six issues du modele des actes - `_actes_vocabulaire.RESULTATS` - et
#: rien d'autre: c'est la colonne `a.resultat` que cet ecran affiche, pas le
#: registre des resolutions. Un jeton de la voie resolutions ecrit ici serait
#: mort: il ne peut pas atteindre cette colonne, que `_pont_actes_source.ISSUES`
#: traduit d'abord.
#:
#: `ISSUE_NON_LUE` dit exactement le contraire de `SANS_ISSUE_TRACEE`, et les
#: deux libelles doivent le montrer sans jargon: dans un cas le document ne
#: conclut pas, dans l'autre il conclut et nous n'avons pas su le lire. Le
#: second n'est pas un constat sur la copropriete - c'est une relecture due.
RESULTATS = {
    "ADOPTEE": "Adoptée",
    "REJETEE": "Rejetée",
    "PAS_DE_VOTE": "Pas de vote",
    "VOTE_SANS_FORMULE": "Voix comptées, issue non énoncée",
    "SANS_ISSUE_TRACEE": "Le procès-verbal ne conclut pas",
    "ISSUE_NON_LUE": "Issue écrite, non lue par le logiciel, à relire",
}

#: La conclusion appartient a l'utilisateur, et elle vit en bout de ligne.
#: Le mot `validation` est interdit (CC-IT-046).
CONCLUSIONS = {
    "a_instruire": "À instruire",
    "QUESTION_POSEE": "Question posée",
    "CONTROLE_TRACE": "Contrôle tracé",
    "RESERVE": "Réserve posée",
}

#: Le motif de droit de chaque constat, en clair. Le motif brut de `v_constats`
#: cite deja la piece et la date; celui-ci dit ce que le lecteur doit en faire.
LIBELLES_CONSTAT = {
    "ACTE_SANS_FONDEMENT": "Aucune délégation en vigueur ne fonde cette décision",
    "OBLIGATION_NON_TENUE": "Obligation née après la décision, non tenue",
    "URGENCE_JAMAIS_PORTEE": "Urgence jamais portée devant une assemblée",
    "DELEGATION_EXPIREE": "Décision prise après l'expiration de la délégation",
    "PLAFOND_DEPASSE": "Plafond de délégation franchi en cumul",
    "ACTE_SANS_EXECUTION": "Voté, aucune dépense rattachée",
    "MONTANT_DIVERGENT": "Payé autrement que voté",
    "ISSUE_NON_ENONCEE": "Voix comptées, conclusion du vote absente",
    # Le seul libellé de cette table qui ne nomme pas un défaut de la
    # copropriété. Les autres disent ce qui manque au dossier ; celui-ci dit ce
    # que nous n'avons pas su lire dans une pièce qui, elle, est là. Écrire
    # « issue absente » ou « conclusion manquante » le rangerait parmi les
    # reproches au syndic, et ce serait faux.
    "ISSUE_NON_LUE_A_RELIRE": "Conclusion écrite au procès-verbal, non lue par le logiciel",
    "MAJORITE_NON_ENONCEE": "Aucune majorité énoncée",
    "PV_SANS_DATE_LUE": "Procès-verbal dont la date d'assemblée n'a pas été lue",
}

#: Les constats qui portent sur une depense ou un document, pas sur un acte.
#: Ils ne font pas de ligne ici: l'aiguillage 44/45 et la T.V.A. vivent sur
#: l'ecran comptes (blueprint 3.2). Ils sont comptes et nommes, pas caches.
CONSTATS_HORS_ECRAN = {
    "EURO_SANS_ACTE": "dépenses hors budget prévisionnel qu'aucun acte ne couvre",
    "IMPUTATION_A_TRANCHER": "dépenses dont l'imputation reste à trancher",
    "TVA_INCOHERENTE": "écarts entre la T.V.A. retenue et celle annoncée",
}

#: L'ordre de gravite d'un statut de cellule. Une preuve absente ne se compense
#: pas par une preuve fournie a cote: le statut filtrable d'une colonne qui
#: porte plusieurs bulles est le plus defavorable de ses bulles. `non_exige` ne
#: compte pas - ce n'est ni un manque ni une preuve.
ORDRE_STATUT = ("manquante", "confirmer", "disponible", "non_applicable")


def pire_statut(bulles: Iterable[dict[str, Any]]) -> str:
    """Le statut filtrable d'une colonne qui porte plusieurs bulles.

    **Les sous-bulles comptent.** L'annexe est une sous-bulle de la resolution
    qui y renvoie, mais c'est une preuve comme une autre: une annexe visee et
    absente rend la colonne incomplete. L'oublier ici rangerait la ligne parmi
    celles que rien ne contredit - un faux calme, qui est le pire des defauts
    de cet ecran.
    """
    pire = ""
    for bulle in bulles or ():
        for candidate in [bulle, *(bulle.get("sous") or ())]:
            statut = candidate.get("statut", "")
            if statut == "non_applicable":
                continue
            if not pire or ORDRE_STATUT.index(statut) < ORDRE_STATUT.index(pire):
                pire = statut
    return pire or "non_applicable"


def euros(valeur: Any) -> str:
    """`18 240,00 EUR`, jamais `18240.0` (blueprint 3.1)."""
    try:
        montant = float(valeur)
    except (TypeError, ValueError):
        return ""
    entier, _, decimales = f"{montant:,.2f}".partition(".")
    return entier.replace(",", " ") + "," + decimales + " EUR"


def _bulle(
    statut: str,
    texte: str,
    detail: str = "",
    *,
    sous: list[dict[str, Any]] | None = None,
    legifrance: str = "",
    citation: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Une bulle, et **d'ou vient ce qu'elle affirme**.

    `citation` vaut `None` quand il n'y a rien a citer, et c'est un etat a part
    entiere: une cellule sans lien n'a aucune source a montrer, ce qui n'est pas
    la meme chose qu'une source dont la page n'a pas ete notee. Le gabarit doit
    pouvoir distinguer les deux, donc la cle existe toujours.
    """
    return {
        "statut": statut,
        "statut_libelle": STATUTS_BULLE[statut],
        "texte": texte,
        "detail": detail,
        "sous": sous or [],
        "legifrance": legifrance,
        "citation": citation,
    }


def _cellule(
    valeur: str,
    portee: str,
    controle: str,
    libelles: dict[str, str],
    *,
    legifrance: str = "",
    citation: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Une cellule de la matrice, traduite en bulle.

    `NON_APPLICABLE` porte le motif de droit du retrait, jamais un blanc:
    retirer un controle sans dire pourquoi serait la meme faute que de
    l'afficher a tort - dans les deux cas le lecteur ne peut pas prendre le
    controle en defaut.

    `controle` vide signifie **cette cellule n'est pas un des sept controles**:
    c'est le cas du texte de la resolution, qui rapporte ce que le document dit
    et ne verifie rien. Passer un nom invente a la place - `RESOLUTION` l'etait -
    faisait interroger la matrice des retraits avec une cle qu'elle ne connait
    pas, ce qui rend toujours la chaine vide, donc toujours le motif generique.
    """
    statut = FORCE_VERS_STATUT.get(valeur, "manquante")
    if statut == "non_applicable":
        motif = motif_hors_controle(portee, controle) if controle else ""
        # Un controle retire n'a pas de source a citer: la question ne se pose
        # pas. Laisser passer une citation ici ferait pointer une page a cote
        # de la phrase `non exige ici`, ce qui se lirait comme une exigence.
        return _bulle(
            statut,
            libelles["nom"] + " : non exigé ici",
            motif or "Ce contrôle n'a pas d'objet sur ce type.",
            legifrance=legifrance,
        )
    return _bulle(statut, libelles["nom"], libelles.get(statut, ""),
                  legifrance=legifrance, citation=citation)
