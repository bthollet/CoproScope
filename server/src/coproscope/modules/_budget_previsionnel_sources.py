"""Registre des sources legales des controles du budget previsionnel.

Un controle sans identifiant `LEGIARTI` n'entre pas dans la grille. Ce fichier
est le seul endroit ou une source est declaree: un predicat cite une cle, il ne
recopie jamais un numero d'article.

Toutes les versions ci-dessous ont ete lues sur Legifrance via PISTE le
2026-09-03, fonds `LODA_DATE`, filtre de date pose au jour de la lecture. Aucune
ne portait de date de fin de vigueur. `VIGUEUR` signifie "en vigueur a la date
demandee", jamais "a jour": la date de version fait partie de la citation.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Source:
    """Un article, dans la version qui a ete effectivement lue."""

    cle: str
    texte: str
    article: str
    legiarti: str
    version_debut: str
    lu_le: str = "2026-09-03"

    def citation(self) -> str:
        return f"{self.article} {self.texte} ({self.legiarti}, version du {self.version_debut})"


_LOI = "de la loi n. 65-557 du 10 juillet 1965"
_D67 = "du decret n. 67-223 du 17 mars 1967"
_D05 = "du decret n. 2005-240 du 14 mars 2005"
_A05 = "de l'arrete du 14 mars 2005 relatif aux comptes du syndicat"

SOURCES: dict[str, Source] = {
    "loi.14-1": Source("loi.14-1", _LOI, "article 14-1", "LEGIARTI000043977299", "2023-01-01"),
    "loi.14-2": Source("loi.14-2", _LOI, "article 14-2", "LEGIARTI000043977289", "2023-01-01"),
    "loi.14-2-1": Source("loi.14-2-1", _LOI, "article 14-2-1", "LEGIARTI000043967792", "2023-01-01"),
    "loi.18": Source("loi.18", _LOI, "article 18", "LEGIARTI000049398867", "2024-04-11"),
    "loi.24": Source("loi.24", _LOI, "article 24", "LEGIARTI000051749514", "2025-06-18"),
    "d67.11": Source("d67.11", _D67, "article 11", "LEGIARTI000053191281", "2025-12-25"),
    "d67.35": Source("d67.35", _D67, "article 35", "LEGIARTI000053191341", "2025-12-25"),
    "d67.43": Source("d67.43", _D67, "article 43", "LEGIARTI000006488753", "2004-06-04"),
    "d67.44": Source("d67.44", _D67, "article 44", "LEGIARTI000006488761", "2004-06-04"),
    "d67.45-1": Source("d67.45-1", _D67, "article 45-1", "LEGIARTI000042078810", "2020-07-04"),
    "d05.2": Source("d05.2", _D05, "article 2", "LEGIARTI000042412723", "2020-12-31"),
    "d05.5": Source("d05.5", _D05, "article 5", "LEGIARTI000006239513", "2005-03-18"),
    "d05.8": Source("d05.8", _D05, "article 8", "LEGIARTI000006239516", "2005-03-18"),
    "d05.9": Source("d05.9", _D05, "article 9", "LEGIARTI000006239517", "2005-03-18"),
    "d05.10": Source("d05.10", _D05, "article 10", "LEGIARTI000006239518", "2005-03-18"),
    "d05.12": Source("d05.12", _D05, "article 12", "LEGIARTI000006239520", "2005-03-18"),
    "d05.annexe2": Source("d05.annexe2", _D05, "annexe 2", "LEGIARTI000042412729", "2020-12-31"),
    "a05.6": Source("a05.6", _A05, "article 6", "LEGIARTI000006501186", "2005-03-18"),
    "a05.7": Source("a05.7", _A05, "article 7", "LEGIARTI000042413155", "2020-12-31"),
    "a05.8": Source("a05.8", _A05, "article 8", "LEGIARTI000006501225", "2005-03-18"),
}


def source(cle: str) -> Source:
    """Rend la source declaree, ou echoue en le disant.

    Un `KeyError` silencieux produirait un controle sans fondement affiche;
    mieux vaut casser au chargement du module.
    """
    try:
        return SOURCES[cle]
    except KeyError:
        raise KeyError(
            f"source legale inconnue: {cle!r}. "
            "Verifier l'article sur Legifrance avant de l'ajouter a SOURCES."
        ) from None


def citations(cles: tuple[str, ...]) -> tuple[str, ...]:
    return tuple(source(cle).citation() for cle in cles)


def legiartis(cles: tuple[str, ...]) -> tuple[str, ...]:
    return tuple(source(cle).legiarti for cle in cles)


def cles_par_legiarti(legiarti: str) -> tuple[str, ...]:
    """Les cles de ce registre qui citent cet article.

    `RM-2026-0089`, point (2) de la description: *qu'une mise a jour
    reglementaire se traduise MECANIQUEMENT en liste de controles a
    reverifier, au lieu d'un audit manuel*. L'index direct - une cle vers un
    article - existait depuis l'origine; **l'index inverse manquait**, et
    c'est lui que la question pose: *cet article a bouge, qu'est-ce qui en
    depend ?*

    Rend un tuple TRIE, et **vide quand rien ne cite cet article** - ce qui se
    lit *aucun choix de code n'en depend ici*, jamais *l'article est
    inconnu*. Les deux se distinguent en interrogeant `SOURCES`.

    **Ce registre n'est pas le seul:** `_extranet_referentiel` en tient un
    autre. Une reponse vide ici ne vaut donc que pour ce registre, et
    `server/tests/test_fondements_juridiques.py` compose les deux.
    """
    return tuple(sorted(
        cle for cle, declaration in SOURCES.items()
        if declaration.legiarti == legiarti))
