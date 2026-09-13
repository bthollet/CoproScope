"""Les regimes de majorite: ce que la loi impose de compter.

Extrait de `_decompte_voix` le 2026-09-04, pour que la table des regimes se
relise seule et que le module de calcul reste sous la limite de taille du
depot. Le contenu n'a pas change de sens: **ce tableau reste le seul endroit ou
une assiette se decide.**

Sources lues sur Legifrance via PISTE le 2026-09-04, fonds `LODA_DATE`, filtre
de date pose au jour de la lecture. `VIGUEUR` signifie "en vigueur a la date
demandee", jamais "a jour": la date de version fait partie de la citation.

Aucune donnee nominative ne transite par ce module.
"""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass
from typing import Optional

# --------------------------------------------------------------------------
# Les assiettes, et le texte qui les impose
# --------------------------------------------------------------------------

#: Les voix exprimees des coproprietaires presents, representes ou ayant vote
#: par correspondance. Les abstentions n'en font pas partie: elles ne sont pas
#: des voix exprimees.
ASSIETTE_VOIX_EXPRIMEES = "VOIX_EXPRIMEES"

#: Les voix de tous les coproprietaires du syndicat, presents ou non.
ASSIETTE_TOUTES_LES_VOIX = "TOUTES_LES_VOIX"

#: Deux conditions cumulatives: une majorite en nombre de membres du syndicat
#: ET les deux tiers des voix. Le nombre de membres est une donnee que les
#: proces-verbaux du corpus ne publient pas systematiquement.
ASSIETTE_DOUBLE = "DOUBLE_MAJORITE"

#: La totalite des voix du syndicat, sans exception. Elle se distingue de
#: `ASSIETTE_TOUTES_LES_VOIX` par son seuil, pas par sa base: l'article 25 se
#: compte sur toutes les voix mais se gagne a la moitie plus une, et il ouvre
#: la passerelle de l'article 25-1. L'unanimite ne se gagne qu'a la totalite et
#: n'ouvre aucun second vote.
ASSIETTE_UNANIMITE = "UNANIMITE"

ASSIETTES = (
    ASSIETTE_VOIX_EXPRIMEES,
    ASSIETTE_TOUTES_LES_VOIX,
    ASSIETTE_DOUBLE,
    ASSIETTE_UNANIMITE,
)

MAJORITE_24 = "24"
MAJORITE_25 = "25"
MAJORITE_25_1 = "25-1"
MAJORITE_26 = "26"

#: L'unanimite des voix de tous les coproprietaires. Ce n'est pas un article de
#: plus dans la serie 24-26: c'est le seuil que l'article 26 dernier alinea
#: reserve a certains objets - l'alienation de parties communes necessaires au
#: respect de la destination de l'immeuble, la modification de cette
#: destination. Le module ne comptait que jusqu'aux deux tiers: une resolution
#: soumise a l'unanimite passait `ADOPTEE_CONFIRMEE` des les deux tiers
#: atteints, et le mot "unanimite" n'apparaissait nulle part dans le module.
MAJORITE_UNANIMITE = "unanimite"


@dataclass(frozen=True)
class Regime:
    """Ce que la loi impose de compter pour une majorite donnee."""

    majorite: str
    assiette: str
    enonce: str
    sources: tuple

    def __str__(self) -> str:  # pragma: no cover - confort de lecture
        return f"article {self.majorite}: {self.enonce}"


