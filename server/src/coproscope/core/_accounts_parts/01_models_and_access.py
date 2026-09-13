from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Iterable


DateLike = date | datetime | str | None

LEVEL_COPRO = "copro"
LEVEL_CS = "cs"
LEVEL_COMMISSION = "commission"

ROLE_COPROPRIETAIRE = "coproprietaire"
ROLE_CONSEIL_SYNDICAL = "conseil_syndical"
ROLE_REFERENT_COMMISSION = "referent_commission"
ROLE_CONTRIBUTEUR_COMMISSION = "contributeur_commission"
ROLE_AUDITEUR_LECTURE = "auditeur_lecture"
ROLE_ADMINISTRATEUR_LOCAL = "administrateur_local"
ROLE_SYNDIC = "syndic"

ACTION_READ = "read"
ACTION_COMMENT = "comment"
ACTION_CREATE_ACTION = "create_action"
ACTION_SIGN_EVENT = "sign_event"
ACTION_MANAGE_MEMBERS = "manage_members"
ACTION_MANAGE_ACCESS = "manage_access"
ACTION_EXPORT = "export"
ACTION_RECOVER_KEY = "recover_key"
ACTION_TECHNICAL_ADMIN = "technical_admin"

RESOURCE_ANY = "*"


@dataclass(frozen=True)
class UserAccount:
    account_id: str
    display_name: str
    contact_hint: str = ""
    created_on: DateLike = None
    disabled_on: DateLike = None

    def is_active(self, as_of: DateLike = None) -> bool:
        return _is_active_window(as_of=as_of, revoked_on=self.disabled_on)


@dataclass(frozen=True)
class LocalProfile:
    profile_id: str
    account_id: str
    machine_label: str
    protected_by: str = "local_password"
    created_on: DateLike = None
    disabled_on: DateLike = None
    recovery_note_seen: bool = False

    def is_active_for(self, account: UserAccount | str, as_of: DateLike = None) -> bool:
        account_id = account.account_id if isinstance(account, UserAccount) else account
        return self.account_id == account_id and _is_active_window(as_of=as_of, revoked_on=self.disabled_on)


@dataclass(frozen=True)
class VaultMember:
    member_id: str
    account_id: str
    vault_id: str
    display_name: str
    joined_on: DateLike = None
    revoked_on: DateLike = None
    revocation_reason: str = ""
    lot_refs: tuple[str, ...] = field(default_factory=tuple)

    def is_active(self, as_of: DateLike = None) -> bool:
        return _is_active_window(as_of=as_of, starts_on=self.joined_on, revoked_on=self.revoked_on)


@dataclass(frozen=True)
class DeviceIdentity:
    device_id: str
    member_id: str
    vault_id: str
    public_key: str
    label: str = ""
    created_on: DateLike = None
    revoked_on: DateLike = None
    last_seen_on: DateLike = None
    can_sign: bool = True

    def is_active_for(self, member: VaultMember | str, as_of: DateLike = None) -> bool:
        member_id = member.member_id if isinstance(member, VaultMember) else member
        return (
            self.member_id == member_id
            and self.can_sign
            and _is_active_window(as_of=as_of, starts_on=self.created_on, revoked_on=self.revoked_on)
        )


@dataclass(frozen=True)
class RoleGrant:
    grant_id: str
    member_id: str
    role: str
    level: str = LEVEL_COPRO
    scope_id: str = ""
    granted_by: str = ""
    starts_on: DateLike = None
    expires_on: DateLike = None
    revoked_on: DateLike = None
    source_event_id: str = ""
    reason: str = ""

    def is_active_for(self, member: VaultMember | str, as_of: DateLike = None) -> bool:
        member_id = member.member_id if isinstance(member, VaultMember) else member
        return self.member_id == member_id and _is_active_window(
            as_of=as_of,
            starts_on=self.starts_on,
            expires_on=self.expires_on,
            revoked_on=self.revoked_on,
        )


