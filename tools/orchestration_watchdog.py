from __future__ import annotations

import argparse
import datetime as dt
import re
import sys
from dataclasses import dataclass
from pathlib import Path


ACTIVE_STATUSES = {"A_LANCER", "EN_COURS", "EN_ATTENTE_USER", "BLOQUE", "PRET_A_INTEGRER"}
TERMINAL_STATUSES = {"INTEGRE", "CLOTURE", "ABANDONNE", "EXPIRE"}
WATCHDOG_ID = "relance-equipe-agile-gouvernail-autonome"
ORCHESTRATION_TRACE_MARKERS = (
    "POINT_REPRISE_",
    "ROUTAGE_EQUIPE",
    "BOT_START",
    "BOT-START",
    "BOT_END",
    "BOT-END",
    "REVISION_START_",
    "REVISION_END_",
    "REVISION_VERIF_",
    "INTEGRATE_",
    "NO_ORD_ACTIONNABLE",
    "HEARTBEAT_",
    "UXUI-DONE",
    "AGILE-DONE",
)
AGILE_COMPOSITION_PROMPT = (
    "Composition agile canonique: coordinateur-scribe, designer/facilitateur, "
    "utilisateur novice, dev front, dev back/viewmodel, QA et, si le budget de "
    "threads le permet, testeur expert metier juridique + compta + process "
    "chantier + syndic. Si aucun thread n'est disponible, QA et coordinateur "
    "reprennent explicitement cette checklist."
)
TEAM_ROUTER_DOC = "docs/strategie_equipes_multi_agents.md"


@dataclass(frozen=True)
class TeamRoute:
    key: str
    label: str
    protocol: str
    orchestration: str
    roles: str
    gate: str


@dataclass
class Conversation:
    conversation: str
    roadmap: str
    chantier: str
    role: str
    status: str
    ownership: str
    worktree: str
    heartbeat: str
    expire: str
    next_step: str
    trace: str
    line_no: int

    @property
    def text(self) -> str:
        return " | ".join(
            [
                self.conversation,
                self.roadmap,
                self.chantier,
                self.role,
                self.status,
                self.next_step,
                self.trace,
            ]
        )

    @property
    def conv_id(self) -> str:
        return first_code(self.conversation)

    @property
    def ch_id(self) -> str:
        return first_code(self.chantier)


@dataclass
class OrdItem:
    order: str
    chunk: str
    loop: str
    rms: str
    next_task: str
    gate: str
    line_no: int


TEAM_ROUTES = {
    "INCIDENT_STATIONNEMENT": TeamRoute(
        "INCIDENT_STATIONNEMENT",
        "incident, arbitrage ou blocage",
        TEAM_ROUTER_DOC,
        "monitor-only: check-in persistant, aucun nouveau CH-* ni ORD-*",
        "coordinateur-scribe + superviseur/watchdog",
        "remonter l'arbitrage ou le blocage avant tout dispatch",
    ),
    "FANIN_CONSOLIDATION": TeamRoute(
        "FANIN_CONSOLIDATION",
        "retours concurrents ou tardifs",
        TEAM_ROUTER_DOC,
        "fan-in: collecter par angle, dedoublonner, conserver les contradictions",
        "coordinateur-scribe + QA/privacy en lecture si utile",
        "un seul prochain dispatch propose apres synthese",
    ),
    "RECHERCHE_METIER": TeamRoute(
        "RECHERCHE_METIER",
        "recherche ou challenge metier sans dev",
        TEAM_ROUTER_DOC,
        "fan-out/fan-in borne par angles metier",
        "juridique/syndic, compta, travaux/process, CS/usage, privacy/QA novice",
        "sortie fait -> preuve -> regle/process -> action; aucun code",
    ),
    "UXUI_RECHERCHE": TeamRoute(
        "UXUI_RECHERCHE",
        "recherche UX/UI visuelle sans dev",
        "docs/protocole_equipe_ux_ui_recherche.md",
        "divergence puis convergence sur images candidates et decisions",
        "orchestrateur UX/UI, chercheur utilisateur, architecte UX, designer visuel, testeurs metier et novice",
        "marqueur UXUI-DONE; aucune modification code",
    ),
    "AGILE_UI_PRODUIT": TeamRoute(
        "AGILE_UI_PRODUIT",
        "delivery UI produit",
        "docs/protocole_equipe_agile_agents.md",
        "pipeline decale N-1/N/N+1",
        "coordinateur, designer, novice, dev front, dev back/viewmodel, QA, expert metier si possible",
        "UI reelle, visuel IA bitmap plein ecran, blueprint, GO novice avant dev",
    ),
    "BACKEND_DOMAINE": TeamRoute(
        "BACKEND_DOMAINE",
        "backend, data, vault, sync ou extracteurs",
        TEAM_ROUTER_DOC,
        "hub-and-spoke: un owner code unique, experts en lecture",
        "coordinateur, owner backend/data, expert metier, QA privacy/regression, integration lead si besoin",
        "contrat de donnees et tests cibles avant integration",
    ),
    "RECETTE_LIVE_QA": TeamRoute(
        "RECETTE_LIVE_QA",
        "recette navigateur ou serveur visible reserve",
        TEAM_ROUTER_DOC,
        "serie stricte: serveur reserve, checks, captures, verdict",
        "QA live, novice, designer/readiness, coordinateur; dev en lecture",
        "port, instance et token reserves; aucun serveur non reserve",
    ),
    "INTEGRATION_RELEASE": TeamRoute(
        "INTEGRATION_RELEASE",
        "integration ou release",
        TEAM_ROUTER_DOC,
        "serie stricte: une branche ou un worktree a la fois",
        "coordinateur integration, QA regression, owners d'origine consultes",
        "diff relu et tests relances avant statut INTEGRE",
    ),
    "DOCTRINE_SIDEQUEST": TeamRoute(
        "DOCTRINE_SIDEQUEST",
        "doctrine ou cadrage transverse",
        TEAM_ROUTER_DOC,
        "travail documentaire borne hors chemin critique",
        "coordinateur doctrine ou sub-agent docs",
        "aucun code applicatif sauf demande explicite",
    ),
}


