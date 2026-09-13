"""Contrat d'entree des controles du budget previsionnel, et forme du constat.

Ces objets sont le contrat que l'extracteur d'annexes devra remplir. Tout champ
vaut `None` tant qu'il n'est pas extrait, et `None` ne se confond jamais avec
zero: un controle qui ne dispose pas de son entree rend `INAPPLICABLE`, pas
`CONFORME`. C'est la difference entre "verifie" et "pas verifiable", et c'est
elle qui dit ce que l'outil devra reclamer au syndic.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date

# Statuts d'un constat.
CONFORME = "CONFORME"
ECART = "ECART"
INAPPLICABLE = "INAPPLICABLE"
A_VERIFIER_HUMAIN = "A_VERIFIER_HUMAIN"

STATUTS = (CONFORME, ECART, INAPPLICABLE, A_VERIFIER_HUMAIN)


@dataclass(frozen=True)
class LigneBudget:
    """Une ligne du budget previsionnel, telle que le syndic la presente.

    `compte_brut` est conserve tel quel: c'est la seule facon de rendre compte
    d'un regroupement de presentation sans le maquiller en compte reel.
    """

    compte_brut: str
    libelle: str = ""
    montant: float | None = None


@dataclass(frozen=True)
class BudgetPrevisionnel:
    """Le budget soumis au vote."""

    exercice_debut: date | None = None
    exercice_fin: date | None = None
    lignes: tuple[LigneBudget, ...] = ()
    total_charges: float | None = None
    total_produits: float | None = None


@dataclass(frozen=True)
class Vote:
    """La decision d'assemblee qui porte le budget."""

    date_assemblee: date | None = None
    article_majorite: str | None = None
    adopte: bool | None = None
    budget_precedent_vote: float | None = None
    autorisation_provisions_transitoires: bool | None = None
    provisions_transitoires_appelees: int | None = None
    assiette_provisions_transitoires: float | None = None
    modalites_de_provision_votees: bool | None = None
    montant_provision_periodique: float | None = None


@dataclass(frozen=True)
class Convocation:
    """Ce qui a ete notifie au plus tard en meme temps que l'ordre du jour."""

    projet_budget_notifie: bool | None = None
    comparatif_dernier_budget_vote_notifie: bool | None = None
    presentation_conforme_annexe2: bool | None = None
    question_suspension_cotisation_inscrite: bool | None = None


@dataclass(frozen=True)
class Annexes:
    """Totaux des annexes, dans le seul perimetre du vote du budget.

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

    Les totaux modelises ici restent ceux dont l'article 10 parle
    explicitement, ce qui est un choix de perimetre et non plus une lacune de
    source.
    """

    total_charges_annexe2_courantes: float | None = None
    total_charges_annexe3_courantes: float | None = None
    solde_fonds_travaux: float | None = None


@dataclass(frozen=True)
class Copropriete:
    """Le contexte sans lequel plusieurs controles n'ont pas de sens."""

    destination_habitation: bool | None = None
    date_reception_travaux_construction: date | None = None
    plan_pluriannuel_adopte: bool | None = None
    montant_travaux_plan_adopte: float | None = None
    premier_exercice: bool | None = None
    cloture_exercice_precedent: date | None = None
    avance_reserve_prevue_reglement: float | None = None
    cotisation_fonds_travaux_votee: float | None = None
    concertation_conseil_syndical_tracee: bool | None = None
    annexes_archivees_avec_pv: bool | None = None


@dataclass(frozen=True)
class Dossier:
    """Tout ce qu'un controle peut lire. Rien d'autre n'est autorise."""

    budget: BudgetPrevisionnel = field(default_factory=BudgetPrevisionnel)
    vote: Vote = field(default_factory=Vote)
    convocation: Convocation = field(default_factory=Convocation)
    annexes: Annexes = field(default_factory=Annexes)
    copropriete: Copropriete = field(default_factory=Copropriete)
    reference: str = ""


@dataclass(frozen=True)
class Constat:
    """Le resultat d'un controle, avec ce qui lui a manque le cas echeant."""

    controle: str
    statut: str
    enonce: str
    message: str
    sources: tuple[str, ...] = ()
    legiartis: tuple[str, ...] = ()
    entrees_manquantes: tuple[str, ...] = ()
    ne_prouve_pas: str = ""

    def __post_init__(self) -> None:
        if self.statut not in STATUTS:
            raise ValueError(f"statut inconnu: {self.statut!r}")
        if self.statut == INAPPLICABLE and not self.entrees_manquantes:
            raise ValueError(
                f"{self.controle}: un constat INAPPLICABLE doit nommer "
                "l'entree qui manque, sinon il ne sert a rien"
            )


def manquantes(**entrees: object) -> tuple[str, ...]:
    """Noms des entrees restees a `None`, dans l'ordre de declaration."""
    return tuple(nom for nom, valeur in entrees.items() if valeur is None)
