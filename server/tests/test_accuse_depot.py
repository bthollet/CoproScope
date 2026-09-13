from __future__ import annotations

import json
import re
import shutil
import tempfile
import unittest
from pathlib import Path

from coproscope.core.common import load_instance
from coproscope.web.accuse_depot import CHAMP_CONSOMMATION, lignes_accuse, servir_accuse
from coproscope.web.app import create_app


"""L'accuse de depot: une fois, au deposant, et nulle part ailleurs.

Arbitrage de Brice du 2026-09-08, `RM-2026-0126`, verbatim au depot dans
`docs/arbitrage_brice_0126_verbatim_2026-09-08.md`:

    « Un accuse de depot montre le nom au deposant seul, juste apres le depot
    et nulle part ailleurs. »

**Ce que ce fichier prouve, et ce qu'il refuse de laisser croire.** Les trois
morceaux de la phrase de Brice n'ont pas la meme solidite, et les tests le
disent au lieu de les traiter comme un bloc:

- `montre le nom` - tenu, et verifie;
- `juste apres le depot` - tenu par un comptage: un depot donne au plus un
  accuse. Verifie;
- `au deposant seul` - **PAS tenu.** Il n'existe aucune notion de deposant dans
  CoproScope: pas de session, pas d'utilisateur, un jeton unique partage. Sous
  l'hypothese monoutilisateur cela suffit, parce que le seul porteur du jeton
  est le deposant. Le test `RESIDU` le mesure au lieu de le supposer.
"""

JETON = "accuse-local"
PIECE = ("assignation MARTIN lot B12.pdf", b"%PDF-1.4\n% piece de test\n")


