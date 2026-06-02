import csv
import hashlib
import re
from collections import Counter
from pathlib import Path
from typing import Any, Iterable, Mapping


STATUS_LABELS = {
    "A_DEMANDER": "a demander",
    "A_VERIFIER": "a verifier",
    "EN_SUIVI": "en suivi",
    "PREUVE_MANQUANTE": "preuve manquante",
    "ECHEANCE": "echeance a verifier",
    "OK": "suivi stable",
}

STATUS_ALIASES = {
    "ABSENT": "PREUVE_MANQUANTE",
    "MANQUANT": "PREUVE_MANQUANTE",
    "A_PRODUIRE": "A_DEMANDER",
    "A_DEMANDER": "A_DEMANDER",
    "A_VERIFIER": "A_VERIFIER",
    "INCOMPLET": "A_VERIFIER",
    "PRESENT": "A_VERIFIER",
    "EXPIRE": "ECHEANCE",
    "ECHEANCE": "ECHEANCE",
    "OK": "OK",
    "VALIDE": "OK",
}

FAMILY_LABELS = {
    "assurance": "Assurance",
    "maintenance": "Maintenance",
    "syndic": "Syndic",
    "travaux": "Travaux",
    "charges": "Charges",
    "autre": "Contrat",
}

CONTRACT_KEYWORDS = (
    "contrat",
    "assurance",
    "attestation",
    "maintenance",
    "entretien",
    "syndic",
    "police",
    "devis comparatif",
)


def register_contractops_routes(
    app: Any,
    templates: Any,
    context: Any,
    year: int,
    require_token: Any,
    html_response: Any,
) -> None:
    from fastapi import Request as FastAPIRequest

    @app.get("/contrats", response_class=html_response)
    def contrats(request: FastAPIRequest):
        require_token(request)
        view = build_contractops_view(instance=getattr(app.state, "instance", None), year=year)
        return templates.TemplateResponse(
            request=request,
            name="contracts.html",
            context=context(request, "contractops", model=view["shell_model"], contracts=view),
        )


