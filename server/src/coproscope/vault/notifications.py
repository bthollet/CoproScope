from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import datetime, timezone
from enum import Enum
import hashlib
import json
from typing import Any, Iterable, Mapping

from .sync_alerts import VaultSyncActionCode, VaultSyncAlertLevel, VaultSyncAlertReport


class VaultNotificationSeverity(str, Enum):
    INFORMATION = "information"
    ATTENTION = "attention"
    PROTECTION = "protection"
    INCIDENT = "incident"


class VaultNotificationRecipientKind(str, Enum):
    ROLE = "role"
    MEMBER = "member"


@dataclass(frozen=True)
class VaultNotificationRecipient:
    kind: VaultNotificationRecipientKind
    value: str

    @classmethod
    def role(cls, role: str) -> "VaultNotificationRecipient":
        return cls(VaultNotificationRecipientKind.ROLE, role)

    @classmethod
    def member(cls, member_id: str) -> "VaultNotificationRecipient":
        return cls(VaultNotificationRecipientKind.MEMBER, member_id)

    def as_dict(self) -> dict[str, str]:
        return {"kind": self.kind.value, "value": self.value}


@dataclass(frozen=True)
class VaultNotificationEvent:
    event_type: str
    notification_id: str
    payload: Mapping[str, Any]


@dataclass(frozen=True)
class VaultNotification:
    notification_id: str
    vault_id: str
    severity: VaultNotificationSeverity
    title: str
    detail: str
    recipients: tuple[VaultNotificationRecipient, ...]
    source_event_id: str
    source_event_type: str
    action_required: bool
    action_code: str = ""
    action_label: str = ""
    created_at: datetime | None = None
    acknowledged_at: datetime | None = None

    @property
    def is_acknowledged(self) -> bool:
        return self.acknowledged_at is not None

    def acknowledge(self, acknowledged_at: datetime | None = None) -> "VaultNotification":
        return replace(self, acknowledged_at=acknowledged_at or _utc_now())

    def as_internal_event(self) -> VaultNotificationEvent:
        return VaultNotificationEvent(
            event_type="vault.notification.raised",
            notification_id=self.notification_id,
            payload={
                "notification_id": self.notification_id,
                "vault_id": self.vault_id,
                "severity": self.severity.value,
                "title": self.title,
                "detail": self.detail,
                "recipients": [recipient.as_dict() for recipient in self.recipients],
                "source_event_id": self.source_event_id,
                "source_event_type": self.source_event_type,
                "action_required": self.action_required,
                "action_code": self.action_code,
                "action_label": self.action_label,
                "created_at": _datetime_to_text(self.created_at),
                "acknowledged_at": _datetime_to_text(self.acknowledged_at),
            },
        )


DEFAULT_SYNC_ALERT_RECIPIENT_ROLES = ("conseil_syndical", "administrateur_local")
SYNC_ALERT_NOTIFICATION_LEVELS = (VaultSyncAlertLevel.PROTECTION, VaultSyncAlertLevel.INCIDENT)


def notifications_from_sync_alert_report(
    report: VaultSyncAlertReport,
    vault_id: str,
    *,
    recipient_roles: Iterable[str] = DEFAULT_SYNC_ALERT_RECIPIENT_ROLES,
    recipient_member_ids: Iterable[str] = (),
    source_event_id: str = "",
    created_at: datetime | None = None,
) -> tuple[VaultNotification, ...]:
    """Build internal vault notifications for sync protection and incident reports."""
    if report.level not in SYNC_ALERT_NOTIFICATION_LEVELS:
        return ()

    source_event = report.internal_events[0] if report.internal_events else None
    resolved_source_event_id = source_event_id or _source_event_id(source_event)
    source_event_type = source_event.event_type if source_event is not None else "vault.sync_alert.classified"
    severity = VaultNotificationSeverity(report.level.value)
    recipients = _recipients(recipient_roles, recipient_member_ids)
    action_code, action_label = _notification_action(report.level)
    alert_codes = ", ".join(alert.code for alert in report.alerts)
    title = _notification_title(report.level)
    detail = _notification_detail(report.level, alert_codes)
    notification_id = _notification_id(vault_id, severity, resolved_source_event_id, recipients)

    return (
        VaultNotification(
            notification_id=notification_id,
            vault_id=vault_id,
            severity=severity,
            title=title,
            detail=detail,
            recipients=recipients,
            source_event_id=resolved_source_event_id,
            source_event_type=source_event_type,
            action_required=True,
            action_code=action_code,
            action_label=action_label,
            created_at=created_at or _utc_now(),
        ),
    )


