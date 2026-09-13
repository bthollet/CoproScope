# -*- coding: utf-8 -*-
"""Une divergence entre deux denominations d'un meme contenu devient une DEMANDE.

`RM-2026-0088`, residu du refus d'integration. La cellule prescrivait:
*« Reconcilier les lignes qui partagent une empreinte... Ne PAS heriter une date
d'un document a l'autre: **LA DEMANDER**, comme `/documents/non-lus` demande
deja l'accord OCR. »* Le lot avait livre la reconciliation et le non-heritage -
proprement, et les gardes le prouvent. **Il n'avait pas livre la demande.**

**Le motif du refus, mot pour mot:** *« le code livre fait la reconciliation et
la non-heritage, pas la demande [...] se contente d'append une note dont le
TEXTE dit "la valeur manquante se demande" - c'est un enonce, pas un chemin. »*
Verifie: la note existe bien, elle est juste, et rien nulle part ne produisait
la demande qu'elle annonce.

**AUCUN REGISTRE NOUVEAU N'EST CREE, et c'est le point de conception.** La file
`pieces_a_demander.csv` existe, elle porte deja les pieces manquantes de la
completude, et l'ecran des courriers la lit. Un second registre de demandes
reproduirait le defaut numero un du produit - plusieurs comptages concurrents
pour la meme notion. La divergence devient donc une ligne de cette file, au
format `DOCUMENT_REQUEST_FIELDS`.

**LA DEMANDE NE RECALCULE RIEN ET NE LIT AUCUNE NOTE.** Elle rejoue
`grouper_par_empreinte` et `champs_du_verdict_sur_le_contenu` - les memes
fonctions que la reconciliation. Deriver une demande de la PROSE d'une note
ferait du libelle une interface, et le premier reformulateur casserait la file
en silence.

**RESERVE QUI TIENT, et elle etait deja dans la cellule:** sur le corpus
reabsorbe, **858 documents portent 858 empreintes distinctes, zero collision**.
La file de divergences est donc **vide sur la matiere reelle**, et ces tests
l'exercent sur des cas construits. Un corpus ou le meme fichier arrive sous deux
noms reste a rencontrer.
"""

from __future__ import annotations

import unittest

from coproscope.modules import docuscope as D
from coproscope.modules._docuscope_parts import __name__ as _parts  # noqa: F401

CHAMPS = D.DOCUMENT_REQUEST_FIELDS

EMPREINTE = "abc123def4567890abc123def4567890abc123def4567890abc123def4567890"


def _ligne(doc_id: str, nom: str, **champs) -> dict:
    base = {
        "doc_id": doc_id,
        "sha256": EMPREINTE,
        "file_name": nom,
        "document_type": "",
        "raw_max_college": "",
    }
    base.update(champs)
    return base


class UN_DESACCORD_PRODUIT_UNE_DEMANDE(unittest.TestCase):
    """Deux valeurs incompatibles sur un seul contenu: une au moins est fausse."""

    def _demandes(self, lignes):
        return D.demandes_de_divergence(lignes)

    def test_deux_types_differents_font_une_demande(self) -> None:
        demandes = self._demandes([
            _ligne("D1", "a.pdf", document_type="PV_AG"),
            _ligne("D2", "b.pdf", document_type="Convocation_AG"),
        ])
        self.assertEqual(1, len(demandes))
        self.assertTrue(demandes[0]["request_id"].startswith("DIV-"))

    def test_la_demande_nomme_les_valeurs_en_presence(self) -> None:
        """Sans quoi le lecteur ne sait pas entre quoi trancher."""
        demandes = self._demandes([
            _ligne("D1", "a.pdf", document_type="PV_AG"),
            _ligne("D2", "b.pdf", document_type="Convocation_AG"),
        ])
        attendu = demandes[0]["expected_piece"]
        self.assertIn("PV_AG", attendu)
        self.assertIn("Convocation_AG", attendu)

    def test_la_demande_n_ELIT_aucune_valeur(self) -> None:
        """**Le coeur de la doctrine de l'item.** Si le produit savait laquelle
        est la bonne, il n'y aurait pas de divergence. La diligence demande de
        trancher; elle ne suggere pas de reponse."""
        demandes = self._demandes([
            _ligne("D1", "a.pdf", document_type="PV_AG"),
            _ligne("D2", "b.pdf", document_type="Convocation_AG"),
        ])
        diligence = demandes[0]["suggested_diligence"].lower()
        self.assertNotIn("retenir", diligence)
        self.assertNotIn("privilégier", diligence)
        self.assertIn("trancher", diligence)

    def test_un_desaccord_passe_en_priorite_haute(self) -> None:
        demandes = self._demandes([
            _ligne("D1", "a.pdf", document_type="PV_AG"),
            _ligne("D2", "b.pdf", document_type="Convocation_AG"),
        ])
        self.assertEqual("P1", demandes[0]["priority"])


