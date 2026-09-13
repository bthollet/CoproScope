"""Constats tires d'un etat des depenses, seul puis confronte aux pieces.

Trois ecarts reels ont ete releves a la main sur l'exercice mesure. Leur
enseignement est le plus important du lot: **aucun des trois n'est une erreur
d'arithmetique.**

- une taxe a 20 pour cent sur une facture emise a 10 pour cent;
- une taxe constatee sur une facture portant `taxe non applicable`;
- une taxe sur une prime d'assurance, qui n'en supporte pas.

Dans les trois cas la ligne comptable est cohérente avec elle-meme: le taux
affiche et la taxe extraite retombent au centime. Un controle qui ne lirait que
l'etat des depenses ne verrait rien, et c'est exactement ce qui s'est produit
lors de la premiere mesure de ce lot.

D'ou la separation en deux familles:

`constats_internes` ne lit que l'etat. Il ne peut attraper que le troisieme
ecart, et seulement par la **nature du compte**, jamais par son libelle: un
libelle est une modalite de cabinet, un numero de compte est une norme.

`constats_contre_pieces` confronte chaque ligne a la piece que sa reference
designe. C'est la seule voie pour les deux premiers ecarts, et c'est pour cela
que la colonne de reference de piece est l'axe le plus precieux du tableau: sans
elle, le rapprochement se rabat sur le montant, qui n'est pas identifiant.

Aucun de ces constats ne corrige quoi que ce soit. Chacun conserve la valeur du
document et la valeur attendue, et nomme la piece. Seul le syndic peut dire s'il
s'agit d'un parametrage de compte ou d'une erreur d'imputation.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from ._comptes_extraction_lexique import TOLERANCE_TVA, normaliser_compte
from ._comptes_extraction_modele import (
    COURANTES,
    GENERAL,
    TRAVAUX,
    TOTAL_NON_RECONCILIE,
    ConstatExtraction,
    EtatDepenses,
)

# Codes propres a cette famille de controles.
TAXE_SUR_COMPTE_EXONERE = "TAXE_SUR_COMPTE_EXONERE"
TAUX_DISCORDANT_AVEC_PIECE = "TAUX_DISCORDANT_AVEC_PIECE"
TAXE_SUR_PIECE_SANS_TAXE = "TAXE_SUR_PIECE_SANS_TAXE"
MONTANT_DISCORDANT_AVEC_PIECE = "MONTANT_DISCORDANT_AVEC_PIECE"
PIECE_SANS_LIGNE = "PIECE_SANS_LIGNE"

# Comptes dont la nature exclut la taxe sur la valeur ajoutee. La cle est le
# prefixe normalise du compte, pas son libelle: un cabinet ecrit `PRIMES
# D'ASSURANCES`, un autre `ASSURANCE MULTIRISQUE`, et le numero ne bouge pas.
#
# Ce que ce controle NE prouve PAS: que l'operation soit irreguliere. Une prime
# d'assurance supporte une taxe sur les conventions d'assurance, deja comprise
# dans le montant appele; la porter en taxe sur la valeur ajoutee est une
# question a poser, pas une faute etablie par la seule lecture du tableau.
COMPTES_SANS_TAXE_SUR_VALEUR_AJOUTEE = {
    "616": "primes d'assurances",
}


@dataclass(frozen=True)
class PieceJustificative:
    """Ce qu'une piece dit d'elle-meme, pour confrontation avec la ligne.

    Tout champ vaut `None` quand la piece ne le porte pas. `taxe_non_applicable`
    a trois etats: vrai, faux, et `None` quand la piece ne se prononce pas.
    """

    reference: str
    total: Decimal | None = None
    taux: Decimal | None = None
    taxe: Decimal | None = None
    taxe_non_applicable: bool | None = None
    nature: str = ""


def constats_internes(etat: EtatDepenses) -> tuple[ConstatExtraction, ...]:
    """Constats tires du seul etat des depenses."""
    constats: list[ConstatExtraction] = []
    constats.extend(_taxe_sur_comptes_exoneres(etat))
    constats.extend(_totaux_non_reconcilies(etat))
    return tuple(constats)


def _taxe_sur_comptes_exoneres(etat: EtatDepenses) -> list[ConstatExtraction]:
    constats: list[ConstatExtraction] = []
    for ligne in etat.lignes:
        if not ligne.taux_taxe or ligne.taux_taxe <= 0:
            continue
        normalise = normaliser_compte(ligne.compte)
        for prefixe, nature in COMPTES_SANS_TAXE_SUR_VALEUR_AJOUTEE.items():
            if not normalise.startswith(prefixe):
                continue
            constats.append(
                ConstatExtraction(
                    code=TAXE_SUR_COMPTE_EXONERE,
                    message=(
                        f"Une taxe sur la valeur ajoutee est extraite d'une ligne "
                        f"imputee en {nature}, dont la nature ne la supporte pas. "
                        "A poser comme question au syndic: parametrage de compte, "
                        "ou erreur d'imputation."
                    ),
                    reference_piece=ligne.reference_piece,
                    compte=ligne.compte,
                    valeur_document=str(ligne.montant_taxe),
                    valeur_calculee="",
                )
            )
    return constats


def _totaux_non_reconcilies(etat: EtatDepenses) -> list[ConstatExtraction]:
    """Compare chaque total imprime de bloc a la somme des lignes du bloc.

    Le module ne remplace jamais un total imprime par sa propre somme: il
    expose l'ecart. Un total imprime qui ne retombe pas sur ses lignes est le
    signe le plus simple d'une lecture incomplete, et il vaut mieux le dire que
    publier un chiffre qui a l'air rond.
    """
    somme = sum(
        (ligne.montant_a_repartir or Decimal("0")) for ligne in etat.lignes
    )
    general = etat.total(GENERAL)
    if general is None or general.montant_a_repartir is None:
        return []
    ecart = abs(general.montant_a_repartir - somme)
    if ecart <= TOLERANCE_TVA:
        return []
    return [
        ConstatExtraction(
            code=TOTAL_NON_RECONCILIE,
            message=(
                "Le total general imprime ne retombe pas sur la somme des lignes "
                "lues. Le total imprime fait foi; l'ecart signale une lecture "
                "incomplete et non une erreur du document."
            ),
            valeur_document=str(general.montant_a_repartir),
            valeur_calculee=str(somme),
        )
    ]


def constats_contre_pieces(
    etat: EtatDepenses,
    pieces: dict[str, PieceJustificative],
) -> tuple[ConstatExtraction, ...]:
    """Confronte chaque ligne a la piece que sa reference designe.

    Le rapprochement se fait **par la reference de piece**, jamais par le
    montant: deux factures peuvent porter le meme montant, et le montant est
    precisement ce que le controle cherche a verifier.

    Hors des valeurs observees: une reference absente du dictionnaire ne produit
    aucun constat sur la ligne, et une piece qu'aucune ligne ne reprend produit
    `PIECE_SANS_LIGNE`. Le silence n'est jamais interprete comme une conformite.
    """
    constats: list[ConstatExtraction] = []
    references_vues: set[str] = set()
    for ligne in etat.lignes:
        piece = pieces.get(ligne.reference_piece)
        if piece is None:
            continue
        references_vues.add(piece.reference)
        constats.extend(_confronter(ligne.compte, ligne, piece))
    for reference, piece in pieces.items():
        if reference in references_vues:
            continue
        constats.append(
            ConstatExtraction(
                code=PIECE_SANS_LIGNE,
                message=(
                    "Aucune ligne de l'etat des depenses ne reprend cette piece. "
                    "Elle peut relever d'un autre exercice, d'un autre syndicat, "
                    "ou n'avoir pas ete comptabilisee."
                ),
                reference_piece=reference,
                valeur_document=str(piece.total) if piece.total is not None else "",
            )
        )
    return tuple(constats)


def _confronter(
    compte: str,
    ligne: object,
    piece: PieceJustificative,
) -> list[ConstatExtraction]:
    constats: list[ConstatExtraction] = []
    taux_ligne = getattr(ligne, "taux_taxe", None)
    taxe_ligne = getattr(ligne, "montant_taxe", None)
    montant_ligne = getattr(ligne, "montant_a_repartir", None)

    if piece.taxe_non_applicable is True and taux_ligne and taux_ligne > 0:
        constats.append(
            ConstatExtraction(
                code=TAXE_SUR_PIECE_SANS_TAXE,
                message=(
                    "La piece indique expressement que la taxe n'est pas "
                    "applicable, et la ligne comptable en extrait pourtant une. "
                    "A poser comme question au syndic."
                ),
                reference_piece=piece.reference,
                compte=compte,
                valeur_document=str(taxe_ligne),
                valeur_calculee="0.00",
            )
        )
    elif (
        piece.taux is not None
        and taux_ligne is not None
        and piece.taux != taux_ligne
    ):
        constats.append(
            ConstatExtraction(
                code=TAUX_DISCORDANT_AVEC_PIECE,
                message=(
                    "Le taux retenu par la comptabilite differe du taux porte par "
                    "la piece. La ligne est coherente avec elle-meme: seul le "
                    "rapprochement avec la piece revele l'ecart."
                ),
                reference_piece=piece.reference,
                compte=compte,
                valeur_document=str(taux_ligne),
                valeur_calculee=str(piece.taux),
            )
        )

    if (
        piece.total is not None
        and montant_ligne is not None
        and abs(piece.total - montant_ligne) > TOLERANCE_TVA
    ):
        constats.append(
            ConstatExtraction(
                code=MONTANT_DISCORDANT_AVEC_PIECE,
                message=(
                    "Le montant porte par la ligne differe du total de la piece. "
                    "Ni l'un ni l'autre n'est corrige: les deux sont exposes."
                ),
                reference_piece=piece.reference,
                compte=compte,
                valeur_document=str(montant_ligne),
                valeur_calculee=str(piece.total),
            )
        )
    return constats


def totaux_de_bloc(etat: EtatDepenses) -> dict[str, Decimal | None]:
    """Les trois totaux de bloc, imprimes ou deduits, avec leur provenance.

    Le corpus montre un cabinet qui imprime le total des charges courantes sur
    certains exercices et pas sur d'autres. Quand il manque, il se deduit du
    total general moins le total travaux; la cle `courantes_deduite` dit quand
    c'est le cas, pour qu'un lecteur ne prenne jamais un calcul pour une lecture.
    """
    general = etat.total(GENERAL)
    courantes = etat.total(COURANTES)
    travaux = etat.total(TRAVAUX)
    valeur_generale = general.montant_a_repartir if general else None
    valeur_travaux = travaux.montant_a_repartir if travaux else None
    valeur_courantes = courantes.montant_a_repartir if courantes else None
    deduite = False
    if valeur_courantes is None and valeur_generale is not None and valeur_travaux is not None:
        valeur_courantes = valeur_generale - valeur_travaux
        deduite = True
    return {
        "general": valeur_generale,
        "courantes": valeur_courantes,
        "travaux": valeur_travaux,
        "courantes_deduite": deduite,
    }


__all__ = [
    "COMPTES_SANS_TAXE_SUR_VALEUR_AJOUTEE",
    "MONTANT_DISCORDANT_AVEC_PIECE",
    "PIECE_SANS_LIGNE",
    "PieceJustificative",
    "TAUX_DISCORDANT_AVEC_PIECE",
    "TAXE_SUR_COMPTE_EXONERE",
    "TAXE_SUR_PIECE_SANS_TAXE",
    "constats_contre_pieces",
    "constats_internes",
    "totaux_de_bloc",
]