#: majorite -> regime. **Ce tableau est le seul endroit ou une assiette se
#: decide.** Toute autre fonction du module le lit; aucune ne le contourne.
REGIMES = {
    MAJORITE_24: Regime(
        majorite=MAJORITE_24,
        assiette=ASSIETTE_VOIX_EXPRIMEES,
        enonce=(
            "majorite des voix exprimees des coproprietaires presents, "
            "representes ou ayant vote par correspondance"
        ),
        sources=(("loi 65-557, art. 24 I", "LEGIARTI000051749514"),),
    ),
    MAJORITE_25: Regime(
        majorite=MAJORITE_25,
        assiette=ASSIETTE_TOUTES_LES_VOIX,
        enonce="majorite des voix de tous les coproprietaires",
        sources=(("loi 65-557, art. 25", "LEGIARTI000051749507"),),
    ),
    MAJORITE_25_1: Regime(
        majorite=MAJORITE_25_1,
        assiette=ASSIETTE_VOIX_EXPRIMEES,
        enonce=(
            "second vote immediat a la majorite de l'article 24, ouvert "
            "seulement si le projet a recueilli au moins le tiers des voix de "
            "tous les coproprietaires"
        ),
        sources=(
            ("loi 65-557, art. 25-1", "LEGIARTI000049398359"),
            ("loi 65-557, art. 24 I", "LEGIARTI000051749514"),
        ),
    ),
    MAJORITE_26: Regime(
        majorite=MAJORITE_26,
        assiette=ASSIETTE_DOUBLE,
        enonce=(
            "majorite des membres du syndicat representant au moins les deux "
            "tiers des voix"
        ),
        sources=(("loi 65-557, art. 26", "LEGIARTI000050623612"),),
    ),
    MAJORITE_UNANIMITE: Regime(
        majorite=MAJORITE_UNANIMITE,
        assiette=ASSIETTE_UNANIMITE,
        enonce="unanimite des voix de tous les coproprietaires",
        sources=(("loi 65-557, art. 26 dernier alinea", "LEGIARTI000050623612"),),
    ),
}

#: Le nombre de voix d'un coproprietaire suit sa quote-part de parties
#: communes, et il est reduit quand il detient plus de la moitie.
SOURCE_VOIX = ("loi 65-557, art. 22 I", "LEGIARTI000039313531")

#: Quand le reglement met certaines depenses a la seule charge de certains
#: coproprietaires, il peut prevoir qu'eux seuls votent, avec un nombre de voix
#: proportionnel a leur participation. C'est le fondement des scrutins par cle
#: speciale - `VOTE AUX TANTIEMES ENTREE` chez le cabinet A, `Base de
#: repartition: CHARGES BATIMENT B` chez le cabinet B.
SOURCE_CLE_SPECIALE = ("loi 65-557, art. 10 dernier alinea", "LEGIARTI000043977284")

#: La feuille de presence porte, pour chaque coproprietaire, le nombre de voix
#: dont il dispose, et elle est annexee au proces-verbal.
SOURCE_FEUILLE_PRESENCE = ("decret 67-223, art. 14", "LEGIARTI000042078670")
SOURCE_FEUILLE_ANNEXEE = ("decret 67-223, art. 17", "LEGIARTI000042078689")

#: Le votant par correspondance ayant vote favorablement est assimile a un
#: coproprietaire defaillant si la resolution est amendee en seance.
SOURCE_CORRESPONDANCE_AMENDEE = (
    "loi 65-557, art. 17-1 A al. 2",
    "LEGIARTI000039313644",
)

#: Le formulaire de vote par correspondance n'est pas pris en compte lorsque le
#: coproprietaire ou son mandataire est present au moment du vote. Cette regle
#: se joue dans la construction de la feuille de presence, en amont de ce
#: module: elle est citee ici comme source, jamais recalculee.
SOURCE_CORRESPONDANCE_PRESENT = ("decret 67-223, art. 14-1", "LEGIARTI000042076720")


