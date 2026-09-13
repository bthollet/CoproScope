"""Proces-verbal ou convocation: le decider en lisant, pas en croyant l'etiquette.

Le probleme n'est pas theorique. Sur le corpus Erables (pseudo), le classement par
nom de fichier se trompe de facon mesurable:

- `2023-06-19_AG_PV_Convoc.pdf` porte `PV` dans son nom et **n'est pas un PV**:
  zero formule de cloture, zero decompte de voix. Le traiter comme un proces-
  verbal fabriquerait des votes qui n'ont pas eu lieu - l'erreur exacte qui
  rendait quatorze resolutions "adoptees" sur une convocation Tilleuls (pseudo);
- `..._Convoc-comptes.pdf` est classe `Annexe_Comptable` en 2023 et `CR_CS` en
  2024, 2025 et 2026, pour un contenu de meme nature. Le nom a change, pas la
  piece.

La difference entre les deux objets n'est pas dans leur nom, elle est dans leur
texte, et elle est franche. Mesure sur les vingt-deux pieces du corpus:

    piece                        clotures   decomptes de voix
    les deux vrais PV              54, 37          119, 72
    toutes les convocations             0                0

Aucun cas intermediaire. Un vote laisse une trace ou il n'a pas eu lieu.

Consequence de modele: le proces-verbal et la convocation ne sont pas deux
objets mais **le meme objet dans deux etats** - `CONSTATEE` et `PROJETEE`, au
sens de la section 9 du modele de gouvernance. Ce module ne fait que dire dans
quel etat se trouve un document donne, pour que l'aiguillage entre les deux
lectures repose sur son contenu et non sur son nom.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

# Une issue de vote enoncee. Les deux syndics du corpus ecrivent differemment -
# "cette resolution est adoptee" chez l'un, "est rejetee" chez l'autre - mais
# aucun ne peut rapporter un vote sans en nommer l'issue.
CLOTURE_RE = re.compile(
    r"(?:cette\s+r[ée]solution\s+est"
    r"|est\s+(?:adopt[ée]e|rejet[ée]e|refus[ée]e|approuv[ée]e)\b"
    r"|r[ée]solution\s+(?:adopt[ée]e|rejet[ée]e))",
    re.IGNORECASE,
)

# Un decompte de voix. Il n'existe qu'apres un vote.
VOIX_RE = re.compile(
    r"(?:ont\s+vot[ée]s?\s+(?:pour|contre)"
    r"|se\s+sont\s+abstenus?"
    r"|voix\s+(?:pour|contre)"
    r"|nombre\s+de\s+voix)",
    re.IGNORECASE,
)

ETAT_CONSTATEE = "CONSTATEE"
ETAT_PROJETEE = "PROJETEE"
ETAT_ILLISIBLE = "ILLISIBLE"
ETAT_INDETERMINE = "INDETERMINE"

# En deca, il n'y a pas de couche texte exploitable, quoi qu'en dise le niveau
# d'extraction enregistre.
SEUIL_COUCHE_TEXTE = 50


@dataclass(frozen=True)
class Nature:
    """Ce que le document est, et ce qui permet de l'affirmer."""

    etat: str
    clotures: int
    decomptes: int
    caracteres: int
    signature_numerotation: str = ""

    @property
    def porte_des_votes(self) -> bool:
        return self.clotures > 0 or self.decomptes > 0

    def __str__(self) -> str:
        return (
            f"{self.etat} (clotures={self.clotures}, voix={self.decomptes}, "
            f"caracteres={self.caracteres})"
        )


def nature_du_document(pages: list[str], signature: object | None = None) -> Nature:
    """L'etat d'un document, mesure sur son texte.

    Trois reponses possibles, et la troisieme compte autant que les deux autres:

    `CONSTATEE`     le document rapporte des votes: c'est un proces-verbal;
    `PROJETEE`      il n'en rapporte aucun et porte une numerotation reconnue:
                    c'est une convocation, ou un projet;
    `ILLISIBLE`     il n'a pas de couche texte, donc rien n'est mesurable;
    `INDETERMINE`   il est lisible mais ne porte ni vote ni enumeration: on ne
                    tranche pas, et on le dit.

    `INDETERMINE` n'est pas un echec: c'est le cas d'une annexe comptable ou
    d'un devis, qui ne sont ni l'un ni l'autre. Le forcer dans une des deux
    familles serait une erreur silencieuse.
    """
    texte = "\n".join(pages)
    caracteres = len(texte.strip())
    if caracteres < SEUIL_COUCHE_TEXTE:
        return Nature(ETAT_ILLISIBLE, 0, 0, caracteres)
    clotures = len(CLOTURE_RE.findall(texte))
    decomptes = len(VOIX_RE.findall(texte))
    signature_lisible = str(signature) if signature else ""
    if _rapporte_des_votes(clotures, signature):
        return Nature(ETAT_CONSTATEE, clotures, decomptes, caracteres, signature_lisible)
    if signature is not None:
        return Nature(ETAT_PROJETEE, clotures, decomptes, caracteres, signature_lisible)
    return Nature(ETAT_INDETERMINE, clotures, decomptes, caracteres)


# Un proces-verbal rapporte l'issue de la PLUPART de ses resolutions. Un
# document ou moins d'une resolution sur cinq porte une issue ne rapporte pas
# des votes: il en mentionne un.
PART_MINIMALE = 5
CLOTURES_MINIMALES = 3


def _rapporte_des_votes(clotures: int, signature: object | None) -> bool:
    """La densite, pas la presence.

    La presence seule se trompe, et le contre-exemple est net: la convocation
    Tilleuls du 29/04/2026 porte UNE formule de cloture noyee dans quatre cent
    vingt-cinq mille caracteres - un `est approuvee` isole dans une annexe. Elle
    etait donc lue comme un proces-verbal, et l'extracteur y aurait cherche des
    votes qui n'ont pas eu lieu.

    On compare donc le nombre d'issues a la taille de l'enumeration quand elle
    est connue: un PV en porte autant que de resolutions, une convocation en
    porte une sur quarante-sept.
    """
    if clotures < CLOTURES_MINIMALES:
        return False
    portee = getattr(signature, "portee", 0) or 0
    if not portee:
        return True
    return clotures * PART_MINIMALE >= portee
