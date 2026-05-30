import re
from collections import Counter
from pathlib import Path
from typing import Any, Iterable


STATUS_LABELS = {
    "EN_COURS": "Travaille",
    "PRET_A_INTEGRER": "A relire",
    "INTEGRE": "Integre",
    "BLOQUE": "Bloque",
    "CLOTURE": "Termine",
    "EXPIRE": "Expire",
}

STATUS_GROUPS = {
    "EN_COURS": "active",
    "PRET_A_INTEGRER": "review",
    "INTEGRE": "done",
    "BLOQUE": "blocked",
    "CLOTURE": "closed",
    "EXPIRE": "expired",
}

FORBIDDEN_PATTERNS = (
    re.compile(r"(?<![A-Za-z])[A-Za-z]:[\\/][^\s|,;`)]*"),
    re.compile(r"file://\S+", re.IGNORECASE),
    re.compile(r"(?:^|[\s`'\"(])(?:raw|restricted|logs|private)[\\/]\S*", re.IGNORECASE),
    re.compile(r"(?:token|secret|password|prompt)\s*[:=]\s*\S+", re.IGNORECASE),
)


def register_activity_routes(
    app: Any,
    templates: Any,
    context: Any,
    year: int,
    require_token: Any,
    html_response: Any,
) -> None:
    from fastapi import Request as FastAPIRequest

    @app.get("/pilotage/activite", response_class=html_response)
    def activity(request: FastAPIRequest):
        require_token(request)
        view = build_activity_view()
        return templates.TemplateResponse(
            request=request,
            name="activity.html",
            context=context(request, "activityops", model=view["shell_model"], activity=view),
        )


def build_activity_view(docs_root: Path | None = None, *, max_rows: int = 12) -> dict[str, Any]:
    docs = Path(docs_root) if docs_root else _repo_root() / "docs"
    rows = _presence_rows(docs / "presence_agents.md")
    activity_rows = [_activity_row(row) for row in rows]
    visible_rows = _sort_rows([row for row in activity_rows if row])[:max_rows]
    counts = Counter(row["status"] for row in visible_rows)
    blocked = [row for row in visible_rows if row["status"] == "BLOQUE"]
    active = [row for row in visible_rows if row["status"] == "EN_COURS"]
    review = [row for row in visible_rows if row["status"] == "PRET_A_INTEGRER"]
    guardrails = [
        _entry("Synthese courte", "La page affiche des statuts, pas des journaux techniques."),
        _entry("Details sensibles retires", "Chemins, identifiants et consignes longues restent hors interface."),
        _entry("Action humaine visible", "Un blocage dit quoi manque, sans exposer le contenu protege."),
    ]
    return {
        "title": "Activite en cours",
        "headline": "Travaux agents, blocages et prochains passages",
        "notice": "Synthese derivee de la presence et du gouvernail.",
        "status": {
            "label": _status_label(active, blocked, review),
            "summary": "Cette page montre ce qui travaille, ce qui attend une relecture et ce qui bloque.",
            "cta": "Relire les blocages",
        },
        "summary": [
            _metric("Travaux actifs", str(len(active)), "Agents ou heartbeats avec une prochaine action."),
            _metric("A relire", str(len(review)), "Lots termines qui demandent une integration ou decision."),
            _metric("Blocages", str(len(blocked)), "Points qui attendent une action humaine ou une preuve."),
            _metric("Integres visibles", str(counts.get("INTEGRE", 0)), "Derniers lots fermes gardes en lecture rapide."),
        ],
        "activities": visible_rows,
        "blocked": blocked,
        "status_counts": _count_rows(counts),
        "heartbeats": _heartbeat_rows(docs / "roadmap_backlog_central.md"),
        "definitions": [
            _entry("Travaille", "Une equipe ou automation a encore une action prevue."),
            _entry("A relire", "Un lot est pret mais demande une verification ou integration."),
            _entry("Bloque", "Une decision, une preuve ou une action manuelle manque."),
            _entry("Integre", "Le lot est ferme dans la base locale et verifie par tests ou trace."),
            _entry("Dernier passage", "Moment du dernier point lisible dans le registre."),
            _entry("Prochaine relance", "Moment declare pour reprendre ou surveiller le lot."),
        ],
        "actions": [
            _action("Retour aux indicateurs", "Disponible", "Revenir au pilotage des cartes metier.", "/pilotage"),
            _action("Voir actions orchestration", "Disponible", "Ouvrir la file d'actions filtree.", "/actions?scope=orchestration"),
            _action("Voir memoire de passation", "Disponible", "Relire les sujets ouverts et traces derivees.", "/chantiers?categorie=orchestration"),
            _action("Ouvrir journal technique", "Bloquee", "Les journaux complets restent hors interface.", ""),
            _action("Afficher consignes longues", "Bloquee", "Les consignes longues restent dans les traces de travail.", ""),
            _action("Afficher chemins locaux", "Bloquee", "Les emplacements complets ne sont pas affiches.", ""),
        ],
        "boundaries": guardrails,
        "guardrails": guardrails,
        "version_log": [
            "Vue Activite en cours creee depuis presence_agents et gouvernail.",
            "Projection limitee a des statuts courts et traces derivees.",
            "Journaux techniques, chemins, identifiants sensibles et consignes longues exclus.",
        ],
        "shell_model": _shell_model(),
    }


