from __future__ import annotations

import datetime as dt
import importlib.util
import sys
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
TOOL_PATH = REPO_ROOT / "tools" / "orchestration_supervisor.py"


def _load_supervisor_module():
    spec = importlib.util.spec_from_file_location("orchestration_supervisor", TOOL_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot load supervisor tool from {TOOL_PATH}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


supervisor = _load_supervisor_module()
watchdog = supervisor.watchdog


def _row(conv_id: str, status: str) -> object:
    return watchdog.Conversation(
        f"`{conv_id}`",
        "`RM-2026-0006`",
        "`CH-20260525-000000-RM-2026-0006-test`",
        "Role test",
        f"`{status}`",
        "Lecture seule",
        "repo principal",
        "2026-05-25 10:00 +0200",
        "n/a",
        "Prochain geste test",
        "Trace test",
        1,
    )


def _process(name: str, command: str, mb: int) -> dict[str, object]:
    return {
        "Name": name,
        "CommandLine": command,
        "WorkingSetSize": mb * 1024 * 1024,
    }


def _automation(automation_id: str, kind: str, status: str) -> object:
    return supervisor.Automation(
        automation_id=automation_id,
        kind=kind,
        status=status,
        rrule="FREQ=MINUTELY;INTERVAL=5",
        path=Path("automation.toml"),
    )


class OrchestrationSupervisorTests(unittest.TestCase):
    def test_optional_policy_allows_paused_canonical_heartbeat(self) -> None:
        automations = [
            _automation(supervisor.CANONICAL_HEARTBEAT, "heartbeat", "PAUSED"),
            _automation("reveil-borne-ch-1234", "heartbeat", "ACTIVE"),
        ]

        self.assertEqual(
            supervisor.active_legacy_heartbeats(automations, supervisor.CANONICAL_HEARTBEAT),
            [],
        )

    def test_optional_policy_flags_active_legacy_heartbeat(self) -> None:
        automations = [
            _automation(supervisor.CANONICAL_HEARTBEAT, "heartbeat", "ACTIVE"),
            _automation("relance-worker-drive", "heartbeat", "ACTIVE"),
        ]

        active = supervisor.active_legacy_heartbeats(automations, supervisor.CANONICAL_HEARTBEAT)

        self.assertEqual([item.automation_id for item in active], [
            supervisor.CANONICAL_HEARTBEAT,
            "relance-worker-drive",
        ])

    def test_quiet_trace_has_a_finite_grace_period(self) -> None:
        now = dt.datetime(2026, 5, 25, 11, 0, tzinfo=dt.timezone(dt.timedelta(hours=2)))
        trace = (
            "| 2026-05-25 10:35 +02:00 | `relance-equipe-agile-gouvernail-autonome` "
            "| `HEARTBEAT_POST_RESPONSIVE_STATIONNEMENT` | A remonter: arbitrage "
            "`CONV-2026-1641`. Aucun role artificiel ouvert. |"
        )

        state = supervisor.trace_state(
            now - dt.timedelta(minutes=25),
            trace,
            decisions=[_row("CONV-2026-1641", "EN_ATTENTE_USER")],
            blocked=[],
            stale=[],
            expired=[],
            now=now,
            stale_minutes=20,
            quiet_grace_minutes=30,
        )

        self.assertEqual(state, "QUIET")

    def test_quiet_trace_eventually_becomes_stale(self) -> None:
        now = dt.datetime(2026, 5, 25, 11, 20, tzinfo=dt.timezone(dt.timedelta(hours=2)))
        trace = (
            "| 2026-05-25 10:35 +02:00 | `relance-equipe-agile-gouvernail-autonome` "
            "| `HEARTBEAT_POST_RESPONSIVE_STATIONNEMENT` | A remonter: arbitrage "
            "`CONV-2026-1641`. Aucun role artificiel ouvert. |"
        )

        state = supervisor.trace_state(
            now - dt.timedelta(minutes=45),
            trace,
            decisions=[_row("CONV-2026-1641", "EN_ATTENTE_USER")],
            blocked=[],
            stale=[],
            expired=[],
            now=now,
            stale_minutes=20,
            quiet_grace_minutes=30,
        )

        self.assertEqual(state, "STALE")

    def test_codex_hygiene_counts_tool_process_bloat(self) -> None:
        hygiene = supervisor.summarize_codex_process_hygiene(
            [
                _process("node_repl.exe", r"C:\Users\brice\AppData\Local\OpenAI\Codex\bin\node_repl.exe", 18),
                _process("codex.exe", r"C:\Users\brice\AppData\Local\OpenAI\Codex\bin\codex.exe app-server --listen stdio://", 31),
                _process("Codex.exe", r"C:\Program Files\WindowsApps\OpenAI.Codex_1\app\Codex.exe --type=renderer", 900),
                _process("python.exe", r"C:\Users\brice\CoproScope\server\.venv\Scripts\python.exe", 80),
            ]
        )

        self.assertEqual(hygiene.tool_process_count, 2)
        self.assertEqual(hygiene.tool_working_set_mb, 49.0)
        self.assertEqual(hygiene.ui_process_count, 1)
        self.assertEqual(hygiene.ui_working_set_mb, 900.0)

    def test_codex_hygiene_threshold_ignores_small_tool_counts(self) -> None:
        hygiene = supervisor.CodexProcessHygiene(
            available=True,
            tool_process_count=2,
            tool_working_set_mb=49.0,
        )

        self.assertFalse(
            supervisor.codex_hygiene_needs_cleanup(
                hygiene,
                count_warning=20,
                memory_warning_mb=1024.0,
            )
        )

        hygiene.tool_process_count = 20
        self.assertTrue(
            supervisor.codex_hygiene_needs_cleanup(
                hygiene,
                count_warning=20,
                memory_warning_mb=1024.0,
            )
        )


if __name__ == "__main__":
    unittest.main()
