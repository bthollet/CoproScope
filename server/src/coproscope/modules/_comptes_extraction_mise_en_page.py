"""Mise en page d'un etat des depenses: entetes, pieds, intitules de total.

Tout ce que ce fichier contient est un axe de MISE EN PAGE, jamais de sens
comptable. On y trouve la reconnaissance des repetitions d'entete et de pied de
page, les intitules de colonne annonces, les intitules de total, et la forme
d'une reference de piece.

La separation est deliberee: le sens comptable vit dans le lexique et dans les
controles, la mise en page vit ici, et l'automate de lecture n'a a connaitre ni
l'un ni l'autre en detail. Un cabinet non observe change presque toujours la
mise en page et presque jamais le sens.
"""

from __future__ import annotations

import re

from . import _marqueur_page
from ._comptes_extraction_lexique import est_date, marqueur_de

#: Le marqueur de page vient du module qui le PRODUIT (`RM-2026-0146`).
#: Ce fichier en portait sa propre version, sans le `\s*` final - un marqueur
#: suivi d'une espace lui echappait - et avec `IGNORECASE`, que l'autre lecteur
#: n'avait pas. Un producteur, deux motifs.
_PAGE = _marqueur_page.MARQUEUR_RE
_EXERCICE = re.compile(r"EXERCICE\s+DU", re.IGNORECASE)
_TITRE = re.compile(r"ETAT\s+DES\s+DEPENSES", re.IGNORECASE)
_COMPTE_ET_LIBELLE = re.compile(r"^\s*(\d{3,8})\s{2,}(\S.*)$")
_CODE_SEUL = re.compile(r"^\s*([A-Z]?\d{2,4})\s*$")
_PARTS = re.compile(r"(?:en|sur)\s+([\d  ']+)\s*parts", re.IGNORECASE)
_PIED = re.compile(r"^\s*(Edit|Page\s*:|\d+\s*/\s*\d+\s*$)", re.IGNORECASE)


# Intitules de colonne. Ils servent a lire l'ORDRE ANNONCE par l'entete, qui est
# un axe; ils ne servent jamais a lier les valeurs, qui se lient par l'identite
# de taxe. Un cabinet qui nommerait autrement ses colonnes perd l'ordre annonce
# et garde la liaison.
_ENTETES = {
    "MONTANT A REPARTIR": "montant_a_repartir",
    "CHARGES LOCATIVES": "charges_locatives",
    "LOCATIVES": "charges_locatives",
    "TAUX TVA": "taux_taxe",
    "TAUX": "taux_taxe",
    "TVA": "taux_taxe",
    "MONTANT TVA": "montant_taxe",
    "T.V.A.": "montant_taxe",
    "MONTANT": "montant_a_repartir",
    "NATURE DES CHARGES": "libelle",
}


_MOT_TOTAL = re.compile(r"TOTAL|T\s+O\s+T\s+A\s+L", re.IGNORECASE)

# Un meme cabinet espace certains intitules lettre a lettre et pas d'autres:
# `T O T A L   G E N E R A L` cotoie `TOTAL CHARGES GENERALES` dans le meme
# fichier. L'espacement est donc un axe de mise en page, jamais un signe de
# nature. Tous les intitules sont compares **apres suppression de tout blanc**,
# ce qui rend la reconnaissance insensible a cette mise en page.
_SANS_BLANC = re.compile(r"\s+")
_TOTAL_GENERAL = "TOTALGENERAL"
_TOTAL_COURANTES = "TOTALCHARGESCOURANTES"
_TOTAL_TRAVAUX = "TOTALCHARGESTRAVAUX"


def _compacte(libelle: str) -> str:
    """Intitule sans aucun blanc, en majuscules, pour comparaison de nature."""
    return _SANS_BLANC.sub("", libelle).upper()


def _est_bruit(brut: str) -> bool:
    """Vrai pour les repetitions d'entete et de pied de page."""
    nu = brut.strip()
    if not nu:
        return True
    if _PAGE.match(nu) or _PIED.match(nu) or _TITRE.search(nu) or _EXERCICE.search(nu):
        return True
    majuscule = nu.upper().strip(". ")
    return majuscule in _ENTETES or majuscule in {"COPROPRIETE:", "COPROPRIÉTÉ:", "AU", "DU"}


def _colonnes_annoncees(lignes: list[str]) -> tuple[str, ...]:
    """Ordre des colonnes tel que l'entete l'annonce, dans l'ordre de lecture.

    L'ordre annonce est un axe a part entiere: il peut differer de l'ordre des
    valeurs, et un cabinet peut n'annoncer aucune entete. Le lecteur le
    conserve pour le rapport, sans jamais s'en servir pour lier les valeurs.
    """
    trouvees: list[str] = []
    for brut in lignes[:60]:
        majuscule = brut.strip().upper().strip(". ")
        nom = _ENTETES.get(majuscule)
        if nom and nom not in trouvees:
            trouvees.append(nom)
    return tuple(trouvees)


def _exercice(lignes: list[str]) -> tuple[str, str]:
    """Bornes de l'exercice, telles qu'imprimees, ou deux chaines vides."""
    dates: list[str] = []
    apres = False
    for brut in lignes[:80]:
        nu = brut.strip()
        if _EXERCICE.search(nu):
            apres = True
            dates.extend(re.findall(r"\d{2}/\d{2}/\d{2,4}", nu))
            continue
        if apres and re.fullmatch(r"\d{2}/\d{2}/\d{2,4}", nu):
            dates.append(nu)
        if len(dates) >= 2:
            break
    if len(dates) >= 2:
        return dates[0], dates[1]
    return "", ""


_REFERENCE = re.compile(r"^[A-Z]{0,4}[\d][\w\-/]{2,}$")


def _est_reference(nu: str) -> bool:
    """Vrai si le jeton a la forme d'une reference de piece.

    La forme est deliberement large: c'est la colonne qui porte le
    rapprochement facture vers ligne, et une reference manquee coute plus qu'une
    reference retenue a tort, qui reste visible dans le rapport.
    """
    return bool(_REFERENCE.match(nu)) and not est_date(nu) and " " not in nu


def _marqueur_de_ligne(bruts: list[str]) -> str:
    for brut in bruts:
        marqueur = marqueur_de(brut)
        if marqueur:
            return marqueur
    return ""


def _libelle_de_total(libelle: str) -> str:
    nettoye = libelle.strip().strip("*").strip("-").strip()
    nettoye = re.sub(r"[. ]{4,}.*$", "", nettoye).strip()
    return re.sub(r"\s+", " ", nettoye)
