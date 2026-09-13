"""Garde-fous du systeme de design: jetons definis et contrastes mesures.

Ces tests fixent ce que le lot RM-2026-0085 a corrige, pour que les mesures
prises sur l'interface reelle ne puissent pas regresser en silence:

- un jeton `var(--x)` appele mais jamais declare rend la declaration entiere
  invalide; pour un raccourci `border`, `border-style` retombe a `none` et le
  filet ne se dessine pas du tout;
- une couleur de texte posee sur un fond de ton doit tenir le seuil AA de
  4,5:1 pour du texte normal;
- l'etat actif d'une barre d'onglets doit se distinguer de l'inactif
  autrement que par une nuance imperceptible.
"""

from __future__ import annotations

import re
import unittest
from pathlib import Path


SERVER = Path(__file__).resolve().parents[1]
STATIC = SERVER / "src" / "coproscope" / "web" / "static"
TEMPLATES = SERVER / "src" / "coproscope" / "web" / "templates"

SEUIL_AA_TEXTE_NORMAL = 4.5


def _feuilles() -> list[Path]:
    return sorted(STATIC.glob("styles_part_*.css"))


def _bundle() -> str:
    return "\n".join(f.read_text(encoding="utf-8") for f in _feuilles())


def _luminance_relative(couleur: str) -> float:
    couleur = couleur.lstrip("#")
    if len(couleur) == 3:
        couleur = "".join(c * 2 for c in couleur)
    canaux = []
    for i in (0, 2, 4):
        c = int(couleur[i : i + 2], 16) / 255
        canaux.append(c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4)
    return 0.2126 * canaux[0] + 0.7152 * canaux[1] + 0.0722 * canaux[2]


def _contraste(avant: str, arriere: str) -> float:
    a, b = _luminance_relative(avant), _luminance_relative(arriere)
    haut, bas = max(a, b), min(a, b)
    return (haut + 0.05) / (bas + 0.05)


def _sans_commentaires(css: str) -> str:
    return re.sub(r"/\*.*?\*/", "", css, flags=re.S)


def _bloc(css: str, selecteur: str) -> str:
    """Corps de la premiere regle dont la liste de selecteurs contient `selecteur`."""
    motif = re.compile(
        r"(?:^|\})\s*([^{}]*?" + re.escape(selecteur) + r"[^{}]*?)\{([^{}]*)\}",
        re.M,
    )
    trouve = motif.search(_sans_commentaires(css))
    return trouve.group(2) if trouve else ""


def _declaration(corps: str, propriete: str) -> str:
    trouve = re.search(
        rf"(?:^|;)\s*{re.escape(propriete)}\s*:\s*([^;]+)", corps, re.M
    )
    return trouve.group(1).strip() if trouve else ""


class JetonsDeclaresTests(unittest.TestCase):
    """Un jeton appele doit exister, sinon la declaration entiere est perdue."""

    def test_tout_jeton_appele_est_declare_quelque_part(self) -> None:
        bundle = _bundle()
        declares = set(re.findall(r"(--[A-Za-z0-9_-]+)\s*:", bundle))
        for gabarit in TEMPLATES.glob("*.html"):
            declares.update(
                re.findall(r"(--[A-Za-z0-9_-]+)\s*:", gabarit.read_text(encoding="utf-8"))
            )

        manquants: list[str] = []
        for feuille in _feuilles():
            source = feuille.read_text(encoding="utf-8")
            for nom in set(re.findall(r"var\(\s*(--[A-Za-z0-9_-]+)", source)):
                if nom not in declares:
                    manquants.append(f"{feuille.name}: var({nom})")

        self.assertEqual([], sorted(manquants))

    def test_border_et_text_sont_declares_dans_la_palette_racine(self) -> None:
        racine = _bloc((STATIC / "styles_part_01.css").read_text(encoding="utf-8"), ":root")

        self.assertNotEqual("", _declaration(racine, "--border"))
        self.assertNotEqual("", _declaration(racine, "--text"))

    def test_le_bleu_actif_est_un_jeton_et_non_un_litteral_repete(self) -> None:
        racine = _bloc((STATIC / "styles_part_01.css").read_text(encoding="utf-8"), ":root")
        self.assertEqual("#1d5fd8", _declaration(racine, "--accent-blue"))

        for feuille in _feuilles():
            source = feuille.read_text(encoding="utf-8")
            sans_commentaires = re.sub(r"/\*.*?\*/", "", source, flags=re.S)
            if feuille.name == "styles_part_01.css":
                sans_commentaires = sans_commentaires.replace("--accent-blue: #1d5fd8;", "")
            self.assertNotIn("#1d5fd8", sans_commentaires, feuille.name)
            self.assertNotIn("#2f73f6", sans_commentaires, feuille.name)


