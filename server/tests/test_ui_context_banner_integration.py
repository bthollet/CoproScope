from __future__ import annotations

import unittest
from html import unescape
from pathlib import Path
from types import SimpleNamespace


ROOT = Path(__file__).resolve().parents[2]
TEMPLATE_DIR = ROOT / "server" / "src" / "coproscope" / "web" / "templates"
BASE_HTML = TEMPLATE_DIR / "base.html"
STYLES_CSS = ROOT / "server" / "src" / "coproscope" / "web" / "static" / "styles.css"
DOC = ROOT / "docs" / "archive" / "notes_integration" / "integration_bandeau_contexte.md"


class UiContextBannerIntegrationTests(unittest.TestCase):
    def _render_base(self, **extra: object) -> str:
        try:
            from jinja2 import Environment, FileSystemLoader, StrictUndefined, select_autoescape  # type: ignore
        except ImportError as exc:  # pragma: no cover - optional UI dependency
            self.skipTest(f"jinja2 is not installed: {exc}")

        env = Environment(
            loader=FileSystemLoader(str(TEMPLATE_DIR)),
            autoescape=select_autoescape(("html", "xml")),
            undefined=StrictUndefined,
        )
        env.globals["url_for"] = lambda name, **kwargs: f"/static/{kwargs.get('path', '')}"

        context: dict[str, object] = {
            "model": SimpleNamespace(instance=SimpleNamespace(name="Residence Test", year=2026, id="copro-test")),
            "page": "overview",
            "ui_token_query": "",
            "ui_token_param": "",
        }
        context.update(extra)
        return unescape(env.get_template("base.html").render(**context))

    def _banner(self) -> dict[str, object]:
        return {
            "tone": "review",
            "coffre_label": "Residence Test",
            "novice_text": "Confirmez le coffre, le role et la sync avant de partager.",
            "next_action_href": "/gouvernance",
            "next_action": "Confirmer le role avant de continuer.",
            "items": [
                {
                    "label": "Coffre courant",
                    "value": "Residence Test",
                    "help": "Identifiant: copro-test",
                    "tone": "ok",
                },
                {
                    "label": "Role",
                    "value": "Role a confirmer",
                    "help": "confirmez qui utilise l'ecran",
                    "tone": "review",
                },
                {
                    "label": "Sync",
                    "value": "Sync non branchee",
                    "help": "aucun dossier sync n'est declare",
                    "tone": "review",
                },
            ],
        }

    def test_base_includes_context_banner_only_when_context_exists(self) -> None:
        html_without_banner = self._render_base()

        self.assertNotIn('class="context-banner', html_without_banner)
        self.assertNotIn("Contexte actif", html_without_banner)
        self.assertIn('<main id="contenu" tabindex="-1"', html_without_banner)

        html_with_banner = self._render_base(context_banner=self._banner())

        self.assertIn('class="context-banner context-banner--review"', html_with_banner)
        self.assertIn('aria-label="Contexte actif"', html_with_banner)
        self.assertIn("Residence Test", html_with_banner)
        self.assertIn("Voir le contexte", html_with_banner)
        self.assertNotIn("Role a confirmer", html_with_banner)
        self.assertNotIn("Sync non branchee", html_with_banner)
        self.assertNotIn("Prochaine action", html_with_banner)

    def test_base_uses_partial_without_route_or_viewmodel_contract(self) -> None:
        source = BASE_HTML.read_text(encoding="utf-8")

        self.assertIn('{% if context_banner is defined and context_banner %}', source)
        self.assertIn('{% include "_context_banner.html" %}', source)
        self.assertLess(source.index('{% include "_context_banner.html" %}'), source.index('<main id="contenu"'))

    def test_context_banner_styles_are_accessible_and_responsive(self) -> None:
        css = STYLES_CSS.read_text(encoding="utf-8")

        self.assertIn(".context-banner", css)
        self.assertIn(".context-banner--ok", css)
        self.assertIn(".context-banner--review", css)
        self.assertIn(".context-banner--risk", css)
        self.assertIn(".context-banner__link", css)
        self.assertIn("text-decoration: underline", css)
        self.assertIn("@media (max-width: 980px)", css)
        self.assertIn(".context-banner__line", css)

    def test_document_records_minimal_integration_contract(self) -> None:
        text = DOC.read_text(encoding="utf-8")

        self.assertIn("base.html", text)
        self.assertIn("_context_banner.html", text)
        self.assertIn("context_banner", text)
        self.assertIn("sans modifier app.py ni viewmodel.py", text)
        self.assertIn("n'affichent aucun bandeau", text)


if __name__ == "__main__":
    unittest.main()