def first_code(value: str) -> str:
    match = re.search(r"`([^`]+)`", value)
    return match.group(1) if match else clean(value)


def clean(value: str) -> str:
    return re.sub(r"\s+", " ", value.replace("`", "")).strip()


def split_md_row(line: str) -> list[str]:
    return [part.strip() for part in line.strip().strip("|").split("|")]


def repo_root() -> Path:
    current = Path.cwd()
    for candidate in [current, *current.parents]:
        if (candidate / "docs" / "presence_agents.md").exists():
            return candidate
    raise SystemExit("Run from the CoproScope product repository.")


def parse_presence(path: Path) -> list[Conversation]:
    lines = path.read_text(encoding="utf-8").splitlines()
    rows: list[Conversation] = []
    in_table = False
    for line_no, line in enumerate(lines, start=1):
        if line.startswith("| Conversation | Roadmap | Chantier |"):
            in_table = True
            continue
        if not in_table:
            continue
        if line.startswith("|---"):
            continue
        if line.startswith("## ") or not line.strip():
            break
        if not line.lstrip().startswith("|"):
            continue
        parts = split_md_row(line)
        if len(parts) < 11:
            continue
        rows.append(Conversation(*parts[:11], line_no=line_no))
    return rows


def parse_ord(path: Path) -> list[OrdItem]:
    lines = path.read_text(encoding="utf-8").splitlines()
    rows: list[OrdItem] = []
    in_ord = False
    for line_no, line in enumerate(lines, start=1):
        if line.startswith("## File canonique d'execution"):
            in_ord = True
            continue
        if in_ord and line.startswith("## ") and not line.startswith("## File"):
            break
        if not in_ord or not line.lstrip().startswith("| `ORD-"):
            continue
        parts = split_md_row(line)
        if len(parts) < 6:
            continue
        rows.append(OrdItem(*parts[:6], line_no=line_no))
    return rows


def parse_time(value: str) -> dt.datetime | None:
    value = clean(value)
    if not value or value.lower() == "n/a":
        return None
    for fmt in ("%Y-%m-%d %H:%M %z", "%Y-%m-%d %H:%M:%S %z"):
        try:
            return dt.datetime.strptime(value, fmt)
        except ValueError:
            pass
    return None


def status_of(row: Conversation) -> str:
    return first_code(row.status)


def ord_code(text: str) -> str | None:
    match = re.search(r"ORD-P\d-\d{3}", text)
    return match.group(0) if match else None


def _has_any(text: str, words: tuple[str, ...]) -> bool:
    return any(word in text for word in words)


