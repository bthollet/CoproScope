"""Trouver la convention de numerotation d'un document, au lieu de la connaitre.

Le defaut que ce module corrige est une methode, pas un bug. Trois gabarits
rencontres sur deux coproprietes et trois syndics, tous trois designes ici par
un pseudonyme:

    CabinetAlfa  `12- objet`              suffixe `-`
    CabinetBeta  `12)` puis l'objet       suffixe `)`
    D4           `Resolution n°12 : ...`  prefixe `resolution n`

Y repondre par trois motifs ecrits a la main marche sur trois syndics et echoue
sur le quatrieme. Or rien ne borne le nombre de conventions: chaque logiciel de
syndic imprime la sienne, et un meme syndic en change en changeant d'outil.

La sortie n'est donc pas une liste de separateurs connus mais une **mesure**.
Une numerotation d'ordre du jour a trois proprietes qu'aucune autre suite de
nombres du document ne reunit:

1. elle se repete avec la meme signature typographique;
2. ses nombres forment une suite qui part de 1 et progresse sans grand trou;
3. chaque occurrence est suivie d'un libelle, pas d'un autre nombre.

On releve donc toutes les signatures candidates, on les note sur ces criteres,
et on retient la meilleure. Un quatrieme syndic ne demande aucune ligne de code:
il demande que sa convention soit la plus reguliere de son propre document, ce
qui est exactement ce qui fait d'elle une numerotation.
"""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass

# Une ligne candidate: un prefixe litteral court et facultatif, un nombre, un
# suffixe non alphanumerique court et facultatif, puis le reste de la ligne.
CANDIDATE_RE = re.compile(
    r"^[\s•\-–]*(?P<prefixe>[^\d\n]{0,24}?)(?P<numero>\d{1,3})(?P<suffixe>[^\w\n]{0,4})(?P<reste>.*)$"
)

# Ecart tolere entre deux numeros consecutifs. Deux, parce que l'OCR de ce
# corpus rend "Resolution n°S" pour "n°5": un numero saute sans que la suite
# cesse d'etre une suite.
ECART_TOLERE = 2

# En deca, une suite n'est pas une numerotation mais une coincidence.
PORTEE_MINIMALE = 4


@dataclass(frozen=True)
class Signature:
    """La convention de numerotation retenue pour un document."""

    prefixe: str
    suffixe: str
    numeros: tuple[int, ...]
    portee: int
    # Combien de ses occurrences annoncent une majorite. C'est ce qui distingue
    # un ordre du jour d'une liste de pieces jointes de meme forme.
    ancrage_majorite: int = 0

    @property
    def motif(self) -> re.Pattern[str]:
        """Le motif de lecture correspondant, ancre en debut de ligne."""
        debut = _motif_tolerant_aux_accents(self.prefixe) + r"\s*" if self.prefixe else ""
        fin = re.escape(self.suffixe) if self.suffixe else ""
        # Pas d'ancre de fin de ligne: l'exiger faisait manquer toute ligne dont
        # le libelle depasse la borne, et l'ordre du jour Tilleuls passait de
        # quarante-sept points a dix-neuf. Le libelle est borne, la ligne non.
        # L'espace autour du suffixe est libre: la meme convention ecrit
        # `Resolution n°4: Rapport` et `Resolution n°1 : Designation`. Le
        # suffixe normalise ayant perdu ses espaces, le motif doit les rendre.
        return re.compile(rf"(?mi)^[\s•]*{debut}(\d{{1,3}})\s*{fin}\s*(.{{0,180}})")

    def __str__(self) -> str:
        forme = f"{self.prefixe}N{self.suffixe}" if self.prefixe else f"N{self.suffixe}"
        return f"{forme!r} portee={self.portee} ancrage={self.ancrage_majorite}"


# Les accents sont retires a la collecte pour que `Resolution` et `Résolution`
# soient la meme convention. Le motif doit donc les rendre, sans quoi il ne
# retrouve pas le texte dont il a ete tire: la signature `resolution n°` de la
# convocation 2023 etait juste et ne matchait rien.
VARIANTES_ACCENTUEES = {
    "a": "aàâä", "c": "cç", "e": "eéèêë", "i": "iîï",
    "o": "oôö", "u": "uùûü", "y": "yÿ",
}


def _motif_tolerant_aux_accents(litteral: str) -> str:
    morceaux = []
    for caractere in litteral:
        variantes = VARIANTES_ACCENTUEES.get(caractere)
        morceaux.append(f"[{variantes}]" if variantes else re.escape(caractere))
    return "".join(morceaux)


def _sans_accent(valeur: str) -> str:
    decompose = unicodedata.normalize("NFKD", valeur)
    return "".join(c for c in decompose if not unicodedata.combining(c))


def _prefixe_normalise(brut: str) -> str:
    """Un prefixe n'est retenu que s'il est un mot, pas un fragment de phrase."""
    nettoye = _sans_accent(brut).strip().lower()
    nettoye = re.sub(r"\s+", " ", nettoye)
    if not nettoye:
        return ""
    # "resolution n°", "article n", "point": un ou deux mots, rien de plus long.
    if len(nettoye) > 20 or not re.fullmatch(r"[a-z°\s.]{2,20}", nettoye):
        return ""
    return nettoye


def _suffixe_normalise(brut: str) -> str:
    return re.sub(r"\s+", "", brut or "")


def portee_de(numeros: set[int]) -> int:
    """Longueur de la suite qui part du debut et progresse sans grand trou.

    On ne compte pas les nombres, on compte la SUITE: vingt occurrences du
    nombre 1 ne font pas une numerotation, alors que 1, 2, 4, 5, 6 en font une
    malgre son trou.
    """
    if not numeros:
        return 0
    ordonnes = sorted(numeros)
    if ordonnes[0] > 2:
        return 0  # une numerotation d'ordre du jour part de 1, parfois de 2
    portee = 1
    precedent = ordonnes[0]
    for numero in ordonnes[1:]:
        if numero - precedent > ECART_TOLERE:
            break
        portee += 1
        precedent = numero
    return portee


