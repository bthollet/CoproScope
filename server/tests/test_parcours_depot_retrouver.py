"""Front vers back, puis back vers front: l'utilisateur retrouve-t-il ses pieces ?

Demande de Brice du 2026-09-07. Le trou que ce fichier comble est precis: AUCUN
test du depot ne depose PUIS ne verifie une autre route. `test_ui_depot_flow`
depose et s'arrete au manifeste sur disque; `test_ui_live_ux_contract` enchaine
trois lectures sans jamais deposer. Le trajet retour n'etait donc garde par
rien.

Ce fichier melange deux natures de tests, et les nomme comme telles.

Les uns PROTEGENT ce qui marche: le depot rend bien 303 en gardant le jeton, et
l'ecran d'arrivee confirme reellement - contrairement a ce qu'une lecture
statique du code laissait croire, il passe de 4538 a 8628 caracteres visibles et
affiche `1 a qualifier`, `1/1 Deposees localement`, `1/1 Type de document`.

Les autres CARACTERISENT un defaut connu: leur echec futur sera une bonne
nouvelle, et leur message le dit. Ils figent l'etat mesure le 2026-09-07 pour
qu'il cesse d'etre invisible, pas pour le benir.
"""

from __future__ import annotations

import csv
import io
import json
import re
import shutil
import tempfile
import unittest
from pathlib import Path

from coproscope.core.common import load_instance
from coproscope.web.app import create_app

JETON = "parcours-local"
PIECE = ("zz_ma_convocation_importante.txt", b"CONVOCATION A L'ASSEMBLEE GENERALE\nProjet de resolution N1.\n")

#: Au-dela de ce nombre de lignes, `/documents` tronque. Mesure, pas suppose.
PLAFOND_LIGNES_DOCUMENTS = 12


def _visible(html: str) -> str:
    corps = re.search(r"<main[^>]*>(.*?)</main>", html, re.S)
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", corps.group(1) if corps else html)).strip()


