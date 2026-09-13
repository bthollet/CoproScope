from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path

from ..core.common import (
    RunContext,
    detect_date,
    load_structured_file,
    read_csv,
    relative_to,
    write_csv,
    write_text,
)
from . import agscope


DECISION_ACTION_FIELDS = [
    "decision_action_id",
    "ag_id",
    "source_doc_id",
    "source_file",
    "resolution_ref",
    "decision_text",
    "action_attendue",
    "responsable",
    "echeance",
    "preuve_attendue",
    "proof_doc_ids",
    "proof_document_types",
    "related_request_ids",
    "related_invoice_refs",
    "related_work_refs",
    "statut",
    "priorite",
    "notes",
]


@dataclass(frozen=True)
class ActionRule:
    name: str
    keywords: tuple[str, ...]
    action: str
    responsable: str
    preuve: str
    proof_types: tuple[str, ...]
    proof_hints: tuple[str, ...]
    due_days: int
    priorite: str


ACTION_RULES = [
    ActionRule(
        name="contrat_syndic",
        keywords=("contrat syndic", "syndic", "mandat"),
        action="Verifier la version signee, la prise d'effet et la mise a disposition du contrat vote.",
        responsable="Syndic / conseil syndical",
        preuve="Contrat de syndic signe ou mandat applicable, avec date d'effet.",
        proof_types=("Contrat_Syndic",),
        proof_hints=("contrat", "syndic", "mandat", "honoraires"),
        due_days=15,
        priorite="P1",
    ),
    ActionRule(
        name="travaux_devis",
        keywords=("devis", "travaux", "toiture", "ravalement", "ite", "etancheite"),
        action="Transformer le vote en suivi travaux: devis retenu, ordre de service, calendrier et reception.",
        responsable="Syndic / commission travaux",
        preuve="Devis vote, ordre de service, facture ou proces-verbal de reception.",
        proof_types=("Devis", "Dossier_ITE_Travaux", "Facture"),
        proof_hints=("devis", "travaux", "toiture", "reception", "facture"),
        due_days=30,
        priorite="P1",
    ),
    ActionRule(
        name="comptes_budget",
        keywords=("approbation des comptes", "comptes", "budget", "annexe comptable"),
        action="Archiver la decision comptable et verifier les reserves ou pieces a rattacher.",
        responsable="Conseil syndical / syndic",
        preuve="PV signe et annexes comptables approuvees.",
        proof_types=("Annexe_Comptable", "PV_AG"),
        proof_hints=("annexe", "comptable", "budget", "charges", "produits"),
        due_days=15,
        priorite="P2",
    ),
]

DEFAULT_RULE = ActionRule(
    name="decision_generique",
    keywords=(),
    action="Identifier l'action concrete issue de la resolution et la suivre jusqu'a preuve.",
    responsable="Conseil syndical / syndic",
    preuve="PV signe, piece justificative ou reponse du syndic rattachee a la resolution.",
    proof_types=("PV_AG",),
    proof_hints=("pv", "proces verbal", "resolution", "decision"),
    due_days=30,
    priorite="P2",
)


def decision_register_path(instance) -> Path:
    settings = instance.settings().get("decisionops", {})
    configured = settings.get("register") or settings.get("registre")
    resolved = instance.resolve_path(str(configured)) if configured else None
    return resolved or (instance.root("workspace") / "registers" / "registre_decisions_actions_preuves.csv")


def _normalize(value: str) -> str:
    value = unicodedata.normalize("NFKD", value or "")
    value = "".join(char for char in value if not unicodedata.combining(char))
    return re.sub(r"\s+", " ", value.lower()).strip()


def _tokenize(value: str) -> list[str]:
    stopwords = {
        "article",
        "decision",
        "question",
        "resolution",
        "vote",
        "pour",
        "avec",
        "sans",
        "des",
        "les",
        "une",
        "aux",
        "sur",
        "du",
        "de",
        "la",
        "le",
        "et",
    }
    tokens = re.findall(r"[a-z0-9]{3,}", _normalize(value))
    return [token for token in tokens if token not in stopwords]


