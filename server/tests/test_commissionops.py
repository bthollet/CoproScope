from __future__ import annotations

import unittest
from datetime import date

from coproscope.core.accounts import (
    LEVEL_COMMISSION,
    ROLE_CONSEIL_SYNDICAL,
    ROLE_CONTRIBUTEUR_COMMISSION,
    ROLE_COPROPRIETAIRE,
    ROLE_REFERENT_COMMISSION,
    CommissionMembership,
    RoleGrant,
    VaultMember,
)
from coproscope.modules.commissionops import (
    DIFFUSION_COMMISSION,
    DIFFUSION_COPRO,
    DIFFUSION_CS,
    PRODUCTION_DRAFT,
    PRODUCTION_VALIDATED,
    Commission,
    CommissionMandate,
    CommissionProduction,
    active_memberships_for_commission,
    can_read_production,
    can_validate_production,
    novice_summary,
    shareable_productions,
    visible_productions,
)


TODAY = date(2026, 5, 20)
FUTURE = date(2026, 7, 1)


class CommissionOpsTests(unittest.TestCase):
    def _member(self, member_id: str, name: str | None = None) -> VaultMember:
        return VaultMember(member_id, f"account-{member_id}", "vault-copro", name or member_id)

    def test_active_memberships_are_scoped_by_commission_subject_and_period(self) -> None:
        commission = Commission(
            "commission-energie",
            "Commission energie",
            "chauffage collectif",
            referent_member_id="member-cs",
        )
        memberships = [
            CommissionMembership(
                "membership-active",
                "member-ana",
                commission.commission_id,
                "chauffage collectif",
                starts_on=date(2026, 1, 1),
                expires_on=date(2026, 12, 31),
            ),
            CommissionMembership(
                "membership-other-subject",
                "member-ben",
                commission.commission_id,
                "jardin",
                starts_on=date(2026, 1, 1),
                expires_on=date(2026, 12, 31),
            ),
            CommissionMembership(
                "membership-expired",
                "member-camille",
                commission.commission_id,
                "chauffage collectif",
                starts_on=date(2025, 1, 1),
                expires_on=date(2025, 12, 31),
            ),
        ]

        active = active_memberships_for_commission(commission, memberships, as_of=TODAY)

        self.assertEqual([membership.membership_id for membership in active], ["membership-active"])

    def test_commission_production_visibility_reuses_account_access_levels(self) -> None:
        member = self._member("member-ana", "Ana")
        commission_membership = CommissionMembership(
            "membership-energie",
            member.member_id,
            "commission-energie",
            "chauffage",
            role=ROLE_CONTRIBUTEUR_COMMISSION,
        )
        commission_note = CommissionProduction(
            "prod-note",
            "commission-energie",
            "mandate-energie",
            "Notes de visite chaufferie",
            "chauffage",
            diffusion=DIFFUSION_COMMISSION,
        )
        cs_note = CommissionProduction(
            "prod-cs",
            "commission-energie",
            "mandate-energie",
            "Synthese CS",
            "chauffage",
            diffusion=DIFFUSION_CS,
        )
        copro_note = CommissionProduction(
            "prod-copro",
            "commission-energie",
            "mandate-energie",
            "Version coproprietaires",
            "chauffage",
            diffusion=DIFFUSION_COPRO,
        )
        copro_role = RoleGrant("grant-copro", member.member_id, ROLE_COPROPRIETAIRE)

        commission_decision = can_read_production(
            member,
            commission_note,
            role_grants=[copro_role],
            commission_memberships=[commission_membership],
            as_of=TODAY,
        )
        cs_decision = can_read_production(
            member,
            cs_note,
            role_grants=[copro_role],
            commission_memberships=[commission_membership],
            as_of=TODAY,
        )
        visible = visible_productions(
            member,
            [commission_note, cs_note, copro_note],
            role_grants=[copro_role],
            commission_memberships=[commission_membership],
            as_of=TODAY,
        )

        self.assertTrue(commission_decision.allowed)
        self.assertEqual(commission_decision.reason, "commission_membership_allows_scoped_access")
        self.assertFalse(cs_decision.allowed)
        self.assertEqual([production.production_id for production in visible], ["prod-note", "prod-copro"])

    def test_referent_cs_or_cs_role_can_validate_active_mandate(self) -> None:
        referent = self._member("member-cs", "Claire CS")
        other_cs = self._member("member-other-cs", "Omar CS")
        outsider = self._member("member-outsider", "Olivia")
        commission = Commission(
            "commission-travaux",
            "Commission travaux",
            "toiture",
            referent_member_id=referent.member_id,
            starts_on=date(2026, 1, 1),
            expires_on=date(2026, 12, 31),
        )
        mandate = CommissionMandate(
            "mandate-toiture",
            commission.commission_id,
            "toiture",
            starts_on=date(2026, 1, 1),
            expires_on=date(2026, 12, 31),
        )

        referent_decision = can_validate_production(referent, commission, mandate, as_of=TODAY)
        cs_decision = can_validate_production(
            other_cs,
            commission,
            mandate,
            role_grants=[RoleGrant("grant-cs", other_cs.member_id, ROLE_CONSEIL_SYNDICAL)],
            as_of=TODAY,
        )
        outsider_decision = can_validate_production(outsider, commission, mandate, as_of=TODAY)

        self.assertTrue(referent_decision.allowed)
        self.assertEqual(referent_decision.reason, "named_validator")
        self.assertTrue(cs_decision.allowed)
        self.assertEqual(cs_decision.reason, "cs_role_validator")
        self.assertFalse(outsider_decision.allowed)
        self.assertEqual(outsider_decision.reason, "not_a_validator")

    def test_referent_membership_can_validate_without_global_cs_role(self) -> None:
        referent = self._member("member-referent", "Rita")
        commission = Commission("commission-jardin", "Commission jardin", "espaces verts", referent_member_id="")
        mandate = CommissionMandate(
            "mandate-jardin",
            commission.commission_id,
            "espaces verts",
            starts_on=date(2026, 1, 1),
            expires_on=date(2026, 12, 31),
        )
        membership = CommissionMembership(
            "membership-referent",
            referent.member_id,
            commission.commission_id,
            "espaces verts",
            role=ROLE_REFERENT_COMMISSION,
            starts_on=date(2026, 1, 1),
            expires_on=date(2026, 12, 31),
        )

        decision = can_validate_production(
            referent,
            commission,
            mandate,
            commission_memberships=[membership],
            as_of=TODAY,
        )

        self.assertTrue(decision.allowed)
        self.assertEqual(decision.reason, "commission_referent_validator")

    def test_expired_mandate_blocks_validation_but_keeps_history_visible_to_cs(self) -> None:
        cs = self._member("member-cs", "Claire CS")
        commission = Commission("commission-eau", "Commission eau", "fuites", referent_member_id=cs.member_id)
        expired_mandate = CommissionMandate(
            "mandate-fuites",
            commission.commission_id,
            "fuites",
            starts_on=date(2026, 1, 1),
            expires_on=date(2026, 6, 1),
        )
        production = CommissionProduction(
            "prod-fuites",
            commission.commission_id,
            expired_mandate.mandate_id,
            "Historique fuites",
            "fuites",
            proof_refs=("DOC-FUITE-1",),
            diffusion=DIFFUSION_CS,
            status=PRODUCTION_VALIDATED,
            validated_by_member_id=cs.member_id,
        )

        validate_after_expiry = can_validate_production(cs, commission, expired_mandate, as_of=FUTURE)
        visible_after_expiry = visible_productions(
            cs,
            [production],
            role_grants=[RoleGrant("grant-cs", cs.member_id, ROLE_CONSEIL_SYNDICAL)],
            as_of=FUTURE,
        )

        self.assertFalse(validate_after_expiry.allowed)
        self.assertEqual(validate_after_expiry.reason, "mandate_inactive_or_outside_subject")
        self.assertEqual([item.production_id for item in visible_after_expiry], ["prod-fuites"])

    def test_novice_summary_answers_who_validates_and_what_can_be_shared(self) -> None:
        referent = self._member("member-cs", "Claire CS")
        contributor = self._member("member-ana", "Ana")
        validator = self._member("member-val", "Victor")
        commission = Commission(
            "commission-energie",
            "Commission energie",
            "chauffage",
            referent_member_id=referent.member_id,
            member_ids=(contributor.member_id,),
        )
        mandate = CommissionMandate(
            "mandate-energie",
            commission.commission_id,
            "chauffage",
            starts_on=date(2026, 1, 1),
            expires_on=date(2026, 12, 31),
            validator_member_ids=(validator.member_id,),
        )
        validated = CommissionProduction(
            "prod-synthese",
            commission.commission_id,
            mandate.mandate_id,
            "Synthese diffusable chauffage",
            "chauffage",
            proof_refs=("DOC-CHAUF-1",),
            action_refs=("ACT-CHAUF-1",),
            diffusion=DIFFUSION_COPRO,
            status=PRODUCTION_VALIDATED,
            validated_by_member_id=referent.member_id,
        )
        draft = CommissionProduction(
            "prod-brouillon",
            commission.commission_id,
            mandate.mandate_id,
            "Brouillon visite",
            "chauffage",
            diffusion=DIFFUSION_CS,
            status=PRODUCTION_DRAFT,
        )

        summary = novice_summary(
            commission,
            mandate,
            [validated, draft],
            members=[referent, contributor, validator],
            as_of=TODAY,
        )

        self.assertIn("Referent CS: Claire CS", summary.qui_participe)
        self.assertIn("Membre: Ana", summary.qui_participe)
        self.assertIn("Validateur nomme: Victor", summary.qui_valide)
        self.assertEqual(
            summary.ce_qui_peut_etre_partage,
            ("Coproprietaires: Synthese diffusable chauffage (prod-synthese)",),
        )
        self.assertIn("production sans preuve/action rattachee: prod-brouillon", summary.warnings)
        self.assertEqual([production.production_id for production in shareable_productions([validated, draft])], ["prod-synthese"])

    def test_named_validator_must_still_match_active_subject(self) -> None:
        validator = self._member("member-val", "Victor")
        commission = Commission("commission-finances", "Commission finances", "budget", referent_member_id="")
        wrong_subject = CommissionMandate(
            "mandate-wrong",
            commission.commission_id,
            "travaux",
            starts_on=date(2026, 1, 1),
            expires_on=date(2026, 12, 31),
            validator_member_ids=(validator.member_id,),
        )

        decision = can_validate_production(validator, commission, wrong_subject, as_of=TODAY)

        self.assertFalse(decision.allowed)
        self.assertEqual(decision.reason, "mandate_inactive_or_outside_subject")


if __name__ == "__main__":
    unittest.main()
