from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Iterable

from ..core.accounts import (
    ACTION_READ,
    LEVEL_COMMISSION,
    LEVEL_COPRO,
    LEVEL_CS,
    ROLE_CONSEIL_SYNDICAL,
    ROLE_REFERENT_COMMISSION,
    AccessGrant,
    CommissionMembership,
    RoleGrant,
    VaultMember,
    can_member_access_resource,
)


DateLike = date | datetime | str | None

DIFFUSION_COMMISSION = "commission"
DIFFUSION_CS = "cs"
DIFFUSION_COPRO = "copro"
DIFFUSION_PUBLIC = "public"

DIFFUSION_LEVELS = {
    DIFFUSION_COMMISSION: LEVEL_COMMISSION,
    DIFFUSION_CS: LEVEL_CS,
    DIFFUSION_COPRO: LEVEL_COPRO,
    DIFFUSION_PUBLIC: LEVEL_COPRO,
}

PRODUCTION_DRAFT = "draft"
PRODUCTION_READY = "ready"
PRODUCTION_VALIDATED = "validated"


@dataclass(frozen=True)
class Commission:
    commission_id: str
    label: str
    subject: str
    referent_member_id: str
    member_ids: tuple[str, ...] = field(default_factory=tuple)
    starts_on: DateLike = None
    expires_on: DateLike = None
    revoked_on: DateLike = None
    diffusion_default: str = DIFFUSION_CS
    source_event_id: str = ""

    def is_active(self, as_of: DateLike = None) -> bool:
        return _is_active_window(
            as_of=as_of,
            starts_on=self.starts_on,
            expires_on=self.expires_on,
            revoked_on=self.revoked_on,
        )

    def participant_ids(self) -> tuple[str, ...]:
        return _dedupe((self.referent_member_id, *self.member_ids))


@dataclass(frozen=True)
class CommissionMandate:
    mandate_id: str
    commission_id: str
    subject: str
    starts_on: DateLike
    expires_on: DateLike
    validator_member_ids: tuple[str, ...] = field(default_factory=tuple)
    validating_body: str = "conseil_syndical"
    source_decision_action_id: str = ""
    source_event_id: str = ""
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
    mandate_id: str
    title: str
    subject: str
    produced_on: DateLike = None
    author_member_ids: tuple[str, ...] = field(default_factory=tuple)
    proof_refs: tuple[str, ...] = field(default_factory=tuple)
    action_refs: tuple[str, ...] = field(default_factory=tuple)
    diffusion: str = DIFFUSION_CS
    status: str = PRODUCTION_DRAFT
    validated_by_member_id: str = ""
    validated_on: DateLike = None
    source_event_id: str = ""
    notes: str = ""

    def is_validated(self) -> bool:
        return self.status == PRODUCTION_VALIDATED and bool(self.validated_by_member_id)

    def has_traceability(self) -> bool:
        return bool(self.proof_refs or self.action_refs)


@dataclass(frozen=True)
class CommissionAccessDecision:
    allowed: bool
    reason: str
    member_id: str
    production_id: str
    diffusion: str
    matched_role: str = ""
    matched_grant_id: str = ""


@dataclass(frozen=True)
class CommissionNoviceSummary:
    qui_participe: tuple[str, ...]
    qui_valide: tuple[str, ...]
    ce_qui_peut_etre_partage: tuple[str, ...]
    warnings: tuple[str, ...] = field(default_factory=tuple)

    def as_dict(self) -> dict[str, tuple[str, ...]]:
        return {
            "qui_participe": self.qui_participe,
            "qui_valide": self.qui_valide,
            "ce_qui_peut_etre_partage": self.ce_qui_peut_etre_partage,
            "warnings": self.warnings,
        }


def active_memberships_for_commission(
    commission: Commission,
    memberships: Iterable[CommissionMembership],
    *,
    as_of: DateLike = None,
) -> tuple[CommissionMembership, ...]:
    return tuple(
        membership
        for membership in memberships
        if membership.commission_id == commission.commission_id
        and _same_subject(membership.theme, commission.subject)
        and _is_active_membership(membership, as_of=as_of)
    )


