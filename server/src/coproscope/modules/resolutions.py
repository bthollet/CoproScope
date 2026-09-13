"""Extraction des resolutions d'un proces-verbal d'assemblee generale.

Ce module lit le texte deja extrait d'un PV et produit une ligne par
resolution, la ou `agscope` ne produit qu'une ligne par document avec un
compteur.

Il n'interprete pas: il constate ce que le PV ecrit. La qualification en acte
d'autorisation, les liens vers une delegation ou une urgence et les controles de
conformite sont hors de ce module.

Regle de prudence: aucune valeur n'est deduite quand le texte ne la porte pas.
Un champ vide est un fait, pas un echec.

Le travail est reparti en quatre responsabilites, chacune relisable seule:

- `_resolutions_motifs`     ce qui change d'un modele de PV a l'autre;
- `_resolutions_cloture`    l'axe: le texte enonce-t-il l'issue de CE vote;
- `_resolutions_calibrage`  trouver comment CE document numerote;
- `_resolutions_extraction` lire les champs une fois le gabarit connu;
- `_resolutions_registre`   compter, controler la coherence, ecrire.
"""

from __future__ import annotations

from ._resolutions_calibrage import calibrate, detect_family
from ._resolutions_cloture import (
    ANNEAU_AUCUN,
    ANNEAU_LARGE,
    ANNEAU_STRICT,
    CLOTURE_LARGE_RE,
    ancres,
    issues_muettes,
    locution_de_cloture,
)
from ._resolutions_extraction import Resolution, parse_resolutions, sequence_gaps
from ._resolutions_motifs import (
    ABSTENTION_RE,
    CLOTURE_RE,
    CONTRE_RE,
    ISSUE_ENONCEE_NON_LUE,
    ISSUE_NON_RECONNUE,
    ISSUE_PREFIXES,
    MINIMUM_SERIE,
    PARTICIPE_ISSUE_RE,
    MAJORITE_RE,
    NUMERO_RE,
    NUMERO_RE_A,
    NUMERO_RE_B_FLUX,
    NUMERO_RE_B_LIGNE,
    PASSERELLE_CITEE_RE,
    PASSERELLE_UTILISEE_RE,
    PAS_DE_VOTE,
    PAS_DE_VOTE_RE,
    POUR_RE,
    REPORTEE,
    RESOLUTION_FIELDS,
    SANS_ISSUE,
    SANS_OBJET,
    SIGNATURE_RE,
    VOIX_RE,
    VOTE_SANS_FORMULE,
)
from ._resolutions_registre import (
    NATURE_AUTRE,
    NATURE_CONVOCATION,
    NATURE_DEMANDE,
    NATURE_PV,
    NATURE_PV_ISSUES_NON_LUES,
    build_register,
    nature_assemblee,
    coherence,
    parse_file,
    seuils_en_vigueur,
    summarize,
    to_rows,
)

__all__ = [
    "ANNEAU_AUCUN",
    "ANNEAU_LARGE",
    "ANNEAU_STRICT",
    "CLOTURE_LARGE_RE",
    "CLOTURE_RE",
    "ISSUE_ENONCEE_NON_LUE",
    "ISSUE_NON_RECONNUE",
    "MINIMUM_SERIE",
    "NATURE_AUTRE",
    "NATURE_CONVOCATION",
    "NATURE_DEMANDE",
    "NATURE_PV",
    "NATURE_PV_ISSUES_NON_LUES",
    "PARTICIPE_ISSUE_RE",
    "ancres",
    "issues_muettes",
    "locution_de_cloture",
    "ISSUE_PREFIXES",
    "MAJORITE_RE",
    "NUMERO_RE",
    "PAS_DE_VOTE",
    "POUR_RE",
    "REPORTEE",
    "RESOLUTION_FIELDS",
    "Resolution",
    "SANS_ISSUE",
    "SANS_OBJET",
    "SIGNATURE_RE",
    "VOTE_SANS_FORMULE",
    "build_register",
    "nature_assemblee",
    "calibrate",
    "coherence",
    "detect_family",
    "parse_file",
    "parse_resolutions",
    "seuils_en_vigueur",
    "sequence_gaps",
    "summarize",
    "to_rows",
]