def _presence_rows(path: Path) -> list[list[str]]:
    if not path.exists():
        return []
    rows: list[list[str]] = []
    for line in path.read_text(encoding="utf-8", errors="ignore").splitlines():
        if not line.startswith("| `CONV-"):
            continue
        cells = [cell.strip() for cell in line.strip().split("|")[1:-1]]
        if len(cells) >= 11:
            rows.append(cells)
    return rows


def _activity_row(cells: list[str]) -> dict[str, Any]:
    conversation = _strip_code(cells[0])
    roadmap = _sanitize(_strip_code(cells[1]), 80)
    chantier = _sanitize(_strip_code(cells[2]), 80)
    role = _sanitize(_strip_code(cells[3]), 90)
    status = _strip_code(cells[4])
    start_at = _sanitize(_strip_code(cells[7]), 32)
    next_check = _sanitize(_strip_code(cells[8]), 32)
    current_step = _sanitize(cells[9], 180)
    note = _sanitize(cells[10], 180)
    return {
        "conversation_id": conversation,
        "roadmap_id": roadmap,
        "chantier_id": chantier,
        "role": role,
        "status": status,
        "status_label": STATUS_LABELS.get(status, "A verifier"),
        "status_group": STATUS_GROUPS.get(status, "review"),
        "last_heartbeat_at": start_at,
        "next_check_at": "" if status in {"INTEGRE", "CLOTURE", "EXPIRE"} else next_check,
        "current_step": current_step or _step_for(status),
        "blocked_by": _blocked_by(status, f"{current_step} {note}"),
        "proof_summary": _proof_summary(status, note),
        "trace_label": _trace_label(cells[5]),
        "trace_href": "#activity-traces",
    }


def _heartbeat_rows(path: Path, limit: int = 4) -> list[dict[str, str]]:
    if not path.exists():
        return []
    rows: list[dict[str, str]] = []
    for line in path.read_text(encoding="utf-8", errors="ignore").splitlines():
        if "relance-equipe-agile-gouvernail-autonome" not in line:
            continue
        cells = [cell.strip() for cell in line.strip().split("|")[1:-1]]
        if len(cells) < 4:
            continue
        rows.append(
            {
                "at": _sanitize(_strip_code(cells[0]), 32),
                "label": _sanitize(_strip_code(cells[2]), 80),
                "detail": _sanitize(cells[3], 180),
            }
        )
    return rows[-limit:][::-1]


def _sort_rows(rows: Iterable[dict[str, Any]]) -> list[dict[str, Any]]:
    rank = {"EN_COURS": 0, "BLOQUE": 1, "PRET_A_INTEGRER": 2, "INTEGRE": 3, "EXPIRE": 4, "CLOTURE": 5}
    return sorted(rows, key=lambda row: (rank.get(row["status"], 9), row["conversation_id"]), reverse=False)


