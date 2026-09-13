# -*- coding: utf-8 -*-
"""L'accueil du controle de gouvernance filtre sur place, sans second calcul.

`RM-2026-0183`, recette de Brice du 2026-09-13: la liste des decisions sur
l'accueil, des pastilles de constat qui la filtrent sur place, et un seul bloc
pour *etabli par les pieces* et *l'outil ne sait pas encore*, avec des codes.

**LES PREDICATS, ENONCES AVANT DE CHERCHER.**

1. *Pour chaque constat, la liste de l'accueil et le tableau detaille rendent
   le MEME ensemble d'identifiants de ligne, et sa taille est le nombre de la
   pastille.* Mesure sur les pages rendues, par le marqueur `data-cs-ligne`
   pose sur les deux rendus - pas en comptant des `<tr>`.
2. *Une pastille ne quitte pas l'accueil*, et une seule porte `aria-current`:
   celle dont le constat et les filtres sont ceux de l'adresse.
3. *Le script ne recalcule rien*: il ne lit aucune appartenance et retombe sur
   une navigation ordinaire.
4. *Chaque axe n'a qu'un canal.* Dans la feuille de l'accueil, une couleur
   n'est posee que sous `[data-alerte]`, un style de bordure que sous
   `[data-etabli]`, et aucune regle de composant ne pose l'un ou l'autre -
   l'ordre de la feuille ne peut donc pas les ecraser. Chaque valeur que le
   PRODUCTEUR emet (`source` des constats, table `ALERTE_PAR_TON`) a sa regle.

**OU LA GARDE REGARDE.** Les pages servies par la route, sur une copie de
l'exemple alimentee du corpus de `test_controle_gouvernance`; la feuille
`styles_part_37.css` parsee regle par regle. Des temoins fabriques font mordre
chaque instrument.
"""
from __future__ import annotations

import json
import re
import shutil
import tempfile
import unittest
from pathlib import Path

from coproscope.core.common import load_instance
from coproscope.modules import actes_autorisation as A
from coproscope.web import _controle_gouvernance_accueil as ACC
from coproscope.web import _controle_gouvernance_constats as C
from coproscope.web.controle_gouvernance_view import build_controle_gouvernance_view

try:
    from tests.test_controle_gouvernance import CORPUS
except ImportError:  # invocation a plat
    from test_controle_gouvernance import CORPUS  # type: ignore

WEB = Path(__file__).resolve().parents[1] / "src" / "coproscope" / "web"
FEUILLE = WEB / "static" / "styles_part_37.css"
SCRIPT = WEB / "static" / "controle_gouvernance_filtres.js"
COMPOSANTS = ("cs-pastille", "cs-signal", "cs-echantillon", "cs-trait")
COULEUR = {"color", "background", "background-color", "border-color"}
FORME = {"border-style"}


def ids_de_ligne(html: str, zone: str) -> list[str]:
    """Les identifiants portes par `data-cs-ligne` dans la zone nommee."""
    return re.findall(r'data-cs-ligne="([^"]+)"', zone_de(html, zone))


def zone_de(html: str, zone: str) -> str:
    if zone == "accueil":
        m = re.search(r'<ol class="cs-accueil-lignes".*?</ol>', html, re.S)
    else:
        m = re.search(r'<table class="cs-rappro-table.*?</table>', html, re.S)
    return m.group(0) if m else ""


def regles(css: str) -> list[tuple[str, dict[str, str]]]:
    """Les regles les plus internes: `(selecteur, {propriete: valeur})`."""
    sans_commentaires = re.sub(r"/\*.*?\*/", "", css, flags=re.S)
    sortie = []
    for selecteur, corps in re.findall(r"([^{}]+)\{([^{}]*)\}", sans_commentaires):
        props = {}
        for decl in corps.split(";"):
            if ":" in decl:
                cle, valeur = decl.split(":", 1)
                props[cle.strip().lower()] = valeur.strip()
        sortie.append((selecteur.strip(), props))
    return sortie


def violations_d_axe(css: str) -> list[str]:
    fautes = []
    for selecteur, props in regles(css):
        for prop in props:
            if prop in COULEUR and "[data-alerte" not in selecteur and any(c in selecteur for c in COMPOSANTS):
                fautes.append("couleur hors axe: %s { %s }" % (selecteur, prop))
            if prop in COULEUR and "[data-etabli" in selecteur:
                fautes.append("couleur sur l'axe forme: %s { %s }" % (selecteur, prop))
            if prop in FORME and "[data-etabli" not in selecteur:
                fautes.append("forme hors axe: %s { %s }" % (selecteur, prop))
            if prop == "border" and any(c in selecteur for c in COMPOSANTS):
                fautes.append("raccourci border sur un composant: %s" % selecteur)
    return fautes


def valeurs_sans_regle(css: str) -> list[str]:
    selecteurs = " ".join(s for s, _ in regles(css))
    attendues = {'[data-etabli="%s"]' % c["source"] for c in C.CONSTATS}
    attendues |= {'[data-alerte="%s"]' % v for v in ACC.ALERTE_PAR_TON.values()}
    return sorted(a for a in attendues if a not in selecteurs)


