"""C054 a l'ecran: dire que rien ne distingue deux copies d'une assemblee.

Le pont nommait deja les copies concurrentes dans son resume de run. L'ecran de
controle, lui, affichait trois fois la resolution n° 7 - avec deux issues
contradictoires - sans jamais dire qu'il pouvait s'agir du meme proces-verbal
relu. Un journal que personne n'ouvre n'est pas un signalement.

Ce que ces tests exigent, et ce qu'ils n'exigent PAS. Ils exigent que l'ecran
NOMME l'incertitude, sur la ligne et dans la synthese. Ils n'exigent nulle part
qu'il elise la copie qui fait foi: ce serait poser une regle de preuve, et la
mesure d'origine dit que le choix par defaut serait le mauvais - la copie datee
annonce 38 adoptees la ou le proces-verbal en porte 39.
"""

from __future__ import annotations

import shutil
import tempfile
import unittest
from pathlib import Path

from coproscope.modules import actes_autorisation as A
from coproscope.web.controle_gouvernance_view import build_controle_gouvernance_view


def _acte(acte_id: str, **kw: str) -> dict[str, str]:
    ligne = {
        "acte_id": acte_id, "nature": "RESOLUTION_AG", "etat": "CONSTATEE",
        "portee": "ENGAGEMENT_DEPENSE", "date_effet": "2024-07-03", "exercice": "2024",
        "ag_id": "AG-2024-07-03", "numero": "7", "sous_numero": "",
        "objet": "Ravalement de la facade sud", "montant_autorise": "18240.00",
        "entreprise": "", "montant_source": "", "entreprise_source": "",
        "valide_du": "", "valide_au": "", "majorite_requise": "24",
        "majorite_appliquee": "24", "majorite_annoncee": "24",
        "resultat": "ADOPTEE", "resolution_id": "", "page": "4", "ancre": "",
        "confiance": "forte", "doc_id": "DOC-PV-A", "origine": "EXTRAIT",
    }
    ligne.update(kw)
    return ligne


#: Le cas mesure, reduit a son os: la meme resolution n° 7 sous trois
#: assemblees, dont deux dont la date n'a pas ete lue - donc identifiees par
#: leur document. Les issues se contredisent.
TROIS_COPIES = [
    _acte("ACTE-DATE"),
    _acte(
        "ACTE-SANS-DATE-1", ag_id="AG-DOC-729CCCF88863", date_effet="",
        doc_id="DOC-PV-B", resultat="REJETEE",
    ),
    _acte(
        "ACTE-SANS-DATE-2", ag_id="AG-DOC-E67768CA7ACD", date_effet="",
        doc_id="DOC-PV-C", resultat="ADOPTEE",
    ),
]

#: Le contre-cas qui doit rester muet: deux assemblees datees, chacune avec sa
#: resolution n° 7. Leurs dates les distinguent, donc rien n'est signale.
DEUX_ASSEMBLEES_DATEES = [
    _acte("ACTE-2024"),
    _acte(
        "ACTE-2026", ag_id="AG-2026-02-26", date_effet="2026-02-26",
        exercice="2026", doc_id="DOC-PV-D", resultat="REJETEE",
    ),
]


class _Instance:
    display_name = "Copropriete de recette"

    def __init__(self, racine: Path) -> None:
        self.racine = racine

    def settings(self) -> dict[str, object]:
        return {"vault": {"local_root": "./vault_local"}}

    def resolve_path(self, valeur: str) -> Path:
        return (self.racine / str(valeur).lstrip("./")).resolve()


