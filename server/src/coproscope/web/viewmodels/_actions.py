from __future__ import annotations

from ._runtime import *

def _stable_action_id(prefix: str, index: int, *parts: str) -> str:
    raw = "|".join(part for part in parts if part).strip()
    if raw:
        digest = hashlib.sha256(raw.encode("utf-8", errors="ignore")).hexdigest()[:8].upper()
        return f"{prefix}-{digest}"
    return f"{prefix}-{index + 1:04d}"


def _accounting_actions(
    non_matches: DataTable,
    controls_p1: list[dict[str, str]],
    anomalies: DataTable | None = None,
) -> list[dict[str, str]]:
    actions: list[dict[str, str]] = []
    for index, row in enumerate(non_matches.rows):
        question = _question_from_non_match(row)
        supplier = row.get("fournisseur") or "Fournisseur non renseigne"
        invoice = row.get("numero_facture") or row.get("doc_id") or row.get("aliases") or "piece non renseignee"
        amount = row.get("ttc")
        title = f"{supplier} - {amount} EUR" if amount else supplier
        actions.append(
            _action(
                title,
                "ComptaScope",
                _priority_for(row, "P1"),
                row.get("match_reason") or row.get("next_action") or "Rapprochement a clarifier.",
                "/comptes",
                action_id=_stable_action_id("ACT-COMP-RAPP", index, row.get("doc_id", ""), invoice, supplier),
                status="a_demander",
                domain="comptes",
                domain_label="Comptes",
                owner="Syndic a solliciter",
                next_step=question["question"],
                evidence=row.get("chemin_piece") or row.get("doc_id") or invoice,
                channel="syndic",
            )
        )
    for index, row in enumerate(controls_p1):
        question = _question_from_control(row)
        control = row.get("control") or row.get("status") or "Controle comptable"
        evidence = row.get("evidence") or row.get("doc_id") or "piece concernee"
        actions.append(
            _action(
                control,
                "ComptaScope",
                _priority_for(row, "P1"),
                row.get("action") or row.get("status") or "Piece attendue.",
                "/comptes",
                action_id=_stable_action_id("ACT-COMP-CTRL", index, row.get("control_id", ""), row.get("doc_id", ""), evidence),
                status="a_demander",
                domain="comptes",
                domain_label="Comptes",
                owner="Syndic a solliciter",
                next_step=question["question"],
                evidence=evidence,
                channel="syndic",
            )
        )
    for index, row in enumerate((anomalies.rows if isinstance(anomalies, DataTable) else [])):
        priority = _priority_for(row, "P2")
        if priority == "OK":
            continue
        question = _question_from_anomaly(row)
        title = question["title"]
        evidence = row.get("evidence") or row.get("doc_id") or row.get("numero_facture") or "justificatif attendu"
        status = "a_demander" if priority in {"P0", "P1"} else "a_confirmer"
        actions.append(
            _action(
                title,
                "ComptaScope",
                priority,
                row.get("anomaly") or question["reason"] or "Justificatif comptable a clarifier.",
                "/comptes",
                action_id=_stable_action_id("ACT-COMP-ANOM", index, row.get("anomaly_id", ""), title, evidence),
                status=status,
                domain="comptes",
                domain_label="Comptes",
                owner="Syndic a solliciter",
                next_step=question["question"],
                evidence=evidence,
                channel="syndic",
            )
        )
    return actions


