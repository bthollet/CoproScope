"""Un ecran nomme la copropriete qu'il affiche, ou il ne la nomme pas du tout.

Defaut mesure le 2026-09-05 sur `examples/synthetic_copro`, dont le
`display_name` est `Residence Les Platanes`: `/controle-gouvernance` rendait
« Residence Les Platanes », et `/comptes/rapprochement` rendait « Copropriete
FICTIVE ». Deux pages de la meme session, la meme instance, deux coproprietes.

Les DONNEES etaient justes - les lignes de repli sont bien gardees par
`instance is None`. C'est l'identite seule qui etait inventee, ce qui la rend
d'autant plus credible: rien a l'ecran ne signale qu'un nom a ete substitue.
Un coproprietaire qui lit le nom d'une autre copropriete au-dessus de chiffres
corrects ne sait plus de qui sont ces chiffres.
"""

from __future__ import annotations

import pathlib
import re
import unittest
from contextlib import ExitStack

from coproscope.web._identite_coque import identite_coque
from tests._exemple_copie import exemple_copie


class LIdentiteVientDeLInstanceTests(unittest.TestCase):
    """**L'instance est une COPIE** (`RM-2026-0107`).

    La mesure porte sur le nom d'affichage et l'identifiant que l'instance
    DECLARE, donc sur son contenu - que `copytree` reproduit a l'octet. Le
    chemin n'entre pas dans ce qui est mesure, et la reference versionnee n'est
    plus mise a portee d'ecriture.
    """

    @classmethod
    def setUpClass(cls) -> None:
        cls._pile = ExitStack()
        cls.instance = cls._pile.enter_context(exemple_copie("identite_coque"))

    @classmethod
    def tearDownClass(cls) -> None:
        cls._pile.close()

    def test_le_nom_affiche_est_celui_de_l_instance_ouverte(self) -> None:
        identite = identite_coque(self.instance, 2025)
        self.assertEqual(identite["name"], "Residence Les Platanes")
        self.assertEqual(identite["id"], "synthetic-copro")

    def test_sans_instance_le_nom_de_repli_dit_la_verite(self) -> None:
        # `Copropriete FICTIVE` n'est pas un defaut quand AUCUNE instance n'est
        # ouverte: c'est alors exact, et le dire vaut mieux qu'un nom vide.
        self.assertEqual(
            identite_coque(None, 2025)["name"], "Copropriete FICTIVE")

    def test_une_instance_sans_nom_lisible_retombe_sur_le_repli(self) -> None:
        self.assertEqual(
            identite_coque({"instance_id": "x"}, 2025)["name"],
            "Copropriete FICTIVE",
        )


class LesDeuxPagesDeControleNommentLaMemeCoproprieteTests(unittest.TestCase):
    """Les deux livrables de la beta, mesures ensemble sur une seule instance.

    L'instance est une COPIE (`RM-2026-0107`): la page est servie par une
    application reelle, donc tout ce que cette application ecrirait aurait
    atteint la reference versionnee.
    """

    def test_gouvernance_et_comptes_affichent_le_meme_nom(self) -> None:
        from fastapi.testclient import TestClient

        from coproscope.web.app import create_app

        with exemple_copie("deux_pages") as instance:
            self._deux_pages(TestClient(create_app(instance, 2025)))

    def _deux_pages(self, client) -> None:
        noms = {}
        for route in ("/controle-gouvernance", "/comptes/rapprochement"):
            reponse = client.get(route)
            self.assertEqual(reponse.status_code, 200, route)
            texte = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", reponse.text))
            noms[route] = "Residence Les Platanes" in texte
            self.assertNotIn(
                "Copropriete FICTIVE", texte,
                f"{route} affiche un nom de copropriete fabrique alors qu'une "
                f"instance reelle est ouverte")
        self.assertTrue(all(noms.values()), noms)


class LesEcransQuiFabriquentEncoreLeurIdentiteTests(unittest.TestCase):
    """Le compte est retombe a zero, et ce compteur n'est plus la vraie garde.

    Les douze ecrans ont ete branches le 2026-09-09 sur base `ffac60c`
    (`RM-2026-0087`): chacun recoit `instance` et appelle
    `identite_coque(instance, year)`. Le compte passe donc de 12 a 0, comme la
    version precedente de ce texte demandait de l'inscrire.

    **Ce compteur garde une valeur de non-regression, et deux angles morts qu'il
    faut nommer plutot que de laisser croire qu'il protege.** Il cherche une
    chaine exacte, `"name": "Copropriete FICTIVE"`, dans `web/*.py` **a plat**.
    Il ne voit donc pas:

    - un nom fabrique different - `'name': 'Residence du Parc'` produit
      exactement le meme defaut a l'ecran et ne contient pas `FICTIVE`. Mesure
      du 2026-09-09: avec ce defaut injecte et servi sur `/travaux`, ce test
      listait **zero** coupable;
    - la meme ligne posee dans un sous-dossier: **27 des 87 modules `.py` de
      `web/` sont invisibles a son `glob("*.py")`**.

    La garde qui mord sur ces deux cas est
    `tests/test_identite_ecran_source.py`: elle balaie `web/` **recursivement**
    par l'AST - une forme, pas un mot - et elle rend les 65 pages atteignables
    pour verifier que le nom affiche est bien celui de l'instance ouverte.
    """

    ATTENDUS = 0

    def test_le_nombre_d_ecrans_a_brancher_ne_bouge_pas_en_silence(self) -> None:
        web = pathlib.Path(__file__).resolve().parent.parent / "src" / "coproscope" / "web"
        coupables = sorted(
            chemin.name for chemin in web.glob("*.py")
            if chemin.name != "_identite_coque.py"
            and '"name": "Copropriete FICTIVE"' in chemin.read_text(
                encoding="utf-8", errors="replace")
        )
        self.assertEqual(
            len(coupables), self.ATTENDUS,
            "\n\n  Le nombre d'ecrans qui fabriquent leur identite a change.\n"
            f"  attendu {self.ATTENDUS}, trouve {len(coupables)} :\n    "
            + "\n    ".join(coupables)
            + "\n\n  S'il a AUGMENTE: un nouvel ecran reproduit le defaut. Il\n"
            "  doit appeler `identite_coque(instance, year)`.\n"
            "  S'il a BAISSE: tant mieux - mets ATTENDUS a jour et cite le lot.\n"
            "\n  Rappel: ce compteur cherche UNE orthographe dans `web/*.py` a\n"
            "  plat. Un nom fabrique different, ou pose dans un sous-dossier,\n"
            "  lui echappe. La garde qui mord est\n"
            "  `tests/test_identite_ecran_source.py`.\n",
        )


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
