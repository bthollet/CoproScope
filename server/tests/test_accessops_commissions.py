from __future__ import annotations

import unittest
from datetime import date

from coproscope.modules.accessops import (
    ROLE_COMMISSION_MEMBER,
    ROLE_COMMISSION_REFERENT_CS,
    ROLE_CONSEIL_SYNDICAL,
    ROLE_COPROPRIETAIRE,
    SCOPE_COMMISSION,
    AccessDecision,
    Commission,
    CommissionMandate,
    CommissionProduction,
    Member,
    RoleGrant,
    can_access_college,
    can_access_production,
    visible_productions,
)


TODAY = date(2026, 5, 20)
FUTURE = date(2026, 7, 1)


class AccessOpsCommissionTests(unittest.TestCase):
    def test_conseil_syndical_sees_cs_level(self) -> None:
        member = Member("m-cs", "Alice CS")
        grants = [RoleGrant(member_id=member.member_id, role=ROLE_CONSEIL_SYNDICAL)]

        decision = can_access_college(member, "C4_Conseil_Syndical", grants, as_of=TODAY)

        self.assertIsInstance(decision, AccessDecision)
        self.assertTrue(decision.allowed)
        self.assertEqual(decision.reason, "college_allowed")
        self.assertEqual(decision.matched_role, ROLE_CONSEIL_SYNDICAL)

    def test_coproprietaire_sees_copro_level_only(self) -> None:
        member = Member("m-copro", "Bruno Copro")
        grants = [RoleGrant(member_id=member.member_id, role=ROLE_COPROPRIETAIRE)]

        copro_decision = can_access_college(member, "C2_Coproprietaires", grants, as_of=TODAY)
        cs_decision = can_access_college(member, "C4_Conseil_Syndical", grants, as_of=TODAY)

        self.assertTrue(copro_decision.allowed)
        self.assertFalse(cs_decision.allowed)
        self.assertEqual(cs_decision.reason, "insufficient_college")

    def test_commission_member_sees_only_non_expired_thematic_mandate(self) -> None:
        member = Member("m-commission", "Camille Commission")
        grants = [
            RoleGrant(member_id=member.member_id, role=ROLE_COPROPRIETAIRE),
            RoleGrant(
                member_id=member.member_id,
                role=ROLE_COMMISSION_MEMBER,
                scope_type=SCOPE_COMMISSION,
                scope_id="commission-travaux",
            ),
        ]
        commissions = [Commission("commission-travaux", "Commission travaux", "travaux")]
        mandates = [
            CommissionMandate(
                "mandat-travaux-2026",
                "commission-travaux",
                "travaux",
                starts_on=date(2026, 1, 1),
                expires_on=date(2026, 12, 31),
            ),
            CommissionMandate(
                "mandat-finances-2026",
                "commission-travaux",
                "finances",
                starts_on=date(2026, 1, 1),
                expires_on=date(2026, 12, 31),
            ),
            CommissionMandate(
                "mandat-travaux-2025",
                "commission-travaux",
                "travaux",
                starts_on=date(2025, 1, 1),
                expires_on=date(2025, 12, 31),
            ),
        ]
        productions = [
            CommissionProduction(
                "prod-travaux-active",
                "commission-travaux",
                "Analyse devis toiture",
                "travaux",
                mandate_id="mandat-travaux-2026",
            ),
            CommissionProduction(
                "prod-finances-active",
                "commission-travaux",
                "Lecture budget",
                "finances",
                mandate_id="mandat-finances-2026",
            ),
            CommissionProduction(
                "prod-travaux-expired",
                "commission-travaux",
                "Historique toiture 2025",
                "travaux",
                mandate_id="mandat-travaux-2025",
            ),
        ]

        visible = visible_productions(member, productions, grants, mandates, commissions, as_of=TODAY)

        self.assertEqual([production.production_id for production in visible], ["prod-travaux-active"])
        self.assertTrue(
            can_access_production(member, productions[0], grants, mandates, commissions, as_of=TODAY).allowed
        )
        self.assertFalse(
            can_access_production(member, productions[1], grants, mandates, commissions, as_of=TODAY).allowed
        )
        self.assertFalse(
            can_access_production(member, productions[2], grants, mandates, commissions, as_of=TODAY).allowed
        )

    def test_referent_cs_sees_commission_productions(self) -> None:
        member = Member("m-referent", "Dana Referente CS")
        grants = [
            RoleGrant(
                member_id=member.member_id,
                role=ROLE_COMMISSION_REFERENT_CS,
                scope_type=SCOPE_COMMISSION,
                scope_id="commission-energie",
            )
        ]
        commissions = [Commission("commission-energie", "Commission energie", "energie")]
        mandates = [
            CommissionMandate(
                "mandat-energie-2026",
                "commission-energie",
                "energie",
                starts_on=date(2026, 1, 1),
                expires_on=date(2026, 12, 31),
            )
        ]
        production = CommissionProduction(
            "prod-energie",
            "commission-energie",
            "Synthese chauffage",
            "energie",
            mandate_id="mandat-energie-2026",
        )

        decision = can_access_production(member, production, grants, mandates, commissions, as_of=TODAY)

        self.assertTrue(decision.allowed)
        self.assertEqual(decision.reason, "commission_referent_allowed")
        self.assertEqual(decision.matched_role, ROLE_COMMISSION_REFERENT_CS)

    def test_crossed_governance_rights_stay_scoped_to_the_named_commission(self) -> None:
        member = Member("m-asl", "Fatima ASL")
        grants = [
            RoleGrant(
                member_id=member.member_id,
                role=ROLE_COMMISSION_MEMBER,
                scope_type=SCOPE_COMMISSION,
                scope_id="asl-voirie",
            )
        ]
        commissions = [
            Commission("asl-voirie", "ASL voirie", "voirie"),
            Commission("syndicat-secondaire-bat-a", "Syndicat secondaire batiment A", "voirie"),
            Commission("union-chaufferie", "Union chaufferie", "energie"),
        ]
        mandates = [
            CommissionMandate(
                "mandat-asl-2026",
                "asl-voirie",
                "voirie",
                starts_on=date(2026, 1, 1),
                expires_on=date(2026, 12, 31),
            ),
            CommissionMandate(
                "mandat-secondaire-2026",
                "syndicat-secondaire-bat-a",
                "voirie",
                starts_on=date(2026, 1, 1),
                expires_on=date(2026, 12, 31),
            ),
            CommissionMandate(
                "mandat-union-2026",
                "union-chaufferie",
                "energie",
                starts_on=date(2026, 1, 1),
                expires_on=date(2026, 12, 31),
            ),
        ]
        productions = [
            CommissionProduction("prod-asl-voirie", "asl-voirie", "Portail ASL", "voirie"),
            CommissionProduction(
                "prod-secondaire-voirie",
                "syndicat-secondaire-bat-a",
                "Acces batiment A",
                "voirie",
            ),
            CommissionProduction("prod-union-energie", "union-chaufferie", "Chaufferie commune", "energie"),
        ]

        visible = visible_productions(member, productions, grants, mandates, commissions, as_of=TODAY)
        secondary_decision = can_access_production(
            member,
            productions[1],
            grants,
            mandates,
            commissions,
            as_of=TODAY,
        )
        union_decision = can_access_production(member, productions[2], grants, mandates, commissions, as_of=TODAY)

        self.assertEqual([production.production_id for production in visible], ["prod-asl-voirie"])
        self.assertFalse(secondary_decision.allowed)
        self.assertEqual(secondary_decision.reason, "missing_active_commission_role")
        self.assertFalse(union_decision.allowed)
        self.assertEqual(union_decision.reason, "missing_active_commission_role")

    def test_revocation_and_expired_mandate_block_future_access_without_deleting_history(self) -> None:
        member = Member("m-history", "Eli Historique")
        revoked_grant = RoleGrant(
            member_id=member.member_id,
            role=ROLE_COMMISSION_MEMBER,
            scope_type=SCOPE_COMMISSION,
            scope_id="commission-jardin",
            revoked_on=date(2026, 6, 1),
        )
        active_grant = RoleGrant(
            member_id=member.member_id,
            role=ROLE_COMMISSION_MEMBER,
            scope_type=SCOPE_COMMISSION,
            scope_id="commission-jardin",
        )
        commissions = [Commission("commission-jardin", "Commission jardin", "jardin")]
        mandates = [
            CommissionMandate(
                "mandat-jardin-printemps",
                "commission-jardin",
                "jardin",
                starts_on=date(2026, 3, 1),
                expires_on=date(2026, 6, 15),
            )
        ]
        production = CommissionProduction(
            "prod-jardin",
            "commission-jardin",
            "Compte-rendu espaces verts",
            "jardin",
            mandate_id="mandat-jardin-printemps",
        )
        history = [production]

        self.assertTrue(
            can_access_production(member, production, [revoked_grant], mandates, commissions, as_of=TODAY).allowed
        )
        self.assertFalse(
            can_access_production(member, production, [revoked_grant], mandates, commissions, as_of=FUTURE).allowed
        )
        self.assertFalse(
            can_access_production(member, production, [active_grant], mandates, commissions, as_of=FUTURE).allowed
        )
        self.assertEqual(visible_productions(member, history, [active_grant], mandates, commissions, as_of=FUTURE), [])
        self.assertEqual([item.production_id for item in history], ["prod-jardin"])


if __name__ == "__main__":
    unittest.main()
