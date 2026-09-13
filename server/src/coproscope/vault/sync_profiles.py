from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


SYNC_PROFILE_IDS = (
    "google_drive_desktop",
    "onedrive",
    "dropbox",
    "nextcloud",
    "syncthing_p2p",
    "cold_encrypted_backup",
    "local_folder",
)

MANDATORY_EXCLUSIONS = (
    ".git",
    ".venv",
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
    ".cache",
    "node_modules",
    "*.log",
    "logs",
    "decrypted_blobs",
    "blobs_dechiffres",
    "tmp_exports",
    "exports_tmp",
    "temporary_exports",
)

CONFLICT_MARKERS = (
    "conflicted copy",
    "conflict copy",
    "selective sync conflict",
    "sync conflict",
    "sync-conflict",
    "computer's conflicted copy",
    "copie en conflit",
    "edit conflict",
    "fichier en conflit",
    "conflit",
    ".gdoc",
    ".gsheet",
    ".gslides",
    ".tmp",
    ".partial",
)


@dataclass(frozen=True)
class TransportRiskRule:
    kind: str
    severity: str
    detail: str
    exact_names: tuple[str, ...] = ()
    prefixes: tuple[str, ...] = ()
    suffixes: tuple[str, ...] = ()
    markers: tuple[str, ...] = ()


@dataclass(frozen=True)
class TransportRisk:
    path: str
    kind: str
    severity: str
    detail: str


COMMON_TRANSPORT_RISK_RULES = (
    TransportRiskRule(
        kind="partial_write",
        severity="error",
        detail="Temporary, partial, or lock files mean the transport may expose bytes before a stable write.",
        prefixes=("~$", ".~lock."),
        suffixes=(".tmp", ".partial", ".part", ".download", ".crdownload", ".syncing", ".uploading"),
    ),
    TransportRiskRule(
        kind="host_metadata",
        severity="warning",
        detail="Host metadata is not vault content and should stay outside the signed archive surface.",
        exact_names=("desktop.ini", "thumbs.db", ".ds_store"),
    ),
)

GOOGLE_DRIVE_TRANSPORT_RISK_RULES = (
    TransportRiskRule(
        kind="provider_placeholder",
        severity="error",
        detail="Google document pointer files are not hydrated evidence bytes and cannot stand in for vault blobs.",
        suffixes=(".gdoc", ".gsheet", ".gslides"),
    ),
)

DROPBOX_TRANSPORT_RISK_RULES = (
    TransportRiskRule(
        kind="sync_engine_metadata",
        severity="warning",
        detail="Dropbox control metadata is transport state, not vault state.",
        exact_names=(".dropbox", ".dropbox.cache"),
    ),
)

NEXTCLOUD_TRANSPORT_RISK_RULES = (
    TransportRiskRule(
        kind="sync_engine_metadata",
        severity="warning",
        detail="Nextcloud control metadata is transport state, not vault state.",
        exact_names=(".sync_journal.db", ".sync-exclude.lst"),
    ),
)

SYNCTHING_TRANSPORT_RISK_RULES = (
    TransportRiskRule(
        kind="sync_engine_metadata",
        severity="warning",
        detail="Syncthing control metadata is transport state and must not be treated as vault evidence.",
        exact_names=(".stfolder", ".stignore", ".stversions"),
    ),
)


@dataclass(frozen=True)
class SyncProfile:
    id: str
    mode: str
    type: str
    risks: tuple[str, ...]
    mandatory_exclusions: tuple[str, ...]
    conflict_markers: tuple[str, ...]
    transport_risk_rules: tuple[TransportRiskRule, ...]


@dataclass(frozen=True)
class SyncAudit:
    path: str
    profile_id: str
    forbidden_entries: tuple[str, ...]
    conflict_markers: tuple[str, ...]
    transport_risks: tuple[TransportRisk, ...] = ()

    @property
    def clean(self) -> bool:
        return not self.forbidden_entries and not self.conflict_markers and not self.transport_risks


def _transport_rules(*profile_rules: TransportRiskRule) -> tuple[TransportRiskRule, ...]:
    return COMMON_TRANSPORT_RISK_RULES + profile_rules


