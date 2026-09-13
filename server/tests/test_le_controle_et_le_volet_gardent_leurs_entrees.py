# -*- coding: utf-8 -*-
"""Le groupe *Controle* du menu et le volet rabattable ne perdent aucune entree.

`RM-2026-0183` et `RM-2026-0184`, recette de Brice du 2026-09-13: l'entree 06
devient *Controle*, avec deux sous-onglets - comptes et gouvernance - et le
volet de gauche se replie.

**CE QUE CES GARDES MESURENT, ET OU.**

- **Les onglets se mesurent sur la page RENDUE**, pas sur le gabarit: le
  defaut constate en recette etait un ecran ou l'on arrivait sans voir l'autre
  onglet. Chaque ecran du Controle doit porter les deux liens, et un seul
  `aria-current="page"`, qui designe l'ecran ou l'on est.
- **Le repli se mesure sur ce qu'il cache.** Replie, un lien du menu n'affiche
  plus que son icone: il doit donc etre NOMME autrement que par son texte. La
  garde lit chaque `<a>` de la navigation, ou qu'il soit, sans liste d'entrees.
  Les sous-entrees disparaissent: chacune doit rester atteignable depuis
  l'ecran ou mene l'entree de son groupe.
- **Le bouton dit son etat** (`aria-expanded`) et designe ce qu'il replie
  (`aria-controls` vers un identifiant qui existe). Le stockage du navigateur
  peut etre refuse: chaque acces est sous `try`.

**CE QU'ELLES NE MESURENT PAS.** Aucune ne calcule la cascade dans un
navigateur: la largeur reelle du volet replie n'est pas verifiee ici, et la
recette de page reelle reste la preuve de rendu.
"""
from __future__ import annotations

import re
import unittest
from html.parser import HTMLParser
from pathlib import Path

from tests._exemple_copie import exemple_copie

WEB = Path(__file__).resolve().parents[1] / "src" / "coproscope" / "web"
BASE = WEB / "templates" / "base.html"
SCRIPT = WEB / "static" / "volet_rabattable.js"
CSS = WEB / "static" / "styles_part_35.css"
CONTROLE = ("/comptes", "/controle-gouvernance")


class _Liens(HTMLParser):
    """Les `<a>` d'un bloc, avec leurs attributs et leur texte."""

    def __init__(self) -> None:
        super().__init__()
        self.liens: list[dict[str, str]] = []
        self._pile: list[dict[str, str]] = []

    def handle_starttag(self, tag, attrs):
        if tag == "a":
            lien = {k: (v or "") for k, v in attrs}
            lien["_texte"] = ""
            self._pile.append(lien)

    def handle_data(self, data):
        for lien in self._pile:
            lien["_texte"] += data

    def handle_endtag(self, tag):
        if tag == "a" and self._pile:
            self.liens.append(self._pile.pop())


def liens(html: str) -> list[dict[str, str]]:
    lecteur = _Liens()
    lecteur.feed(html)
    return lecteur.liens


def bloc(html: str, motif: str) -> str:
    m = re.search(motif + r".*?</nav>", html, re.S)
    return m.group(0) if m else ""


def entrees_sans_nom(nav: str) -> list[str]:
    """Les liens qu'un menu replie laisserait sans nom: pas d'`aria-label`."""
    return [lien.get("href", "?") for lien in liens(nav) if not lien.get("aria-label", "").strip()]


class L_INSTRUMENT_REPOND_JUSTE(unittest.TestCase):
    def test_un_lien_sans_aria_label_est_vu(self) -> None:
        nav = '<nav><a href="/a" aria-label="A">A</a><a href="/b"><span>B</span></a></nav>'
        self.assertEqual(entrees_sans_nom(nav), ["/b"])

    def test_le_bloc_de_navigation_est_trouve(self) -> None:
        self.assertTrue(bloc(BASE.read_text(encoding="utf-8"), r'<nav[^>]*cs-sidebar-nav'))


