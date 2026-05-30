from __future__ import annotations

import ast
import re
import unittest
from html import unescape
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
WEB = ROOT / "server" / "src" / "coproscope" / "web"
DOC = ROOT / "docs" / "archive" / "recettes_ux" / "qa_post_279_tests.md"

TEMPLATE_TARGETS = (
    WEB / "templates" / "governance.html",
    WEB / "templates" / "_context_banner.html",
)
PYTHON_TEXT_TARGETS = (
    WEB / "governance.py",
    WEB / "context_banner.py",
)

VAULT_WORD = re.compile(r"(?<![A-Za-z0-9_])vault(?![A-Za-z0-9_])", re.I)
JINJA_COMMENT = re.compile(r"\{#.*?#\}", re.S)
JINJA_OUTPUT = re.compile(r"\{\{.*?\}\}", re.S)
JINJA_BLOCK = re.compile(r"\{%.*?%\}", re.S)
HTML_TAG = re.compile(r"<[^>]+>")
VISIBLE_ATTR = re.compile(r"\b(?:aria-label|title|alt|placeholder)=[\"']([^\"']*)[\"']", re.I)


def _visible_template_text(path: Path) -> str:
    source = path.read_text(encoding="utf-8")
    attrs = VISIBLE_ATTR.findall(source)
    text = JINJA_COMMENT.sub(" ", source)
    text = JINJA_OUTPUT.sub(" ", text)
    text = JINJA_BLOCK.sub(" ", text)
    text = HTML_TAG.sub(" ", text)
    return unescape(" ".join([text, *attrs]))


def _attach_parents(tree: ast.AST) -> None:
    for parent in ast.walk(tree):
        for child in ast.iter_child_nodes(parent):
            child.parent = parent  # type: ignore[attr-defined]


def _is_technical_mapping_key(node: ast.Constant) -> bool:
    parent = getattr(node, "parent", None)
    if isinstance(parent, ast.Dict) and node in parent.keys:
        return True
    return (
        isinstance(parent, ast.Call)
        and bool(parent.args)
        and parent.args[0] is node
        and isinstance(parent.func, ast.Attribute)
        and parent.func.attr == "get"
    )


def _python_visible_string_violations(path: Path) -> list[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    _attach_parents(tree)
    violations: list[str] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Constant) or not isinstance(node.value, str):
            continue
        if not VAULT_WORD.search(node.value):
            continue
        if _is_technical_mapping_key(node):
            continue
        violations.append(f"{path.relative_to(ROOT)}:{node.lineno}: {node.value!r}")
    return violations


class UiNoJargonPrimaryTests(unittest.TestCase):
    def test_governance_and_context_banner_visible_text_say_coffre_not_vault(self) -> None:
        violations: list[str] = []

        for path in TEMPLATE_TARGETS:
            visible_text = _visible_template_text(path)
            if VAULT_WORD.search(visible_text):
                violations.append(f"{path.relative_to(ROOT)}: visible template text contains 'vault'")

        for path in PYTHON_TEXT_TARGETS:
            violations.extend(_python_visible_string_violations(path))

        self.assertEqual([], violations)

    def test_technical_vault_exceptions_are_documented(self) -> None:
        doc = DOC.read_text(encoding="utf-8")

        self.assertIn("Texte visible utilisateur: dire `coffre`", doc)
        self.assertIn("config technique `settings.vault`", doc)
        self.assertIn("identifiants de test `vault-*`", doc)
        self.assertIn("permissions techniques `vault.read.*`", doc)
        self.assertIn("docs techniques comme `docs/vault_format.md`", doc)


if __name__ == "__main__":
    unittest.main()