_PROFILES: dict[str, SyncProfile] = {
    "google_drive_desktop": SyncProfile(
        id="google_drive_desktop",
        mode="Google Drive Desktop local folder",
        type="folder_transport",
        risks=(
            "Online-only placeholders may not be available offline.",
            "Google document link files are not evidence blobs.",
            "Concurrent writes can leave provider conflict copies.",
        ),
        mandatory_exclusions=MANDATORY_EXCLUSIONS,
        conflict_markers=CONFLICT_MARKERS,
        transport_risk_rules=_transport_rules(*GOOGLE_DRIVE_TRANSPORT_RISK_RULES),
    ),
    "onedrive": SyncProfile(
        id="onedrive",
        mode="OneDrive local sync folder",
        type="folder_transport",
        risks=(
            "Files On-Demand can expose placeholders instead of bytes.",
            "Office autosave and concurrent edits can create conflict files.",
            "Tenant policy may block or rename some files.",
        ),
        mandatory_exclusions=MANDATORY_EXCLUSIONS,
        conflict_markers=CONFLICT_MARKERS,
        transport_risk_rules=_transport_rules(),
    ),
    "dropbox": SyncProfile(
        id="dropbox",
        mode="Dropbox Desktop local sync folder",
        type="folder_transport",
        risks=(
            "Smart Sync placeholders may hide missing local content.",
            "LAN sync and remote sync can race on active files.",
            "Conflicted copies must be reviewed before evidence is trusted.",
        ),
        mandatory_exclusions=MANDATORY_EXCLUSIONS,
        conflict_markers=CONFLICT_MARKERS,
        transport_risk_rules=_transport_rules(*DROPBOX_TRANSPORT_RISK_RULES),
    ),
    "nextcloud": SyncProfile(
        id="nextcloud",
        mode="Nextcloud Desktop local sync folder",
        type="folder_transport",
        risks=(
            "Server limits and ignored files vary by deployment.",
            "Concurrent updates can create conflict copies.",
            "One server administrator can become a capture point.",
        ),
        mandatory_exclusions=MANDATORY_EXCLUSIONS,
        conflict_markers=CONFLICT_MARKERS,
        transport_risk_rules=_transport_rules(*NEXTCLOUD_TRANSPORT_RISK_RULES),
    ),
    "syncthing_p2p": SyncProfile(
        id="syncthing_p2p",
        mode="Syncthing peer-to-peer replicated folder",
        type="peer_to_peer",
        risks=(
            "Trusted peers can replicate deletions or bad writes.",
            "There is no cloud authority to recover a canonical version.",
            "Adding an untrusted device expands the vault attack surface.",
        ),
        mandatory_exclusions=MANDATORY_EXCLUSIONS,
        conflict_markers=CONFLICT_MARKERS,
        transport_risk_rules=_transport_rules(*SYNCTHING_TRANSPORT_RISK_RULES),
    ),
    "cold_encrypted_backup": SyncProfile(
        id="cold_encrypted_backup",
        mode="Manual encrypted offline backup",
        type="offline_backup",
        risks=(
            "Freshness depends on manual backup cadence.",
            "Lost keys make the backup unrecoverable.",
            "Media failure is only detected by verification restores.",
        ),
        mandatory_exclusions=MANDATORY_EXCLUSIONS,
        conflict_markers=CONFLICT_MARKERS,
        transport_risk_rules=_transport_rules(),
    ),
    "local_folder": SyncProfile(
        id="local_folder",
        mode="Plain local folder without remote transport",
        type="folder_transport",
        risks=(
            "No remote copy exists unless another backup is configured.",
            "Local disk failure can remove the only working copy.",
            "Manual copying can introduce stale duplicates.",
        ),
        mandatory_exclusions=MANDATORY_EXCLUSIONS,
        conflict_markers=CONFLICT_MARKERS,
        transport_risk_rules=_transport_rules(),
    ),
}


def known_sync_profiles() -> tuple[SyncProfile, ...]:
    return tuple(_PROFILES[profile_id] for profile_id in SYNC_PROFILE_IDS)


def get_sync_profile(profile_id: str) -> SyncProfile:
    try:
        return _PROFILES[profile_id]
    except KeyError as exc:
        raise KeyError(f"Unknown sync profile: {profile_id}") from exc


