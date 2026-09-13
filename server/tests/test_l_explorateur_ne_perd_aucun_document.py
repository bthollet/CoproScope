# -*- coding: utf-8 -*-
"""L'explorateur des documents ne perd aucune piece, et ne compte rien deux fois.

`RM-2026-0183`, recette de Brice du 2026-09-13: un explorateur des documents
classes sur `/documents`.

**LE PREDICAT, ENONCE AVANT DE CHERCHER.** *Chaque ligne du registre des
documents apparait exactement une fois dans l'arbre, et la taille affichee de
chaque branche est le nombre de pieces qu'elle contient.* Une piece mal classee
ne doit pas sortir du regard: elle va sous *Non classes*, qui reste affiche.

**OU LA GARDE REGARDE.** Sur le modele que la page rend, construit depuis les
lignes du registre qu'elle recoit, et sur la page rendue: chaque document de
l'arbre y porte un lien vers sa fiche. Un temoin fabrique verifie que
l'instrument voit une piece perdue et une piece comptee deux fois.
"""
from __future__ import annotations

import re
import unittest
from collections import Counter

from coproscope.web.documents_explorateur import (
    NON_CLASSES, PREFIXE_INCONNUE, SANS_DATE, construire_arbre, famille_de)
from tests._exemple_copie import exemple_copie


def pieces_de_l_arbre(arbre: dict) -> list[str]:
    return [d["doc_id"] for f in arbre["familles"] for e in f["exercices"] for d in e["documents"]]


def ecarts(arbre: dict, attendus: list[str]) -> dict[str, list[str]]:
    vus = Counter(pieces_de_l_arbre(arbre))
    return {
        "perdues": sorted(set(attendus) - set(vus)),
        "doublees": sorted(k for k, n in vus.items() if n > 1),
        "tailles_fausses": sorted(
            "%s/%s" % (f["cle"], e["cle"]) for f in arbre["familles"] for e in f["exercices"]
            if e["n"] != len(e["documents"])
        ) + sorted(f["cle"] for f in arbre["familles"] if f["n"] != sum(len(e["documents"]) for e in f["exercices"])),
    }


LIGNES_TEMOIN = [
    {"doc_id": "D1", "lot": "AG", "document_type": "PV_AG", "classification_status": "AUTO_CLASSIFIED", "suspected_date": "2025-06-12"},
    {"doc_id": "D2", "lot": "AG", "document_type": "PV_AG", "classification_status": "AUTO_CLASSIFIED", "suspected_date": ""},
    {"doc_id": "D3", "lot": "", "document_type": "", "classification_status": "PENDING", "suspected_date": "2024-01-01"},
    {"doc_id": "D4", "lot": "Inconnue_Demain", "document_type": "X", "classification_status": "AUTO_CLASSIFIED", "suspected_date": "2023-02-02"},
    {"doc_id": "D5", "lot": "Comptes", "document_type": "Annexe", "classification_status": "A_RECLASSER", "suspected_date": "2024-03-31"},
]


class L_INSTRUMENT_VOIT_UNE_PIECE_PERDUE_OU_DOUBLEE(unittest.TestCase):
    def test_un_arbre_juste_ne_rend_aucun_ecart(self) -> None:
        arbre = construire_arbre(LIGNES_TEMOIN)
        self.assertEqual(ecarts(arbre, [r["doc_id"] for r in LIGNES_TEMOIN]),
                         {"perdues": [], "doublees": [], "tailles_fausses": []})

    def test_une_piece_retiree_et_une_piece_doublee_sont_vues(self) -> None:
        arbre = construire_arbre(LIGNES_TEMOIN)
        arbre["familles"][0]["exercices"][0]["documents"].pop()
        non_classes = arbre["familles"][-1]["exercices"][0]["documents"]
        non_classes.append(dict(non_classes[0]))
        vus = ecarts(arbre, [r["doc_id"] for r in LIGNES_TEMOIN])
        self.assertEqual(vus["perdues"], ["D1"])
        self.assertEqual(len(vus["doublees"]), 1)
        self.assertEqual(len(vus["tailles_fausses"]), 4)


class RIEN_NE_DISPARAIT_FAUTE_DE_CLASSEMENT(unittest.TestCase):
    def test_un_document_non_classe_va_sous_non_classes(self) -> None:
        self.assertEqual(famille_de(LIGNES_TEMOIN[2]), NON_CLASSES)
        self.assertEqual(famille_de(LIGNES_TEMOIN[4]), NON_CLASSES)

    def test_une_famille_inconnue_garde_ses_pieces_mais_pas_son_nom(self) -> None:
        """La colonne `lot` peut porter une valeur ecrite par un tiers: elle ne
        sort ni dans le libelle, ni dans l'adresse du filtre."""
        arbre = construire_arbre(LIGNES_TEMOIN)
        inconnue = [f for f in arbre["familles"] if f["cle"].startswith(PREFIXE_INCONNUE)]
        self.assertEqual([f["n"] for f in inconnue], [1])
        self.assertNotIn("Inconnue", repr(arbre))

    def test_deux_familles_inconnues_restent_deux_branches_distinguees(self) -> None:
        lignes = LIGNES_TEMOIN + [dict(LIGNES_TEMOIN[3], doc_id="D6", lot="Autre_Inconnue")]
        inconnues = [f for f in construire_arbre(lignes)["familles"] if f["cle"].startswith(PREFIXE_INCONNUE)]
        self.assertEqual(len({f["cle"] for f in inconnues}), 2)
        self.assertEqual(len({f["libelle"] for f in inconnues}), 2)

    def test_non_classes_vient_en_dernier_mais_reste_affiche(self) -> None:
        arbre = construire_arbre(LIGNES_TEMOIN)
        self.assertEqual(arbre["familles"][-1]["cle"], NON_CLASSES)
        self.assertEqual(arbre["familles"][-1]["n"], 2)

    def test_une_piece_sans_date_reste_dans_sa_famille(self) -> None:
        arbre = construire_arbre(LIGNES_TEMOIN)
        ag = [f for f in arbre["familles"] if f["cle"] == "AG"][0]
        self.assertEqual([e["cle"] for e in ag["exercices"]], ["2025", SANS_DATE])


class L_EXPLORATEUR_DE_LA_PAGE_PORTE_TOUT_LE_REGISTRE(unittest.TestCase):
    def test_sur_une_copie_de_l_exemple(self) -> None:
        from fastapi.testclient import TestClient

        from coproscope.web.app import create_app
        from coproscope.web.viewmodel import build_dashboard_model

        with exemple_copie("explorateur") as instance:
            lignes = list(build_dashboard_model(instance, 2025)["documents"]["documents"].rows)
            self.assertGreater(len(lignes), 0)
            arbre = construire_arbre(lignes)
            self.assertEqual(ecarts(arbre, [r["doc_id"] for r in lignes]),
                             {"perdues": [], "doublees": [], "tailles_fausses": []})
            self.assertEqual(arbre["total"], len(lignes))

            page = TestClient(create_app(instance, 2025)).get("/documents")
            self.assertEqual(page.status_code, 200)
            nav = re.search(r'<nav class="cs-explorateur-arbre".*?</nav>', page.text, re.S)
            self.assertIsNotNone(nav, "l'arbre de l'explorateur n'est pas rendu")
            fiches = re.findall(r'href="(/documents/[^"?#]+)', nav.group(0))
            attendues = [r["detail_href"] for r in lignes if r.get("detail_href")]
            self.assertEqual(sorted(fiches), sorted(attendues))


if __name__ == "__main__":
    unittest.main()