def _read_text(instance, row: dict[str, str], max_chars: int = 12000) -> str:
    workspace = instance.root("workspace")
    text_path = row.get("text_path")
    if text_path:
        path = workspace / text_path
        if path.exists():
            return path.read_text(encoding="utf-8", errors="ignore")[:max_chars]
    original_path = row.get("original_path")
    if original_path:
        path = workspace / original_path
        if path.exists() and path.suffix.lower() in {".txt", ".md", ".csv"}:
            return path.read_text(encoding="utf-8", errors="ignore")[:max_chars]
    return ""


def _resolution_patterns(instance) -> list[str]:
    rules = load_structured_file(instance.ag_rules_path())
    patterns = rules.get("resolution_patterns") or rules.get("motifs_resolution") or []
    return [_normalize(str(pattern)) for pattern in patterns if str(pattern).strip()]


def _resolution_lines(text: str, patterns: list[str]) -> list[str]:
    rows: list[str] = []
    for raw_line in text.splitlines():
        line = re.sub(r"\s+", " ", raw_line.strip(" -\t"))
        if not line:
            continue
        haystack = _normalize(line)
        if haystack in {"ordre du jour", "annexes jointes"}:
            continue
        if _is_resolution_candidate(haystack, patterns):
            rows.append(line)
    return rows


def _is_resolution_candidate(haystack: str, patterns: list[str]) -> bool:
    if not any(pattern in haystack for pattern in patterns):
        return False
    generic_fragments = {
        "une seule par resolution",
        "prendre toutes resolutions necessaires",
        "chacune des questions",
        "ordre du jour et des documents",
        "le proces-verbal comporte",
        "projet de resolution soumis au vote",
        "etablissement de l ordre du jour",
        "elaboration et envoi de la convocation",
    }
    if any(fragment in haystack for fragment in generic_fragments):
        return False
    if re.search(r"\b(?:resolution|question|decision)\s*(?:n[o°]\s*)?\d", haystack):
        return True
    if re.search(r"\bvote de la resolution\s*(?:n[o°]\s*)?\d", haystack):
        return True
    if re.search(r"^\d+(?:\s*[.\-]\s*\d+)?\s*[-.]\s*(?:vote de la )?resolution", haystack):
        return True
    return "resolution" in haystack and "demande de" in haystack


def _resolution_ref(line: str, index: int) -> str:
    match = re.search(r"\b(?:resolution|question|decision)\s*(?:n[o\u00b0]\s*)?([0-9]+[a-zA-Z]?)\b", line, flags=re.IGNORECASE)
    if match:
        return f"R{match.group(1).upper()}"
    return f"R{index:02d}"


def _row_date(ag_row: dict[str, str] | None, doc_row: dict[str, str]) -> str:
    if ag_row and ag_row.get("detected_date"):
        return ag_row["detected_date"]
    return (
        doc_row.get("suspected_date")
        or detect_date(doc_row.get("file_name", ""))
        or detect_date(doc_row.get("original_path", ""))
        or ""
    )


def _due_date(base_date: str, days: int) -> str:
    if not base_date or not re.match(r"^20\d{2}-[01]\d-[0-3]\d$", base_date):
        return ""
    return (datetime.strptime(base_date, "%Y-%m-%d") + timedelta(days=days)).date().isoformat()


def _rule_for(line: str) -> ActionRule:
    haystack = _normalize(line)
    for rule in ACTION_RULES:
        if any(keyword in haystack for keyword in rule.keywords):
            return rule
    return DEFAULT_RULE


def _decision_id(ag_id: str, doc_id: str, ref: str) -> str:
    base = f"{ag_id}-{ref}" if ag_id else f"{doc_id}-{ref}"
    token = re.sub(r"[^A-Z0-9]+", "-", _normalize(base).upper()).strip("-")
    return f"DAP-{token[:64]}"


def _doc_haystack(instance, row: dict[str, str]) -> str:
    return _normalize(
        "\n".join(
            [
                row.get("doc_id", ""),
                row.get("file_name", ""),
                row.get("document_type", ""),
                row.get("lot", ""),
                _read_text(instance, row, max_chars=3000),
            ]
        )
    )


