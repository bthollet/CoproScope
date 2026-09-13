"""Les controles croises du decompte: seuils, coherence, issue proclamee.

Extrait de `_decompte_voix` le 2026-09-04. Ce module ne rend aucun verdict: il
rend des **faits nommes**, sous forme de chaines, que le verdict porte ensuite.

Trois familles, et le defaut que chacune ferme.

**Les seuils.** Ils etaient deja la. Ils ne changent pas.

**La coherence.** Le module disposait de la presence et du total du syndicat, et
ne s'en servait que comme denominateurs. Un decompte OCRise de travers - un
chiffre colle, un separateur de milliers avale - rendait un verdict de forme
normale: 6 000 voix pour dans une assemblee ou 4 899 seulement sont presentes
donnait 98,36 % d'adoption confirmee, plausible a l'ecran et arithmetiquement
impossible. Les nombres qui ne peuvent pas etre tous vrais sont desormais un
constat, pas un pourcentage.

**L'issue proclamee.** Elle n'etait lue que sous l'article 25, et par un
`startswith("adopt")`. Deux consequences mesurees: aucun etat n'existait pour
"le decompte contredit l'issue proclamee" hors de l'article 25, et une
resolution que le proces-verbal declare non soumise au vote etait comptee comme
une irregularite du syndic au regard de l'article 17 du decret. Le vocabulaire
lu ici est celui de l'extracteur (`PAS_DE_VOTE`, `SANS_OBJET`, `REPORTEE`,
`PROJET`) **et** celui des proces-verbaux en clair.

Aucune donnee nominative ne transite par ce module: il ne manipule que des
totaux de voix et un mot d'issue.
"""

from __future__ import annotations

import re
import unicodedata
from typing import Optional

# --------------------------------------------------------------------------
# Les seuils
# --------------------------------------------------------------------------


def voix_exprimees(
    voix_pour: Optional[int], voix_contre: Optional[int]
) -> Optional[int]:
    """Les voix exprimees: le pour et le contre, jamais les abstentions.

    Rend `None` si l'une des deux manque - une somme partielle serait une base
    fausse, pas une base approchee.
    """

    if voix_pour is None or voix_contre is None:
        return None
    return int(voix_pour) + int(voix_contre)


def seuil_majorite_absolue(voix_totales: Optional[int]) -> Optional[int]:
    """Le nombre de voix minimal pour depasser la moitie de `voix_totales`."""

    if voix_totales is None or voix_totales <= 0:
        return None
    return int(voix_totales) // 2 + 1


