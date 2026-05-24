from __future__ import annotations

import importlib.util
import sys
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
TOOL_PATH = REPO_ROOT / "tools" / "check_code_line_limit.py"


def _load_guardrail_module():
    spec = importlib.util.spec_from_file_location("check_code_line_limit", TOOL_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot load guardrail tool from {TOOL_PATH}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


line_limit = _load_guardrail_module()


class CodeLineLimitTests(unittest.TestCase):
    def test_scoped_code_files_stay_under_600_lines(self) -> None:
        violations = line_limit.find_violations(REPO_ROOT)
        formatted = line_limit.format_violations(violations, REPO_ROOT)
        message = (
            "Scoped code files must stay at or below 600 lines.\n"
            f"Scope: {line_limit.scope_summary()}\n"
            f"{formatted}"
        )
        if violations:
            self.fail(message)


if __name__ == "__main__":
    unittest.main()
