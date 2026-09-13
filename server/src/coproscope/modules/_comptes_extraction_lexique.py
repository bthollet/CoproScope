"""Reconnaissance des jetons d'un tableau comptable, sans profil de cabinet.

Ce fichier ne connait aucun cabinet. Il ne sait que repondre a des questions
elementaires sur une chaine: est-ce un montant, un taux, un compte, une date,
une reference de piece. Les reponses sont assez pauvres pour rester vraies chez
un cabinet qui n'a pas encore ete lu.

Deux axes sont resolus ici, et un seul est resolu par mesure et non par
convention.

`separateur_decimal`. Il est **detecte sur le document**, jamais suppose. Les
deux modalites observees sont la virgule et le point; la detection compte les
occurrences des deux formes completes et tranche a la majorite. Hors des deux
modalites observees, la detection rend `None` et l'appelant devra le dire au
lieu de lire des nombres faux.

`taux de T.V.A.`. Un nombre n'est un taux que s'il appartient a une plage
plausible **et** que l'identite de taxe incluse retombe au centime. C'est
volontairement plus strict qu'une liste de taux en vigueur: une liste ferme la
porte a un taux non encore observe, l'identite non.
"""

from __future__ import annotations

import re
from decimal import Decimal, InvalidOperation

# Un montant, dans les deux notations observees. Le groupe de tete admet les
# separateurs de milliers usuels: espace, espace insecable, apostrophe.
_MONTANT_VIRGULE = re.compile(r"^-?\d{1,3}(?:[  '.]\d{3})*,\d{2}$")
_MONTANT_POINT = re.compile(r"^-?\d{1,3}(?:[  ',]\d{3})*\.\d{2}$")
_MONTANT_NU = re.compile(r"^-?\d+$")

# Une date jour/mois/annee, sur deux ou quatre chiffres d'annee.
_DATE = re.compile(r"^(\d{2})/(\d{2})/(\d{2}|\d{4})$")

# Un numero de compte du plan comptable de la copropriete: au moins trois
# chiffres, eventuellement suivi de zeros de cadrage. Le module ne juge pas
# l'appartenance a la nomenclature, c'est le travail du module budget.
_COMPTE = re.compile(r"^(\d{3,8})$")

# Marqueur accole a un montant chez au moins un cabinet: `1 133,00 T14`.
# La lettre et son eventuel indice sont retires du montant et conserves a part.
_MARQUEUR = re.compile(r"^(?P<nombre>.*?)\s+(?P<marqueur>[A-Z]\d{0,3})$")

# Plage de taux plausible. Elle borne, elle n'enumere pas: un taux inconnu mais
# compris dans la plage reste candidat, et c'est l'identite de taxe incluse qui
# tranche.
TAUX_MINIMUM = Decimal("0")
TAUX_MAXIMUM = Decimal("30")

# Tolerance d'arrondi sur l'identite de taxe incluse, en euros.
TOLERANCE_TVA = Decimal("0.02")

VIRGULE = ","
POINT = "."


def detecter_separateur_decimal(lignes: list[str]) -> str | None:
    """Separateur decimal majoritaire du document, ou `None` si indecidable.

    Compte les jetons entierement conformes a chacune des deux notations. Un
    document qui n'en contient aucune, ou qui en contient autant des deux, rend
    `None`: c'est un refus de lire, pas un defaut.
    """
    virgules = 0
    points = 0
    for brut in lignes:
        for jeton in brut.split():
            nettoye = _sans_marqueur(jeton)[0]
            if _MONTANT_VIRGULE.match(nettoye):
                virgules += 1
            elif _MONTANT_POINT.match(nettoye):
                points += 1
    if virgules == points:
        return None
    return VIRGULE if virgules > points else POINT


def _sans_marqueur(jeton: str) -> tuple[str, str]:
    """Separe un montant de son marqueur de cle accole, s'il en porte un."""
    trouve = _MARQUEUR.match(jeton.strip())
    if trouve is None:
        return jeton.strip(), ""
    return trouve.group("nombre").strip(), trouve.group("marqueur")