def seuil_passerelle_25_1(voix_totales: Optional[int]) -> Optional[int]:
    """Le tiers des voix de tous les coproprietaires, arrondi au superieur.

    "au moins le tiers de ces voix": un tiers exact suffit, une fraction en
    dessous ne suffit pas.
    """

    if voix_totales is None or voix_totales <= 0:
        return None
    total = int(voix_totales)
    return -(-total // 3)


def seuil_deux_tiers(voix_totales: Optional[int]) -> Optional[int]:
    """Les deux tiers des voix, arrondis au superieur: "au moins les deux tiers"."""

    if voix_totales is None or voix_totales <= 0:
        return None
    total = int(voix_totales)
    return -(-2 * total // 3)


def passerelle_25_1_ouverte(
    voix_pour: Optional[int], voix_totales: Optional[int]
) -> Optional[bool]:
    """Le projet a-t-il recueilli au moins le tiers des voix de tous ?

    C'est la condition du premier alinea de l'article 25-1. Elle ne dit pas que
    la resolution est adoptee: elle dit que la meme assemblee **peut** proceder
    immediatement a un second vote a la majorite de l'article 24.
    """

    seuil = seuil_passerelle_25_1(voix_totales)
    if seuil is None or voix_pour is None:
        return None
    return int(voix_pour) >= seuil


def majorite_25_atteignable(
    voix_presentes: Optional[int], voix_totales: Optional[int]
) -> Optional[bool]:
    """L'article 25 est-il arithmetiquement atteignable avec cette presence ?

    L'article 25 exige plus de la moitie des voix de **tous** les
    coproprietaires. Si les presents, representes et votants par correspondance
    ne totalisent pas plus de la moitie du syndicat, aucune resolution ne peut
    l'atteindre, quel que soit le vote.

    Mesure qui fonde ce predicat: sur le proces-verbal etalon, la feuille de
    presence totalise 4 899 voix sur 10 000. Les vingt et une resolutions
    annoncees sous les articles 25 et 25-1 plafonnent a 4 794 voix pour -
    **aucune** n'atteint 5 001. Le predicat rend donc `False`, et les dix-huit
    adoptions ne s'expliquent que par la passerelle de l'article 25-1.

    **Portee reelle, a ne pas taire.** Cette fonction n'a **aucun appelant**
    hors de ce module et de ses tests. C'est la moitie du constat C074 qui
    reste vraie: le fait etalon qu'elle sait calculer - avec 4 899 voix
    presentes sur 10 000, l'article 25 etait arithmetiquement hors d'atteinte -
    n'est affiche sur aucun ecran. `constat_hors_atteinte` porte le meme fait
    dans les verdicts des articles 25 et 26, mais seulement quand l'appelant
    passe `voix_presentes`, ce que le pont de production ne fait pas. Tant que
    ce cablage manque, le predicat reste un outil de mesure, pas un controle en
    service.
    """

    if voix_presentes is None or voix_totales is None or voix_totales <= 0:
        return None
    return int(voix_presentes) * 2 > int(voix_totales)


def constat_hors_atteinte(
    voix_presentes: Optional[int],
    seuil: Optional[int],
    base: Optional[int],
    article: str,
) -> Optional[str]:
    """Le seuil etait-il hors d'atteinte compte tenu de la presence ?

    Vaut pour tout seuil calcule sur les voix du syndicat: la moitie de
    l'article 25 comme les deux tiers de l'article 26. La branche de l'article
    26 ne posait pas la question, alors que c'est celle ou le seuil est le plus
    haut et donc le plus surement inatteignable.
    """

    if voix_presentes is None or seuil is None or base is None:
        return None
    if int(voix_presentes) >= int(seuil):
        return None
    return (
        f"la feuille de presence totalise {int(voix_presentes)} voix sur "
        f"{int(base)}: le seuil de {int(seuil)} voix de l'article {article} est "
        "arithmetiquement hors d'atteinte pour toute resolution de cette "
        "assemblee"
    )


def constat_denominateur(
    denominateur_ecrit: Optional[int], base_retenue: Optional[int]
) -> Optional[str]:
    """Confronte le denominateur imprime a l'assiette deduite du texte.

    La divergence n'est pas une erreur du proces-verbal: c'est une modalite
    d'ecriture, mesuree sur les deux cabinets. Elle devient un constat parce
    qu'un lecteur qui prendrait le nombre imprime pour l'assiette calculerait un
    pourcentage faux.
    """

    if denominateur_ecrit is None or base_retenue is None:
        return None
    if int(denominateur_ecrit) == int(base_retenue):
        return None
    return (
        f"le proces-verbal imprime le vote sur {int(denominateur_ecrit)}, "
        f"l'assiette imposee par la majorite annoncee est {int(base_retenue)}; "
        "le denominateur imprime est une modalite d'ecriture et ne fonde pas "
        "le pourcentage"
    )


# --------------------------------------------------------------------------
# La coherence des nombres lus
# --------------------------------------------------------------------------


#: Un nombre de voix tel que l'extracteur l'ecrit: `_nombre` retire deja les
#: espaces et les points de milliers et rend une suite de chiffres, ou "".
#: Le signe est accepte pour que la valeur negative soit **lue**, puis nommee
#: par `incoherences` - la refuser ici la ferait passer pour illisible alors
#: qu'elle est parfaitement lisible et fausse.
_VOIX_ECRITES_RE = re.compile(r"^[+-]?\d+$")

#: Les separateurs de milliers qu'une valeur relue ou corrigee a la main peut
#: encore porter. Le point n'y est pas: entre le millier francais et la
#: decimale anglaise il est ambigu, et deviner y vaudrait 10 voix pour 10.000.
_ESPACES_DE_MILLIERS = (" ", " ", " ", " ")


#: Le controle croise abandonne quand le scrutin est restreint, et pourquoi.
#: Un controle qu'on renonce a conduire se declare: le taire laisserait croire
#: que le rapprochement a ete fait et qu'il tombe juste.
CONSTAT_CONTROLE_CROISE_NON_CONDUIT = (
    "le vote a lieu sur une cle speciale: le total des voix est celui de cette "
    "cle, tandis que la feuille de presence porte les tantiemes generaux. Le "
    "rapprochement des deux n'a pas de sens et n'a pas ete conduit"
)


def lire_voix(nom: str, valeur: object) -> tuple[Optional[int], Optional[str]]:
    """Traduit une valeur venue de l'extracteur en nombre de voix.

    Le contrat de types entre l'extracteur et ce module n'etait pas defendu.
    `Resolution.voix_pour` est declare `str = ""` et la chaine vide y signifie
    exactement "le proces-verbal ne publie pas les voix". Mesures d'origine:

        voix_pour=""            -> ValueError, au lieu de DECOMPTE_ABSENT
        voix_totales="10000"    -> TypeError sur la comparaison au zero
        voix_pour=100.9         -> tronque a 100, sans un mot

    Rend `(valeur, motif)`. Trois issues, et aucune n'est une exception:

    - **absente** - `None`, chaine vide ou blanche - rend `(None, None)`. C'est
      le "non publie" que l'appelant sait deja lire;
    - **lisible** - un entier, ou une chaine de chiffres - rend `(entier,
      None)`;
    - **ecrite et illisible** - rend `(None, motif)`. Une valeur qu'on ne sait
      pas lire n'est pas une valeur absente: les confondre deplacerait le repli
      muet d'une case au lieu de le fermer. Le motif nomme le champ et
      restitue la valeur telle qu'elle a ete lue.

    Le booleen est refuse explicitement. `True` est un entier en Python: sans
    ce garde, un drapeau egare valait une voix pour.
    """

    if valeur is None:
        return None, None

    if isinstance(valeur, bool):
        return None, _motif_illisible(nom, valeur, "un drapeau n'est pas un nombre de voix")

    if isinstance(valeur, int):
        return valeur, None

    if isinstance(valeur, float):
        if valeur.is_integer():
            return int(valeur), None
        return None, _motif_illisible(
            nom, valeur, "un nombre de voix n'a pas de partie decimale"
        )

    if isinstance(valeur, str):
        texte = valeur.strip()
        if not texte:
            return None, None
        for espace in _ESPACES_DE_MILLIERS:
            texte = texte.replace(espace, "")
        if _VOIX_ECRITES_RE.match(texte):
            return int(texte), None
        return None, _motif_illisible(
            nom, valeur, "la valeur lue ne s'ecrit pas en chiffres"
        )

    return None, _motif_illisible(
        nom, valeur, f"le type lu est {type(valeur).__name__}"
    )


def _motif_illisible(nom: str, valeur: object, raison: str) -> str:
    return (
        f"{nom}: la valeur \"{valeur}\" ne peut pas etre lue comme un nombre "
        f"de voix - {raison}. Le controle n'est pas conduit sur cette "
        "resolution; la valeur n'est ni supposee nulle, ni tenue pour absente"
    )


def incoherences(
    voix_pour: Optional[int] = None,
    voix_contre: Optional[int] = None,
    voix_abstention: Optional[int] = None,
    voix_presentes: Optional[int] = None,
    voix_totales: Optional[int] = None,
    cle_speciale: bool = False,
) -> list[str]:
    """Les nombres lus peuvent-ils etre tous vrais en meme temps ?

    Rend la liste des contradictions constatees, vide quand il n'y en a pas.
    Chaque phrase affiche **les deux nombres** qui s'opposent: un lecteur doit
    pouvoir refaire le rapprochement sur le proces-verbal sans l'outil.

    C'est ici que `voix_abstention` cesse d'etre un parametre mort. Il n'entre
    dans aucune assiette - une abstention n'est pas une voix exprimee - mais il
    entre dans le seul controle croise dont ce module ait les elements: la somme
    du pour, du contre et des abstentions ne peut pas depasser la feuille de
    presence. C'est l'arithmetique que le cabinet B publie et qui tombe juste:
    30 725 + 4 570 + 741 = 36 036.

    `cle_speciale` desarme les deux controles qui melangent alors deux unites.
    Quand le vote est reserve aux coproprietaires concernes, `voix_totales` est
    le total de **leur** cle et la feuille de presence porte les tantiemes
    **generaux**: confronter l'une a l'autre faisait dire "la feuille de
    presence depasse le total des voix du syndicat" a un decompte parfaitement
    coherent. Les deux controles qui restent - une valeur negative, et un pour
    superieur au total de sa propre cle - portent sur des nombres de meme
    unite et ne sont pas desarmes. Le controle abandonne n'est pas passe sous
    silence: `decompte_resolution` en fait un constat.
    """

    faits: list[str] = []
    for nom, valeur in (
        ("les voix pour", voix_pour),
        ("les voix contre", voix_contre),
        ("les abstentions", voix_abstention),
        ("la feuille de presence", voix_presentes),
        ("le total des voix du syndicat", voix_totales),
    ):
        if valeur is not None and int(valeur) < 0:
            faits.append(
                f"{nom} valent {int(valeur)}: un nombre de voix ne peut pas "
                "etre negatif, la valeur lue n'est pas un decompte"
            )

    total = None if voix_totales is None else int(voix_totales)
    if total is not None and total > 0:
        if voix_pour is not None and int(voix_pour) > total:
            faits.append(
                f"les voix pour ({int(voix_pour)}) depassent le total des voix "
                f"du syndicat ({total})"
            )
        if (
            not cle_speciale
            and voix_presentes is not None
            and int(voix_presentes) > total
        ):
            faits.append(
                f"la feuille de presence ({int(voix_presentes)}) depasse le "
                f"total des voix du syndicat ({total})"
            )

    if not cle_speciale and voix_presentes is not None and int(voix_presentes) >= 0:
        lues = [v for v in (voix_pour, voix_contre, voix_abstention) if v is not None]
        somme = sum(int(v) for v in lues)
        if lues and somme > int(voix_presentes):
            faits.append(
                f"les voix lues sous cette resolution totalisent {somme} "
                f"(pour, contre et abstentions) alors que la feuille de "
                f"presence en porte {int(voix_presentes)}"
            )
    return faits


# --------------------------------------------------------------------------
# L'issue proclamee au proces-verbal
# --------------------------------------------------------------------------

#: Le proces-verbal proclame l'adoption.
ISSUE_ADOPTEE = "ADOPTEE"

#: Le proces-verbal proclame le rejet.
ISSUE_REJETEE = "REJETEE"

#: Le proces-verbal enonce que la question n'a pas ete mise aux voix. Ce n'est
#: pas une absence de decompte: c'est un fait constate sur le document.
ISSUE_SANS_VOTE = "SANS_VOTE"

#: Rien de lisible. Distinct de `ISSUE_SANS_VOTE`: "on ne sait pas" n'est pas
#: "le document dit qu'il n'y a pas eu de vote".
ISSUE_INCONNUE = ""

#: Prefixes reconnus, apres normalisation. Le vocabulaire de l'extracteur et
#: celui des proces-verbaux sont lus par la meme table, faute de quoi le module
#: recevrait `PAS_DE_VOTE` sans savoir le lire.
_PREFIXES_ISSUE: tuple[tuple[str, str], ...] = (
    ("adopt", ISSUE_ADOPTEE),
    ("approuv", ISSUE_ADOPTEE),
    ("rejet", ISSUE_REJETEE),
    ("rejat", ISSUE_REJETEE),  # coquille d'OCR rencontree au corpus
    ("refus", ISSUE_REJETEE),
    ("repouss", ISSUE_REJETEE),
    ("pas de vote", ISSUE_SANS_VOTE),
    ("sans vote", ISSUE_SANS_VOTE),
    ("sans objet", ISSUE_SANS_VOTE),
    ("non soumis", ISSUE_SANS_VOTE),
    ("report", ISSUE_SANS_VOTE),
    ("ajourn", ISSUE_SANS_VOTE),
    ("projet", ISSUE_SANS_VOTE),
)


def _sans_accents(texte: str) -> str:
    decompose = unicodedata.normalize("NFKD", texte)
    return "".join(car for car in decompose if not unicodedata.combining(car))


def issue_proclamee(issue_annoncee: Optional[str]) -> str:
    """Ce que le proces-verbal proclame, ramene a quatre valeurs.

    Rend `ISSUE_ADOPTEE`, `ISSUE_REJETEE`, `ISSUE_SANS_VOTE` ou
    `ISSUE_INCONNUE`. Un libelle non reconnu rend `ISSUE_INCONNUE` et jamais une
    valeur par defaut: le decompte n'est alors confronte a rien, ce qui est un
    resultat, pas une confirmation.
    """

    if issue_annoncee is None:
        return ISSUE_INCONNUE
    texte = _sans_accents(str(issue_annoncee)).lower().replace("_", " ")
    texte = re.sub(r"\s+", " ", texte).strip()
    if not texte:
        return ISSUE_INCONNUE
    for prefixe, issue in _PREFIXES_ISSUE:
        if texte.startswith(prefixe):
            return issue
    return ISSUE_INCONNUE
