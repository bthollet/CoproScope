from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any


EXPECTED_INSTANCE = "beauvallon_reconstruction_sim_20260523"
PRIVATE_DIR = "protocole_reconstruction"
ACTIVE_STATUSES = {"A_LANCER", "EN_COURS", "EN_ATTENTE_USER", "BLOQUE", "PRET_A_INTEGRER"}
ROLES = {"expert", "designer", "novice", "coproscope", "qa"}


class ProtocolError(RuntimeError):
    pass


def now_text() -> str:
    return dt.datetime.now(dt.timezone(dt.timedelta(hours=2))).strftime("%Y-%m-%d %H:%M %z")


def parse_time(value: str) -> dt.datetime | None:
    try:
        return dt.datetime.strptime(value, "%Y-%m-%d %H:%M %z")
    except ValueError:
        return None


def repo_root(start: Path | None = None) -> Path:
    current = (start or Path.cwd()).resolve()
    for candidate in [current, *current.parents]:
        if (candidate / "docs" / "presence_agents.md").exists():
            return candidate
    raise ProtocolError("Lance cette commande depuis le depot produit CoproScope.")


def validate_instance(path: str | Path) -> Path:
    instance = Path(path).resolve()
    lowered_parts = {part.lower() for part in instance.parts}
    if "beauvallon" in lowered_parts and EXPECTED_INSTANCE.lower() not in lowered_parts:
        raise ProtocolError("Mauvaise instance: l'ancienne instance Beauvallon est refusee.")
    if instance.name.lower() != "instance" or instance.parent.name != EXPECTED_INSTANCE:
        raise ProtocolError(f"Instance refusee: attends ...\\{EXPECTED_INSTANCE}\\instance.")
    if not instance.exists():
        raise ProtocolError(f"Instance introuvable: {instance}")
    return instance


def journal_root(instance: Path) -> Path:
    return instance.parent / "docs_de_travail" / PRIVATE_DIR


def state_path(instance: Path) -> Path:
    return journal_root(instance) / "state.json"


def doc_path(instance: Path, doc_id: str) -> Path:
    return journal_root(instance) / "documents" / f"{doc_id}.json"


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")


def load_state(instance: Path) -> dict[str, Any]:
    path = state_path(instance)
    if not path.exists():
        raise ProtocolError("Protocole non initialise. Lance d'abord `init`.")
    return read_json(path)


def save_state(instance: Path, state: dict[str, Any]) -> None:
    write_json(state_path(instance), state)


def load_doc(instance: Path, doc_id: str) -> dict[str, Any]:
    path = doc_path(instance, doc_id)
    if not path.exists():
        raise ProtocolError(f"Document inconnu dans le protocole: {doc_id}")
    return read_json(path)


def save_doc(instance: Path, doc: dict[str, Any]) -> None:
    write_json(doc_path(instance, doc["doc_id"]), doc)


def split_md_row(line: str) -> list[str]:
    return [part.strip().replace("`", "") for part in line.strip().strip("|").split("|")]


def git_dirty_lines(root: Path) -> list[str]:
    if not (root / ".git").exists():
        return []
    result = subprocess.run(["git", "status", "--short"], cwd=root, text=True, capture_output=True)
    if result.returncode != 0:
        return ["git status indisponible"]
    return [line for line in result.stdout.splitlines() if line.strip()]


def active_other_work(root: Path) -> list[str]:
    path = root / "docs" / "presence_agents.md"
    if not path.exists():
        return []
    rows: list[str] = []
    in_table = False
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.startswith("| Conversation | Roadmap | Chantier |"):
            in_table = True
            continue
        if not in_table or line.startswith("|---"):
            continue
        if not line.strip() or line.startswith("## "):
            break
        if not line.startswith("|"):
            continue
        parts = split_md_row(line)
        if len(parts) < 11:
            continue
        conversation, roadmap, chantier, _role, status = parts[:5]
        if status in ACTIVE_STATUSES and "RM-2026-0017" not in roadmap:
            rows.append(f"{conversation} / {roadmap} / {chantier} [{status}]")
    return rows