@dataclass(frozen=True)
class AccessGrant:
    grant_id: str
    member_id: str
    actions: tuple[str, ...]
    resource_type: str = RESOURCE_ANY
    resource_id: str = RESOURCE_ANY
    level: str = LEVEL_COPRO
    commission_id: str = ""
    granted_by: str = ""
    starts_on: DateLike = None
    expires_on: DateLike = None
    revoked_on: DateLike = None
    source_event_id: str = ""
    reason: str = ""

    def is_active_for(self, member: VaultMember | str, as_of: DateLike = None) -> bool:
        member_id = member.member_id if isinstance(member, VaultMember) else member
        return self.member_id == member_id and _is_active_window(
            as_of=as_of,
            starts_on=self.starts_on,
            expires_on=self.expires_on,
            revoked_on=self.revoked_on,
        )

    def matches(self, resource_type: str, resource_id: str, action: str) -> bool:
        return (
            _matches(self.resource_type, resource_type)
            and _matches(self.resource_id, resource_id)
            and (ACTION_ALL in self.actions or action in self.actions)
        )


ACTION_ALL = "*"


@dataclass(frozen=True)
class CommissionMembership:
    membership_id: str
    member_id: str
    commission_id: str
    theme: str
    role: str = ROLE_CONTRIBUTEUR_COMMISSION
    referent_member_id: str = ""
    starts_on: DateLike = None
    expires_on: DateLike = None
    revoked_on: DateLike = None
    mandate_id: str = ""
    source_event_id: str = ""

    def is_active_for(self, member: VaultMember | str, as_of: DateLike = None) -> bool:
        member_id = member.member_id if isinstance(member, VaultMember) else member
        return self.member_id == member_id and _is_active_window(
            as_of=as_of,
            starts_on=self.starts_on,
            expires_on=self.expires_on,
            revoked_on=self.revoked_on,
        )


@dataclass(frozen=True)
class RecoveryShare:
    share_id: str
    member_id: str
    vault_id: str
    key_scope: str = "collective"
    group_id: str = "main"
    threshold: int = 2
    share_index: int = 0
    public_fingerprint: str = ""
    custodian_label: str = ""
    created_on: DateLike = None
    revoked_on: DateLike = None
    source_event_id: str = ""

    def is_active(self, as_of: DateLike = None) -> bool:
        return _is_active_window(as_of=as_of, starts_on=self.created_on, revoked_on=self.revoked_on)


@dataclass(frozen=True)
class AccessDecision:
    allowed: bool
    reason: str
    member_id: str
    resource_type: str
    resource_id: str
    action: str
    level: str
    matched_grant_id: str = ""
    matched_role: str = ""
    matched_commission_id: str = ""


@dataclass(frozen=True)
class RecoveryGroup:
    vault_id: str
    key_scope: str
    group_id: str
    threshold: int
    active_share_count: int
    holder_member_ids: tuple[str, ...]
    can_recover: bool
    warnings: tuple[str, ...] = field(default_factory=tuple)


@dataclass(frozen=True)
class IdentitySummary:
    who_am_i: tuple[str, ...]
    can_see: tuple[str, ...]
    can_do: tuple[str, ...]
    recovery: tuple[str, ...]
    warnings: tuple[str, ...]
    active_role_ids: tuple[str, ...]
    inactive_role_ids: tuple[str, ...]
    active_device_ids: tuple[str, ...]
    revoked_device_ids: tuple[str, ...]

    def as_dict(self) -> dict[str, tuple[str, ...]]:
        return {
            "who_am_i": self.who_am_i,
            "can_see": self.can_see,
            "can_do": self.can_do,
            "recovery": self.recovery,
            "warnings": self.warnings,
            "active_role_ids": self.active_role_ids,
            "inactive_role_ids": self.inactive_role_ids,
            "active_device_ids": self.active_device_ids,
            "revoked_device_ids": self.revoked_device_ids,
        }


ROLE_POLICIES: dict[str, dict[str, tuple[str, ...]]] = {
    ROLE_COPROPRIETAIRE: {
        "levels": (LEVEL_COPRO,),
        "see": (
            "documents collectifs ouverts aux coproprietaires",
            "preuves collectives autorisees",
            "archive chiffree et rapport des restrictions",
        ),
        "do": (ACTION_READ, ACTION_COMMENT, ACTION_EXPORT),
    },
    ROLE_CONSEIL_SYNDICAL: {
        "levels": (LEVEL_COPRO, LEVEL_CS),
        "see": (
            "documents collectifs ouverts aux coproprietaires",
            "dossiers conseil syndical",
            "actions, preuves et demandes syndic niveau CS",
        ),
        "do": (
            ACTION_READ,
            ACTION_COMMENT,
            ACTION_CREATE_ACTION,
            ACTION_EXPORT,
            ACTION_MANAGE_ACCESS,
            ACTION_MANAGE_MEMBERS,
        ),
    },
    ROLE_AUDITEUR_LECTURE: {
        "levels": (LEVEL_COPRO,),
        "see": ("journal et exports explicitement ouverts a l'audit",),
        "do": (ACTION_READ,),
    },
    ROLE_ADMINISTRATEUR_LOCAL: {
        "levels": (),
        "see": ("diagnostic technique local sans droit implicite sur le contenu",),
        "do": (ACTION_TECHNICAL_ADMIN,),
    },
    ROLE_SYNDIC: {
        "levels": (),
        "see": ("ressources explicitement partagees avec le syndic",),
        "do": (ACTION_READ, ACTION_COMMENT),
    },
}

