import unittest
import re
from pathlib import Path


CSS_PATH = (
    Path(__file__).resolve().parents[1]
    / "src"
    / "coproscope"
    / "web"
    / "static"
    / "styles_part_05.css"
)
MOBILE_CSS_PATH = CSS_PATH.with_name("styles_part_06.css")


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

    def test_narrow_shell_keeps_active_navigation_compact(self) -> None:
        css = MOBILE_CSS_PATH.read_text(encoding="utf-8")
        responsive = css.split("@media (max-width: 720px)", 1)[1].split("/* Cycle 2 FRONT", 1)[0]
        nav_block = re.search(r"\.cs-sidebar \.nav \{(?P<body>.*?)\}", responsive, flags=re.DOTALL)

        self.assertIn("max-height: 46px;", responsive)
        self.assertIn(".cs-sidebar .nav:focus-within", responsive)
        self.assertIn(".cs-sidebar .nav a.active", responsive)
        self.assertIn("order: -1;", responsive)
        self.assertIsNotNone(nav_block)
        self.assertNotIn("overflow-x: auto;", nav_block.group("body"))


if __name__ == "__main__":
    unittest.main()