class ParcoursDepot(unittest.TestCase):
    def setUp(self) -> None:
        try:
            from fastapi.testclient import TestClient  # type: ignore
        except ImportError:  # pragma: no cover - depend de l'environnement
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
        self.client = TestClient(create_app(load_instance(None, str(self.racine)), 2026, access_token=JETON, rebrancher=frozenset({"ajouter_document"})))

    def _deposer(self, nom: str, contenu: bytes):
        return self.client.post(
            f"/depot?token={JETON}",
            data={"intent": "document", "return": "document_intake", "source": "menu"},
            files=[("files", (nom, contenu, "text/plain"))],
            follow_redirects=False,
        )

    # --- ce qui marche, et qu'il faut proteger ---------------------------------

    def test_le_depot_redirige_en_gardant_le_jeton_et_l_identifiant_du_depot(self) -> None:
        reponse = self._deposer(*PIECE)
        self.assertEqual(reponse.status_code, 303)
        destination = reponse.headers["location"]
        self.assertIn("depot=", destination)
        self.assertIn(f"token={JETON}", destination, "le jeton doit survivre a la redirection")

    def test_l_ecran_d_arrivee_confirme_reellement_le_depot(self) -> None:
        """Compare l'ecran AVANT et APRES: un texte statique ne prouverait rien.

        Les mots `deposez`, `ajouter` sont dans la description permanente de la
        page. Chercher un mot ne dit donc pas si le depot est confirme; seule la
        difference entre les deux etats le dit.
        """
        avant = _visible(self.client.get(f"/documents/ajouter?token={JETON}").text)
        reponse = self._deposer(*PIECE)
        apres = _visible(self.client.get(reponse.headers["location"], follow_redirects=True).text)

        self.assertGreater(len(apres), len(avant), "l'ecran d'arrivee n'a pas change apres un depot")
        self.assertIn("1/1", apres, "l'ecran ne rapporte pas ce qui a ete traite")

    def test_la_piece_deposee_est_retrouvable_quand_le_coffre_est_petit(self) -> None:
        """Retrouver n'est pas afficher. L'assertion d'origine confondait les deux.

        Ecrite le 2026-09-07, elle cherchait `PIECE[0]` - le nom de fichier brut -
        dans le HTML. C'etait une MODALITE: le seul chemin qui la satisfait est
        d'imprimer le nom, or ce nom est ecrit par un tiers et porte souvent un
        patronyme, sur une page diffusable. L'invariant qu'elle voulait garder
        est ailleurs: *la piece que je viens de deposer est sur la page*.

        On l'asserte donc par l'identifiant public de la piece, releve dans le
        registre a partir du nom depose. Le lien entre le depot et la ligne
        rendue est ainsi prouve, sans que le nom traverse la reponse HTTP.
        """

        self._deposer(*PIECE)
        page = self.client.get(f"/documents?token={JETON}").text

        self.assertIn(self._doc_id_de_la_piece(), page, "la piece deposee n'est sur aucune ligne")
        self.assertNotIn(PIECE[0], page, "le nom de fichier brut ne doit jamais etre rendu")

    def test_la_piece_reste_retrouvable_par_recherche_quand_le_coffre_grossit(self) -> None:
        """Le chemin de retour quand la liste tronque: la barre de recherche.

        Ce test est le CONTROLE de la retrouvabilite. Il echoue reellement si le
        filtre serveur cesse de lire le nom de fichier d'origine: le mot
        `importante` n'existe nulle part ailleurs que dans le nom que le
        deposant a donne - ni dans le type deduit, ni dans la date, ni dans
        l'identifiant, ni dans le contenu de la piece.
        """

        for index in range(PLAFOND_LIGNES_DOCUMENTS + 2):
            self._deposer(f"aaa_piece_{index:02d}.txt", b"Piece de remplissage.\n")
        self._deposer(*PIECE)
        doc_id = self._doc_id_de_la_piece()

        sans_recherche = self.client.get(f"/documents?token={JETON}").text
        # `RM-2026-0183`, lot 5 du 2026-09-13: l'explorateur des documents classes
        # range CHAQUE piece du registre. La liste ne tronque plus, et la
        # precondition de ce test - `le coffre tronque` - s'est inversee: elle
        # disait elle-meme de revoir ce test ce jour-la.
        self.assertIn(doc_id, sans_recherche, "l'explorateur ne range plus la piece deposee")
        self.assertNotIn(PIECE[0], sans_recherche, "le nom de fichier brut ne doit jamais etre rendu")

        trouve = self.client.get(f"/documents?q=importante&token={JETON}").text
        self.assertIn(doc_id, trouve, "la piece deposee n'est plus retrouvable par recherche")
        self.assertNotIn(PIECE[0], trouve, "le nom de fichier brut ne doit jamais etre rendu")
        # Ce que la precondition garantissait, dit directement: la page de
        # recherche FILTRE. Sans ce temoin, une page qui rendrait tout le coffre
        # trouverait la piece sans avoir lu son nom.
        self.assertNotIn(self._doc_id_de("aaa_piece_00.txt"), trouve,
                         "la recherche rend tout le coffre: elle ne prouve pas qu'elle lit le nom")

    def test_la_barre_de_recherche_filtre_desormais(self) -> None:
        """Etait un test de CARACTERISATION jusqu'au 2026-09-08.

        Il figeait le defaut `la recherche ne filtre rien`, et son message
        demandait sa suppression le jour de la correction. Plutot que le
        supprimer, on l'a retourne: il garde maintenant l'acquis.
        """

        self._deposer(*PIECE)
        for index in range(PLAFOND_LIGNES_DOCUMENTS + 2):
            self._deposer(f"aaa_piece_{index:02d}.txt", b"Piece de remplissage.\n")

        sans = _visible(self.client.get(f"/documents?token={JETON}").text)
        avec = _visible(self.client.get(f"/documents?q=importante&token={JETON}").text)
        self.assertNotEqual(sans, avec, "la recherche rend la meme page: elle ne filtre rien")
        self.assertIn("Recherche en cours", avec, "l'utilisateur ne voit pas qu'un filtre est actif")

    def _doc_id_de_la_piece(self) -> str:
        """L'identifiant public de la piece deposee, releve dans le registre.

        Lecture SERVEUR d'un champ non expose: c'est exactement l'operation que
        le correctif autorise, et qu'il interdit de rendre.
        """
        return self._doc_id_de(PIECE[0])

    def _doc_id_de(self, nom: str) -> str:
        registre = self.racine / "registers" / "registre_documents.csv"
        self.assertTrue(registre.exists(), "la piece n'a pas atteint le registre")
        with registre.open(encoding="utf-8-sig", newline="") as flux:
            lignes = [ligne for ligne in csv.DictReader(flux) if ligne.get("file_name") == nom]
        self.assertEqual(len(lignes), 1, "la piece deposee n'est pas au registre, ou elle y est en double")
        doc_id = (lignes[0].get("doc_id") or "").strip()
        self.assertTrue(doc_id, "la piece est au registre sans identifiant public")
        return doc_id

    # `test_CARACTERISATION_la_piece_deposee_devient_introuvable_des_que_le_coffre_grossit`
    # vivait ici. Il caracterisait le defaut `au-dela de 12 lignes, la piece
    # n'est sur aucun ecran`, et demandait sa suppression le jour de la
    # correction. Ce jour est le 2026-09-13: l'explorateur range chaque piece
    # (`RM-2026-0183`, lot 5). Il ne serait pas tombe de lui-meme - il mesurait
    # le nom de fichier brut, qui reste masque - et c'est pour cela qu'il part
    # a la main. Sa propriete de confidentialite vit dans le test du dessus.

    # `test_CARACTERISATION_la_barre_de_recherche_ne_filtre_rien` vivait ici. Son
    # propre message demandait sa suppression le jour ou la recherche filtrerait.
    # Ce jour est le 2026-09-08: il est devenu
    # `test_la_barre_de_recherche_filtre_desormais`, plus haut, du cote de ce
    # qu'il faut proteger.


if __name__ == "__main__":
    unittest.main()