def preflight(root: Path) -> dict[str, Any]:
    dirty = git_dirty_lines(root)
    others = active_other_work(root)
    issues: list[str] = []
    if dirty:
        issues.append(f"{len(dirty)} changement(s) Git non integre(s)")
    if others:
        issues.append(f"{len(others)} autre(s) chantier(s) actif(s)")
    return {
        "status": "WAIT_MERGE" if issues else "READY",
        "issues": issues,
        "dirty_count": len(dirty),
        "dirty_preview": dirty[:20],
        "other_active": others[:20],
        "checked_at": now_text(),
    }


def new_state(instance: Path, root: Path) -> dict[str, Any]:
    return {
        "schema_version": 1,
        "instance_kind": EXPECTED_INSTANCE,
        "created_at": now_text(),
        "instance_root_private": str(instance),
        "current_doc": None,
        "last_closed_doc": None,
        "documents": [],
        "series_rules": [],
        "checkpoints": [],
        "preflight": preflight(root),
    }


def _checkpoint_entries(state: dict[str, Any]) -> list[dict[str, Any]]:
    checkpoints = state.get("checkpoints", [])
    if checkpoints:
        return list(checkpoints)
    return list(state.get("heartbeats", []))


def has_recent_checkpoint(state: dict[str, Any], minutes: int = 120) -> bool:
    checkpoints = _checkpoint_entries(state)
    if not checkpoints:
        return False
    last = parse_time(str(checkpoints[-1].get("at", "")))
    if not last:
        return False
    now = dt.datetime.now(dt.timezone(dt.timedelta(hours=2)))
    return now - last <= dt.timedelta(minutes=minutes)


def role_entries(doc: dict[str, Any], role: str) -> list[dict[str, Any]]:
    return list(doc.get("roles", {}).get(role, []))


def any_entry(doc: dict[str, Any], role: str, key: str) -> bool:
    return any(bool(entry.get(key)) for entry in role_entries(doc, role))


def gate_status(state: dict[str, Any], doc: dict[str, Any]) -> tuple[bool, list[str]]:
    missing: list[str] = []
    if not any_entry(doc, "expert", "cloud_analysis"):
        missing.append("analyse IA cloud cote expert")
    if not any_entry(doc, "expert", "audit_analysis"):
        missing.append("audit metier expert")
    if not any_entry(doc, "designer", "cloud_analysis"):
        missing.append("controle IA cloud cote designer")
    if not role_entries(doc, "designer"):
        missing.append("retour designer")
    if not role_entries(doc, "novice"):
        missing.append("retour novice CoproScope")
    if not role_entries(doc, "coproscope"):
        missing.append("observation CoproScope")
    if not doc.get("ui_routes"):
        missing.append("pages UI CoproScope consultees")
    if not doc.get("machine_reviewed"):
        missing.append("revue des traitements machine attendus")
    triage = doc.get("triage", {})
    if not triage.get("decided_at"):
        missing.append("tri designer urgent/backlog/exploration")
    unresolved = [item for item in triage.get("before_next", []) if item not in triage.get("resolved_before_next", [])]
    if unresolved:
        missing.append("points a traiter avant document suivant non resolus")
    exe = doc.get("executable_test", {})
    if exe.get("result") != "ok" or not exe.get("sha256"):
        missing.append("test OK sur dernier executable avec SHA-256")
    if not has_recent_checkpoint(state):
        missing.append("point de reprise manuel de moins de 2 heures")
    return not missing, missing


def initial_doc(index: int, source_ref: str) -> dict[str, Any]:
    doc_id = f"DOC-{index:04d}"
    return {
        "doc_id": doc_id,
        "inbox_index": index,
        "source_ref_private": source_ref,
        "status": "OPEN",
        "opened_at": now_text(),
        "roles": {role: [] for role in sorted(ROLES)},
        "ui_routes": [],
        "machine_reviewed": False,
        "triage": {"before_next": [], "backlog_now": [], "future": [], "resolved_before_next": []},
    }


