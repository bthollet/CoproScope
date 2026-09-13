"""Une assemblee, une ligne, et jamais une reference de fichier en guise de titre.

Ces tests fixent les trois regles etablies apres la recette du 2026-09-04 sur
instance reelle, ou le registre rendait quatre assemblees pour deux, dont une
aux comptages faux, et titrait deux d'entre elles avec la reference interne du
document.
"""

from __future__ import annotations

import shutil
import tempfile
import unittest
from pathlib import Path

from coproscope.modules.resolutions import RESOLUTION_FIELDS
from coproscope.vault.gouvernance_store import remplacer_pour_documents
from coproscope.web._resolutions_assemblees import (
    PIECE_CONVERTIE,
    PIECE_ORIGINE,
    Attestation,
    date_de_ag_id,
    elire,
    meme_assemblee,
    regrouper,
)
from coproscope.web.resolutions_view import build_resolutions_view


class _Instance:
    """Instance minimale: un coffre local et un registre documentaire."""

    def __init__(self, racine: Path) -> None:
        self.racine = racine
        (racine / "coffre").mkdir(parents=True, exist_ok=True)
        self._documents = racine / "registre_documents.csv"
        self._documents.write_text("doc_id,extension\n", encoding="utf-8")

    def settings(self) -> dict[str, object]:
        return {"vault": {"local_root": "./coffre"}}

    def resolve_path(self, valeur: str) -> Path:
        return self.racine / str(valeur).lstrip("./")

    def register(self, nom: str) -> Path:
        if nom == "documents":
            return self._documents
        raise KeyError(nom)

    def declarer_formes(self, formes: dict[str, str]) -> None:
        lignes = ["doc_id,extension"]
        lignes += [f"{doc_id},{extension}" for doc_id, extension in formes.items()]
        self._documents.write_text("\n".join(lignes) + "\n", encoding="utf-8")


def _ligne(doc_id: str, ag_id: str, numero: int, objet: str, resultat: str) -> dict[str, str]:
    modele = {champ: "" for champ in RESOLUTION_FIELDS}
    modele.update(
        {
            "resolution_id": f"{doc_id}-R{numero:03d}",
            "ag_id": ag_id,
            "doc_id": doc_id,
            "numero": str(numero),
            "objet": objet,
            "resultat": resultat,
            "position": str(numero),
            "numerotation": "lue",
            "etat": "CONSTATEE",
            "origine": "EXTRAIT",
            "confiance": "forte",
        }
    )
    return modele


def _serie(doc_id: str, ag_id: str, numeros: range, resultat: str = "ADOPTEE") -> list[dict[str, str]]:
    return [_ligne(doc_id, ag_id, n, f"Objet numero {n}", resultat) for n in numeros]


class RegroupementTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tempdir = tempfile.TemporaryDirectory()
        self.instance = _Instance(Path(self.tempdir.name))

    def tearDown(self) -> None:
        shutil.rmtree(self.tempdir.name, ignore_errors=True)
        self.tempdir.cleanup()

    def _ecrire(self, lignes: list[dict[str, str]]) -> None:
        doc_ids = sorted({ligne["doc_id"] for ligne in lignes})
        remplacer_pour_documents(self.instance, RESOLUTION_FIELDS, lignes, doc_ids)

    def test_un_pv_et_sa_conversion_texte_ne_font_qu_une_assemblee(self) -> None:
        """Le meme proces-verbal lu deux fois reste une seule assemblee."""
        self.instance.declarer_formes({"DOC-PDF": "pdf", "DOC-MD": "md"})
        self._ecrire(_serie("DOC-PDF", "AG-2024-07-03", range(1, 6))
                     + _serie("DOC-MD", "AG-2024-07-03", range(1, 6)))

        vue = build_resolutions_view(self.instance)

        self.assertEqual(len(vue["assemblees"]), 1)
        self.assertEqual(vue["lignes_registre"], 10)
        self.assertEqual(vue["total"], 5)
        self.assertEqual(vue["assemblees"][0]["titre"], "Assemblee du 2024-07-03")

    def test_la_piece_d_origine_prime_sur_sa_conversion_texte(self) -> None:
        """A couverture egale, la re-ecriture cede a la piece."""
        self.instance.declarer_formes({"DOC-PDF": "pdf", "DOC-MD": "md"})
        self._ecrire(_serie("DOC-PDF", "AG-2024-07-03", range(1, 6))
                     + _serie("DOC-MD", "AG-2024-07-03", range(1, 6)))

        ecartees = build_resolutions_view(self.instance)["assemblees"][0]["versions_ecartees"]

        self.assertEqual(len(ecartees), 1)
        self.assertIn("conversion texte", ecartees[0])

    def test_les_fragments_ne_sont_pas_additionnes(self) -> None:
        """La somme de quatre morceaux n'est pas la serie.

        C'est le defaut mesure: quatre documents scindes recomposaient 55
        resolutions avec des comptages faux, a cote du proces-verbal entier.
        """
        self.instance.declarer_formes({"DOC-ENTIER": "pdf", "DOC-A": "pdf", "DOC-B": "pdf"})
        lignes = _serie("DOC-ENTIER", "AG-2024-07-03", range(1, 11))
        # Les fragments se trompent sur l'issue: s'ils etaient additionnes, le
        # comptage affiche changerait.
        lignes += _serie("DOC-A", "AG-2024-07-03", range(1, 5), resultat="REJETEE")
        lignes += _serie("DOC-B", "AG-2024-07-03", range(5, 11), resultat="REJETEE")
        self._ecrire(lignes)

        assemblee = build_resolutions_view(self.instance)["assemblees"][0]

        self.assertEqual(assemblee["total"], 10)
        self.assertEqual(assemblee["adoptees"], 10)
        self.assertEqual(assemblee["rejetees"], 0)
        self.assertEqual(len(assemblee["versions_ecartees"]), 2)
        for motif in assemblee["versions_ecartees"]:
            self.assertIn("document partiel", motif)

    def test_le_tableau_commence_au_premier_numero_du_document(self) -> None:
        """Une seule attestation affichee, donc l'ordre du document est tenu.

        Avec quatre fragments melanges, la table commencait a la resolution 40
        alors que la page promet l'ordre du proces-verbal.
        """
        self.instance.declarer_formes({"DOC-ENTIER": "pdf", "DOC-FIN": "pdf"})
        self._ecrire(_serie("DOC-ENTIER", "AG-2024-07-03", range(1, 11))
                     + _serie("DOC-FIN", "AG-2024-07-03", range(8, 11)))

        assemblee = build_resolutions_view(self.instance)["assemblees"][0]

        self.assertEqual([r["numero"] for r in assemblee["resolutions"]],
                         [str(n) for n in range(1, 11)])

    def test_la_date_est_heritee_du_document_qui_la_porte(self) -> None:
        """Un document sans date lue reste titre par la date de sa serie.

        Cause racine mesuree: `suspected_date` vide sur le proces-verbal entier,
        renseignee sur les documents scindes de la meme assemblee.
        """
        self.instance.declarer_formes({"DOC-SANSDATE": "pdf", "DOC-DATE": "pdf"})
        self._ecrire(_serie("DOC-SANSDATE", "AG-DOC-SANSDATE", range(1, 11))
                     + _serie("DOC-DATE", "AG-2024-07-03", range(1, 5)))

        assemblee = build_resolutions_view(self.instance)["assemblees"][0]

        self.assertEqual(assemblee["titre"], "Assemblee du 2024-07-03")
        self.assertTrue(assemblee["date_lue"])
        self.assertEqual(assemblee["total"], 10)

    def test_sans_aucune_date_le_titre_le_dit_au_lieu_d_afficher_une_reference(self) -> None:
        """Un identifiant technique n'est jamais un titre."""
        self.instance.declarer_formes({"DOC-729CCCF88863": "pdf"})
        self._ecrire(_serie("DOC-729CCCF88863", "AG-DOC-729CCCF88863", range(1, 4)))

        assemblee = build_resolutions_view(self.instance)["assemblees"][0]

        self.assertFalse(assemblee["date_lue"])
        self.assertEqual(assemblee["titre"], "Assemblee dont la date n'a pas ete lue")
        self.assertNotIn("DOC-", assemblee["titre"])

    def test_deux_assemblees_distinctes_restent_distinctes(self) -> None:
        """Partager des numeros de resolution ne fait pas une meme assemblee."""
        self.instance.declarer_formes({"DOC-2024": "pdf", "DOC-2026": "pdf"})
        lignes = _serie("DOC-2024", "AG-2024-07-03", range(1, 6))
        lignes += [
            _ligne("DOC-2026", "AG-2026-02-26", n, f"Tout autre sujet {n}", "ADOPTEE")
            for n in range(1, 6)
        ]
        self._ecrire(lignes)

        vue = build_resolutions_view(self.instance)

        self.assertEqual(len(vue["assemblees"]), 2)
        # La plus recente en tete, et aucune version ecartee.
        self.assertEqual(vue["assemblees"][0]["titre"], "Assemblee du 2026-02-26")
        self.assertEqual(vue["versions_ecartees"], 0)

    def test_une_copie_qui_compte_autrement_est_signalee_et_non_tue(self) -> None:
        """Deux exemplaires en desaccord: l'ecart est nomme, pas efface."""
        self.instance.declarer_formes({"DOC-PDF": "pdf", "DOC-MD": "md"})
        lignes = _serie("DOC-PDF", "AG-2024-07-03", range(1, 6))
        lignes += _serie("DOC-MD", "AG-2024-07-03", range(1, 6))
        lignes[-1]["resultat"] = "REJETEE"
        self._ecrire(lignes)

        ecartees = build_resolutions_view(self.instance)["assemblees"][0]["versions_ecartees"]

        self.assertEqual(len(ecartees), 1)
        self.assertIn("desaccord", ecartees[0])
        self.assertIn("adoptees 4 au lieu de 5", ecartees[0])


