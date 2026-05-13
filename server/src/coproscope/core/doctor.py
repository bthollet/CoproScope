from __future__ import annotations

from pathlib import Path

from .common import InstanceConfig, RunContext, env_snapshot, module_available


def _path_state(path: Path) -> str:
    if path.exists():
        return "OK"
    return "MISSING"


def run_doctor(instance: InstanceConfig, run: RunContext) -> int:
    issues = 0
    lines = [
        f"CoproScope doctor for {instance.display_name}",
        f"- instance_id: {instance.instance_id}",
        f"- instance file: {instance.path}",
        "",
        "Roots:",
    ]
    for root_name in ["workspace", "raw", "system", "outputs", "staging", "logs"]:
        root_path = instance.root(root_name)
        state = _path_state(root_path)
        lines.append(f"- {root_name}: {state} -> {root_path}")
        if state != "OK" and root_name in {"workspace", "raw", "system"}:
            issues += 1

    lines.append("")
    lines.append("Registers:")
    for register_name in ["documents", "duplicates", "manifest", "requests", "ag", "findings", "kpi"]:
        try:
            register_path = instance.register(register_name)
        except KeyError:
            issues += 1
            lines.append(f"- {register_name}: MISSING_CONFIG")
            continue
        lines.append(f"- {register_name}: {register_path}")

    lines.append("")
    lines.append("Dependencies:")
    for dependency in ["pypdf", "openpyxl", "docx"]:
        lines.append(f"- {dependency}: {'OK' if module_available(dependency) else 'OPTIONAL_MISSING'}")

    snapshot = env_snapshot(instance)
    lines.append("")
    lines.append("Environment:")
    for key in instance.required_env():
        present = key in snapshot
        lines.append(f"- {key}: {'OK' if present else 'MISSING'}")
        if not present:
            issues += 1
    for key in instance.optional_env():
        lines.append(f"- {key}: {'SET' if key in snapshot else 'absent'}")

    public_repo_url = instance.settings().get("public_repo_url")
    if public_repo_url:
        lines.append("")
        lines.append("GitHub sharing:")
        lines.append(f"- public_repo_url: {public_repo_url}")
        lines.append("- policy: share generic improvements only; never share private instance data.")

    report = "\n".join(lines) + "\n"
    print(report)
    run.note(report)
    return issues
