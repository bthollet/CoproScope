import csv
import re
from collections import Counter
from pathlib import Path
from typing import Any, Mapping

from ..modules import suggestionops, suggestionview


STATUS_LABELS = {
    suggestionops.SUGGESTION_STATUS_REVIEW: "a revoir",
    suggestionops.SUGGESTION_STATUS_DISMISSED: "ecartee",
    suggestionops.SUGGESTION_STATUS_TRANSFORMED: "deja transformee",
}

REVIEW_LABELS = {
    suggestionops.REVIEW_PENDING: "revue a faire",
    suggestionops.REVIEW_ACCEPTED: "revue acceptee",
    suggestionops.REVIEW_REJECTED: "revue refusee",
    suggestionops.REVIEW_NEEDS_MORE_PROOF: "preuve a completer",
}

FORBIDDEN_PATTERNS = (
    re.compile(r"(?<![A-Za-z])[A-Za-z]:[\\/][^\s|,;`)]*"),
    re.compile(r"file://\S+", re.IGNORECASE),
    re.compile(r"(?:^|[\s`'\"(])(?:raw|restricted|logs|private)[\\/]\S*", re.IGNORECASE),
)


def register_suggestions_routes(
    app: Any,
    templates: Any,
    context: Any,
    year: int,
    require_token: Any,
    html_response: Any,
) -> None:
    from fastapi import Request as FastAPIRequest

    @app.get("/suggestions", response_class=html_response)
    def suggestions(request: FastAPIRequest):
        require_token(request)
        view = build_suggestions_view(instance=getattr(app.state, "instance", None), year=year)
        return templates.TemplateResponse(
            request=request,
            name="suggestions.html",
            context=context(request, "suggestionops", model=view["shell_model"], suggestions=view),
        )


def build_suggestions_view(instance: Any | None = None, year: int = 2025) -> dict[str, Any]:
    if isinstance(instance, int) and year == 2025:
        year = instance
        instance = None
    suggestions, reviews, source_label = _load_sources(instance, year)
    cards = suggestionview.suggestion_cards_to_dicts(suggestionview.build_suggestion_cards(suggestions, reviews))
    card_rows = [_card_view(card, source_label=source_label) for card in cards]
    suggestion_rows = [_suggestion_row(item, reviews, source_label=source_label) for item in suggestions]
    review_counts = Counter(row["review_state"] for row in suggestion_rows)
    destination_counts = Counter(row["destination_label"] for row in card_rows)
    guardrails = [
        _entry("Preuve obligatoire", "Une suggestion sans preuve reste cachee ou a completer."),
        _entry("Revue humaine", "Aucune destination n'est active sans revue acceptee."),
        _entry("Aucun effet automatique", "La page ne cree pas d'action, demande, point, indicateur ou export."),
    ]
    return {
        "title": "Suggestions utiles",
        "headline": "Suggestions sourcees, preuves et suites possibles",
        "notice": _notice(source_label),
        "status": {
            "label": "Suggestions a relire",
            "summary": "Chaque carte affiche une source, une preuve, une revue humaine et une destination possible.",
            "cta": "Relire les suggestions",
        },
        "summary": [
            _metric("Suggestions sourcees", str(len(suggestion_rows)), "Lignes avec source, preuve et prochaine action."),
            _metric("Cartes affichables", str(len(card_rows)), "Suggestions acceptees par revue humaine."),
            _metric("Preuves a completer", str(review_counts.get(suggestionops.REVIEW_NEEDS_MORE_PROOF, 0)), "Suggestions qui restent a documenter."),
            _metric("Destinations", str(len(destination_counts)), "Types de suites possibles apres validation."),
        ],
        "cards": card_rows,
        "suggestions": suggestion_rows,
        "review_counts": _count_rows(review_counts, REVIEW_LABELS),
        "destination_counts": _count_rows(destination_counts, {}),
        "definitions": [
            _entry("Suggestion", "Piste utile issue d'une preuve ou d'un registre."),
            _entry("Source", "Module ou registre qui explique d'ou vient la piste."),
            _entry("Preuve", "Reference lisible qui justifie de regarder la piste."),
            _entry("Revue humaine", "Validation explicite avant toute suite."),
            _entry("Destination", "Action, demande, point, indicateur ou export possible."),
            _entry("Effet automatique", "Creation ou envoi bloque dans cette iteration."),
        ],
        "actions": [
            _action("Voir actions", "Disponible", "Ouvrir la file des actions avant creation humaine.", "/actions?scope=suggestions"),
            _action("Voir demandes syndic", "Disponible", "Relire les demandes avant toute relance.", "/demandes?source=suggestion"),
            _action("Voir indicateurs", "Disponible", "Verifier si une carte de pilotage existe deja.", "/pilotage"),
            _action("Voir preuves manquantes", "Disponible", "Relire les pieces attendues.", "/pieces?proof=missing"),
            _action("Creer action automatiquement", "Bloquee", "Une action doit etre creee ou validee par un humain.", ""),
            _action("Envoyer demande", "Bloquee", "Aucun envoi depuis CoproScope.", ""),
            _action("Exporter sans revue", "Bloquee", "Un export demande une revue de diffusion.", ""),
        ],
        "boundaries": guardrails,
        "guardrails": guardrails,
        "version_log": [
            "Vue Suggestions utiles branchee sur suggestionops et suggestionview.",
            "Exemples FICTIFS utilises si aucun registre derive n'existe.",
            "Transformations automatiques bloquees dans cette iteration.",
        ],
        "shell_model": _shell_model(year),
    }


