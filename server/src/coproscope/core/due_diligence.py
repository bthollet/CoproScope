from __future__ import annotations

import json
from pathlib import Path

from .common import RunContext, write_csv, write_text


def _result_label(item: dict) -> str:
    return item.get("nom_complet") or item.get("nom_raison_sociale") or item.get("nom_commercial") or ""


def _dirigeants_label(item: dict) -> str:
    labels = []
    for dirigeant in item.get("dirigeants") or []:
        if dirigeant.get("type_dirigeant") == "personne morale":
            labels.append(f"{dirigeant.get('denomination', '')} ({dirigeant.get('qualite', '')})".strip())
        else:
            labels.append(f"{dirigeant.get('prenoms', '')} {dirigeant.get('nom', '')} ({dirigeant.get('qualite', '')})".strip())
    return "; ".join(labels[:5])


def summarize_due_diligence(instance, run: RunContext) -> Path:
    cache_dir = instance.matrix("due_diligence_dir")
    reports_dir = instance.artifact("reports_dir")
    out_csv = reports_dir / "matrice_due_diligence_publique.csv"
    out_md = reports_dir / "rapport_due_diligence_publique.md"

    rows: list[dict[str, str]] = []
    if cache_dir and cache_dir.exists():
        for path in sorted(cache_dir.glob("recherche_entreprises_*.json")):
            payload = json.loads(path.read_text(encoding="utf-8"))
            query = payload.get("query", "")
            data = payload.get("data") or {}
            results = data.get("results") or []
            first = results[0] if results else None
            siege = (first or {}).get("siege") or {}
            qualification = "AUCUN_RESULTAT"
            total_results = int(data.get("total_results") or 0)
            if first and total_results == 1:
                qualification = "CANDIDAT_UNIQUE_A_RECOUPER"
            elif first and total_results <= 3:
                qualification = "QUELQUES_HOMONYMES_A_RECOUPER"
            elif first:
                qualification = "REQUETE_AMBIGUE"
            rows.append(
                {
                    "query": query,
                    "total_results": str(data.get("total_results", "")),
                    "qualification": qualification,
                    "first_name": _result_label(first or {}),
                    "first_siren": (first or {}).get("siren", ""),
                    "first_siret_siege": siege.get("siret", ""),
                    "first_adresse": siege.get("adresse", ""),
                    "etat_administratif": (first or {}).get("etat_administratif", ""),
                    "activite_principale": (first or {}).get("activite_principale", ""),
                    "dirigeants": _dirigeants_label(first or {}),
                    "cache_json": str(path),
                    "action": "Recouper avec devis, contrat, assurance et signataire.",
                }
            )

    fields = [
        "query",
        "total_results",
        "qualification",
        "first_name",
        "first_siren",
        "first_siret_siege",
        "first_adresse",
        "etat_administratif",
        "activite_principale",
        "dirigeants",
        "cache_json",
        "action",
    ]
    write_csv(out_csv, fields, rows)
    report_lines = [
        "# Rapport de due diligence publique",
        "",
        f"- Resultats: {len(rows)}",
        "",
        "| Query | Qualification | Premier resultat | SIREN |",
        "|---|---|---|---|",
    ]
    for row in rows:
        report_lines.append(
            f"| {row['query']} | {row['qualification']} | {row['first_name']} | {row['first_siren']} |"
        )
    if not rows:
        report_lines.append("| - | AUCUN_CACHE | - | - |")
    write_text(out_md, "\n".join(report_lines) + "\n")
    run.log_action("write", out_csv, "due diligence summary csv")
    run.log_action("write", out_md, "due diligence summary report")
    return out_csv