class AccuseDeDepot(unittest.TestCase):
    def setUp(self) -> None:
        try:
            from fastapi.testclient import TestClient  # type: ignore
        except ImportError:  # pragma: no cover
            self.skipTest("FastAPI test client indisponible")
        depot_racine = Path(__file__).resolve().parents[2]
        source = depot_racine / "examples" / "synthetic_copro"
        self.pile = tempfile.TemporaryDirectory()
        self.addCleanup(self.pile.cleanup)
        self.racine = Path(self.pile.name) / "instance"
        self.racine.mkdir(parents=True)
        shutil.copy(source / "instance.yml", self.racine / "instance.yml")
        shutil.copytree(source / "system", self.racine / "system")
        for dossier in ("raw", "registers", "outputs", "staging", "logs"):
            (self.racine / dossier).mkdir()
        config = json.loads((self.racine / "instance.yml").read_text(encoding="utf-8"))
        config.setdefault("settings", {})["vault"] = {"local_root": "./vault_local"}
        (self.racine / "instance.yml").write_text(json.dumps(config, indent=2), encoding="utf-8")
        self.instance = load_instance(None, str(self.racine))
        self.client = TestClient(create_app(self.instance, 2026, access_token=JETON, rebrancher=frozenset({"ajouter_document"})))

    def _deposer(self) -> str:
        """Depose la piece et rend l'identifiant de depot."""

        reponse = self.client.post(
            f"/depot?token={JETON}",
            data={"intent": "document", "return": "document_intake", "source": "menu"},
            files=[("files", (PIECE[0], PIECE[1], "application/pdf"))],
            follow_redirects=False,
        )
        self.assertEqual(reponse.status_code, 303)
        destination = reponse.headers["location"]
        trouve = re.search(r"depot=(DEPOT-[0-9TZ]+(?:-\d+)?)", destination)
        self.assertIsNotNone(trouve, f"pas d'identifiant de depot dans {destination}")
        return trouve.group(1)

    # --- ce que Brice a demande -------------------------------------------------

    def test_l_accuse_montre_le_nom_juste_apres_le_depot(self) -> None:
        depot = self._deposer()
        page = self.client.get(f"/documents/ajouter?depot={depot}&token={JETON}").text
        self.assertIn(
            PIECE[0],
            page,
            "l'accuse ne confirme pas au deposant ce qu'il vient d'envoyer",
        )
        self.assertIn("Accuse de depot", page)

    def test_l_accuse_ne_se_rejoue_pas_a_la_visite_suivante(self) -> None:
        """`juste apres le depot`, tenu par un comptage et non par une duree.

        Un delai en secondes serait un nombre choisi au hasard et rendrait ce
        test dependant de l'horloge. La borne est: un depot, au plus un accuse.
        """

        depot = self._deposer()
        premiere = self.client.get(f"/documents/ajouter?depot={depot}&token={JETON}").text
        seconde = self.client.get(f"/documents/ajouter?depot={depot}&token={JETON}").text

        self.assertIn(PIECE[0], premiere)
        self.assertNotIn(
            PIECE[0],
            seconde,
            "l'accuse se rejoue: `nulle part ailleurs` devient `partout, tout "
            "le temps, pour qui garde l'URL`.",
        )

    def test_le_nom_n_apparait_sur_aucune_autre_page(self) -> None:
        """`nulle part ailleurs`, verifie sur les pages ou la piece est listee."""

        depot = self._deposer()
        for route in ("/documents", "/documents/ajouter", "/depot", "/confidentialite", "/"):
            with self.subTest(route=route):
                page = self.client.get(f"{route}?token={JETON}").text
                self.assertNotIn(PIECE[0], page, f"le nom depose sort sur {route}")
        # Et meme la page de l'accuse, si l'URL ne nomme pas le depot.
        sans_depot = self.client.get(f"/documents/ajouter?token={JETON}").text
        self.assertNotIn(PIECE[0], sans_depot)
        self.assertTrue(depot)

    def test_l_accuse_ne_se_sert_pas_sans_identifiant(self) -> None:
        """Aucun repli sur le dernier depot.

        `GET /depot` se replie, lui, sur `latest_deposit_manifest`. Si l'accuse
        faisait pareil, il serait atteignable par quelqu'un qui n'a rien depose
        et ne connait aucun identifiant: il suffirait d'ouvrir la page.
        """

        depot = self._deposer()
        manifeste = json.loads(
            (self.racine / "outputs" / "deposits" / f"{depot}.json").read_text(encoding="utf-8")
        )
        self.assertEqual(servir_accuse(self.instance, manifeste, depot_demande=""), [])
        self.assertNotEqual(
            lignes_accuse(manifeste), [], "le manifeste ne porte aucun nom: le test ne prouve rien"
        )

    def test_la_trace_de_consommation_est_ecrite_dans_le_manifeste(self) -> None:
        """La garantie `une fois` doit etre une propriete du systeme, pas un espoir."""

        depot = self._deposer()
        chemin = self.racine / "outputs" / "deposits" / f"{depot}.json"
        avant = json.loads(chemin.read_text(encoding="utf-8"))
        self.assertNotIn(CHAMP_CONSOMMATION, avant)

        self.client.get(f"/documents/ajouter?depot={depot}&token={JETON}")

        apres = json.loads(chemin.read_text(encoding="utf-8"))
        self.assertTrue(
            str(apres.get(CHAMP_CONSOMMATION) or "").strip(),
            "l'accuse a ete servi sans laisser de trace: il se rejouera",
        )

    # --- le residu, mesure et non promis ---------------------------------------

    def test_RESIDU_l_identifiant_de_depot_est_devinable(self) -> None:
        """`au deposant seul` n'est pas tenu, et voici de combien.

        L'identifiant est un horodatage UTC a la seconde (`web/depot.py:183`).
        Il n'est ni secret, ni aleatoire, ni derive d'une identite. Ce test
        reconstruit l'identifiant a partir du seul horodatage - ce que ferait
        quelqu'un qui sait qu'un depot a eu lieu ce jour-la - et montre qu'il
        obtient l'accuse a la place du deposant.

        **Ce que ce test protege reellement:** il echouera le jour ou quelqu'un
        prendra le caractere a un coup pour un controle d'acces. Ce n'en est pas
        un: c'est une borne de degat. Sous l'hypothese monoutilisateur - un
        jeton, un lecteur - la question ne se pose pas. Elle se pose au deuxieme
        utilisateur, et le remede est dans
        `docs/cdc_pseudonymisation_multiutilisateur_2026-09-08.md`.
        """

        depot = self._deposer()
        self.assertRegex(
            depot,
            r"^DEPOT-\d{8}T\d{6}Z(?:-\d+)?$",
            "l'identifiant n'est plus un horodatage: ce residu a peut-etre ete "
            "corrige, relire ce test avant de le garder.",
        )

        # Un tiers qui n'a rien depose, mais qui sait quand le depot a eu lieu,
        # reconstruit l'URL et consomme l'accuse.
        vole = self.client.get(f"/documents/ajouter?depot={depot}&token={JETON}").text
        self.assertIn(PIECE[0], vole, "le tiers n'obtient rien: le residu a change")

        # Et le deposant, arrivant apres, ne voit plus sa confirmation.
        deposant = self.client.get(f"/documents/ajouter?depot={depot}&token={JETON}").text
        self.assertNotIn(
            PIECE[0],
            deposant,
            "le deposant voit encore son accuse alors qu'il a deja ete consomme",
        )

    def test_RESIDU_il_n_existe_aucune_notion_de_deposant(self) -> None:
        """`au deposant seul` repose sur l'hypothese monoutilisateur, pas sur du code.

        Le manifeste de depot ne porte aucune identite: ni utilisateur, ni
        session, ni acteur. Il ne PEUT donc pas distinguer le deposant d'un
        autre lecteur du meme jeton. Ce test fige ce fait pour que personne ne
        croie que la garde existe.
        """

        depot = self._deposer()
        manifeste = json.loads(
            (self.racine / "outputs" / "deposits" / f"{depot}.json").read_text(encoding="utf-8")
        )
        champs_d_identite = [
            cle
            for cle in manifeste
            if any(mot in cle.lower() for mot in ("user", "utilisateur", "deposant", "auteur", "actor", "session"))
        ]
        self.assertEqual(
            champs_d_identite,
            [],
            "Le manifeste porte maintenant une identite de deposant "
            f"({champs_d_identite}). C'est une bonne nouvelle: relisez "
            "`accuse_depot.py`, dont la borne peut desormais s'appuyer sur "
            "cette identite plutot que sur le comptage.",
        )


if __name__ == "__main__":
    unittest.main()
