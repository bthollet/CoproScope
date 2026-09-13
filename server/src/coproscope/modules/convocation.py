"""Lecture des convocations d'assemblee generale.

Facade du lot. Le detail vit dans quatre modules, decoupes par responsabilite:

    _convocation_motifs      le vocabulaire, ce qui change d'un gabarit a l'autre
    _convocation_extraction  texte -> objets, pur, sans aucune ecriture
    _convocation_controles   de quoi l'extraction se refute elle-meme
    _convocation_registre    la seule porte d'ecriture, confrontation comprise

Ce que la convocation apporte et que le proces-verbal n'a pas: elle annonce ce
qu'elle contient, donc elle se verifie sans etalon manuel; elle porte des
projets et jamais des votes; et elle declare parfois ce qu'une autre assemblee
a decide - contestation, rejeu - ce qui rend ces liens suivables au lieu d'etre
devines.
"""

from __future__ import annotations

from ._convocation_controles import (
    affirmations_sans_piece,
    controles,
    enumeration,
    quantification,
    references_a_resoudre,
    sequence,
)
from ._convocation_extraction import (
    Convocation,
    DeclarationSurAG,
    DevisCite,
    Point,
    TotalAnnonce,
    annexes_citees,
    declarations_sur_ag,
    devis_cites,
    parse_convocation,
    points_annonces,
    totaux_annonces,
)
from ._convocation_motifs import (
    CONVOCATION_FIELDS,
    DECLARATION_FIELDS,
    DEVIS_CITE_FIELDS,
    NATURE_CONTESTATION,
    NATURE_REJEU,
    ORIGINE_CORRIGE,
    ORIGINE_EXTRAIT,
    PORTEE_PARTIELLE,
    PORTEE_TOTALE,
    PRIX_NON_LU,
    PRIX_NON_QUANTIFIE,
    PRIX_QUANTIFIE,
)
from ._convocation_calibrage import Signature, calibrer
from ._convocation_nature import (
    ETAT_CONSTATEE,
    ETAT_ILLISIBLE,
    ETAT_INDETERMINE,
    ETAT_PROJETEE,
    Nature,
    nature_du_document,
)
from ._convocation_store import (
    GouvernanceStoreIndisponible,
    lire,
    remplacer_pour_documents,
    store_path,
)
from ._convocation_registre import (
    TYPE_CONVOCATION,
    build_register,
    confronter,
    pages_du_document,
)

__all__ = [
    "CONVOCATION_FIELDS",
    "DECLARATION_FIELDS",
    "DEVIS_CITE_FIELDS",
    "NATURE_CONTESTATION",
    "NATURE_REJEU",
    "ORIGINE_CORRIGE",
    "ORIGINE_EXTRAIT",
    "PORTEE_PARTIELLE",
    "PORTEE_TOTALE",
    "PRIX_NON_LU",
    "PRIX_NON_QUANTIFIE",
    "PRIX_QUANTIFIE",
    "TYPE_CONVOCATION",
    "Convocation",
    "ETAT_CONSTATEE",
    "ETAT_ILLISIBLE",
    "ETAT_INDETERMINE",
    "ETAT_PROJETEE",
    "Nature",
    "Signature",
    "calibrer",
    "nature_du_document",
    "GouvernanceStoreIndisponible",
    "DeclarationSurAG",
    "DevisCite",
    "Point",
    "TotalAnnonce",
    "affirmations_sans_piece",
    "annexes_citees",
    "build_register",
    "confronter",
    "controles",
    "declarations_sur_ag",
    "devis_cites",
    "enumeration",
    "lire",
    "pages_du_document",
    "parse_convocation",
    "points_annonces",
    "quantification",
    "remplacer_pour_documents",
    "references_a_resoudre",
    "sequence",
    "store_path",
    "totaux_annonces",
]
