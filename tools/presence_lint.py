"""Lecture du registre de presence: qui travaille sur quoi, et ou ca se chevauche.

Remplace la moitie utile de l'ancien `orchestration_watchdog.py`. Ne relance
rien, n'ecrit rien, n'appelle aucun processus. La vivacite reelle des sessions
n'est pas de son ressort: elle s'obtient cote agent avec `ListAgents`, le champ
`isRunning` des metadonnees de session s'etant revele faux le 2026-09-02.

Usage:
    python tools/presence_lint.py
    python tools/presence_lint.py --json
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

ACTIVE_STATUSES = {"A_LANCER", "EN_COURS", "EN_ATTENTE_USER", "BLOQUE", "PRET_A_INTEGRER"}
HEADER_PREFIX = "| Conversation | Roadmap | Chantier |"
PATH_RE = re.compile(r"`([^`]+)`")

# Registres de coordination: tout chantier actif les declare, par construction.
# Les compter comme chevauchement produirait un signal a chaque fois.
SHARED_BY_DESIGN = {
    "docs/presence_agents.md",
    "docs/roadmap_backlog_central.md",
}


@dataclass
class Row:
    conversation: str
    roadmap: str
    chantier: str
    role: str
    status: str
    ownership: str
    branch: str
    updated: str
    expires: str
    next_step: str
    trace: str
    line_no: int
    owned: set[str] = field(default_factory=set)


def repo_root() -> Path:
    for candidate in [Path.cwd(), *Path.cwd().parents]:
        if (candidate / "docs" / "presence_agents.md").exists():
            return candidate
    raise SystemExit("Lancer depuis le depot produit CoproScope.")


def _cells(line: str) -> list[str]:
    return [part.strip() for part in line.strip().strip("|").split("|")]


def owned_paths(ownership: str) -> set[str]:
    """Chemins revendiques, extraits des segments entre accents graves.

    Un segment n'est retenu que s'il ressemble a un chemin de fichier: il porte
    un separateur ou une extension. Cela ecarte les identifiants `RM-*`, `CH-*`
    et les statuts, qui sont ecrits de la meme facon.
    """
    found: set[str] = set()
    for raw in PATH_RE.findall(ownership):
        token = raw.strip()
        if "/" in token or re.search(r"\.[a-z]{2,5}$", token):
            found.add(token)
    return found


def parse_presence(path: Path) -> list[Row]:
    rows: list[Row] = []
    in_table = False
    for line_no, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if line.startswith(HEADER_PREFIX):
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
        cells = _cells(line)
        if len(cells) < 11:
            continue
        row = Row(*cells[:11], line_no=line_no)
        row.owned = owned_paths(row.ownership)
        rows.append(row)
    return rows


def status_of(row: Row) -> str:
    match = PATH_RE.search(row.status)
    return (match.group(1) if match else row.status).strip().upper()


def parse_date(value: str) -> dt.date | None:
    match = re.search(r"(\d{4})-(\d{2})-(\d{2})", value or "")
    if not match:
        return None
    try:
        return dt.date(int(match.group(1)), int(match.group(2)), int(match.group(3)))
    except ValueError:
        return None


def active_rows(rows: list[Row]) -> list[Row]:
    return [row for row in rows if status_of(row) in ACTIVE_STATUSES]


def overlaps(rows: list[Row]) -> list[tuple[Row, Row, set[str]]]:
    """Paires de chantiers actifs revendiquant au moins un meme fichier."""
    found: list[tuple[Row, Row, set[str]]] = []
    live = active_rows(rows)
    for index, left in enumerate(live):
        for right in live[index + 1 :]:
            shared = (left.owned & right.owned) - SHARED_BY_DESIGN
            if shared:
                found.append((left, right, shared))
    return found


def expired(rows: list[Row], today: dt.date) -> list[Row]:
    out = []
    for row in active_rows(rows):
        due = parse_date(row.expires)
        if due is not None and due < today:
            out.append(row)
    return out


def build_report(rows: list[Row], today: dt.date) -> dict[str, object]:
    live = active_rows(rows)
    return {
        "total": len(rows),
        "actifs": [
            {
                "conversation": row.conversation,
                "roadmap": row.roadmap,
                "statut": status_of(row),
                "role": row.role,
                "branche": row.branch,
                "expire": row.expires,
                "ligne": row.line_no,
                "fichiers": sorted(row.owned),
            }
            for row in live
        ],
        "chevauchements": [
            {
                "a": left.conversation,
                "b": right.conversation,
                "fichiers": sorted(shared),
            }
            for left, right, shared in overlaps(rows)
        ],
        "expires": [
            {"conversation": row.conversation, "expire": row.expires, "ligne": row.line_no}
            for row in expired(rows, today)
        ],
    }


def render(report: dict[str, object]) -> str:
    lines = [f"Registre de presence: {report['total']} lignes, {len(report['actifs'])} actives.", ""]
    for item in report["actifs"]:
        lines.append(f"  {item['statut']:<18} {item['conversation']}  {item['roadmap']}  {item['role']}")
    if report["chevauchements"]:
        lines += ["", "CHEVAUCHEMENTS DE PERIMETRE:"]
        for item in report["chevauchements"]:
            lines.append(f"  {item['a']} et {item['b']}: {', '.join(item['fichiers'])}")
    if report["expires"]:
        lines += ["", "LIGNES EXPIREES:"]
        for item in report["expires"]:
            lines.append(f"  {item['conversation']} expire le {item['expire']} (ligne {item['ligne']})")
    if not report["chevauchements"] and not report["expires"]:
        lines += ["", "Aucun chevauchement ni ligne expiree."]
    lines += [
        "",
        "Vivacite non verifiee ici: croiser ces lignes avec ListAgents cote agent.",
    ]
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true", help="sortie machine")
    parser.add_argument("--presence", type=Path, default=None, help="chemin du registre")
    args = parser.parse_args()

    path = args.presence or (repo_root() / "docs" / "presence_agents.md")
    rows = parse_presence(path)
    report = build_report(rows, dt.date.today())
    print(json.dumps(report, ensure_ascii=False, indent=2) if args.json else render(report))
    return 0


if __name__ == "__main__":
    sys.exit(main())
