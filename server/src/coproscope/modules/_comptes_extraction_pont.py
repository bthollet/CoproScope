"""Le pont entre l'etat des depenses lu et le module comptable. Lot `RM-2026-0074`.

======================================================================
Ce qui manquait, et ce qui ne manquait pas
======================================================================

`RM-2026-0074` a ete ouvert sur le constat que l'extracteur d'etat des depenses
n'existait pas. Mesure du 2026-09-08: **il existe**. `lire_etat_depenses` lit
la couche de texte et retombe au centime sur le total imprime des quatre
exercices du premier cabinet - 2022, 2023, 2024, 2025 - dont l'exercice 2025
sur lequel `RM-2026-0064` avait etabli a la main un etalon de `357 493,10`.

Ce qui manque est le **pont**. `_load_expense_statement_lines` attend un CSV
pre-existant, et seul `demoops` en fabrique un, en recopiant des fixtures. Sur
une instance reelle ce fichier n'existe jamais, donc le module comptable tourne
a vide alors que la lecture, elle, fonctionne. Ecrire un second extracteur
aurait ete la pire reponse: deux comptages concurrents pour la meme notion,
qui est le defaut numero un du produit.

======================================================================
La regle d'admission, et pourquoi elle n'est pas une liste de cas
======================================================================

Un pont naif recopierait les lignes de tout document qu'on lui donne. Mesure
sur le second cabinet, 22 documents, aucun n'etant un etat des depenses:
**sept d'entre eux rendent quand meme des lignes**, 1 014 au total, pour une
somme de l'ordre de 2 798 919 EUR. Parmi les producteurs: un **contrat de
syndic** (1 ligne) et deux jeux de **devis**. Les annexes reglementaires de
2025 rendent a elles seules 211 lignes et 948 327,15 EUR, pour une copropriete
dont les annexes affichent 159 000,00 de charges nettes.

Un pont sans regle d'admission aurait donc affiche un total faux d'un facteur
six, sans aucune erreur visible, sur un corpus parfaitement ordinaire.

*L'axe*: **la granularite de la piece comptable fournie**. Un cabinet publie un
etat detaille, une ligne par ecriture; un autre ne publie que les annexes
reglementaires, une ligne par compte. Rien n'oblige un troisieme a choisir
l'une de ces deux granularites.

*L'invariant le long de l'axe*: **un document qui publie un detail publie aussi
le total de ce detail.** Un etat des depenses ferme ses rubriques, ses comptes
et son document par des totaux imprimes - c'est ce qui en fait une piece
opposable, et cela ne depend d'aucun cabinet. Un document qui ne ferme rien
n'est pas un etat des depenses, quel que soit son vocabulaire.

*Ce que le code en fait*: l'admission est une **conservation**, pas une liste de
temoins. Le document est admis si, et seulement si, il publie un total general
et si la somme de ses lignes retombe dessus a la tolerance du centime. Une
conservation signale sa propre panne; une liste de cas ne le fait jamais.

*Hors des valeurs observees*: un troisieme cabinet dont le gabarit est inconnu
mais qui publie detail et totaux passe le controle si son arithmetique tient,
sans que rien n'ait ete code pour lui. S'il ne le passe pas, il est **refuse en
nommant l'ecart**, jamais admis a moitie. Le mode degrade est le refus, et le
refus est chiffre.

Piege ecarte a dessein: un temoin de vocabulaire - le titre `ETAT DES
DEPENSES`, le mot `copropriete`, la mention `MONTANT A REPARTIR` - aurait
suffi sur ce corpus-ci. C'est precisement le variant deguise en invariant que
la doctrine du depot interdit: il code l'habitude d'un cabinet. Le titre est
donc lu, mais seulement comme **indice rapporte**, jamais comme condition.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal

from ._comptes_extraction_etat import lire_etat_depenses
from ._comptes_extraction_modele import EtatDepenses, LigneEtat

#: Tolerance de la conservation. Le document publie des montants au centime, et
#: les totaux imprimes du premier cabinet retombent exactement; la tolerance ne
#: couvre donc que l'arrondi de sommation, pas un ecart metier.
TOLERANCE = Decimal("0.01")

# Motifs d'admission ou de refus. Ils sont rendus tels quels a l'appelant, qui
# les affiche: aucun n'est un code interne muet.
ADMIS = "ADMIS"
REFUS_TOTAL_ABSENT = "REFUS_TOTAL_GENERAL_ABSENT"
REFUS_CONSERVATION = "REFUS_CONSERVATION_NON_TENUE"
REFUS_AUCUNE_LIGNE = "REFUS_AUCUNE_LIGNE"

_MOTIFS_LISIBLES = {
    ADMIS: "Le document publie son total general et la somme de ses lignes retombe dessus.",
    REFUS_TOTAL_ABSENT: (
        "Le document ne publie aucun total general. Rien ne permet de verifier "
        "que ses lignes forment un etat des depenses complet."
    ),
    REFUS_CONSERVATION: (
        "La somme des lignes lues ne retombe pas sur le total general imprime. "
        "La lecture est incomplete ou le document n'est pas un etat des depenses."
    ),
    REFUS_AUCUNE_LIGNE: "Aucune ligne de depense n'a ete lue dans ce document.",
}


@dataclass(frozen=True)
class Admission:
    """Le verdict d'admission d'un document, avec de quoi le contester.

    Tous les champs chiffres sont conserves meme en cas de refus: un refus qui
    ne dit pas de combien il rate n'est pas verifiable.
    """

    admis: bool = False
    motif: str = REFUS_AUCUNE_LIGNE
    total_imprime: Decimal | None = None
    somme_lignes: Decimal = Decimal("0.00")
    ecart: Decimal | None = None
    nombre_lignes: int = 0
    lignes: tuple[LigneEtat, ...] = ()
    constats: tuple[str, ...] = ()

    @property
    def explication(self) -> str:
        """Le motif en francais, pour un lecteur qui n'est pas comptable."""

        base = _MOTIFS_LISIBLES.get(self.motif, self.motif)
        if self.motif == REFUS_CONSERVATION and self.ecart is not None:
            return f"{base} Ecart mesure: {self.ecart} EUR."
        return base