class LES_INSTRUMENTS_MORDENT(unittest.TestCase):
    def test_une_couleur_posee_sous_la_forme_est_vue(self) -> None:
        fausse = FEUILLE.read_text(encoding="utf-8") + '\n[data-etabli="outil"] { color: #d92d20; }\n'
        self.assertTrue(violations_d_axe(fausse))

    def test_une_couleur_posee_sur_un_composant_est_vue(self) -> None:
        fausse = FEUILLE.read_text(encoding="utf-8") + "\n.cs-pastille.is-active { background: #eee; }\n"
        self.assertTrue(violations_d_axe(fausse))

    def test_des_tirets_retires_sont_vus(self) -> None:
        fausse = FEUILLE.read_text(encoding="utf-8").replace('[data-etabli="outil"]', '[data-etabli="autre"]')
        self.assertEqual(valeurs_sans_regle(fausse), ['[data-etabli="outil"]'])

    def test_une_ligne_retiree_d_une_zone_est_vue(self) -> None:
        html = '<ol class="cs-accueil-lignes"><li data-cs-ligne="a"></li></ol><table class="cs-rappro-table"><tr data-cs-ligne="a"></tr><tr data-cs-ligne="b"></tr></table>'
        self.assertNotEqual(sorted(ids_de_ligne(html, "accueil")), sorted(ids_de_ligne(html, "tableau")))


class CHAQUE_AXE_N_A_QU_UN_CANAL(unittest.TestCase):
    def test_la_feuille_de_l_accueil_separe_les_axes(self) -> None:
        self.assertEqual(violations_d_axe(FEUILLE.read_text(encoding="utf-8")), [])

    def test_chaque_valeur_emise_par_le_producteur_a_sa_regle(self) -> None:
        self.assertEqual(valeurs_sans_regle(FEUILLE.read_text(encoding="utf-8")), [])

    def test_le_script_ne_recalcule_aucun_filtre_et_sait_se_replier(self) -> None:
        script = SCRIPT.read_text(encoding="utf-8")
        for interdit in ("data-cs-cles", "data-etabli", "data-alerte", "signaux", "hidden"):
            with self.subTest(interdit=interdit):
                self.assertNotIn(interdit, script)
        self.assertIn("location.assign", script)
        self.assertIn("fetch(", script)


class LA_LISTE_ET_LE_TABLEAU_SONT_LE_MEME_FILTRE(unittest.TestCase):
    def setUp(self) -> None:
        depot = Path(__file__).resolve().parents[2]
        self.tempdir = tempfile.TemporaryDirectory()
        racine = Path(self.tempdir.name) / "instance"
        shutil.copytree(depot / "examples" / "synthetic_copro", racine)
        config = json.loads((racine / "instance.yml").read_text(encoding="utf-8"))
        config["settings"]["vault"] = {"local_root": "./vault_local"}
        (racine / "instance.yml").write_text(json.dumps(config, indent=2), encoding="utf-8")
        self.instance = load_instance(str(racine / "instance.yml"), None)
        A.ecrire(self.instance, A.TABLE_ACTES, CORPUS, ["DOC-PV"])

    def tearDown(self) -> None:
        self.tempdir.cleanup()

    def _client(self):
        from fastapi.testclient import TestClient

        from coproscope.web.app import create_app

        return TestClient(create_app(self.instance, 2025))

    def test_un_cas_a_reponse_connue(self) -> None:
        """`f_issue=REJETEE` sur le corpus: le nombre est connu d'avance, et un
        zero uniforme ne passerait pas en silence."""
        attendu = sum(1 for acte in CORPUS if str(acte.get("resultat") or "").upper() == "REJETEE")
        self.assertGreater(attendu, 0)
        page = self._client().get("/controle-gouvernance?vue=synthese&f_issue=REJETEE").text
        self.assertEqual(len(ids_de_ligne(page, "accueil")), attendu)

    def test_chaque_pastille_rend_le_meme_ensemble_dans_les_deux_vues(self) -> None:
        client = self._client()
        vue = build_controle_gouvernance_view(self.instance, 2025, {})
        mesures = vue["constats"] + vue["constats_outil"]
        self.assertTrue(mesures, "le corpus doit produire des constats")
        for mesure in mesures:
            with self.subTest(constat=mesure["constat"]["cle"]):
                self.assertIn("vue=synthese", mesure["lien"])
                self.assertTrue(mesure["lien"].endswith("#cs-liste"))
                accueil = client.get(mesure["lien"]).text
                tableau = client.get(mesure["lien"].replace("vue=synthese", "vue=tableau")).text
                vus = ids_de_ligne(accueil, "accueil")
                self.assertEqual(len(vus), mesure["n"])
                self.assertEqual(sorted(vus), sorted(ids_de_ligne(tableau, "tableau")))
                self.assertNotIn("Divergence entre les deux vues", accueil)
                actives = re.findall(r'<a class="cs-pastille(?: is-active)?"[^>]*aria-current="true"', accueil)
                self.assertEqual(len(actives), 1)
                self.assertIn('data-cs-filtre="%s"' % mesure["constat"]["cle"], actives[0])

    def test_sans_filtre_seule_toutes_les_decisions_est_active(self) -> None:
        page = self._client().get("/controle-gouvernance").text
        self.assertEqual(len(ids_de_ligne(page, "accueil")), len(CORPUS))
        self.assertEqual(re.findall(r'<a class="cs-pastille(?: is-active)?"[^>]*aria-current', page), [])
        self.assertIn('data-cs-filtre="tout" aria-current="true"', page)

    def test_une_marge_sans_conclusion_ne_dit_rien_d_alarmant(self) -> None:
        page = self._client().get("/controle-gouvernance").text
        marges = re.findall(r'<span class="cs-accueil-marge">(.*?)</span>\s*</summary>', page, re.S)
        self.assertEqual(len(marges), len(CORPUS))
        for marge in marges:
            visible = re.sub(r'<span class="sr-only">.*?</span>', "", marge, flags=re.S)
            self.assertNotIn("instruire", visible.lower())


if __name__ == "__main__":
    unittest.main()