def _recipients(
    roles: Iterable[str],
    member_ids: Iterable[str],
) -> tuple[VaultNotificationRecipient, ...]:
    recipients = [VaultNotificationRecipient.role(role) for role in _dedupe_text(roles)]
    recipients.extend(VaultNotificationRecipient.member(member_id) for member_id in _dedupe_text(member_ids))
    return tuple(recipients)


def _notification_title(level: VaultSyncAlertLevel) -> str:
    if level == VaultSyncAlertLevel.INCIDENT:
        return "Incident vault a traiter"
    return "Protection vault a verifier"


def _notification_detail(level: VaultSyncAlertLevel, alert_codes: str) -> str:
    if level == VaultSyncAlertLevel.INCIDENT:
        return f"Le lot sync_alerts a classe le vault en incident: {alert_codes}."
    return f"Le lot sync_alerts demande une protection avant diffusion: {alert_codes}."


def _notification_action(level: VaultSyncAlertLevel) -> tuple[str, str]:
    if level == VaultSyncAlertLevel.INCIDENT:
        return (
            VaultSyncActionCode.LOCK_READONLY.value,
            "Controler l'integrite et maintenir le vault en lecture seule.",
        )
    return (
        VaultSyncActionCode.SUSPEND_PUBLICATION.value,
        "Nettoyer ou isoler la surface synchronisee avant publication.",
    )


def _source_event_id(event: object | None) -> str:
    if event is None:
        return "vault.sync_alert.classified:unknown"
    payload = getattr(event, "payload", {})
    text = _canonical_json(
        {
            "event_type": getattr(event, "event_type", ""),
            "level": getattr(getattr(event, "level", ""), "value", getattr(event, "level", "")),
            "code": getattr(event, "code", ""),
            "payload": payload,
        }
    )
    return "vault.sync_alert.classified:" + _short_hash(text)


def _notification_id(
    vault_id: str,
    severity: VaultNotificationSeverity,
    source_event_id: str,
    recipients: tuple[VaultNotificationRecipient, ...],
) -> str:
    recipient_keys = [f"{recipient.kind.value}:{recipient.value}" for recipient in recipients]
    text = _canonical_json(
        {
            "vault_id": vault_id,
            "severity": severity.value,
            "source_event_id": source_event_id,
            "recipients": recipient_keys,
        }
    )
    return "vault_notification_" + _short_hash(text)


def _canonical_json(value: Mapping[str, Any]) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), default=str)


def _short_hash(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]


def _dedupe_text(values: Iterable[str]) -> tuple[str, ...]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        normalized = str(value).strip()
        if not normalized or normalized in seen:
            continue
        seen.add(normalized)
        result.append(normalized)
    return tuple(result)


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _datetime_to_text(value: datetime | None) -> str:
    return "" if value is None else value.isoformat()


__all__ = [
    "DEFAULT_SYNC_ALERT_RECIPIENT_ROLES",
    "SYNC_ALERT_NOTIFICATION_LEVELS",
    "VaultNotification",
    "VaultNotificationEvent",
    "VaultNotificationRecipient",
    "VaultNotificationRecipientKind",
    "VaultNotificationSeverity",
    "notifications_from_sync_alert_report",
]