COMMISSION_ACTIONS = (ACTION_READ, ACTION_COMMENT, ACTION_CREATE_ACTION)


def can_member_access_resource(
    member: VaultMember,
    resource_type: str,
    resource_id: str,
    action: str,
    level: str,
    role_grants: Iterable[RoleGrant] = (),
    access_grants: Iterable[AccessGrant] = (),
    commission_memberships: Iterable[CommissionMembership] = (),
    *,
    commission_id: str = "",
    as_of: DateLike = None,
) -> AccessDecision:
    if not member.is_active(as_of=as_of):
        return _decision(False, "member_revoked", member, resource_type, resource_id, action, level)

    for grant in access_grants:
        if grant.is_active_for(member, as_of=as_of) and grant.matches(resource_type, resource_id, action):
            return _decision(
                True,
                "explicit_access_grant",
                member,
                resource_type,
                resource_id,
                action,
                level,
                matched_grant_id=grant.grant_id,
            )

    roles = tuple(grant for grant in role_grants if grant.is_active_for(member, as_of=as_of))
    role_names = {_role_key(grant.role) for grant in roles}

    if _level_key(level) == LEVEL_COPRO and role_names.intersection(
        {ROLE_COPROPRIETAIRE, ROLE_CONSEIL_SYNDICAL, ROLE_AUDITEUR_LECTURE}
    ):
        if action == ACTION_READ or action in _allowed_actions_for_roles(roles):
            return _decision(
                True,
                "role_allows_copro_level",
                member,
                resource_type,
                resource_id,
                action,
                level,
                matched_role=_first_matching_role(roles, {ROLE_COPROPRIETAIRE, ROLE_CONSEIL_SYNDICAL, ROLE_AUDITEUR_LECTURE}),
            )

    if _level_key(level) == LEVEL_CS and ROLE_CONSEIL_SYNDICAL in role_names:
        if action == ACTION_READ or action in _allowed_actions_for_roles(roles):
            return _decision(
                True,
                "role_allows_cs_level",
                member,
                resource_type,
                resource_id,
                action,
                level,
                matched_role=ROLE_CONSEIL_SYNDICAL,
            )

    if _level_key(level) == LEVEL_COMMISSION:
        membership = _active_commission_membership(
            member,
            commission_memberships,
            commission_id=commission_id,
            as_of=as_of,
        )
        if membership is not None and action in COMMISSION_ACTIONS:
            return _decision(
                True,
                "commission_membership_allows_scoped_access",
                member,
                resource_type,
                resource_id,
                action,
                level,
                matched_commission_id=membership.commission_id,
                matched_role=membership.role,
            )
        if ROLE_CONSEIL_SYNDICAL in role_names:
            return _decision(
                True,
                "cs_role_allows_commission_oversight",
                member,
                resource_type,
                resource_id,
                action,
                level,
                matched_role=ROLE_CONSEIL_SYNDICAL,
                matched_commission_id=commission_id,
            )

    return _decision(False, "no_active_role_or_access_grant", member, resource_type, resource_id, action, level)