def approved_series(state: dict[str, Any], rule_id: str) -> bool:
    return any(rule.get("rule_id") == rule_id and rule.get("approved") for rule in state.get("series_rules", []))


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def cmd_init(args: argparse.Namespace) -> int:
    root = repo_root()
    instance = validate_instance(args.instance_root)
    path = state_path(instance)
    if path.exists() and not args.restart:
        raise ProtocolError("Journal deja present. Utilise `init --restart` pour repartir de zero.")
    state = new_state(instance, root)
    state["restart_from_zero"] = bool(args.restart)
    write_json(path, state)
    print(f"Protocole initialise: {journal_root(instance)}")
    print(f"Preflight: {state['preflight']['status']}")
    for issue in state["preflight"]["issues"]:
        print(f"- {issue}")
    return 2 if state["preflight"]["status"] == "WAIT_MERGE" else 0


def cmd_status(args: argparse.Namespace) -> int:
    root = repo_root()
    instance = validate_instance(args.instance_root)
    state = read_json(state_path(instance)) if state_path(instance).exists() else None
    check = preflight(root)
    print(f"Instance: {EXPECTED_INSTANCE}")
    print(f"Preflight: {check['status']}")
    if state is None:
        print("Journal: non initialise")
        return 0
    print(f"Document courant: {state.get('current_doc') or 'aucun'}")
    print(f"Dernier document clos: {state.get('last_closed_doc') or 'aucun'}")
    print(f"Point de reprise recent: {'oui' if has_recent_checkpoint(state) else 'non'}")
    if state.get("current_doc"):
        doc = load_doc(instance, state["current_doc"])
        ok, missing = gate_status(state, doc)
        print(f"Gate document: {'OK' if ok else 'BLOQUE'}")
        for item in missing:
            print(f"- {item}")
    return 0


def cmd_checkpoint(args: argparse.Namespace) -> int:
    instance = validate_instance(args.instance_root)
    state = load_state(instance)
    state.setdefault("checkpoints", []).append({"at": now_text(), "note": args.note or "checkpoint protocole"})
    save_state(instance, state)
    print("Point de reprise protocole enregistre.")
    return 0


def cmd_next_doc(args: argparse.Namespace) -> int:
    root = repo_root()
    instance = validate_instance(args.instance_root)
    state = load_state(instance)
    check = preflight(root)
    state["preflight"] = check
    if check["status"] != "READY":
        save_state(instance, state)
        raise ProtocolError("WAIT_MERGE: autres changements ou chantiers a fusionner/garer avant l'inbox.")
    current = state.get("current_doc")
    if current:
        ok, missing = gate_status(state, load_doc(instance, current))
        if not ok:
            raise ProtocolError("Document precedent bloque: " + "; ".join(missing))
    expected = len(state.get("documents", [])) + 1
    index = args.inbox_index or expected
    if index != expected and not (args.series_rule and approved_series(state, args.series_rule)):
        raise ProtocolError("Saut de document refuse sans regle de serie approuvee.")
    doc = initial_doc(expected, args.source_ref or f"inbox-rank-{index}")
    doc["inbox_index"] = index
    save_doc(instance, doc)
    state.setdefault("documents", []).append(doc["doc_id"])
    state["current_doc"] = doc["doc_id"]
    save_state(instance, state)
    print(f"Document ouvert: {doc['doc_id']} (rang inbox {index})")
    return 0


def cmd_record(args: argparse.Namespace) -> int:
    instance = validate_instance(args.instance_root)
    state = load_state(instance)
    doc = load_doc(instance, args.doc or state.get("current_doc"))
    entry = {
        "at": now_text(),
        "note": args.note,
        "cloud_analysis": bool(args.cloud_analysis),
        "audit_analysis": bool(args.audit_analysis),
        "machine_review": bool(args.machine_reviewed),
    }
    doc.setdefault("roles", {}).setdefault(args.role, []).append(entry)
    if args.route:
        doc.setdefault("ui_routes", []).extend(args.route)
    if args.machine_reviewed:
        doc["machine_reviewed"] = True
    save_doc(instance, doc)
    print(f"Note {args.role} enregistree pour {doc['doc_id']}.")
    return 0