class ReglesElementairesTests(unittest.TestCase):
    def test_seule_la_forme_datee_de_l_identifiant_donne_une_date(self) -> None:
        self.assertEqual(date_de_ag_id("AG-2024-07-03"), "2024-07-03")
        self.assertEqual(date_de_ag_id("AG-DOC-729CCCF88863"), "")
        self.assertEqual(date_de_ag_id(""), "")

    def test_deux_dates_lues_differentes_ne_se_confondent_jamais(self) -> None:
        gauche = Attestation("A", "2024-07-03", PIECE_ORIGINE, {1: "meme objet"})
        droite = Attestation("B", "2026-02-26", PIECE_ORIGINE, {1: "meme objet"})

        self.assertFalse(meme_assemblee(gauche, droite))

    def test_deux_fragments_disjoints_se_rejoignent_par_le_document_entier(self) -> None:
        """La transitivite est necessaire: 1-3 et 4-6 n'ont aucun numero commun."""
        entier = Attestation("ENTIER", "", PIECE_ORIGINE, {n: f"o{n}" for n in range(1, 7)})
        debut = Attestation("DEBUT", "", PIECE_ORIGINE, {n: f"o{n}" for n in range(1, 4)})
        fin = Attestation("FIN", "", PIECE_ORIGINE, {n: f"o{n}" for n in range(4, 7)})

        self.assertFalse(meme_assemblee(debut, fin))
        groupes = regrouper([debut, fin, entier])
        self.assertEqual(len(groupes), 1)
        self.assertEqual(len(groupes[0]), 3)

    def test_l_election_est_deterministe_a_criteres_egaux(self) -> None:
        """Une reconstruction doit reelire le meme document, pas un au hasard."""
        objets = {n: f"o{n}" for n in range(1, 4)}
        premier = Attestation("DOC-B", "", PIECE_ORIGINE, dict(objets))
        second = Attestation("DOC-A", "", PIECE_ORIGINE, dict(objets))

        self.assertEqual(elire([premier, second])[0].doc_id, "DOC-A")
        self.assertEqual(elire([second, premier])[0].doc_id, "DOC-A")

    def test_la_couverture_prime_sur_la_forme_de_la_piece(self) -> None:
        """Une conversion complete vaut mieux qu'un fragment d'original."""
        complete = Attestation("DOC-MD", "", PIECE_CONVERTIE, {n: f"o{n}" for n in range(1, 7)})
        partielle = Attestation("DOC-PDF", "", PIECE_ORIGINE, {n: f"o{n}" for n in range(1, 3)})

        retenue, _ = elire([complete, partielle])
        self.assertEqual(retenue.doc_id, "DOC-MD")


if __name__ == "__main__":
    unittest.main()
