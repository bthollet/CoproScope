from __future__ import annotations

from datetime import datetime, timezone
import unittest

from coproscope.vault.notifications import (
    VaultNotificationRecipientKind,
    VaultNotificationSeverity,
    notifications_from_sync_alert_report,
)
from coproscope.vault.sync_alerts import (
    VaultIntegrityFinding,
    VaultSyncAlertLevel,
    classify_vault_sync_audit,
)
from coproscope.vault.sync_profiles import SyncAudit


class VaultNotificationsTests(unittest.TestCase):
    def test_protection_sync_alert_creates_internal_notification_event(self) -> None:
        report = classify_vault_sync_audit(
            SyncAudit(
                path="C:/vault/sync",
                profile_id="local_folder",
                forbidden_entries=(".git", "tmp_exports"),
                conflict_markers=(),
            )
        )
        created_at = datetime(2026, 5, 20, 18, 30, tzinfo=timezone.utc)

        notifications = notifications_from_sync_alert_report(
            report,
            "vault-copro",
            recipient_roles=("conseil_syndical", "administrateur_local", "conseil_syndical"),
            recipient_member_ids=("member-alice",),
            created_at=created_at,
        )

        self.assertEqual(len(notifications), 1)
        notification = notifications[0]
        self.assertEqual(notification.severity, VaultNotificationSeverity.PROTECTION)
        self.assertTrue(notification.action_required)
        self.assertEqual(notification.action_code, "suspend_publication")
        self.assertEqual(notification.source_event_type, "vault.sync_alert.classified")
        self.assertEqual(
            tuple((recipient.kind, recipient.value) for recipient in notification.recipients),
            (
                (VaultNotificationRecipientKind.ROLE, "conseil_syndical"),
                (VaultNotificationRecipientKind.ROLE, "administrateur_local"),
                (VaultNotificationRecipientKind.MEMBER, "member-alice"),
            ),
        )

        event = notification.as_internal_event()
        self.assertEqual(event.event_type, "vault.notification.raised")
        self.assertEqual(event.payload["created_at"], "2026-05-20T18:30:00+00:00")
        self.assertEqual(event.payload["acknowledged_at"], "")
        self.assertNotIn("email", event.payload)
        self.assertNotIn("sms", event.payload)

    def test_incident_sync_alert_keeps_source_event_and_requires_read_only_action(self) -> None:
        report = classify_vault_sync_audit(
            SyncAudit(
                path="C:/vault/sync",
                profile_id="local_folder",
                forbidden_entries=(),
                conflict_markers=(),
            ),
            integrity_findings=[
                VaultIntegrityFinding(
                    code="invalid_signature",
                    detail="signature does not verify",
                    path="events/device-a/000001.json",
                )
            ],
        )

        notifications = notifications_from_sync_alert_report(
            report,
            "vault-copro",
            source_event_id="evt-sync-alert-1",
        )

        self.assertEqual(len(notifications), 1)
        notification = notifications[0]
        self.assertEqual(notification.severity, VaultNotificationSeverity.INCIDENT)
        self.assertEqual(notification.source_event_id, "evt-sync-alert-1")
        self.assertEqual(notification.action_code, "lock_readonly")
        self.assertIn("lecture seule", notification.action_label)

    def test_information_and_attention_sync_alerts_do_not_create_notifications(self) -> None:
        clean_report = classify_vault_sync_audit(
            SyncAudit(
                path="C:/vault/sync",
                profile_id="local_folder",
                forbidden_entries=(),
                conflict_markers=(),
            ),
            sync_active=True,
        )
        attention_report = classify_vault_sync_audit(
            SyncAudit(
                path="C:/vault/sync",
                profile_id="dropbox",
                forbidden_entries=(),
                conflict_markers=("budget conflicted copy.xlsx",),
            )
        )

        self.assertEqual(clean_report.level, VaultSyncAlertLevel.INFORMATION)
        self.assertEqual(attention_report.level, VaultSyncAlertLevel.ATTENTION)
        self.assertEqual(notifications_from_sync_alert_report(clean_report, "vault-copro"), ())
        self.assertEqual(notifications_from_sync_alert_report(attention_report, "vault-copro"), ())

    def test_acknowledge_returns_a_new_notification_with_acknowledged_at(self) -> None:
        report = classify_vault_sync_audit(
            SyncAudit(
                path="C:/vault/sync",
                profile_id="local_folder",
                forbidden_entries=(".venv",),
                conflict_markers=(),
            )
        )
        notification = notifications_from_sync_alert_report(report, "vault-copro")[0]
        acknowledged_at = datetime(2026, 5, 20, 19, 0, tzinfo=timezone.utc)

        acknowledged = notification.acknowledge(acknowledged_at)

        self.assertFalse(notification.is_acknowledged)
        self.assertTrue(acknowledged.is_acknowledged)
        self.assertEqual(acknowledged.acknowledged_at, acknowledged_at)
        self.assertEqual(acknowledged.as_internal_event().payload["acknowledged_at"], "2026-05-20T19:00:00+00:00")


if __name__ == "__main__":
    unittest.main()