def audit_sync_folder(path: str | Path, profile_id: str) -> SyncAudit:
    profile = get_sync_profile(profile_id)
    root = Path(path)
    if not root.exists():
        raise FileNotFoundError(root)
    if not root.is_dir():
        raise NotADirectoryError(root)

    forbidden_entries: list[str] = []
    conflict_entries: list[str] = []
    transport_risks: list[TransportRisk] = []
    case_candidates: dict[tuple[str, str], list[str]] = {}
    for entry in _iter_entries(root):
        relative_path = entry.relative_to(root).as_posix()
        name = entry.name
        if _matches_any_exclusion(name, profile.mandatory_exclusions):
            forbidden_entries.append(relative_path)
        if _matches_any_marker(name, profile.conflict_markers):
            conflict_entries.append(relative_path)
        transport_risks.extend(_transport_risks_for_entry(entry, relative_path, profile))
        _record_case_candidate(root, entry, case_candidates)
    transport_risks.extend(_case_collision_risks(case_candidates))

    return SyncAudit(
        path=str(root),
        profile_id=profile.id,
        forbidden_entries=tuple(sorted(forbidden_entries)),
        conflict_markers=tuple(sorted(conflict_entries)),
        transport_risks=_sort_transport_risks(_dedupe_transport_risks(transport_risks)),
    )


def _iter_entries(root: Path) -> Iterable[Path]:
    yield from root.rglob("*")


def _matches_any_exclusion(name: str, exclusions: Iterable[str]) -> bool:
    normalized = name.lower()
    return any(_matches_exclusion(normalized, exclusion.lower()) for exclusion in exclusions)


def _matches_exclusion(name: str, exclusion: str) -> bool:
    if exclusion.startswith("*."):
        return name.endswith(exclusion[1:])
    return name == exclusion


def _matches_any_marker(name: str, markers: Iterable[str]) -> bool:
    normalized = name.lower()
    return any(marker.lower() in normalized for marker in markers)


def _transport_risks_for_entry(entry: Path, relative_path: str, profile: SyncProfile) -> list[TransportRisk]:
    risks: list[TransportRisk] = []
    try:
        if entry.is_symlink():
            risks.append(
                TransportRisk(
                    path=relative_path,
                    kind="symlink",
                    severity="error",
                    detail="Symlinks are not stable evidence bytes across sync providers.",
                )
            )
        elif not entry.is_file() and not entry.is_dir():
            risks.append(
                TransportRisk(
                    path=relative_path,
                    kind="non_regular_entry",
                    severity="error",
                    detail="Only regular files and directories can be part of a verifiable vault sync tree.",
                )
            )
    except OSError as exc:
        risks.append(
            TransportRisk(
                path=relative_path,
                kind="unreadable_entry",
                severity="error",
                detail=f"Entry metadata cannot be read reliably: {exc}",
            )
        )

    for rule in profile.transport_risk_rules:
        if _matches_transport_rule(entry.name, rule):
            risks.append(
                TransportRisk(
                    path=relative_path,
                    kind=rule.kind,
                    severity=rule.severity,
                    detail=rule.detail,
                )
            )
    return risks


def _matches_transport_rule(name: str, rule: TransportRiskRule) -> bool:
    normalized = name.lower()
    return (
        normalized in {item.lower() for item in rule.exact_names}
        or any(normalized.startswith(prefix.lower()) for prefix in rule.prefixes)
        or any(normalized.endswith(suffix.lower()) for suffix in rule.suffixes)
        or any(marker.lower() in normalized for marker in rule.markers)
    )


def _record_case_candidate(root: Path, entry: Path, candidates: dict[tuple[str, str], list[str]]) -> None:
    try:
        parent = entry.parent.relative_to(root).as_posix()
    except ValueError:
        parent = str(entry.parent)
    key = (parent, entry.name.casefold())
    candidates.setdefault(key, []).append(entry.relative_to(root).as_posix())


def _case_collision_risks(candidates: dict[tuple[str, str], list[str]]) -> list[TransportRisk]:
    risks: list[TransportRisk] = []
    for paths in candidates.values():
        if len({Path(path).name for path in paths}) <= 1:
            continue
        for relative_path in paths:
            risks.append(
                TransportRisk(
                    path=relative_path,
                    kind="case_collision",
                    severity="error",
                    detail="Entries that differ only by case can collapse on case-insensitive sync clients.",
                )
            )
    return risks


def _dedupe_transport_risks(risks: Iterable[TransportRisk]) -> tuple[TransportRisk, ...]:
    unique: dict[tuple[str, str, str, str], TransportRisk] = {}
    for risk in risks:
        unique[(risk.path, risk.kind, risk.severity, risk.detail)] = risk
    return tuple(unique.values())


def _sort_transport_risks(risks: Iterable[TransportRisk]) -> tuple[TransportRisk, ...]:
    return tuple(sorted(risks, key=lambda risk: (risk.severity, risk.kind, risk.path, risk.detail)))
