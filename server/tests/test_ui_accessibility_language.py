from __future__ import annotations

import re
import unittest
from html import unescape
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SERVER = ROOT / "server"
WEB = SERVER / "src" / "coproscope" / "web"
BASE_HTML = SERVER / "src" / "coproscope" / "web" / "templates" / "base.html"
STYLES_CSS = SERVER / "src" / "coproscope" / "web" / "static" / "styles.css"
LANGUAGE_DOC = ROOT / "docs" / "accessibilite_registre_langage.md"
QA_DOC = ROOT / "docs" / "archive" / "recettes_ux" / "qa_ux_accessibilite_securite.md"

MAIN_TEMPLATE_TARGETS = (
    WEB / "templates" / "overview.html",
    WEB / "templates" / "actions.html",
    WEB / "templates" / "documents.html",
    WEB / "templates" / "pieces.html",
    WEB / "templates" / "requests.html",
    WEB / "templates" / "agcontentieux.html",
    WEB / "templates" / "pilotage.html",
    WEB / "templates" / "governance.html",
    WEB / "templates" / "depot.html",
)

PRIMARY_VISIBLE_SELECTORS = (
    r"<h[1-3][^>]*>(.*?)</h[1-3]>",
    r"<a\b[^>]*>(.*?)</a>",
    r"<strong\b[^>]*>(.*?)</strong>",
    r"<span\b[^>]*class=[\"'][^\"']*(?:novice-label|nav-extra|badge|pill)[^\"']*[\"'][^>]*>(.*?)</span>",
)

JINJA_COMMENT = re.compile(r"\{#.*?#\}", re.S)
JINJA_OUTPUT = re.compile(r"\{\{.*?\}\}", re.S)
JINJA_BLOCK = re.compile(r"\{%.*?%\}", re.S)
HTML_TAG = re.compile(r"<[^>]+>")
VAULT_WORD = re.compile(r"(?<![A-Za-z0-9_])vault(?![A-Za-z0-9_])", re.I)


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _plain_text(fragment: str) -> str:
    text = JINJA_OUTPUT.sub(" ", fragment)
    text = JINJA_BLOCK.sub(" ", text)
    text = HTML_TAG.sub(" ", text)
    return unescape(re.sub(r"\s+", " ", text)).strip()


def _primary_visible_text(path: Path) -> str:
    source = JINJA_COMMENT.sub(" ", _read(path))
    fragments: list[str] = []
    for pattern in PRIMARY_VISIBLE_SELECTORS:
        fragments.extend(re.findall(pattern, source, flags=re.S | re.I))
    return "\n".join(text for text in (_plain_text(fragment) for fragment in fragments) if text)


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
        self.assertIn('aria-label="Droits, roles et gouvernance"', nav)
        self.assertIn('aria-label="Confidentialite, diffusion et masquage"', nav)
        self.assertIn('aria-label="Depot local et exports prepares"', nav)
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

        for path in MAIN_TEMPLATE_TARGETS:
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

        for path in MAIN_TEMPLATE_TARGETS:
            primary_text = _primary_visible_text(path)
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


if __name__ == "__main__":
    unittest.main()