def _score_proof_candidate(haystack: str, doc_type: str, tokens: list[str], rule: ActionRule) -> int:
    score = 0
    if doc_type in rule.proof_types:
        score += 6
    score += sum(1 for token in set(tokens) if token in haystack)
    score += sum(2 for hint in rule.proof_hints if hint in haystack)
    return score


def _proof_links(
    instance,
    docs: list[dict[str, str]],
    source_doc_id: str,
    line: str,
    rule: ActionRule,
) -> list[dict[str, str]]:
    tokens = _tokenize(line)
    candidates: list[tuple[int, dict[str, str]]] = []
    for doc in docs:
        if doc.get("doc_id") == source_doc_id:
            continue
        haystack = _doc_haystack(instance, doc)
        doc_type = doc.get("document_type", "")
        score = _score_proof_candidate(haystack, doc_type, tokens, rule)
        token_hits = sum(1 for token in set(tokens) if token in haystack)
        if doc_type in rule.proof_types and score >= 6:
            candidates.append((score, doc))
        elif score >= 8 and token_hits >= 3:
            candidates.append((score, doc))
    candidates.sort(key=lambda item: (-item[0], item[1].get("doc_id", "")))
    return [doc for _, doc in candidates[:5]]


def _request_links(instance, line: str) -> list[str]:
    try:
        _, requests = read_csv(instance.register("requests"))
    except KeyError:
        return []
    tokens = set(_tokenize(line))
    linked: list[str] = []
    for request in requests:
        haystack = _normalize(
            " ".join(
                [
                    request.get("subject", ""),
                    request.get("expected_piece", ""),
                    request.get("notes", ""),
                    request.get("related_doc_ids", ""),
                ]
            )
        )
        if len(tokens.intersection(set(_tokenize(haystack)))) >= 2:
            linked.append(request.get("request_id", ""))
    return [item for item in linked if item][:5]


def _ag_rows_by_doc(instance, run: RunContext, ensure_ag: bool) -> dict[str, dict[str, str]]:
    ag_path = instance.register("ag")
    _, rows = read_csv(ag_path)
    if ensure_ag and not rows:
        agscope.analyze(instance, run)
        _, rows = read_csv(ag_path)
    return {row.get("doc_id", ""): row for row in rows if row.get("doc_id")}


def _ag_candidate_docs(docs: list[dict[str, str]]) -> list[dict[str, str]]:
    candidates: list[dict[str, str]] = []
    for doc in docs:
        doc_type = doc.get("document_type", "")
        haystack = _normalize(f"{doc.get('file_name', '')} {doc.get('original_path', '')}")
        if doc_type in {"Convocation_AG", "PV_AG", "Annexe_AG"} or "assemblee" in haystack or "convocation" in haystack:
            candidates.append(doc)
    return candidates


