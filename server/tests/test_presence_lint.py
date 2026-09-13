from __future__ import annotations

import datetime as dt
import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
TOOL_PATH = REPO_ROOT / "tools" / "presence_lint.py"


def _load_module():
    spec = importlib.util.spec_from_file_location("presence_lint", TOOL_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot load presence lint tool from {TOOL_PATH}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


presence_lint = _load_module()


HEADER = (
    "| Conversation | Roadmap | Chantier | Role | Statut | Ownership | "
    "Worktree / branche | Dernier heartbeat | Expire | Prochain geste | Trace finale |"
)
SEPARATOR = "|---|---|---|---|---|---|---|---|---|---|---|"


def _row(conv: str, status: str, ownership: str, expires: str = "n/a") -> str:
    return (
        f"| `{conv}` | `RM-2026-0001` | `CH-x` | Role | `{status}` | {ownership} | "
        f"local / `main` | 2026-09-01 10:00 +02:00 | {expires} | Geste | Trace |"
    )


def _write(rows: list[str]) -> Path:
    directory = Path(tempfile.mkdtemp())
    path = directory / "presence_agents.md"
    path.write_text(
        "\n".join(["# Presence", "", HEADER, SEPARATOR, *rows, ""]),
        encoding="utf-8",
    )
    return path


class PresenceLintTests(unittest.TestCase):
    def test_parses_only_table_rows(self) -> None:
        path = _write([_row("CONV-1", "EN_COURS", "`server/src/a.py`")])
        rows = presence_lint.parse_presence(path)
        self.assertEqual(len(rows), 1)
        self.assertEqual(presence_lint.status_of(rows[0]), "EN_COURS")

    def test_terminal_status_is_not_active(self) -> None:
        path = _write(
            [
                _row("CONV-1", "EN_COURS", "`server/src/a.py`"),
                _row("CONV-2", "INTEGRE", "`server/src/a.py`"),
            ]
        )
        rows = presence_lint.parse_presence(path)
        self.assertEqual([r.conversation for r in presence_lint.active_rows(rows)], ["`CONV-1`"])

    def test_overlap_detected_between_active_rows(self) -> None:
        path = _write(
            [
                _row("CONV-1", "EN_COURS", "`server/src/a.py`, `docs/x.md`"),
                _row("CONV-2", "BLOQUE", "`server/src/a.py`"),
            ]
        )
        found = presence_lint.overlaps(presence_lint.parse_presence(path))
        self.assertEqual(len(found), 1)
        self.assertEqual(found[0][2], {"server/src/a.py"})

    def test_overlap_ignores_shared_coordination_registers(self) -> None:
        ownership = "`docs/presence_agents.md`, `docs/roadmap_backlog_central.md`"
        path = _write(
            [
                _row("CONV-1", "EN_COURS", ownership),
                _row("CONV-2", "EN_COURS", ownership),
            ]
        )
        self.assertEqual(presence_lint.overlaps(presence_lint.parse_presence(path)), [])

    def test_overlap_ignores_terminal_rows(self) -> None:
        path = _write(
            [
                _row("CONV-1", "EN_COURS", "`server/src/a.py`"),
                _row("CONV-2", "CLOTURE", "`server/src/a.py`"),
            ]
        )
        self.assertEqual(presence_lint.overlaps(presence_lint.parse_presence(path)), [])

    def test_identifiers_are_not_taken_for_paths(self) -> None:
        path = _write([_row("CONV-1", "EN_COURS", "`RM-2026-0001`, `CH-20260101-x`")])
        rows = presence_lint.parse_presence(path)
        self.assertEqual(rows[0].owned, set())

    def test_expired_row_is_reported(self) -> None:
        path = _write(
            [
                _row("CONV-1", "EN_COURS", "`server/src/a.py`", "2026-06-02 09:36 +02:00"),
                _row("CONV-2", "EN_COURS", "`server/src/b.py`", "2027-01-01 09:36 +02:00"),
            ]
        )
        rows = presence_lint.parse_presence(path)
        stale = presence_lint.expired(rows, dt.date(2026, 9, 2))
        self.assertEqual([r.conversation for r in stale], ["`CONV-1`"])

    def test_report_shape_is_serialisable(self) -> None:
        path = _write([_row("CONV-1", "EN_COURS", "`server/src/a.py`")])
        report = presence_lint.build_report(presence_lint.parse_presence(path), dt.date(2026, 9, 2))
        self.assertEqual(report["total"], 1)
        self.assertIn("chevauchements", report)
        self.assertIn("Aucun chevauchement", presence_lint.render(report))


if __name__ == "__main__":
    unittest.main()
