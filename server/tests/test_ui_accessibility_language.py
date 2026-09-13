from __future__ import annotations

import importlib.util
import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SERVER = ROOT / "server"
WEB = SERVER / "src" / "coproscope" / "web"
BASE_HTML = SERVER / "src" / "coproscope" / "web" / "templates" / "base.html"
STYLES_CSS = SERVER / "src" / "coproscope" / "web" / "static" / "styles.css"
LANGUAGE_DOC = ROOT / "docs" / "accessibilite_registre_langage.md"
QA_DOC = ROOT / "docs" / "archive" / "recettes_ux" / "qa_ux_accessibilite_securite.md"

TEMPLATES = WEB / "templates"

#: `RM-2026-0106`, 2026-09-12. **Cette portee etait une liste de neuf gabarits
#: ecrite une fois, et le dossier en porte 46.** Trente-sept n'etaient jamais
#: regardes, et **la garde ne l'a jamais dit** - c'est le mode de defaillance
#: propre aux gardes: pas une reponse fausse, une fausse tranquillite. Un
#: gabarit ajoute demain restait hors du regard pour toujours.
#:
#: La portee se derive donc de l'arborescence: **une PAGE est un gabarit qui
#: etend `base.html`**, ce qui est un invariant du produit et non une liste de
#: noms observes. Mesure du jour: 40 pages sur 46 gabarits, les neuf de
#: l'ancienne liste toutes comprises, et **zero nouveau constat** - elargir ne
#: coutait rien, c'est le silence qui coutait.
EXTEND_BASE = re.compile(r'\{%\s*extends\s+"base\.html"')


def _pages() -> tuple[Path, ...]:
    """Les gabarits de PAGE, derives de l'arborescence et jamais enumeres."""
    return tuple(
        chemin for chemin in sorted(TEMPLATES.glob("*.html"))
        if EXTEND_BASE.search(chemin.read_text(encoding="utf-8"))
    )


def _tous_les_gabarits() -> tuple[Path, ...]:
    """Tout gabarit, page ou fragment: un fragment s'affiche dans une page."""
    return tuple(sorted(TEMPLATES.glob("*.html")))

VAULT_WORD = re.compile(r"(?<![A-Za-z0-9_])vault(?![A-Za-z0-9_])", re.I)


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


# `RM-2026-0106`: la definition de *texte qui parvient a l'utilisateur* vit a
# cote, dans `_texte_visible.py`, et cette garde ne la redefinit plus. Le
# chargement par chemin tient dans les DEUX facons dont ce depot joue ses
# tests - `discover -s tests` a plat et `-m unittest tests.X` en paquet -
# la ou un import relatif ne tient que dans la seconde.
_SPEC_TEXTE = importlib.util.spec_from_file_location(
    "coproscope_tests_texte_visible",
    Path(__file__).resolve().with_name("_texte_visible.py"))
_TEXTE = importlib.util.module_from_spec(_SPEC_TEXTE)
_SPEC_TEXTE.loader.exec_module(_TEXTE)
texte_visible = _TEXTE.texte_visible


