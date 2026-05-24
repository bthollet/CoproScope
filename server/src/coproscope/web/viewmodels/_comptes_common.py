from __future__ import annotations

from ._runtime import *

def _comptes_empty_selected(year: int) -> dict[str, object]:
    return {
        "category_id": "",
        "label": "Aucune categorie selectionnee",
        "icon": "box",
        "account_family_label": "",
        "amount_charges": None,
        "amount_charges_label": "Montant non charge",
        "amount_state": "missing",
        "invoice_count": 0,
        "matched_invoice_count": 0,
        "matched_ratio": 0,
        "matched_ratio_label": "A calculer",
        "unmatched_invoice_count": 0,
        "missing_pieces_count": 0,
        "ecart_amount": None,
        "ecart_label": "Aucun ecart calcule",
        "ecart_state": "unknown",
        "last_invoice_label": "Date non lue",
        "last_invoice_href": _route_href("/comptes", tab="pieces"),
        "status": "empty",
        "status_label": COMPTES_STATUS_LABELS["empty"],
        "status_detail": "Generer ou importer les sorties ComptaScope pour commencer le controle.",
        "status_tone": "info",
        "alert_count": 0,
        "p1_count": 0,
        "p2_count": 0,
        "ok_count": 0,
        "question_count": 0,
        "ag_included": False,
        "next_action_label": "Generer ou importer les sorties ComptaScope pour cet exercice.",
        "href": _route_href("/comptes"),
        "is_selected": True,
        "novice_summary": "Aucun controle comptes charge pour cet exercice.",
        "controls_summary": {
            "conforme": "Aucun point conforme charge.",
            "a_confirmer": "Aucun point a confirmer charge.",
            "bloquant": "Aucun point prioritaire charge.",
        },
        "alerts": [],
        "pieces": [],
        "questions": [],
        "ag_section": {
            "title": f"Rapport AG comptes {year}",
            "include_in_ag_report": False,
            "scope_label": "Aucun point inclus",
            "notes": [],
            "href": _route_href("/comptes", tab="rapport-ag"),
        },
        "history": [],
        "subcategories": [],
        "source_rows": [],
        "diffusion": {
            "status": "local_only",
            "label": "Prive local",
            "reason": "Aucune donnee comptable exploitable n'est chargee.",
            "allowed_audience": "Conseil syndical",
            "blocked_by": [],
        },
        "memory_note": "Relancer le controle apres import des sorties ComptaScope.",
    }


def _comptes_status_from_counts(p1_count: int, p2_count: int, missing_count: int, ok_count: int, total: int) -> str:
    if p1_count:
        return "p1"
    if p2_count:
        return "p2"
    if missing_count and not ok_count:
        return "missing"
    if total:
        return "ok"
    return "unknown"


def _comptes_status_detail(status: str, matched: int, total: int, missing: int) -> str:
    if status == "p1":
        return "Au moins un point doit etre traite avant AG avec une preuve attendue."
    if status == "p2":
        return "Rapprochement plausible ou piece candidate a confirmer avec le syndic."
    if status == "missing":
        return "Piece ou justificatif manquant pour conclure le controle."
    if status == "ok":
        return f"{matched}/{total} pieces disposent d'une preuve rattachee."
    return "Categorie a qualifier a partir des sorties disponibles."


def _comptes_tabs(selected: dict[str, object]) -> list[dict[str, object]]:
    category_id = str(selected.get("category_id") or "")
    counts = {
        "detail": int(selected.get("alert_count") or 0),
        "pieces": len(selected.get("pieces", [])) if isinstance(selected.get("pieces"), list) else 0,
        "questions": len(selected.get("questions", [])) if isinstance(selected.get("questions"), list) else 0,
        "rapport-ag": 1 if selected.get("ag_included") else 0,
    }
    labels = {
        "detail": "Detail",
        "pieces": "Pieces",
        "questions": "Questions au syndic",
        "rapport-ag": "Rapport AG",
    }
    return [
        {
            "id": tab_id,
            "label": labels[tab_id],
            "count": counts[tab_id],
            "is_active": tab_id == "detail",
            "href": _route_href("/comptes", categorie=category_id, tab=tab_id) if category_id else _route_href("/comptes", tab=tab_id),
        }
        for tab_id in ["detail", "pieces", "questions", "rapport-ag"]
    ]


