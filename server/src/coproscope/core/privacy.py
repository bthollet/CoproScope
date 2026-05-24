from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .common import InstanceConfig, load_structured_file


ACCESS_COLLEGES = [
    "C0_Public",
    "C1_Occupants_Usagers",
    "C2_Coproprietaires",
    "C3_Coproprietaire_Concerne",
    "C4_Conseil_Syndical",
    "C5_Syndic_Admin",
    "C6_Prestataire_Mandate",
    "C7_Contentieux_Secret",
    "C8_Restreint_Critique",
]

ACCESS_RANK = {college: index for index, college in enumerate(ACCESS_COLLEGES)}

POLICY_FIELDS = [
    "raw_max_college",
    "derivative_max_college",
    "publication_form",
    "restriction_reasons",
    "personal_data_level",
    "ip_status",
    "ai_processing_ceiling",
    "review_required",
    "policy_confidence",
    "required_transformations",
    "screening_signals",
    "privacy_review_status",
]

SCREENING_FIELDS = [
    "doc_id",
    "sha256",
    "original_path",
    "file_name",
    "extension",
    "source_zone",
    "raw_max_college",
    "derivative_max_college",
    "publication_form",
    "required_transformations",
    "restriction_reasons",
    "personal_data_level",
    "ip_status",
    "ai_processing_ceiling",
    "review_required",
    "policy_confidence",
    "screening_signals",
    "exposure_risk",
    "remediation_priority",
    "recommended_action",
]

CONFIDENCE_RANK = {"low": 0, "medium": 1, "high": 2}


@dataclass(frozen=True)
class PrivacySignal:
    category: str
    value: str
    reason: str
    confidence: str = "medium"

    def marker(self) -> str:
        return f"{self.category}:{self.reason}:{self.confidence}"


