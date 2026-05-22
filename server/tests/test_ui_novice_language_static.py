from __future__ import annotations

import re
import unittest
from html import unescape
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
WEB_TEMPLATES = ROOT / "server" / "src" / "coproscope" / "web" / "templates"
LANGUAGE_DOC = ROOT / "docs" / "registre_langage_ui.md"
P0_DOC = ROOT / "docs" / "ux_novice_p0.md"

TEMPLATE_TARGETS = (
    WEB_TEMPLATES / "base.html",
    WEB_TEMPLATES / "_context_banner.html",
    WEB_TEMPLATES / "overview.html",
    WEB_TEMPLATES / "governance.html",
    WEB_TEMPLATES / "depot.html",
    WEB_TEMPLATES / "actions.html",
    WEB_TEMPLATES / "pieces.html",
    WEB_TEMPLATES / "requests.html",
    WEB_TEMPLATES / "agcontentieux.html",
)

EXCLUDED_TEMPLATE = WEB_TEMPLATES / "document_intake.html"

JINJA_COMMENT = re.compile(r"\{#.*?#\}", re.S)
JINJA_OUTPUT = re.compile(r"\{\{.*?\}\}", re.S)
JINJA_BLOCK = re.compile(r"\{%.*?%\}", re.S)
HTML_TAG = re.compile(r"<[^>]+>")
VISIBLE_ATTR = re.compile(r"\b(?:aria-label|title|alt|placeholder)=[\"']([^\"']*)[\"']", re.I)
PRIMARY_BLOCKS = re.compile(
    r"<(?:h[1-3]|a|button|strong|span|small|caption)\b[^>]*>(.*?)</(?:h[1-3]|a|button|strong|span|small|caption)>",
    re.I | re.S,
)
VAULT_WORD = re.compile(r"(?<![A-Za-z0-9_])vault(?![A-Za-z0-9_])", re.I)


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _plain(fragment: str) -> str:
    text = JINJA_OUTPUT.sub(" ", fragment)
    text = JINJA_BLOCK.sub(" ", text)
    text = HTML_TAG.sub(" ", text)
    return unescape(re.sub(r"\s+", " ", text)).strip()


def _primary_text(path: Path) -> str:
    source = JINJA_COMMENT.sub(" ", _read(path))
    attrs = VISIBLE_ATTR.findall(source)
    blocks = PRIMARY_BLOCKS.findall(source)
    return "\n".join(part for part in (_plain(item) for item in (*attrs, *blocks)) if part)


class UiNoviceLanguageStaticTests(unittest.TestCase):
    def test_language_register_defines_core_translation_grid(self) -> None:
        doc = _read(LANGUAGE_DOC)

        self.assertIn("| Concept | Dire en premier niveau | Definition novice |", doc)
        for row in (
            "| Coffre | coffre de copro, coffre local, coffre chiffre |",
            "| Sync | synchronisation a verifier, sync externe, dossier de synchronisation |",
            "| Role | role, mandat, qui agit |",
            "| Preuve | preuve, source, justificatif |",
            "| Action | prochaine action, action attendue, relance |",
        ):
            self.assertIn(row, doc)

        self.assertIn("Jargon primaire interdit sans traduction", doc)
        self.assertIn("Infobulles", doc)
        self.assertIn("Registres de langue", doc)
        self.assertIn("Templates hors perimetre de modification L1: `document_intake.html`", doc)

    def test_p0_doc_records_scope_and_static_contract(self) -> None:
        doc = _read(P0_DOC)

        self.assertIn("sans modifier les templates", doc)
        self.assertIn("ne modifie pas `document_intake.html`", doc)
        self.assertIn("ne touche pas `annotationops`", doc)
        self.assertIn("ne modifie pas les tests QA reserves a Sagan", doc)
        self.assertIn("prochaine action concrete", doc)
        self.assertIn("depot, export prepare, sync non automatique", doc)
        self.assertIn("Le code Jinja, les noms de variables, les routes et les chemins techniques", doc)

    def test_existing_templates_keep_core_novice_anchors(self) -> None:
        expected = {
            "base.html": (
                "Contexte du coffre local",
                "Atelier pieces, relier piece, point, action et preuve",
                "Droits, roles et gouvernance",
                "Depot local et exports prepares",
            ),
            "_context_banner.html": (
                "Contexte du coffre, du role et de la synchronisation",
                "Prochaine action",
            ),
            "overview.html": (
                "Statut sync a verifier",
                "aucune synchronisation externe",
                "Coffre chiffre/signe a controler",
                "Preuve ou source",
                "Prochaine action",
            ),
            "governance.html": (
                "preuves restent dans quel coffre",
                "Droits croises",
                "Droits limites par role",
                "Raccourcis vers les preuves",
            ),
            "depot.html": (
                "Ce depot reste local",
                "Cette page ne synchronise rien vers un service cloud",
                "A verifier avant toute sync externe",
                "Actions et preuves a suivre",
            ),
            "actions.html": (
                "Pourquoi",
                "Preuve / source",
                "Prochaine action",
                "Prudence diffusion",
            ),
            "pieces.html": (
                "Pieces a demander",
                "Preuves locales a verifier",
                "Action primaire",
                "Prochaine etape",
            ),
            "requests.html": (
                "lecture novice",
                "preuve/source",
                "prochaine action",
                "diffusion",
            ),
            "agcontentieux.html": (
                "Parcours AG contentieux passation",
                "Preuve / source",
                "Restriction / diffusion",
                "Prochaine action",
            ),
        }

        missing: list[str] = []
        for template_name, snippets in expected.items():
            source = _read(WEB_TEMPLATES / template_name)
            for snippet in snippets:
                if snippet not in source:
                    missing.append(f"{template_name}: {snippet!r}")

        self.assertEqual([], missing)

    def test_primary_template_copy_says_coffre_not_vault(self) -> None:
        violations: list[str] = []

        for path in TEMPLATE_TARGETS:
            text = _primary_text(path)
            if VAULT_WORD.search(text):
                violations.append(str(path.relative_to(ROOT)))

        self.assertEqual([], violations)

    def test_templates_with_help_dots_explain_jargon_in_short_titles(self) -> None:
        governance = _read(WEB_TEMPLATES / "governance.html")
        titles = re.findall(r'class="help-dot"\s+title="([^"]+)"', governance)

        self.assertGreaterEqual(len(titles), 5)
        joined = " ".join(titles)
        self.assertIn("Un coffre est l'espace de donnees chiffre d'une copro", joined)
        self.assertIn("Droits limites par role, mandat, theme et duree", joined)
        self.assertIn("preuves attendues", joined)
        self.assertIn("sans copie physique du document", joined)

    def test_static_scope_does_not_target_reserved_document_intake_template(self) -> None:
        self.assertNotIn(EXCLUDED_TEMPLATE, TEMPLATE_TARGETS)
        self.assertTrue(EXCLUDED_TEMPLATE.exists())


if __name__ == "__main__":
    unittest.main()