def _privacy_actions(review_rows: list[dict[str, str]]) -> list[dict[str, str]]:
    actions: list[dict[str, str]] = []
    for index, row in enumerate(review_rows):
        title = row.get("file_name") or row.get("doc_id") or "Document"
        transformation = row.get("required_transformations") or row.get("publication_form") or "revue diffusion"
        review_status = row.get("privacy_review_status", "")
        action_status = "bloque" if review_status == "BLOQUE" else "a_revoir"
        actions.append(
            _action(
                title,
                "PrivacyOps",
                row.get("remediation_priority", "P2"),
                row.get("publication_blocker") or row.get("recommended_action") or "Revoir la politique de diffusion.",
                "/confidentialite",
                action_id=_stable_action_id("ACT-PRIV", index, row.get("doc_id", ""), row.get("original_path", ""), title),
                status=action_status,
                domain="confidentialite",
                domain_label="Confidentialite",
                owner="Conseil syndical",
                next_step=row.get("review_next_step") or row.get("recommended_action") or f"Verifier le niveau de diffusion : {transformation}.",
                evidence=row.get("original_path") or row.get("doc_id") or title,
            )
        )
    return actions


def _document_actions(stale_or_missing: list[dict[str, str]]) -> list[dict[str, str]]:
    actions: list[dict[str, str]] = []
    for index, row in enumerate(stale_or_missing):
        title = (
            row.get("title")
            or row.get("subject")
            or row.get("expected_piece")
            or row.get("expected_label")
            or row.get("document_type")
            or row.get("doc_id")
            or "Piece documentaire"
        )
        status = row.get("status") or "a_verifier"
        action_status = "a_demander" if status in {"ABSENT", "A_DEMANDER", "OBSOLETE"} else "a_verifier"
        actions.append(
            _action(
                title,
                "DocOps",
                row.get("severity") or row.get("priority") or row.get("criticality") or "P2",
                row.get("detail") or row.get("finding") or row.get("reason") or status or "Piece documentaire a verifier.",
                "/documents",
                action_id=_stable_action_id(
                    "ACT-DOC",
                    index,
                    row.get("request_id", ""),
                    row.get("finding_id", ""),
                    row.get("source_ref", ""),
                    row.get("doc_id", ""),
                    title,
                ),
                status=action_status,
                domain="documents",
                domain_label="Documents",
                owner="Conseil syndical",
                next_step=row.get("suggested_diligence")
                or row.get("next_action")
                or row.get("action")
                or row.get("diligence")
                or "Verifier la piece ou preparer une demande au syndic.",
                evidence=row.get("evidence")
                or row.get("evidence_paths")
                or row.get("related_doc_ids")
                or row.get("original_path")
                or row.get("doc_id")
                or title,
                channel="syndic" if "syndic" in " ".join(row.values()).lower() else "",
            )
        )
    return actions


def _decision_actions(decisions: dict[str, object]) -> list[dict[str, str]]:
    rows = decisions.get("open_rows")
    if not isinstance(rows, list):
        return []
    actions: list[dict[str, str]] = []
    status_map = {
        "PREUVE_A_DEMANDER": "a_demander",
        "CANDIDAT_AVANT_AG": "a_confirmer",
        "PREUVE_LOCALE_A_VERIFIER": "a_verifier",
    }
    for index, row in enumerate(rows):
        if not isinstance(row, dict):
            continue
        statut = row.get("statut", "")
        title = " - ".join(part for part in [row.get("resolution_ref", ""), _clip(row.get("decision_text", ""), 90)] if part)
        actions.append(
            _action(
                title or row.get("decision_action_id", "") or "Decision AG",
                "DecisionOps",
                row.get("priorite") or "P2",
                row.get("notes") or statut or "Decision a suivre.",
                "/chantiers",
                action_id=_stable_action_id(
                    "ACT-DEC",
                    index,
                    row.get("decision_action_id", ""),
                    row.get("ag_id", ""),
                    row.get("resolution_ref", ""),
                ),
                status=status_map.get(statut, "a_traiter"),
                domain="decisions",
                domain_label="Decisions",
                owner=row.get("responsable") or "Conseil syndical / syndic",
                next_step=row.get("action_attendue") or "Suivre la resolution jusqu'a sa preuve.",
                evidence=row.get("preuve_attendue") or row.get("proof_doc_ids") or row.get("source_file", ""),
                channel="syndic"
                if "syndic" in " ".join([row.get("responsable", ""), row.get("action_attendue", "")]).lower()
                else "",
            )
        )
    return actions


