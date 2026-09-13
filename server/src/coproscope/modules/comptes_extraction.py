"""Extraction des pieces comptables d'une assemblee. Lot `RM-2026-0074`.

Le contrat d'entree est **par assemblee, pas par document**. Cette contrainte
vient du corpus et non d'une preference: un cabinet eclate sa convocation en
plusieurs fichiers, annexes d'un cote, ordre du jour de l'autre, et un second
cabinet regroupe les cinq annexes reglementaires dans un unique fichier. Un
contrat par document obligerait l'appelant a savoir a l'avance combien de
fichiers composent une assemblee, ce qu'aucun des deux cabinets ne lui dit.

`dossier_assemblee` prend donc un sac de pieces, sans ordre impose, et rend le
`Dossier` que les controles du budget previsionnel (`RM-2026-0082`) attendent.
Ce qu'aucune piece du sac n'apporte reste a `None`, et un controle prive de son
entree rendra `INAPPLICABLE` en la nommant. C'est ce comptage qui dit ce qu'il
faut reclamer au syndic.

Ce que ce module ne fait pas: il ne lit pas de PDF. Il consomme la couche de
texte deja extraite, ce qui garde l'extraction de texte, qui depend de l'outil,
separee de la lecture comptable, qui depend du droit.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from decimal import Decimal
from typing import Iterable

from ._budget_previsionnel_modele import Annexes, BudgetPrevisionnel, Dossier, LigneBudget
from ._comptes_extraction_annexe import lire_annexe
from ._comptes_extraction_controles import (
    PieceJustificative,
    constats_contre_pieces,
    constats_internes,
    totaux_de_bloc,
)
from ._comptes_extraction_etat import lire_etat_depenses
from ._comptes_extraction_modele import (
    AnnexeComptable,
    ConstatExtraction,
    EtatDepenses,
    LigneEtat,
    ProfilTableau,
    TotalEtat,
)

# Natures de piece reconnues dans un sac d'assemblee.
ETAT_DES_DEPENSES = "ETAT_DES_DEPENSES"
ANNEXE = "ANNEXE"
INDETERMINEE = "INDETERMINEE"

_NUMERO_ANNEXE = re.compile(r"ANNEXE\s*N\s*[°ºo]?\s*(\d)", re.IGNORECASE)


@dataclass(frozen=True)
class PieceAssemblee:
    """Une piece du dossier d'assemblee, designee par un identifiant stable.

    `identifiant` ne doit jamais etre un nom de fichier brut: c'est l'appelant
    qui choisit un identifiant sans donnee personnelle, et le module s'en sert
    tel quel dans ses constats.
    """

    identifiant: str
    texte: str


@dataclass(frozen=True)
class DossierComptable:
    """Ce qu'une assemblee apporte, toutes pieces confondues.

    `sans_nature` liste les pieces qu'aucun lecteur n'a reconnues. Une piece
    non reconnue n'est jamais silencieuse: elle sort ici, pour que l'absence
    d'un chiffre ne puisse pas etre prise pour un zero.
    """

    etats: tuple[EtatDepenses, ...] = ()
    annexes: tuple[AnnexeComptable, ...] = ()
    sans_nature: tuple[str, ...] = ()
    constats: tuple[ConstatExtraction, ...] = ()

    def annexe(self, numero: str) -> AnnexeComptable | None:
        """La premiere annexe portant ce numero, ou `None`."""
        for element in self.annexes:
            if element.numero == numero:
                return element
        return None

    def etat_de_exercice(self, fin: str) -> EtatDepenses | None:
        """L'etat des depenses dont l'exercice se clot a cette date."""
        for element in self.etats:
            if element.exercice_fin == fin:
                return element
        return None


def nature_de(texte: str) -> str:
    """Nature d'une piece, lue sur son contenu et jamais sur son nom.

    Le corpus mesure interdit de se fier au nom: un fichier nomme `detaillees`
    porte un etat de synthese, un etat des depenses a ete etiquete comme un
    grand livre, et un fichier de travail interne a ete etiquete comme un etat
    des depenses. Le nom est une assertion de classement; le contenu est la
    piece.
    """
    compact = " ".join(texte[:4000].upper().split())
    if "ETAT DES DEPENSES" in compact:
        return ETAT_DES_DEPENSES
    if "ANNEXE N" in compact:
        return ANNEXE
    return INDETERMINEE


def dossier_comptable(pieces: Iterable[PieceAssemblee]) -> DossierComptable:
    """Lit toutes les pieces d'une assemblee, quel que soit leur nombre.

    Une piece peut contenir plusieurs annexes: le second cabinet mesure les
    empile toutes dans un seul fichier. Le lecteur d'annexe est donc applique
    a chaque bloc ouvert par un intitule d'annexe, pas au fichier entier.
    """
    etats: list[EtatDepenses] = []
    annexes: list[AnnexeComptable] = []
    sans_nature: list[str] = []
    constats: list[ConstatExtraction] = []
    for piece in pieces:
        nature = nature_de(piece.texte)
        if nature == ETAT_DES_DEPENSES:
            etat = lire_etat_depenses(piece.texte)
            etats.append(etat)
            constats.extend(_rattacher(etat.constats, piece.identifiant))
            constats.extend(_rattacher(constats_internes(etat), piece.identifiant))
        elif nature == ANNEXE:
            for bloc in _blocs_d_annexe(piece.texte):
                lue = lire_annexe(bloc)
                # Un bloc sans numero ni total est un residu de decoupage, pas
                # une annexe: le retenir ferait croire a une piece de plus.
                if not lue.numero and lue.total_charges is None:
                    continue
                annexes.append(lue)
                constats.extend(_rattacher(lue.constats, piece.identifiant))
        else:
            sans_nature.append(piece.identifiant)
    return DossierComptable(
        etats=tuple(etats),
        annexes=tuple(annexes),
        sans_nature=tuple(sans_nature),
        constats=tuple(constats),
    )


def _blocs_d_annexe(texte: str) -> list[str]:
    """Decoupe un fichier en autant de blocs que d'annexes distinctes.

    Le decoupage se fait sur le **changement de numero d'annexe**, jamais sur
    l'apparition de l'intitule: un cabinet le repete en tete de chaque page, et
    un autre repete l'annexe 3 une fois par cle de repartition. Compter les
    apparitions donnerait sept annexes 3 la ou il y en a une, declinee.

    L'entete d'une annexe est parfois precedee, dans l'ordre aplati, des
    intitules de ses propres colonnes. Un bloc commence donc a la ligne qui suit
    la fin du bloc precedent, pas a la ligne de son propre intitule.
    """
    lignes = texte.splitlines()
    bornes: list[int] = []
    dernier = ""
    for index, brut in enumerate(lignes):
        trouve = _NUMERO_ANNEXE.search(brut)
        if trouve is None:
            continue
        numero = trouve.group(1)
        if numero != dernier:
            bornes.append(index)
            dernier = numero
    if not bornes:
        return [texte]
    blocs: list[str] = []
    for position, borne in enumerate(bornes):
        debut = 0 if position == 0 else bornes[position]
        fin = bornes[position + 1] if position + 1 < len(bornes) else len(lignes)
        bloc = "\n".join(lignes[debut:fin]).strip()
        if bloc:
            blocs.append(bloc)
    return blocs


def _rattacher(
    constats: Iterable[ConstatExtraction],
    identifiant: str,
) -> list[ConstatExtraction]:
    """Ajoute l'identifiant de piece aux constats qui n'en portent pas."""
    rattaches: list[ConstatExtraction] = []
    for constat in constats:
        if constat.reference_piece:
            rattaches.append(constat)
            continue
        rattaches.append(
            ConstatExtraction(
                code=constat.code,
                message=constat.message,
                reference_piece=identifiant,
                compte=constat.compte,
                valeur_document=constat.valeur_document,
                valeur_calculee=constat.valeur_calculee,
            )
        )
    return rattaches


def dossier_assemblee(
    pieces: Iterable[PieceAssemblee],
    *,
    exercice_du_vote: str = "",
) -> tuple[Dossier, DossierComptable]:
    """Rend le `Dossier` attendu par les controles du budget previsionnel.

    `exercice_du_vote` est la date de cloture de l'exercice dont les comptes
    sont soumis, au format imprime par les pieces. Quand elle est vide, le
    module prend l'unique exercice present, et n'en choisit aucun s'il y en a
    plusieurs: choisir a la place de l'appelant produirait un chiffre juste
    pour le mauvais exercice, qui est le pire des resultats.
    """
    lu = dossier_comptable(pieces)
    annexe2 = lu.annexe("2")
    annexe3 = lu.annexe("3")
    budget = _budget_depuis(annexe3 or annexe2)
    return (
        Dossier(
            budget=budget,
            annexes=Annexes(
                total_charges_annexe2_courantes=_total_de(annexe2),
                total_charges_annexe3_courantes=_total_de(annexe3),
            ),
            reference=exercice_du_vote,
        ),
        lu,
    )


def _total_de(annexe: AnnexeComptable | None) -> float | None:
    """Le total des charges, **converti** au type que la grille declare.

    L'extraction compte en `Decimal` - un euro n'a pas de representation
    binaire exacte, et un total lu sur une annexe doit rester exact. La grille
    du budget previsionnel, elle, declare `float`. Les deux ont raison chacune
    de leur cote; ce qui manquait etait la conversion au raccord.

    Mesure du 2026-09-04: le `Decimal` passait tel quel dans un dataclass
    `frozen` sans validation. B-4 rendait CONFORME - `Decimal` se compare a un
    `float` sans broncher - et B-6 levait `TypeError: unsupported operand
    type(s) for +: 'decimal.Decimal' and 'float'` sur `avance > plafond +
    _TOLERANCE`. `evaluer()` est un tuple-comprehension sans garde: les seize
    controles mouraient au sixieme. Deux suites vertes de part et d'autre d'un
    raccord casse.
    """
    if annexe is None or annexe.total_charges is None:
        return None
    return float(annexe.total_charges)


def _budget_depuis(annexe: AnnexeComptable | None) -> BudgetPrevisionnel:
    """Le budget previsionnel vit **dans** l'annexe, pas dans un document a part.

    Le corpus le confirme: aucune piece autonome intitulee budget previsionnel
    n'existe au dossier mesure, et les deux etiquettes posees par le classement
    portaient sur des fichiers de travail. Le budget est une colonne de
    l'annexe 2 ou 3. Tant que la lecture ligne a ligne de cette colonne n'est
    pas faite, le module rend un budget sans lignes plutot qu'un budget invente.
    """
    if annexe is None:
        return BudgetPrevisionnel()
    lignes: tuple[LigneBudget, ...] = ()
    return BudgetPrevisionnel(lignes=lignes, total_charges=_total_de(annexe))


__all__ = [
    "ANNEXE",
    "AnnexeComptable",
    "ETAT_DES_DEPENSES",
    "EtatDepenses",
    "INDETERMINEE",
    "ConstatExtraction",
    "DossierComptable",
    "LigneEtat",
    "PieceAssemblee",
    "PieceJustificative",
    "ProfilTableau",
    "TotalEtat",
    "constats_contre_pieces",
    "constats_internes",
    "dossier_assemblee",
    "dossier_comptable",
    "lire_annexe",
    "lire_etat_depenses",
    "nature_de",
    "totaux_de_bloc",
]