def can_read_production(
    member: VaultMember,
    production: CommissionProduction,
    role_grants: Iterable[RoleGrant] = (),
    access_grants: Iterable[AccessGrant] = (),
    commission_memberships: Iterable[CommissionMembership] = (),
    *,
    as_of: DateLike = None,
) -> CommissionAccessDecision:
    diffusion = _diffusion_key(production.diffusion)
    level = DIFFUSION_LEVELS[diffusion]
    account_decision = can_member_access_resource(
        member,
        "commission_production",
        production.production_id,
        ACTION_READ,
        level,
        role_grants=role_grants,
        access_grants=access_grants,
        commission_memberships=commission_memberships,
        commission_id=production.commission_id,
        as_of=as_of,
    )
    return CommissionAccessDecision(
        allowed=account_decision.allowed,
        reason=account_decision.reason,
        member_id=member.member_id,
        production_id=production.production_id,
        diffusion=diffusion,
        matched_role=account_decision.matched_role,
        matched_grant_id=account_decision.matched_grant_id,
    )


def visible_productions(
    member: VaultMember,
    productions: Iterable[CommissionProduction],
    role_grants: Iterable[RoleGrant] = (),
    access_grants: Iterable[AccessGrant] = (),
    commission_memberships: Iterable[CommissionMembership] = (),
    *,
    as_of: DateLike = None,
) -> tuple[CommissionProduction, ...]:
    roles = tuple(role_grants)
    grants = tuple(access_grants)
    memberships = tuple(commission_memberships)
    return tuple(
        production
        for production in productions
        if can_read_production(
            member,
            production,
            roles,
            grants,
            memberships,
            as_of=as_of,
        ).allowed
    )


def can_validate_production(
    member: VaultMember,
    commission: Commission,
    mandate: CommissionMandate,
    role_grants: Iterable[RoleGrant] = (),
    commission_memberships: Iterable[CommissionMembership] = (),
    *,
    as_of: DateLike = None,
) -> CommissionAccessDecision:
    if not member.is_active(as_of=as_of):
        return _commission_decision(False, "member_revoked", member, "", commission.diffusion_default)
    if not commission.is_active(as_of=as_of):
        return _commission_decision(False, "commission_inactive", member, "", commission.diffusion_default)
    if not _mandate_matches_commission(mandate, commission, as_of=as_of):
        return _commission_decision(False, "mandate_inactive_or_outside_subject", member, "", commission.diffusion_default)
    if member.member_id == commission.referent_member_id or member.member_id in mandate.validator_member_ids:
        return _commission_decision(True, "named_validator", member, "", commission.diffusion_default)

    active_roles = tuple(grant for grant in role_grants if grant.is_active_for(member, as_of=as_of))
    role_names = {_role_key(grant.role) for grant in active_roles}
    if ROLE_CONSEIL_SYNDICAL in role_names:
        return _commission_decision(True, "cs_role_validator", member, "", commission.diffusion_default, matched_role=ROLE_CONSEIL_SYNDICAL)

    active_memberships = active_memberships_for_commission(commission, commission_memberships, as_of=as_of)
    for membership in active_memberships:
        if membership.member_id != member.member_id:
            continue
        if _role_key(membership.role) == ROLE_REFERENT_COMMISSION:
            return _commission_decision(
                True,
                "commission_referent_validator",
                member,
                "",
                commission.diffusion_default,
                matched_role=membership.role,
            )

    return _commission_decision(False, "not_a_validator", member, "", commission.diffusion_default)


def shareable_productions(productions: Iterable[CommissionProduction]) -> tuple[CommissionProduction, ...]:
    return tuple(
        production
        for production in productions
        if production.is_validated() and production.has_traceability() and _diffusion_key(production.diffusion) != DIFFUSION_COMMISSION
    )


