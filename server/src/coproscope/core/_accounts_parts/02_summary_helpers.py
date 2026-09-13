from __future__ import annotations



def _decision(
    allowed: bool,
    reason: str,
    member: VaultMember,
    resource_type: str,
    resource_id: str,
    action: str,
    level: str,
    *,
    matched_grant_id: str = "",
    matched_role: str = "",
    matched_commission_id: str = "",
) -> AccessDecision:
    return AccessDecision(
        allowed=allowed,
        reason=reason,
        member_id=member.member_id,
        resource_type=resource_type,
        resource_id=resource_id,
        action=action,
        level=_level_key(level),
        matched_grant_id=matched_grant_id,
        matched_role=matched_role,
        matched_commission_id=matched_commission_id,
    )


def _active_commission_membership(
    member: VaultMember,
    memberships: Iterable[CommissionMembership],
    *,
    commission_id: str,
    as_of: DateLike = None,
) -> CommissionMembership | None:
    for membership in memberships:
        if not membership.is_active_for(member, as_of=as_of):
            continue
        if commission_id and membership.commission_id != commission_id:
            continue
        return membership
    return None


def _role_visibility(grants: Iterable[RoleGrant]) -> list[str]:
    visible: list[str] = []
    for grant in grants:
        visible.extend(ROLE_POLICIES.get(_role_key(grant.role), {}).get("see", ()))
    return visible


def _role_actions(grants: Iterable[RoleGrant]) -> list[str]:
    actions: list[str] = []
    for grant in grants:
        actions.extend(ROLE_POLICIES.get(_role_key(grant.role), {}).get("do", ()))
    return actions


def _allowed_actions_for_roles(grants: Iterable[RoleGrant]) -> set[str]:
    return set(_role_actions(grants))


def _first_matching_role(grants: Iterable[RoleGrant], roles: set[str]) -> str:
    for grant in grants:
        role = _role_key(grant.role)
        if role in roles:
            return role
    return ""


def _recovery_sentence(group: RecoveryGroup) -> str:
    status = "quorum actif" if group.can_recover else "quorum insuffisant"
    holders = ", ".join(group.holder_member_ids) if group.holder_member_ids else "aucun detenteur actif"
    return (
        f"{group.key_scope}/{group.group_id}: {status} "
        f"({group.active_share_count}/{group.threshold}) avec {holders}"
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


def _matches(pattern: str, value: str) -> bool:
    return pattern in {"", RESOURCE_ANY} or pattern == value


def _role_key(role: str) -> str:
    return role.strip().lower()


def _level_key(level: str) -> str:
    normalized = level.strip().lower()
    aliases = {
        "coproprietaire": LEVEL_COPRO,
        "copropriete": LEVEL_COPRO,
        "conseil_syndical": LEVEL_CS,
        "cs": LEVEL_CS,
        "commission": LEVEL_COMMISSION,
    }
    return aliases.get(normalized, normalized)


def _dedupe(values: Iterable[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        if value in seen:
            continue
        seen.add(value)
        result.append(value)
    return result