class UiAccessibilityLanguageContractTests(unittest.TestCase):
    def test_base_exposes_keyboard_skip_and_help_landmarks(self) -> None:
        html = _read(BASE_HTML)

        self.assertIn('<a class="skip-link" href="#contenu">Aller au contenu</a>', html)
        self.assertIn('<main id="contenu" tabindex="-1"', html)
        self.assertIn('aria-describedby="navigation-aide"', html)
        self.assertIn('class="quick-help"', html)
        self.assertIn("<details>", html)
        self.assertIn("<summary>Aide rapide</summary>", html)
        self.assertIn("Au clavier", html)
        self.assertIn("ecran tactile", html)

    def test_global_navigation_explains_jargon_in_accessible_labels(self) -> None:
        html = _read(BASE_HTML)
        nav_match = re.search(r"<nav[^>]*>(?P<nav>.*?)</nav>", html, flags=re.S)
        self.assertIsNotNone(nav_match)
        nav = nav_match.group("nav")

        self.assertIn('aria-label="Navigation principale"', html)
        self.assertIn('aria-describedby="navigation-aide"', html)
        self.assertIn('aria-label="Tableau de bord, accueil des priorites"', nav)
        self.assertIn('aria-label="Travaux suivis, preuves manquantes et partage a verifier"', nav)
        self.assertIn('aria-label="Documents, pieces et preuves"', nav)
        # Ecrans supprimes par la recette du 2026-09-13 (`RM-2026-0183`).
        self.assertNotIn('aria-label="Droits, roles et gouvernance"', nav)
        self.assertNotIn('aria-label="Confidentialite, diffusion et masquage"', nav)
        self.assertNotIn('aria-label="Depot local et exports prepares"', nav)
        self.assertIn('aria-current="page"', nav)

    def test_global_styles_keep_focus_and_table_helpers_visible(self) -> None:
        css = _read(STYLES_CSS)

        self.assertIn(".skip-link:focus", css)
        self.assertIn(".skip-link:focus-visible", css)
        self.assertIn(":focus-visible", css)
        self.assertIn(".sr-only", css)
        self.assertIn(".quick-help", css)
        self.assertIn("caption-side: top", css)
        self.assertIn(".table-caption", css)
        self.assertIn("@media (hover: none)", css)
        self.assertIn("min-height: 44px", css)

    def test_language_register_documents_table_and_help_rules(self) -> None:
        doc = _read(LANGUAGE_DOC)

        self.assertIn("Les tableaux doivent avoir un titre", doc)
        self.assertIn("infobulle ou une micro-definition proche", doc)
        self.assertIn("clavier/tactile", doc)
        self.assertIn("Ne pas utiliser la couleur seule", doc)
        self.assertIn("Le focus clavier doit etre visible", doc)
        self.assertIn("Depot local", doc)
        self.assertIn("Sync", doc)

    def test_main_views_keep_novice_friendly_explanations(self) -> None:
        missing: list[str] = []

        for path in _pages():
            source = _read(path)
            has_help = any(
                marker in source
                for marker in (
                    'class="hint"',
                    'class="lead"',
                    'aria-label=',
                    "<caption",
                    'title="',
                    "<dl",
                    "<small",
                    "help-dot",
                )
            )
            if not has_help:
                missing.append(str(path.relative_to(ROOT)))

        self.assertEqual([], missing)

    def test_primary_visible_text_uses_coffre_not_vault_jargon(self) -> None:
        violations: list[str] = []

        for path in _tous_les_gabarits():
            primary_text = texte_visible(path)
            match = VAULT_WORD.search(primary_text)
            if match:
                violations.append(f"{path.relative_to(ROOT)}: {match.group(0)!r}")

        self.assertEqual([], violations)

    def test_qa_doc_records_manual_review_axes(self) -> None:
        doc = _read(QA_DOC).lower()

        self.assertIn("novice-friendly", doc)
        self.assertIn("coffre", doc)
        self.assertIn("routes gardees par token", doc)
        self.assertIn("exports passation derives", doc)
        self.assertIn(".git/.venv/caches", doc)


class LA_PORTEE_DERIVEE_NE_PEUT_PAS_DEVENIR_VIDE(unittest.TestCase):
    """`RM-2026-0106`: deriver une portee cree un nouveau silence possible.

    Une liste ecrite a la main ne se vide pas toute seule; une portee derivee,
    si - un dossier deplace, un motif qui cesse de correspondre, et les deux
    gardes ci-dessus passent sur l'ensemble vide **en rendant OK**. La garde
    de l'instrument est donc la contrepartie obligatoire de la derivation.
    """

    def test_la_derivation_trouve_les_pages(self) -> None:
        pages = _pages()
        self.assertGreaterEqual(
            # Plancher a la mesure: 40 pages avant la recette du 2026-09-13, 28
            # apres la suppression de 12 ecrans (`RM-2026-0183`).
            len(pages), 28,
            "la derivation ne trouve presque aucune page: le motif `extends` "
            "ou le dossier a bouge, et les gardes de langage passeraient sur "
            "le vide sans rien signaler")

    def test_toute_page_est_un_gabarit_du_dossier(self) -> None:
        self.assertLessEqual(len(_pages()), len(_tous_les_gabarits()))

    def test_la_portee_couvre_ce_que_la_liste_couvrait(self) -> None:
        """Conservation: aucune des neuf pages historiques ne sort du regard.

        Quatre ont ete SUPPRIMEES par la recette du 2026-09-13 (`RM-2026-0183`):
        elles doivent avoir disparu du dossier, et non pas seulement du regard.
        """
        noms = {chemin.name for chemin in _pages()}
        for historique in ("overview.html", "documents.html", "pieces.html",
                           "requests.html", "agcontentieux.html"):
            with self.subTest(gabarit=historique):
                self.assertIn(historique, noms)
        for supprime in ("actions.html", "pilotage.html", "governance.html", "depot.html"):
            with self.subTest(supprime=supprime):
                self.assertFalse((TEMPLATES / supprime).exists())


if __name__ == "__main__":
    unittest.main()
