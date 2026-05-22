from __future__ import annotations

import unittest
from datetime import date

from coproscope.core.accounts import (
    ACTION_COMMENT,
    ACTION_CREATE_ACTION,
    ACTION_MANAGE_MEMBERS,
    ACTION_READ,
    LEVEL_COMMISSION,
    LEVEL_COPRO,
    LEVEL_CS,
    ROLE_ADMINISTRATEUR_LOCAL,
    ROLE_CONSEIL_SYNDICAL,
    ROLE_CONTRIBUTEUR_COMMISSION,
    ROLE_COPROPRIETAIRE,
    AccessGrant,
    CommissionMembership,
    DeviceIdentity,
    LocalProfile,
    RecoveryShare,
    RoleGrant,
    UserAccount,
    VaultMember,
    can_member_access_resource,
    identity_summary,
    recovery_groups_for,
)


TODAY = date(2026, 5, 20)
FUTURE = date(2026, 7, 1)


class AccountsIdentityTests(unittest.TestCase):
    def _account(self) -> UserAccount:
        return UserAccount("account-alice", "Alice Martin", "alice@example.invalid")

    def _profile(self) -> LocalProfile:
        return LocalProfile("profile-laptop", "account-alice", "PC salon")

    def _member(self, member_id: str = "member-alice") -> VaultMember:
        return VaultMember(member_id, "account-alice", "vault-copro", "Alice copro", lot_refs=("A12",))

    def test_identity_summary_answers_novice_questions_for_coproprietaire(self) -> None:
        account = self._account()
        profile = self._profile()
        member = self._member()
        roles = [
            RoleGrant(
                "grant-copro",
                member.member_id,
                ROLE_COPROPRIETAIRE,
                level=LEVEL_COPRO,
                source_event_id="evt-role-copro",
            )
        ]
        devices = [
            DeviceIdentity(
                "device-laptop",
                member.member_id,
                member.vault_id,
                public_key="pub-test",
                label="PC salon",
            )
        ]
        shares = [
            RecoveryShare("share-a", member.member_id, member.vault_id, threshold=2),
            RecoveryShare("share-b", "member-bruno", member.vault_id, threshold=2),
        ]

        summary = identity_summary(
            account,
            profile,
            member,
            devices,
            roles,
            recovery_shares=shares,
            as_of=TODAY,
        )

        self.assertIn("Compte local: Alice Martin (account-alice)", summary.who_am_i)
        self.assertIn("Lots declares: A12", summary.who_am_i)
        self.assertIn("documents collectifs ouverts aux coproprietaires", summary.can_see)
        self.assertIn(ACTION_COMMENT, summary.can_do)
        self.assertIn("device-laptop", summary.active_device_ids)
        self.assertEqual(summary.inactive_role_ids, ())
        self.assertIn("collective/main: quorum actif (2/2)", summary.recovery[0])
        self.assertNotIn("aucun quorum de recuperation actif pour ce coffre", summary.warnings)

    def test_cs_role_sees_cs_level_and_can_manage_members(self) -> None:
        member = self._member("member-cs")
        roles = [RoleGrant("grant-cs", member.member_id, ROLE_CONSEIL_SYNDICAL, level=LEVEL_CS)]

        read_decision = can_member_access_resource(
            member,
            "decision",
            "decision-2026-05",
            ACTION_READ,
            LEVEL_CS,
            roles,
            as_of=TODAY,
        )
        manage_decision = can_member_access_resource(
            member,
            "membre",
            "member-new",
            ACTION_MANAGE_MEMBERS,
            LEVEL_CS,
            roles,
            as_of=TODAY,
        )

        self.assertTrue(read_decision.allowed)
        self.assertEqual(read_decision.reason, "role_allows_cs_level")
        self.assertTrue(manage_decision.allowed)
        self.assertEqual(manage_decision.matched_role, ROLE_CONSEIL_SYNDICAL)

    def test_commission_membership_is_scoped_and_revocation_preserves_history(self) -> None:
        account = self._account()
        profile = self._profile()
        member = self._member("member-jardin")
        membership = CommissionMembership(
            "membership-jardin",
            member.member_id,
            "commission-jardin",
            "espaces verts",
            role=ROLE_CONTRIBUTEUR_COMMISSION,
            starts_on=date(2026, 1, 1),
            revoked_on=date(2026, 6, 1),
            mandate_id="mandat-jardin-2026",
        )

        active_decision = can_member_access_resource(
            member,
            "note",
            "note-tonte",
            ACTION_CREATE_ACTION,
            LEVEL_COMMISSION,
            commission_memberships=[membership],
            commission_id="commission-jardin",
            as_of=TODAY,
        )
        other_commission_decision = can_member_access_resource(
            member,
            "note",
            "note-budget",
            ACTION_READ,
            LEVEL_COMMISSION,
            commission_memberships=[membership],
            commission_id="commission-comptes",
            as_of=TODAY,
        )
        future_decision = can_member_access_resource(
            member,
            "note",
            "note-tonte",
            ACTION_READ,
            LEVEL_COMMISSION,
            commission_memberships=[membership],
            commission_id="commission-jardin",
            as_of=FUTURE,
        )
        summary_after_revocation = identity_summary(
            account,
            profile,
            member,
            commission_memberships=[membership],
            as_of=FUTURE,
        )

        self.assertTrue(active_decision.allowed)
        self.assertEqual(active_decision.reason, "commission_membership_allows_scoped_access")
        self.assertFalse(other_commission_decision.allowed)
        self.assertFalse(future_decision.allowed)
        self.assertIn("commissions revoquees ou expirees conservees dans l'historique", summary_after_revocation.warnings)

    def test_explicit_access_grant_can_open_one_resource_until_revoked(self) -> None:
        member = self._member("member-reader")
        grant = AccessGrant(
            "access-contentieux-read",
            member.member_id,
            actions=(ACTION_READ,),
            resource_type="dossier",
            resource_id="contentieux-42",
            level=LEVEL_CS,
            revoked_on=date(2026, 6, 1),
            reason="mandat de lecture ponctuel",
        )

        allowed = can_member_access_resource(
            member,
            "dossier",
            "contentieux-42",
            ACTION_READ,
            LEVEL_CS,
            access_grants=[grant],
            as_of=TODAY,
        )
        denied_other_resource = can_member_access_resource(
            member,
            "dossier",
            "contentieux-99",
            ACTION_READ,
            LEVEL_CS,
            access_grants=[grant],
            as_of=TODAY,
        )
        denied_after_revocation = can_member_access_resource(
            member,
            "dossier",
            "contentieux-42",
            ACTION_READ,
            LEVEL_CS,
            access_grants=[grant],
            as_of=FUTURE,
        )

        self.assertTrue(allowed.allowed)
        self.assertEqual(allowed.reason, "explicit_access_grant")
        self.assertEqual(allowed.matched_grant_id, grant.grant_id)
        self.assertFalse(denied_other_resource.allowed)
        self.assertFalse(denied_after_revocation.allowed)

    def test_administrateur_local_has_no_implicit_content_access(self) -> None:
        account = self._account()
        profile = self._profile()
        member = self._member("member-admin")
        roles = [RoleGrant("grant-admin", member.member_id, ROLE_ADMINISTRATEUR_LOCAL, level=LEVEL_COPRO)]

        decision = can_member_access_resource(
            member,
            "piece",
            "facture-001",
            ACTION_READ,
            LEVEL_COPRO,
            roles,
            as_of=TODAY,
        )
        summary = identity_summary(account, profile, member, role_grants=roles, as_of=TODAY)

        self.assertFalse(decision.allowed)
        self.assertIn("diagnostic technique local sans droit implicite sur le contenu", summary.can_see)
        self.assertNotIn("documents collectifs ouverts aux coproprietaires", summary.can_see)

    def test_device_revocation_blocks_future_signing_but_keeps_audit_trace(self) -> None:
        account = self._account()
        profile = self._profile()
        member = self._member("member-device")
        active = DeviceIdentity("device-active", member.member_id, member.vault_id, "pub-active")
        revoked = DeviceIdentity(
            "device-revoked",
            member.member_id,
            member.vault_id,
            "pub-revoked",
            revoked_on=date(2026, 5, 1),
        )

        summary = identity_summary(account, profile, member, devices=[active, revoked], as_of=TODAY)

        self.assertTrue(active.is_active_for(member, as_of=TODAY))
        self.assertFalse(revoked.is_active_for(member, as_of=TODAY))
        self.assertEqual(summary.active_device_ids, ("device-active",))
        self.assertEqual(summary.revoked_device_ids, ("device-revoked",))

    def test_recovery_groups_require_quorum_and_ignore_revoked_shares(self) -> None:
        shares = [
            RecoveryShare("share-a", "member-a", "vault-copro", threshold=3),
            RecoveryShare("share-b", "member-b", "vault-copro", threshold=3),
            RecoveryShare("share-c", "member-c", "vault-copro", threshold=3, revoked_on=date(2026, 5, 1)),
            RecoveryShare("share-d", "member-d", "vault-copro", key_scope="commission:jardin", threshold=1),
        ]

        groups = recovery_groups_for(shares, "vault-copro", as_of=TODAY)
        collective = [group for group in groups if group.key_scope == "collective"][0]
        commission = [group for group in groups if group.key_scope == "commission:jardin"][0]

        self.assertFalse(collective.can_recover)
        self.assertEqual(collective.active_share_count, 2)
        self.assertEqual(collective.threshold, 3)
        self.assertIn("quorum insuffisant", collective.warnings)
        self.assertFalse(commission.can_recover)
        self.assertIn("seuil inferieur a 2: risque de confiscation par une seule personne", commission.warnings)


if __name__ == "__main__":
    unittest.main()
