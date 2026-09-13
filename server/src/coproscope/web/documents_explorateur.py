# -*- coding: utf-8 -*-
"""L'explorateur des documents CLASSES: famille, puis exercice, puis la piece.

`RM-2026-0183`, recette de Brice du 2026-09-13: *pour les documents, prevois un
genre d'explorateur avec les documents classes*. La page listait douze lignes
d'un registre qui en porte des centaines; un lecteur ne pouvait pas y retrouver
une piece sans connaitre son nom.

**UNE SEULE SOURCE.** L'arbre se calcule depuis les lignes du registre des
documents que la page recoit deja - pas depuis un second comptage. Chaque nombre
affiche est la taille d'une branche, et la somme des branches est le registre.

**RIEN NE DISPARAIT FAUTE DE CLASSEMENT.** Un document sans famille, sans type
ou dont le classement est a reprendre va sous *Non classes*, qui reste visible;
un document sans date lisible va sous *Sans date lue*, dans sa famille. Une
famille que ce module ne connait pas reste une branche, avec toutes ses pieces.

**MAIS ELLE N'AFFICHE PAS SON NOM DE REGISTRE.** La colonne `lot` peut porter
une valeur ecrite par un tiers, et `test_ui_nom_de_fichier_ne_fuit_pas` l'a vue
sortir sur la page au premier passage - dans le libelle ET dans l'adresse du
filtre. Une famille inconnue s'affiche donc *Famille non reconnue*, numerotee,
et son adresse porte une empreinte courte de la valeur, jamais la valeur.
"""
from __future__ import annotations

import hashlib
from typing import Any, Iterable, Mapping
from urllib.parse import urlencode

NON_CLASSES = "__non_classes__"
SANS_DATE = "__sans_date__"

#: libelle d'une famille (colonne `lot` du registre). Habillage seulement.
LIBELLES: dict[str, str] = {
    "AG": "Assemblées générales",
    "Assurance": "Assurance",
    "Communication": "Courriers et échanges",
    "Comptes": "Comptes",
    "Conseil_Syndical": "Conseil syndical",
    "Contentieux": "Contentieux",
    "Contrats": "Contrats",
    "Factures_Fournisseurs": "Devis et factures",
    "Incidents": "Incidents et sinistres",
    "Syndic": "Syndic",
    "Travaux": "Travaux",
}

#: statuts de classement qui ne valent pas classement.
A_CLASSER = frozenset({"", "PENDING", "A_RECLASSER", "A_CLASSER"})


def _texte(row: Mapping[str, Any], cle: str) -> str:
    return str(row.get(cle) or "").strip()


PREFIXE_INCONNUE = "autre-"


def famille_de(row: Mapping[str, Any]) -> str:
    """La cle PUBLIQUE de la branche d'un document.

    `NON_CLASSES` si le registre ne le classe pas; la valeur du registre si ce
    module la connait; sinon une empreinte courte, qui separe deux familles
    inconnues sans jamais ecrire ce qu'elles valent.
    """
    if _texte(row, "classification_status").upper() in A_CLASSER:
        return NON_CLASSES
    lot = _texte(row, "lot")
    if not lot or not _texte(row, "document_type"):
        return NON_CLASSES
    if lot in LIBELLES:
        return lot
    return PREFIXE_INCONNUE + hashlib.sha256(lot.encode("utf-8")).hexdigest()[:10]


def exercice_de(row: Mapping[str, Any]) -> str:
    date = _texte(row, "suspected_date")
    return date[:4] if len(date) >= 4 and date[:4].isdigit() else SANS_DATE


def libelle_famille(cle: str) -> str:
    if cle == NON_CLASSES:
        return "Non classés"
    return LIBELLES.get(cle, "Famille non reconnue")


def libelle_exercice(cle: str) -> str:
    return "Sans date lue" if cle == SANS_DATE else cle


def _href(**parametres: str) -> str:
    utiles = {k: v for k, v in parametres.items() if v}
    return "/documents" + ("?" + urlencode(utiles) if utiles else "")


def _document(row: Mapping[str, Any]) -> dict[str, str]:
    return {
        "doc_id": _texte(row, "doc_id"),
        "titre": _texte(row, "display_file_name") or _texte(row, "display_doc_id") or "Document",
        "reference": _texte(row, "display_doc_id"),
        "type": _texte(row, "display_document_type"),
        "date": _texte(row, "suspected_date") or "date non lue",
        "lecture": "texte lu" if _texte(row, "text_quality") in {"strong", "medium"} else "lecture a verifier",
        "href": _texte(row, "detail_href"),
    }


def _cle_famille(cle: str) -> tuple[int, str, str]:
    return (1 if cle == NON_CLASSES else 0, libelle_famille(cle).lower(), cle)


def _cle_exercice(cle: str) -> tuple[int, str]:
    return (1, "") if cle == SANS_DATE else (0, "%s" % (9999 - int(cle)))


def construire_arbre(rows: Iterable[Mapping[str, Any]], famille: str = "", exercice: str = "") -> dict[str, Any]:
    groupes: dict[str, dict[str, list[Mapping[str, Any]]]] = {}
    total = 0
    for row in rows:
        groupes.setdefault(famille_de(row), {}).setdefault(exercice_de(row), []).append(row)
        total += 1

    def trier(lignes: list[Mapping[str, Any]]) -> list[dict[str, str]]:
        docs = [_document(r) for r in lignes]
        return sorted(docs, key=lambda d: (d["date"] == "date non lue", "" if d["date"] == "date non lue" else _inverse(d["date"]), d["titre"].lower()))

    familles = []
    inconnues = [c for c in sorted(groupes, key=_cle_famille) if c.startswith(PREFIXE_INCONNUE)]
    for cle_f in sorted(groupes, key=_cle_famille):
        exercices = []
        for cle_e in sorted(groupes[cle_f], key=_cle_exercice):
            lignes = groupes[cle_f][cle_e]
            exercices.append({
                "cle": cle_e,
                "libelle": libelle_exercice(cle_e),
                "n": len(lignes),
                "href": _href(famille=cle_f, exercice=cle_e),
                "actif": cle_f == famille and cle_e == exercice,
                "documents": trier(lignes),
            })
        familles.append({
            "cle": cle_f,
            "libelle": libelle_famille(cle_f) + (
                " %d" % (inconnues.index(cle_f) + 1) if len(inconnues) > 1 and cle_f in inconnues else ""),
            "n": sum(e["n"] for e in exercices),
            "href": _href(famille=cle_f),
            "actif": cle_f == famille,
            "a_classer": cle_f == NON_CLASSES,
            "exercices": exercices,
        })

    if famille in groupes and exercice in groupes[famille]:
        choisis = groupes[famille][exercice]
        titre = "%s, %s" % (libelle_famille(famille), libelle_exercice(exercice))
    elif famille in groupes:
        choisis = [r for lignes in groupes[famille].values() for r in lignes]
        titre = libelle_famille(famille)
    else:
        choisis = [r for f in groupes.values() for lignes in f.values() for r in lignes]
        titre = "Toutes les pièces"
    return {
        "total": total,
        "familles": familles,
        "selection": {"titre": titre, "n": len(choisis), "documents": trier(choisis),
                      "filtre": bool(famille in groupes), "tout_href": _href()},
    }


def _inverse(date: str) -> str:
    """Tri decroissant sur une date ISO sans convertir: chaque chiffre est complemente."""
    return "".join(chr(ord("9") - ord(c) + ord("0")) if c.isdigit() else c for c in date)