def build_contractops_view(instance: Any | None = None, year: int = 2025) -> dict[str, Any]:
    """Return a ContractOps view with fictive rows or privacy-safe derived rows."""
    if isinstance(instance, int) and year == 2025:
        year = instance
        instance = None
    rows = _contract_rows(instance, year)
    status_counts = Counter(row["status"] for row in rows)
    family_counts = Counter(row["family"] for row in rows)
    open_rows = [row for row in rows if row["status"] != "OK"]
    attestations = [row for row in rows if _has_words(row["proof_expected"], ("attestation", "assurance"))]
    guardrails = [
        _entry("Synthese derivee", "La page ne sert pas les contrats, attestations ou originaux."),
        _entry("Validation humaine", "Aucun rappel juridique ni mise en concurrence n'est declenche."),
        _entry("References opaques", "Les liens pointent vers des vues locales tokenisees, pas vers des fichiers bruts."),
    ]
    return {
        "title": "Contrats et obligations",
        "headline": "Contrats, echeances et preuves attendues",
        "notice": _notice(instance, rows),
        "status": {
            "label": "Obligations a verifier",
            "summary": (
                "Chaque ligne relie un contrat, une obligation, une echeance, "
                "une preuve attendue et les modules charges, travaux ou incidents."
            ),
            "cta": "Verifier une obligation",
        },
        "summary": [
            _metric("Obligations ouvertes", str(len(open_rows)), "Points qui demandent une preuve ou une verification."),
            _metric("Attestations attendues", str(len(attestations)), "Assurance, entretien ou attestation a rattacher."),
            _metric("Echeances visibles", str(sum(1 for row in rows if row["due_at"])), "Dates a relire avant relance humaine."),
            _metric("Contrats suivis", str(len(rows)), "Contrats ou attestations visibles dans la synthese."),
        ],
        "definitions": [
            _entry("Contrat", "Accord ou police a suivre: syndic, assurance, maintenance ou travaux."),
            _entry("Obligation", "Ce qui doit etre fait, fourni ou controle selon le contrat."),
            _entry("Attestation", "Preuve annuelle ou ponctuelle demandee au syndic ou prestataire."),
            _entry("Echeance", "Date a surveiller avant reconduction, expiration ou relance."),
            _entry("Clause clef", "Point du contrat utile au controle: duree, prix, assurance, sortie."),
            _entry("Preuve attendue", "Document derive, facture, attestation ou validation a rattacher."),
        ],
        "contracts": rows,
        "status_counts": _count_rows(status_counts, STATUS_LABELS),
        "family_counts": _count_rows(family_counts, FAMILY_LABELS),
        "decision_gates": [
            _entry("Verifier la source", "Lire le contrat ou la synthese derivee avant toute conclusion."),
            _entry("Nommer la preuve", "Une obligation ne se cloture pas sans attestation ou trace rattachee."),
            _entry("Relier les modules", "Charges, travaux et incidents doivent pointer vers les memes preuves."),
            _entry("Arbitrer hors outil", "Relance juridique et mise en concurrence restent externes et humaines."),
        ],
        "actions": [
            _action("Voir pieces contrats", "Disponible", "Retrouver les pieces contractuelles attendues.", "/pieces?proof=missing&group=contrats"),
            _action("Voir charges liees", "Disponible", "Controler factures et charges rattachees.", "/comptes?scope=contrats"),
            _action("Voir travaux lies", "Disponible", "Suivre les contrats de travaux ou maintenance.", "/travaux?scope=contrats"),
            _action("Voir incidents lies", "Disponible", "Verifier sinistres et assurances rattaches.", "/incidents?scope=contrats"),
            _action("Ajouter preuve locale", "Disponible", "Deposer une preuve derivee ou biffee.", "/depot?intent=document&return=contrats"),
            _action("Rappel juridique automatique", "Bloquee", "Aucune relance contractuelle sans validation humaine.", ""),
            _action("Lancer mise en concurrence", "Bloquee", "Decision et dossier a preparer hors automatisme.", ""),
            _action("Transmettre attestation", "Bloquee", "Aucun envoi depuis CoproScope.", ""),
        ],
        "boundaries": guardrails,
        "guardrails": guardrails,
        "version_log": [
            "Vue ContractOps creee pour obligations, attestations et echeances.",
            "Exemples FICTIFS utilises si aucune synthese documentaire derivee n'existe.",
            "Rappels juridiques, envois et mise en concurrence sans validation humaine bloques.",
        ],
        "shell_model": _shell_model(year),
    }


def _contract_rows(instance: Any | None, year: int) -> list[dict[str, Any]]:
    local_rows = _local_contract_rows(instance)
    if local_rows:
        return local_rows
    return [_row_view(row, index=index, source_label="FICTIF") for index, row in enumerate(_fallback_rows(year), start=1)]


def _local_contract_rows(instance: Any | None) -> list[dict[str, Any]]:
    reports_dir = _reports_dir(instance)
    if reports_dir is None:
        return []
    sources = (
        (reports_dir / "matrice_completude_documentaire.csv", "Synthese derivee"),
        (reports_dir / "pieces_a_demander.csv", "Synthese derivee"),
    )
    rows: list[dict[str, Any]] = []
    for path, source_label in sources:
        for row in _read_csv_rows(path):
            if _looks_like_contract(row):
                rows.append(_row_view(row, index=len(rows) + 1, source_label=source_label))
    return rows[:8]


