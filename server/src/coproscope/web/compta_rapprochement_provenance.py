"""D'ou vient le montant affiche dans une cellule de rapprochement.

Lot `RM-2026-0075`, extrait de `compta_rapprochement_view` qui atteignait la
limite de 600 lignes du depot.

Le rapprochement confronte plusieurs sources sur une meme depense: la facture,
la ligne de l'etat des depenses, l'ecriture comptable, le mouvement bancaire.
Leur DESACCORD est l'objet meme de l'ecran - c'est lui qui produit la question
a poser au syndic.

Un helper qui rendait la premiere valeur presente sans dire de quelle colonne
elle venait effacait donc exactement ce que l'ecran est cense montrer. Le
montant lu sur la ligne comptable s'affichait dans une cellule intitulee
`Facture`, avec la consigne d'aller le retrouver dans la piece - consigne
fausse des que la valeur ne vient pas de la piece.
"""

from __future__ import annotations

import re
from typing import Any, Mapping

#: Nom lisible des colonnes de montant, pour l'afficher a cote du chiffre.
#: `ttc` vient de la facture, `montant_depense` de la ligne comptable: deux
#: grandeurs qui peuvent legitimement differer.
ORIGINE_MONTANT = {
    "ttc": "la facture",
    "montant_depense": "la ligne de depenses",
    "amount": "la ligne de depenses",
    "statement_amount": "l'etat des depenses",
}

_MARQUEURS_VIDES = {"", "vid", "vide", "nan", "none", "null", "na", "nd"}


def est_marqueur_vide(value: Any) -> bool:
    """Vrai pour les valeurs qui disent `rien`, quelle qu'en soit l'orthographe."""

    normalized = re.sub(r"[^a-z0-9]+", "", str(value or "").strip().lower())
    return normalized in _MARQUEURS_VIDES


def premiere_valeur_et_source(row: Mapping[str, Any], *fields: str) -> tuple[str, str]:
    """La premiere valeur presente, ET le nom du champ qui l'a fournie.

    Rendre le nom du champ ne coute rien au site d'appel et lui redonne le
    choix: afficher la provenance, ou l'ignorer en connaissance de cause. La
    version qui jetait ce nom ne laissait pas ce choix.
    """

    for field in fields:
        value = str(row.get(field) or "").strip()
        if value and not est_marqueur_vide(value):
            return value, field
    return "", ""


def premiere_valeur(row: Mapping[str, Any], *fields: str) -> str:
    """La premiere valeur presente, quand la provenance n'est pas affichee."""

    return premiere_valeur_et_source(row, *fields)[0]


def signal_montant(montant: str, champ: str) -> str:
    """Le signal affiche dans la cellule facture, avec la source du montant.

    Une source inconnue ne fabrique pas de mention: mieux vaut un signal sans
    provenance qu'une provenance inventee.
    """

    if not montant:
        return ""
    origine = ORIGINE_MONTANT.get(champ, "")
    if not origine:
        return f"Montant a retrouver: {montant} EUR"
    return f"Montant a retrouver: {montant} EUR, lu sur {origine}"