def identity_summary(
    account: UserAccount,
    profile: LocalProfile,
    member: VaultMember,
    devices: Iterable[DeviceIdentity] = (),
    role_grants: Iterable[RoleGrant] = (),
    access_grants: Iterable[AccessGrant] = (),
    commission_memberships: Iterable[CommissionMembership] = (),
    recovery_shares: Iterable[RecoveryShare] = (),
    *,
    as_of: DateLike = None,
) -> IdentitySummary:
    active_roles = tuple(grant for grant in role_grants if grant.is_active_for(member, as_of=as_of))
    inactive_roles = tuple(grant for grant in role_grants if grant.member_id == member.member_id and grant not in active_roles)
    active_memberships = tuple(
        membership for membership in commission_memberships if membership.is_active_for(member, as_of=as_of)
    )
    inactive_memberships = tuple(
        membership
        for membership in commission_memberships
        if membership.member_id == member.member_id and membership not in active_memberships
    )
    active_devices = tuple(device for device in devices if device.is_active_for(member, as_of=as_of))
    revoked_devices = tuple(
        device for device in devices if device.member_id == member.member_id and not device.is_active_for(member, as_of=as_of)
    )
    active_access = tuple(grant for grant in access_grants if grant.is_active_for(member, as_of=as_of))

    who = [
        f"Compte local: {account.display_name} ({account.account_id})",
        f"Profil sur ce poste: {profile.machine_label} ({profile.profile_id})",
        f"Membre du coffre: {member.display_name} ({member.member_id})",
    ]
    if member.lot_refs:
        who.append("Lots declares: " + ", ".join(member.lot_refs))

    can_see = _dedupe(_role_visibility(active_roles))
    can_do = _dedupe(_role_actions(active_roles))

    for membership in active_memberships:
        can_see.append(f"commission {membership.commission_id}: {membership.theme}")
        can_do.extend(COMMISSION_ACTIONS)

    for grant in active_access:
        target = f"{grant.resource_type}:{grant.resource_id}"
        if ACTION_READ in grant.actions or ACTION_ALL in grant.actions:
            can_see.append(f"acces explicite a {target}")
        for action in grant.actions:
            if action != ACTION_READ:
                can_do.append(f"{action} sur {target}")

    recovery_groups = recovery_groups_for(recovery_shares, member.vault_id, as_of=as_of)
    recovery = tuple(_recovery_sentence(group) for group in recovery_groups)

    warnings = []
    if not account.is_active(as_of=as_of):
        warnings.append("compte local desactive")
    if not profile.is_active_for(account, as_of=as_of):
        warnings.append("profil local inactif pour ce compte")
    if not member.is_active(as_of=as_of):
        warnings.append("membre revoque: les acces futurs sont bloques, l'historique reste auditable")
    if inactive_roles:
        warnings.append("roles revoques ou expires conserves dans l'historique")
    if inactive_memberships:
        warnings.append("commissions revoquees ou expirees conservees dans l'historique")
    if not active_devices:
        warnings.append("aucun appareil signataire actif")
    if not any(group.can_recover for group in recovery_groups):
        warnings.append("aucun quorum de recuperation actif pour ce coffre")

    return IdentitySummary(
        who_am_i=tuple(who),
        can_see=tuple(_dedupe(can_see)),
        can_do=tuple(_dedupe(can_do)),
        recovery=recovery,
        warnings=tuple(warnings),
        active_role_ids=tuple(grant.grant_id for grant in active_roles),
        inactive_role_ids=tuple(grant.grant_id for grant in inactive_roles),
        active_device_ids=tuple(device.device_id for device in active_devices),
        revoked_device_ids=tuple(device.device_id for device in revoked_devices),
    )


def recovery_groups_for(
    recovery_shares: Iterable[RecoveryShare],
    vault_id: str,
    *,
    key_scope: str = "",
    as_of: DateLike = None,
) -> tuple[RecoveryGroup, ...]:
    grouped: dict[tuple[str, str, str], list[RecoveryShare]] = {}
    all_shares = [share for share in recovery_shares if share.vault_id == vault_id]
    if key_scope:
        all_shares = [share for share in all_shares if share.key_scope == key_scope]
    for share in all_shares:
        grouped.setdefault((share.vault_id, share.key_scope, share.group_id), []).append(share)

    groups: list[RecoveryGroup] = []
    for (group_vault_id, group_key_scope, group_id), shares in sorted(grouped.items()):
        active = [share for share in shares if share.is_active(as_of=as_of)]
        thresholds = {max(1, share.threshold) for share in shares}
        threshold = max(thresholds) if thresholds else 1
        warnings = []
        if len(thresholds) > 1:
            warnings.append("seuils incoherents dans le groupe")
        if threshold < 2:
            warnings.append("seuil inferieur a 2: risque de confiscation par une seule personne")
        if len(active) < threshold:
            warnings.append("quorum insuffisant")
        groups.append(
            RecoveryGroup(
                vault_id=group_vault_id,
                key_scope=group_key_scope,
                group_id=group_id,
                threshold=threshold,
                active_share_count=len(active),
                holder_member_ids=tuple(share.member_id for share in active),
                can_recover=len(active) >= threshold and threshold >= 2,
                warnings=tuple(warnings),
            )
        )
    return tuple(groups)