def cmd_record_executable(args: argparse.Namespace) -> int:
    instance = validate_instance(args.instance_root)
    state = load_state(instance)
    doc = load_doc(instance, args.doc or state.get("current_doc"))
    exe_path = Path(args.exe_path)
    exe_sha = args.exe_sha256.upper() if args.exe_sha256 else ""
    if not exe_sha:
        if not exe_path.exists():
            raise ProtocolError("Executable introuvable et aucun SHA-256 fourni.")
        exe_sha = sha256_file(exe_path)
    if not re.fullmatch(r"[A-F0-9]{64}", exe_sha):
        raise ProtocolError("SHA-256 invalide.")
    doc["executable_test"] = {
        "at": now_text(),
        "path_private": str(exe_path),
        "sha256": exe_sha,
        "result": args.result,
        "note": args.note or "",
    }
    if args.route:
        doc.setdefault("ui_routes", []).extend(args.route)
    save_doc(instance, doc)
    print(f"Test executable enregistre pour {doc['doc_id']}: {args.result}")
    return 0


def cmd_triage(args: argparse.Namespace) -> int:
    instance = validate_instance(args.instance_root)
    state = load_state(instance)
    doc = load_doc(instance, args.doc or state.get("current_doc"))
    if not (args.no_items or args.before_next or args.backlog_now or args.future):
        raise ProtocolError("Tri designer vide: ajoute un item ou utilise --no-items.")
    triage = doc.setdefault("triage", {})
    triage["decided_at"] = now_text()
    triage["before_next"] = args.before_next or []
    triage["backlog_now"] = args.backlog_now or []
    triage["future"] = args.future or []
    if args.resolve_before_next == "all":
        triage["resolved_before_next"] = list(triage["before_next"])
    if args.machine_reviewed:
        doc["machine_reviewed"] = True
    save_doc(instance, doc)
    print(f"Tri designer enregistre pour {doc['doc_id']}.")
    return 0


def cmd_gate(args: argparse.Namespace) -> int:
    instance = validate_instance(args.instance_root)
    state = load_state(instance)
    doc = load_doc(instance, args.doc or state.get("current_doc"))
    ok, missing = gate_status(state, doc)
    if not ok:
        print("BLOQUE")
        for item in missing:
            print(f"- {item}")
        return 2
    print("OK - passage autorise")
    if args.close:
        doc["status"] = "CLOSED"
        doc["closed_at"] = now_text()
        save_doc(instance, doc)
        state["last_closed_doc"] = doc["doc_id"]
        state["current_doc"] = None
        save_state(instance, state)
    return 0


def cmd_series(args: argparse.Namespace) -> int:
    instance = validate_instance(args.instance_root)
    state = load_state(instance)
    if args.examples < 2:
        raise ProtocolError("Serie refusee: au moins 2 exemples complets sont requis.")
    if not (args.expert_ok and args.designer_ok and args.qa_ok):
        raise ProtocolError("Serie refusee: validations expert, designer et QA requises.")
    state.setdefault("series_rules", []).append(
        {
            "rule_id": args.rule_id,
            "approved": True,
            "examples": args.examples,
            "at": now_text(),
            "note": args.note or "",
        }
    )
    save_state(instance, state)
    print(f"Regle de serie approuvee: {args.rule_id}")
    return 0


def safe_summary(state: dict[str, Any], doc: dict[str, Any] | None) -> str:
    lines = ["# Synthese anonymisee protocole reconstruction", ""]
    lines.append(f"- Preflight: {state.get('preflight', {}).get('status', 'UNKNOWN')}")
    lines.append(f"- Document courant: {state.get('current_doc') or 'aucun'}")
    lines.append(f"- Dernier document clos: {state.get('last_closed_doc') or 'aucun'}")
    lines.append(f"- Point de reprise recent: {'oui' if has_recent_checkpoint(state) else 'non'}")
    if doc:
        ok, missing = gate_status(state, doc)
        exe = doc.get("executable_test", {})
        lines.append(f"- Document: {doc['doc_id']} / rang inbox {doc.get('inbox_index')}")
        lines.append(f"- Gate: {'OK' if ok else 'BLOQUE'}")
        lines.append(f"- Roles notes: {', '.join(role for role in sorted(ROLES) if role_entries(doc, role)) or 'aucun'}")
        if exe:
            lines.append(f"- Executable: {Path(exe.get('path_private', 'CoproScope.exe')).name}")
            lines.append(f"- SHA-256: {exe.get('sha256', '')}")
        if missing:
            lines.append("- Manques: " + "; ".join(missing))
    return "\n".join(lines) + "\n"


