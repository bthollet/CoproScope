"""Ce qu'un etat des depenses et une annexe comptable rendent, et ce qu'ils avouent.

Deux principes gouvernent ces objets.

**`None` n'est pas zero.** Une colonne absente du tableau vaut `None`. Une
colonne presente et vide vaut zero. Confondre les deux ferait passer pour
verifie ce qui n'a jamais ete lu, et c'est exactement le defaut que le contrat
d'entree du module budget interdit.

**Un ecart est un constat rattache a une piece, jamais une correction.** Quand
la taxe portee par une ligne ne retombe pas sur le taux affiche, le module
conserve **les deux** valeurs, celle du document et celle du calcul, et emet un
constat qui nomme la reference de piece. Il ne recrit jamais le document.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal
from typing import Any

# Portee d'un total, du plus fin au plus general.
SOUS_POSTE = "SOUS_POSTE"
COMPTE = "COMPTE"
CLE = "CLE"
COURANTES = "COURANTES"
TRAVAUX = "TRAVAUX"
GENERAL = "GENERAL"

PORTEES = (SOUS_POSTE, COMPTE, CLE, COURANTES, TRAVAUX, GENERAL)

# Granularite du tableau. Axe, pas modalite: un cabinet peut n'editer que l'un
# des deux, ou les deux, ou melanger les deux dans un meme fichier.
SYNTHESE = "SYNTHESE"
DETAILLE = "DETAILLE"
GRANULARITES = (SYNTHESE, DETAILLE)

# Convention de la colonne de montant. `INCONNUE` est un etat legitime: il dit
# que le document ne porte pas de quoi trancher, et interdit tout calcul de
# taxe derive.
TTC_TAXE_INCLUSE = "TTC_TAXE_INCLUSE"
HT_TAXE_AJOUTEE = "HT_TAXE_AJOUTEE"
CONVENTION_INCONNUE = "CONVENTION_INCONNUE"
CONVENTIONS = (TTC_TAXE_INCLUSE, HT_TAXE_AJOUTEE, CONVENTION_INCONNUE)

# Ou se trouve le total general. Trois modalites observees ou anticipees.
TOTAL_LIGNE = "LIGNE"
TOTAL_PIED = "PIED_DE_TABLEAU"
TOTAL_ABSENT = "ABSENT"

# Codes de constat. Chacun nomme un fait, pas une opinion.
TAXE_DISCORDANTE = "TAXE_DISCORDANTE"
COLONNES_NON_LIABLES = "COLONNES_NON_LIABLES"
TOTAL_NON_RECONCILIE = "TOTAL_NON_RECONCILIE"
SEPARATEUR_INDECIDABLE = "SEPARATEUR_INDECIDABLE"
CONVENTION_NON_ETABLIE = "CONVENTION_NON_ETABLIE"
EXERCICE_ABSENT = "EXERCICE_ABSENT"
#: La ligne de total porte des nombres, mais leur nombre ne correspond a
#: aucune structure de colonnes etablie. Aucun total n'est elu: elire par
#: position dans une liste dont on ignore la structure est precisement le
#: defaut `C037`.
STRUCTURE_DE_COLONNES_INCONNUE = "STRUCTURE_DE_COLONNES_INCONNUE"
TOTAL_GENERAL_ABSENT = "TOTAL_GENERAL_ABSENT"
GRANULARITE_MELANGEE = "GRANULARITE_MELANGEE"
TOTAL_AMBIGU = "TOTAL_AMBIGU"
TOTAL_INTROUVABLE = "TOTAL_INTROUVABLE"


@dataclass(frozen=True)
class ConstatExtraction:
    """Un fait de lecture, rattache a la piece ou a la ligne qui le porte.

    `reference_piece` est vide quand le constat porte sur le document entier.
    Les deux valeurs en presence sont conservees: le module ne tranche pas a la
    place du syndic, il expose l'ecart.
    """

    code: str
    message: str
    reference_piece: str = ""
    compte: str = ""
    valeur_document: str = ""
    valeur_calculee: str = ""


@dataclass(frozen=True)
class ProfilTableau:
    """Les axes du tableau, mesures sur le document et non supposes.

    Chaque champ est un axe de generalisation. La valeur qu'il porte est la
    modalite observee sur ce document-ci; le code ne depend d'aucune de ces
    modalites, il depend de l'axe.
    """

    separateur_decimal: str | None = None
    colonnes: tuple[str, ...] = ()
    convention_montant: str = CONVENTION_INCONNUE
    granularite: str = SYNTHESE
    reference_piece_presente: bool = False
    emplacement_total_general: str = TOTAL_ABSENT
    colonne_charges_locatives: bool = False
    colonne_taux: bool = False
    marqueurs_de_cle_observes: tuple[str, ...] = ()


@dataclass(frozen=True)
class LigneEtat:
    """Une ligne de depense, telle que le document la porte.

    `montant_a_repartir` est rendu **sans conversion**. Sa convention est dite
    par `ProfilTableau.convention_montant`, et c'est a l'appelant de ne pas la
    confondre avec un hors taxes.
    """

    cle_repartition: str = ""
    compte: str = ""
    compte_libelle: str = ""
    sous_poste: str = ""
    date: str = ""
    reference_piece: str = ""
    libelle: str = ""
    montant_a_repartir: Decimal | None = None
    charges_locatives: Decimal | None = None
    taux_taxe: Decimal | None = None
    montant_taxe: Decimal | None = None
    marqueur_cle: str = ""


@dataclass(frozen=True)
class TotalEtat:
    """Un total imprime par le document, conserve tel quel.

    Le module ne remplace jamais un total imprime par sa propre somme. Il
    compare les deux et, s'ils different, emet `TOTAL_NON_RECONCILIE`.
    """

    portee: str
    libelle: str
    montant_a_repartir: Decimal | None = None
    charges_locatives: Decimal | None = None
    montant_taxe: Decimal | None = None
    parts: str = ""


@dataclass(frozen=True)
class EtatDepenses:
    """Un etat des depenses lu, avec ses totaux imprimes et ses constats."""

    exercice_debut: str = ""
    exercice_fin: str = ""
    profil: ProfilTableau = field(default_factory=ProfilTableau)
    lignes: tuple[LigneEtat, ...] = ()
    totaux: tuple[TotalEtat, ...] = ()
    constats: tuple[ConstatExtraction, ...] = ()

    def total(self, portee: str) -> TotalEtat | None:
        """Le premier total imprime de cette portee, ou `None` s'il n'y en a pas."""
        for element in self.totaux:
            if element.portee == portee:
                return element
        return None

    @property
    def total_general(self) -> Decimal | None:
        """Le total general imprime, jamais une somme recalculee."""
        trouve = self.total(GENERAL)
        return None if trouve is None else trouve.montant_a_repartir


@dataclass(frozen=True)
class ColonneAnnexe:
    """Une colonne comparative d'annexe, avec l'exercice et l'usage qu'elle sert.

    Le nombre de colonnes est un axe: le corpus en montre cinq chez un cabinet.
    Rien n'oblige un autre cabinet a en aligner autant, et le code n'en attend
    aucun nombre fixe.
    """

    exercice: str = ""
    intitule: str = ""
    usage: str = ""
    #: Le role lu dans les mots de l'entete, sur deux axes independants -
    #: nature et statut - ou `None` quand le bloc d'entetes n'a pas pu
    #: etre decoupe en autant de libelles que de colonnes. Voir
    #: `_comptes_extraction_roles`.
    role: Any = None


@dataclass(frozen=True)
class AnnexeComptable:
    """Une annexe reglementaire lue au niveau de ses totaux.

    **Limitation levee le 2026-09-12, `RM-2026-0094`.** Elle portait sur l'ACCES
    et non sur l'existence de la source: trois voies numeriques l'ont confirmee
    le 2026-09-06 - l'API rend `Annexe non reproduite`, la page du JO renvoie au
    tableau papier, le PDF est refuse en 401 puis 403. **Brice a depose le fichier
    officiel lui-meme** - `joe_20050318_0065_0007.pdf`, JO du 18 mars 2005, texte 7
    sur 102, NOR `SOCU0412534D` - lu page par page, releve dans
    `docs/annexes_comptables_decret_2005-240.md`. Les quatre egalites de controle
    sont desormais executables dans `_comptes_egalites_annexes.py`.
    **Ce qui n'est PAS leve:** les rubriques de ventilation des annexes 3 et 4 sont
    *arretees en fonction des clauses du reglement de copropriete*. Elles ne sont
    donc jamais universelles, et aucun controle ne doit les coder.

    Ce modele ne porte toujours qu'un total par annexe - voir le residu nomme
    dans `_comptes_extraction_annexe`.
    """

    numero: str = ""
    exercice_debut: str = ""
    exercice_fin: str = ""
    intitule: str = ""
    colonnes: tuple[ColonneAnnexe, ...] = ()
    total_charges: Decimal | None = None
    total_charges_par_colonne: tuple[Decimal | None, ...] = ()
    profil: ProfilTableau = field(default_factory=ProfilTableau)
    constats: tuple[ConstatExtraction, ...] = ()