def _load_sources(instance: Any | None, year: int) -> tuple[list[Any], list[Any], str]:
    local = _local_rows(instance)
    if local[0]:
        suggestions = [suggestionops.normalize_suggestion(row) for row in local[0]]
        reviews = [suggestionops.normalize_review(row) for row in local[1]]
        return suggestions, reviews, "Synthese derivee"
    suggestions = [suggestionops.normalize_suggestion(row) for row in _fallback_suggestions(year)]
    reviews = [suggestionops.normalize_review(row) for row in _fallback_reviews()]
    return suggestions, reviews, "FICTIF"


def _local_rows(instance: Any | None) -> tuple[list[dict[str, str]], list[dict[str, str]]]:
    reports_dir = _reports_dir(instance)
    if reports_dir is None:
        return [], []
    suggestions = _read_csv_rows(reports_dir / "suggestions_utiles.csv")
    reviews = _read_csv_rows(reports_dir / "suggestions_reviews.csv")
    return suggestions, reviews


def _reports_dir(instance: Any | None) -> Path | None:
    if instance is None:
        return None
    try:
        return Path(instance.artifact("reports_dir"))
    except (AttributeError, KeyError, TypeError, ValueError, OSError):
        return None


def _read_csv_rows(path: Path) -> list[dict[str, str]]:
    if not path.exists() or not path.is_file():
        return []
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return [dict(row) for row in csv.DictReader(handle)]


def _fallback_suggestions(year: int) -> list[dict[str, str]]:
    return [
        {
            "suggestion_id": "SUG-FICTIF-01",
            "title": "Relancer le syndic sur l'attestation assurance",
            "why": "La piece attendue n'est pas presente dans la synthese documentaire.",
            "proof": f"MATRICE-PREUVES-{year}#assurance",
            "source": "DocOps FICTIF",
            "next_action": "Relire la preuve puis preparer une demande au syndic.",
            "impact": "fort",
            "effort": "faible",
            "confidence": "haute",
            "public": "conseil_syndical",
            "transformations": "demande;action;point",
        },
        {
            "suggestion_id": "SUG-FICTIF-02",
            "title": "Creer un indicateur de demandes en retard",
            "why": "Plusieurs demandes fictives depassent l'echeance de suivi.",
            "proof": f"REG-DEMANDES-{year}",
            "source": "SyndicOps FICTIF",
            "next_action": "Verifier la source avant d'ajouter une carte de pilotage.",
            "impact": "moyen",
            "effort": "moyen",
            "confidence": "moyenne",
            "public": "conseil_syndical",
            "transformations": "indicateur;action",
        },
        {
            "suggestion_id": "SUG-FICTIF-03",
            "title": "Clarifier la diffusion du pack passation",
            "why": "La synthese fictive contient des elements a relire avant partage.",
            "proof": f"PRIVACY-FICTIF-{year}",
            "source": "PrivacyOps FICTIF",
            "next_action": "Completer la preuve avant export.",
            "impact": "fort",
            "effort": "moyen",
            "confidence": "a_verifier",
            "public": "conseil_syndical",
            "transformations": "export;point",
        },
    ]


