from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Iterable

from ..core.privacy import ACCESS_RANK, normalize_college


ROLE_OCCUPANT = "occupant"
ROLE_COPROPRIETAIRE = "coproprietaire"
ROLE_CONSEIL_SYNDICAL = "conseil_syndical"
ROLE_SYNDIC = "syndic"
ROLE_COMMISSION_MEMBER = "commission_member"
ROLE_COMMISSION_REFERENT_CS = "commission_referent_cs"

SCOPE_GLOBAL = "global"
SCOPE_COMMISSION = "commission"

ROLE_ACCESS_COLLEGES = {
    ROLE_OCCUPANT: "C1_Occupants_Usagers",
    ROLE_COPROPRIETAIRE: "C2_Coproprietaires",
    ROLE_CONSEIL_SYNDICAL: "C4_Conseil_Syndical",
    "cs": "C4_Conseil_Syndical",
    ROLE_SYNDIC: "C5_Syndic_Admin",
}

COMMISSION_MEMBER_ROLES = {ROLE_COMMISSION_MEMBER, "membre_commission"}
COMMISSION_REFERENT_ROLES = {
    ROLE_COMMISSION_REFERENT_CS,
    "referent_cs",
    "referent_conseil_syndical",
}


DateLike = date | datetime | str | None


@dataclass(frozen=True)
class Member:
    member_id: str
    display_name: str = ""
    default_college: str = "C0_Public"


@dataclass(frozen=True)
class RoleGrant:
    member_id: str
    role: str
    scope_type: str = SCOPE_GLOBAL
    scope_id: str = ""
    starts_on: DateLike = None
    expires_on: DateLike = None
    revoked_on: DateLike = None
    grant_id: str = ""

    def is_active_for(self, member: Member | str, as_of: DateLike = None) -> bool:
        member_id = member.member_id if isinstance(member, Member) else member
        return self.member_id == member_id and _is_active_window(
            as_of=as_of,
            starts_on=self.starts_on,
            expires_on=self.expires_on,
            revoked_on=self.revoked_on,
        )


@dataclass(frozen=True)
class Commission:
    commission_id: str
    label: str
    theme: str
    active: bool = True


@dataclass(frozen=True)
class CommissionMandate:
    mandate_id: str
    commission_id: str
    theme: str
    starts_on: DateLike
    expires_on: DateLike
    title: str = ""
    revoked_on: DateLike = None

    def is_active(self, as_of: DateLike = None) -> bool:
        return _is_active_window(
            as_of=as_of,
            starts_on=self.starts_on,
            expires_on=self.expires_on,
            revoked_on=self.revoked_on,
        )


@dataclass(frozen=True)
class CommissionProduction:
    production_id: str
    commission_id: str
    title: str
    theme: str
    mandate_id: str = ""
    access_college: str = "C4_Conseil_Syndical"
    produced_on: DateLike = None
    source_doc_ids: tuple[str, ...] = field(default_factory=tuple)


@dataclass(frozen=True)
class AccessDecision:
    allowed: bool
    reason: str
    member_id: str
    resource_id: str
    access_college: str = ""
    matched_role: str = ""
    matched_mandate_id: str = ""


def member_clearance(member: Member, grants: Iterable[RoleGrant], as_of: DateLike = None) -> str:
    clearance = normalize_college(member.default_college, default="C0_Public")
    for grant in grants:
        if not grant.is_active_for(member, as_of=as_of):
            continue
        if _role_key(grant.role) not in ROLE_ACCESS_COLLEGES:
            continue
        if grant.scope_type not in {"", SCOPE_GLOBAL, "copropriete"}:
            continue
        grant_college = normalize_college(ROLE_ACCESS_COLLEGES[_role_key(grant.role)], default=clearance)
        if ACCESS_RANK[grant_college] > ACCESS_RANK[clearance]:
            clearance = grant_college
    return clearance


def can_access_college(
    member: Member,
    access_college: str,
    grants: Iterable[RoleGrant],
    as_of: DateLike = None,
    *,
    resource_id: str = "",
) -> AccessDecision:
    grants = tuple(grants)
    target_college = normalize_college(access_college, default="C4_Conseil_Syndical")
    clearance = member_clearance(member, grants, as_of=as_of)
    allowed = ACCESS_RANK[target_college] <= ACCESS_RANK[clearance]
    return AccessDecision(
        allowed=allowed,
        reason="college_allowed" if allowed else "insufficient_college",
        member_id=member.member_id,
        resource_id=resource_id or target_college,
        access_college=target_college,
        matched_role=_role_for_clearance(member, grants, clearance, as_of=as_of) if allowed else "",
    )