def route_for(team: str, candidate: OrdItem | None) -> TeamRoute:
    if team == "uxui":
        return TEAM_ROUTES["UXUI_RECHERCHE"]
    if team == "agile":
        return TEAM_ROUTES["AGILE_UI_PRODUIT"]
    if candidate is None:
        return TEAM_ROUTES["DOCTRINE_SIDEQUEST"]

    text = clean(
        " ".join(
            [
                candidate.order,
                candidate.chunk,
                candidate.loop,
                candidate.rms,
                candidate.next_task,
                candidate.gate,
            ]
        )
    ).lower()
    if _has_any(text, ("recette", "navigateur", "captures", "desktop", "tablette", "mobile", "8788")):
        return TEAM_ROUTES["RECETTE_LIVE_QA"]
    if _has_any(text, ("integrer", "integration", "worktree", "branche", "pret a integrer", "release")):
        return TEAM_ROUTES["INTEGRATION_RELEASE"]
    if _has_any(text, ("ux/ui", "recherche ux", "images candidates", "parcours", "wireflow")) and not _has_any(
        text, ("route", "template", "css", "dev")
    ):
        return TEAM_ROUTES["UXUI_RECHERCHE"]
    if _has_any(text, ("veille", "challenge", "cadrage", "juridique", "syndic", "shs", "sources officielles")) and not _has_any(
        text, ("implementer", "route", "template", "css")
    ):
        return TEAM_ROUTES["RECHERCHE_METIER"]
    if _has_any(
        text,
        (
            "db",
            "vault",
            "schema",
            "read model",
            "projection",
            "sync",
            "drive",
            "extract",
            "ocr",
            "recorder",
            "taxonomie",
            "api",
            "contrat",
        ),
    ):
        return TEAM_ROUTES["BACKEND_DOMAINE"]
    if _has_any(text, ("protocole", "agents", "watchdog", "gouvernail", "doctrine")):
        return TEAM_ROUTES["DOCTRINE_SIDEQUEST"]
    return TEAM_ROUTES["AGILE_UI_PRODUIT"]


def latest_watchdog_trace(path: Path) -> tuple[dt.datetime | None, str | None]:
    latest_at: dt.datetime | None = None
    latest_line: str | None = None
    for line in path.read_text(encoding="utf-8").splitlines():
        if WATCHDOG_ID not in line and not any(marker in line for marker in ORCHESTRATION_TRACE_MARKERS):
            continue
        parts = split_md_row(line)
        if not parts:
            continue
        when = parse_time(parts[0])
        if when is None and len(parts) >= 8:
            when = parse_time(parts[7])
        if when and (latest_at is None or when > latest_at):
            latest_at = when
            latest_line = line
    return latest_at, latest_line


def is_recent(when: dt.datetime | None, now: dt.datetime, minutes: int) -> bool:
    return bool(when and now - when <= dt.timedelta(minutes=minutes))


def _conv_ids(rows: list[Conversation]) -> set[str]:
    return {row.conv_id for row in rows if row.conv_id}


def quiet_trace_matches_current_state(
    trace_line: str | None,
    decisions: list[Conversation],
    blocked: list[Conversation],
    stale: list[Conversation],
    expired: list[Conversation],
) -> bool:
    """Return True when an old stationnement trace still describes current blockers.

    Heartbeat replies can intentionally be `DONT_NOTIFY` without editing the
    repo. In that case the last persisted orchestrator trace ages, but the
    orchestration state is not stale if the same blockers/arbitrages are still
    the only reason to stay quiet.
    """
    if not trace_line:
        return False
    text = clean(trace_line)
    lower = text.lower()
    if not (
        "stationnement" in lower
        or "aucun role artificiel" in lower
        or "no_ord_actionnable" in lower
    ):
        return False

    important_ids = _conv_ids(decisions + blocked + stale + expired)
    if not important_ids:
        return "no_ord_actionnable" in lower or "aucun role artificiel" in lower
    return all(conv_id in text for conv_id in important_ids)


def summarize_row(row: Conversation) -> str:
    ord_ref = "" if status_of(row) == "EN_ATTENTE_USER" else ord_code(row.text)
    ord_part = f" / {ord_ref}" if ord_ref else ""
    return f"{row.conv_id}{ord_part} [{status_of(row)}] {clean(row.role)} -> {clean(row.next_step)}"


def next_ord_candidate(items: list[OrdItem], rows: list[Conversation]) -> OrdItem | None:
    blocked = {"ORD-P0-900", "ORD-P0-990"}
    active_codes = {code for row in rows if status_of(row) in ACTIVE_STATUSES for code in [ord_code(row.text)] if code}
    done_agile_codes = {
        code
        for row in rows
        if status_of(row) in TERMINAL_STATUSES and "AGILE-DONE" in row.text
        for code in [ord_code(row.text)]
        if code
    }
    for item in items:
        code = first_code(item.order)
        if code in blocked:
            continue
        if code in active_codes:
            continue
        if code in done_agile_codes:
            continue
        if "secret" in item.gate.lower() or "bloque" in item.gate.lower():
            continue
        return item
    return None