def cmd_export(args: argparse.Namespace) -> int:
    instance = validate_instance(args.instance_root)
    state = load_state(instance)
    doc_id = args.doc or state.get("current_doc") or state.get("last_closed_doc")
    doc = load_doc(instance, doc_id) if doc_id else None
    text = safe_summary(state, doc)
    if args.output:
        Path(args.output).write_text(text, encoding="utf-8")
    else:
        print(text, end="")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Garde-fou local reconstruction Beauvallon.")
    parser.add_argument("--instance-root", required=True)
    sub = parser.add_subparsers(dest="command", required=True)
    p_init = sub.add_parser("init")
    p_init.add_argument("--restart", action="store_true")
    p_init.set_defaults(func=cmd_init)
    sub.add_parser("status").set_defaults(func=cmd_status)
    p_checkpoint = sub.add_parser("checkpoint")
    p_checkpoint.add_argument("--note")
    p_checkpoint.set_defaults(func=cmd_checkpoint)
    p_hb = sub.add_parser("heartbeat", help="Alias legacy de checkpoint; ne cree aucune automation Codex.")
    p_hb.add_argument("--note")
    p_hb.set_defaults(func=cmd_checkpoint)
    p_next = sub.add_parser("next-doc")
    p_next.add_argument("--inbox-index", type=int)
    p_next.add_argument("--source-ref")
    p_next.add_argument("--series-rule")
    p_next.set_defaults(func=cmd_next_doc)
    p_record = sub.add_parser("record")
    p_record.add_argument("role", choices=sorted(ROLES))
    p_record.add_argument("--doc")
    p_record.add_argument("--note", required=True)
    p_record.add_argument("--cloud-analysis", action="store_true")
    p_record.add_argument("--audit-analysis", action="store_true")
    p_record.add_argument("--machine-reviewed", action="store_true")
    p_record.add_argument("--route", action="append")
    p_record.set_defaults(func=cmd_record)
    p_exe = sub.add_parser("record-executable-test")
    p_exe.add_argument("--doc")
    p_exe.add_argument("--exe-path", required=True)
    p_exe.add_argument("--exe-sha256")
    p_exe.add_argument("--result", choices=["ok", "failed"], required=True)
    p_exe.add_argument("--route", action="append")
    p_exe.add_argument("--note")
    p_exe.set_defaults(func=cmd_record_executable)
    p_triage = sub.add_parser("triage")
    p_triage.add_argument("--doc")
    p_triage.add_argument("--before-next", action="append")
    p_triage.add_argument("--backlog-now", action="append")
    p_triage.add_argument("--future", action="append")
    p_triage.add_argument("--resolve-before-next", choices=["all"])
    p_triage.add_argument("--machine-reviewed", action="store_true")
    p_triage.add_argument("--no-items", action="store_true")
    p_triage.set_defaults(func=cmd_triage)
    p_gate = sub.add_parser("gate")
    p_gate.add_argument("--doc")
    p_gate.add_argument("--close", action="store_true")
    p_gate.set_defaults(func=cmd_gate)
    p_series = sub.add_parser("series")
    p_series.add_argument("--rule-id", required=True)
    p_series.add_argument("--examples", type=int, required=True)
    p_series.add_argument("--expert-ok", action="store_true")
    p_series.add_argument("--designer-ok", action="store_true")
    p_series.add_argument("--qa-ok", action="store_true")
    p_series.add_argument("--note")
    p_series.set_defaults(func=cmd_series)
    p_export = sub.add_parser("export-safe-summary")
    p_export.add_argument("--doc")
    p_export.add_argument("--output")
    p_export.set_defaults(func=cmd_export)
    return parser


def main(argv: list[str] | None = None) -> int:
    try:
        args = build_parser().parse_args(argv)
        return int(args.func(args))
    except ProtocolError as exc:
        print(f"ERREUR: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