def _status_label(active: list[dict[str, Any]], blocked: list[dict[str, Any]], review: list[dict[str, Any]]) -> str:
    if blocked:
        return "Blocages a regarder"
    if active:
        return "Travail actif"
    if review:
        return "Relectures en attente"
    return "Derniers lots integres"


def _blocked_by(status: str, text: str) -> str:
    if status != "BLOQUE":
        return "non bloque"
    lowered = text.lower()
    if "serveur" in lowered or "port" in lowered or "8788" in lowered:
        return "serveur a relancer"
    if "manuel" in lowered or "brice" in lowered or "user" in lowered:
        return "action humaine"
    if "test" in lowered or "preuve" in lowered:
        return "preuve ou test"
    return "decision a prendre"


def _proof_summary(status: str, note: str) -> str:
    lowered = note.lower()
    ok_match = re.search(r"([A-Za-z0-9_/ -]{0,45}\b\d+\s+OK)", note)
    if ok_match:
        return _sanitize(ok_match.group(1), 90)
    if status == "INTEGRE":
        return "Tests ou trace de fin declares."
    if status == "BLOQUE":
        return "Blocage declare dans la presence."
    if status == "PRET_A_INTEGRER":
        return "Livrable pret a verifier."
    if "diff-check" in lowered:
        return "Verification locale declaree."
    return "Trace courte disponible."


def _trace_label(ownership_cell: str) -> str:
    match = re.search(r"docs/([A-Za-z0-9_.-]+\.md)", ownership_cell)
    if match:
        return match.group(1)
    return "presence_agents.md"


def _step_for(status: str) -> str:
    return {
        "EN_COURS": "Continuer le lot et verifier les preuves.",
        "PRET_A_INTEGRER": "Relire le diff et lancer les tests d'integration.",
        "BLOQUE": "Lever le blocage indique avant reprise.",
        "INTEGRE": "Aucune action immediate.",
    }.get(status, "Relire le statut.")


def _sanitize(value: str, limit: int) -> str:
    text = _strip_code(value)
    for pattern in FORBIDDEN_PATTERNS:
        text = pattern.sub("[retire]", text)
    text = re.sub(r"\b(raw|restricted|logs?|private|tokens?|secrets?|prompts?)\b", "[retire]", text, flags=re.IGNORECASE)
    text = re.sub(r"`[^`]*(?:raw|restricted|logs|private|token|secret|prompt)[^`]*`", "[retire]", text, flags=re.IGNORECASE)
    text = re.sub(r"\s+", " ", text).strip()
    if len(text) <= limit:
        return text
    return f"{text[: limit - 1].rstrip()}..."


def _strip_code(value: str) -> str:
    return value.replace("`", "").strip()


def _metric(label: str, value: str, detail: str) -> dict[str, str]:
    return {"label": label, "value": value, "detail": detail}


def _entry(label: str, detail: str) -> dict[str, str]:
    return {"label": label, "detail": detail}


def _action(label: str, state: str, reason: str, href: str) -> dict[str, str]:
    return {"label": label, "state": state, "reason": reason, "href": href, "enabled": "true" if href else "false"}


def _count_rows(counts: Counter[str]) -> list[dict[str, Any]]:
    return [{"key": key, "label": STATUS_LABELS.get(key, key), "count": count} for key, count in counts.items() if count]


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[4]


def _shell_model() -> dict[str, Any]:
    return {
        "instance": {"id": "FICTIF", "name": "Copropriete FICTIVE", "root": "", "year": 2025},
        "ux": {
            "shell": {
                "app_title": "CoproScope",
                "page_title": "Activite en cours",
                "active_page": "activityops",
                "search_placeholder": "Rechercher une equipe, un statut ou un blocage...",
                "notification_count": 0,
                "sharing_mode_label": "Synthese locale",
                "sharing_mode_status": "Aucune trace technique complete affichee",
            }
        },
        "action_summary": {"total": "", "accounting": "", "scope_counts": {}},
        "kpis": {"actions": "", "doc_requests": "", "decisions": "", "privacy_reviews": ""},
    }