def can_access_production(
    member: Member,
    production: CommissionProduction,
    grants: Iterable[RoleGrant],
    mandates: Iterable[CommissionMandate],
    commissions: Iterable[Commission] = (),
    as_of: DateLike = None,
) -> AccessDecision:
    grants = tuple(grants)
    mandates = tuple(mandates)
    commission = _commission_for(production.commission_id, commissions)
    if commission is not None and not commission.active:
        return _deny(member, production, "commission_inactive")
    if commission is not None and not _same_theme(commission.theme, production.theme):
        return _deny(member, production, "production_outside_commission_theme")

    college_decision = can_access_college(
        member,
        production.access_college,
        grants,
        as_of=as_of,
        resource_id=production.production_id,
    )
    if college_decision.allowed:
        return college_decision

    mandate = _matching_active_mandate(production, mandates, as_of=as_of)
    if mandate is None:
        return _deny(member, production, "missing_active_thematic_mandate")

    for grant in _active_commission_grants(member, grants, production.commission_id, as_of=as_of):
        role = _role_key(grant.role)
        if role in COMMISSION_REFERENT_ROLES:
            return _allow(member, production, "commission_referent_allowed", grant, mandate)
        if role in COMMISSION_MEMBER_ROLES:
            return _allow(member, production, "commission_mandate_allowed", grant, mandate)

    return _deny(member, production, "missing_active_commission_role")


def visible_productions(
    member: Member,
    productions: Iterable[CommissionProduction],
    grants: Iterable[RoleGrant],
    mandates: Iterable[CommissionMandate],
    commissions: Iterable[Commission] = (),
    as_of: DateLike = None,
) -> list[CommissionProduction]:
    grant_list = tuple(grants)
    mandate_list = tuple(mandates)
    commission_list = tuple(commissions)
    return [
        production
        for production in productions
        if can_access_production(
            member,
            production,
            grant_list,
            mandate_list,
            commission_list,
            as_of=as_of,
        ).allowed
    ]


def _allow(
    member: Member,
    production: CommissionProduction,
    reason: str,
    grant: RoleGrant,
    mandate: CommissionMandate,
) -> AccessDecision:
    return AccessDecision(
        allowed=True,
        reason=reason,
        member_id=member.member_id,
        resource_id=production.production_id,
        access_college=normalize_college(production.access_college, default="C4_Conseil_Syndical"),
        matched_role=grant.role,
        matched_mandate_id=mandate.mandate_id,
    )


def _deny(member: Member, production: CommissionProduction, reason: str) -> AccessDecision:
    return AccessDecision(
        allowed=False,
        reason=reason,
        member_id=member.member_id,
        resource_id=production.production_id,
        access_college=normalize_college(production.access_college, default="C4_Conseil_Syndical"),
    )


def _active_commission_grants(
    member: Member,
    grants: Iterable[RoleGrant],
    commission_id: str,
    as_of: DateLike = None,
) -> Iterable[RoleGrant]:
    for grant in grants:
        if not grant.is_active_for(member, as_of=as_of):
            continue
        if grant.scope_type != SCOPE_COMMISSION or grant.scope_id != commission_id:
            continue
        if _role_key(grant.role) in COMMISSION_MEMBER_ROLES | COMMISSION_REFERENT_ROLES:
            yield grant


def _matching_active_mandate(
    production: CommissionProduction,
    mandates: Iterable[CommissionMandate],
    as_of: DateLike = None,
) -> CommissionMandate | None:
    for mandate in mandates:
        if mandate.commission_id != production.commission_id:
            continue
        if production.mandate_id and mandate.mandate_id != production.mandate_id:
            continue
        if not _same_theme(mandate.theme, production.theme):
            continue
        if mandate.is_active(as_of=as_of):
            return mandate
    return None


def _commission_for(commission_id: str, commissions: Iterable[Commission]) -> Commission | None:
    commission_list = tuple(commissions)
    if not commission_list:
        return None
    for commission in commission_list:
        if commission.commission_id == commission_id:
            return commission
    return Commission(commission_id=commission_id, label="", theme="", active=False)


def _role_for_clearance(
    member: Member,
    grants: Iterable[RoleGrant],
    clearance: str,
    as_of: DateLike = None,
) -> str:
    for grant in grants:
        role = _role_key(grant.role)
        if not grant.is_active_for(member, as_of=as_of):
            continue
        if ROLE_ACCESS_COLLEGES.get(role) == clearance:
            return grant.role
    return ""


def _is_active_window(
    *,
    as_of: DateLike = None,
    starts_on: DateLike = None,
    expires_on: DateLike = None,
    revoked_on: DateLike = None,
) -> bool:
    current = _as_date(as_of) or date.today()
    starts = _as_date(starts_on)
    expires = _as_date(expires_on)
    revoked = _as_date(revoked_on)
    if starts is not None and current < starts:
        return False
    if expires is not None and current > expires:
        return False
    if revoked is not None and current >= revoked:
        return False
    return True


def _as_date(value: DateLike) -> date | None:
    if value is None:
        return None
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    if isinstance(value, str):
        if not value.strip():
            return None
        return date.fromisoformat(value[:10])
    raise TypeError(f"Unsupported date value: {value!r}")


def _role_key(role: str) -> str:
    return role.strip().lower()


def _same_theme(left: str, right: str) -> bool:
    return left.strip().lower() == right.strip().lower()
