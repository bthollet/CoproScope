from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any, Iterable, Mapping

from .sync_profiles import SyncAudit, TransportRisk, audit_sync_folder


class VaultSyncAlertLevel(str, Enum):
    INFORMATION = "information"
    ATTENTION = "attention"
    PROTECTION = "protection"
    INCIDENT = "incident"


class VaultSyncActionCode(str, Enum):
    NO_LOCK = "no_lock"
    SUSPEND_PUBLICATION = "suspend_publication"
    LOCK_READONLY = "lock_readonly"
    NOTIFY_INTERNAL = "notify_internal"


@dataclass(frozen=True)
class VaultIntegrityFinding:
    code: str
    detail: str
    path: str = ""


@dataclass(frozen=True)
class VaultSyncAlert:
    level: VaultSyncAlertLevel
    code: str
    detail: str
    paths: tuple[str, ...] = ()


@dataclass(frozen=True)
class VaultSyncAction:
    code: VaultSyncActionCode
    detail: str
    enabled: bool = True


@dataclass(frozen=True)
class VaultSyncEvent:
    event_type: str
    level: VaultSyncAlertLevel
    code: str
    payload: Mapping[str, Any]


@dataclass(frozen=True)
class VaultSyncAlertReport:
    level: VaultSyncAlertLevel
    sync_audit: SyncAudit
    alerts: tuple[VaultSyncAlert, ...]
    actions: tuple[VaultSyncAction, ...]
    internal_events: tuple[VaultSyncEvent, ...]

    @property
    def lock_mode(self) -> str:
        if self.has_action(VaultSyncActionCode.LOCK_READONLY):
            return "read_only"
        return "none"

    @property
    def publication_suspended(self) -> bool:
        return self.has_action(VaultSyncActionCode.SUSPEND_PUBLICATION)

    @property
    def notification_required(self) -> bool:
        return self.has_action(VaultSyncActionCode.NOTIFY_INTERNAL)

    def has_action(self, code: VaultSyncActionCode) -> bool:
        return any(action.enabled and action.code == code for action in self.actions)


_LEVEL_RANK = {
    VaultSyncAlertLevel.INFORMATION: 0,
    VaultSyncAlertLevel.ATTENTION: 1,
    VaultSyncAlertLevel.PROTECTION: 2,
    VaultSyncAlertLevel.INCIDENT: 3,
}

_INCIDENT_INTEGRITY_CODES = {
    "missing_signature",
    "invalid_signature",
    "missing_event_hash",
    "invalid_event_hash",
    "missing_payload_hash",
    "invalid_payload_hash",
    "missing_blob",
    "invalid_blob_hash",
    "missing_public_key",
    "missing_vault_manifest",
}

_INCIDENT_ERROR_TOKENS = (
    "signature",
    "event hash",
    "snapshot hash",
    "encrypted payload hash",
    "missing blob",
    "invalid blob hash",
    "missing public key",
    "missing vault.json",
)


def evaluate_vault_sync_alerts(
    sync_root: str | Path,
    profile_id: str,
    *,
    integrity_findings: Iterable[VaultIntegrityFinding | Mapping[str, Any]] = (),
    integrity_report: Mapping[str, Any] | None = None,
    sync_active: bool = True,
) -> VaultSyncAlertReport:
    """Audit a sync folder and classify alerts without process or port scanning."""
    return classify_vault_sync_audit(
        audit_sync_folder(sync_root, profile_id),
        integrity_findings=integrity_findings,
        integrity_report=integrity_report,
        sync_active=sync_active,
    )


