"""L'extraction de texte tient l'UTF-8 de bout en bout, et dit ce qu'elle relit.

Ces tests fixent un axe, pas une modalite constatee: les fichiers deposes dans
une copropriete ne sont pas ecrits par le meme outil ni sur la meme plateforme
que celle qui les relit. Trois regles en decoulent.

- **la marque d'ordre d'octets n'est pas du texte.** Un tableur pose en tete de
  fichier une marque invisible. Relue en `utf-8` simple, elle survit dans le
  texte extrait: le premier mot du document cesse alors de commencer par sa
  premiere lettre, et toute recherche ancree en debut de texte le manque sans
  rien signaler. Mesure du 2026-09-04 sur cabinet reel: 21 artefacts sur 2 209
  portaient cette marque residuelle;
- **une source relue autrement est un fait, pas un rattrapage.** L'ancienne
  chaine retombait sur un jeu latin qui ne peut pas echouer. Elle produisait
  donc toujours un texte, parfois faux, et jamais de trace. Le fait de
  provenance suit desormais le document;
- **ce qui est ecrit est relu a l'identique.** L'artefact texte est UTF-8 quel
  que soit l'encodage par defaut de la plateforme, qui sur Windows n'est pas
  l'UTF-8.
"""

from __future__ import annotations

import shutil
import tempfile
import unittest
from pathlib import Path

from coproscope.core.common import RunContext, load_instance, read_csv
from coproscope.modules import docuscope


PHRASE = "Proces-verbal de l’Assemblée générale du 3 juillet."


class ExtractionEncodageTests(unittest.TestCase):
    def setUp(self) -> None:
        repo_root = Path(__file__).resolve().parents[2]
        source_example = repo_root / "examples" / "synthetic_copro"
        self.tempdir = tempfile.TemporaryDirectory()
        self.example_root = Path(self.tempdir.name) / "synthetic_copro"
        shutil.copytree(source_example, self.example_root)
        self.instance = load_instance(str(self.example_root / "instance.yml"), None)
        self.depot = self.instance.root("raw")

    def tearDown(self) -> None:
        self.tempdir.cleanup()

    def _extraire(self, nom: str, octets: bytes) -> dict[str, str]:
        """Depose une source brute, lance la chaine, rend la fiche du document."""
        cible = self.depot / nom
        cible.parent.mkdir(parents=True, exist_ok=True)
        cible.write_bytes(octets)
        run = RunContext(self.instance, "extraction encodage")
        docuscope.inventory(self.instance, run)
        docuscope.extract_text(self.instance, run)
        _, rows = read_csv(self.instance.register("documents"))
        return next(row for row in rows if row["file_name"] == nom)

    def _texte_extrait(self, row: dict[str, str]) -> str:
        chemin = self.instance.root("workspace") / row["text_path"]
        return chemin.read_bytes().decode("utf-8")

    def test_la_marque_dordre_doctets_ne_survit_pas_dans_le_texte(self) -> None:
        row = self._extraire("bom_utf8.txt", b"\xef\xbb\xbf" + PHRASE.encode("utf-8"))
        texte = self._texte_extrait(row)

        self.assertNotIn("\ufeff", texte)
        self.assertIn(PHRASE, texte)
        # Le premier mot commence bien par sa premiere lettre: rien ne s'est
        # glisse entre la fin de l'en-tete de page et le debut du texte.
        corps = texte.split("=====", 2)[-1].lstrip("\r\n")
        self.assertTrue(corps.startswith("Proces-verbal"), repr(corps[:20]))

    def test_une_source_latine_est_relue_et_le_fait_est_inscrit(self) -> None:
        row = self._extraire("latin.txt", PHRASE.encode("cp1252"))
        texte = self._texte_extrait(row)

        self.assertIn("Assemblée générale", texte)
        self.assertNotIn("\ufffd", texte)
        self.assertIn("relue en cp1252", row["notes"])

    def test_une_source_indecodable_est_signalee_et_non_avalee(self) -> None:
        # 0x81 n'est defini ni en UTF-8 ni en cp1252: seul le dernier recours
        # accepte ces octets, et il doit le dire.
        row = self._extraire("indecodable.txt", b"Quorum \x81\x9d atteint")
        texte = self._texte_extrait(row)

        self.assertIn("Quorum", texte)
        self.assertIn("dernier recours en latin-1", row["notes"])

    def test_une_source_utf8_propre_ne_porte_aucune_note_dencodage(self) -> None:
        row = self._extraire("propre.txt", PHRASE.encode("utf-8"))

        self.assertNotIn("cp1252", row.get("notes", ""))
        self.assertNotIn("dernier recours", row.get("notes", ""))
        self.assertIn("Assemblée", self._texte_extrait(row))

    def test_lartefact_texte_est_utf8_quel_que_soit_le_defaut_de_plateforme(self) -> None:
        """L'encodage par defaut de Windows n'est pas l'UTF-8.

        Une ecriture qui laisserait la plateforme choisir produirait ici des
        octets latins, illisibles par le reste de la chaine qui, elle, relit en
        UTF-8. On verifie donc les octets, pas la chaine deja decodee.
        """
        row = self._extraire("accents.txt", PHRASE.encode("utf-8"))
        octets = (self.instance.root("workspace") / row["text_path"]).read_bytes()

        self.assertIn("Assemblée".encode("utf-8"), octets)
        self.assertNotIn("Assemblée".encode("cp1252"), octets)
        self.assertNotIn(b"\xef\xbf\xbd", octets)

    def test_le_html_suit_la_meme_regle_dencodage(self) -> None:
        page = f"<html><body><p>{PHRASE}</p></body></html>"
        row = self._extraire("page.html", b"\xef\xbb\xbf" + page.encode("utf-8"))
        texte = self._texte_extrait(row)

        self.assertNotIn("\ufeff", texte)
        self.assertIn("Assemblée générale", texte)


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
