from __future__ import annotations

import argparse
import datetime as dt
import importlib.util
import json
import os
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

try:
    import tomllib
except ModuleNotFoundError:  # pragma: no cover - Python < 3.11 fallback.
    tomllib = None


CANONICAL_HEARTBEAT = "relance-equipe-agile-gouvernail-autonome"
EXPECTED_RRULE = "FREQ=MINUTELY;INTERVAL=5"
CODEX_TOOL_COUNT_WARNING = 20
CODEX_TOOL_MEMORY_WARNING_MB = 1024.0
CODEX_UI_MEMORY_WARNING_MB = 4096.0


@dataclass
class Automation:
    automation_id: str
    kind: str
    status: str
    rrule: str
    path: Path


@dataclass
class CodexProcessHygiene:
    available: bool
    tool_process_count: int = 0
    tool_working_set_mb: float = 0.0
    ui_process_count: int = 0
    ui_working_set_mb: float = 0.0
    stopped_tool_processes: int = 0
    error: str = ""


def load_watchdog():
    path = Path(__file__).with_name("orchestration_watchdog.py")
    spec = importlib.util.spec_from_file_location("orchestration_watchdog", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot load watchdog tool from {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


watchdog = load_watchdog()


def codex_home() -> Path:
    configured = os.environ.get("CODEX_HOME")
    if configured:
        return Path(configured)
    return Path.home() / ".codex"


def parse_toml(path: Path) -> dict[str, object]:
    text = path.read_text(encoding="utf-8")
    if tomllib is not None:
        return tomllib.loads(text)
    values: dict[str, object] = {}
    for line in text.splitlines():
        match = re.match(r'([a-zA-Z_]+)\s*=\s*"([^"]*)"', line)
        if match:
            values[match.group(1)] = match.group(2)
    return values


def read_automations(home: Path) -> list[Automation]:
    root = home / "automations"
    if not root.exists():
        return []
    automations: list[Automation] = []
    for path in sorted(root.glob("*/automation.toml")):
        data = parse_toml(path)
        automations.append(
            Automation(
                automation_id=str(data.get("id", path.parent.name)),
                kind=str(data.get("kind", "")),
                status=str(data.get("status", "")),
                rrule=str(data.get("rrule", "")),
                path=path,
            )
        )
    return automations


def _process_name(process: dict[str, object]) -> str:
    return str(process.get("Name") or "").lower()


def _process_command(process: dict[str, object]) -> str:
    return str(process.get("CommandLine") or "")


def _working_set_mb(processes: list[dict[str, object]]) -> float:
    total = 0.0
    for process in processes:
        try:
            total += float(process.get("WorkingSetSize") or 0)
        except (TypeError, ValueError):
            pass
    return round(total / (1024 * 1024), 1)


def is_codex_tool_process(process: dict[str, object]) -> bool:
    name = _process_name(process)
    command = _process_command(process)
    return (
        name == "node_repl.exe"
        and "OpenAI\\Codex" in command
    ) or (
        name == "codex.exe"
        and "app-server --listen stdio://" in command
    )


def is_codex_ui_process(process: dict[str, object]) -> bool:
    command = _process_command(process)
    return _process_name(process) == "codex.exe" and (
        "WindowsApps\\OpenAI.Codex" in command
        or "Program Files\\WindowsApps\\OpenAI.Codex" in command
        or "OpenAI.Codex_" in command
    )


def summarize_codex_process_hygiene(processes: list[dict[str, object]]) -> CodexProcessHygiene:
    tool_processes = [process for process in processes if is_codex_tool_process(process)]
    ui_processes = [
        process
        for process in processes
        if is_codex_ui_process(process)
    ]
    return CodexProcessHygiene(
        available=True,
        tool_process_count=len(tool_processes),
        tool_working_set_mb=_working_set_mb(tool_processes),
        ui_process_count=len(ui_processes),
        ui_working_set_mb=_working_set_mb(ui_processes),
    )


def codex_hygiene_needs_cleanup(
    hygiene: CodexProcessHygiene,
    count_warning: int,
    memory_warning_mb: float,
) -> bool:
    return bool(
        hygiene.available
        and (
            hygiene.tool_process_count >= count_warning
            or hygiene.tool_working_set_mb >= memory_warning_mb
        )
    )


def _read_windows_codex_processes() -> list[dict[str, object]]:
    script = r"""
$ErrorActionPreference = 'Stop'
Get-CimInstance Win32_Process |
  Where-Object {
    $_.Name -in @('Codex.exe','codex.exe','node_repl.exe') -or
    $_.CommandLine -match 'OpenAI\\Codex|WindowsApps\\OpenAI\.Codex'
  } |
  Select-Object ProcessId,Name,WorkingSetSize,CommandLine |
  ConvertTo-Json -Compress
"""
    result = subprocess.run(
        ["powershell.exe", "-NoProfile", "-NonInteractive", "-Command", script],
        capture_output=True,
        text=True,
        timeout=15,
        check=True,
    )
    text = result.stdout.strip()
    if not text:
        return []
    data = json.loads(text)
    if isinstance(data, dict):
        return [data]
    if isinstance(data, list):
        return [item for item in data if isinstance(item, dict)]
    return []


def _stop_windows_processes(processes: list[dict[str, object]]) -> int:
    pids: list[int] = []
    for process in processes:
        try:
            pids.append(int(process.get("ProcessId") or 0))
        except (TypeError, ValueError):
            pass
    pids = [pid for pid in pids if pid > 0]
    if not pids:
        return 0
    ids = ",".join(str(pid) for pid in sorted(set(pids)))
    script = f"Stop-Process -Id {ids} -Force -ErrorAction SilentlyContinue"
    subprocess.run(
        ["powershell.exe", "-NoProfile", "-NonInteractive", "-Command", script],
        capture_output=True,
        text=True,
        timeout=15,
        check=False,
    )
    return len(set(pids))


def check_codex_process_hygiene(
    cleanup: bool,
    count_warning: int,
    memory_warning_mb: float,
) -> CodexProcessHygiene:
    if os.name != "nt":
        return CodexProcessHygiene(available=False, error="unsupported on non-Windows")
    try:
        processes = _read_windows_codex_processes()
        hygiene = summarize_codex_process_hygiene(processes)
        if cleanup and codex_hygiene_needs_cleanup(hygiene, count_warning, memory_warning_mb):
            tool_processes = [process for process in processes if is_codex_tool_process(process)]
            stopped = _stop_windows_processes(tool_processes)
            processes = _read_windows_codex_processes()
            hygiene = summarize_codex_process_hygiene(processes)
            hygiene.stopped_tool_processes = stopped
        return hygiene
    except Exception as exc:  # pragma: no cover - local environment dependent.
        return CodexProcessHygiene(available=False, error=str(exc))


def trace_state(
    watch_at: dt.datetime | None,
    watch_line: str | None,
    decisions: list[object],
    blocked: list[object],
    stale: list[object],
    expired: list[object],
    now: dt.datetime,
    stale_minutes: int,
    quiet_grace_minutes: int,
) -> str:
    if watch_at is None:
        return "MISSING"
    if watchdog.is_recent(watch_at, now, stale_minutes):
        return "OK"
    age = now - watch_at
    quiet_matches = watchdog.quiet_trace_matches_current_state(
        watch_line,
        decisions,
        blocked,
        stale,
        expired,
    )
    if quiet_matches and age <= dt.timedelta(minutes=quiet_grace_minutes):
        return "QUIET"
    return "STALE"


def recovery_prompt(reason: str, heartbeat: Automation | None, duplicates: list[Automation]) -> str:
    duplicate_ids = ", ".join(item.automation_id for item in duplicates) or "aucun"
    current_status = "absente" if heartbeat is None else f"{heartbeat.status} / {heartbeat.rrule}"
    return "\n".join(
        [
            "Relance superviseur externe CoproScope.",
            f"Raison: {reason}. Heartbeat canonique: {current_status}. Doublons actifs: {duplicate_ids}.",
            "Lire AGENTS.md, docs/orchestration_watchdog.md, docs/presence_agents.md et docs/roadmap_backlog_central.md.",
            "Reparer ou recadrer l'automation relance-equipe-agile-gouvernail-autonome en ACTIVE, FREQ=MINUTELY;INTERVAL=5, mode surveillance/reprise.",
            "Le heartbeat doit laisser une trace persistante a chaque passage, meme en DONT_NOTIFY.",
            "Ne pas dupliquer de roles vivants; si un arbitrage ou blocage existe, le remonter avant tout dispatch.",
            "Appliquer docs/strategie_equipes_multi_agents.md avant tout nouveau dispatch: routeur d'equipe-type, puis un seul CH-* et owners uniques.",
            "Relancer seulement les roles manquants, idle, bloques ou expires d'un CH-* deja declare; ne jamais choisir un nouveau ORD-* quand EN_ATTENTE_USER ou incident doublon est present.",
            "Si aucun P0 n'est actionnable ou autorise, tracer NO_ORD_ACTIONNABLE ou HEARTBEAT_CHECKIN avec la raison exacte.",
            "Verifier l'hygiene processus Codex via .\\tools\\orchestration-supervise.cmd --cleanup-codex-tool-processes si les outils node_repl/stdio s'accumulent.",
            "Interdits: instances privees, documents bruts, OCR/logs, exports bruts, secrets, serveurs non reserves, push GitHub, RM-2026-0017, ORD-P0-990.",
        ]
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Supervise the CoproScope orchestration heartbeat.")
    parser.add_argument("--strict", action="store_true", help="Exit 2 when recovery is required.")
    parser.add_argument("--emit-recovery-prompt", action="store_true")
    parser.add_argument("--heartbeat-id", default=CANONICAL_HEARTBEAT)
    parser.add_argument("--stale-minutes", type=int, default=20)
    parser.add_argument("--quiet-grace-minutes", type=int, default=30)
    parser.add_argument("--skip-codex-hygiene", action="store_true")
    parser.add_argument("--cleanup-codex-tool-processes", action="store_true")
    parser.add_argument("--codex-tool-count-warning", type=int, default=CODEX_TOOL_COUNT_WARNING)
    parser.add_argument("--codex-tool-memory-warning-mb", type=float, default=CODEX_TOOL_MEMORY_WARNING_MB)
    parser.add_argument("--codex-ui-memory-warning-mb", type=float, default=CODEX_UI_MEMORY_WARNING_MB)
    args = parser.parse_args()

    root = watchdog.repo_root()
    presence_path = root / "docs" / "presence_agents.md"
    rows = watchdog.parse_presence(presence_path)
    now = dt.datetime.now(dt.timezone(dt.timedelta(hours=2)))

    running = [row for row in rows if watchdog.status_of(row) == "EN_COURS"]
    decisions = [row for row in rows if watchdog.status_of(row) == "EN_ATTENTE_USER"]
    blocked = [row for row in rows if watchdog.status_of(row) == "BLOQUE"]
    stale = []
    expired = []
    for row in running:
        heartbeat = watchdog.parse_time(row.heartbeat)
        expire = watchdog.parse_time(row.expire)
        if not watchdog.is_recent(heartbeat, now, args.stale_minutes):
            stale.append(row)
        if expire and now > expire:
            expired.append(row)

    watch_at, watch_line = watchdog.latest_watchdog_trace(presence_path)
    state = trace_state(
        watch_at,
        watch_line,
        decisions,
        blocked,
        stale,
        expired,
        now,
        args.stale_minutes,
        args.quiet_grace_minutes,
    )

    automations = read_automations(codex_home())
    heartbeat = next((item for item in automations if item.automation_id == args.heartbeat_id), None)
    active_heartbeats = [item for item in automations if item.kind == "heartbeat" and item.status == "ACTIVE"]
    duplicates = [item for item in active_heartbeats if item.automation_id != args.heartbeat_id]

    heartbeat_ok = bool(heartbeat and heartbeat.status == "ACTIVE" and heartbeat.rrule == EXPECTED_RRULE)
    trace_ok = state in {"OK", "QUIET"}
    hygiene = (
        CodexProcessHygiene(available=False, error="skipped")
        if args.skip_codex_hygiene
        else check_codex_process_hygiene(
            args.cleanup_codex_tool_processes,
            args.codex_tool_count_warning,
            args.codex_tool_memory_warning_mb,
        )
    )
    hygiene_issue = codex_hygiene_needs_cleanup(
        hygiene,
        args.codex_tool_count_warning,
        args.codex_tool_memory_warning_mb,
    )
    recovery_required = not heartbeat_ok or not trace_ok or bool(duplicates) or hygiene_issue

    reasons: list[str] = []
    if not heartbeat_ok:
        reasons.append("heartbeat canonique absent, pause ou cadence incorrecte")
    if not trace_ok:
        reasons.append(f"trace orchestrateur {state}")
    if duplicates:
        reasons.append("doublon heartbeat actif")
    if hygiene_issue:
        reasons.append("processus outils Codex accumules")
    reason = "; ".join(reasons) or "etat supervise sain"

    print("CoproScope orchestration supervisor")
    print(f"Repository:          {root}")
    print(f"Canonical heartbeat: {args.heartbeat_id}")
    print(f"Expected rrule:      {EXPECTED_RRULE}")
    print(f"Automation state:    {'OK' if heartbeat_ok else 'RECOVER'}")
    if heartbeat:
        print(f"  {heartbeat.status} / {heartbeat.rrule} / {heartbeat.path}")
    else:
        print("  missing")
    print(f"Trace state:         {state}")
    if watch_at:
        print(f"  last {watch_at.strftime('%Y-%m-%d %H:%M %z')} ({now - watch_at})")
    print(f"Active duplicates:   {', '.join(item.automation_id for item in duplicates) or 'none'}")
    if hygiene.available:
        hygiene_state = "RECOVER" if hygiene_issue else "OK"
        ui_state = "HIGH" if hygiene.ui_working_set_mb >= args.codex_ui_memory_warning_mb else "OK"
        print(f"Codex tool hygiene:  {hygiene_state}")
        print(
            "  tools "
            f"{hygiene.tool_process_count} proc / {hygiene.tool_working_set_mb:.1f} MB"
        )
        if hygiene.stopped_tool_processes:
            print(f"  stopped {hygiene.stopped_tool_processes} tool processes")
        print(
            "  ui "
            f"{hygiene.ui_process_count} proc / {hygiene.ui_working_set_mb:.1f} MB / {ui_state}"
        )
    else:
        print(f"Codex tool hygiene:  SKIPPED ({hygiene.error})")
    print(f"Decision:            {'RECOVER' if recovery_required else 'OK'}")

    if recovery_required or args.emit_recovery_prompt:
        print("")
        print("--- RECOVERY PROMPT ---")
        print(recovery_prompt(reason, heartbeat, duplicates))

    return 2 if args.strict and recovery_required else 0


if __name__ == "__main__":
    sys.exit(main())
