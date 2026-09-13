# -*- coding: utf-8 -*-
"""L'ecran des courriers lit ce que la chaine a calcule, et se compte lui-meme.

Arbitrage de Brice du 2026-09-11: *« On branche les ecrans. »*

**Le defaut corrige n'est pas celui qu'on attend.** Les trois brouillons de
courrier etaient inventes, mais ils ne trompaient personne: leurs identifiants
portaient `FICTIF` en toutes lettres. **La page se contredisait elle-meme:** son
bandeau annoncait *3 brouillons a valider* alors qu'**un seul** des trois
portait ce statut, et *2 preuves a rattacher* alors que le tableau situe **juste
en dessous** en comptait **trois**. Deux comptages ecrits a la main, pour la
meme notion, a trois centimetres l'un de l'autre - le defaut numero un du
produit, en miniature.

**Ce qui les remplace n'a demande aucune table nouvelle.** La chaine produit
deja un rapport *pieces a demander* dont chaque ligne est litteralement un
courrier a envoyer: sujet, piece attendue, raison, priorite, statut, diligence.
Mesure sur une instance VIDE reabsorbant 858 pieces sources: **6 lignes reelles,
dont 5 en priorite haute**.

**Deux choses ont ete RETIREES plutot que remplies, et c'est le coeur du lot.**

1. **La colonne destinataire.** L'ecran en avait une. La colonne d'emetteur du
   registre est vide sur **les 60 documents de correspondance, sans exception**,
   et pour les douze vraies lettres la liste des destinataires vit a l'interieur
   d'un document, pas comme donnee. Afficher une colonne vide sur chaque ligne
   apprend a ne plus la regarder.
2. **Le filtre par type de document.** Il aurait ete naturel de lister les
   courriers deja ecrits en filtrant sur *Communication*. Mesure sur douze
   vraies lettres - meme dossier, meme jour, meme nature: **6 seulement portent
   ce type**; quatre sont typees *Convocation d'AG*. Et dans l'autre sens,
   *Convocation d'AG* compte 39 documents dont 4 lettres. **Un filtre qui rate
   la moitie de sa population et en ramasse trente-cinq de trop n'est pas un
   filtre.**
"""

from __future__ import annotations

import csv
import tempfile
import unittest
from pathlib import Path

from coproscope.web._courriers_matiere import (
    CHAINE_NON_PASSEE,
    PRET,
    RIEN_A_DEMANDER,
    matiere_de_courriers,
)
from coproscope.web.courriers_preuves_view import build_courriers_preuves_view

COLONNES_DEMANDES = [
    "request_id", "source_ref", "priority", "status", "subject",
    "expected_piece", "reason", "related_doc_ids", "evidence_paths",
    "suggested_diligence",
]
COLONNES_COMPLETUDE = [
    "proof_id", "lot", "expected_label", "document_type", "status",
    "criticality", "freshness_months", "matched_doc_ids", "evidence_paths",
    "newest_date", "reason", "action",
]


class _Instance:
    """Instance minimale: seul le dossier des rapports compte ici."""

    def __init__(self, rapports: Path | None) -> None:
        self._rapports = rapports

    def artifact(self, nom: str) -> str:
        if nom != "reports_dir" or self._rapports is None:
            raise KeyError(nom)
        return str(self._rapports)


class _AvecRapports(unittest.TestCase):
    def setUp(self) -> None:
        self._temp = tempfile.TemporaryDirectory(ignore_cleanup_errors=True)
        self.addCleanup(self._temp.cleanup)
        self.rapports = Path(self._temp.name) / "reports"
        self.rapports.mkdir()
        self.instance = _Instance(self.rapports)

    def _ecrire(self, nom: str, colonnes: list[str], lignes: list[dict]) -> None:
        with (self.rapports / nom).open("w", encoding="utf-8", newline="") as f:
            ecrivain = csv.DictWriter(f, fieldnames=colonnes)
            ecrivain.writeheader()
            for ligne in lignes:
                ecrivain.writerow({c: ligne.get(c, "") for c in colonnes})

    def _demandes(self, lignes: list[dict]) -> None:
        self._ecrire("pieces_a_demander.csv", COLONNES_DEMANDES, lignes)

    def _completude(self, lignes: list[dict]) -> None:
        self._ecrire("matrice_completude_documentaire.csv", COLONNES_COMPLETUDE, lignes)


class TROIS_ETATS_ET_LE_MILIEU_EST_UNE_BONNE_NOUVELLE(_AvecRapports):
    """*La chaine n'a pas tourne* et *elle n'a rien trouve* sont opposes."""

    def test_sans_rapport_produit_l_ecran_le_dit(self) -> None:
        matiere = matiere_de_courriers(_Instance(None))
        self.assertEqual(CHAINE_NON_PASSEE, matiere["etat"])
        self.assertIn("traitement des documents", matiere["action"])
        self.assertEqual(0, matiere["compte"])

    def test_un_rapport_VIDE_est_une_bonne_nouvelle_et_se_lit_ainsi(self) -> None:
        """Zero piece a demander n'est pas un ecran casse: c'est un syndic
        qui n'a rien laisse de cote."""
        self._demandes([])
        matiere = matiere_de_courriers(self.instance)
        self.assertEqual(RIEN_A_DEMANDER, matiere["etat"])
        self.assertIn("Aucune pièce n'est à demander", matiere["message"])
        self.assertIn("Rien à écrire", matiere["action"])

    def test_des_lignes_donnent_des_courriers(self) -> None:
        self._demandes([
            {"request_id": "REQ-1", "priority": "P1", "status": "ABSENT",
             "subject": "Demander l'attestation d'assurance"},
            {"request_id": "REQ-2", "priority": "P2", "status": "A_CLASSER",
             "subject": "Vérifier le classement du procès-verbal"},
        ])
        matiere = matiere_de_courriers(self.instance)
        self.assertEqual(PRET, matiere["etat"])
        self.assertEqual(2, matiere["compte"])
        self.assertEqual(1, matiere["haute_priorite"])


