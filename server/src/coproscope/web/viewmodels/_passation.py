from __future__ import annotations

from ._runtime import *

def _build_passation_export_model(
    *,
    year: int,
    memoire: dict[str, object],
    priority_views: dict[str, object],
    action_detail: dict[str, object],
) -> dict[str, object]:
    memoire_summary = memoire.get("summary") if isinstance(memoire.get("summary"), dict) else {}
    memoire_export = memoire.get("export") if isinstance(memoire.get("export"), dict) else {}
    memoire_pack = memoire.get("pack") if isinstance(memoire.get("pack"), dict) else {}
    late_view = priority_views.get("late_actions") if isinstance(priority_views.get("late_actions"), dict) else {}
    missing_view = priority_views.get("missing_pieces") if isinstance(priority_views.get("missing_pieces"), dict) else {}
    followup_view = priority_views.get("syndic_followups") if isinstance(priority_views.get("syndic_followups"), dict) else {}
    late_actions = _list_of_dicts(late_view.get("items"))
    missing_pieces = _list_of_dicts(missing_view.get("items"))
    followups = _list_of_dicts(followup_view.get("items"))
    timeline = _list_of_dicts(memoire.get("timeline"))
    transmit = memoire.get("transmit") if isinstance(memoire.get("transmit"), dict) else {}
    transmit_items = _list_of_dicts(transmit.get("items"))
    raw_omissions = _list_of_dicts(memoire_export.get("omissions") or memoire_pack.get("omissions"))
    omitted_items = [
        {
            "id": _public_text(item.get("id"), _stable_action_id("OMIT", index, str(item.get("label", "")))),
            "label": _public_text(item.get("label"), "Element exclu ou masque"),
            "reason": _public_text(item.get("reason"), "Diffusion a verifier."),
            "type_label": _public_text(item.get("type_label"), "Element de passation"),
            "review_href": _public_href(item.get("href"), _route_href("/confidentialite")),
        }
        for index, item in enumerate(raw_omissions, start=1)
    ]
    if not omitted_items and missing_pieces:
        omitted_items.append(
            {
                "id": "omission-preuves-manquantes",
                "label": "Preuves manquantes",
                "reason": "Les preuves absentes sont listees comme points a obtenir.",
                "type_label": "Preuve",
                "review_href": _route_href("/pieces", proof="missing"),
            }
        )
    diffusion_limited_count = int(memoire_summary.get("diffusion_limited_count") or 0)
    missing_count = len(missing_pieces)
    blocker_rows: list[dict[str, object]] = []
    if diffusion_limited_count:
        blocker_rows.append(
            {
                "id": "diffusion-a-verifier",
                "label": "Diffusion a verifier",
                "detail": f"{diffusion_limited_count} element(s) demandent une relecture avant export complet.",
                "href": _route_href("/confidentialite", scope="export", export="passation"),
            }
        )
    if missing_count:
        blocker_rows.append(
            {
                "id": "preuves-manquantes",
                "label": "Preuves manquantes",
                "detail": f"{missing_count} preuve(s) ou piece(s) seront listees comme points a obtenir.",
                "href": _route_href("/pieces", proof="missing"),
            }
        )
    can_export = not blocker_rows
    downloads = {
        "requires_preview": True,
        "previewed": True,
        "can_download": can_export,
        "download_disabled_reason": "" if can_export else "Verifier la diffusion et les preuves manquantes.",
    }
    format_specs = [
        ("txt", "TXT", "Synthese lisible et copiable.", "/exports/passation.txt"),
        ("json", "JSON", "Export structure pour audit ou reprise.", "/exports/passation.json"),
    ]
    formats = [
        {
            "id": format_id,
            "label": label,
            "description": description,
            "href": _route_href(path, audience="conseil_syndical"),
            "enabled": can_export,
            "disabled_reason": "" if can_export else "Verifier la diffusion avant export.",
        }
        for format_id, label, description, path in format_specs
    ]
    checklist = [
        {
            "id": "audience",
            "label": "Public vise choisi",
            "status": "done",
            "status_label": "Pret",
            "detail": "Version conseil syndical.",
        },
        {
            "id": "restrictions",
            "label": "Diffusion relue",
            "status": "blocked" if diffusion_limited_count else "done",
            "status_label": "A verifier" if diffusion_limited_count else "Pret",
            "detail": "Relire les elements limites avant partage." if diffusion_limited_count else "Aucun blocage de diffusion signale.",
            "href": _route_href("/confidentialite", scope="export", export="passation"),
        },
        {
            "id": "missing-proofs",
            "label": "Preuves manquantes visibles",
            "status": "blocked" if missing_count else "done",
            "status_label": "A obtenir" if missing_count else "Pret",
            "detail": f"{missing_count} piece(s) ou preuve(s) a obtenir." if missing_count else "Aucune preuve manquante prioritaire.",
            "href": _route_href("/pieces", proof="missing"),
        },
        {
            "id": "watermark",
            "label": "Mention export derive presente",
            "status": "done",
            "status_label": "Pret",
            "detail": "Export derive, non source collaborative.",
        },
    ]
    selected_action_id = ""
    selected = action_detail.get("selected") if isinstance(action_detail.get("selected"), dict) else {}
    if isinstance(selected, dict):
        selected_action_id = _public_text(selected.get("id"), "")
    sections_included = [
        {"id": "synthese", "label": "Synthese", "count": 1, "included": True},
        {"id": "events", "label": "Evenements memoire", "count": len(timeline), "included": True},
        {"id": "actions", "label": "Actions ouvertes", "count": len(late_actions), "included": True},
        {"id": "documents", "label": "Documents de passation", "count": len(transmit_items), "included": True},
        {"id": "proofs", "label": "Preuves a obtenir", "count": missing_count, "included": True},
        {"id": "restrictions", "label": "Restrictions et omissions", "count": diffusion_limited_count + len(omitted_items), "included": True},
    ]
    excluded_or_blocked = [
        {
            "id": _public_text(item.get("id"), _stable_action_id("BLOCK", index, str(item.get("label", "")))),
            "label": _public_text(item.get("label"), "Element a verifier"),
            "reason": _public_text(item.get("reason") or item.get("detail"), "Diffusion ou preuve a verifier."),
            "href": _public_href(item.get("review_href") or item.get("href"), _route_href("/confidentialite", scope="export", export="passation")),
        }
        for index, item in enumerate([*omitted_items, *blocker_rows], start=1)
    ]
    return {
        "watermark": "Export derive, non source collaborative",
        "source_of_truth": False,
        "context": {
            "route": "/exports/passation",
            "title": "Apercu de passation",
            "subtitle": "Verifiez le contenu, les diffusions limitees et les omissions avant export.",
            "source_of_truth": False,
            "watermark": "Export derive, non source collaborative",
            "role_label": "Conseil syndical",
            "as_of_label": f"Situation {year}",
        },
        "sections_included": sections_included,
        "scope": {
            "period_label": "10 ans",
            "selected_scope": "handover",
            "selected_event_id": None,
            "selected_action_id": selected_action_id or None,
            "include_open_actions": True,
            "include_memory_events": True,
            "include_key_documents": True,
            "include_limited_documents": False,
            "hrefs": {
                "all": _route_href("/exports/passation", scope="handover"),
                "open_actions": _route_href("/exports/passation", scope="open-actions"),
                "event": _route_href("/exports/passation", scope="event"),
                "action": _route_href("/exports/passation", scope="action", selected=selected_action_id),
            },
        },
        "audience": {
            "selected": "conseil_syndical",
            "selected_label": "Conseil syndical",
            "options": [
                {
                    "id": "conseil_syndical",
                    "label": "Conseil syndical",
                    "description": "Version de travail interne avec limites visibles.",
                    "href": _route_href("/exports/passation", audience="conseil_syndical"),
                },
                {
                    "id": "diffusable",
                    "label": "Synthese diffusable",
                    "description": "Version plus courte, avec elements sensibles exclus ou masques.",
                    "href": _route_href("/exports/passation", audience="diffusable"),
                },
            ],
        },
        "summary": {
            "included_events_count": len(timeline),
            "open_topics_count": int(memoire_summary.get("open_topics_count") or 0),
            "included_actions_count": len(late_actions),
            "included_documents_count": len(transmit_items),
            "missing_proofs_count": missing_count,
            "diffusion_limited_count": diffusion_limited_count,
            "omitted_items_count": len(omitted_items),
            "can_export": can_export,
            "can_export_label": "Pret a exporter apres apercu" if can_export else "A verifier avant export",
            "last_updated_label": f"Situation {year}",
        },
        "checklist": checklist,
        "preview": {
            "title": "Passation conseil syndical",
            "intro": "Synthese derivee des actions, evenements memoire et documents utiles.",
            "sections": [
                {
                    "id": "synthese",
                    "title": "Synthese",
                    "items": [
                        f"{int(memoire_summary.get('open_topics_count') or 0)} sujets ouverts",
                        f"{missing_count} preuves manquantes",
                        f"{diffusion_limited_count} diffusions a verifier",
                    ],
                },
                {
                    "id": "actions",
                    "title": "Actions ouvertes",
                    "items": [str(item.get("title", "Action ouverte")) for item in late_actions[:8]],
                    "empty_label": "Aucune action ouverte dans ce perimetre.",
                },
                {
                    "id": "relances",
                    "title": "Relances syndic",
                    "items": [str(item.get("title", "Relance syndic")) for item in followups[:8]],
                    "empty_label": "Aucune relance syndic dans ce perimetre.",
                },
            ],
        },
        "included": {
            "events": timeline[:8],
            "actions": late_actions[:8],
            "documents": transmit_items[:8],
            "proofs": [item for item in missing_pieces[:8] if item.get("candidate_docs")],
        },
        "omitted": {
            "items": omitted_items,
            "summary_label": f"{len(omitted_items)} element(s) exclus, masques ou signales.",
        },
        "restrictions": {
            "highest_level": "conseil_syndical" if diffusion_limited_count else "diffusable",
            "label": "Diffusion limitee" if diffusion_limited_count else "Diffusion a relire",
            "reason": "Le pack contient des sujets ouverts ou des pieces a arbitrer." if diffusion_limited_count else "Relire avant partage externe.",
            "review_href": _route_href("/confidentialite", scope="export", export="passation"),
        },
        "blockers": blocker_rows,
        "excluded_or_blocked": excluded_or_blocked,
        "formats_available": formats,
        "formats": formats,
        "downloads": downloads,
        "audit": {
            "generated_at_label": f"Situation {year}",
            "generated_from": "Memoire, actions, preuves et decisions de diffusion",
            "source_of_truth": False,
            "omissions_included": True,
        },
        "empty_states": {
            "no_content": {
                "is_visible": not bool(timeline or late_actions or transmit_items),
                "label": "Aucun contenu de passation disponible. Ajoutez des evenements memoire ou des actions ouvertes.",
                "href": _route_href("/chantiers"),
            },
            "blocked": {
                "is_visible": bool(blocker_rows),
                "label": "Export bloque: relisez la diffusion ou choisissez une synthese diffusable.",
                "href": _route_href("/confidentialite", scope="export", export="passation"),
            },
        },
    }