def build_decision_register(instance, run: RunContext, ensure_ag: bool = True, doc_id: str | None = None) -> dict[str, object]:
    _, docs = read_csv(instance.register("documents"))
    ag_by_doc = _ag_rows_by_doc(instance, run, ensure_ag=ensure_ag)
    patterns = _resolution_patterns(instance)
    rows: list[dict[str, str]] = []

    for doc in _ag_candidate_docs(docs):
        if doc_id and doc.get("doc_id") != doc_id:
            continue
        text = _read_text(instance, doc, max_chars=250000)
        lines = _resolution_lines(text, patterns)
        ag_row = ag_by_doc.get(doc.get("doc_id", ""))
        ag_id = (ag_row or {}).get("ag_id") or f"AG-{_row_date(ag_row, doc) or doc.get('doc_id', '')[-6:]}"
        base_date = _row_date(ag_row, doc)
        for index, line in enumerate(lines, start=1):
            ref = _resolution_ref(line, index)
            rule = _rule_for(line)
            proofs = _proof_links(instance, docs, doc.get("doc_id", ""), line, rule)
            proof_doc_ids = [proof.get("doc_id", "") for proof in proofs if proof.get("doc_id")]
            proof_types = [proof.get("document_type", "") for proof in proofs if proof.get("document_type")]
            proof_ids_joined = "; ".join(proof_doc_ids)
            doc_type = doc.get("document_type", "")
            if doc_type == "Convocation_AG":
                statut = "CANDIDAT_AVANT_AG"
            elif proof_doc_ids:
                statut = "PREUVE_LOCALE_A_VERIFIER"
            else:
                statut = "PREUVE_A_DEMANDER"
            if doc_type != "Convocation_AG" and not proof_doc_ids:
                notes = "Aucune preuve locale rattachee automatiquement."
            elif doc_type == "Convocation_AG":
                notes = "Resolution issue d'une convocation: confirmer le vote dans le PV."
            else:
                notes = "Preuves candidates rattachees automatiquement."
            related_work_refs = [
                proof.get("doc_id", "")
                for proof in proofs
                if proof.get("document_type") in {"Devis", "Dossier_ITE_Travaux"}
            ]
            related_invoice_refs = [proof.get("doc_id", "") for proof in proofs if proof.get("document_type") == "Facture"]
            rows.append(
                {
                    "decision_action_id": _decision_id(ag_id, doc.get("doc_id", ""), ref),
                    "ag_id": ag_id,
                    "source_doc_id": doc.get("doc_id", ""),
                    "source_file": doc.get("file_name", ""),
                    "resolution_ref": ref,
                    "decision_text": line,
                    "action_attendue": rule.action,
                    "responsable": rule.responsable,
                    "echeance": _due_date(base_date, rule.due_days),
                    "preuve_attendue": rule.preuve,
                    "proof_doc_ids": proof_ids_joined,
                    "proof_document_types": "; ".join(dict.fromkeys(proof_types)),
                    "related_request_ids": "; ".join(_request_links(instance, line)),
                    "related_invoice_refs": "; ".join(related_invoice_refs),
                    "related_work_refs": "; ".join(related_work_refs),
                    "statut": statut,
                    "priorite": rule.priorite,
                    "notes": notes,
                }
            )

    register_path = decision_register_path(instance)
    if doc_id:
        _, existing_rows = read_csv(register_path)
        rows = [row for row in existing_rows if row.get("source_doc_id") != doc_id] + rows
    rows.sort(key=lambda row: (row["ag_id"], row["resolution_ref"], row["decision_action_id"]))
    write_csv(register_path, DECISION_ACTION_FIELDS, rows)
    run.log_action("write", register_path, f"decision-action rows={len(rows)}")

    report_path = instance.artifact("reports_dir") / "rapport_decisions_actions_preuves.md"
    _write_report(report_path, rows)
    run.log_action("write", report_path, "decision-action report")
    return {
        "status": "ok",
        "decision_action_count": len(rows),
        "register": str(register_path),
        "report": str(report_path),
        "register_relative": relative_to(instance.root("workspace"), register_path),
        "report_relative": relative_to(instance.root("workspace"), report_path),
    }


def _write_report(path: Path, rows: list[dict[str, str]]) -> None:
    with_proofs = sum(1 for row in rows if row.get("proof_doc_ids"))
    missing = sum(1 for row in rows if row.get("statut") == "PREUVE_A_DEMANDER")
    candidate = sum(1 for row in rows if row.get("statut") == "CANDIDAT_AVANT_AG")
    lines = [
        "# Registre decisions-actions-preuves",
        "",
        f"- Decisions ou resolutions suivies: {len(rows)}",
        f"- Preuves locales rattachees: {with_proofs}",
        f"- Preuves a demander: {missing}",
        f"- Candidats avant PV: {candidate}",
        "",
        "| ID | AG | Resolution | Statut | Action | Preuves |",
        "|---|---|---|---|---|---|",
    ]
    for row in rows:
        lines.append(
            f"| {row['decision_action_id']} | {row['ag_id']} | {row['resolution_ref']} | "
            f"{row['statut']} | {row['action_attendue']} | {row['proof_doc_ids'] or '-'} |"
        )
    if not rows:
        lines.append("| - | - | - | - | Aucune resolution exploitable detectee. | - |")
    write_text(path, "\n".join(lines) + "\n")
