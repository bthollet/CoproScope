# -*- coding: utf-8 -*-
"""La demo statique tient sans serveur: chaque lien mene a un fichier.

`RM-2026-0183`, lot 8 du 2026-09-13. La demo publiee sur GitHub Pages est un
export de l'interface (`tools/demo_statique/exporter.py`).

**LE PREDICAT, ENONCE AVANT DE CHERCHER.** *Dans un site exporte, tout `href` et
tout `src` qui ne sort pas du site mene a un fichier present; aucun ne vise la
racine d'un serveur; aucun jeton ne subsiste; chaque page porte le bandeau de
demo; chaque page charge au moins une feuille de style; aucun formulaire ne
soumet.*

**UN DEFAUT QUE LA PREMIERE VERSION DE CETTE GARDE NE VOYAIT PAS.** Le client de
test ecrit les feuilles de style en absolu, sur son propre hote
(`http://testserver/static/styles.css`). Le verificateur ignorait tout `http:`
comme un lien externe: 296 pages sans aucun style ont passe, et le defaut n'est
apparu qu'a la capture. La forme d'ecriture d'une adresse est un axe; la garde
juge desormais ce qu'une adresse VISE, et exige qu'une feuille de style se
charge.

**OU LA GARDE REGARDE.** Un export reel de l'interface, sur une copie de
`examples/synthetic_copro`, borne par un plafond de pages pour tenir dans la
suite: les liens vers les pages hors plafond doivent alors etre NEUTRALISES, ce
qui eprouve la meme branche que les pages que l'export ne sait pas rendre. Des
temoins fabriques font mordre chaque clause du verificateur.
"""
from __future__ import annotations

import importlib.util
import json
import shutil
import tempfile
import unittest
from pathlib import Path

DEPOT = Path(__file__).resolve().parents[2]
PLAFOND = 40