def _somme(lignes: tuple[LigneEtat, ...] | list[LigneEtat]) -> Decimal:
    total = Decimal("0.00")
    for ligne in lignes:
        if ligne.montant_a_repartir is not None:
            total += ligne.montant_a_repartir
    return total


def admettre(etat: EtatDepenses) -> Admission:
    """Dit si un etat lu peut alimenter le module comptable, et pourquoi.

    L'ordre des controles va du plus structurel au plus fin, pour que le motif
    rendu soit le plus explicatif possible: un document sans total general ne
    doit pas etre refuse pour `conservation non tenue`, qui laisserait croire a
    une erreur d'arithmetique la ou il manque une piece entiere.
    """

    lignes = tuple(etat.lignes)
    codes = tuple(sorted({constat.code for constat in etat.constats}))
    somme = _somme(lignes)
    total = etat.total_general

    if not lignes:
        return Admission(
            motif=REFUS_AUCUNE_LIGNE, somme_lignes=somme, constats=codes, total_imprime=total
        )
    if total is None:
        return Admission(
            motif=REFUS_TOTAL_ABSENT,
            somme_lignes=somme,
            nombre_lignes=len(lignes),
            constats=codes,
        )

    ecart = somme - total
    if abs(ecart) > TOLERANCE:
        return Admission(
            motif=REFUS_CONSERVATION,
            total_imprime=total,
            somme_lignes=somme,
            ecart=ecart,
            nombre_lignes=len(lignes),
            constats=codes,
        )
    return Admission(
        admis=True,
        motif=ADMIS,
        total_imprime=total,
        somme_lignes=somme,
        ecart=ecart,
        nombre_lignes=len(lignes),
        lignes=lignes,
        constats=codes,
    )


def admettre_texte(texte: str) -> Admission:
    """Lit une couche de texte puis rend son verdict d'admission."""

    return admettre(lire_etat_depenses(texte))


def _identifiant(annee: int, rang: int) -> str:
    return f"DEP-{annee}-{rang:04d}"