def emit_prompt(team: str, rows: list[Conversation], items: list[OrdItem]) -> str:
    decisions = [row for row in rows if status_of(row) == "EN_ATTENTE_USER"]
    blocked = [row for row in rows if status_of(row) == "BLOQUE"]
    running = [row for row in rows if status_of(row) == "EN_COURS"]
    candidate = next_ord_candidate(items, rows)
    route = route_for(team, candidate)
    if decisions:
        incident = TEAM_ROUTES["INCIDENT_STATIONNEMENT"]
        lines = [
            "Arbitrage orchestration CoproScope, sans relance automatique.",
            "Lis AGENTS.md, docs/presence_agents.md et docs/roadmap_backlog_central.md avant toute action.",
            f"Equipe-type: {incident.key} ({incident.orchestration}).",
            "Ne lance aucune nouvelle equipe et ne choisis aucun nouveau ORD tant que l'arbitrage EN_ATTENTE_USER n'est pas tranche.",
            "Les sous-agents attendent une mission explicite du fil pilote, pas un slot separe.",
            "Laisse seulement un check-in persistant et respecte les interdits: instances privees, documents bruts, secrets, exports bruts, serveurs non reserves, push GitHub et RM-2026-0017.",
        ]
    else:
        lines = [
            "Relance orchestration CoproScope.",
            f"Lis AGENTS.md, {TEAM_ROUTER_DOC}, docs/presence_agents.md et docs/roadmap_backlog_central.md avant toute action.",
            "Ne duplique pas de roles vivants, ne rouvre pas un lot AGILE-DONE sans nouveau diff ou decision explicite,",
            "et ne touche pas aux instances privees, documents bruts, secrets, exports bruts, serveurs non reserves, push GitHub ni RM-2026-0017.",
            "Si un dispatch est autorise, trace ROUTAGE_EQUIPE puis donne une mission bornee a chaque sous-agent.",
        ]
    if not decisions and (team == "agile" or route.key == "AGILE_UI_PRODUIT"):
        lines.append(AGILE_COMPOSITION_PROMPT)
    if decisions:
        lines.append("")
        lines.append("Priorite: remonter les arbitrages EN_ATTENTE_USER avant toute relance:")
        lines.extend(f"- {summarize_row(row)}" for row in decisions[:5])
    elif blocked:
        lines.append("")
        lines.append("Priorite: traiter ou confirmer les blocages avant de lancer une equipe:")
        lines.extend(f"- {summarize_row(row)}" for row in blocked[:5])
    elif running:
        lines.append("")
        lines.append("Verifier ces conversations EN_COURS et relancer seulement les roles manquants/idle/expires:")
        lines.extend(f"- {summarize_row(row)}" for row in running[:5])
    elif candidate:
        lines.append("")
        lines.append("Aucune conversation active prioritaire: appliquer le routeur automatique avant ouverture.")
        lines.append(f"Equipe-type: {route.key} - {route.label}.")
        lines.append(f"Protocole: {route.protocol}.")
        lines.append(f"Orchestration: {route.orchestration}.")
        lines.append(f"Roles: {route.roles}.")
        lines.append(f"Gate: {route.gate}.")
        lines.append(
            f"Cible: {first_code(candidate.order)} / {clean(candidate.chunk)} / RM lies {clean(candidate.rms)}."
        )
        lines.append(f"Tache suivante: {clean(candidate.next_task)}")
        lines.append(f"Gate backlog: {clean(candidate.gate)}")
        lines.append("Tracer ROUTAGE_EQUIPE dans docs/presence_agents.md avant de lancer les roles.")
        lines.append("Les sous-agents recoivent directement role, ownership, fichiers evites, preuves et condition d'arret.")
    else:
        lines.append("")
        lines.append("Aucun ORD actionnable detecte. Tracer NO_ORD_ACTIONNABLE avec la raison concrete.")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Check CoproScope orchestration state.")
    parser.add_argument("--strict", action="store_true", help="Exit 2 when action is required.")
    parser.add_argument("--emit-prompt", action="store_true", help="Print a relaunch prompt.")
    parser.add_argument("--team", choices=["auto", "agile", "uxui"], default="auto")
    parser.add_argument("--stale-minutes", type=int, default=20)
    parser.add_argument(
        "--quiet-grace-minutes",
        type=int,
        default=30,
        help="Maximum age for a quiet stationnement trace before it becomes stale.",
    )
    parser.add_argument("--require-recent-trace", action="store_true")
    args = parser.parse_args()

    root = repo_root()
    presence_path = root / "docs" / "presence_agents.md"
    roadmap_path = root / "docs" / "roadmap_backlog_central.md"
    rows = parse_presence(presence_path)
    ord_items = parse_ord(roadmap_path)
    now = dt.datetime.now(dt.timezone(dt.timedelta(hours=2)))

    running = [row for row in rows if status_of(row) == "EN_COURS"]
    decisions = [row for row in rows if status_of(row) == "EN_ATTENTE_USER"]
    blocked = [row for row in rows if status_of(row) == "BLOQUE"]
    ready = [row for row in rows if status_of(row) == "PRET_A_INTEGRER"]
    open_rows = [row for row in rows if status_of(row) in ACTIVE_STATUSES]
    stale = []
    expired = []
    for row in running:
        heartbeat = parse_time(row.heartbeat)
        expire = parse_time(row.expire)
        if not is_recent(heartbeat, now, args.stale_minutes):
            stale.append(row)
        if expire and now > expire:
            expired.append(row)

    watch_at, watch_line = latest_watchdog_trace(presence_path)
    watch_ok = is_recent(watch_at, now, args.stale_minutes)
    candidate = next_ord_candidate(ord_items, rows)

    print("CoproScope orchestration watchdog")
    print(f"Repository: {root}")
    print(f"Presence:   {presence_path}")
    print(f"Roadmap:    {roadmap_path}")
    print(f"Now:        {now.strftime('%Y-%m-%d %H:%M %z')}")
    print("")
    print(f"Running: {len(running)} | Waiting user: {len(decisions)} | Blocked: {len(blocked)} | Ready: {len(ready)}")
    print(f"Trace-open: {len(open_rows)} | Trace-ready: {len(ready)}")
    watch_age = now - watch_at if watch_at else None
    quiet_allowed = bool(watch_age and watch_age <= dt.timedelta(minutes=args.quiet_grace_minutes))
    watch_quiet = bool(
        not watch_ok
        and quiet_allowed
        and quiet_trace_matches_current_state(watch_line, decisions, blocked, stale, expired)
    )

    if watch_at:
        state = "OK" if watch_ok else "QUIET" if watch_quiet else "STALE"
        print(f"Orchestrator trace: {state}, last {watch_at.strftime('%Y-%m-%d %H:%M %z')} ({watch_age})")
        if watch_quiet:
            print("  Known stationnement still matches current blockers; no new role should be opened.")
        if watch_line:
            print(f"  {clean(watch_line)[:240]}")
    else:
        print("Orchestrator trace: MISSING")

    def section(title: str, values: list[Conversation], limit: int = 8) -> None:
        if not values:
            return
        print("")
        print(title)
        for row in values[:limit]:
            print(f"- {summarize_row(row)}")
        if len(values) > limit:
            print(f"- ... {len(values) - limit} more")

    section("Expired conversations", expired)
    section("Stale running conversations", stale)
    section("Decisions required", decisions)
    section("Blocked conversations", blocked)
    section("Ready to integrate", ready, limit=5)

    print("")
    if decisions:
        print("Recommended action: ask Brice to arbitrate before launching more roles.")
    elif blocked:
        print("Recommended action: clear blockers or explicitly station them before relaunch.")
    elif stale or expired:
        print("Recommended action: relaunch missing/idle roles or close expired conversations.")
    elif running:
        print("Recommended action: continue current team; relaunch only missing, idle or expired roles.")
    elif candidate:
        route = route_for(args.team, candidate)
        print(
            "Recommended action: route next team as "
            f"{route.key} on {first_code(candidate.order)} / {clean(candidate.chunk)}."
        )
    else:
        print("Recommended action: trace NO_ORD_ACTIONNABLE.")

    if args.emit_prompt:
        print("")
        print("--- RELAUNCH PROMPT ---")
        print(emit_prompt(args.team, rows, ord_items))

    trace_issue = args.require_recent_trace and not watch_ok and not watch_quiet
    has_issue = bool(decisions or blocked or stale or expired or trace_issue)
    return 2 if args.strict and has_issue else 0


if __name__ == "__main__":
    sys.exit(main())