# Ce qui distingue un ordre du jour de toute autre liste numerotee du document.
#
# Le critere typographique ne suffit pas: sur la convocation Erables (pseudo) de
# 2024, la liste des `piece jointe n°X` est plus longue et plus reguliere que
# l'ordre du jour lui-meme, donc elle gagnerait. Ce qui les separe n'est pas la
# forme mais le fond - un point d'ordre du jour annonce sous quelle majorite il
# sera vote, une piece jointe n'annonce rien.
MAJORITE_PROCHE_RE = re.compile(
    r"(?:articles?\s*(?:n[°o]\s*)?2[3456]|sans\s+vote|majorit[ée])", re.IGNORECASE
)


def signatures_candidates(pages: list[str]) -> dict[tuple[str, str], tuple[set[int], int]]:
    """Toutes les conventions vues, avec leurs numeros et leur ancrage metier.

    Une occurrence ne compte que si elle est suivie d'un libelle, sur sa ligne
    ou sur la suivante: c'est ce qui distingue une numerotation d'une colonne de
    chiffres dans un tableau de devis.

    Le second nombre rendu compte les occurrences suivies d'une mention de
    majorite. C'est l'ancrage metier, et c'est lui qui tranche entre deux
    numerotations concurrentes.
    """
    releve: dict[tuple[str, str], set[int]] = {}
    ancrage: dict[tuple[str, str], int] = {}
    for texte in pages:
        lignes = texte.splitlines()
        for rang, ligne in enumerate(lignes):
            trouve = CANDIDATE_RE.match(ligne)
            if not trouve:
                continue
            prefixe = _prefixe_normalise(trouve.group("prefixe"))
            if prefixe == "" and trouve.group("prefixe").strip():
                continue  # un prefixe present mais non retenu: ce n'est pas un point
            suffixe = _suffixe_normalise(trouve.group("suffixe"))
            if not _suivi_d_un_libelle(trouve.group("reste"), lignes, rang):
                continue
            cle = (prefixe, suffixe)
            releve.setdefault(cle, set()).add(int(trouve.group("numero")))
            voisinage = " ".join([trouve.group("reste"), *lignes[rang + 1: rang + 4]])
            if MAJORITE_PROCHE_RE.search(voisinage):
                ancrage[cle] = ancrage.get(cle, 0) + 1
    return {cle: (numeros, ancrage.get(cle, 0)) for cle, numeros in releve.items()}


def _suivi_d_un_libelle(reste: str, lignes: list[str], rang: int) -> bool:
    """Un point porte un libelle; une cellule de tableau porte un autre chiffre."""
    if _est_un_libelle(reste):
        return True
    for suivante in lignes[rang + 1: rang + 3]:
        if suivante.strip():
            return _est_un_libelle(suivante)
    return False


def _est_un_libelle(valeur: str) -> bool:
    nettoye = valeur.strip()
    return len(nettoye) >= 3 and sum(c.isalpha() for c in nettoye) >= 3


def calibrer(pages: list[str]) -> Signature | None:
    """La convention la plus reguliere du document, ou rien.

    Rendre `None` est un resultat: cela dit que le document ne porte pas
    d'enumeration reconnaissable, et l'appelant doit le signaler plutot que de
    presenter une liste vide comme une absence de resolutions.
    """
    meilleures: list[Signature] = []
    for (prefixe, suffixe), (numeros, ancrage) in signatures_candidates(pages).items():
        portee = portee_de(numeros)
        if portee < PORTEE_MINIMALE:
            continue
        meilleures.append(Signature(prefixe, suffixe, tuple(sorted(numeros)), portee, ancrage))
    if not meilleures:
        return None
    # Score = portee + ancrage PLAFONNE a la portee. Quatre reglages ont ete
    # essayes et mesures sur les sept convocations des deux corpus; celui-ci est
    # le seul qui les rende toutes justes. Les trois autres, et leur contre-
    # exemple, valent d'etre gardes ici parce qu'ils reviendront a l'esprit:
    #
    # - portee seule: `piece jointe n°X` (portee 23) bat le vrai ordre du jour
    #   de Erables (pseudo) 2024 (portee 19). Une liste de pieces jointes est plus
    #   reguliere qu'un ordre du jour, c'est justement ce qui la trahit;
    # - ancrage en critere premier: la forme `11.` des sous-points Tilleuls
    #   (portee 5, ancrage 78) bat la vraie numerotation de portee 47;
    # - ancrage en filtre eliminatoire: casse Erables (pseudo) 2026, dont la
    #   signature gagnante n'est pas celle qui porte les majorites.
    #
    # Le plafond empeche une signature courte mais tres ancree de l'emporter,
    # tout en recompensant l'ancrage a portee comparable.
    #
    # LIMITE CONNUE, non couverte: une liste non ancree DEUX FOIS plus longue
    # que l'ordre du jour repasserait devant. Aucun document des deux corpus
    # n'est dans ce cas - l'ecart reel est 23 contre 19 -, mais rien ne l'interdit.
    # La sortie propre serait de ne collecter les candidates que dans la region
    # qui nomme l'ordre du jour, ce qui supprime la concurrence au lieu de
    # l'arbitrer. A faire quand un document le demandera.
    meilleures.sort(
        key=lambda s: (
            s.portee + min(s.ancrage_majorite, s.portee),
            len(s.prefixe) + len(s.suffixe),
            s.portee,
        ),
        reverse=True,
    )
    return meilleures[0]
