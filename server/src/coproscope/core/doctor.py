from __future__ import annotations

import shutil
from pathlib import Path

from .common import InstanceConfig, RunContext, env_snapshot, module_available


def _path_state(path: Path) -> str:
    if path.exists():
        return "OK"
    return "MISSING"


def run_doctor(instance: InstanceConfig, run: RunContext) -> int:
    issues = 0
    politique_linguistique = instance.politique_linguistique()
    lines = [
        f"Diagnostic CoproScope pour {instance.display_name}",
        f"- identifiant_instance: {instance.instance_id}",
        f"- fichier_instance: {instance.path}",
        "",
        "Racines:",
    ]
    root_labels = {
        "workspace": "espace_travail",
        "raw": "bruts",
        "system": "systeme",
        "outputs": "sorties",
        "staging": "preparation",
        "logs": "journaux",
    }
    for root_name in ["workspace", "raw", "system", "outputs", "staging", "logs"]:
        root_path = instance.root(root_name)
        state = _path_state(root_path)
        lines.append(f"- {root_labels[root_name]}: {state} -> {root_path}")
        if state != "OK" and root_name in {"workspace", "raw", "system"}:
            issues += 1

    lines.append("")
    lines.append("Registres:")
    register_labels = {
        "documents": "documents",
        "duplicates": "doublons",
        "manifest": "manifeste",
        "requests": "demandes",
        "ag": "assemblees_generales",
        "findings": "constats",
        "kpi": "indicateurs",
    }
    for register_name in ["documents", "duplicates", "manifest", "requests", "ag", "findings", "kpi"]:
        try:
            register_path = instance.register(register_name)
        except KeyError:
            issues += 1
            lines.append(f"- {register_labels[register_name]}: CONFIG_MANQUANTE")
            continue
        lines.append(f"- {register_labels[register_name]}: {register_path}")

    lines.append("")
    lines.append("Dependances:")
    for dependency in ["pypdf", "openpyxl", "docx", "duckdb", "pandas", "pdfplumber", "facturx", "grist_api"]:
        lines.append(f"- {dependency}: {'OK' if module_available(dependency) else 'OPTIONNEL_ABSENT'}")

    lines.append("")
    lines.append("Outils systeme:")
    for executable in ["python", "gh", "git", "uv", "rg", "fd", "jq", "duckdb", "qpdf", "pdftotext", "tesseract", "magick", "node", "npm.cmd", "evidence.cmd"]:
        lines.append(f"- {executable}: {'OK' if shutil.which(executable) else 'OPTIONNEL_ABSENT'}")
    lines.append("- grist-ctl: BLOQUE_SECURITE si absent; utiliser grist_api par defaut.")

    docai = instance.docai_settings()
    lines.append("")
    lines.append("Document Intelligence:")
    lines.append(f"- mode: {docai['mode']}")
    lines.append(f"- confidentialite: {docai['privacy']}")
    lines.append(f"- device: {docai['device']}")
    lines.append(f"- backends_actifs: {', '.join(docai['enabled_backends']) if docai['enabled_backends'] else 'aucun'}")
    for dependency in ["fitz", "docling", "rapidocr", "torch", "transformers"]:
        lines.append(f"- {dependency}: {'OK' if module_available(dependency) else 'OPTIONNEL_ABSENT'}")

    snapshot = env_snapshot(instance)
    lines.append("")
    lines.append("Environnement:")
    for key in instance.required_env():
        present = key in snapshot
        lines.append(f"- {key}: {'OK' if present else 'ABSENT'}")
        if not present:
            issues += 1
    for key in instance.optional_env():
        lines.append(f"- {key}: {'DEFINIE' if key in snapshot else 'absente'}")

    lines.append("")
    lines.append("Politique linguistique:")
    lines.append(f"- langue_principale: {politique_linguistique['langue_principale']}")
    lines.append(f"- locale_preferree: {politique_linguistique['locale_preferree']}")
    lines.append(f"- preferer_le_francais: {politique_linguistique['preferer_le_francais']}")
    lines.append(f"- autoriser_anglais_technique: {politique_linguistique['autoriser_anglais_technique']}")
    lines.append(f"- traduire_sorties_diffusables: {politique_linguistique['traduire_sorties_diffusables']}")

    settings = instance.settings()
    public_repo_url = settings.get("url_depot_public") or settings.get("public_repo_url")
    if public_repo_url:
        lines.append("")
        lines.append("Partage GitHub:")
        lines.append(f"- url_depot_public: {public_repo_url}")
        lines.append("- politique: partager uniquement des ameliorations generiques ; ne jamais publier de donnees d'instance privee.")

    report = "\n".join(lines) + "\n"
    print(report)
    run.note(report)
    return issues