def lignes_csv(admission: Admission, annee: int, source: str = "") -> list[dict[str, str]]:
    """Les lignes au format du contrat `expense.statement`, ou rien.

    Un refus ne rend **aucune** ligne. C'est la traduction directe de la regle
    d'admission: il n'existe pas d'etat des depenses a moitie lu. Rendre les
    lignes d'un document refuse laisserait l'appelant libre de les afficher, et
    la garantie ne serait plus une garantie.

    `source` doit etre un identifiant choisi par l'appelant, jamais un chemin
    local ni un nom de fichier brut: cette valeur est ecrite dans un CSV que
    l'interface lit.
    """

    if not admission.admis:
        return []
    rows: list[dict[str, str]] = []
    for rang, ligne in enumerate(admission.lignes, start=1):
        if ligne.montant_a_repartir is None:
            continue
        rows.append(
            {
                "statement_line_id": _identifiant(annee, rang),
                "date": ligne.date,
                "account": ligne.compte,
                "account_label": ligne.compte_libelle,
                "reference": ligne.reference_piece,
                # L'etat des depenses ne porte pas de colonne fournisseur: le
                # nom du tiers est dans le libelle, melange a l'objet. Le pont
                # ne devine pas de fournisseur - `RM-2026-0058` a mesure que 69
                # pour cent des valeurs distinctes d'une colonne fournisseur
                # devinee n'etaient pas des noms d'entreprise.
                "supplier_hint": "",
                "label": ligne.libelle,
                "amount": f"{ligne.montant_a_repartir:.2f}",
                "source": source,
            }
        )
    return rows


@dataclass(frozen=True)
class Conservation:
    """Le bilan chiffre d'une absorption, verifiable par soustraction.

    `admis + ecarte == lu` doit tenir par construction. La classe existe pour
    que cette egalite soit **affichable**, et donc contestable, plutot que
    supposee vraie parce que le code a l'air correct.
    """

    total_lu: Decimal = Decimal("0.00")
    total_admis: Decimal = Decimal("0.00")
    total_ecarte: Decimal = Decimal("0.00")
    documents_admis: int = 0
    documents_ecartes: int = 0
    motifs: tuple[tuple[str, str], ...] = ()

    @property
    def tient(self) -> bool:
        """L'egalite de conservation, verifiee et non postulee."""

        return abs((self.total_admis + self.total_ecarte) - self.total_lu) <= TOLERANCE


def absorber(pieces: dict[str, str], annee: int) -> tuple[list[dict[str, str]], Conservation]:
    """Absorbe un sac de pieces et rend les lignes admises avec leur bilan.

    `pieces` associe un identifiant sans donnee personnelle a une couche de
    texte. Le bilan nomme chaque piece ecartee et son motif: une piece qui
    disparait sans motif est indiscernable d'une piece jamais fournie.
    """

    lignes: list[dict[str, str]] = []
    total_lu = Decimal("0.00")
    total_admis = Decimal("0.00")
    total_ecarte = Decimal("0.00")
    admis = 0
    ecartes = 0
    motifs: list[tuple[str, str]] = []

    for identifiant in sorted(pieces):
        admission = admettre_texte(pieces[identifiant])
        total_lu += admission.somme_lignes
        if admission.admis:
            admis += 1
            total_admis += admission.somme_lignes
            lignes.extend(lignes_csv(admission, annee, source=identifiant))
            motifs.append((identifiant, ADMIS))
        else:
            ecartes += 1
            total_ecarte += admission.somme_lignes
            motifs.append((identifiant, admission.motif))

    # Les identifiants de ligne doivent rester uniques a travers le sac entier:
    # `_load_expense_statement_lines` deduplique sur `statement_line_id`, et
    # deux pieces numerotees chacune a partir de 1 se masqueraient l'une l'autre.
    for rang, row in enumerate(lignes, start=1):
        row["statement_line_id"] = _identifiant(annee, rang)

    return lignes, Conservation(
        total_lu=total_lu,
        total_admis=total_admis,
        total_ecarte=total_ecarte,
        documents_admis=admis,
        documents_ecartes=ecartes,
        motifs=tuple(motifs),
    )