def _row_view(row: Mapping[str, Any], *, index: int, source_label: str) -> dict[str, Any]:
    title = _first_text(row, ("expected_piece", "expected_label", "subject", "title", "document_type")) or "Contrat a qualifier"
    text = " ".join(_cell(row.get(field)) for field in row)
    family = _family_for(text)
    status = _status(_first_text(row, ("status", "statut", "privacy_review_status")))
    due_at = _first_text(row, ("due_at", "echeance", "deadline", "newest_date", "date_fin")) or _default_due(status)
    proof_expected = _proof_expected(title, text)
    contract_id = _first_text(row, ("contract_id", "proof_id", "request_id", "doc_id")) or title
    return {
        "id": _public_id(contract_id, index),
        "title": _clip(title, 72),
        "family": family,
        "family_label": FAMILY_LABELS.get(family, "Contrat"),
        "provider_label": _provider_label(family),
        "status": status,
        "status_label": STATUS_LABELS.get(status, "a verifier"),
        "obligation": _obligation(title, family),
        "due_at": due_at,
        "clause_key": _clause_key(family),
        "proof_expected": proof_expected,
        "proof_state": _proof_state(status),
        "linked_charge": _linked_charge(family),
        "linked_work": _linked_work(family),
        "linked_incident": _linked_incident(family),
        "next_action": _first_text(row, ("suggested_diligence", "action", "next_action", "reason")) or _next_action(status, family),
        "diffusion": "CS seulement",
        "source_label": source_label,
    }


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


def _fallback_rows(year: int) -> list[dict[str, str]]:
    return [
        {
            "contract_id": "CTR-FICTIF-01",
            "expected_piece": "Contrat entretien ascenseur signe",
            "status": "A_VERIFIER",
            "echeance": f"{year}-06-30",
            "reason": "Verifier duree, prix, assurance et preuve d'intervention.",
        },
        {
            "contract_id": "CTR-FICTIF-02",
            "expected_piece": "Attestation assurance immeuble en cours",
            "status": "ABSENT",
            "echeance": f"{year}-05-31",
            "suggested_diligence": "Demander l'attestation au syndic avant partage large.",
        },
        {
            "contract_id": "CTR-FICTIF-03",
            "expected_piece": "Contrat syndic vote et version signee",
            "status": "A_DEMANDER",
            "echeance": f"{year}-07-01",
            "action": "Rattacher la version signee et verifier la prise d'effet.",
        },
    ]


def _notice(instance: Any | None, rows: Iterable[Mapping[str, Any]]) -> str:
    if instance is not None and any(row.get("source_label") == "Synthese derivee" for row in rows):
        return "Synthese derivee: aucun contrat original servi."
    return "Scenario FICTIF: obligations de demonstration, aucun envoi."


def _looks_like_contract(row: Mapping[str, Any]) -> bool:
    return _has_words(" ".join(_cell(value) for value in row.values()), CONTRACT_KEYWORDS)


def _family_for(text: str) -> str:
    lowered = text.lower()
    if "assurance" in lowered or "attestation" in lowered or "police" in lowered:
        return "assurance"
    if "syndic" in lowered or "mandat" in lowered:
        return "syndic"
    if "travaux" in lowered or "chantier" in lowered or "devis" in lowered:
        return "travaux"
    if "charge" in lowered or "facture" in lowered:
        return "charges"
    if "maintenance" in lowered or "entretien" in lowered or "ascenseur" in lowered:
        return "maintenance"
    return "autre"


def _status(value: str) -> str:
    raw = re.sub(r"[^A-Z0-9]+", "_", value.upper()).strip("_")
    return STATUS_ALIASES.get(raw, "A_VERIFIER")


def _proof_expected(title: str, text: str) -> str:
    if _has_words(f"{title} {text}", ("attestation", "assurance")):
        return "Attestation ou police en cours de validite."
    if _has_words(f"{title} {text}", ("facture", "charges")):
        return "Facture rattachee, contrat ou clause de prix."
    if _has_words(f"{title} {text}", ("travaux", "maintenance", "entretien")):
        return "Contrat signe, bon d'intervention ou PV de reception."
    return "Contrat signe ou synthese de clause a rattacher."


def _obligation(title: str, family: str) -> str:
    if family == "assurance":
        return "Verifier validite, garanties et attestation."
    if family == "syndic":
        return "Verifier prise d'effet, duree et version signee."
    if family == "travaux":
        return "Relier devis, ordre de service et reception."
    if family == "maintenance":
        return "Verifier passages, assurance et prix applique."
    return f"Controler la preuve et la clause utile: {_clip(title, 42)}."