def _fallback_reviews() -> list[dict[str, str]]:
    return [
        {
            "review_id": "REV-FICTIF-01",
            "suggestion_id": "SUG-FICTIF-01",
            "reviewer": "Conseil syndical fictif",
            "decision": "accepted",
            "rationale": "Preuve lisible et suite prudente.",
            "selected_outcome_type": "demande",
            "public": "commission_assurance",
        },
        {
            "review_id": "REV-FICTIF-02",
            "suggestion_id": "SUG-FICTIF-02",
            "reviewer": "",
            "decision": "pending",
            "rationale": "",
            "selected_outcome_type": "indicateur",
        },
        {
            "review_id": "REV-FICTIF-03",
            "suggestion_id": "SUG-FICTIF-03",
            "reviewer": "Conseil syndical fictif",
            "decision": "needs_more_proof",
            "rationale": "Preuve de diffusion incomplete.",
            "selected_outcome_type": "export",
        },
    ]


def _card_view(card: Mapping[str, Any], *, source_label: str) -> dict[str, Any]:
    return {
        "card_id": _safe(card.get("card_id"), 80),
        "suggestion_id": _safe(card.get("suggestion_id"), 60),
        "title": _safe(card.get("title"), 90),
        "why": _safe(card.get("why"), 140),
        "proof": _safe(card.get("proof"), 90),
        "source": _safe(card.get("source"), 80),
        "evidence": _safe(card.get("evidence"), 110),
        "next_action": _safe(card.get("next_action"), 140),
        "diffusion": _safe(card.get("diffusion"), 60),
        "confidence": _safe(card.get("confidence"), 40),
        "effort": _safe(card.get("effort"), 40),
        "destination": _safe(card.get("destination"), 40),
        "destination_label": _safe(card.get("destination_label"), 60),
        "available_destinations": ", ".join(_safe(item, 30) for item in card.get("available_destinations", ())),
        "source_label": source_label,
    }


def _suggestion_row(suggestion: Any, reviews: list[Any], *, source_label: str) -> dict[str, Any]:
    review = next((item for item in reviews if item.suggestion_id == suggestion.suggestion_id), None)
    review_state = review.decision if review else suggestionops.REVIEW_PENDING
    return {
        "suggestion_id": _safe(suggestion.suggestion_id, 60),
        "title": _safe(suggestion.title, 90),
        "why": _safe(suggestion.why, 130),
        "proof": _safe(suggestion.proof, 90),
        "source": _safe(suggestion.source, 80),
        "next_action": _safe(suggestion.next_action, 130),
        "status_label": STATUS_LABELS.get(suggestion.status, "a revoir"),
        "review_state": review_state,
        "review_label": REVIEW_LABELS.get(review_state, "revue a faire"),
        "destination_label": _safe(getattr(review, "selected_outcome_type", ""), 50) or "a choisir",
        "source_label": source_label,
    }


def _notice(source_label: str) -> str:
    if source_label == "Synthese derivee":
        return "Synthese derivee: aucune transformation automatique."
    return "Scenario FICTIF: suggestions de demonstration."


def _safe(value: Any, limit: int) -> str:
    text = re.sub(r"\s+", " ", str(value or "")).strip()
    for pattern in FORBIDDEN_PATTERNS:
        text = pattern.sub("[retire]", text)
    text = re.sub(r"`[^`]*(?:raw|restricted|logs|private|token|secret)[^`]*`", "[retire]", text, flags=re.IGNORECASE)
    if len(text) <= limit:
        return text
    return f"{text[: limit - 1].rstrip()}..."


def _metric(label: str, value: str, detail: str) -> dict[str, str]:
    return {"label": label, "value": value, "detail": detail}


def _entry(label: str, detail: str) -> dict[str, str]:
    return {"label": label, "detail": detail}


def _action(label: str, state: str, reason: str, href: str) -> dict[str, str]:
    return {"label": label, "state": state, "reason": reason, "href": href, "enabled": "true" if href else "false"}


def _count_rows(counts: Counter[str], labels: dict[str, str]) -> list[dict[str, Any]]:
    return [{"key": key, "label": labels.get(key, key), "count": count} for key, count in counts.items() if count]


def _shell_model(year: int) -> dict[str, Any]:
    return {
        "instance": {"id": "FICTIF", "name": "Copropriete FICTIVE", "root": "", "year": year},
        "ux": {
            "shell": {
                "app_title": "CoproScope",
                "page_title": "Suggestions utiles",
                "active_page": "suggestionops",
                "search_placeholder": "Rechercher une suggestion, une preuve ou une suite...",
                "notification_count": 0,
                "sharing_mode_label": "Revue locale",
                "sharing_mode_status": "Aucune creation automatique",
            }
        },
        "action_summary": {"total": "", "accounting": "", "scope_counts": {}},
        "kpis": {"actions": "", "doc_requests": "", "decisions": "", "privacy_reviews": ""},
    }