class LA_PRIORITE_HAUTE_PASSE_DEVANT(_AvecRapports):
    def test_l_ordre_du_rapport_est_conserve_a_l_interieur(self) -> None:
        """Reordonner a l'interieur d'une priorite fabriquerait un second
        classement concurrent de celui que la chaine a calcule."""
        self._demandes([
            {"request_id": "A", "priority": "P2", "subject": "deux"},
            {"request_id": "B", "priority": "P1", "subject": "un"},
            {"request_id": "C", "priority": "P1", "subject": "trois"},
        ])
        ordre = [b["id"] for b in matiere_de_courriers(self.instance)["brouillons"]]
        self.assertEqual(["B", "C", "A"], ordre)


class AUCUNE_COLONNE_VIDE_N_EST_AFFICHEE(_AvecRapports):
    """Une colonne vide sur chaque ligne apprend a ne plus la regarder."""

    def test_le_destinataire_a_disparu(self) -> None:
        self._demandes([{"request_id": "REQ-1", "subject": "Sujet"}])
        brouillon = matiere_de_courriers(self.instance)["brouillons"][0]
        self.assertNotIn("recipient", brouillon)
        self.assertNotIn("destinataire", brouillon)


class LES_COMPTEURS_COMPTENT_CE_QU_ILS_ANNONCENT(_AvecRapports):
    """**Le defaut central, et il etait visible a l'oeil nu.**

    Le bandeau annoncait trois nombres ecrits a la main qui contredisaient le
    tableau situe juste en dessous.
    """

    def test_le_compteur_egale_la_longueur_de_la_liste_affichee(self) -> None:
        self._demandes([
            {"request_id": "REQ-%d" % n, "priority": "P1" if n < 3 else "P2",
             "subject": "Sujet %d" % n}
            for n in range(1, 6)
        ])
        vue = build_courriers_preuves_view(2026, instance=self.instance)
        valeurs = {m["label"]: m["value"] for m in vue["summary"]}
        self.assertEqual(str(len(vue["drafts"])), valeurs["Pièces à demander"])
        self.assertEqual("5", valeurs["Pièces à demander"])
        self.assertEqual("2", valeurs["Dont priorité haute"])

    def test_le_compteur_de_preuves_compte_les_pieces_RATTACHEES(self) -> None:
        """Zero rattache se dit zero, et c'est une absence mesuree."""
        self._demandes([{"request_id": "REQ-1", "subject": "Sujet"}])
        self._completude([
            {"proof_id": "PRV-025",
             "expected_label": "Preuves d'envoi et accusés de réception",
             "status": "ABSENT", "criticality": "P1", "matched_doc_ids": ""},
            {"proof_id": "PRV-001", "expected_label": "Contrat de syndic",
             "status": "OK", "criticality": "P1", "matched_doc_ids": "DOC-1"},
        ])
        vue = build_courriers_preuves_view(2026, instance=self.instance)
        valeurs = {m["label"]: m["value"] for m in vue["summary"]}
        self.assertEqual("0", valeurs["Preuves d'envoi rattachées"])
        self.assertEqual(1, len(vue["proofs"]),
                         "seule la ligne des preuves d'envoi concerne cet écran")


class L_ECRAN_LIT_VRAIMENT_LE_RAPPORT(_AvecRapports):
    """Le temoin de cablage: retirer l'appel doit faire rougir."""

    def test_les_lignes_de_la_PAGE_viennent_du_rapport(self) -> None:
        self._demandes([
            {"request_id": "REQ-UNIQUE", "priority": "P1",
             "subject": "Un sujet que personne n'aurait invente"},
        ])
        vue = build_courriers_preuves_view(2026, instance=self.instance)
        self.assertEqual(1, len(vue["drafts"]))
        self.assertEqual("REQ-UNIQUE", vue["drafts"][0]["id"])

    def test_plus_aucune_ligne_fictive_quand_l_ecran_lit(self) -> None:
        self._demandes([{"request_id": "REQ-1", "subject": "Sujet"}])
        vue = build_courriers_preuves_view(2026, instance=self.instance)
        for ligne in vue["drafts"]:
            self.assertNotIn("FICTIF", ligne["id"])
        self.assertNotIn("FICTIF", vue["notice"].upper())

    def test_le_contenu_REDIGE_est_intact(self) -> None:
        """Definitions, limites et boutons bloques ne sont pas des donnees
        inventees: ils disent ce que l'outil s'interdit de faire."""
        self._demandes([{"request_id": "REQ-1", "subject": "Sujet"}])
        vue = build_courriers_preuves_view(2026, instance=self.instance)
        self.assertEqual(4, len(vue["definitions"]))
        self.assertEqual(4, len(vue["boundaries"]))
        bloquees = [a for a in vue["actions"] if a.get("enabled") == "false"]
        self.assertTrue(bloquees, "les envois doivent rester bloques")


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