class UNE_LECTURE_PARTIELLE_SE_DEMANDE_AUSSI(unittest.TestCase):
    """Une absence n'est pas une seconde valeur, et ne s'herite pas."""

    def test_une_valeur_lue_d_un_seul_cote_fait_une_demande(self) -> None:
        demandes = D.demandes_de_divergence([
            _ligne("D1", "a.pdf", document_type="PV_AG"),
            _ligne("D2", "b.pdf", document_type=""),
        ])
        self.assertEqual(1, len(demandes))
        self.assertTrue(demandes[0]["request_id"].startswith("PAR-"))

    def test_elle_demande_la_valeur_AU_LIEU_de_la_reprendre(self) -> None:
        """La phrase exacte de la doctrine: ne pas heriter, demander."""
        demandes = D.demandes_de_divergence([
            _ligne("D1", "a.pdf", document_type="PV_AG"),
            _ligne("D2", "b.pdf", document_type=""),
        ])
        diligence = demandes[0]["suggested_diligence"].lower()
        self.assertIn("demander", diligence)
        self.assertIn("plutôt que", diligence)

    def test_elle_reste_en_priorite_normale(self) -> None:
        """Rien n'est faux ici: il manque quelque chose. Confondre les deux
        noierait les vrais desaccords sous des absences."""
        demandes = D.demandes_de_divergence([
            _ligne("D1", "a.pdf", document_type="PV_AG"),
            _ligne("D2", "b.pdf", document_type=""),
        ])
        self.assertEqual("P2", demandes[0]["priority"])


class AUCUNE_DEMANDE_QUAND_IL_N_Y_A_RIEN_A_DEMANDER(unittest.TestCase):
    """Le temoin: une file qui se remplit toujours ne designe rien."""

    def test_deux_denominations_D_ACCORD_ne_demandent_rien(self) -> None:
        self.assertEqual([], D.demandes_de_divergence([
            _ligne("D1", "a.pdf", document_type="PV_AG"),
            _ligne("D2", "b.pdf", document_type="PV_AG"),
        ]))

    def test_un_contenu_SEUL_ne_demande_rien(self) -> None:
        """Le cas de tout le corpus mesure: 858 empreintes distinctes."""
        self.assertEqual([], D.demandes_de_divergence([
            _ligne("D1", "a.pdf", document_type="PV_AG"),
        ]))

    def test_une_ligne_SANS_empreinte_ne_fabrique_pas_de_demande(self) -> None:
        """Sans empreinte, aucune confrontation n'est possible: inventer une
        demande la ferait passer pour confrontee."""
        self.assertEqual([], D.demandes_de_divergence([
            {"doc_id": "D1", "sha256": "", "file_name": "a.pdf",
             "document_type": "PV_AG"},
            {"doc_id": "D2", "sha256": "", "file_name": "b.pdf",
             "document_type": "Convocation_AG"},
        ]))


class LA_DEMANDE_ENTRE_DANS_LA_FILE_EXISTANTE(unittest.TestCase):
    """Un second registre reproduirait le defaut numero un du produit."""

    def test_la_ligne_porte_EXACTEMENT_les_colonnes_de_la_file(self) -> None:
        demandes = D.demandes_de_divergence([
            _ligne("D1", "a.pdf", document_type="PV_AG"),
            _ligne("D2", "b.pdf", document_type="Convocation_AG"),
        ])
        self.assertEqual(set(CHAMPS), set(demandes[0]))

    def test_la_file_est_ECRITE_avec_les_deux_sources(self) -> None:
        """**Le temoin de cablage.** Sans lui, la fabrication existerait et ne
        serait appelee par personne - exactement le motif pour lequel un autre
        lot a ete refuse le meme jour: *livrer un correctif et l'adopter sont
        deux choses*."""
        from pathlib import Path
        source = (Path(__file__).resolve().parents[1]
                  / "src/coproscope/modules/_docuscope_parts"
                  / "04_completeness_and_kpis.py").read_text(encoding="utf-8")
        self.assertIn("demandes_de_divergence(docs)", source)
        self.assertIn("action_rows + demandes_de_divergence", source)

    def test_les_identifiants_de_demande_ne_se_collisionnent_pas(self) -> None:
        """Deux champs en desaccord sur la meme empreinte font deux demandes
        distinctes; un identifiant unique les ecraserait l'une l'autre."""
        demandes = D.demandes_de_divergence([
            _ligne("D1", "a.pdf", document_type="PV_AG",
                   raw_max_college="C2_Coproprietaires"),
            _ligne("D2", "b.pdf", document_type="Convocation_AG",
                   raw_max_college="C4_Conseil_Syndical"),
        ])
        identifiants = [d["request_id"] for d in demandes]
        self.assertEqual(len(identifiants), len(set(identifiants)))
        self.assertGreaterEqual(len(identifiants), 2)


class TROIS_DENOMINATIONS_NE_CHANGENT_PAS_LA_REGLE(unittest.TestCase):
    """L'axe: le degre de liberte est le NOMBRE de denominations, pas deux."""

    def test_trois_valeurs_font_UNE_demande_qui_les_nomme_toutes(self) -> None:
        demandes = D.demandes_de_divergence([
            _ligne("D1", "a.pdf", document_type="PV_AG"),
            _ligne("D2", "b.pdf", document_type="Convocation_AG"),
            _ligne("D3", "c.pdf", document_type="Contrat_Syndic"),
        ])
        self.assertEqual(1, len(demandes))
        for valeur in ("PV_AG", "Convocation_AG", "Contrat_Syndic"):
            self.assertIn(valeur, demandes[0]["expected_piece"])

    def test_la_demande_rattache_TOUS_les_documents_concernes(self) -> None:
        demandes = D.demandes_de_divergence([
            _ligne("D1", "a.pdf", document_type="PV_AG"),
            _ligne("D2", "b.pdf", document_type="Convocation_AG"),
            _ligne("D3", "c.pdf", document_type="Contrat_Syndic"),
        ])
        rattaches = demandes[0]["related_doc_ids"].split(";")
        self.assertEqual({"D1", "D2", "D3"}, set(rattaches))


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