class CopiesConcurrentesAfficheesTests(unittest.TestCase):
    def setUp(self) -> None:
        self.racine = Path(tempfile.mkdtemp())
        self.instance = _Instance(self.racine)

    def tearDown(self) -> None:
        shutil.rmtree(self.racine, ignore_errors=True)

    def _vue(self, actes: list[dict[str, str]], params: dict | None = None) -> dict:
        A.ecrire(
            self.instance, A.TABLE_ACTES, actes,
            sorted({a["doc_id"] for a in actes}),
        )
        return build_controle_gouvernance_view(self.instance, 2025, params or {})

    def test_chaque_ligne_dit_qu_elle_n_est_pas_seule_sur_son_rang(self) -> None:
        """Le manque exact releve par le verificateur: la ligne ne portait
        aucun signalement, donc l'utilisateur voyait trois n° 7 et deux issues
        contradictoires sans savoir quoi en penser."""
        vue = self._vue(TROIS_COPIES, {"vue": "tableau"})
        self.assertEqual(len(vue["lignes"]), 3)
        for ligne in vue["lignes"]:
            with self.subTest(acte=ligne["id"]):
                self.assertIsNotNone(
                    ligne["copies"],
                    "la ligne doit dire que son rang est occupe plusieurs fois",
                )
                self.assertEqual(ligne["copies"]["total"], 3)
                self.assertEqual(ligne["copies"]["rang"], "Résolution 7")
                self.assertEqual(ligne["copies"]["sans_date"], 2)

    def test_la_ligne_nomme_les_autres_sans_en_elire_aucune(self) -> None:
        """L'ecran refuse de trancher: il rend les concurrentes cote a cote, et
        aucune cle ne designe une copie de reference."""
        vue = self._vue(TROIS_COPIES, {"vue": "tableau"})
        ligne = next(l for l in vue["lignes"] if l["id"] == "ACTE-DATE")
        autres = ligne["copies"]["autres"]
        self.assertEqual(
            sorted(c["acte_id"] for c in autres),
            ["ACTE-SANS-DATE-1", "ACTE-SANS-DATE-2"],
        )
        self.assertEqual(sorted(c["resultat"] for c in autres), ["ADOPTEE", "REJETEE"])
        for cle in ("fait_foi", "retenue", "copie_de_reference", "gagnante"):
            self.assertNotIn(cle, ligne["copies"])

    def test_la_synthese_compte_les_lignes_concernees(self) -> None:
        """Le meme fait doit se lire sans ouvrir le tableau: une limite qui ne
        se voit qu'au journal est une limite que personne ne leve."""
        vue = self._vue(TROIS_COPIES)
        textes = ["".join(b["texte"] for b in ligne) for ligne in vue["limites"]]
        concerne = [t for t in textes if "numéros de résolution" in t]
        self.assertEqual(len(concerne), 1, textes)
        self.assertIn("3", concerne[0])
        self.assertIn("CoproScope n'élit aucune copie", concerne[0])

    def test_deux_assemblees_datees_ne_declenchent_aucun_signalement(self) -> None:
        """Garde anti-sur-correction, et le faux positif le plus probable: une
        copropriete qui tient une assemblee par an a une resolution n° 7 par
        annee, et elles n'ont rien a voir."""
        vue = self._vue(DEUX_ASSEMBLEES_DATEES, {"vue": "tableau"})
        self.assertEqual(len(vue["lignes"]), 2)
        self.assertEqual([l["copies"] for l in vue["lignes"]], [None, None])

    def test_la_synthese_reste_muette_quand_rien_n_est_concurrent(self) -> None:
        vue = self._vue(DEUX_ASSEMBLEES_DATEES)
        textes = ["".join(b["texte"] for b in ligne) for ligne in vue["limites"]]
        self.assertEqual([t for t in textes if "numéros de résolution" in t], [])

    def test_un_filtre_ne_fait_pas_disparaitre_la_concurrence(self) -> None:
        """Le calcul porte sur la matrice entiere, pas sur ce qui reste apres
        filtrage: masquer la copie ne la rend pas inexistante, et l'ecran doit
        dire la meme chose dans les deux cas."""
        vue = self._vue(TROIS_COPIES, {"vue": "tableau", "f_issue": "REJETEE"})
        self.assertEqual(len(vue["lignes"]), 1)
        self.assertEqual(vue["lignes"][0]["copies"]["total"], 3)


class LeSignalementArriveDansLaPageTests(unittest.TestCase):
    """Le modele de vue ne suffit pas: C054 demandait que ce soit AFFICHE.

    Une cle correcte dans un dictionnaire qu'aucun gabarit ne lit est
    exactement le defaut que ce constat decrit - le fait etait deja dans le
    resume de run, et l'ecran n'en montrait rien.
    """

    @classmethod
    def setUpClass(cls) -> None:
        try:
            from fastapi.testclient import TestClient  # noqa: F401
        except ImportError:  # pragma: no cover - dependance optionnelle
            raise unittest.SkipTest("FastAPI test client indisponible")

    def setUp(self) -> None:
        import json
        from coproscope.core.common import load_instance

        depot = Path(__file__).resolve().parents[2]
        self.tempdir = tempfile.TemporaryDirectory()
        racine = Path(self.tempdir.name) / "instance"
        shutil.copytree(depot / "examples" / "synthetic_copro", racine)
        config = json.loads((racine / "instance.yml").read_text(encoding="utf-8"))
        config["settings"]["vault"] = {"local_root": "./vault_local"}
        (racine / "instance.yml").write_text(json.dumps(config, indent=2), encoding="utf-8")
        self.instance = load_instance(str(racine / "instance.yml"), None)

    def tearDown(self) -> None:
        self.tempdir.cleanup()

    def _page(self, actes: list[dict[str, str]], chemin: str) -> str:
        from fastapi.testclient import TestClient

        from coproscope.web.app import create_app

        A.ecrire(
            self.instance, A.TABLE_ACTES, actes,
            sorted({a["doc_id"] for a in actes}),
        )
        return TestClient(create_app(self.instance, 2025)).get(chemin).text

    def test_le_tableau_ecrit_la_phrase_sous_la_decision(self) -> None:
        page = self._page(TROIS_COPIES, "/controle-gouvernance?vue=tableau")
        self.assertIn("cs-decision-copies", page)
        self.assertIn("Cette ligne n'est pas seule sur ce", page)
        self.assertIn("3 décisions s'appellent", page)
        self.assertIn("Résolution 7", page)
        self.assertIn("dont 2 venues d'assemblées dont la date n'a pas été lue", page)
        self.assertIn("CoproScope ne choisit pas", page)

    def test_la_page_ne_dit_jamais_qu_une_copie_fait_foi(self) -> None:
        """Le refus d'elire est une regle de preuve: la page ne doit pas la
        contourner par un mot."""
        page = self._page(TROIS_COPIES, "/controle-gouvernance?vue=tableau")
        for mot in ("fait foi", "copie de référence", "version retenue"):
            self.assertNotIn(mot, page)

    def test_sans_concurrence_la_page_reste_silencieuse(self) -> None:
        page = self._page(DEUX_ASSEMBLEES_DATEES, "/controle-gouvernance?vue=tableau")
        self.assertNotIn("cs-decision-copies", page)


if __name__ == "__main__":
    unittest.main()