def lire_montant(brut: str, separateur: str) -> Decimal | None:
    """Montant porte par `brut`, dans la notation `separateur`, sinon `None`.

    La notation opposee est refusee explicitement: lire `1.234` comme mille deux
    cent trente-quatre dans un document a virgule decimale produirait une erreur
    d'un facteur mille sans aucun signe visible.
    """
    nettoye, _ = _sans_marqueur(brut)
    if not nettoye:
        return None
    attendu = _MONTANT_VIRGULE if separateur == VIRGULE else _MONTANT_POINT
    if attendu.match(nettoye):
        sans_milliers = re.sub(r"[  ']", "", nettoye)
        if separateur == VIRGULE:
            sans_milliers = sans_milliers.replace(".", "").replace(",", ".")
        else:
            sans_milliers = sans_milliers.replace(",", "")
        try:
            return Decimal(sans_milliers)
        except InvalidOperation:  # pragma: no cover - filtre par la regex
            return None
    return None


def marqueur_de(brut: str) -> str:
    """Marqueur de cle accole au montant, ou chaine vide."""
    return _sans_marqueur(brut)[1]


def est_date(brut: str) -> bool:
    """Vrai si `brut` a la forme d'une date jour/mois/annee."""
    trouve = _DATE.match(brut.strip())
    if trouve is None:
        return False
    jour = int(trouve.group(1))
    mois = int(trouve.group(2))
    return 1 <= jour <= 31 and 1 <= mois <= 12


def est_compte(brut: str) -> bool:
    """Vrai si `brut` a la forme d'un numero de compte."""
    return _COMPTE.match(brut.strip()) is not None


def normaliser_compte(brut: str) -> str:
    """Numero de compte sans ses zeros de cadrage a droite.

    `601000` et `601` designent le meme poste chez deux cabinets differents. La
    normalisation ne retire jamais le dernier chiffre significatif: `700` reste
    `700`, il ne devient pas `7`.
    """
    nettoye = brut.strip()
    if not est_compte(nettoye):
        return nettoye
    reduit = nettoye.rstrip("0")
    return reduit if len(reduit) >= 3 else nettoye[:3]


def taxe_incluse(montant: Decimal, taux: Decimal) -> Decimal:
    """Taxe **comprise dans** `montant` au taux `taux`, arrondie au centime.

    C'est l'identite mesuree sur le corpus: la colonne du montant a repartir est
    un toutes taxes comprises, et la colonne de taxe donne la part incluse. Un
    outil qui lirait la premiere comme un hors taxes gonflerait chaque ligne.
    """
    if taux <= 0:
        return Decimal("0.00")
    brute = montant * taux / (Decimal("100") + taux)
    return brute.quantize(Decimal("0.01"))


def taxe_ajoutee(montant: Decimal, taux: Decimal) -> Decimal:
    """Taxe **ajoutee a** `montant` au taux `taux`, arrondie au centime.

    Sert uniquement a departager les deux conventions possibles d'une colonne de
    montant. Le corpus lu ne l'utilise pas, mais un cabinet qui publierait des
    hors taxes serait invisible sans elle.
    """
    if taux <= 0:
        return Decimal("0.00")
    return (montant * taux / Decimal("100")).quantize(Decimal("0.01"))


def est_taux_plausible(valeur: Decimal) -> bool:
    """Vrai si `valeur` tombe dans la plage des taux de taxe plausibles."""
    return TAUX_MINIMUM <= valeur <= TAUX_MAXIMUM


def identite_taxe_tient(
    montant: Decimal,
    taux: Decimal,
    taxe: Decimal,
    *,
    incluse: bool = True,
) -> bool:
    """Vrai si `taxe` est bien la taxe portee par `montant` au taux `taux`."""
    attendue = taxe_incluse(montant, taux) if incluse else taxe_ajoutee(montant, taux)
    return abs(attendue - taxe) <= TOLERANCE_TVA
