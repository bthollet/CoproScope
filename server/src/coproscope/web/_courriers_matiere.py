# -*- coding: utf-8 -*-
"""Les courriers a ecrire, lus dans ce que la chaine a deja calcule.

**Ce que cet ecran faisait jusqu'au 2026-09-11, et le defaut n'est pas celui
qu'on attend.** Il affichait trois brouillons de courrier inventes. Ces trois
lignes ne trompaient personne: chaque identifiant portait le mot `FICTIF` -
`DRAFT-FICTIF-01`, `SYNDIC-FICTIF` - et le bandeau annoncait *Scenario FICTIF*.

**Le vrai defaut etait que la page se contredisait elle-meme.** Le bandeau
annoncait *3 brouillons a valider* alors qu'**un seul** des trois portait ce
statut; il annoncait *2 preuves a rattacher* alors que le tableau juste en
dessous en comptait **trois**. Deux comptages ecrits a la main, pour la meme
notion, sur le meme ecran, qui ne tombaient pas d'accord - c'est le defaut
numero un du produit, en miniature et a trois centimetres de distance.

**Ce qui les remplace existe deja et n'a demande aucune table nouvelle.** La
chaine produit un rapport *pieces a demander*: chaque ligne y porte le sujet,
la piece attendue, la raison, la priorite, le statut et la diligence suggeree.
**C'est litteralement une liste de courriers a envoyer, deja calculee.** Mesure
du 2026-09-11 sur une instance VIDE reabsorbant 858 pieces sources: **6 lignes
reelles**, dont 5 en priorite haute; 4 au statut *a classer* - une piece
candidate existe mais son rangement est incertain - et 2 *absentes*, rien dans
le corpus n'y repond.

**UNE COLONNE EST RETIREE PLUTOT QUE REMPLIE DE VIDE: le destinataire.** L'ecran
en avait une. Le registre des documents porte bien une colonne d'emetteur:
**elle est vide sur les 60 documents de correspondance, sans exception**. Pour
les douze vraies lettres du corpus, la liste des destinataires existe - mais a
l'interieur d'un document, pas comme donnee. Afficher une colonne vide sur
chaque ligne apprend au lecteur a ne plus la regarder; la retirer dit la verite:
**a qui on ecrit n'est pas une donnee que ce produit connait aujourd'hui.**

**UN FILTRE N'A PAS ETE POSE, et c'est mesure.** Il aurait ete naturel de lister
les courriers deja ecrits en filtrant le registre sur le type *Communication*.
Mesure sur les douze vraies lettres du corpus - meme dossier, meme jour, meme
nature: **6 seulement portent ce type**. Quatre sont typees *Convocation d'AG*,
une *Etat descriptif de division*, une *Reglement de copropriete*. Le filtre
raterait donc la moitie des courriers, et dans l'autre sens *Convocation d'AG*
compte 39 documents dont 4 lettres. **Un filtre qui rate la moitie de sa
population et en ramasse trente-cinq de trop n'est pas un filtre.** Le nom du
dossier d'origine, lui, serait fiable sur ce corpus - mais c'est une modalite
d'un seul cabinet, et la regle des axes l'interdit.

**Hors des valeurs observees.** Pas de rapport produit, rapport present mais
vide, rapport avec des lignes: les trois se distinguent et se disent. Le
deuxieme n'est pas un ecran vide - c'est *la chaine a tourne et n'a rien trouve
a demander*, ce qui est une bonne nouvelle et doit se lire comme telle.
"""

from __future__ import annotations

import csv
import unicodedata
from pathlib import Path
from typing import Any

__all__ = [
    "CHAINE_NON_PASSEE",
    "PRET",
    "RIEN_A_DEMANDER",
    "matiere_de_courriers",
]

CHAINE_NON_PASSEE = "chaine_non_passee"
RIEN_A_DEMANDER = "rien_a_demander"
PRET = "pret"

RAPPORT_DEMANDES = "pieces_a_demander.csv"
RAPPORT_COMPLETUDE = "matrice_completude_documentaire.csv"

#: Ce que la matrice de completude appelle une preuve d'envoi. Le libelle est
#: lu, jamais l'identifiant de ligne: un identifiant est un rang dans un
#: fichier, et il bouge au premier ajout.
#:
#: **La comparaison ignore les accents, et ce n'est pas un detail de confort.**
#: Le corpus mesure ecrit `accuses de reception` sans accent - c'est une sortie
#: d'extraction - la ou un libelle redige a la main ecrit `accuses` avec.
#: Un filtre sensible a l'accent aurait donc trouve la ligne sur le corpus reel
#: et l'aurait ratee partout ailleurs: exactement une modalite prise pour un
#: axe. L'accent porte de l'orthographe, jamais du sens.
_MOTS_PREUVE_ENVOI = ("preuve", "accuse")