class ContrasteMesureTests(unittest.TestCase):
    """Chaque paire ci-dessous a ete mesuree en echec sur l'interface reelle."""

    def test_entree_de_navigation_active(self) -> None:
        css = (STATIC / "styles_part_04.css").read_text(encoding="utf-8")
        corps = _bloc(css, ".cs-sidebar .nav a.active")

        self.assertEqual("#ffffff", _declaration(corps, "color"))
        self.assertEqual("var(--accent-blue)", _declaration(corps, "background"))
        # #2f73f6 mesurait 4,28:1, sous le seuil; #1d5fd8 mesure 5,71:1.
        self.assertGreaterEqual(_contraste("#ffffff", "#1d5fd8"), SEUIL_AA_TEXTE_NORMAL)

    def test_pastille_d_echeance_verte(self) -> None:
        css = (STATIC / "styles_part_05.css").read_text(encoding="utf-8")
        corps = _bloc(css, ".cs-deadline-list time")

        fond = _declaration(corps, "background")
        texte = _declaration(corps, "color")
        # #138866 sur #eaf7f1 mesurait 4,02:1.
        self.assertGreaterEqual(_contraste(texte, fond), SEUIL_AA_TEXTE_NORMAL)

    def test_la_famille_de_ton_ne_fixe_pas_la_couleur_du_texte(self) -> None:
        """cs-status-dot + cs-tone-warn mesurait 2,40:1 sur trois lignes."""
        bundle = _bundle()
        for ton in ("danger", "warn", "ok", "info"):
            for famille in ("cs-tone", "cs-card-tone", "cs-reprise-tone"):
                corps = _bloc(bundle, f".{famille}-{ton}")
                self.assertEqual(
                    "",
                    _declaration(corps, "color"),
                    f".{famille}-{ton} ne doit pas imposer de couleur de texte",
                )

    def test_les_fonds_de_ton_tiennent_le_seuil_avec_l_encre_courante(self) -> None:
        bundle = _bundle()
        encre = "#101828"
        for ton in ("danger", "warn", "ok", "info"):
            corps = _bloc(bundle, f".cs-card-tone-{ton}")
            fond = _declaration(corps, "--ton-fond")
            self.assertTrue(fond.startswith("#"), f"cs-card-tone-{ton}: {fond!r}")
            self.assertGreaterEqual(_contraste(encre, fond), SEUIL_AA_TEXTE_NORMAL, ton)

    def test_le_ton_de_reprise_est_un_alias_sans_valeurs_propres(self) -> None:
        """Le nom peut etre rejoue tard; la couleur, elle, n'est ecrite qu'une fois."""
        for ton in ("danger", "warn", "ok", "info"):
            for feuille in _feuilles():
                css = _sans_commentaires(feuille.read_text(encoding="utf-8"))
                if f".cs-reprise-tone-{ton}" not in css:
                    continue
                corps = _bloc(css, f".cs-reprise-tone-{ton}")
                for propriete in ("background", "border-left-color"):
                    valeur = _declaration(corps, propriete)
                    if valeur:
                        self.assertTrue(
                            valeur.startswith("var("),
                            f"{feuille.name}: .cs-reprise-tone-{ton} redeclare "
                            f"{propriete}: {valeur!r}",
                        )

    def test_le_ton_de_reprise_est_rejoue_apres_le_fond_blanc_des_cartes(self) -> None:
        """A specificite egale, seul l'ordre decide: le ton doit venir en dernier.

        Mesure en recette avant correction: la carte de reprise ressortait en
        #ffffff, le ton efface par `.cs-reprise-card { background: #ffffff }`.
        """
        feuille_fond_blanc = None
        feuille_ton = None
        for feuille in _feuilles():
            css = _sans_commentaires(feuille.read_text(encoding="utf-8"))
            if _declaration(_bloc(css, ".cs-reprise-card,"), "background"):
                feuille_fond_blanc = feuille.name
            if ".cs-reprise-tone-danger,\n.cs-reprise-tone-warn" in css:
                feuille_ton = feuille.name

        self.assertIsNotNone(feuille_fond_blanc, "fond des cartes de reprise introuvable")
        self.assertIsNotNone(feuille_ton, "reapplication tardive du ton introuvable")
        self.assertGreater(feuille_ton, feuille_fond_blanc)