def _comptes_facet_options(
    field: str,
    rows: list[dict[str, object]],
    *,
    route_field: str | None = None,
    labels: dict[str, str] | None = None,
) -> list[dict[str, object]]:
    counts = Counter(str(row.get(field, "") or "non renseigne") for row in rows)
    options: list[dict[str, object]] = []
    for value, count in sorted(counts.items(), key=lambda item: (item[0] == "non renseigne", item[0])):
        option_label = (labels or {}).get(value, value)
        options.append(
            {
                "value": value,
                "label": _public_text(option_label, "non renseigne"),
                "count": count,
                "href": _route_href("/comptes", **{route_field or field: value}),
                "is_active": False,
            }
        )
    return options


def _comptes_ag_note(category: dict[str, object]) -> dict[str, object]:
    category_id = str(category.get("category_id") or "")
    return {
        "note_id": _stable_action_id("NOTE-COMP", 0, category_id, str(category.get("status", ""))),
        "category_id": category_id,
        "author_label": "Conseil syndical",
        "created_on_label": "A completer",
        "text": _public_text(
            category.get("next_action_label"),
            "Point a relire avant diffusion aux coproprietaires.",
        ),
        "diffusion_level": "to_review" if category.get("status") in {"p1", "p2", "missing"} else "ag_public",
        "related_alert_ids": [],
        "related_question_ids": [],
        "href": _route_href("/comptes", categorie=category_id, tab="rapport-ag"),
    }


def _comptes_ag_report(
    year: int,
    categories: list[dict[str, object]],
    alerts: list[dict[str, object]],
    pieces: list[dict[str, object]],
    questions: list[dict[str, object]],
) -> dict[str, object]:
    included = [category for category in categories if category.get("ag_included")]
    excluded = [category for category in categories if not category.get("ag_included")]
    p1_points = [alert for alert in alerts if alert.get("priority") == "P1"]
    p2_points = [alert for alert in alerts if alert.get("priority") == "P2"]
    ok_points = [piece for piece in pieces if piece.get("proof_state") == "verified"][:12]
    missing_pieces = [piece for piece in pieces if piece.get("proof_state") == "missing"]
    open_questions = [question for question in questions if question.get("status") != "closed"]
    notes = [_comptes_ag_note(category) for category in included[:12]]
    preview_lines = [
        f"# Controle des comptes - AG {year}",
        "",
        f"- Points a traiter: {len(p1_points)}",
        f"- Points a confirmer: {len(p2_points)}",
        f"- Pieces manquantes: {len(missing_pieces)}",
        f"- Questions syndic ouvertes: {len(open_questions)}",
    ]
    if included:
        preview_lines.append("")
        preview_lines.append("## Categories a citer")
        for category in included[:8]:
            preview_lines.append(f"- {category.get('label')}: {category.get('status_label')} - {category.get('next_action_label')}")
    diffusion_status = "warning" if p1_points or p2_points or open_questions else "ok"
    return {
        "title": f"Rapport AG controle des comptes {year}",
        "scope_label": "Points ouverts et preuves utiles",
        "generated_on_label": f"Situation {year}",
        "included_categories": included,
        "excluded_categories": [
            {
                "category_id": category.get("category_id"),
                "label": category.get("label"),
                "reason": "Non prioritaire pour le rapport AG",
                "href": category.get("href"),
            }
            for category in excluded
        ],
        "p1_points": p1_points,
        "p2_points": p2_points,
        "ok_with_proof_points": ok_points,
        "missing_pieces": missing_pieces,
        "open_questions": open_questions,
        "notes": notes,
        "preview_markdown": "\n".join(preview_lines),
        "diffusion_status": diffusion_status,
        "diffusion_label": "A relire avant export" if diffusion_status == "warning" else "Export possible",
        "blocked_by": [],
        "export_href": _route_href("/comptes", export="rapport-ag"),
        "edit_href": _route_href("/comptes", tab="rapport-ag"),
    }