def sources_du_scrutin(
    regime: "Regime",
    cle_speciale: bool = False,
    presence_lue: bool = False,
    correspondance_lue: bool = False,
) -> tuple:
    """Les textes qui fondent ce scrutin-la, et pas seulement sa majorite.

    Comptage du 2026-09-04: cinq des six constantes de source n'avaient qu'une
    occurrence dans le module, leur propre definition. Un verdict rendu sur un
    scrutin par cle speciale portait `('loi 65-557, art. 24 I', ...)` et rien
    d'autre - ni l'article 22 I, qui dit ce qu'est une voix et donc ce que
    comptent tous ces nombres, ni l'article 10 dernier alinea, qui est le
    fondement meme du scrutin restreint. Une interface qui affiche
    `verdict.sources` ne pouvait donc jamais montrer ces fondements.

    Trois regles, et aucune n'est deduite d'un nombre imprime:

    - l'article 22 I accompagne **tout** verdict de ce module: il n'y a pas de
      decompte de voix qui ne repose pas sur lui;
    - l'article 10 dernier alinea n'est cite que si l'appelant **declare** le
      scrutin par cle speciale. Le deduire du denominateur imprime
      contredirait la doctrine centrale du module - le nombre imprime a cote
      d'un vote n'est pas l'assiette legale de ce vote;
    - l'article 14 du decret n'est cite que si une feuille de presence a
      reellement ete lue, et l'article 14-1 que si un vote par correspondance
      a reellement ete pris en compte.

    L'ordre de citation est stable et aucune source n'apparait deux fois.
    """

    citees: list[tuple] = list(regime.sources)
    ajouts = [SOURCE_VOIX]
    if cle_speciale:
        ajouts.append(SOURCE_CLE_SPECIALE)
    if presence_lue:
        ajouts.append(SOURCE_FEUILLE_PRESENCE)
    if correspondance_lue:
        ajouts.append(SOURCE_CORRESPONDANCE_PRESENT)
    for source in ajouts:
        if source not in citees:
            citees.append(source)
    return tuple(citees)


# `Article 24`, `art. 25`, `Articles n° 26`: le mot, l'abreviation, le signe
# numero et les espaces sont du bruit d'ecriture. Ils ne portent aucun sens
# juridique et ne doivent pas faire manquer un regime enonce.
_BRUIT_MAJORITE_RE = re.compile(r"(?i)^\s*(?:articles?|art\.?)\s*(?:n[°o]\s*)?")


def normaliser_majorite(majorite: Optional[str]) -> str:
    """Retire le bruit d'ecriture d'une majorite enoncee, et rien de plus.

    **Ce qui est retire n'a aucun sens juridique**: le mot `article`, son
    abreviation, le signe numero, la casse et les espaces. Ce qui reste est
    conserve tel quel - en particulier la lettre d'un `25 B`, qui distingue des
    regimes de l'article 25 et n'est donc pas du bruit. Un `25B` ressort `25B`
    et n'est pas ramene a `25`: il sera refuse en nommant son motif reel.
    """

    if majorite is None:
        return ""
    texte = _BRUIT_MAJORITE_RE.sub("", str(majorite).strip())
    return re.sub(r"\s+", "", texte)


def regime_de_majorite(majorite: Optional[str]) -> Optional[Regime]:
    """Rend le regime d'une majorite, ou `None` si elle n'est pas reconnue.

    `None` est un resultat, pas un echec: une resolution dont la majorite n'est
    pas enoncee existe dans le corpus, et l'ecran doit le dire au lieu de
    supposer l'article 24.

    `None` couvre cependant deux situations que l'appelant doit separer: la
    majorite n'est **pas enoncee**, ou elle est enoncee et **non reconnue** par
    cette table. `majorite_enoncee` permet de les distinguer.
    """

    cle = normaliser_majorite(majorite)
    regime = REGIMES.get(cle)
    if regime is not None:
        return regime
    # Les regimes chiffres se lisent tels quels; celui qui s'ecrit en lettres
    # arrive accentue et capitalise de facons variees ("Unanimite",
    # "UNANIMITE", "unanimite"). On replie donc accents et casse en second
    # recours seulement: `normaliser_majorite` doit continuer de rendre "25B"
    # avec sa lettre, qui distingue des regimes et n'est pas du bruit.
    return REGIMES.get(_replie(cle))


def _replie(cle: str) -> str:
    """Casse et accents retires. N'est utilise que pour les regimes en lettres."""

    sans_accent = unicodedata.normalize("NFKD", cle)
    return "".join(c for c in sans_accent if not unicodedata.combining(c)).lower()


def majorite_enoncee(majorite: Optional[str]) -> bool:
    """Le proces-verbal a-t-il ecrit une majorite, reconnue ou non ?

    Le defaut que ce predicat ferme: quand la table ne reconnaissait pas un
    libelle, le refus rendu disait "la majorite n'est pas enoncee". C'est faux -
    elle l'est, elle n'est pas reconnue. Le lecteur concluait a un defaut du
    document alors que le defaut est dans l'outil.
    """

    return bool(normaliser_majorite(majorite))
