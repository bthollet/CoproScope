import unittest
from pathlib import Path


CSS_PATH = (
    Path(__file__).resolve().parents[1]
    / "src"
    / "coproscope"
    / "web"
    / "static"
    / "styles_part_05.css"
)


class ResponsiveShellCssTests(unittest.TestCase):
    def test_sidebar_navigation_stacks_without_horizontal_scroll(self) -> None:
        css = CSS_PATH.read_text(encoding="utf-8")
        responsive = css.split("@media (max-width: 980px)", 1)[1]

        self.assertIn("max-height: none;", responsive)
        self.assertIn("overflow: visible;", responsive)
        self.assertIn("grid-template-columns: repeat(auto-fit, minmax(132px, 1fr));", responsive)
        self.assertIn("display: contents;", responsive)
        self.assertIn("overflow-wrap: anywhere;", responsive)
        self.assertIn("display: none;", responsive)
        self.assertNotIn("max-height: 260px;", responsive)
        self.assertNotIn("overflow-x: auto;", responsive)


if __name__ == "__main__":
    unittest.main()