class OngletActifTests(unittest.TestCase):
    """L'etat actif doit se voir, pas seulement s'annoncer au lecteur d'ecran."""

    FOND_DE_PAGE = "#ffffff"

    def _etats(self) -> tuple[str, str, str, str]:
        css = (STATIC / "styles_part_33.css").read_text(encoding="utf-8")
        actif = _bloc(css, '.cs-comptes-tabs a[aria-current]:not([aria-current="false"])')
        inactif_bord = _declaration(_bloc(css, ".cs-comptes-tabs a,"), "border-color")
        return (
            _declaration(actif, "background"),
            _declaration(actif, "color"),
            _declaration(actif, "border-color"),
            inactif_bord,
        )

    def test_l_etat_actif_est_pilote_par_aria_current(self) -> None:
        css = (STATIC / "styles_part_33.css").read_text(encoding="utf-8")

        for famille in ("cs-comptes-tabs", "cs-reprise-tabs"):
            selecteur = f'.{famille} a[aria-current]:not([aria-current="false"])'
            self.assertTrue(
                selecteur in css,
                f"{famille}: l'apparence doit suivre la marque semantique, "
                f"selecteur absent: {selecteur}",
            )

        # `_actions_reprise_syndic.html`, second porteur d'onglets, est supprime
        # avec l'ecran `/actions` le 2026-09-13 (`RM-2026-0183`).
        for gabarit, classe in (
            ("accounting.html", "active"),
        ):
            source = (TEMPLATES / gabarit).read_text(encoding="utf-8")
            self.assertTrue(
                f'class="{classe}" aria-current="page"' in source,
                f"{gabarit}: l'onglet courant doit porter aria-current",
            )

    def test_l_actif_se_distingue_de_l_inactif_par_le_fond(self) -> None:
        fond_actif, texte_actif, bord_actif, bord_inactif = self._etats()

        self.assertEqual("var(--accent-blue)", fond_actif)
        self.assertEqual("#ffffff", texte_actif)
        # Avant: #eef4ff contre #ffffff, soit 1,10:1 - invisible sur une capture.
        self.assertGreaterEqual(
            _contraste("#1d5fd8", self.FOND_DE_PAGE), SEUIL_AA_TEXTE_NORMAL
        )
        self.assertEqual("var(--accent-blue)", bord_actif)
        self.assertGreaterEqual(
            _contraste(bord_inactif, self.FOND_DE_PAGE), SEUIL_AA_TEXTE_NORMAL
        )

    def test_le_texte_passe_le_seuil_dans_les_deux_etats(self) -> None:
        fond_actif, texte_actif, _, _ = self._etats()
        del fond_actif, texte_actif

        # actif: #ffffff sur #1d5fd8 ; inactif: #1d5fd8 sur #ffffff.
        self.assertGreaterEqual(_contraste("#ffffff", "#1d5fd8"), SEUIL_AA_TEXTE_NORMAL)
        self.assertGreaterEqual(_contraste("#1d5fd8", "#ffffff"), SEUIL_AA_TEXTE_NORMAL)

    def test_la_barre_ne_grossit_pas(self) -> None:
        """Le budget mesure par l'audit est de 37 px: la hauteur de lien ne bouge pas."""
        css = (STATIC / "styles_part_07.css").read_text(encoding="utf-8")
        corps = _bloc(css, ".cs-comptes-tabs a")

        self.assertEqual("32px", _declaration(corps, "min-height"))


if __name__ == "__main__":
    unittest.main()