class LE_MENU_REPLIE_GARDE_CHAQUE_ENTREE_NOMMEE(unittest.TestCase):
    def setUp(self) -> None:
        self.base = BASE.read_text(encoding="utf-8")
        self.nav = bloc(self.base, r'<nav[^>]*cs-sidebar-nav')

    def test_chaque_lien_du_menu_porte_un_nom(self) -> None:
        self.assertGreater(len(liens(self.nav)), 5)
        self.assertEqual(entrees_sans_nom(self.nav), [])

    def test_le_bouton_dit_son_etat_et_ce_qu_il_replie(self) -> None:
        bouton = re.search(r"<button[^>]*cs-volet-bascule[^>]*>", self.base)
        self.assertIsNotNone(bouton)
        self.assertIn('aria-expanded="true"', bouton.group(0))
        cible = re.search(r'aria-controls="([^"]+)"', bouton.group(0))
        self.assertIsNotNone(cible)
        self.assertIn('id="%s"' % cible.group(1), self.base)
        self.assertIn("volet_rabattable.js", self.base)

    def test_le_script_bascule_l_etat_annonce_et_survit_a_un_stockage_refuse(self) -> None:
        script = SCRIPT.read_text(encoding="utf-8")
        self.assertIn('setAttribute("aria-expanded"', script)
        acces = [ligne for ligne in script.splitlines() if "localStorage" in ligne]
        self.assertTrue(acces)
        for ligne in acces:
            with self.subTest(ligne=ligne.strip()):
                self.assertIn("try {", ligne)

    def test_le_repli_cache_des_textes_jamais_des_liens(self) -> None:
        css = CSS.read_text(encoding="utf-8")
        replie = css[css.index("@media (min-width: 981px)"):]
        # Regles les plus internes seulement: un corps sans accolade. Le premier
        # jet lisait `@media ... {` comme un selecteur et avalait la regle
        # suivante - une mutation qui cachait tous les liens passait.
        regles = [sel for sel, corps in re.findall(r"([^{}]+)\{([^{}]*)\}", replie)
                  if re.search(r"display:\s*none", corps)]
        self.assertTrue(regles)
        for regle in regles:
            for selecteur in regle.split(","):
                with self.subTest(selecteur=selecteur.strip()):
                    self.assertIsNone(re.search(r"(^|\s)a\s*$", selecteur.strip()), selecteur)

    def test_une_sous_entree_cachee_reste_atteignable_depuis_son_groupe(self) -> None:
        sous = re.search(r'<div class="cs-nav-sous">(.*?)</div>', self.nav, re.S)
        self.assertIsNotNone(sous)
        hrefs = {re.sub(r"\{\{ token_href\('([^']+)'\) \}\}", r"\1", l["href"]) for l in liens(sous.group(1))}
        self.assertEqual(hrefs, set(CONTROLE))
        onglets = (WEB / "templates" / "_controle_onglets.html").read_text(encoding="utf-8")
        for href in hrefs:
            with self.subTest(href=href):
                self.assertIn('href="%s{{ _jeton }}"' % href, onglets)


class LE_CONTROLE_MONTRE_SES_DEUX_ONGLETS(unittest.TestCase):
    """Mesure sur les pages rendues d'une copie de l'exemple synthetique."""

    def test_chaque_ecran_porte_les_deux_onglets_et_designe_le_sien(self) -> None:
        from fastapi.testclient import TestClient

        from coproscope.web.app import create_app

        with exemple_copie("controle_onglets") as instance:
            client = TestClient(create_app(instance, 2025, access_token="jeton-local"))
            for chemin in CONTROLE:
                with self.subTest(ecran=chemin):
                    reponse = client.get(chemin + "?token=jeton-local")
                    self.assertEqual(reponse.status_code, 200)
                    nav = bloc(reponse.text, r'<nav class="cs-controle-onglets')
                    self.assertTrue(nav, "onglets du Controle absents")
                    vus = liens(nav)
                    self.assertEqual([l["href"].split("?")[0] for l in vus], list(CONTROLE))
                    for lien in vus:
                        self.assertIn("token=jeton-local", lien["href"])
                    actifs = [l["href"].split("?")[0] for l in vus if l.get("aria-current") == "page"]
                    self.assertEqual(actifs, [chemin])
                    self.assertNotIn('role="tablist"', nav)


if __name__ == "__main__":
    unittest.main()