def classify_vault_sync_audit(
    sync_audit: SyncAudit,
    *,
    integrity_findings: Iterable[VaultIntegrityFinding | Mapping[str, Any]] = (),
    integrity_report: Mapping[str, Any] | None = None,
    sync_active: bool = True,
) -> VaultSyncAlertReport:
    findings = tuple(_normalize_integrity_finding(finding) for finding in integrity_findings)
    findings += tuple(_integrity_findings_from_report(integrity_report or {}))

    alerts = _alerts_from_audit(sync_audit, sync_active=sync_active) + _alerts_from_integrity_findings(findings)
    if not alerts:
        alerts = (
            VaultSyncAlert(
                level=VaultSyncAlertLevel.INFORMATION,
                code="sync_inactive",
                detail="Aucun signal de synchronisation active ou de risque transport n'a ete detecte.",
            ),
        )

    level = _highest_alert_level(alerts)
    actions = _actions_for_level(level, sync_active=sync_active)
    events = (_internal_event(sync_audit, level, alerts, actions),)
    return VaultSyncAlertReport(
        level=level,
        sync_audit=sync_audit,
        alerts=alerts,
        actions=actions,
        internal_events=events,
    )


def _alerts_from_audit(sync_audit: SyncAudit, *, sync_active: bool) -> tuple[VaultSyncAlert, ...]:
    alerts: list[VaultSyncAlert] = []
    if sync_active and sync_audit.clean:
        alerts.append(
            VaultSyncAlert(
                level=VaultSyncAlertLevel.INFORMATION,
                code="sync_active_clean",
                detail="Le transport de synchronisation est actif sans marqueur de conflit ni entree interdite.",
            )
        )
    if sync_audit.conflict_markers:
        alerts.append(
            VaultSyncAlert(
                level=VaultSyncAlertLevel.ATTENTION,
                code="provider_conflict_markers",
                detail="Des marqueurs de conflit fournisseur demandent une revue humaine avant confiance.",
                paths=sync_audit.conflict_markers,
            )
        )
    if sync_audit.forbidden_entries:
        alerts.append(
            VaultSyncAlert(
                level=VaultSyncAlertLevel.PROTECTION,
                code="forbidden_sync_entries",
                detail="Des entrees de developpement, cache ou export temporaire sont dans le dossier synchronise.",
                paths=sync_audit.forbidden_entries,
            )
        )

    warning_risks = _transport_risk_paths(sync_audit.transport_risks, severity="warning")
    error_risks = _transport_risk_paths(sync_audit.transport_risks, severity="error")
    if warning_risks:
        alerts.append(
            VaultSyncAlert(
                level=VaultSyncAlertLevel.ATTENTION,
                code="transport_warning",
                detail="Le transport expose des metadonnees ou signaux non probants pour le vault.",
                paths=warning_risks,
            )
        )
    if error_risks:
        alerts.append(
            VaultSyncAlert(
                level=VaultSyncAlertLevel.PROTECTION,
                code="unstable_transport_bytes",
                detail="Des placeholders, ecritures partielles ou entrees non regulieres menacent la surface signee.",
                paths=error_risks,
            )
        )
    return tuple(alerts)


def _alerts_from_integrity_findings(findings: tuple[VaultIntegrityFinding, ...]) -> tuple[VaultSyncAlert, ...]:
    if not findings:
        return ()
    incident_paths = tuple(sorted({finding.path for finding in findings if finding.path}))
    codes = ", ".join(sorted({finding.code for finding in findings}))
    details = "; ".join(finding.detail for finding in findings if finding.detail)
    return (
        VaultSyncAlert(
            level=VaultSyncAlertLevel.INCIDENT,
            code="vault_integrity_incident",
            detail=f"Controle d'integrite vault en incident: {codes}. {details}".strip(),
            paths=incident_paths,
        ),
    )


def _transport_risk_paths(risks: Iterable[TransportRisk], *, severity: str) -> tuple[str, ...]:
    return tuple(sorted({risk.path for risk in risks if risk.severity == severity}))


def _highest_alert_level(alerts: Iterable[VaultSyncAlert]) -> VaultSyncAlertLevel:
    return max((alert.level for alert in alerts), key=lambda level: _LEVEL_RANK[level])