def _lignes(chemin: Path) -> list[dict[str, str]]:
    if not chemin.exists() or not chemin.is_file():
        return []
    with chemin.open("r", encoding="utf-8-sig", newline="") as flux:
        return [dict(ligne) for ligne in csv.DictReader(flux)]


def _dossier_rapports(instance: Any | None) -> Path | None:
    if instance is None:
        return None
    try:
        return Path(instance.artifact("reports_dir"))
    except (AttributeError, KeyError, TypeError, ValueError, OSError):
        return None


def _texte(valeur: Any) -> str:
    return str(valeur or "").strip()


def _sans_accent(brut: str) -> str:
    decompose = unicodedata.normalize("NFD", str(brut or "").lower())
    return "".join(c for c in decompose if unicodedata.category(c) != "Mn")


def _brouillon(ligne: dict[str, str], rang: int) -> dict[str, str]:
    """Une ligne de courrier a ecrire, telle que la chaine l'a calculee."""
    statut = _texte(ligne.get("status"))
    return {
        "id": _texte(ligne.get("request_id")) or "DEM-%02d" % rang,
        "subject": _texte(ligne.get("subject")) or "Sujet non lu",
        "piece": _texte(ligne.get("expected_piece")),
        "reason": _texte(ligne.get("reason")),
        "priority": _texte(ligne.get("priority")),
        "status": statut,
        # **Pas de destinataire.** Il n'existe nulle part comme donnee, et une
        # colonne vide sur chaque ligne apprend a ne plus la regarder.
        "mandate": _texte(ligne.get("suggested_diligence")),
    }


def matiere_de_courriers(instance: Any | None) -> dict[str, Any]:
    """Ce qu'il y a reellement a demander, ou pourquoi il n'y a rien."""
    vide = {
        "etat": CHAINE_NON_PASSEE,
        "message": "Les rapports de la chaîne n'ont pas encore été produits "
                   "pour cette copropriété.",
        "action": "Lancez le traitement des documents : c'est lui qui calcule "
                  "les pièces à demander.",
        "brouillons": [], "compte": 0, "haute_priorite": 0,
        "preuves_attendues": [],
    }
    dossier = _dossier_rapports(instance)
    if dossier is None or not dossier.exists():
        return vide

    demandes = _lignes(dossier / RAPPORT_DEMANDES)
    if not demandes:
        return {
            "etat": RIEN_A_DEMANDER,
            "message": "Aucune pièce n'est à demander au syndic aujourd'hui.",
            "action": "Rien à écrire de ce côté. Cette page se remplira si un "
                      "contrôle trouve une pièce manquante.",
            "brouillons": [], "compte": 0, "haute_priorite": 0,
            "preuves_attendues": [],
        }

    brouillons = [_brouillon(l, n) for n, l in enumerate(demandes, start=1)]
    # La priorite haute passe devant; a l'interieur, l'ordre du rapport est
    # conserve - c'est celui que la chaine a calcule, et le reordonner ici
    # fabriquerait un second classement concurrent du sien.
    brouillons.sort(key=lambda b: b["priority"] != "P1")

    preuves = [
        {
            "id": _texte(l.get("proof_id")),
            "label": _texte(l.get("expected_label")),
            "status": _texte(l.get("status")),
            "criticality": _texte(l.get("criticality")),
            "reason": _texte(l.get("reason")),
            "rattaches": len([d for d in _texte(l.get("matched_doc_ids")).split(";") if d.strip()]),
        }
        for l in _lignes(dossier / RAPPORT_COMPLETUDE)
        if all(mot in _sans_accent(l.get("expected_label"))
               for mot in _MOTS_PREUVE_ENVOI)
    ]

    return {
        "etat": PRET,
        "message": "",
        "action": "",
        "brouillons": brouillons,
        # **Un seul comptage, et il compte la liste affichee.** Le bandeau
        # annoncait des nombres ecrits a la main qui contredisaient le tableau
        # situe juste en dessous.
        "compte": len(brouillons),
        "haute_priorite": len([b for b in brouillons if b["priority"] == "P1"]),
        "preuves_attendues": preuves,
    }