def novice_summary(
    commission: Commission,
    mandate: CommissionMandate,
    productions: Iterable[CommissionProduction] = (),
    members: Iterable[VaultMember] = (),
    memberships: Iterable[CommissionMembership] = (),
    *,
    as_of: DateLike = None,
) -> CommissionNoviceSummary:
    member_names = {member.member_id: member.display_name or member.member_id for member in members}
    active_memberships = active_memberships_for_commission(commission, memberships, as_of=as_of)
    participant_ids = list(commission.participant_ids())
    participant_ids.extend(membership.member_id for membership in active_memberships)
    participant_ids = list(_dedupe(participant_ids))

    referent = _display(commission.referent_member_id, member_names)
    participants = [f"Referent CS: {referent}"] if commission.referent_member_id else []
    participants.extend(
        f"Membre: {_display(member_id, member_names)}"
        for member_id in participant_ids
        if member_id and member_id != commission.referent_member_id
    )

    validators = [f"{mandate.validating_body}: validation du mandat {mandate.mandate_id}"]
    for member_id in mandate.validator_member_ids:
        validators.append(f"Validateur nomme: {_display(member_id, member_names)}")
    if commission.referent_member_id:
        validators.append(f"Referent CS: {referent}")

    shareable = [
        f"{_diffusion_label(production.diffusion)}: {production.title} ({production.production_id})"
        for production in shareable_productions(productions)
    ]
    if not shareable:
        shareable.append("Rien a partager: aucune production validee avec preuve ou action rattachee.")

    warnings = []
    if not commission.is_active(as_of=as_of):
        warnings.append("commission inactive: les acces futurs doivent etre bloques")
    if not _mandate_matches_commission(mandate, commission, as_of=as_of):
        warnings.append("mandat inactif ou hors sujet: les productions restent en historique")
    for production in productions:
        if production.commission_id != commission.commission_id:
            warnings.append(f"production hors commission ignoree: {production.production_id}")
        elif not production.has_traceability():
            warnings.append(f"production sans preuve/action rattachee: {production.production_id}")

    return CommissionNoviceSummary(
        qui_participe=tuple(_dedupe(participants)),
        qui_valide=tuple(_dedupe(validators)),
        ce_qui_peut_etre_partage=tuple(_dedupe(shareable)),
        warnings=tuple(_dedupe(warnings)),
    )


def _commission_decision(
    allowed: bool,
    reason: str,
    member: VaultMember,
    production_id: str,
    diffusion: str,
    *,
    matched_role: str = "",
    matched_grant_id: str = "",
) -> CommissionAccessDecision:
    return CommissionAccessDecision(
        allowed=allowed,
        reason=reason,
        member_id=member.member_id,
        production_id=production_id,
        diffusion=_diffusion_key(diffusion),
        matched_role=matched_role,
        matched_grant_id=matched_grant_id,
    )


def _mandate_matches_commission(mandate: CommissionMandate, commission: Commission, *, as_of: DateLike = None) -> bool:
    return (
        mandate.commission_id == commission.commission_id
        and _same_subject(mandate.subject, commission.subject)
        and mandate.is_active(as_of=as_of)
    )


def _is_active_membership(membership: CommissionMembership, *, as_of: DateLike = None) -> bool:
    return _is_active_window(
        as_of=as_of,
        starts_on=membership.starts_on,
        expires_on=membership.expires_on,
        revoked_on=membership.revoked_on,
    )


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
        stripped = value.strip()
        if not stripped:
            return None
        return date.fromisoformat(stripped[:10])
    raise TypeError(f"Unsupported date value: {value!r}")


def _diffusion_key(value: str) -> str:
    normalized = (value or DIFFUSION_CS).strip().lower()
    aliases = {
        "conseil_syndical": DIFFUSION_CS,
        "coproprietaires": DIFFUSION_COPRO,
        "copropriete": DIFFUSION_COPRO,
    }
    normalized = aliases.get(normalized, normalized)
    if normalized not in DIFFUSION_LEVELS:
        raise ValueError(f"Unsupported diffusion level: {value!r}")
    return normalized


def _diffusion_label(value: str) -> str:
    return {
        DIFFUSION_COMMISSION: "Commission seulement",
        DIFFUSION_CS: "Conseil syndical",
        DIFFUSION_COPRO: "Coproprietaires",
        DIFFUSION_PUBLIC: "Public apres redaction",
    }[_diffusion_key(value)]


def _same_subject(left: str, right: str) -> bool:
    return " ".join(left.lower().split()) == " ".join(right.lower().split())


def _role_key(role: str) -> str:
    return role.strip().lower()


def _display(member_id: str, member_names: dict[str, str]) -> str:
    return member_names.get(member_id, member_id)


def _dedupe(values: Iterable[str]) -> tuple[str, ...]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        if not value or value in seen:
            continue
        seen.add(value)
        result.append(value)
    return tuple(result)