def _actions_for_level(level: VaultSyncAlertLevel, *, sync_active: bool) -> tuple[VaultSyncAction, ...]:
    actions = [
        VaultSyncAction(
            code=VaultSyncActionCode.NOTIFY_INTERNAL,
            detail="Publier un evenement abstrait interne pour journaliser le niveau d'alerte.",
        )
    ]
    if level == VaultSyncAlertLevel.INCIDENT:
        actions.append(
            VaultSyncAction(
                code=VaultSyncActionCode.LOCK_READONLY,
                detail="Verrouiller le vault en lecture seule jusqu'a resolution de l'incident d'integrite.",
            )
        )
    elif level == VaultSyncAlertLevel.PROTECTION:
        actions.append(
            VaultSyncAction(
                code=VaultSyncActionCode.SUSPEND_PUBLICATION,
                detail="Suspendre la publication externe tant que la surface synchronisee n'est pas nettoyee.",
            )
        )
    elif sync_active:
        actions.append(
            VaultSyncAction(
                code=VaultSyncActionCode.NO_LOCK,
                detail="Ne pas verrouiller le vault pour une simple synchronisation active propre ou a surveiller.",
            )
        )
    return tuple(actions)


def _internal_event(
    sync_audit: SyncAudit,
    level: VaultSyncAlertLevel,
    alerts: tuple[VaultSyncAlert, ...],
    actions: tuple[VaultSyncAction, ...],
) -> VaultSyncEvent:
    return VaultSyncEvent(
        event_type="vault.sync_alert.classified",
        level=level,
        code="vault_sync_alerts_evaluated",
        payload={
            "profile_id": sync_audit.profile_id,
            "sync_root": sync_audit.path,
            "level": level.value,
            "alert_codes": [alert.code for alert in alerts],
            "action_codes": [action.code.value for action in actions if action.enabled],
        },
    )


def _normalize_integrity_finding(finding: VaultIntegrityFinding | Mapping[str, Any]) -> VaultIntegrityFinding:
    if isinstance(finding, VaultIntegrityFinding):
        return finding
    code = str(finding.get("code") or finding.get("kind") or "integrity_error")
    detail = str(finding.get("detail") or finding.get("error") or finding.get("message") or code)
    path = str(finding.get("path") or finding.get("event_path") or "")
    return VaultIntegrityFinding(code=_incident_code(code, detail), detail=detail, path=path)


def _integrity_findings_from_report(report: Mapping[str, Any]) -> tuple[VaultIntegrityFinding, ...]:
    raw_errors = report.get("errors", ())
    if isinstance(raw_errors, str):
        errors = (raw_errors,)
    elif isinstance(raw_errors, Iterable):
        errors = tuple(str(error) for error in raw_errors)
    else:
        errors = ()
    return tuple(
        VaultIntegrityFinding(code=_incident_code("integrity_error", error), detail=error, path=_path_from_error(error))
        for error in errors
        if _is_incident_error(error)
    )


def _incident_code(code: str, detail: str) -> str:
    normalized = code.strip().lower()
    if normalized in _INCIDENT_INTEGRITY_CODES:
        return normalized
    text = detail.lower()
    if "signature" in text:
        return "invalid_signature"
    if "missing blob" in text:
        return "missing_blob"
    if "blob hash" in text:
        return "invalid_blob_hash"
    if "event hash" in text or "snapshot hash" in text:
        return "invalid_event_hash"
    if "encrypted payload hash" in text:
        return "invalid_payload_hash"
    if "missing public key" in text:
        return "missing_public_key"
    if "missing vault.json" in text:
        return "missing_vault_manifest"
    return normalized or "integrity_error"


def _is_incident_error(error: str) -> bool:
    normalized = error.lower()
    return any(token in normalized for token in _INCIDENT_ERROR_TOKENS)


def _path_from_error(error: str) -> str:
    return error.split(":", 1)[0] if ":" in error else ""