def _incident_actions(incidents: dict[str, object]) -> list[dict[str, str]]:
    rows = incidents.get("open_rows")
    if not isinstance(rows, list):
        return []
    actions: list[dict[str, str]] = []
    status_map = {
        "EN_ATTENTE_PREUVE": "a_demander",
        "A_CLOTURER": "a_demander",
        "EN_RELANCE": "a_demander",
        "A_QUALIFIER": "a_revoir",
        "NOUVEAU": "a_traiter",
        "EN_COURS": "a_traiter",
    }
    for index, row in enumerate(rows):
        if not isinstance(row, dict):
            continue
        status = incidentops.normalize_status(row.get("status"))
        title_parts = [row.get("lieu", ""), row.get("date_signalement", ""), _clip(row.get("description", ""), 80)]
        title = " - ".join(part for part in title_parts if part)
        actions.append(
            _action(
                title or row.get("incident_id", "") or "Incident ouvert",
                "IncidentOps",
                row.get("priority") or "P2",
                row.get("notes") or row.get("description") or status,
                "/chantiers",
                action_id=_stable_action_id(
                    "ACT-INC",
                    index,
                    row.get("incident_id", ""),
                    row.get("source_refs", ""),
                    row.get("description", ""),
                ),
                status=status_map.get(status, "a_traiter"),
                domain="incidents",
                domain_label="Incidents",
                owner=row.get("syndic_or_provider") or "Conseil syndical / syndic",
                next_step=row.get("next_action") or "Qualifier l'incident et demander une trace ecrite.",
                evidence=row.get("expected_closure_proof") or row.get("closure_proof_ref") or row.get("piece_ref", ""),
                channel="syndic"
                if "syndic" in " ".join([row.get("syndic_or_provider", ""), row.get("next_action", "")]).lower()
                else "",
            )
        )
    return actions


def _action_rank(action: dict[str, str]) -> tuple[int, int, str]:
    priority_rank = {"P0": 0, "P1": 1, "P2": 2, "P3": 3, "OK": 4}
    status_rank = {
        "bloque": 0,
        "a_demander": 1,
        "a_traiter": 2,
        "a_revoir": 3,
        "a_confirmer": 4,
        "a_verifier": 5,
        "clos": 9,
    }
    return (
        priority_rank.get(action.get("priority", "P2"), 2),
        status_rank.get(action.get("status", "a_traiter"), 4),
        action.get("title", "").lower(),
    )


def _build_action_items(
    documents: dict[str, object],
    accounting: dict[str, object],
    privacy: dict[str, object],
    decisions: dict[str, object],
    incidents: dict[str, object],
) -> list[dict[str, str]]:
    non_matches = accounting.get("non_matches")
    controls_p1 = accounting.get("controls_p1")
    anomalies = accounting.get("anomalies")
    review_rows = privacy.get("review_rows")
    stale_or_missing = documents.get("stale_or_missing")
    actionable = documents.get("actionable")
    actions: list[dict[str, str]] = []
    if isinstance(non_matches, DataTable):
        actions.extend(_accounting_actions(non_matches, controls_p1 if isinstance(controls_p1, list) else [], anomalies if isinstance(anomalies, DataTable) else None))
    if isinstance(review_rows, list):
        actions.extend(_privacy_actions(review_rows))
    doc_rows: list[dict[str, str]] = []
    if isinstance(actionable, dict) and isinstance(actionable.get("to_request"), list):
        doc_rows.extend(row for row in actionable["to_request"] if isinstance(row, dict))
    if isinstance(stale_or_missing, list):
        doc_rows.extend(row for row in stale_or_missing if isinstance(row, dict))
    if doc_rows:
        actions.extend(_document_actions(doc_rows))
    actions.extend(_decision_actions(decisions))
    actions.extend(_incident_actions(incidents))
    return sorted(actions, key=_action_rank)