def _exporteur():
    spec = importlib.util.spec_from_file_location(
        "demo_statique_exporter", DEPOT / "tools" / "demo_statique" / "exporter.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


E = _exporteur()


def _site(pages: dict[str, str]) -> tempfile.TemporaryDirectory:
    dossier = tempfile.TemporaryDirectory()
    for chemin, texte in pages.items():
        cible = Path(dossier.name) / chemin
        cible.parent.mkdir(parents=True, exist_ok=True)
        cible.write_text(texte, encoding="utf-8")
    return dossier


STYLE = '<link rel="stylesheet" href="%sstatic/s.css">'
BON = STYLE % "" + '<body><div class="cs-demo-statique"></div><a href="b/index.html">b</a></body>'
BON_B = STYLE % "../" + '<body><div class="cs-demo-statique"></div><a href="../index.html">a</a></body>'


class LE_VERIFICATEUR_MORD(unittest.TestCase):
    def _fautes(self, pages: dict[str, str]) -> list[str]:
        dossier = _site({"static/s.css": "body{}", **pages})
        self.addCleanup(dossier.cleanup)
        return E.verifier_site(Path(dossier.name))

    def test_un_site_juste_ne_rend_rien(self) -> None:
        self.assertEqual(self._fautes({"index.html": BON, "b/index.html": BON_B}), [])

    def test_une_cible_absente_est_vue(self) -> None:
        self.assertTrue(self._fautes({"index.html": BON}))

    def test_un_lien_vers_la_racine_est_vu(self) -> None:
        self.assertTrue(self._fautes({"index.html": BON.replace("b/index.html", "/comptes")}))

    def test_une_adresse_absolue_vers_le_serveur_d_export_est_vue(self) -> None:
        page = BON.replace('href="static/s.css"', 'href="http://testserver/static/s.css"')
        self.assertIn("index.html: adresse du serveur d'export http://testserver/static/s.css", self._fautes({"index.html": page, "b/index.html": BON_B}))

    def test_une_page_sans_style_est_vue(self) -> None:
        page = BON.replace(STYLE % "", "")
        self.assertEqual(["index.html: aucune feuille de style ne se charge"], self._fautes({"index.html": page, "b/index.html": BON_B}))

    def test_un_bandeau_absent_est_vu(self) -> None:
        self.assertTrue(self._fautes({"index.html": STYLE % "" + "<body><a href='#'>x</a></body>"}))

    def test_un_formulaire_actif_est_vu(self) -> None:
        self.assertTrue(self._fautes({"index.html": BON + '<form action="/x"></form>', "b/index.html": BON_B}))

    def test_un_jeton_est_vu(self) -> None:
        self.assertTrue(self._fautes({"index.html": BON + '<a href="#?token=x">x</a>', "b/index.html": BON_B}))


class LA_REECRITURE(unittest.TestCase):
    def test_deux_requetes_differentes_donnent_deux_fichiers(self) -> None:
        a = E.fichier_de("/controle-gouvernance?vue=synthese")
        b = E.fichier_de("/controle-gouvernance?vue=tableau")
        self.assertNotEqual(a, b)
        self.assertEqual(a, E.fichier_de("/controle-gouvernance?vue=synthese"))
        self.assertEqual(E.fichier_de("/"), "index.html")

    def test_un_lien_exporte_devient_relatif_et_un_autre_est_neutralise(self) -> None:
        html = ('<link rel="stylesheet" href="http://testserver/static/styles.css?v=1">'
                '<body><a href="/comptes?token=t#x">c</a><a href="http://testserver/retire">r</a>'
                '<form action="/p" method="post"></form></body>')
        texte, neutralises = E.reecrire("documents/index.html", html, {"/comptes"})
        self.assertIn('href="../static/styles.css?v=1"', texte)
        self.assertIn('href="../comptes/index.html#x"', texte)
        self.assertIn("data-demo-indisponible", texte)
        self.assertEqual(neutralises, 1)
        self.assertNotIn('action="/p"', texte)
        self.assertIn("cs-demo-statique", texte)


class UNE_INSTANCE_QUI_NE_SE_DIT_PAS_FICTIVE_N_EST_PAS_EXPORTEE(unittest.TestCase):
    """Le bandeau dit *fictive*: sans la declaration dans l'instance, rien ne sort."""

    def _instance(self, dossier: Path, settings: dict | None, brut: str | None = None) -> Path:
        racine = dossier / "instance"
        racine.mkdir()
        texte = brut if brut is not None else json.dumps({"settings": settings or {}})
        (racine / "instance.yml").write_text(texte, encoding="utf-8")
        return racine

    def test_seule_la_declaration_explicite_passe(self) -> None:
        cas = [({"demo": {"fictive": True}}, None, True),
               ({"demo": {"fictive": "oui"}}, None, False),
               ({"demo": {}}, None, False),
               ({}, None, False),
               (None, "settings:\n  demo:\n    fictive: true\n", False)]
        for settings, brut, attendu in cas:
            with self.subTest(settings=settings, brut=brut), tempfile.TemporaryDirectory() as d:
                self.assertIs(E.instance_fictive(self._instance(Path(d), settings, brut)), attendu)

    def test_l_export_refuse_avant_d_ecrire(self) -> None:
        with tempfile.TemporaryDirectory() as d:
            racine = self._instance(Path(d), {})
            sortie = Path(d) / "site"
            with self.assertRaises(SystemExit):
                E.exporter(racine, sortie, 2025, plafond=5)
            self.assertFalse(sortie.exists())


class UN_EXPORT_REEL_TIENT_SANS_SERVEUR(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls._dossier = tempfile.TemporaryDirectory()
        racine = Path(cls._dossier.name) / "instance"
        shutil.copytree(DEPOT / "examples" / "synthetic_copro", racine)
        config = json.loads((racine / "instance.yml").read_text(encoding="utf-8"))
        config["settings"]["vault"] = {"local_root": "./vault_local"}
        config["settings"]["demo"] = {"fictive": True}
        (racine / "instance.yml").write_text(json.dumps(config, indent=2), encoding="utf-8")
        cls.sortie = Path(cls._dossier.name) / "site"
        cls.rapport = E.exporter(racine, cls.sortie, 2025, plafond=PLAFOND)

    @classmethod
    def tearDownClass(cls) -> None:
        cls._dossier.cleanup()

    def test_des_pages_ont_ete_exportees(self) -> None:
        self.assertGreater(self.rapport["pages"], 5)
        self.assertTrue((self.sortie / "index.html").is_file())

    def test_le_site_tient_sans_serveur(self) -> None:
        self.assertEqual(E.verifier_site(self.sortie), [])

    def test_le_rapport_nomme_ce_qui_manque(self) -> None:
        rapport = json.loads((self.sortie / "_rapport.json").read_text(encoding="utf-8"))
        self.assertIn("non_exportees", rapport)
        self.assertIn("plafond_atteint", rapport)


if __name__ == "__main__":
    unittest.main()