def _provider_label(family: str) -> str:
    return {
        "assurance": "Assureur ou syndic",
        "syndic": "Syndic",
        "travaux": "Entreprise ou maitre d'oeuvre",
        "maintenance": "Prestataire",
        "charges": "Fournisseur",
    }.get(family, "Prestataire a qualifier")


def _clause_key(family: str) -> str:
    return {
        "assurance": "garantie et periode",
        "syndic": "duree et honoraires",
        "travaux": "prix, delai et reception",
        "maintenance": "prix, frequence et assurance",
        "charges": "prix et mode de calcul",
    }.get(family, "clause a qualifier")


def _proof_state(status: str) -> str:
    if status == "OK":
        return "Preuve rattachee a relire"
    if status == "PREUVE_MANQUANTE":
        return "Preuve manquante"
    return "Preuve a verifier"


def _linked_charge(family: str) -> str:
    return "Charges a verifier" if family in {"charges", "maintenance", "syndic", "assurance"} else "Charges possibles"


def _linked_work(family: str) -> str:
    return "Travaux lies" if family in {"travaux", "maintenance"} else "Aucun chantier rattache"


def _linked_incident(family: str) -> str:
    return "Incidents ou sinistres a verifier" if family == "assurance" else "Aucun incident rattache"


def _default_due(status: str) -> str:
    return "echeance a fixer" if status in {"A_DEMANDER", "PREUVE_MANQUANTE", "ECHEANCE"} else ""


def _next_action(status: str, family: str) -> str:
    if status in {"A_DEMANDER", "PREUVE_MANQUANTE"}:
        return "Demander la preuve au syndic puis rattacher une synthese."
    if family == "assurance":
        return "Verifier attestation, garanties et incidents rattaches."
    return "Relire la clause utile puis decider la suite humaine."


def _public_id(value: str, index: int) -> str:
    seed = _cell(value) or f"contract-{index}"
    if seed.upper().startswith(("CTR-", "CONTRAT-")) and not any(part in seed.lower() for part in ("raw", "private")):
        return _clip(seed.upper(), 32)
    digest = hashlib.sha256(seed.encode("utf-8")).hexdigest()[:8].upper()
    return f"CTR-{index:02d}-{digest}"


def _metric(label: str, value: str, detail: str) -> dict[str, str]:
    return {"label": label, "value": value, "detail": detail}


def _entry(label: str, detail: str) -> dict[str, str]:
    return {"label": label, "detail": detail}


def _action(label: str, state: str, reason: str, href: str) -> dict[str, str]:
    return {"label": label, "state": state, "reason": reason, "href": href, "enabled": "true" if href else "false"}


def _count_rows(counts: Counter[str], labels: Mapping[str, str]) -> list[dict[str, Any]]:
    return [{"key": key, "label": labels.get(key, key), "count": count} for key, count in counts.items() if count]


def _first_text(row: Mapping[str, Any], fields: Iterable[str]) -> str:
    for field in fields:
        value = _cell(row.get(field))
        if value:
            return value
    return ""


def _has_words(value: str, words: Iterable[str]) -> bool:
    folded = value.lower()
    return any(word in folded for word in words)


def _cell(value: Any) -> str:
    return re.sub(r"\s+", " ", str(value or "")).strip()


def _clip(value: str, limit: int) -> str:
    text = _cell(value)
    if len(text) <= limit:
        return text
    return f"{text[: limit - 1].rstrip()}..."


def _shell_model(year: int) -> dict[str, Any]:
    return {
        "instance": {"id": "FICTIF", "name": "Copropriete FICTIVE", "root": "", "year": year},
        "ux": {
            "shell": {
                "app_title": "CoproScope",
                "page_title": "Contrats et obligations",
                "active_page": "contractops",
                "search_placeholder": "Rechercher un contrat, une attestation ou une echeance...",
                "notification_count": 0,
                "sharing_mode_label": "Suivi local",
                "sharing_mode_status": "Aucun envoi ni rappel automatique",
            }
        },
        "action_summary": {"total": "", "accounting": "", "scope_counts": {}},
        "kpis": {"actions": "", "doc_requests": "", "decisions": "", "privacy_reviews": ""},
    }