REGEX_RULES: list[tuple[str, str, str, str]] = [
    ("EMAIL", r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", "RGPD", "high"),
    ("PHONE", r"(?<!\d)(?:\+33|0)[1-9](?:[\s.\-]?\d{2}){4}(?!\d)", "RGPD", "medium"),
    ("IBAN", r"\b[A-Z]{2}\d{2}(?:[\s\-]?[A-Z0-9]){11,30}\b", "finance", "high"),
    ("SIRET", r"\b\d{3}[\s.]?\d{3}[\s.]?\d{3}[\s.]?\d{5}\b", "tiers", "medium"),
    ("LOT", r"\b(?:lot|lots|appartement|batiment|bat\.?)\s*(?:n[°o]\s*)?[A-Z0-9\-]{1,8}\b", "RGPD", "medium"),
    ("ACCOUNT_INDIVIDUAL", r"\b(?:compte individuel|appel[s]? de fonds|quote-part|solde debiteur)\b", "RGPD", "high"),
    ("IMPAID", r"\b(?:impay[eé]s?|d[eé]biteur|recouvrement|mise en demeure)\b", "RGPD", "high"),
    ("CONTENTIOUS", r"\b(?:assignation|avocat|tribunal|proc[eé]dure|contentieux|huissier|commissaire de justice)\b", "contentieux", "high"),
    ("HEALTH", r"\b(?:sant[eé]|handicap|invalidit[eé]|m[eé]dical|maladie)\b", "RGPD_art9", "high"),
    ("REVENUE", r"\b(?:revenu fiscal|avis d'imposition|quotient familial|ressources du foyer|subvention individuelle)\b", "RGPD", "high"),
    (
        "SECURITY_SECRET",
        r"\b(?:mot de passe|password|code portail|code badge|code vigik|vigik|clef|cl[eé] d'acc[eè]s)\s*[:=]\s*[A-Z0-9#*@._\-]{3,40}\b",
        "securite",
        "high",
    ),
    ("SECURITY", r"\b(?:mot de passe|password|code portail|code badge|vigik|clef|cl[eé] d'acc[eè]s|camera|videosurveillance)\b", "securite", "high"),
    ("CONFIDENTIAL", r"\b(?:confidentiel|secret|secret des affaires|ne pas diffuser|diffusion restreinte)\b", "secret", "high"),
    ("IP_PLAN", r"\b(?:architecte|maitrise d'oeuvre|plan d'architecte|plan de principe|croquis|copyright)\b", "IP", "medium"),
    ("PERSON_NAME", r"\b(?:m\.|mme|monsieur|madame)\s+[A-Z][A-Za-z'\-]+(?:\s+[A-Z][A-Za-z'\-]+){0,2}\b", "RGPD", "medium"),
]

TEXT_DIRECT_IDENTIFIER_CATEGORIES = {
    "EMAIL",
    "PHONE",
    "IBAN",
    "LOT",
    "ACCOUNT_INDIVIDUAL",
    "PERSON_NAME",
    "SECURITY_SECRET",
}

CRITICAL_CATEGORIES = {"IBAN", "IMPAID", "HEALTH", "REVENUE", "SECURITY", "SECURITY_SECRET", "CONFIDENTIAL"}


def normalize_college(value: str | None, default: str = "C4_Conseil_Syndical") -> str:
    if not value:
        return default
    cleaned = value.strip()
    if cleaned in ACCESS_RANK:
        return cleaned
    by_lower = {college.lower(): college for college in ACCESS_COLLEGES}
    return by_lower.get(cleaned.lower(), default)


def max_restrictive(*values: str | None, default: str = "C4_Conseil_Syndical") -> str:
    colleges = [normalize_college(value, default=default) for value in values if value]
    if not colleges:
        return default
    return max(colleges, key=lambda college: ACCESS_RANK[college])


def min_restrictive(*values: str | None, default: str = "C4_Conseil_Syndical") -> str:
    colleges = [normalize_college(value, default=default) for value in values if value]
    if not colleges:
        return default
    return min(colleges, key=lambda college: ACCESS_RANK[college])


def is_wider_or_equal(candidate: str, ceiling: str) -> bool:
    return ACCESS_RANK[normalize_college(candidate)] <= ACCESS_RANK[normalize_college(ceiling)]


def ensure_policy_fields(fields: list[str]) -> list[str]:
    for field in POLICY_FIELDS:
        if field not in fields:
            fields.append(field)
    return fields


def load_privacy_rules(instance: InstanceConfig) -> dict[str, Any]:
    path = instance.privacy_rules_path()
    if not path.exists():
        return {}
    data = load_structured_file(path)
    return data if isinstance(data, dict) else {}


def detect_privacy_signals(text: str) -> list[PrivacySignal]:
    signals: list[PrivacySignal] = []
    for category, pattern, reason, confidence in REGEX_RULES:
        for match in re.finditer(pattern, text, flags=re.IGNORECASE):
            value = match.group(0).strip()
            if value:
                signals.append(PrivacySignal(category, value, reason, confidence))
    return _dedupe_signals(signals)


def redaction_signals(text: str) -> list[PrivacySignal]:
    return [
        signal
        for signal in detect_privacy_signals(text)
        if signal.category in TEXT_DIRECT_IDENTIFIER_CATEGORIES
    ]


def _dedupe_signals(signals: list[PrivacySignal]) -> list[PrivacySignal]:
    seen: set[tuple[str, str]] = set()
    unique: list[PrivacySignal] = []
    for signal in signals:
        key = (signal.category, signal.value.lower())
        if key in seen:
            continue
        seen.add(key)
        unique.append(signal)
    return unique


def _append_reasons(existing: set[str], signals: list[PrivacySignal]) -> None:
    for signal in signals:
        existing.add(signal.reason)


def _configured_policy(row: dict[str, str], rules: dict[str, Any], haystack: str) -> tuple[str, str, str, set[str], str]:
    default_raw = str(rules.get("default_college", "C4_Conseil_Syndical"))
    raw_candidates: list[str] = []
    derivative = ""
    publication_form = ""
    reasons: set[str] = set()
    confidence = "low"

    normalized_path = haystack.lower().replace("\\", "/")
    for marker in rules.get("public_path_markers", []):
        if str(marker).lower() in normalized_path:
            raw_candidates.append("C0_Public")
            derivative = "C0_Public"
            publication_form = "raw"
            confidence = "medium"

    for rule in rules.get("path_rules", []):
        markers = [str(marker).lower() for marker in rule.get("markers", [])]
        if markers and any(marker in normalized_path for marker in markers):
            raw_candidates.append(str(rule.get("raw_max_college", default_raw)))
            derivative = str(rule.get("derivative_max_college", derivative))
            publication_form = str(rule.get("publication_form", publication_form))
            reasons.update(str(item) for item in rule.get("restriction_reasons", []))
            confidence = _max_confidence(confidence, str(rule.get("confidence", "medium")))

    doc_type = row.get("document_type", "")
    for rule in rules.get("document_type_rules", []):
        doc_types = {str(item) for item in rule.get("document_types", [])}
        if doc_type and doc_type in doc_types:
            raw_candidates.append(str(rule.get("raw_max_college", default_raw)))
            derivative = str(rule.get("derivative_max_college", derivative))
            publication_form = str(rule.get("publication_form", publication_form))
            reasons.update(str(item) for item in rule.get("restriction_reasons", []))
            confidence = _max_confidence(confidence, str(rule.get("confidence", "medium")))

    raw = max_restrictive(*raw_candidates, default=default_raw) if raw_candidates else default_raw
    return normalize_college(raw), derivative, publication_form, reasons, confidence


def _max_confidence(left: str, right: str) -> str:
    return right if CONFIDENCE_RANK.get(right, 0) > CONFIDENCE_RANK.get(left, 0) else left


def _signal_summary(signals: list[PrivacySignal]) -> list[str]:
    by_category: dict[str, dict[str, object]] = {}
    for signal in signals:
        summary = by_category.setdefault(
            signal.category,
            {"count": 0, "confidence": "low", "reasons": set()},
        )
        summary["count"] = int(summary["count"]) + 1
        summary["confidence"] = _max_confidence(str(summary["confidence"]), signal.confidence)
        reasons = summary["reasons"]
        if isinstance(reasons, set):
            reasons.add(signal.reason)

    values: list[str] = []
    for category in sorted(by_category):
        summary = by_category[category]
        reasons = summary["reasons"]
        reason_text = ",".join(sorted(str(reason) for reason in reasons)) if isinstance(reasons, set) else ""
        values.append(f"{category}:count={summary['count']}:confidence={summary['confidence']}:reason={reason_text}")
    return values


def _default_derivative_for_raw(raw: str) -> tuple[str, str]:
    if ACCESS_RANK[raw] <= ACCESS_RANK["C2_Coproprietaires"]:
        return raw, "raw"
    if raw in {"C3_Coproprietaire_Concerne", "C4_Conseil_Syndical"}:
        return "C2_Coproprietaires", "redaction_required"
    if raw in {"C7_Contentieux_Secret", "C8_Restreint_Critique"}:
        return "C2_Coproprietaires", "aggregation_required"
    return "C4_Conseil_Syndical", "metadata_only"


def _normalize_derivative_policy(raw: str, derivative: str, publication_form: str) -> tuple[str, str]:
    if not derivative:
        return _default_derivative_for_raw(raw)

    derivative = normalize_college(derivative, default=raw)
    if ACCESS_RANK[derivative] < ACCESS_RANK[raw] and publication_form == "raw":
        return _default_derivative_for_raw(raw)

    if (
        ACCESS_RANK[raw] >= ACCESS_RANK["C4_Conseil_Syndical"]
        and ACCESS_RANK[derivative] <= ACCESS_RANK["C2_Coproprietaires"]
        and publication_form in {"", "raw"}
    ):
        if raw in {"C7_Contentieux_Secret", "C8_Restreint_Critique"}:
            return derivative, "aggregation_required"
        return derivative, "redaction_required"

    return derivative, publication_form or ("raw" if derivative == raw else "metadata_only")


def build_access_policy(row: dict[str, str], text: str, instance: InstanceConfig | None = None) -> dict[str, str]:
    rules = load_privacy_rules(instance) if instance is not None else {}
    path_haystack = "\n".join(
        [
            row.get("file_name", ""),
            row.get("original_path", ""),
            row.get("document_type", ""),
        ]
    )
    haystack = "\n".join(
        [
            path_haystack,
            text[:50000],
        ]
    )
    lower = haystack.lower()
    signals = detect_privacy_signals(haystack)
    raw, derivative, publication_form, reasons, confidence = _configured_policy(row, rules, path_haystack)
    _append_reasons(reasons, signals)

    categories = {signal.category for signal in signals}
    if categories.intersection(CRITICAL_CATEGORIES):
        raw = max_restrictive(raw, "C8_Restreint_Critique")
        confidence = _max_confidence(confidence, "high")
    elif "CONTENTIOUS" in categories:
        raw = max_restrictive(raw, "C7_Contentieux_Secret")
        confidence = _max_confidence(confidence, "high")
    elif {"EMAIL", "PHONE", "PERSON_NAME", "LOT", "ACCOUNT_INDIVIDUAL"}.intersection(categories):
        raw = max_restrictive(raw, "C4_Conseil_Syndical")
        confidence = _max_confidence(confidence, "medium")

    if "facture" in lower or row.get("document_type") in {"Facture", "Devis", "Annexe_Comptable"}:
        raw = max_restrictive(raw, "C4_Conseil_Syndical")
        derivative = derivative or "C2_Coproprietaires"
        publication_form = publication_form or "redaction_required"
        reasons.add("finance")

    derivative, publication_form = _normalize_derivative_policy(raw, derivative, publication_form)
    required_transformations = _required_transformations(publication_form, categories)
    personal_data_level = _personal_data_level(categories)
    ip_status = _ip_status(categories, lower, row)
    ai_processing_ceiling = "no_ai" if raw in {"C7_Contentieux_Secret", "C8_Restreint_Critique"} else "local_only"
    review_required = _review_required(raw, publication_form, confidence, categories)

    return {
        "raw_max_college": raw,
        "derivative_max_college": derivative,
        "publication_form": publication_form,
        "restriction_reasons": ";".join(sorted(reason for reason in reasons if reason)),
        "personal_data_level": personal_data_level,
        "ip_status": ip_status,
        "ai_processing_ceiling": ai_processing_ceiling,
        "review_required": "YES" if review_required else "",
        "policy_confidence": confidence,
        "required_transformations": ";".join(required_transformations),
        "screening_signals": ";".join(_signal_summary(signals)),
        "privacy_review_status": "A_REVOIR" if review_required else "AUTO_POLICY",
    }


def apply_access_policy(row: dict[str, str], text: str = "", instance: InstanceConfig | None = None) -> dict[str, str]:
    row.update(build_access_policy(row, text, instance))
    return row


def _required_transformations(publication_form: str, categories: set[str]) -> list[str]:
    transformations: list[str] = []
    if publication_form in {"redaction_required", "pseudonymization_or_redaction_required"}:
        transformations.append("redaction")
    if publication_form == "aggregation_required":
        transformations.append("aggregation")
    if publication_form == "metadata_only":
        transformations.append("metadata_only")
    if categories.intersection(TEXT_DIRECT_IDENTIFIER_CATEGORIES):
        if "redaction" not in transformations:
            transformations.append("redaction")
    if categories.intersection(CRITICAL_CATEGORIES):
        if "human_review" not in transformations:
            transformations.append("human_review")
    return transformations


def _personal_data_level(categories: set[str]) -> str:
    if categories.intersection({"HEALTH"}):
        return "sensitive_art9"
    if categories.intersection({"REVENUE", "IBAN", "ACCOUNT_INDIVIDUAL", "IMPAID", "PERSON_NAME", "EMAIL", "PHONE", "LOT", "SECURITY_SECRET"}):
        return "nominative"
    if categories:
        return "incidental"
    return "none"


def _ip_status(categories: set[str], lower: str, row: dict[str, str]) -> str:
    if "IP_PLAN" in categories or "architecte" in lower or "plan" in lower:
        return "architect_plan_or_third_party"
    if row.get("document_type") in {"Diagnostic_Technique", "Devis", "Dossier_ITE_Travaux"}:
        return "third_party_report"
    if "examples/synthetic_copro" in lower:
        return "synthetic_public"
    return "unknown"


def _review_required(raw: str, publication_form: str, confidence: str, categories: set[str]) -> bool:
    if confidence == "low":
        return True
    if raw in {"C0_Public", "C7_Contentieux_Secret", "C8_Restreint_Critique"}:
        return True
    if publication_form in {"aggregation_required", "metadata_only"}:
        return True
    if categories.intersection(CRITICAL_CATEGORIES):
        return True
    return False


def exposure_risk_for(row: dict[str, str]) -> tuple[str, str, str]:
    path = row.get("original_path", "").lower().replace("\\", "/")
    raw = normalize_college(row.get("raw_max_college"))
    broad_markers = ["diffusable", "communicable", "public", "publication", "livrables_coproprietaires"]
    if ACCESS_RANK[raw] >= ACCESS_RANK["C7_Contentieux_Secret"] and any(marker in path for marker in broad_markers):
        return "P0", "CRITICAL_EXPOSURE", "Retirer du dossier large puis revoir avant toute diffusion."
    if ACCESS_RANK[raw] >= ACCESS_RANK["C4_Conseil_Syndical"] and any(marker in path for marker in broad_markers):
        return "P1", "POSSIBLE_OVEREXPOSURE", "Verifier le dossier et publier seulement une version expurgee."
    if row.get("review_required"):
        return "P2", "REVIEW_REQUIRED", "Revue humaine de la politique d'acces."
    return "OK", "NO_OBVIOUS_EXPOSURE", "Aucune action immediate."


def safe_relative_path(base: Path, target: Path) -> str:
    try:
        return str(target.resolve().relative_to(base.resolve()))
    except ValueError:
        return str(target.resolve())
